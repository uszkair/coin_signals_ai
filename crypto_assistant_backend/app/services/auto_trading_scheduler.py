"""
Automatic Trading Scheduler
Continuous market monitoring and automatic trade execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.services.signal_engine import get_current_signal
from app.services.coinbase_trading import execute_automatic_trade, initialize_global_trader
from app.services.ml_signal_generator import generate_ai_signal
from app.services.trading_settings_service import get_trading_settings_service
from app.database import get_db
from app.services.database_service import DatabaseService

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
            from app.database import get_sync_db
            db = next(get_sync_db())
            settings_service = get_trading_settings_service(db)
            return settings_service.get_auto_trading_settings()
        except Exception as e:
            logger.error(f"Error getting auto-trading settings: {e}")
            # Return default settings if database fails
            return {
                'enabled': True,
                'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'],
                'interval': 300,
                'min_confidence': 70
            }
    
    async def _get_position_size_settings(self):
        """Get current position size settings from database"""
        try:
            from app.database import get_sync_db
            db = next(get_sync_db())
            settings_service = get_trading_settings_service(db)
            return settings_service.get_position_size_settings()
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
        try:
            # Use the trading settings service for consistency
            from app.database import get_sync_db
            db = next(get_sync_db())
            settings_service = get_trading_settings_service(db)
            
            # Update auto-trading settings using the service
            settings_data = {'enabled': True}
            settings_service.update_auto_trading_settings(settings_data)
            
            logger.info("Auto-trading ENABLED")
        except Exception as e:
            logger.error(f"Error enabling auto-trading: {e}")
            raise
    
    async def disable_auto_trading(self):
        """Disable automatic trading"""
        try:
            # Use the trading settings service for consistency
            from app.database import get_sync_db
            db = next(get_sync_db())
            settings_service = get_trading_settings_service(db)
            
            # Update auto-trading settings using the service
            settings_data = {'enabled': False}
            settings_service.update_auto_trading_settings(settings_data)
            
            logger.info("Auto-trading DISABLED")
        except Exception as e:
            logger.error(f"Error disabling auto-trading: {e}")
            raise
    
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
                # Log the rejection reason for better debugging
                rejection_reason = result.get('rejection_reason', 'unknown')
                logger.warning(f"Auto-trade rejected for {symbol}: {result.get('error', 'Unknown error')} (reason: {rejection_reason})")
                
                # Note: Rejected trades are now automatically saved to history by the trading service
                # Store signal to prevent duplicates even for rejected trades
                self.last_signals[symbol] = {
                    'signal': signal,
                    'timestamp': datetime.now(),
                    'result': result,
                    'rejected': True,
                    'rejection_reason': rejection_reason
                }
                
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
                'scheduler_running': True,  # Scheduler always runs as background service
                'auto_trading_enabled': auto_settings['enabled'],
                'monitored_symbols': auto_settings['symbols'],
                'check_interval': auto_settings['interval'],
                'min_signal_confidence': auto_settings['min_confidence'],
                'last_signals_count': len(self.last_signals),
                'last_check': datetime.now().isoformat(),
                'mode': 'AUTOMATIC' if auto_settings['enabled'] else 'MANUAL'
            }
        except Exception as e:
            logger.error(f"Error getting auto-trading status: {e}")
            return {
                'scheduler_running': True,  # Scheduler always runs as background service
                'auto_trading_enabled': True,
                'monitored_symbols': [],
                'check_interval': 300,
                'min_signal_confidence': 70,
                'last_signals_count': len(self.last_signals),
                'last_check': datetime.now().isoformat(),
                'mode': 'AUTOMATIC',
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
            
            from app.database import get_sync_db
            db = next(get_sync_db())
            settings_service = get_trading_settings_service(db)
            settings_service.update_auto_trading_settings(update_data)
            logger.info("Auto-trading settings updated in database")
            
        except Exception as e:
            logger.error(f"Error updating auto-trading settings: {e}")
            raise

    async def _monitor_active_positions(self):
        """Monitor active positions and update their status in signal performance"""
        try:
            trader = initialize_global_trader()
            active_positions = await trader.get_active_positions()
            
            # IMPORTANT: Check for orphaned "open" positions in database that are no longer active on Coinbase
            await self._check_orphaned_open_positions(active_positions)
            
            if not active_positions:
                # Also check for pending orders in database that need status updates
                await self._refresh_pending_orders()
                return
            
            logger.debug(f"Monitoring {len(active_positions)} active positions...")
            
            # Prepare position data for WebSocket broadcast
            position_updates = []
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                for position_id, position in active_positions.items():
                    try:
                        # Refresh order status from Coinbase API
                        main_order_id = position.get('main_order_id')
                        symbol = position.get('symbol')
                        
                        if main_order_id and symbol:
                            # Get fresh order status from Coinbase
                            refresh_result = await trader.refresh_order_status(main_order_id, symbol)
                            if refresh_result.get('success'):
                                logger.debug(f"Order {main_order_id} status refreshed: {refresh_result.get('status')}")
                        
                        # Check if position should be closed based on stop loss or take profit
                        current_price = position.get('current_price', 0)
                        entry_price = position.get('entry_price', 0)
                        stop_loss = position.get('stop_loss', 0)
                        take_profit = position.get('take_profit', 0)
                        direction = position.get('direction', '')
                        
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
                                
                                # Broadcast position closure via WebSocket
                                try:
                                    from app.routers.websocket import broadcast_position_status
                                    await broadcast_position_status({
                                        'action': 'closed',
                                        'symbol': symbol,
                                        'position_id': position_id,
                                        'reason': close_reason,
                                        'pnl': close_result.get('pnl', 0),
                                        'pnl_percentage': close_result.get('pnl_percentage', 0)
                                    })
                                except Exception as ws_error:
                                    logger.error(f"Failed to broadcast position closure: {ws_error}")
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
                        
                        # Calculate expected profit and loss
                        quantity = position.get('quantity', 0)
                        expected_profit = 0
                        max_loss = 0
                        
                        if quantity > 0 and entry_price > 0:
                            if direction == 'BUY':
                                # For BUY positions
                                if take_profit > 0:
                                    expected_profit = quantity * (take_profit - entry_price)
                                if stop_loss > 0:
                                    max_loss = abs(quantity * (entry_price - stop_loss))
                            elif direction == 'SELL':
                                # For SELL positions
                                if take_profit > 0:
                                    expected_profit = quantity * (entry_price - take_profit)
                                if stop_loss > 0:
                                    max_loss = abs(quantity * (stop_loss - entry_price))
                        
                        # Collect position data for WebSocket broadcast
                        position_updates.append({
                            'symbol': symbol,
                            'position_side': direction,
                            'position_amt': quantity,
                            'entry_price': entry_price,
                            'mark_price': current_price,
                            'unrealized_pnl': position.get('unrealized_pnl', 0),
                            'pnl_percentage': position.get('unrealized_pnl_percentage', 0),
                            'stop_loss_price': stop_loss,
                            'take_profit_price': take_profit,
                            'expected_profit': expected_profit,
                            'max_loss': max_loss,
                            'position_type': position.get('position_type', 'FUTURES'),
                            'leverage': position.get('leverage', 1),
                            'margin_type': position.get('margin_type', 'cross'),
                            'update_time': int(asyncio.get_event_loop().time() * 1000)
                        })
                    
                    except Exception as e:
                        logger.error(f"Error monitoring position {position_id}: {e}")
                
                # Broadcast position updates via WebSocket
                if position_updates:
                    try:
                        from app.routers.websocket import broadcast_position_update
                        await broadcast_position_update({
                            'pnl_updates': position_updates,
                            'count': len(position_updates),
                            'timestamp': int(asyncio.get_event_loop().time() * 1000)
                        })
                        logger.debug(f"Broadcasted {len(position_updates)} position updates via WebSocket")
                    except Exception as ws_error:
                        logger.error(f"Failed to broadcast position updates: {ws_error}")
                
                # Also refresh pending orders that might not be in active positions
                await self._refresh_pending_orders()
                        
        except Exception as e:
            logger.error(f"Error in position monitoring: {e}")
    
    async def _refresh_pending_orders(self):
        """Refresh status of pending orders from database"""
        try:
            trader = initialize_global_trader()
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Get all pending trading performances with order IDs
                pending_performances = await DatabaseService.get_pending_trading_performances(db)
                
                for performance in pending_performances:
                    if performance.main_order_id and performance.signal:
                        try:
                            symbol = performance.signal.symbol
                            order_id = performance.main_order_id
                            
                            # Refresh order status from Coinbase
                            refresh_result = await trader.refresh_order_status(order_id, symbol)
                            
                            if refresh_result.get('success'):
                                logger.info(f"Pending order {order_id} status updated: {refresh_result.get('status')}")
                            else:
                                logger.warning(f"Failed to refresh order {order_id}: {refresh_result.get('error')}")
                                
                        except Exception as e:
                            logger.error(f"Error refreshing pending order {performance.main_order_id}: {e}")
                            
        except Exception as e:
            logger.error(f"Error refreshing pending orders: {e}")

    async def _check_orphaned_open_positions(self, active_positions: Dict):
        """Check for 'open' positions in database that are no longer active on Coinbase"""
        try:
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Get all "open" positions from database
                open_performances = await DatabaseService.get_pending_trading_performances(db)
                open_positions = [p for p in open_performances if p.result == 'open']
                
                if not open_positions:
                    return
                
                logger.debug(f"Checking {len(open_positions)} open positions in database against {len(active_positions)} active Coinbase positions...")
                
                # Extract main order IDs from active Coinbase positions
                active_order_ids = set()
                for position in active_positions.values():
                    main_order_id = position.get('main_order_id')
                    if main_order_id:
                        active_order_ids.add(str(main_order_id))
                
                # Check each open position in database
                for performance in open_positions:
                    if not performance.main_order_id:
                        continue
                    
                    main_order_id = str(performance.main_order_id)
                    
                    # If this order ID is not in active positions, it means the position was manually closed
                    if main_order_id not in active_order_ids:
                        logger.warning(f"Found orphaned 'open' position: Order ID {main_order_id} for {performance.signal.symbol if performance.signal else 'UNKNOWN'}")
                        
                        try:
                            # Try to get the final order status from Coinbase to determine exit price and P&L
                            trader = initialize_global_trader()
                            symbol = performance.signal.symbol if performance.signal else None
                            
                            if symbol:
                                # Get order status from Coinbase
                                order_status = await trader.get_order_status(symbol, main_order_id)
                                
                                if order_status.get('success') and order_status.get('status') == 'FILLED':
                                    # Order was filled, calculate P&L
                                    entry_price = float(performance.signal.price) if performance.signal else 0
                                    exit_price = order_status.get('avg_price', entry_price)
                                    quantity = performance.quantity or 0
                                    direction = performance.signal.signal_type if performance.signal else 'BUY'
                                    
                                    # Calculate P&L
                                    if direction == 'BUY':
                                        pnl = quantity * (exit_price - entry_price)
                                    else:  # SELL
                                        pnl = quantity * (entry_price - exit_price)
                                    
                                    # Calculate percentage
                                    if quantity > 0 and entry_price > 0:
                                        pnl_percentage = (pnl / (quantity * entry_price)) * 100
                                    else:
                                        pnl_percentage = 0.0
                                    
                                    # Determine result
                                    if pnl > 0:
                                        result = "profit"
                                    elif pnl < 0:
                                        result = "loss"
                                    else:
                                        result = "breakeven"
                                    
                                    # Update the performance record
                                    update_data = {
                                        "exit_price": exit_price,
                                        "exit_time": order_status.get('update_time', datetime.now()),
                                        "profit_loss": pnl,
                                        "profit_percentage": pnl_percentage,
                                        "result": result
                                    }
                                    
                                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                                    logger.info(f"✅ Updated orphaned position: {symbol} Order {main_order_id} -> {result} (${pnl:.2f})")
                                    
                                else:
                                    # Could not get order status, mark as unknown closure
                                    update_data = {
                                        "exit_time": datetime.now(),
                                        "result": "loss",  # Conservative assumption
                                        "profit_loss": 0.0,
                                        "profit_percentage": 0.0
                                    }
                                    
                                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                                    logger.warning(f"⚠️ Marked orphaned position as closed (unknown P&L): {symbol} Order {main_order_id}")
                            else:
                                # No symbol info, just mark as closed
                                update_data = {
                                    "exit_time": datetime.now(),
                                    "result": "loss",  # Conservative assumption
                                    "profit_loss": 0.0,
                                    "profit_percentage": 0.0
                                }
                                
                                await DatabaseService.update_trading_performance(db, performance.id, update_data)
                                logger.warning(f"⚠️ Marked orphaned position as closed (no symbol): Order {main_order_id}")
                                
                        except Exception as e:
                            logger.error(f"❌ Error updating orphaned position {main_order_id}: {e}")
                            # As a last resort, mark it as closed with unknown result
                            try:
                                update_data = {
                                    "exit_time": datetime.now(),
                                    "result": "loss",  # Conservative assumption
                                    "profit_loss": 0.0,
                                    "profit_percentage": 0.0
                                }
                                await DatabaseService.update_trading_performance(db, performance.id, update_data)
                                logger.warning(f"⚠️ Force-closed orphaned position due to error: Order {main_order_id}")
                            except:
                                pass
                
        except Exception as e:
            logger.error(f"Error checking orphaned open positions: {e}")


# Global scheduler instance
auto_trading_scheduler = AutoTradingScheduler()


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