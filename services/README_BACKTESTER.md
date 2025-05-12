# Signal Backtester

A Python module for backtesting trading signals on historical cryptocurrency data.

## Overview

This module analyzes historical candlestick data for the past 30 days (or any specified period), detects trading signals, calculates entry/exit points, and backtests whether the signals would have been successful. It provides comprehensive analysis including trend direction, volatility assessment, pattern recognition, and risk/reward evaluation.

## Features

- **Historical Analysis**: Processes the last 30 days (configurable) of candlestick data
- **Signal Detection**: Identifies BUY/SELL signals using candlestick patterns
- **Entry/Exit Calculation**: Determines entry, stop loss, and take profit levels
- **Backtesting**: Tests if signals would have hit take profit or stop loss
- **Multi-Timeframe Analysis**: Compares trends across different timeframes
- **Performance Metrics**: Calculates win rate, profit factor, and expectancy
- **Detailed Reporting**: Provides comprehensive analysis for each signal

## Usage

### Basic Usage

```python
import asyncio
from services.signal_backtester import run_backtest

# Run a backtest with default parameters
results = asyncio.run(run_backtest(
    symbol="BTCUSDT",
    interval="1h",
    lookback_days=30,
    risk_reward_ratio=1.5
))
```

### Running the Test Script

A test script is provided to demonstrate various backtesting scenarios:

```bash
python test_signal_backtester.py
```

The test script offers several options:
1. Basic backtest (single symbol)
2. Multi-symbol comparison
3. Timeframe comparison
4. Run all tests

### Output Format

The backtester returns a list of signal analysis dictionaries, each containing:

```json
{
  "timestamp": "2024-04-18T14:00:00",
  "signal": "BUY",
  "pattern": "Hammer",
  "entry": 42850.0,
  "stop_loss": 42600.0,
  "take_profit": 43250.0,
  "score": 4,
  "trend": "BUY",
  "higher_timeframe_trend": "BUY",
  "rsi": 28.3,
  "macd": "bullish",
  "atr": 150.2,
  "volatility": "medium",
  "outcome": "take_profit_hit",
  "duration_minutes": 90,
  "exit_timestamp": "2024-04-18T15:30:00",
  "exit_price": 43250.0,
  "rr_ratio": 1.5,
  "confidence_level": "high",
  "comment": "BUY jelzés Hammer alakzat alapján. A jelzés trendirányba történt. A magasabb időkeret trendje (BUY) megerősíti a jelzést. Medium volatilitás mellett. High megbízhatóságú jelzés. A jelzés sikeres volt, elérte a célpontot."
}
```

## Analysis Components

The backtester analyzes the following elements:

1. **Candlestick Patterns**
   - Identifies specific patterns (Doji, Hammer, Engulfing, etc.)
   - Rates pattern strength and confidence

2. **Trend Direction**
   - Analyzes current timeframe trend
   - Compares with higher timeframe trend (4h for 1h analysis, 1d for 4h analysis)

3. **Technical Indicators**
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - EMA (Exponential Moving Average)
   - ATR (Average True Range)

4. **Volatility Assessment**
   - Classifies as low/medium/high based on ATR
   - Considers ATR as percentage of price

5. **Risk/Reward Analysis**
   - Calculates risk-to-reward ratio
   - Determines optimal take profit levels

6. **Outcome Evaluation**
   - Tracks if take profit or stop loss was hit first
   - Measures time to outcome in minutes
   - Calculates win rate and expectancy

7. **Confidence Scoring**
   - Rates signal confidence as low/medium/high
   - Based on multiple factors including pattern strength and trend alignment

## Performance Metrics

The backtester calculates several performance metrics:

- **Win Rate**: Percentage of signals that hit take profit
- **Average Duration**: Time to reach take profit or stop loss
- **Profit Factor**: (Win Rate × Risk Reward) ÷ Loss Rate
- **Expectancy**: (Win Rate × Risk Reward) - (Loss Rate × 1)

## Integration

This module integrates with the existing candlestick analyzer and can be incorporated into the trading assistant application to provide historical performance analysis and strategy optimization.