import pandas as pd
import numpy as np
from services.candlestick_analyzer import analyze_candlesticks
from utils.binance import fetch_binance_data
import asyncio
import json

async def test_analyzer():
    """Test the candlestick analyzer with real Binance data"""
    print("Fetching BTCUSDT data from Binance...")
    
    # Fetch data from Binance
    df = await fetch_binance_data("BTCUSDT", interval="1h", limit=100)
    
    if df is None or len(df) < 50:
        print("Error: Could not fetch enough data from Binance")
        return
    
    print(f"Successfully fetched {len(df)} candles")
    
    # Analyze the candlestick patterns
    print("\nAnalyzing candlestick patterns...")
    result = analyze_candlesticks(df)
    
    # Print the results in a formatted way
    print("\n=== Analysis Results ===")
    print(f"Trend: {result['trend']}")
    print(f"Signal: {result['signal']}")
    print(f"Score: {result['score']} / 4")
    print("\nPattern:")
    print(f"  Name: {result['pattern']['name']}")
    print(f"  Direction: {result['pattern']['direction']}")
    print(f"  Confidence: {result['pattern']['confidence']} / 4")
    print(f"  Timestamp: {result['pattern']['timestamp']}")
    print("\nEntry/Exit Points:")
    print(f"  Entry: {result['entry']}")
    print(f"  Stop Loss: {result['stop_loss']}")
    print(f"  Take Profit: {result['take_profit']}")
    
    # Print the last 5 candles for visual verification
    print("\nLast 5 candles (for visual verification):")
    last_candles = df.tail(5).copy()
    last_candles['body_size'] = abs(last_candles['close'] - last_candles['open'])
    last_candles['upper_shadow'] = last_candles['high'] - last_candles[['open', 'close']].max(axis=1)
    last_candles['lower_shadow'] = last_candles[['open', 'close']].min(axis=1) - last_candles['low']
    last_candles['is_bullish'] = last_candles['close'] > last_candles['open']
    
    for idx, candle in last_candles.iterrows():
        candle_type = "Bullish 📈" if candle['is_bullish'] else "Bearish 📉"
        print(f"  {idx}: {candle_type} - O: {candle['open']:.2f}, H: {candle['high']:.2f}, L: {candle['low']:.2f}, C: {candle['close']:.2f}")
        print(f"     Body: {candle['body_size']:.2f}, Upper Shadow: {candle['upper_shadow']:.2f}, Lower Shadow: {candle['lower_shadow']:.2f}")
    
    # Print as JSON
    print("\nJSON Output:")
    print(json.dumps(result, indent=2))
    
    return result

def test_with_sample_data():
    """Test the analyzer with sample data"""
    # Create sample data
    dates = pd.date_range(start='2025-01-01', periods=100, freq='h')
    
    # Generate random price data with a slight uptrend
    close = np.linspace(40000, 45000, 100) + np.random.normal(0, 500, 100)
    open_prices = close - np.random.normal(0, 200, 100)
    high = np.maximum(close, open_prices) + np.random.normal(100, 100, 100)
    low = np.minimum(close, open_prices) - np.random.normal(100, 100, 100)
    volume = np.random.normal(100, 30, 100)
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    # Analyze the candlestick patterns
    print("Analyzing sample data...")
    result = analyze_candlesticks(df)
    
    # Print the results
    print("\n=== Sample Data Analysis Results ===")
    print(f"Trend: {result['trend']}")
    print(f"Signal: {result['signal']}")
    print(f"Score: {result['score']} / 4")
    print("\nPattern:")
    print(f"  Name: {result['pattern']['name']}")
    print(f"  Direction: {result['pattern']['direction']}")
    print(f"  Confidence: {result['pattern']['confidence']} / 4")
    print("\nEntry/Exit Points:")
    print(f"  Entry: {result['entry']}")
    print(f"  Stop Loss: {result['stop_loss']}")
    print(f"  Take Profit: {result['take_profit']}")
    
    # Print the last 3 candles for visual verification
    print("\nLast 3 candles (for visual verification):")
    last_candles = df.tail(3).copy()
    for idx, candle in last_candles.iterrows():
        candle_type = "Bullish 📈" if candle['close'] > candle['open'] else "Bearish 📉"
        print(f"  {idx.strftime('%Y-%m-%d %H:%M')}: {candle_type}")
        print(f"     O: {candle['open']:.2f}, H: {candle['high']:.2f}, L: {candle['low']:.2f}, C: {candle['close']:.2f}")
    
    return result

if __name__ == "__main__":
    # Test with real data
    try:
        asyncio.run(test_analyzer())
    except Exception as e:
        print(f"Error testing with real data: {e}")
        print("Falling back to sample data...")
        test_with_sample_data()