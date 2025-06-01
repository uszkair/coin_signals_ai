# app/models/database_models.py

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False, index=True)  # BUY, SELL, HOLD
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    current_price = Column(DECIMAL(20, 8), nullable=False)
    stop_loss = Column(DECIMAL(20, 8))
    take_profit = Column(DECIMAL(20, 8))
    confidence = Column(Integer, nullable=False, index=True)
    score = Column(Integer, default=0)
    pattern = Column(String(50), index=True)
    trend = Column(String(20))
    interval_type = Column(String(10), default='1h')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to performance
    performance = relationship("SignalPerformance", back_populates="signal", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "signal": self.signal_type,
            "entry_price": float(self.entry_price),
            "current_price": float(self.current_price),
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "take_profit": float(self.take_profit) if self.take_profit else None,
            "confidence": self.confidence,
            "score": self.score,
            "pattern": self.pattern,
            "trend": self.trend,
            "interval": self.interval_type,
            "timestamp": self.created_at.isoformat() if self.created_at else None
        }

class SignalPerformance(Base):
    __tablename__ = "signal_performance"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    exit_price = Column(DECIMAL(20, 8))
    exit_time = Column(TIMESTAMP(timezone=True))
    profit_loss = Column(DECIMAL(20, 8))
    profit_percentage = Column(DECIMAL(10, 4))
    result = Column(String(20))  # profit, loss, breakeven, pending
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to signal
    signal = relationship("Signal", back_populates="performance")

    def to_dict(self):
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "profit_loss": float(self.profit_loss) if self.profit_loss else None,
            "profit_percentage": float(self.profit_percentage) if self.profit_percentage else None,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    open_price = Column(DECIMAL(20, 8), nullable=False)
    high_price = Column(DECIMAL(20, 8), nullable=False)
    low_price = Column(DECIMAL(20, 8), nullable=False)
    close_price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(20, 8), nullable=False)
    interval_type = Column(String(10), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "open": float(self.open_price),
            "high": float(self.high_price),
            "low": float(self.low_price),
            "close": float(self.close_price),
            "volume": float(self.volume),
            "interval": self.interval_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    favorite_symbols = Column(ARRAY(Text), default=[])
    min_confidence = Column(Integer, default=60)
    notifications_enabled = Column(Boolean, default=True)
    auto_refresh_interval = Column(Integer, default=30)  # seconds
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "favorite_symbols": self.favorite_symbols or [],
            "min_confidence": self.min_confidence,
            "notifications_enabled": self.notifications_enabled,
            "auto_refresh_interval": self.auto_refresh_interval,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }