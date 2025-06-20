"""
Notifications API Router
Endpoints for managing notifications
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications"])

class MarkReadRequest(BaseModel):
    notification_id: int

class DeleteNotificationRequest(BaseModel):
    notification_id: int

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    priority: str
    data: Optional[dict] = None
    is_read: bool
    is_sent: bool
    sent_at: Optional[str] = None
    read_at: Optional[str] = None
    created_at: str
    updated_at: str

@router.get("/")
async def get_notifications(
    user_id: str = Query('default', description="User ID"),
    limit: int = Query(50, description="Maximum number of notifications"),
    unread_only: bool = Query(False, description="Only return unread notifications")
):
    """Get notifications for a user"""
    try:
        notifications = await NotificationService.get_notifications(
            user_id=user_id,
            limit=limit,
            unread_only=unread_only
        )
        
        return {
            "success": True,
            "data": notifications,
            "count": len(notifications)
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(user_id: str = Query('default', description="User ID")):
    """Get count of unread notifications"""
    try:
        unread_notifications = await NotificationService.get_notifications(
            user_id=user_id,
            limit=1000,  # High limit to get all unread
            unread_only=True
        )
        
        return {
            "success": True,
            "data": {
                "unread_count": len(unread_notifications)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-read")
async def mark_notification_read(request: MarkReadRequest, user_id: str = Query('default')):
    """Mark a notification as read"""
    try:
        success = await NotificationService.mark_notification_read(
            notification_id=request.notification_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Notification marked as read"
            }
        else:
            return {
                "success": False,
                "error": "Notification not found or could not be marked as read"
            }
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-all-read")
async def mark_all_notifications_read(user_id: str = Query('default')):
    """Mark all notifications as read for a user"""
    try:
        # Get all unread notifications
        unread_notifications = await NotificationService.get_notifications(
            user_id=user_id,
            limit=1000,
            unread_only=True
        )
        
        # Mark each as read
        marked_count = 0
        for notification in unread_notifications:
            success = await NotificationService.mark_notification_read(
                notification_id=notification['id'],
                user_id=user_id
            )
            if success:
                marked_count += 1
        
        return {
            "success": True,
            "message": f"Marked {marked_count} notifications as read",
            "data": {
                "marked_count": marked_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_notification(request: DeleteNotificationRequest, user_id: str = Query('default')):
    """Delete a specific notification"""
    try:
        success = await NotificationService.delete_notification(
            notification_id=request.notification_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Notification deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Notification not found or could not be deleted"
            }
        
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-all-read")
async def delete_all_read_notifications(user_id: str = Query('default')):
    """Delete all read notifications for a user"""
    try:
        deleted_count = await NotificationService.delete_all_read_notifications(user_id=user_id)
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} read notifications",
            "data": {
                "deleted_count": deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error deleting all read notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_old_notifications(
    user_id: str = Query('default', description="User ID"),
    days_old: int = Query(7, description="Delete notifications older than this many days")
):
    """Clean up old read notifications"""
    try:
        deleted_count = await NotificationService.cleanup_old_notifications(
            user_id=user_id,
            days_old=days_old
        )
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old notifications",
            "data": {
                "deleted_count": deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_notifications(
    user_id: str = Query('default', description="User ID"),
    hours: int = Query(24, description="Get notifications from last N hours")
):
    """Get recent notifications from the last N hours"""
    try:
        from datetime import datetime, timedelta
        from app.models.notification_models import Notification
        from app.database import AsyncSessionLocal
        from sqlalchemy import select, desc
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        async with AsyncSessionLocal() as db:
            query = select(Notification).where(
                Notification.user_id == user_id,
                Notification.created_at >= cutoff_time
            ).order_by(desc(Notification.created_at))
            
            result = await db.execute(query)
            notifications = result.scalars().all()
            
            notification_data = [notification.to_dict() for notification in notifications]
        
        return {
            "success": True,
            "data": notification_data,
            "count": len(notification_data),
            "hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error getting recent notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_notification_stats(user_id: str = Query('default', description="User ID")):
    """Get notification statistics"""
    try:
        from app.models.notification_models import Notification
        from app.database import AsyncSessionLocal
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as db:
            # Total notifications
            total_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
            total_result = await db.execute(total_query)
            total_count = total_result.scalar()
            
            # Unread notifications
            unread_query = select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            unread_result = await db.execute(unread_query)
            unread_count = unread_result.scalar()
            
            # Notifications by type
            type_query = select(
                Notification.notification_type,
                func.count(Notification.id).label('count')
            ).where(
                Notification.user_id == user_id
            ).group_by(Notification.notification_type)
            
            type_result = await db.execute(type_query)
            type_stats = {row.notification_type: row.count for row in type_result}
        
        return {
            "success": True,
            "data": {
                "total_notifications": total_count,
                "unread_notifications": unread_count,
                "read_notifications": total_count - unread_count,
                "by_type": type_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))