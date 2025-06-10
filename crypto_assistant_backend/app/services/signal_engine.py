# app/services/signal_engine.py

from datetime import datetime, timedelta
from typing import Optional
import random
from app.utils.price_data import get_historical_data, get_current_price

class TradeResult:
    def __init__(self, entry_price: float, stop_loss: float, take_profit: float, 
                 exit_price: Optional[float], exit_time: Optional[datetime], 
                 result: str, profit_usd: float, profit_percent: float):
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.result = result
        self.profit_usd = profit_usd
        self.profit_percent = profit_percent

async def simulate_trade(entry: float, direction: str, candle: dict,
                         symbol: str = "BTCUSDT", rr_ratio: float = 2.0, days_ahead: int = 7) -> TradeResult:
    # Calculate proper ATR from multiple candles for better accuracy
    try:
        # Get recent candles for better ATR calculation
        recent_candles = await get_historical_data(symbol=symbol, interval="1h", days=7)
        if len(recent_candles) >= 14:
            # Calculate 14-period ATR
            atr_values = []
            for i in range(1, min(15, len(recent_candles))):
                curr = recent_candles[i]
                prev = recent_candles[i-1]
                tr = max(
                    curr["high"] - curr["low"],
                    abs(curr["high"] - prev["close"]),
                    abs(curr["low"] - prev["close"])
                )
                atr_values.append(tr)
            atr = sum(atr_values) / len(atr_values)
        else:
            atr = candle["high"] - candle["low"]
    except:
        atr = candle["high"] - candle["low"]
    
    # More realistic stop loss and take profit distances
    sl_distance = atr * 1.0  # Increased from 0.5 to 1.0
    tp_distance = sl_distance * rr_ratio  # Now 2.0 instead of 1.5

    stop_loss = entry - sl_distance if direction == "BUY" else entry + sl_distance
    take_profit = entry + tp_distance if direction == "BUY" else entry - tp_distance

    try:
        future_candles = await get_historical_data(symbol=symbol, interval="1h", days=days_ahead)
        if not future_candles or len(future_candles) < 24:  # Need at least 1 day of data
            print(f"Insufficient future data for {symbol}: got {len(future_candles) if future_candles else 0} candles")
            # Return breakeven if no sufficient data - this is honest
            return TradeResult(entry, stop_loss, take_profit, entry, None, "breakeven", 0.0, 0.0)
    except Exception as e:
        print(f"Error getting future candles for {symbol}: {e}")
        # Return breakeven if data fetch fails - this is honest
        return TradeResult(entry, stop_loss, take_profit, entry, None, "breakeven", 0.0, 0.0)
    for fc in future_candles:
        low = fc["low"]
        high = fc["high"]
        ts = fc["timestamp"]

        if direction == "BUY":
            if low <= stop_loss:
                return TradeResult(entry, stop_loss, take_profit, stop_loss, ts, "stop_loss_hit", -sl_distance, -sl_distance / entry * 100)
            elif high >= take_profit:
                return TradeResult(entry, stop_loss, take_profit, take_profit, ts, "take_profit_hit", tp_distance, tp_distance / entry * 100)
        else:  # SELL
            if high >= stop_loss:
                return TradeResult(entry, stop_loss, take_profit, stop_loss, ts, "stop_loss_hit", -sl_distance, -sl_distance / entry * 100)
            elif low <= take_profit:
                return TradeResult(entry, stop_loss, take_profit, take_profit, ts, "take_profit_hit", tp_distance, tp_distance / entry * 100)

    # No exit found in available data - use REAL final price from data
    print(f"No exit found for {symbol} {direction} trade in {days_ahead} days - using final market price")
    
    # Calculate REAL price movement from entry to last available candle
    if future_candles:
        last_candle = future_candles[-1]
        final_price = last_candle["close"]
        
        # Calculate actual profit/loss based on real market movement
        if direction == "BUY":
            profit_pct = ((final_price - entry) / entry) * 100
        else:  # SELL
            profit_pct = ((entry - final_price) / entry) * 100
        
        profit_usd = (profit_pct / 100) * entry
        result_type = "profit" if profit_pct > 0 else "loss" if profit_pct < 0 else "breakeven"
        
        return TradeResult(entry, stop_loss, take_profit, final_price, last_candle["timestamp"], result_type, profit_usd, profit_pct)
    else:
        # No data available - honest breakeven
        return TradeResult(entry, stop_loss, take_profit, entry, None, "breakeven", 0.0, 0.0)


