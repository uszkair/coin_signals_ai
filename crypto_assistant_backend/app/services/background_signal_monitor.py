# app/services/background_signal_monitor.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.services.database_service import DatabaseService
from app.services.signal_engine import get_current_signal
from app.utils.price_data import get_current_price

logger = logging.getLogger(__name__)

class BackgroundSignalMonitor:
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
        self.interval = '1h'
        self.running = False
        self.last_prices = {}
        
    async def start_monitoring(self):
        """Start the background signal monitoring"""
        self.running = True
        logger.info("Starting background signal monitoring...")
        
        while self.running:
            try:
                await self.check_all_symbols()
                # Wait 1 minute before next check
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def stop_monitoring(self):
        """Stop the background signal monitoring"""
        self.running = False
        logger.info("Stopping background signal monitoring...")
    
    async def check_all_symbols(self):
        """Check all symbols for potential signals"""
        async with get_db_session() as db:
            for symbol in self.symbols:
                try:
                    await self.check_symbol_for_signal(db, symbol)
                except Exception as e:
                    logger.error(f"Error checking {symbol}: {e}")
    
    async def check_symbol_for_signal(self, db: AsyncSession, symbol: str):
        """Check a specific symbol for potential trading signals"""
        try:
            # Get current price
            current_price = await get_current_price(symbol)
            
            # Check if price changed significantly since last check
            if symbol in self.last_prices:
                price_change_percent = abs(current_price - self.last_prices[symbol]) / self.last_prices[symbol] * 100
                
                # Only analyze if price changed more than 0.5%
                if price_change_percent < 0.5:
                    return
            
            self.last_prices[symbol] = current_price
            
            # Get the latest signal from database
            recent_signals = await DatabaseService.get_recent_signals(
                db, hours=1, symbol=symbol, limit=1
            )
            
            # Generate new signal analysis
            signal_data = await get_current_signal(symbol, self.interval)
            
            # Check if this is a significant signal worth saving
            should_save_signal = await self.should_save_signal(db, symbol, signal_data, recent_signals)
            
            if should_save_signal:
                # Save the new signal to database
                await DatabaseService.save_signal(db, signal_data)
                logger.info(f"New signal saved for {symbol}: {signal_data['signal']} at {signal_data['entry_price']}")
                
                # TODO: Send push notification to frontend
                await self.send_signal_notification(signal_data)
                
        except Exception as e:
            logger.error(f"Error checking signal for {symbol}: {e}")
    
    async def should_save_signal(self, db: AsyncSession, symbol: str, new_signal: dict, recent_signals: List) -> bool:
        """Determine if a new signal should be saved to database"""
        
        # Always save if no recent signals
        if not recent_signals:
            return True
        
        latest_signal = recent_signals[0]
        
        # Don't save if signal type is the same and within 30 minutes
        if (latest_signal.signal_type == new_signal['signal'] and 
            (datetime.now() - latest_signal.created_at) < timedelta(minutes=30)):
            return False
        
        # Save if signal type changed (BUY -> SELL or SELL -> BUY)
        if latest_signal.signal_type != new_signal['signal']:
            return True
        
        # Save if confidence significantly improved (>10% increase)
        if new_signal['confidence'] > latest_signal.confidence + 10:
            return True
        
        # Save if price moved significantly (>2% from last signal)
        price_change = abs(new_signal['entry_price'] - latest_signal.price) / latest_signal.price * 100
        if price_change > 2.0:
            return True
        
        return False
    
    async def send_signal_notification(self, signal_data: dict):
        """Send push notification for new signal (placeholder for WebSocket)"""
        # TODO: Implement WebSocket notification
        logger.info(f"📢 New Signal Alert: {signal_data['symbol']} - {signal_data['signal']} @ ${signal_data['entry_price']}")
        
        # For now, just log the notification
        # In the future, this would send via WebSocket to connected clients

# Global instance
signal_monitor = BackgroundSignalMonitor()

async def start_background_monitoring():
    """Start the background signal monitoring service"""
    await signal_monitor.start_monitoring()

def stop_background_monitoring():
    """Stop the background signal monitoring service"""
    signal_monitor.stop_monitoring()