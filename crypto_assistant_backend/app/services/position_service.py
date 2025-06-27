"""
Position Management Service
Handles position table updates and real-time position tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.routers.websocket import manager, broadcast_trade_update

logger = logging.getLogger(__name__)

class PositionService:
    """Service for managing position table updates"""
    
    @staticmethod
    async def update_position_table(position_data: Dict[str, Any]):
        """
        Update position table when a new position is created or modified
        
        Args:
            position_data: Dictionary containing position information
        """
        try:
            # Create position table update message
            table_update = {
                "type": "position_table_update",
                "action": "add_position",  # or "update_position", "remove_position"
                "data": {
                    "symbol": position_data.get('symbol'),
                    "direction": position_data.get('direction'),
                    "quantity": position_data.get('quantity'),
                    "entry_price": position_data.get('entry_price'),
                    "current_price": position_data.get('entry_price'),  # Initially same as entry
                    "unrealized_pnl": 0.0,  # Initially zero
                    "pnl_percentage": 0.0,  # Initially zero
                    "position_size_usd": position_data.get('position_size_usd'),
                    "stop_loss": position_data.get('stop_loss'),
                    "take_profit": position_data.get('take_profit'),
                    "main_order_id": position_data.get('main_order_id'),
                    "stop_loss_order_id": position_data.get('stop_loss_order_id'),
                    "take_profit_order_id": position_data.get('take_profit_order_id'),
                    "position_id": position_data.get('position_id'),
                    "timestamp": datetime.now().isoformat(),
                    "testnet": position_data.get('testnet', True),
                    "confidence": position_data.get('confidence', 0),
                    "status": "active"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast table update via WebSocket
            await broadcast_trade_update(table_update)
            
            logger.info(f"SUCCESS: Position table updated for new position: {position_data.get('symbol')} {position_data.get('direction')}")
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error updating position table: {e}")
            return False
    
    @staticmethod
    async def update_position_pnl(symbol: str, current_price: float, unrealized_pnl: float, pnl_percentage: float):
        """
        Update position P&L in real-time
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            unrealized_pnl: Unrealized profit/loss
            pnl_percentage: P&L percentage
        """
        try:
            # Create P&L update message
            pnl_update = {
                "type": "position_table_update",
                "action": "update_pnl",
                "data": {
                    "symbol": symbol,
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl,
                    "pnl_percentage": pnl_percentage,
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast P&L update via WebSocket
            await broadcast_trade_update(pnl_update)
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error updating position P&L for {symbol}: {e}")
            return False
    
    @staticmethod
    async def remove_position_from_table(position_data: Dict[str, Any]):
        """
        Remove position from table when closed
        
        Args:
            position_data: Dictionary containing closed position information
        """
        try:
            # Create position removal message
            removal_update = {
                "type": "position_table_update",
                "action": "remove_position",
                "data": {
                    "symbol": position_data.get('symbol'),
                    "position_id": position_data.get('position_id'),
                    "final_pnl": position_data.get('pnl'),
                    "final_pnl_percentage": position_data.get('pnl_percentage'),
                    "exit_price": position_data.get('exit_price'),
                    "reason": position_data.get('reason'),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast removal update via WebSocket
            await broadcast_trade_update(removal_update)
            
            logger.info(f"SUCCESS: Position removed from table: {position_data.get('symbol')}")
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error removing position from table: {e}")
            return False
    
    @staticmethod
    async def refresh_position_table():
        """
        Refresh entire position table with current data
        """
        try:
            # Import here to avoid circular imports
            from app.services.coinbase_trading import initialize_global_trader
            
            trader = initialize_global_trader()
            active_positions = await trader.get_active_positions()
            
            # Create full table refresh message
            refresh_update = {
                "type": "position_table_update",
                "action": "refresh_table",
                "data": {
                    "positions": list(active_positions.values()),
                    "count": len(active_positions),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast table refresh via WebSocket
            await broadcast_trade_update(refresh_update)
            
            logger.info(f"SUCCESS: Position table refreshed with {len(active_positions)} positions")
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error refreshing position table: {e}")
            return False

# Global position service instance
position_service = PositionService()

# Convenience functions for easy access
async def update_position_table(position_data: Dict[str, Any]):
    """Update position table with new position"""
    return await position_service.update_position_table(position_data)

async def update_position_pnl(symbol: str, current_price: float, unrealized_pnl: float, pnl_percentage: float):
    """Update position P&L in real-time"""
    return await position_service.update_position_pnl(symbol, current_price, unrealized_pnl, pnl_percentage)

async def remove_position_from_table(position_data: Dict[str, Any]):
    """Remove position from table when closed"""
    return await position_service.remove_position_from_table(position_data)

async def refresh_position_table():
    """Refresh entire position table"""
    return await position_service.refresh_position_table()