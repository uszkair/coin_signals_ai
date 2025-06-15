"""
Notification Database Models
Models for storing notifications in the database
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True, default='default')
    
    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)  # new_position, position_closed, trade_error
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    
    # Notification data
    data = Column(JSON, nullable=True)  # Additional data (symbol, prices, etc.)
    
    # Status tracking
    is_read = Column(Boolean, default=False, index=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "data": self.data,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True, default='default')
    
    # Notification preferences
    new_position_enabled = Column(Boolean, default=True)
    position_closed_enabled = Column(Boolean, default=True)
    trade_error_enabled = Column(Boolean, default=True)
    position_update_enabled = Column(Boolean, default=False)  # Real-time P&L updates
    
    # Delivery methods
    websocket_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=False)
    
    # Auto-cleanup settings
    auto_delete_read_after_days = Column(Integer, default=7)
    max_notifications_stored = Column(Integer, default=100)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "new_position_enabled": self.new_position_enabled,
            "position_closed_enabled": self.position_closed_enabled,
            "trade_error_enabled": self.trade_error_enabled,
            "position_update_enabled": self.position_update_enabled,
            "websocket_enabled": self.websocket_enabled,
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "auto_delete_read_after_days": self.auto_delete_read_after_days,
            "max_notifications_stored": self.max_notifications_stored,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }