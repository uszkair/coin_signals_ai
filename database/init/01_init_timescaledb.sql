-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS plpgsql;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Optional: use a dedicated schema for organization
CREATE SCHEMA IF NOT EXISTS crypto;
SET search_path TO crypto;

-- === SIGNALS TABLE ===
CREATE TABLE crypto.signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    price DECIMAL(20,8) NOT NULL,
    confidence DECIMAL(10,4) NOT NULL CHECK (confidence >= 0),
    pattern VARCHAR(50),
    trend VARCHAR(20),
    volume DECIMAL(20,8),
    rsi DECIMAL(5,2),
    macd DECIMAL(20,8),
    bollinger_position DECIMAL(5,4),
    support_level DECIMAL(20,8),
    resistance_level DECIMAL(20,8),
    interval_type VARCHAR(10) DEFAULT '1h' CHECK (interval_type IN ('1m','5m','15m','1h','4h','1d')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('crypto.signals', 'created_at');

-- === SIGNAL PERFORMANCE ===
CREATE TABLE crypto.signal_performance (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES crypto.signals(id) ON DELETE CASCADE,
    exit_price DECIMAL(20,8),
    exit_time TIMESTAMPTZ,
    profit_loss DECIMAL(20,8),
    profit_percentage DECIMAL(10,4),
    result VARCHAR(20) CHECK (result IN ('profit', 'loss', 'breakeven', 'pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('crypto.signal_performance', 'created_at');

-- === PRICE HISTORY ===
CREATE TABLE crypto.price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    interval_type VARCHAR(10) NOT NULL CHECK (interval_type IN ('1m','5m','15m','1h','4h','1d')),
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('crypto.price_history', 'timestamp');

-- === USER SETTINGS ===
CREATE TABLE crypto.user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    favorite_symbols TEXT[] DEFAULT '{}',
    min_confidence INTEGER DEFAULT 60 CHECK (min_confidence BETWEEN 0 AND 100),
    notifications_enabled BOOLEAN DEFAULT true,
    auto_refresh_interval INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- === INDEXES ===
CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON crypto.signals (symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type_time ON crypto.signals (signal_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON crypto.signals (confidence DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_pattern ON crypto.signals (pattern, created_at DESC) WHERE pattern IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_performance_signal_id ON crypto.signal_performance (signal_id);
CREATE INDEX IF NOT EXISTS idx_performance_result_time ON crypto.signal_performance (result, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON crypto.price_history (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_interval_time ON crypto.price_history (interval_type, timestamp DESC);

-- === CONTINUOUS AGGREGATES ===
CREATE MATERIALIZED VIEW crypto.signals_hourly_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', created_at) AS hour,
    symbol,
    signal_type,
    COUNT(*) AS signal_count,
    AVG(confidence) AS avg_confidence,
    MAX(confidence) AS max_confidence,
    MIN(confidence) AS min_confidence
FROM crypto.signals
GROUP BY hour, symbol, signal_type
WITH DATA;

SELECT add_continuous_aggregate_policy('crypto.signals_hourly_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

CREATE MATERIALIZED VIEW crypto.signals_daily_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', created_at) AS day,
    symbol,
    COUNT(*) AS total_signals,
    COUNT(*) FILTER (WHERE signal_type = 'BUY') AS buy_signals,
    COUNT(*) FILTER (WHERE signal_type = 'SELL') AS sell_signals,
    COUNT(*) FILTER (WHERE signal_type = 'HOLD') AS hold_signals,
    AVG(confidence) AS avg_confidence,
    AVG(score) AS avg_score
FROM crypto.signals
GROUP BY day, symbol
WITH DATA;

SELECT add_continuous_aggregate_policy('crypto.signals_daily_stats',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- === RETENTION POLICIES ===
SELECT add_retention_policy('crypto.signals', INTERVAL '1 year');
SELECT add_retention_policy('crypto.signal_performance', INTERVAL '1 year');
SELECT add_retention_policy('crypto.price_history', INTERVAL '6 months');

-- === TRIGGERS ===
CREATE OR REPLACE FUNCTION crypto.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_settings_updated_at
BEFORE UPDATE ON crypto.user_settings
FOR EACH ROW EXECUTE FUNCTION crypto.update_updated_at_column();

-- === GRANTS ===
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA crypto TO crypto_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA crypto TO crypto_user;

-- === NO TEST DATA - CLEAN INSTALLATION ===
-- Database is ready for production use without sample data