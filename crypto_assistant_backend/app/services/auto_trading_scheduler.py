"""
Automatic Trading Scheduler
Continuous market monitoring and automatic trade execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

from app.services.signal_engine import get_current_signal
from app.services.binance_trading import execute_automatic_trade, binance_trader
from app.services.ml_signal_generator import generate_ai_signal

logger = logging.getLogger(__name__)


class AutoTradingScheduler:
    """Automatic trading scheduler with continuous market monitoring"""
    
    def __init__(self):
        self.is_running = False
        self.auto_trading_enabled = False
        self.monitored_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        self.check_interval = 300  # 5 minutes
        self.min_signal_confidence = 70
        self.last_signals = {}
        self.settings_file = "auto_trading_settings.json"
        
        # Position size settings
        self.position_size_mode = 'percentage'  # 'percentage' or 'fixed_usd'
        self.fixed_position_size_usd = None
        
        # Load settings
        self._load_settings()
    
    def _load_settings(self):
        """Load auto-trading settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.auto_trading_enabled = settings.get('enabled', False)
                    self.monitored_symbols = settings.get('symbols', self.monitored_symbols)
                    self.check_interval = settings.get('interval', 300)
                    self.min_signal_confidence = settings.get('min_confidence', 70)
                    logger.info(f"Auto-trading settings loaded: enabled={self.auto_trading_enabled}")
        except Exception as e:
            logger.error(f"Error loading auto-trading settings: {e}")
    
    def _save_settings(self):
        """Save auto-trading settings to file"""
        try:
            settings = {
                'enabled': self.auto_trading_enabled,
                'symbols': self.monitored_symbols,
                'interval': self.check_interval,
                'min_confidence': self.min_signal_confidence,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auto-trading settings: {e}")
    
    async def start_monitoring(self):
        """Start continuous market monitoring"""
        if self.is_running:
            logger.warning("Auto-trading scheduler already running")
            return
        
        self.is_running = True
        logger.info("Starting auto-trading scheduler...")
        
        while self.is_running:
            try:
                if self.auto_trading_enabled:
                    await self._check_and_execute_trades()
                else:
                    logger.debug("Auto-trading disabled, skipping trade checks")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_monitoring(self):
        """Stop continuous market monitoring"""
        self.is_running = False
        logger.info("Auto-trading scheduler stopped")
    
    def enable_auto_trading(self):
        """Enable automatic trading"""
        self.auto_trading_enabled = True
        self._save_settings()
        logger.info("Auto-trading ENABLED")
    
    def disable_auto_trading(self):
        """Disable automatic trading"""
        self.auto_trading_enabled = False
        self._save_settings()
        logger.info("Auto-trading DISABLED")
    
    async def _check_and_execute_trades(self):
        """Check signals and execute trades for all monitored symbols"""
        logger.info(f"Checking signals for {len(self.monitored_symbols)} symbols...")
        
        for symbol in self.monitored_symbols:
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
        if not self._is_signal_valid(signal, ai_signal):
            logger.debug(f"{symbol}: Signal not strong enough for auto-trading")
            return
        
        # Check if we already traded on this signal recently
        if self._is_duplicate_signal(symbol, signal):
            logger.debug(f"{symbol}: Duplicate signal, skipping")
            return
        
        # Check risk management
        if not await self._check_risk_management():
            logger.warning("Risk management limits reached, stopping auto-trading")
            self.disable_auto_trading()
            return
        
        # Execute trade with position size
        try:
            logger.info(f"Executing auto-trade for {symbol}: {signal['signal']} (confidence: {signal['confidence']}%)")
            
            # Determine position size based on settings
            position_size_usd = None
            if self.position_size_mode == 'fixed_usd' and self.fixed_position_size_usd:
                position_size_usd = self.fixed_position_size_usd
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
    
    def _is_signal_valid(self, signal: Dict, ai_signal: Dict) -> bool:
        """Check if signal is valid for auto-trading"""
        # Check confidence
        if signal.get('confidence', 0) < self.min_signal_confidence:
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
            stats = await binance_trader.get_trading_statistics()
            
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
    
    def get_status(self) -> Dict:
        """Get current auto-trading status"""
        return {
            'is_running': self.is_running,
            'auto_trading_enabled': self.auto_trading_enabled,
            'monitored_symbols': self.monitored_symbols,
            'check_interval': self.check_interval,
            'min_signal_confidence': self.min_signal_confidence,
            'last_signals_count': len(self.last_signals),
            'last_check': datetime.now().isoformat()
        }
    
    def update_settings(self, settings: Dict):
        """Update auto-trading settings"""
        if 'symbols' in settings:
            self.monitored_symbols = settings['symbols']
        
        if 'interval' in settings:
            self.check_interval = max(60, settings['interval'])  # Minimum 1 minute
        
        if 'min_confidence' in settings:
            self.min_signal_confidence = max(50, min(95, settings['min_confidence']))
        
        self._save_settings()
        logger.info("Auto-trading settings updated")


# Global scheduler instance
auto_trading_scheduler = AutoTradingScheduler()


async def start_auto_trading():
    """Start the auto-trading scheduler"""
    await auto_trading_scheduler.start_monitoring()


def stop_auto_trading():
    """Stop the auto-trading scheduler"""
    auto_trading_scheduler.stop_monitoring()


def enable_auto_trading():
    """Enable automatic trading"""
    auto_trading_scheduler.enable_auto_trading()


def disable_auto_trading():
    """Disable automatic trading"""
    auto_trading_scheduler.disable_auto_trading()


def get_auto_trading_status():
    """Get auto-trading status"""
    return auto_trading_scheduler.get_status()


def update_auto_trading_settings(settings: Dict):
    """Update auto-trading settings"""
    auto_trading_scheduler.update_settings(settings)