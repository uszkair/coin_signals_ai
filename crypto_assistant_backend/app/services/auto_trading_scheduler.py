"""
Automatic Trading Scheduler
Continuous market monitoring and automatic trade execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.services.signal_engine import get_current_signal
from app.services.binance_trading import execute_automatic_trade, initialize_global_trader
from app.services.ml_signal_generator import generate_ai_signal
from app.services.trading_settings_service import trading_settings_service
from app.services.database_service import DatabaseService
from app.database import get_db

logger = logging.getLogger(__name__)


class AutoTradingScheduler:
    """Automatic trading scheduler with continuous market monitoring"""
    
    def __init__(self):
        self.is_running = False
        self.last_signals = {}
        
        # Load settings from database
        self._load_settings()
    
    def _load_settings(self):
        """Load auto-trading settings from database"""
        try:
            # Settings are now loaded dynamically from database via trading_settings_service
            # No need to cache them in memory as the service handles caching
            logger.info("Auto-trading scheduler initialized with database settings")
        except Exception as e:
            logger.error(f"Error initializing auto-trading scheduler: {e}")
    
    async def _get_auto_trading_settings(self):
        """Get current auto-trading settings from database"""
        try:
            return await trading_settings_service.get_auto_trading_settings()
        except Exception as e:
            logger.error(f"Error getting auto-trading settings: {e}")
            # Return default settings if database fails
            return {
                'enabled': False,
                'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
                'interval': 300,
                'min_confidence': 70
            }
    
    async def _get_position_size_settings(self):
        """Get current position size settings from database"""
        try:
            return await trading_settings_service.get_position_size_settings()
        except Exception as e:
            logger.error(f"Error getting position size settings: {e}")
            # Return default settings if database fails
            return {
                'mode': 'percentage',
                'max_position_size': 2.0,
                'default_position_size_usd': None
            }
    
    async def start_monitoring(self):
        """Start continuous market monitoring"""
        if self.is_running:
            logger.warning("Auto-trading scheduler already running")
            return
        
        self.is_running = True
        logger.info("Starting auto-trading scheduler...")
        
        while self.is_running:
            try:
                # Get current settings from database
                auto_settings = await self._get_auto_trading_settings()
                
                if auto_settings['enabled']:
                    await self._check_and_execute_trades()
                    await self._monitor_active_positions()
                else:
                    logger.debug("Auto-trading disabled, skipping trade checks")
                    # Still monitor positions even if auto-trading is disabled
                    await self._monitor_active_positions()
                
                # Wait for next check (use interval from database)
                await asyncio.sleep(auto_settings['interval'])
                
            except Exception as e:
                logger.error(f"Error in auto-trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_monitoring(self):
        """Stop continuous market monitoring"""
        self.is_running = False
        logger.info("Auto-trading scheduler stopped")
    
    async def enable_auto_trading(self):
        """Enable automatic trading"""
        await trading_settings_service.update_auto_trading_settings({'enabled': True})
        logger.info("Auto-trading ENABLED")
    
    async def disable_auto_trading(self):
        """Disable automatic trading"""
        await trading_settings_service.update_auto_trading_settings({'enabled': False})
        logger.info("Auto-trading DISABLED")
    
    async def _check_and_execute_trades(self):
        """Check signals and execute trades for all monitored symbols"""
        # Get current monitored symbols from database
        auto_settings = await self._get_auto_trading_settings()
        monitored_symbols = auto_settings['symbols']
        
        logger.info(f"Checking signals for {len(monitored_symbols)} symbols...")
        
        for symbol in monitored_symbols:
            try:
                await self._process_symbol(symbol)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
    
    async def _process_symbol(self, symbol: str):
        """Process a single symbol for trading signals"""
        # Get current signal
        signal = await get_current_signal(symbol, "1h")
        
        # Get AI signal for additional confirmation
        ai_signal = await generate_ai_signal(symbol, "1h")
        
        # Check if signal is strong enough
        if not await self._is_signal_valid(signal, ai_signal):
            logger.debug(f"{symbol}: Signal not strong enough for auto-trading")
            return
        
        # Check if we already traded on this signal recently
        if self._is_duplicate_signal(symbol, signal):
            logger.debug(f"{symbol}: Duplicate signal, skipping")
            return
        
        # Check risk management
        if not await self._check_risk_management():
            logger.warning("Risk management limits reached, stopping auto-trading")
            await self.disable_auto_trading()
            return
        
        # Execute trade with position size
        try:
            logger.info(f"Executing auto-trade for {symbol}: {signal['signal']} (confidence: {signal['confidence']}%)")
            
            # Get position size settings from database
            position_settings = await self._get_position_size_settings()
            
            # Determine position size based on settings
            position_size_usd = None
            if position_settings['mode'] == 'fixed_usd' and position_settings['default_position_size_usd']:
                position_size_usd = position_settings['default_position_size_usd']
                logger.info(f"Using fixed position size: ${position_size_usd}")
            else:
                logger.info("Using percentage-based position sizing from trader config")
            
            result = await execute_automatic_trade(signal, position_size_usd)
            
            if result['success']:
                logger.info(f"Auto-trade executed successfully for {symbol}: {result}")
                
                # Store signal to prevent duplicates
                self.last_signals[symbol] = {
                    'signal': signal,
                    'timestamp': datetime.now(),
                    'result': result
                }
            else:
                logger.error(f"Auto-trade failed for {symbol}: {result}")
                
        except Exception as e:
            logger.error(f"Error executing auto-trade for {symbol}: {e}")
    
    async def _is_signal_valid(self, signal: Dict, ai_signal: Dict) -> bool:
        """Check if signal is valid for auto-trading"""
        # Get current auto-trading settings
        auto_settings = await self._get_auto_trading_settings()
        min_confidence = auto_settings['min_confidence']
        
        # Check confidence
        if signal.get('confidence', 0) < min_confidence:
            return False
        
        # Check signal direction (not HOLD)
        if signal.get('signal') == 'HOLD':
            return False
        
        # Check AI confirmation (optional but recommended)
        ai_direction = ai_signal.get('ai_signal', 'HOLD')
        signal_direction = signal.get('signal')
        
        # AI should agree or be neutral
        if ai_direction != 'HOLD' and ai_direction != signal_direction:
            logger.debug(f"AI signal ({ai_direction}) conflicts with technical signal ({signal_direction})")
            return False
        
        return True
    
    def _is_duplicate_signal(self, symbol: str, signal: Dict) -> bool:
        """Check if this is a duplicate signal"""
        if symbol not in self.last_signals:
            return False
        
        last_signal = self.last_signals[symbol]
        
        # Check if signal is too recent (within 1 hour)
        time_diff = datetime.now() - last_signal['timestamp']
        if time_diff < timedelta(hours=1):
            return True
        
        # Check if signal direction is the same
        if last_signal['signal']['signal'] == signal['signal']:
            return True
        
        return False
    
    async def _check_risk_management(self) -> bool:
        """Check risk management limits"""
        try:
            trader = initialize_global_trader()
            stats = await trader.get_trading_statistics()
            
            # Check daily trade limit
            if stats['daily_trades'] >= stats['max_daily_trades']:
                logger.warning("Daily trade limit reached")
                return False
            
            # Check daily loss limit
            if stats['daily_pnl'] <= -stats['daily_loss_limit']:
                logger.warning("Daily loss limit reached")
                return False
            
            # Check if trading is allowed
            if not stats.get('can_trade', True):
                logger.warning("Trading not allowed by risk management")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk management: {e}")
            return False
    
    async def get_status(self) -> Dict:
        """Get current auto-trading status"""
        try:
            auto_settings = await self._get_auto_trading_settings()
            return {
                'is_running': self.is_running,
                'auto_trading_enabled': auto_settings['enabled'],
                'monitored_symbols': auto_settings['symbols'],
                'check_interval': auto_settings['interval'],
                'min_signal_confidence': auto_settings['min_confidence'],
                'last_signals_count': len(self.last_signals),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting auto-trading status: {e}")
            return {
                'is_running': self.is_running,
                'auto_trading_enabled': False,
                'monitored_symbols': [],
                'check_interval': 300,
                'min_signal_confidence': 70,
                'last_signals_count': len(self.last_signals),
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def update_settings(self, settings: Dict):
        """Update auto-trading settings"""
        try:
            # Validate and update settings in database
            update_data = {}
            
            if 'symbols' in settings:
                update_data['symbols'] = settings['symbols']
            
            if 'interval' in settings:
                update_data['interval'] = max(60, settings['interval'])  # Minimum 1 minute
            
            if 'min_confidence' in settings:
                update_data['min_confidence'] = max(50, min(95, settings['min_confidence']))
            
            if 'enabled' in settings:
                update_data['enabled'] = settings['enabled']
            
            await trading_settings_service.update_auto_trading_settings(update_data)
            logger.info("Auto-trading settings updated in database")
            
        except Exception as e:
            logger.error(f"Error updating auto-trading settings: {e}")
            raise

    async def _monitor_active_positions(self):
        """Monitor active positions and update their status in signal performance"""
        try:
            trader = initialize_global_trader()
            active_positions = await trader.get_active_positions()
            
            if not active_positions:
                return
            
            logger.debug(f"Monitoring {len(active_positions)} active positions...")
            
            async for db in get_db():
                for position_id, position in active_positions.items():
                    try:
                        # Check if position should be closed based on stop loss or take profit
                        current_price = position.get('current_price', 0)
                        entry_price = position.get('entry_price', 0)
                        stop_loss = position.get('stop_loss', 0)
                        take_profit = position.get('take_profit', 0)
                        direction = position.get('direction', '')
                        main_order_id = position.get('main_order_id')
                        
                        should_close = False
                        close_reason = ""
                        
                        if direction == 'BUY':
                            if current_price <= stop_loss:
                                should_close = True
                                close_reason = "stop_loss_hit"
                            elif current_price >= take_profit:
                                should_close = True
                                close_reason = "take_profit_hit"
                        elif direction == 'SELL':
                            if current_price >= stop_loss:
                                should_close = True
                                close_reason = "stop_loss_hit"
                            elif current_price <= take_profit:
                                should_close = True
                                close_reason = "take_profit_hit"
                        
                        if should_close:
                            logger.info(f"Auto-closing position {position_id}: {close_reason}")
                            
                            # Close the position
                            close_result = await trader.close_position(position_id, close_reason)
                            
                            if close_result.get('success'):
                                logger.info(f"Position {position_id} closed successfully: P&L = ${close_result.get('pnl', 0):.2f}")
                            else:
                                logger.error(f"Failed to close position {position_id}: {close_result.get('error')}")
                        
                        # Update signal performance with current unrealized P&L
                        if main_order_id:
                            performance = await DatabaseService.find_performance_by_order_id(db, main_order_id)
                            if performance and performance.result == 'pending':
                                unrealized_pnl = position.get('unrealized_pnl', 0)
                                unrealized_pnl_percentage = position.get('unrealized_pnl_percentage', 0)
                                
                                # Only update if there's a significant change
                                if abs(unrealized_pnl) > 0.01:  # More than 1 cent change
                                    update_data = {
                                        'profit_loss': unrealized_pnl,
                                        'profit_percentage': unrealized_pnl_percentage
                                    }
                                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                    
                    except Exception as e:
                        logger.error(f"Error monitoring position {position_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in position monitoring: {e}")


# Global scheduler instance
auto_trading_scheduler = AutoTradingScheduler()


async def start_auto_trading():
    """Start the auto-trading scheduler"""
    await auto_trading_scheduler.start_monitoring()


def stop_auto_trading():
    """Stop the auto-trading scheduler"""
    auto_trading_scheduler.stop_monitoring()


async def enable_auto_trading():
    """Enable automatic trading"""
    await auto_trading_scheduler.enable_auto_trading()


async def disable_auto_trading():
    """Disable automatic trading"""
    await auto_trading_scheduler.disable_auto_trading()


async def get_auto_trading_status():
    """Get auto-trading status"""
    return await auto_trading_scheduler.get_status()


async def update_auto_trading_settings(settings: Dict):
    """Update auto-trading settings"""
    await auto_trading_scheduler.update_settings(settings)