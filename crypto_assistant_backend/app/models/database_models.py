# app/models/database_models.py

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False, index=True)  # BUY, SELL, HOLD
    price = Column(DECIMAL(20, 8), nullable=False)
    confidence = Column(DECIMAL(10, 4), nullable=False, index=True)
    pattern = Column(String(50), index=True)
    trend = Column(String(20))
    volume = Column(DECIMAL(20, 8))
    rsi = Column(DECIMAL(5, 2))
    macd = Column(DECIMAL(20, 8))
    bollinger_position = Column(DECIMAL(5, 4))
    support_level = Column(DECIMAL(20, 8))
    resistance_level = Column(DECIMAL(20, 8))
    interval_type = Column(String(10), default='1h')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship to performance
    performance = relationship("SignalPerformance", back_populates="signal", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "signal": self.signal_type,
            "entry_price": float(self.price),
            "current_price": float(self.price),
            "stop_loss": float(self.support_level) if self.support_level else None,
            "take_profit": float(self.resistance_level) if self.resistance_level else None,
            "confidence": float(self.confidence) if self.confidence else 0,
            "score": 0,  # Not available in current schema
            "pattern": self.pattern,
            "trend": self.trend,
            "interval": self.interval_type,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "volume": float(self.volume) if self.volume else None,
            "rsi": float(self.rsi) if self.rsi else None,
            "macd": float(self.macd) if self.macd else None,
            "bollinger_position": float(self.bollinger_position) if self.bollinger_position else None,
            "support_level": float(self.support_level) if self.support_level else None,
            "resistance_level": float(self.resistance_level) if self.resistance_level else None
        }

class SignalPerformance(Base):
    __tablename__ = "signal_performance"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("crypto.signals.id", ondelete="CASCADE"), nullable=False)
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
    __table_args__ = {'schema': 'crypto'}

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
    __table_args__ = {'schema': 'crypto'}

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

class TradingSettings(Base):
    __tablename__ = "trading_settings"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True, default='default')
    
    # Auto-trading settings
    auto_trading_enabled = Column(Boolean, default=False)
    monitored_symbols = Column(ARRAY(Text), default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'])
    check_interval = Column(Integer, default=300)  # seconds
    min_signal_confidence = Column(Integer, default=70)
    
    # Position size settings
    position_size_mode = Column(String(20), default='percentage')  # 'percentage' or 'fixed_usd'
    max_position_size = Column(DECIMAL(5, 4), default=0.02)  # 2% default
    default_position_size_usd = Column(DECIMAL(10, 2), nullable=True)
    
    # Risk management settings
    max_daily_trades = Column(Integer, default=10)
    daily_loss_limit = Column(DECIMAL(5, 4), default=0.05)  # 5% default
    
    # Trading environment
    testnet_mode = Column(Boolean, default=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "auto_trading_enabled": self.auto_trading_enabled,
            "monitored_symbols": self.monitored_symbols or [],
            "check_interval": self.check_interval,
            "min_signal_confidence": self.min_signal_confidence,
            "position_size_mode": self.position_size_mode,
            "max_position_size": float(self.max_position_size) if self.max_position_size else 0.02,
            "default_position_size_usd": float(self.default_position_size_usd) if self.default_position_size_usd else None,
            "max_daily_trades": self.max_daily_trades,
            "daily_loss_limit": float(self.daily_loss_limit) if self.daily_loss_limit else 0.05,
            "testnet_mode": self.testnet_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }