-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create signals table with time-series optimization
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8) NOT NULL,
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    score INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 5),
    pattern VARCHAR(50),
    trend VARCHAR(20),
    interval_type VARCHAR(10) DEFAULT '1h',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable (TimescaleDB time-series table)
SELECT create_hypertable('signals', 'created_at', chunk_time_interval => INTERVAL '1 day');

-- Create signal performance tracking table
CREATE TABLE signal_performance (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id) ON DELETE CASCADE,
    exit_price DECIMAL(20,8),
    exit_time TIMESTAMPTZ,
    profit_loss DECIMAL(20,8),
    profit_percentage DECIMAL(10,4),
    result VARCHAR(20) CHECK (result IN ('profit', 'loss', 'breakeven', 'pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert performance table to hypertable
SELECT create_hypertable('signal_performance', 'created_at', chunk_time_interval => INTERVAL '7 days');

-- Create price history table for backtesting
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    interval_type VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert price history to hypertable
SELECT create_hypertable('price_history', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create user settings table (optional)
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    favorite_symbols TEXT[] DEFAULT '{}',
    min_confidence INTEGER DEFAULT 60 CHECK (min_confidence >= 0 AND min_confidence <= 100),
    notifications_enabled BOOLEAN DEFAULT true,
    auto_refresh_interval INTEGER DEFAULT 30, -- seconds
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for optimal query performance
CREATE INDEX idx_signals_symbol_time ON signals (symbol, created_at DESC);
CREATE INDEX idx_signals_type_time ON signals (signal_type, created_at DESC);
CREATE INDEX idx_signals_confidence ON signals (confidence DESC, created_at DESC);
CREATE INDEX idx_signals_pattern ON signals (pattern, created_at DESC) WHERE pattern IS NOT NULL;

CREATE INDEX idx_performance_signal_id ON signal_performance (signal_id);
CREATE INDEX idx_performance_result_time ON signal_performance (result, created_at DESC);

CREATE INDEX idx_price_symbol_time ON price_history (symbol, timestamp DESC);
CREATE INDEX idx_price_interval_time ON price_history (interval_type, timestamp DESC);

-- Create continuous aggregates for analytics (TimescaleDB feature)
CREATE MATERIALIZED VIEW signals_hourly_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', created_at) AS hour,
    symbol,
    signal_type,
    COUNT(*) as signal_count,
    AVG(confidence) as avg_confidence,
    MAX(confidence) as max_confidence,
    MIN(confidence) as min_confidence
FROM signals
GROUP BY hour, symbol, signal_type
WITH NO DATA;

-- Enable continuous aggregate refresh
SELECT add_continuous_aggregate_policy('signals_hourly_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Create daily stats view
CREATE MATERIALIZED VIEW signals_daily_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', created_at) AS day,
    symbol,
    COUNT(*) as total_signals,
    COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
    COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
    COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) as hold_signals,
    AVG(confidence) as avg_confidence,
    AVG(score) as avg_score
FROM signals
GROUP BY day, symbol
WITH NO DATA;

-- Enable daily stats refresh
SELECT add_continuous_aggregate_policy('signals_daily_stats',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Create retention policy (keep data for 1 year)
SELECT add_retention_policy('signals', INTERVAL '1 year');
SELECT add_retention_policy('signal_performance', INTERVAL '1 year');
SELECT add_retention_policy('price_history', INTERVAL '6 months');

-- Insert some sample data for testing
INSERT INTO signals (symbol, signal_type, entry_price, current_price, stop_loss, take_profit, confidence, score, pattern, trend, interval_type) VALUES
('BTCUSDT', 'BUY', 45000.00, 45150.00, 44500.00, 46000.00, 85, 4, 'Hammer', 'bullish', '1h'),
('ETHUSDT', 'SELL', 3200.00, 3180.00, 3250.00, 3100.00, 75, 3, 'Shooting Star', 'bearish', '1h'),
('BNBUSDT', 'BUY', 320.00, 322.00, 315.00, 330.00, 65, 2, NULL, 'bullish', '1h'),
('ADAUSDT', 'HOLD', 0.45, 0.451, 0.44, 0.47, 50, 1, 'Doji', 'neutral', '1h');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crypto_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO crypto_user;