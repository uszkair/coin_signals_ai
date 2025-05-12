# Candlestick Pattern Analyzer

A Python module for detecting candlestick patterns and generating trading signals based on technical analysis.

## Overview

This module analyzes historical price data to:

1. Determine the long-term trend direction (BUY/SELL/SIDEWAYS)
2. Detect candlestick patterns (Hammer, Inverted Hammer, Bullish Engulfing, etc.)
3. Calculate entry, stop loss, and take profit levels
4. Generate a confidence score (0-4)
5. Provide a final trading signal (BUY/SELL/HOLD)

## Usage

### Basic Usage

```python
from services.candlestick_analyzer import analyze_candlesticks
import pandas as pd

# Load your OHLCV data into a pandas DataFrame
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Analyze the data
result = analyze_candlesticks(df)

# Access the results
print(f"Trend: {result['trend']}")
print(f"Pattern: {result['pattern']['name']}")
print(f"Signal: {result['signal']}")
print(f"Entry: {result['entry']}")
print(f"Stop Loss: {result['stop_loss']}")
print(f"Take Profit: {result['take_profit']}")
```

### Integration with Binance Data

```python
from utils.binance import fetch_binance_data
from services.candlestick_analyzer import analyze_candlesticks
import asyncio

async def analyze_symbol(symbol, interval="1h"):
    # Fetch data from Binance
    df = await fetch_binance_data(symbol, interval=interval, limit=100)
    
    if df is None or len(df) < 50:
        return {"error": "Not enough data"}
    
    # Analyze the data
    return analyze_candlesticks(df)

# Run the analysis
result = asyncio.run(analyze_symbol("BTCUSDT", "1h"))
```

### Running the Test Script

A test script is provided to demonstrate the analyzer:

```bash
python test_candlestick_analyzer.py
```

## Output Format

The analyzer returns a dictionary with the following structure:

```python
{
  "trend": "BUY" | "SELL" | "SIDEWAYS",
  "pattern": {
    "name": "Bullish Engulfing",
    "direction": "bullish",
    "confidence": 4,
    "timestamp": "2024-05-12T14:00:00"
  },
  "entry": 43250.0,
  "stop_loss": 42950.0,
  "take_profit": 43850.0,
  "score": 3,
  "signal": "BUY" | "SELL" | "HOLD"
}
```

## Detected Patterns

The analyzer can detect the following candlestick patterns:

1. **Doji** - A candle with a very small body, indicating indecision
2. **Hammer** - A bullish reversal pattern with a small body and long lower shadow
3. **Inverted Hammer** - A bullish reversal pattern with a small body and long upper shadow
4. **Shooting Star** - A bearish reversal pattern with a small body and long upper shadow
5. **Bullish Engulfing** - A bullish reversal pattern where the current candle engulfs the previous one
6. **Bearish Engulfing** - A bearish reversal pattern where the current candle engulfs the previous one

## Trend Determination

The trend is determined based on the following criteria:

- **BUY trend**: EMA50 > EMA200, ADX > 20, MACD positive
- **SELL trend**: EMA50 < EMA200, ADX > 20, MACD negative
- **SIDEWAYS**: EMA50 ≈ EMA200, ADX < 20

## Score System

The confidence score (0-4) is calculated based on:

1. +1 if the pattern aligns with the trend
2. +1 if the pattern has high confidence (≥ 3)
3. +1 if RSI/MACD confirms the signal
4. +1 if ATR is increasing (volatility is rising)

## Dependencies

- pandas
- numpy
- ta (Technical Analysis library)