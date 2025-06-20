# app/services/signal_engine.py

from datetime import datetime, timedelta
from typing import Optional
import random
import logging
from app.utils.price_data import get_historical_data, get_current_price
from app.services.trading_settings_service import get_trading_settings_service
from app.database import get_db

logger = logging.getLogger(__name__)

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

# simulate_trade function removed - no simulation code allowed in live trading system

# === GET CURRENT SIGNAL (for /api/signal/current) ===
from app.services.indicators import compute_indicators
from app.services.candlestick_analyzer import detect_patterns
from app.services.technical_indicators import calculate_professional_indicators
from app.services.ml_signal_generator import generate_ai_signal
from app.services.support_resistance_analyzer import analyze_support_resistance
from app.services.multi_timeframe_analyzer import analyze_multi_timeframe_indicators

async def get_current_signal(symbol: str, interval: str):
    """
    Get current trading signal for a symbol and interval.
    
    Note: This function does not use a 'mode' parameter (scalp, swing).
    Those trading modes are not needed for this implementation.
    """
    # Get settings from database
    try:
        from app.database import get_sync_db
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        
        # Get all relevant settings (these are sync functions, no await needed)
        indicator_weights = settings_service.get_technical_indicator_weights()
        rsi_settings = settings_service.get_rsi_settings()
        macd_settings = settings_service.get_macd_settings()
        bollinger_settings = settings_service.get_bollinger_settings()
        ma_settings = settings_service.get_ma_settings()
        volume_settings = settings_service.get_volume_settings()
        candlestick_settings = settings_service.get_candlestick_settings()
        ai_ml_settings = settings_service.get_ai_ml_settings()
        
    except Exception as e:
        print(f"Warning: Failed to load settings from database: {e}")
        # Use default values
        indicator_weights = {'rsi_weight': 1.0, 'macd_weight': 1.0, 'volume_weight': 1.0, 'candlestick_weight': 2.0, 'bollinger_weight': 1.0, 'ma_weight': 1.0, 'support_resistance_weight': 2.0}
        rsi_settings = {'period': 14, 'overbought': 70, 'oversold': 30}
        macd_settings = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        bollinger_settings = {'period': 20, 'deviation': 2.0}
        ma_settings = {'short_ma': 20, 'long_ma': 50, 'ma_type': 'EMA'}
        volume_settings = {'volume_threshold_multiplier': 1.5, 'high_volume_threshold': 2.0}
        candlestick_settings = {'sensitivity': 'medium', 'min_pattern_score': 0.7}
        ai_ml_settings = {'ai_signal_weight': 2.0, 'ai_confidence_threshold': 60.0}
    
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

    # Calculate professional technical indicators (function only takes candle data)
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
    
    # Get multi-timeframe support/resistance analysis
    try:
        sr_analysis = await analyze_support_resistance(symbol, current_price)
        sr_signals = sr_analysis.get('trading_signals', {})
        nearby_levels = sr_analysis.get('nearby_levels', {'support': [], 'resistance': []})
        price_position = sr_analysis.get('price_position', {})
    except Exception as e:
        print(f"Warning: Support/Resistance analysis failed for {symbol}: {e}")
        sr_analysis = {}
        sr_signals = {}
        nearby_levels = {'support': [], 'resistance': []}
        price_position = {}
    
    # Get multi-timeframe technical indicators analysis
    try:
        mt_analysis = await analyze_multi_timeframe_indicators(symbol)
        mt_signals = mt_analysis.get('multi_timeframe_signals', {})
        mt_overall = mt_signals.get('overall_signal', {})
    except Exception as e:
        print(f"Warning: Multi-timeframe analysis failed for {symbol}: {e}")
        mt_analysis = {}
        mt_signals = {}
        mt_overall = {}
    
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
            "weight": 0,
            "multi_timeframe_analysis": sr_analysis.get('timeframe_analysis', {}),
            "nearby_support": nearby_levels.get('support', []),
            "nearby_resistance": nearby_levels.get('resistance', []),
            "price_position": price_position.get('position', 'neutral')
        },
        "ai_ml_analysis": {
            "ai_signal": ai_signal,
            "ai_confidence": ai_confidence,
            "risk_score": ai_risk_score,
            "signal": "NEUTRAL",
            "reasoning": "AI/ML analysis neutral",
            "weight": 0
        },
        "multi_timeframe_analysis": {
            "signal": "NEUTRAL",
            "reasoning": "Multi-timeframe analysis neutral",
            "weight": 0,
            "rsi_confluence": mt_signals.get('rsi_confluence', {}),
            "macd_confluence": mt_signals.get('macd_confluence', {}),
            "trend_confluence": mt_signals.get('trend_confluence', {}),
            "pattern_confluence": mt_signals.get('pattern_confluence', {}),
            "overall_signal": mt_overall
        }
    }
    
    # Pattern-based signals (if pattern exists) - use database weight
    candlestick_weight = indicator_weights.get('candlestick_weight', 2.0)
    if pattern in ["Hammer", "Bullish Engulfing"]:
        weight = candlestick_weight
        signal_score += weight
        decision_factors["candlestick_pattern"]["signal"] = "BUY"
        decision_factors["candlestick_pattern"]["reasoning"] = f"Strong bullish pattern: {pattern}"
        decision_factors["candlestick_pattern"]["weight"] = weight
    elif pattern in ["Shooting Star", "Bearish Engulfing"]:
        weight = -candlestick_weight
        signal_score += weight
        decision_factors["candlestick_pattern"]["signal"] = "SELL"
        decision_factors["candlestick_pattern"]["reasoning"] = f"Strong bearish pattern: {pattern}"
        decision_factors["candlestick_pattern"]["weight"] = weight
    elif pattern == "Doji":
        signal_score += 0  # Neutral
        decision_factors["candlestick_pattern"]["signal"] = "NEUTRAL"
        decision_factors["candlestick_pattern"]["reasoning"] = "Doji pattern indicates indecision"
        decision_factors["candlestick_pattern"]["weight"] = 0
    
    # Trend-based signals - use MA weight
    ma_weight = indicator_weights.get('ma_weight', 1.0)
    if indicators["trend"] == "bullish":
        signal_score += ma_weight
        decision_factors["trend_analysis"]["signal"] = "BUY"
        decision_factors["trend_analysis"]["reasoning"] = "Bullish trend detected"
        decision_factors["trend_analysis"]["weight"] = ma_weight
    elif indicators["trend"] == "bearish":
        signal_score -= ma_weight
        decision_factors["trend_analysis"]["signal"] = "SELL"
        decision_factors["trend_analysis"]["reasoning"] = "Bearish trend detected"
        decision_factors["trend_analysis"]["weight"] = -ma_weight
    
    # Strength-based signals
    if indicators["strength"] == "strong":
        weight = ma_weight if indicators["trend"] == "bullish" else -ma_weight
        signal_score += weight
        decision_factors["momentum_strength"]["signal"] = "BUY" if weight > 0 else "SELL"
        decision_factors["momentum_strength"]["reasoning"] = f"Strong momentum supporting {indicators['trend']} trend"
        decision_factors["momentum_strength"]["weight"] = weight
    
    # Professional RSI analysis - use database weight
    rsi_weight = indicator_weights.get('rsi_weight', 1.0)
    rsi_data = professional_indicators.get('rsi', {})
    rsi_value = rsi_data.get('value', 50)
    rsi_signal = rsi_data.get('signal', 'NEUTRAL')
    
    decision_factors["rsi_analysis"]["value"] = rsi_value
    if rsi_signal == "SELL":
        signal_score -= rsi_weight
        decision_factors["rsi_analysis"]["signal"] = "SELL"
        decision_factors["rsi_analysis"]["reasoning"] = f"RSI overbought at {rsi_value:.1f} (threshold: {rsi_settings['overbought']})"
        decision_factors["rsi_analysis"]["weight"] = -rsi_weight
    elif rsi_signal == "BUY":
        signal_score += rsi_weight
        decision_factors["rsi_analysis"]["signal"] = "BUY"
        decision_factors["rsi_analysis"]["reasoning"] = f"RSI oversold at {rsi_value:.1f} (threshold: {rsi_settings['oversold']})"
        decision_factors["rsi_analysis"]["weight"] = rsi_weight
    else:
        decision_factors["rsi_analysis"]["reasoning"] = f"RSI neutral at {rsi_value:.1f} (range: {rsi_settings['oversold']}-{rsi_settings['overbought']})"
    
    # Professional MACD analysis - use database weight
    macd_weight = indicator_weights.get('macd_weight', 1.0)
    macd_data = professional_indicators.get('macd', {})
    macd_value = macd_data.get('macd', 0)
    macd_signal_type = macd_data.get('signal_type', 'NEUTRAL')
    macd_histogram = macd_data.get('histogram', 0)
    
    decision_factors["macd_analysis"]["value"] = macd_value
    if macd_signal_type == "BUY":
        signal_score += macd_weight
        decision_factors["macd_analysis"]["signal"] = "BUY"
        decision_factors["macd_analysis"]["reasoning"] = f"MACD bullish crossover (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
        decision_factors["macd_analysis"]["weight"] = macd_weight
    elif macd_signal_type == "SELL":
        signal_score -= macd_weight
        decision_factors["macd_analysis"]["signal"] = "SELL"
        decision_factors["macd_analysis"]["reasoning"] = f"MACD bearish crossover (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
        decision_factors["macd_analysis"]["weight"] = -macd_weight
    else:
        decision_factors["macd_analysis"]["reasoning"] = f"MACD neutral (MACD: {macd_value:.3f}, Histogram: {macd_histogram:.3f})"
    
    # Professional Volume analysis - use database weight
    volume_weight = indicator_weights.get('volume_weight', 1.0)
    volume_data = professional_indicators.get('volume', {})
    current_volume = volume_data.get('current', 0)
    volume_trend = volume_data.get('volume_trend', 'NORMAL')
    is_high_volume = volume_data.get('high_volume', False)
    
    if is_high_volume and volume_trend == 'HIGH':
        weight = volume_weight if signal_score > 0 else -volume_weight if signal_score < 0 else 0
        signal_score += weight
        decision_factors["volume_analysis"]["signal"] = "BUY" if weight > 0 else "SELL" if weight < 0 else "NEUTRAL"
        decision_factors["volume_analysis"]["reasoning"] = f"High volume ({current_volume/1000000:.1f}M) confirms signal (threshold: {volume_settings['high_volume_threshold']}x)"
        decision_factors["volume_analysis"]["weight"] = weight
    else:
        decision_factors["volume_analysis"]["reasoning"] = f"Volume analysis: {volume_trend.lower()} volume ({current_volume/1000000:.1f}M)"
    
    # Multi-timeframe Support/Resistance analysis
    sr_weight = indicator_weights.get('support_resistance_weight', 2.0)  # New weight for S/R analysis
    
    # Analyze based on multi-timeframe support/resistance
    if sr_signals.get('breakout_potential') == 'resistance_test':
        # Price testing strong resistance - potential breakout
        sr_strength = sr_signals.get('signal_strength', 0)
        if sr_strength >= 4:  # Very strong resistance
            weight = sr_weight * 1.5  # Strong signal for breakout
            signal_score += weight
            decision_factors["support_resistance"]["signal"] = "BUY"
            decision_factors["support_resistance"]["reasoning"] = f"Price testing very strong multi-timeframe resistance (strength: {sr_strength}) - breakout potential"
            decision_factors["support_resistance"]["weight"] = weight
        elif sr_strength >= 2:  # Moderate resistance
            weight = sr_weight * 0.5
            signal_score += weight
            decision_factors["support_resistance"]["signal"] = "BUY"
            decision_factors["support_resistance"]["reasoning"] = f"Price testing multi-timeframe resistance (strength: {sr_strength}) - potential breakout"
            decision_factors["support_resistance"]["weight"] = weight
    
    elif sr_signals.get('breakout_potential') == 'support_test':
        # Price testing strong support - potential bounce
        sr_strength = sr_signals.get('signal_strength', 0)
        if sr_strength >= 4:  # Very strong support
            weight = sr_weight * 1.5  # Strong signal for bounce
            signal_score += weight
            decision_factors["support_resistance"]["signal"] = "BUY"
            decision_factors["support_resistance"]["reasoning"] = f"Price testing very strong multi-timeframe support (strength: {sr_strength}) - bounce potential"
            decision_factors["support_resistance"]["weight"] = weight
        elif sr_strength >= 2:  # Moderate support
            weight = sr_weight * 0.5
            signal_score += weight
            decision_factors["support_resistance"]["signal"] = "BUY"
            decision_factors["support_resistance"]["reasoning"] = f"Price testing multi-timeframe support (strength: {sr_strength}) - potential bounce"
            decision_factors["support_resistance"]["weight"] = weight
    
    elif price_position.get('position') == 'near_resistance':
        # Price near resistance but not testing yet
        if nearby_levels.get('resistance'):
            strongest_resistance = max(nearby_levels['resistance'], key=lambda x: x.get('strength', 0))
            resistance_strength = strongest_resistance.get('strength', 0)
            if resistance_strength >= 3:
                weight = -sr_weight * 0.5  # Negative signal - resistance ahead
                signal_score += weight
                decision_factors["support_resistance"]["signal"] = "SELL"
                decision_factors["support_resistance"]["reasoning"] = f"Price approaching strong resistance at {strongest_resistance.get('price', 0):.2f} (strength: {resistance_strength})"
                decision_factors["support_resistance"]["weight"] = weight
    
    elif price_position.get('position') == 'near_support':
        # Price near support - potential bounce area
        if nearby_levels.get('support'):
            strongest_support = max(nearby_levels['support'], key=lambda x: x.get('strength', 0))
            support_strength = strongest_support.get('strength', 0)
            if support_strength >= 3:
                weight = sr_weight * 0.5  # Positive signal - support nearby
                signal_score += weight
                decision_factors["support_resistance"]["signal"] = "BUY"
                decision_factors["support_resistance"]["reasoning"] = f"Price near strong support at {strongest_support.get('price', 0):.2f} (strength: {support_strength})"
                decision_factors["support_resistance"]["weight"] = weight
    
    else:
        # Default case - analyze general position
        if price_position.get('position') == 'middle_range':
            decision_factors["support_resistance"]["reasoning"] = "Price in middle range between support and resistance levels"
        elif price_position.get('position') == 'above_all_resistance':
            decision_factors["support_resistance"]["reasoning"] = "Price above all known resistance levels - strong bullish territory"
            signal_score += sr_weight * 0.5
            decision_factors["support_resistance"]["signal"] = "BUY"
            decision_factors["support_resistance"]["weight"] = sr_weight * 0.5
        elif price_position.get('position') == 'below_all_support':
            decision_factors["support_resistance"]["reasoning"] = "Price below all known support levels - weak bearish territory"
            signal_score -= sr_weight * 0.5
            decision_factors["support_resistance"]["signal"] = "SELL"
            decision_factors["support_resistance"]["weight"] = -sr_weight * 0.5
        else:
            decision_factors["support_resistance"]["reasoning"] = "Multi-timeframe support/resistance analysis neutral"
    
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
    
    # AI/ML Signal Analysis - use database settings for weight and threshold
    ai_signal_weight = ai_ml_settings.get('ai_signal_weight', 2.0)
    ai_confidence_threshold = ai_ml_settings.get('ai_confidence_threshold', 60.0)
    
    if ai_confidence >= 75:  # High confidence AI signal
        if ai_signal == 'BUY':
            ai_weight = ai_signal_weight
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "BUY"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"High confidence AI BUY signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
        elif ai_signal == 'SELL':
            ai_weight = -ai_signal_weight
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "SELL"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"High confidence AI SELL signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
    elif ai_confidence >= ai_confidence_threshold:  # Medium confidence AI signal - use database threshold
        if ai_signal == 'BUY':
            ai_weight = ai_signal_weight * 0.5  # Half weight for medium confidence
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "BUY"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"Medium confidence AI BUY signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
        elif ai_signal == 'SELL':
            ai_weight = -ai_signal_weight * 0.5  # Half weight for medium confidence
            signal_score += ai_weight
            decision_factors["ai_ml_analysis"]["signal"] = "SELL"
            decision_factors["ai_ml_analysis"]["reasoning"] = f"Medium confidence AI SELL signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%)"
            decision_factors["ai_ml_analysis"]["weight"] = ai_weight
    else:
        decision_factors["ai_ml_analysis"]["reasoning"] = f"Low confidence AI signal ({ai_confidence:.1f}%, Risk: {ai_risk_score:.1f}%) - below threshold ({ai_confidence_threshold}%)"
    
    # Multi-timeframe analysis weight
    mt_weight = indicator_weights.get('multi_timeframe_weight', 1.5)
    if mt_overall and isinstance(mt_overall, dict):
        mt_signal = mt_overall.get('signal', 'NEUTRAL')
        mt_confidence = mt_overall.get('confidence', 0)
        
        if mt_signal in ['STRONG_BUY', 'BUY'] and mt_confidence >= 60:
            weight = mt_weight * (1.5 if mt_signal == 'STRONG_BUY' else 1.0)
            signal_score += weight
            decision_factors["multi_timeframe_analysis"]["signal"] = mt_signal
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe confluence: {mt_signals.get('confluence_score', 0):.2f}, Confidence: {mt_confidence:.1f}%"
            decision_factors["multi_timeframe_analysis"]["weight"] = weight
        elif mt_signal in ['STRONG_SELL', 'SELL'] and mt_confidence >= 60:
            weight = -mt_weight * (1.5 if mt_signal == 'STRONG_SELL' else 1.0)
            signal_score += weight
            decision_factors["multi_timeframe_analysis"]["signal"] = mt_signal
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe confluence: {mt_signals.get('confluence_score', 0):.2f}, Confidence: {mt_confidence:.1f}%"
            decision_factors["multi_timeframe_analysis"]["weight"] = weight
        else:
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe analysis: {mt_signal} (Confidence: {mt_confidence:.1f}% - below threshold)"
    elif isinstance(mt_overall, str):
        # Handle string format
        if mt_overall in ['STRONG_BUY', 'BUY']:
            weight = mt_weight * (1.5 if mt_overall == 'STRONG_BUY' else 1.0)
            signal_score += weight
            decision_factors["multi_timeframe_analysis"]["signal"] = mt_overall
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe confluence: {mt_signals.get('confluence_score', 0):.2f}"
            decision_factors["multi_timeframe_analysis"]["weight"] = weight
        elif mt_overall in ['STRONG_SELL', 'SELL']:
            weight = -mt_weight * (1.5 if mt_overall == 'STRONG_SELL' else 1.0)
            signal_score += weight
            decision_factors["multi_timeframe_analysis"]["signal"] = mt_overall
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe confluence: {mt_signals.get('confluence_score', 0):.2f}"
            decision_factors["multi_timeframe_analysis"]["weight"] = weight
        else:
            decision_factors["multi_timeframe_analysis"]["reasoning"] = f"Multi-timeframe analysis: {mt_overall}"
    else:
        decision_factors["multi_timeframe_analysis"]["reasoning"] = "Multi-timeframe analysis neutral or unavailable"
    
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

    # Calculate stop loss and take profit for live trading
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
    
    # Get user settings for stop loss and take profit calculation
    try:
        db = next(get_db())
        settings_service = get_trading_settings_service(db)
        sl_tp_settings = settings_service.get_stop_loss_take_profit_settings()
        
        if sl_tp_settings['use_atr_based_sl_tp']:
            # Use ATR-based calculation with user-defined multipliers
            sl_distance = atr * sl_tp_settings['atr_multiplier_sl']
            tp_distance = atr * sl_tp_settings['atr_multiplier_tp']
        else:
            # Use percentage-based calculation
            sl_distance = entry_price * sl_tp_settings['stop_loss_percentage']
            tp_distance = entry_price * sl_tp_settings['take_profit_percentage']
        
        db.close()
    except Exception as e:
        logger.warning(f"Could not get user settings, using defaults: {e}")
        # Fallback to default values
        sl_distance = atr * 1.0
        tp_distance = atr * 2.0
    
    # Calculate stop loss and take profit levels for live trading
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
        "confidence": min(95, max(25, 40 + abs(combined_score) * 12)),  # Improved confidence: 1 point = 52%, 3 points = 76%, 5 points = 100%
        "timestamp": signal_timestamp.isoformat(),
        "decision_factors": decision_factors,  # Detailed breakdown of decision logic
        "total_score": combined_score,  # Combined professional + traditional + AI score
        "professional_indicators": professional_indicators,  # Full professional analysis
        "ai_signal_data": {  # AI/ML analysis data
            "ai_signal": ai_signal,
            "ai_confidence": ai_confidence,
            "risk_score": ai_risk_score
        },
        "support_resistance_analysis": sr_analysis  # Full multi-timeframe S/R analysis
    }
