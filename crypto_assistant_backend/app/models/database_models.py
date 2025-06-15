# app/models/database_models.py

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Text, ARRAY, JSON
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
    
    # Add decision factors as JSON field
    decision_factors = Column(JSON, nullable=True)
    total_score = Column(Integer, default=0)
    
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
            "resistance_level": float(self.resistance_level) if self.resistance_level else None,
            # Add decision factors and total score
            "decision_factors": self.decision_factors,
            "total_score": self.total_score
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
    result = Column(String(20))  # profit, loss, breakeven, pending, failed_order
    
    # Order execution details
    main_order_id = Column(String(50), nullable=True)
    stop_loss_order_id = Column(String(50), nullable=True)
    take_profit_order_id = Column(String(50), nullable=True)
    quantity = Column(DECIMAL(20, 8), nullable=True)
    position_size_usd = Column(DECIMAL(20, 8), nullable=True)
    
    # Order failure details
    failure_reason = Column(Text, nullable=True)
    
    # Trading environment
    testnet_mode = Column(Boolean, default=True)
    
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
            "main_order_id": self.main_order_id,
            "stop_loss_order_id": self.stop_loss_order_id,
            "take_profit_order_id": self.take_profit_order_id,
            "quantity": float(self.quantity) if self.quantity else None,
            "position_size_usd": float(self.position_size_usd) if self.position_size_usd else None,
            "failure_reason": self.failure_reason,
            "testnet_mode": self.testnet_mode,
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
    
    # Stop Loss and Take Profit settings (percentage based)
    stop_loss_percentage = Column(DECIMAL(5, 4), default=0.02)  # 2% default
    take_profit_percentage = Column(DECIMAL(5, 4), default=0.04)  # 4% default
    use_atr_based_sl_tp = Column(Boolean, default=False)  # Use ATR or percentage
    atr_multiplier_sl = Column(DECIMAL(5, 2), default=1.0)  # ATR multiplier for stop loss
    atr_multiplier_tp = Column(DECIMAL(5, 2), default=2.0)  # ATR multiplier for take profit
    
    # Trading environment
    testnet_mode = Column(Boolean, default=True)
    use_futures = Column(Boolean, default=True)
    
    # Signal Generation Settings
    technical_indicator_weights = Column(JSON, default={
        'rsi_weight': 1.0,
        'macd_weight': 1.0,
        'volume_weight': 1.0,
        'candlestick_weight': 2.0,
        'bollinger_weight': 1.0,
        'ma_weight': 1.0
    })

    # Technical Analysis Settings
    rsi_settings = Column(JSON, default={
        'period': 14,
        'overbought': 70,
        'oversold': 30
    })
    macd_settings = Column(JSON, default={
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
    })
    bollinger_settings = Column(JSON, default={
        'period': 20,
        'deviation': 2.0
    })
    ma_settings = Column(JSON, default={
        'short_ma': 20,
        'long_ma': 50,
        'ma_type': 'EMA'
    })
    volume_settings = Column(JSON, default={
        'volume_threshold_multiplier': 1.5,
        'high_volume_threshold': 2.0
    })
    candlestick_settings = Column(JSON, default={
        'sensitivity': 'medium',
        'min_pattern_score': 0.7
    })

    # AI/ML Settings
    ai_ml_settings = Column(JSON, default={
        'ai_signal_weight': 2.0,
        'ai_confidence_threshold': 60.0,
        'ml_models': {
            'lstm_enabled': True,
            'random_forest_enabled': True,
            'gradient_boosting_enabled': True
        },
        'market_regime_detection': True,
        'sentiment_analysis': False,
        'ensemble_method': 'weighted'
    })

    # Notification Settings
    notification_settings = Column(JSON, default={
        'signal_notifications': {
            'enabled': True,
            'email': False,
            'push': True,
            'in_app': True,
            'min_confidence': 70
        },
        'trade_notifications': {
            'enabled': True,
            'execution_alerts': True,
            'profit_loss_alerts': True,
            'risk_alerts': True
        },
        'system_notifications': {
            'enabled': True,
            'connection_issues': True,
            'error_alerts': True,
            'maintenance_alerts': False
        }
    })

    # Backtesting Settings
    backtest_settings = Column(JSON, default={
        'default_period_days': 30,
        'default_symbols': ['BTCUSDT', 'ETHUSDT'],
        'commission_rate': 0.001,
        'slippage_bps': 5,
        'initial_capital': 10000,
        'benchmark_symbol': 'BTCUSDT'
    })

    # Data & History Settings
    data_history_settings = Column(JSON, default={
        'retention_period_days': 90,
        'auto_cleanup': True,
        'export_format': 'JSON',
        'performance_tracking_period': 30,
        'max_signals_stored': 1000
    })

    # Advanced Settings
    advanced_settings = Column(JSON, default={
        'api_rate_limit': 1200,
        'retry_attempts': 3,
        'request_timeout': 30,
        'cache_duration': 300,
        'logging_level': 'INFO',
        'webhook_urls': []
    })

    # UI/UX Settings
    ui_settings = Column(JSON, default={
        'dashboard_refresh_rate': 30,
        'chart_default_timeframe': '1h',
        'table_rows_per_page': 25,
        'theme': 'light',
        'language': 'hu',
        'decimal_places': 6
    })
    
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
            "stop_loss_percentage": float(self.stop_loss_percentage) if self.stop_loss_percentage else 0.02,
            "take_profit_percentage": float(self.take_profit_percentage) if self.take_profit_percentage else 0.04,
            "use_atr_based_sl_tp": self.use_atr_based_sl_tp,
            "atr_multiplier_sl": float(self.atr_multiplier_sl) if self.atr_multiplier_sl else 1.0,
            "atr_multiplier_tp": float(self.atr_multiplier_tp) if self.atr_multiplier_tp else 2.0,
            "testnet_mode": self.testnet_mode,
            "use_futures": self.use_futures,
            "technical_indicator_weights": self.technical_indicator_weights or {},
            "rsi_settings": self.rsi_settings or {},
            "macd_settings": self.macd_settings or {},
            "bollinger_settings": self.bollinger_settings or {},
            "ma_settings": self.ma_settings or {},
            "volume_settings": self.volume_settings or {},
            "candlestick_settings": self.candlestick_settings or {},
            "ai_ml_settings": self.ai_ml_settings or {},
            "notification_settings": self.notification_settings or {},
            "backtest_settings": self.backtest_settings or {},
            "data_history_settings": self.data_history_settings or {},
            "advanced_settings": self.advanced_settings or {},
            "ui_settings": self.ui_settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class BacktestData(Base):
    __tablename__ = "backtest_data"
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

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    interval_type = Column(String(10), nullable=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    
    # Test parameters
    min_confidence = Column(Integer, default=70)
    position_size = Column(DECIMAL(10, 2), default=100.0)
    
    # Results
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit_usd = Column(DECIMAL(20, 8), default=0.0)
    total_profit_percent = Column(DECIMAL(10, 4), default=0.0)
    win_rate = Column(DECIMAL(5, 2), default=0.0)
    max_drawdown = Column(DECIMAL(10, 4), default=0.0)
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True)
    notes = Column(Text, nullable=True)  # Add missing notes field
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "test_name": self.test_name,
            "symbol": self.symbol,
            "interval": self.interval_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "min_confidence": self.min_confidence,
            "position_size": float(self.position_size) if self.position_size else 100.0,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_profit_usd": float(self.total_profit_usd) if self.total_profit_usd else 0.0,
            "total_profit_percent": float(self.total_profit_percent) if self.total_profit_percent else 0.0,
            "win_rate": float(self.win_rate) if self.win_rate else 0.0,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else 0.0,
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    __table_args__ = {'schema': 'crypto'}

    id = Column(Integer, primary_key=True, index=True)
    backtest_result_id = Column(Integer, ForeignKey("crypto.backtest_results.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    exit_price = Column(DECIMAL(20, 8), nullable=True)
    stop_loss = Column(DECIMAL(20, 8), nullable=True)
    take_profit = Column(DECIMAL(20, 8), nullable=True)
    confidence = Column(DECIMAL(10, 4), nullable=False)
    pattern = Column(String(50), nullable=True)
    entry_time = Column(TIMESTAMP(timezone=True), nullable=False)
    exit_time = Column(TIMESTAMP(timezone=True), nullable=True)
    profit_usd = Column(DECIMAL(20, 8), default=0.0)
    profit_percent = Column(DECIMAL(10, 4), default=0.0)
    result = Column(String(20), default='pending')  # profit, loss, pending
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "backtest_result_id": self.backtest_result_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "entry_price": float(self.entry_price) if self.entry_price else 0.0,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "take_profit": float(self.take_profit) if self.take_profit else None,
            "confidence": float(self.confidence) if self.confidence else 0.0,
            "pattern": self.pattern,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "profit_usd": float(self.profit_usd) if self.profit_usd else 0.0,
            "profit_percent": float(self.profit_percent) if self.profit_percent else 0.0,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
