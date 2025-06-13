-- Migration: Add comprehensive settings to trading_settings table
-- Date: 2025-12-06

-- Add new JSON columns for comprehensive settings
ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS technical_indicator_weights JSON DEFAULT '{
    "rsi_weight": 1.0,
    "macd_weight": 1.0,
    "volume_weight": 1.0,
    "candlestick_weight": 2.0,
    "bollinger_weight": 1.0,
    "ma_weight": 1.0
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS rsi_settings JSON DEFAULT '{
    "period": 14,
    "overbought": 70,
    "oversold": 30
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS macd_settings JSON DEFAULT '{
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS bollinger_settings JSON DEFAULT '{
    "period": 20,
    "deviation": 2.0
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS ma_settings JSON DEFAULT '{
    "short_ma": 20,
    "long_ma": 50,
    "ma_type": "EMA"
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS volume_settings JSON DEFAULT '{
    "volume_threshold_multiplier": 1.5,
    "high_volume_threshold": 2.0
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS candlestick_settings JSON DEFAULT '{
    "sensitivity": "medium",
    "min_pattern_score": 0.7
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS ai_ml_settings JSON DEFAULT '{
    "ai_signal_weight": 2.0,
    "ai_confidence_threshold": 60.0,
    "ml_models": {
        "lstm_enabled": true,
        "random_forest_enabled": true,
        "gradient_boosting_enabled": true
    },
    "market_regime_detection": true,
    "sentiment_analysis": false,
    "ensemble_method": "weighted"
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS notification_settings JSON DEFAULT '{
    "signal_notifications": {
        "enabled": true,
        "email": false,
        "push": true,
        "in_app": true,
        "min_confidence": 70
    },
    "trade_notifications": {
        "enabled": true,
        "execution_alerts": true,
        "profit_loss_alerts": true,
        "risk_alerts": true
    },
    "system_notifications": {
        "enabled": true,
        "connection_issues": true,
        "error_alerts": true,
        "maintenance_alerts": false
    }
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS backtest_settings JSON DEFAULT '{
    "default_period_days": 30,
    "default_symbols": ["BTCUSDT", "ETHUSDT"],
    "commission_rate": 0.001,
    "slippage_bps": 5,
    "initial_capital": 10000,
    "benchmark_symbol": "BTCUSDT"
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS data_history_settings JSON DEFAULT '{
    "retention_period_days": 90,
    "auto_cleanup": true,
    "export_format": "JSON",
    "performance_tracking_period": 30,
    "max_signals_stored": 1000
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS advanced_settings JSON DEFAULT '{
    "api_rate_limit": 1200,
    "retry_attempts": 3,
    "request_timeout": 30,
    "cache_duration": 300,
    "logging_level": "INFO",
    "webhook_urls": []
}';

ALTER TABLE crypto.trading_settings 
ADD COLUMN IF NOT EXISTS ui_settings JSON DEFAULT '{
    "dashboard_refresh_rate": 30,
    "chart_default_timeframe": "1h",
    "table_rows_per_page": 25,
    "theme": "light",
    "language": "hu",
    "decimal_places": 6
}';

-- Update existing records with default values if they don't have them
UPDATE crypto.trading_settings 
SET 
    technical_indicator_weights = COALESCE(technical_indicator_weights, '{
        "rsi_weight": 1.0,
        "macd_weight": 1.0,
        "volume_weight": 1.0,
        "candlestick_weight": 2.0,
        "bollinger_weight": 1.0,
        "ma_weight": 1.0
    }'::json),
    rsi_settings = COALESCE(rsi_settings, '{
        "period": 14,
        "overbought": 70,
        "oversold": 30
    }'::json),
    macd_settings = COALESCE(macd_settings, '{
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    }'::json),
    bollinger_settings = COALESCE(bollinger_settings, '{
        "period": 20,
        "deviation": 2.0
    }'::json),
    ma_settings = COALESCE(ma_settings, '{
        "short_ma": 20,
        "long_ma": 50,
        "ma_type": "EMA"
    }'::json),
    volume_settings = COALESCE(volume_settings, '{
        "volume_threshold_multiplier": 1.5,
        "high_volume_threshold": 2.0
    }'::json),
    candlestick_settings = COALESCE(candlestick_settings, '{
        "sensitivity": "medium",
        "min_pattern_score": 0.7
    }'::json),
    ai_ml_settings = COALESCE(ai_ml_settings, '{
        "ai_signal_weight": 2.0,
        "ai_confidence_threshold": 60.0,
        "ml_models": {
            "lstm_enabled": true,
            "random_forest_enabled": true,
            "gradient_boosting_enabled": true
        },
        "market_regime_detection": true,
        "sentiment_analysis": false,
        "ensemble_method": "weighted"
    }'::json),
    notification_settings = COALESCE(notification_settings, '{
        "signal_notifications": {
            "enabled": true,
            "email": false,
            "push": true,
            "in_app": true,
            "min_confidence": 70
        },
        "trade_notifications": {
            "enabled": true,
            "execution_alerts": true,
            "profit_loss_alerts": true,
            "risk_alerts": true
        },
        "system_notifications": {
            "enabled": true,
            "connection_issues": true,
            "error_alerts": true,
            "maintenance_alerts": false
        }
    }'::json),
    backtest_settings = COALESCE(backtest_settings, '{
        "default_period_days": 30,
        "default_symbols": ["BTCUSDT", "ETHUSDT"],
        "commission_rate": 0.001,
        "slippage_bps": 5,
        "initial_capital": 10000,
        "benchmark_symbol": "BTCUSDT"
    }'::json),
    data_history_settings = COALESCE(data_history_settings, '{
        "retention_period_days": 90,
        "auto_cleanup": true,
        "export_format": "JSON",
        "performance_tracking_period": 30,
        "max_signals_stored": 1000
    }'::json),
    advanced_settings = COALESCE(advanced_settings, '{
        "api_rate_limit": 1200,
        "retry_attempts": 3,
        "request_timeout": 30,
        "cache_duration": 300,
        "logging_level": "INFO",
        "webhook_urls": []
    }'::json),
    ui_settings = COALESCE(ui_settings, '{
        "dashboard_refresh_rate": 30,
        "chart_default_timeframe": "1h",
        "table_rows_per_page": 25,
        "theme": "light",
        "language": "hu",
        "decimal_places": 6
    }'::json)
WHERE 
    technical_indicator_weights IS NULL OR
    rsi_settings IS NULL OR
    macd_settings IS NULL OR
    bollinger_settings IS NULL OR
    ma_settings IS NULL OR
    volume_settings IS NULL OR
    candlestick_settings IS NULL OR
    ai_ml_settings IS NULL OR
    notification_settings IS NULL OR
    backtest_settings IS NULL OR
    data_history_settings IS NULL OR
    advanced_settings IS NULL OR
    ui_settings IS NULL;