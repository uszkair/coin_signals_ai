# app/services/indicators.py

import numpy as np
from typing import Dict, Any, Tuple

def calculate_rsi(candles: list, period: int = 14) -> float:
    """
    Relative Strength Index számítása
    """
    closes = [c["close"] for c in candles]
    deltas = np.diff(closes)
    
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(candles: list) -> Tuple[float, float, float]:
    """
    MACD (Moving Average Convergence Divergence) számítása
    """
    closes = [c["close"] for c in candles]
    
    # EMA számítás
    ema12 = np.mean(closes[-12:])
    ema26 = np.mean(closes[-26:])
    
    macd_line = ema12 - ema26
    signal_line = np.mean([c["close"] for c in candles[-9:]])
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_ema(candles: list, period: int = 20) -> float:
    """
    Exponential Moving Average számítása
    """
    closes = [c["close"] for c in candles]
    return np.mean(closes[-period:])

def compute_indicators(candle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Technikai indikátorok számítása egy gyertyára
    """
    # Valós implementációban ez több gyertyát használna
    # Itt egyszerűsített implementációt adunk
    
    close = candle["close"]
    open_price = candle["open"]
    high = candle["high"]
    low = candle["low"]
    
    # Trend meghatározása
    trend = "bullish" if close > open_price else "bearish"
    
    # Volatilitás
    volatility = (high - low) / low * 100
    
    # Egyéb indikátorok (egyszerűsített)
    strength = "strong" if abs(close - open_price) / (high - low) > 0.7 else "weak"
    
    return {
        "trend": trend,
        "volatility": volatility,
        "strength": strength,
        "reason": f"{trend.capitalize()} trend with {strength} momentum"
    }