# === GET CURRENT SIGNAL (for /api/signal/current) ===
from app.services.indicators import compute_indicators
from app.services.candlestick_analyzer import detect_patterns
from app.services.technical_indicators import calculate_professional_indicators
from app.services.ml_signal_generator import generate_ai_signal

async def get_current_signal(symbol: str, interval: str):
    """
    Get current trading signal for a symbol and interval.
    
    Note: This function does not use a 'mode' parameter (scalp, swing).
    Those trading modes are not needed for this implementation.
    """
    # Get more historical data for accurate technical indicators (minimum 200 candles for MA200)
    candles = await get_historical_data(symbol, interval, days=30)
    latest = candles[-1]
    previous = candles[-2] if len(candles) > 1 else None

    # Get current real-time price
    try:
        current_price_data = await get_current_price(symbol)
        current_price = float(current_price_data)
    except:
        current_price = float(latest["close"])

    # Calculate professional technical indicators
    professional_indicators = calculate_professional_indicators(candles)
    
    # Get AI/ML signal for additional intelligence
    try:
        ai_signal_data = await generate_ai_signal(symbol, interval)
        ai_signal = ai_signal_data.get('ai_signal', 'NEUTRAL')
        ai_confidence = ai_signal_data.get('ai_confidence', 50.0)
        ai_risk_score = ai_signal_data.get('risk_score', 50.0)
    except Exception as e:
        print(f"Warning: AI signal generation failed for {symbol}: {e}")
        ai_signal = 'NEUTRAL'
        ai_confidence = 50.0
        ai_risk_score = 50.0
    
    # Keep legacy indicators for compatibility
    indicators = compute_indicators(latest)
    pattern, score = detect_patterns(latest, previous)
    
    # Use current time for live trading signals
    signal_timestamp = datetime.now()

    # Signal generation based on multiple factors with detailed tracking
    signal_score = 0
    decision_factors = {
        "candlestick_pattern": {
            "name": pattern,
            "score": score,
            "signal": "NEUTRAL",
            "reasoning": "No significant pattern detected",
            "weight": 0
        },
        "trend_analysis": {
            "trend": indicators["trend"],
            "signal": "NEUTRAL",
            "reasoning": "Neutral trend detected",
            "weight": 0
        },
        "momentum_strength": {
            "strength": indicators["strength"],
            "signal": "NEUTRAL",
            "reasoning": "Weak momentum detected",
            "weight": 0
        },
        "rsi_analysis": {
            "value": 50,  # Default RSI
            "signal": "NEUTRAL",
            "reasoning": "RSI in neutral zone (30-70)",
            "weight": 0
        },
        "macd_analysis": {
            "value": 0,  # Default MACD
            "signal": "NEUTRAL",
            "reasoning": "MACD showing neutral momentum",
            "weight": 0
        },
        "volume_analysis": {
            "signal": "NEUTRAL",
            "reasoning": "Normal volume levels",
            "weight": 0
        },
        "support_resistance": {
            "signal": "NEUTRAL",
            "reasoning": "Price within normal range",
            "weight": 0
        },
        "ai_ml_analysis": {
            "ai_signal": ai_signal,
            "ai_confidence": ai_confidence,
            "risk_score": ai_risk_score,
            "signal": "NEUTRAL",
            "reasoning": "AI/ML analysis neutral",
            "weight": 0
        }
    }
    
    # Pattern-based signals (if pattern exists)
    if pattern in ["Hammer", "Bullish Engulfing"]:
        signal_score += 2
        decision_factors["candlestick_pattern"]["signal"] = "BUY"
        decision_factors["candlestick_pattern"]["reasoning"] = f"Strong bullish pattern: {pattern}"
        decision_factors["candlestick_pattern"]["weight"] = 2
    elif pattern in ["Shooting Star", "Bearish Engulfing"]:
        signal_score -= 2
        decision_factors["candlestick_pattern"]["signal"] = "SELL"
        decision_factors["candlestick_pattern"]["reasoning"] = f"Strong bearish pattern: {pattern}"
        decision_factors["candlestick_pattern"]["weight"] = -2
    elif pattern == "Doji":
        signal_score += 0  # Neutral
        decision_factors["candlestick_pattern"]["signal"] = "NEUTRAL"
        decision_factors["candlestick_pattern"]["reasoning"] = "Doji pattern indicates indecision"
        decision_factors["candlestick_pattern"]["weight"] = 0
    
    # Trend-based signals
    if indicators["trend"] == "bullish":
        signal_score += 1
        decision_factors["trend_analysis"]["signal"] = "BUY"
        decision_factors["trend_analysis"]["reasoning"] = "Bullish trend detected"
        decision_factors["trend_analysis"]["weight"] = 1
    elif indicators["trend"] == "bearish":
        signal_score -= 1
        decision_factors["trend_analysis"]["signal"] = "SELL"
        decision_factors["trend_analysis"]["reasoning"] = "Bearish trend detected"
        decision_factors["trend_analysis"]["weight"] = -1
    
    # Strength-based signals
    if indicators["strength"] == "strong":
        weight = 1 if indicators["trend"] == "bullish" else -1
        signal_score += weight
        decision_factors["momentum_strength"]["signal"] = "BUY" if weight > 0 else "SELL"
        decision_factors["momentum_strength"]["reasoning"] = f"Strong momentum supporting {indicators['trend']} trend"
        decision_factors["momentum_strength"]["weight"] = weight
    
    # Professional RSI analysis
    rsi_data = professional_indicators.get('rsi', {})
    rsi_value = rsi_data.get('value', 50)
    rsi_signal = rsi_data.get('signal', 'NEUTRAL')
    
    decision_factors["rsi_analysis"]["value"] = rsi_value
    if rsi_signal == "SELL":
        signal_score -= 1
        decision_factors["rsi_analysis"]["signal"] = "SELL"
        decision_factors["rsi_analysis"]["reasoning"] = f"Professional RSI overbought at {rsi_value:.1f}"
        decision_factors["rsi_analysis"]["weight"] = -1
    elif rsi_signal == "BUY":
        signal_score += 1
        decision_factors["rsi_analysis"]["signal"] = "BUY"
        decision_factors["rsi_analysis"]["reasoning"] = f"Professional RSI oversold at {rsi_value:.1f}"
        decision_factors["rsi_analysis"]["weight"] = 1
    else:
        decision_factors["rsi_analysis"]["reasoning"] = f"Professional RSI neutral at {rsi_value:.1f}"
    
    # Professional MACD analysis
    macd_data = professional_indicators.get('macd', {})
    macd_value = macd_data.get('macd', 0)
    macd_signal_type = macd_data.get('signal_type', 'NEUTRAL')
    macd_histogram = macd_data.get('histogram', 0)
    
    decision_factors["macd_analysis"]["value"] = macd_value
    if macd_signal_type == "BUY":
        signal_score += 1
        decision_factors["macd_analysis"]["signal"] = "BUY"
        decision_factors["macd_analysis"]["reasoning"] = f"Professional MACD bullish crossover (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
        decision_factors["macd_analysis"]["weight"] = 1
    elif macd_signal_type == "SELL":
        signal_score -= 1
        decision_factors["macd_analysis"]["signal"] = "SELL"
        decision_factors["macd_analysis"]["reasoning"] = f"Professional MACD bearish crossover (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
        decision_factors["macd_analysis"]["weight"] = -1
    else:
        decision_factors["macd_analysis"]["reasoning"] = f"Professional MACD neutral (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
    
    # Professional Volume analysis
    volume_data = professional_indicators.get('volume', {})
    current_volume = volume_data.get('current', 0)
    volume_trend = volume_data.get('volume_trend', 'NORMAL')
    is_high_volume = volume_data.get('high_volume', False)
    
    if is_high_volume and volume_trend == 'HIGH':
        weight = 1 if signal_score > 0 else -1 if signal_score < 0 else 0
        signal_score += weight
        decision_factors["volume_analysis"]["signal"] = "BUY" if weight > 0 else "SELL" if weight < 0 else "NEUTRAL"
        decision_factors["volume_analysis"]["reasoning"] = f"Professional volume analysis: High volume ({current_volume/1000000:.1f}M) confirms signal"
        decision_factors["volume_analysis"]["weight"] = weight
    else:
        decision_factors["volume_analysis"]["reasoning"] = f"Professional volume analysis: {volume_trend.lower()} volume ({current_volume/1000000:.1f}M)"
    
    # Support/Resistance analysis
    close = latest["close"]
    high = latest["high"]
    low = latest["low"]
    price_position = (close - low) / (high - low) if high != low else 0.5
    if price_position > 0.8:
        signal_score += 1
        decision_factors["support_resistance"]["signal"] = "BUY"
        decision_factors["support_resistance"]["reasoning"] = "Price near resistance, potential breakout"
        decision_factors["support_resistance"]["weight"] = 1
    elif price_position < 0.2:
        signal_score -= 1
        decision_factors["support_resistance"]["signal"] = "SELL"
        decision_factors["support_resistance"]["reasoning"] = "Price near support, potential breakdown"
        decision_factors["support_resistance"]["weight"] = -1
    else:
        decision_factors["support_resistance"]["reasoning"] = "Price in middle range"
    
    # Add Bollinger Bands analysis
    bb_data = professional_indicators.get('bollinger_bands', {})
    bb_breakout = bb_data.get('breakout', 'NONE')
    bb_percent = bb_data.get('percent_b', 0.5)
    
    if bb_breakout == 'UPPER':
        signal_score += 1
        decision_factors["support_resistance"]["signal"] = "BUY"
        decision_factors["support_resistance"]["reasoning"] = f"Bollinger Bands upper breakout (BB%: {bb_percent:.2f})"
        decision_factors["support_resistance"]["weight"] = 1
    elif bb_breakout == 'LOWER':
        signal_score -= 1
        decision_factors["support_resistance"]["signal"] = "SELL"
        decision_factors["support_resistance"]["reasoning"] = f"Bollinger Bands lower breakout (BB%: {bb_percent:.2f})"
        decision_factors["support_resistance"]["weight"] = -1
    
    # AI/ML Signal Analysis - add significant weight for strong AI signals
    if ai_confidence >= 75:  # High confidence AI signal
        if ai_signal == 'BUY':
            ai_weight = 2
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "BUY"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"High confidence AI BUY signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
        elif ai_signal == 'SELL':
            ai_weight = -2
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "SELL"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"High confidence AI SELL signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
    elif ai_confidence >= 60:  # Medium confidence AI signal
        if ai_signal == 'BUY':
            ai_weight = 1
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "BUY"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"Medium confidence AI BUY signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
        elif ai_signal == 'SELL':
            ai_weight = -1
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "SELL"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"Medium confidence AI SELL signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
    else:
        decision_factors["ai_ml_analysis"]["reasoning"] = f"Low confidence AI signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%) - not used"
    
    # Use professional signal strength calculation
    professional_strength = professional_indicators.get('market_assessment', {}).get('signal_strength', 0)
    
    # Combine traditional scoring with professional assessment and AI
    combined_score = (signal_score + professional_strength) // 2
    
    # Determine final direction
    if combined_score > 0:
        direction = "BUY"
    elif combined_score < 0:
        direction = "SELL"
    else:
        direction = "HOLD"

    # Calculate stop loss and take profit for live trading (without simulation)
    entry_price = float(latest["close"])
    
    # Calculate ATR for stop loss/take profit calculation
    try:
        recent_candles = await get_historical_data(symbol=symbol, interval="1h", days=7)
        if len(recent_candles) >= 14:
            # Calculate 14-period ATR
            atr_values = []
            for i in range(1, min(15, len(recent_candles))):
                curr = recent_candles[i]
                prev = recent_candles[i-1]
                tr = max(
                    curr["high"] - curr["low"],
                    abs(curr["high"] - prev["close"]),
                    abs(curr["low"] - prev["close"])
                )
                atr_values.append(tr)
            atr = sum(atr_values) / len(atr_values)
        else:
            atr = latest["high"] - latest["low"]
    except:
        atr = latest["high"] - latest["low"]
    
    # Calculate stop loss and take profit levels for live trading
    sl_distance = atr * 1.0
    tp_distance = sl_distance * 2.0
    
    if direction == "BUY":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    elif direction == "SELL":
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
    else:  # HOLD
        stop_loss = entry_price * 0.98
        take_profit = entry_price * 1.02

    return {
        "symbol": symbol,
        "interval": interval,
        "signal": direction,
        "entry_price": entry_price,
        "current_price": current_price,  # Real-time current price
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "pattern": pattern,  # Send None instead of "None" string
        "score": abs(combined_score),  # Use combined professional + traditional score
        "trend": professional_indicators.get('market_assessment', {}).get('trend', indicators["trend"]),
        "confidence": min(85, max(15, 30 + abs(combined_score) * 8)),  # More realistic confidence: 1 point = 38%, 5 points = 70%
        "timestamp": signal_timestamp.isoformat(),
        "decision_factors": decision_factors,  # Detailed breakdown of decision logic
        "total_score": combined_score,  # Combined professional + traditional + AI score
        "professional_indicators": professional_indicators,  # Full professional analysis
        "ai_signal_data": {  # AI/ML analysis data
            "ai_signal": ai_signal,
            "ai_confidence": ai_confidence,
            "risk_score": ai_risk_score
        }
    }
