import pandas as pd
import numpy as np
from datetime import datetime
import ta

def analyze_candlesticks(df):
    """
    Analyze candlestick patterns and trends from historical data.
    
    Args:
        df (pandas.DataFrame): DataFrame with OHLCV data (open, high, low, close, volume)
                              Minimum 50 rows required.
    
    Returns:
        dict: Analysis results including trend, pattern, entry/exit points, and confidence score
    """
    # Validate input
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")
    
    if len(df) < 50:
        raise ValueError("DataFrame must contain at least 50 rows of data")
    
    # Make a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Calculate technical indicators
    calculate_indicators(df)
    
    # Determine trend
    trend = determine_trend(df)
    
    # Detect candlestick patterns
    pattern = detect_patterns(df)
    
    # Calculate entry, stop loss, and take profit levels
    entry, stop_loss, take_profit = calculate_levels(df, pattern, trend)
    
    # Calculate confidence score
    score = calculate_score(df, trend, pattern)
    
    # Determine final signal
    signal = determine_signal(trend, pattern, score)
    
    # Create result dictionary
    result = {
        "trend": trend,
        "pattern": pattern,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "score": score,
        "signal": signal
    }
    
    return result

def calculate_indicators(df):
    """Calculate technical indicators and add them to the DataFrame"""
    # Add EMA indicators
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    
    # Add RSI
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    
    # Add MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    # Add ADX
    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
    df['adx'] = adx.adx()
    
    # Add ATR
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
    
    # Add Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bb_upper'] = bollinger.bollinger_hband()
    df['bb_middle'] = bollinger.bollinger_mavg()
    df['bb_lower'] = bollinger.bollinger_lband()
    
    # Calculate candle properties
    df['body_size'] = abs(df['close'] - df['open'])
    df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    
    # Calculate previous candle properties
    df['prev_close'] = df['close'].shift(1)
    df['prev_open'] = df['open'].shift(1)
    df['prev_high'] = df['high'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    df['prev_is_bullish'] = df['is_bullish'].shift(1)
    df['prev_is_bearish'] = df['is_bearish'].shift(1)
    df['prev_body_size'] = df['body_size'].shift(1)

def determine_trend(df):
    """Determine the long-term trend based on technical indicators"""
    # Get the latest values
    latest = df.iloc[-1]
    
    # Check trend conditions
    ema_trend = latest['ema50'] > latest['ema200']
    adx_strong = latest['adx'] > 20
    macd_positive = latest['macd'] > latest['macd_signal']
    
    if ema_trend and adx_strong and macd_positive:
        return "BUY"
    elif not ema_trend and adx_strong and not macd_positive:
        return "SELL"
    else:
        return "SIDEWAYS"

def detect_patterns(df):
    """Detect candlestick patterns in the data"""
    # We'll focus on the most recent candle
    latest_idx = len(df) - 1
    latest = df.iloc[latest_idx]
    timestamp = df.index[latest_idx]
    
    # Convert timestamp to ISO format string if it's not already
    if isinstance(timestamp, (pd.Timestamp, datetime)):
        timestamp_str = timestamp.isoformat()
    else:
        timestamp_str = str(timestamp)
    
    # Initialize pattern with default values
    pattern = {
        "name": "No Pattern",
        "direction": "neutral",
        "confidence": 0,
        "timestamp": timestamp_str
    }
    
    # Check for Doji
    if is_doji(latest):
        pattern["name"] = "Doji"
        pattern["direction"] = "neutral"
        pattern["confidence"] = 2
        return pattern
    
    # Check for Hammer
    if is_hammer(latest):
        pattern["name"] = "Hammer"
        pattern["direction"] = "bullish"
        pattern["confidence"] = 3
        return pattern
    
    # Check for Inverted Hammer
    if is_inverted_hammer(latest):
        pattern["name"] = "Inverted Hammer"
        pattern["direction"] = "bullish"
        pattern["confidence"] = 3
        return pattern
    
    # Check for Shooting Star
    if is_shooting_star(latest):
        pattern["name"] = "Shooting Star"
        pattern["direction"] = "bearish"
        pattern["confidence"] = 3
        return pattern
    
    # Check for Bullish Engulfing
    if is_bullish_engulfing(latest):
        pattern["name"] = "Bullish Engulfing"
        pattern["direction"] = "bullish"
        pattern["confidence"] = 4
        return pattern
    
    # Check for Bearish Engulfing
    if is_bearish_engulfing(latest):
        pattern["name"] = "Bearish Engulfing"
        pattern["direction"] = "bearish"
        pattern["confidence"] = 4
        return pattern
    
    return pattern

def is_doji(candle):
    """Check if the candle is a Doji pattern"""
    body_to_range_ratio = candle['body_size'] / (candle['high'] - candle['low'])
    return body_to_range_ratio < 0.1

def is_hammer(candle):
    """Check if the candle is a Hammer pattern"""
    if not candle['is_bullish']:
        return False
    
    body_to_range_ratio = candle['body_size'] / (candle['high'] - candle['low'])
    lower_shadow_ratio = candle['lower_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    upper_shadow_ratio = candle['upper_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    
    return (body_to_range_ratio < 0.3 and 
            lower_shadow_ratio > 2 and 
            upper_shadow_ratio < 0.5)

def is_inverted_hammer(candle):
    """Check if the candle is an Inverted Hammer pattern"""
    if not candle['is_bullish']:
        return False
    
    body_to_range_ratio = candle['body_size'] / (candle['high'] - candle['low'])
    lower_shadow_ratio = candle['lower_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    upper_shadow_ratio = candle['upper_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    
    return (body_to_range_ratio < 0.3 and 
            upper_shadow_ratio > 2 and 
            lower_shadow_ratio < 0.5)

def is_shooting_star(candle):
    """Check if the candle is a Shooting Star pattern"""
    if not candle['is_bearish']:
        return False
    
    body_to_range_ratio = candle['body_size'] / (candle['high'] - candle['low'])
    lower_shadow_ratio = candle['lower_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    upper_shadow_ratio = candle['upper_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0
    
    return (body_to_range_ratio < 0.3 and 
            upper_shadow_ratio > 2 and 
            lower_shadow_ratio < 0.5)

def is_bullish_engulfing(candle):
    """Check if the candle is a Bullish Engulfing pattern"""
    if not candle['is_bullish'] or not candle['prev_is_bearish']:
        return False
    
    return (candle['open'] < candle['prev_close'] and 
            candle['close'] > candle['prev_open'] and
            candle['body_size'] > candle['prev_body_size'])

def is_bearish_engulfing(candle):
    """Check if the candle is a Bearish Engulfing pattern"""
    if not candle['is_bearish'] or not candle['prev_is_bullish']:
        return False
    
    return (candle['open'] > candle['prev_close'] and 
            candle['close'] < candle['prev_open'] and
            candle['body_size'] > candle['prev_body_size'])

def calculate_levels(df, pattern, trend):
    """Calculate entry, stop loss, and take profit levels"""
    latest = df.iloc[-1]
    
    # Default to current close price for entry
    entry = latest['close']
    
    # Calculate stop loss based on pattern and trend
    if pattern['direction'] == 'bullish':
        # For bullish patterns, stop loss is below the low
        stop_loss = min(latest['low'], latest['ema20'] * 0.99)
    elif pattern['direction'] == 'bearish':
        # For bearish patterns, stop loss is above the high
        stop_loss = max(latest['high'], latest['ema20'] * 1.01)
    else:
        # For neutral patterns, use a percentage-based stop loss
        if trend == "BUY":
            stop_loss = entry * 0.98  # 2% below entry
        elif trend == "SELL":
            stop_loss = entry * 1.02  # 2% above entry
        else:
            stop_loss = entry * 0.99 if latest['is_bullish'] else entry * 1.01
    
    # Calculate take profit based on risk:reward ratio (1:1.5)
    risk = abs(entry - stop_loss)
    if trend == "BUY" or (trend == "SIDEWAYS" and pattern['direction'] == 'bullish'):
        take_profit = entry + (risk * 1.5)
    elif trend == "SELL" or (trend == "SIDEWAYS" and pattern['direction'] == 'bearish'):
        take_profit = entry - (risk * 1.5)
    else:
        # Neutral case
        take_profit = entry * 1.015 if latest['is_bullish'] else entry * 0.985
    
    return round(entry, 2), round(stop_loss, 2), round(take_profit, 2)

def calculate_score(df, trend, pattern):
    """Calculate confidence score (0-4) based on multiple factors"""
    latest = df.iloc[-1]
    score = 0
    
    # +1 if pattern aligns with trend
    if (trend == "BUY" and pattern['direction'] == 'bullish') or \
       (trend == "SELL" and pattern['direction'] == 'bearish'):
        score += 1
    
    # +1 if pattern has high confidence
    if pattern['confidence'] >= 3:
        score += 1
    
    # +1 if RSI/MACD confirms the signal
    if (trend == "BUY" and latest['rsi'] < 70 and latest['rsi'] > 30 and latest['macd'] > latest['macd_signal']) or \
       (trend == "SELL" and latest['rsi'] < 70 and latest['rsi'] > 30 and latest['macd'] < latest['macd_signal']):
        score += 1
    
    # +1 if ATR is increasing (volatility is rising)
    if latest['atr'] > df['atr'].iloc[-5:].mean():
        score += 1
    
    return score

def determine_signal(trend, pattern, score):
    """Determine the final trading signal based on trend, pattern, and score"""
    # Strong buy signal
    if trend == "BUY" and pattern['direction'] == 'bullish' and score >= 3:
        return "BUY"
    
    # Strong sell signal
    if trend == "SELL" and pattern['direction'] == 'bearish' and score >= 3:
        return "SELL"
    
    # Moderate buy signal
    if (trend == "BUY" and score >= 2) or (pattern['direction'] == 'bullish' and score >= 3):
        return "BUY"
    
    # Moderate sell signal
    if (trend == "SELL" and score >= 2) or (pattern['direction'] == 'bearish' and score >= 3):
        return "SELL"
    
    # Default to hold
    return "HOLD"