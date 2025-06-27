"""
Notification Service for Trading Events
Handles notifications for new positions, trades, and other trading events
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.routers.websocket import manager, broadcast_trade_update
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling trading notifications"""
    
    @staticmethod
    async def notify_new_position(position_data: Dict[str, Any], db_session=None):
        """
        Send notification when a new position is opened
        
        Args:
            position_data: Dictionary containing position information
            db_session: Database session for saving notification data
        """
        try:
            # Create notification message
            notification = {
                "type": "new_position",
                "title": "Új pozíció nyitva",
                "message": f"Új {position_data.get('direction', 'N/A')} pozíció nyitva: {position_data.get('symbol', 'N/A')}",
                "data": {
                    "symbol": position_data.get('symbol'),
                    "direction": position_data.get('direction'),
                    "quantity": position_data.get('quantity'),
                    "entry_price": position_data.get('entry_price'),
                    "position_size_usd": position_data.get('position_size_usd'),
                    "stop_loss": position_data.get('stop_loss'),
                    "take_profit": position_data.get('take_profit'),
                    "main_order_id": position_data.get('main_order_id'),
                    "timestamp": datetime.now().isoformat(),
                    "testnet": position_data.get('testnet', True)
                },
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket to all connected clients
            await broadcast_trade_update(notification)
            
            # Log the notification
            logger.info(f"SUCCESS: New position notification sent: {position_data.get('symbol')} {position_data.get('direction')}")
            
            # Save notification to database if session provided
            if db_session:
                await NotificationService._save_notification_to_db(db_session, notification)
            else:
                # Save to database with new session
                await NotificationService._save_notification_to_db_async(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error sending new position notification: {e}")
            return False
    
    @staticmethod
    async def notify_position_update(position_data: Dict[str, Any]):
        """
        Send notification when a position is updated (P&L changes, etc.)
        
        Args:
            position_data: Dictionary containing updated position information
        """
        try:
            # Create update notification
            notification = {
                "type": "position_update",
                "title": "Pozíció frissítve",
                "message": f"Pozíció frissítve: {position_data.get('symbol', 'N/A')}",
                "data": {
                    "symbol": position_data.get('symbol'),
                    "unrealized_pnl": position_data.get('unrealized_pnl'),
                    "pnl_percentage": position_data.get('pnl_percentage'),
                    "current_price": position_data.get('current_price'),
                    "timestamp": datetime.now().isoformat()
                },
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            await broadcast_trade_update(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error sending position update notification: {e}")
            return False
    
    @staticmethod
    async def notify_position_closed(position_data: Dict[str, Any], db_session=None):
        """
        Send notification when a position is closed
        
        Args:
            position_data: Dictionary containing closed position information
            db_session: Database session for saving notification data
        """
        try:
            # Determine result type for message
            pnl = position_data.get('pnl', 0)
            if pnl > 0:
                result_text = f"Nyereség: ${pnl:.2f}"
                priority = "high"
            elif pnl < 0:
                result_text = f"Veszteség: ${abs(pnl):.2f}"
                priority = "high"
            else:
                result_text = "Nullszaldó"
                priority = "medium"
            
            notification = {
                "type": "position_closed",
                "title": "Pozíció lezárva",
                "message": f"Pozíció lezárva: {position_data.get('symbol', 'N/A')} - {result_text}",
                "data": {
                    "symbol": position_data.get('symbol'),
                    "direction": position_data.get('direction'),
                    "entry_price": position_data.get('entry_price'),
                    "exit_price": position_data.get('exit_price'),
                    "pnl": pnl,
                    "pnl_percentage": position_data.get('pnl_percentage'),
                    "reason": position_data.get('reason', 'manual'),
                    "timestamp": datetime.now().isoformat()
                },
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            await broadcast_trade_update(notification)
            
            # Log the notification
            logger.info(f"SUCCESS: Position closed notification sent: {position_data.get('symbol')} - {result_text}")
            
            # Save notification to database if session provided
            if db_session:
                await NotificationService._save_notification_to_db(db_session, notification)
            else:
                # Save to database with new session
                await NotificationService._save_notification_to_db_async(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error sending position closed notification: {e}")
            return False
    
    @staticmethod
    async def notify_trade_error(error_data: Dict[str, Any]):
        """
        Send notification when a trade error occurs
        
        Args:
            error_data: Dictionary containing error information
        """
        try:
            notification = {
                "type": "trade_error",
                "title": "Kereskedési hiba",
                "message": f"Hiba történt: {error_data.get('symbol', 'N/A')} - {error_data.get('error', 'Ismeretlen hiba')}",
                "data": {
                    "symbol": error_data.get('symbol'),
                    "error": error_data.get('error'),
                    "error_code": error_data.get('error_code'),
                    "timestamp": datetime.now().isoformat()
                },
                "priority": "critical",
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            await broadcast_trade_update(notification)
            
            # Log the error notification
            logger.error(f"ERROR: Trade error notification sent: {error_data.get('symbol')} - {error_data.get('error')}")
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error sending trade error notification: {e}")
            return False
    
    @staticmethod
    async def _save_notification_to_db(db_session, notification_data: Dict[str, Any]):
        """
        Save notification to database for history tracking
        
        Args:
            db_session: Database session
            notification_data: Notification data to save
        """
        try:
            from app.models.notification_models import Notification
            
            # Create notification record
            notification = Notification(
                user_id='default',  # Default user for now
                notification_type=notification_data['type'],
                title=notification_data['title'],
                message=notification_data['message'],
                priority=notification_data.get('priority', 'medium'),
                data=notification_data.get('data'),
                is_sent=True,
                sent_at=datetime.now()
            )
            
            db_session.add(notification)
            await db_session.commit()
            await db_session.refresh(notification)
            
            logger.info(f"📝 Notification saved to database: ID {notification.id} - {notification_data['type']}")
            return notification.id
            
        except Exception as e:
            logger.error(f"ERROR: Error saving notification to database: {e}")
            try:
                await db_session.rollback()
            except:
                pass
            return None
    
    @staticmethod
    async def _save_notification_to_db_async(notification_data: Dict[str, Any]):
        """
        Save notification to database with new async session
        
        Args:
            notification_data: Notification data to save
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                # Create notification record
                notification = Notification(
                    user_id='default',  # Default user for now
                    notification_type=notification_data['type'],
                    title=notification_data['title'],
                    message=notification_data['message'],
                    priority=notification_data.get('priority', 'medium'),
                    data=notification_data.get('data'),
                    is_sent=True,
                    sent_at=datetime.now()
                )
                
                db.add(notification)
                await db.commit()
                await db.refresh(notification)
                
                logger.info(f"📝 Notification saved to database: ID {notification.id} - {notification_data['type']}")
                return notification.id
                
        except Exception as e:
            logger.error(f"ERROR: Error saving notification to database: {e}")
            return None
    
    @staticmethod
    async def get_notifications(user_id: str = 'default', limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get notifications from database
        
        Args:
            user_id: User ID to get notifications for
            limit: Maximum number of notifications to return
            unread_only: If True, only return unread notifications
            
        Returns:
            List of notification dictionaries
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            from sqlalchemy import select, desc
            
            async with AsyncSessionLocal() as db:
                query = select(Notification).where(Notification.user_id == user_id)
                
                if unread_only:
                    query = query.where(Notification.is_read == False)
                
                query = query.order_by(desc(Notification.created_at)).limit(limit)
                
                result = await db.execute(query)
                notifications = result.scalars().all()
                
                return [notification.to_dict() for notification in notifications]
                
        except Exception as e:
            logger.error(f"ERROR: Error getting notifications from database: {e}")
            return []
    
    @staticmethod
    async def mark_notification_read(notification_id: int, user_id: str = 'default') -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: ID of the notification to mark as read
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                query = select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
                
                result = await db.execute(query)
                notification = result.scalar_one_or_none()
                
                if notification:
                    notification.is_read = True
                    notification.read_at = datetime.now()
                    await db.commit()
                    
                    logger.info(f"📖 Notification marked as read: ID {notification_id}")
                    return True
                else:
                    logger.warning(f"ERROR: Notification not found: ID {notification_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"ERROR: Error marking notification as read: {e}")
            return False
    
    @staticmethod
    async def delete_notification(notification_id: int, user_id: str = 'default') -> bool:
        """
        Delete a specific notification
        
        Args:
            notification_id: ID of the notification to delete
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            from sqlalchemy import select, delete
            
            async with AsyncSessionLocal() as db:
                # Delete the specific notification
                delete_query = delete(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
                
                result = await db.execute(delete_query)
                deleted_count = result.rowcount
                await db.commit()
                
                if deleted_count > 0:
                    logger.info(f"🗑️ Notification deleted: ID {notification_id}")
                    return True
                else:
                    logger.warning(f"ERROR: Notification not found for deletion: ID {notification_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"ERROR: Error deleting notification: {e}")
            return False
    
    @staticmethod
    async def delete_all_read_notifications(user_id: str = 'default') -> int:
        """
        Delete all read notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications deleted
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            from sqlalchemy import delete
            
            async with AsyncSessionLocal() as db:
                # Delete all read notifications
                delete_query = delete(Notification).where(
                    Notification.user_id == user_id,
                    Notification.is_read == True
                )
                
                result = await db.execute(delete_query)
                deleted_count = result.rowcount
                await db.commit()
                
                logger.info(f"🗑️ Deleted {deleted_count} read notifications for user {user_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"ERROR: Error deleting all read notifications: {e}")
            return 0
    
    @staticmethod
    async def cleanup_old_notifications(user_id: str = 'default', days_old: int = 7) -> int:
        """
        Clean up old read notifications
        
        Args:
            user_id: User ID
            days_old: Delete notifications older than this many days
            
        Returns:
            Number of notifications deleted
        """
        try:
            from app.models.notification_models import Notification
            from app.database import AsyncSessionLocal
            from sqlalchemy import select, delete
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            async with AsyncSessionLocal() as db:
                # Delete old read notifications
                delete_query = delete(Notification).where(
                    Notification.user_id == user_id,
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date
                )
                
                result = await db.execute(delete_query)
                deleted_count = result.rowcount
                await db.commit()
                
                logger.info(f"🧹 Cleaned up {deleted_count} old notifications for user {user_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"ERROR: Error cleaning up old notifications: {e}")
            return 0

# Global notification service instance
notification_service = NotificationService()

# Convenience functions for easy access
async def notify_new_position(position_data: Dict[str, Any], db_session=None):
    """Send notification for new position"""
    return await notification_service.notify_new_position(position_data, db_session)

async def notify_position_update(position_data: Dict[str, Any]):
    """Send notification for position update"""
    return await notification_service.notify_position_update(position_data)

async def notify_position_closed(position_data: Dict[str, Any], db_session=None):
    """Send notification for closed position"""
    return await notification_service.notify_position_closed(position_data, db_session)

async def notify_trade_error(error_data: Dict[str, Any]):
    """Send notification for trade error"""
    return await notification_service.notify_trade_error(error_data)