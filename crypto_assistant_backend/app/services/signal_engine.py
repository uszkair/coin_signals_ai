# app/services/signal_engine.py

from datetime import datetime, timedelta
from typing import Optional
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
                         rr_ratio: float = 1.5, days_ahead: int = 3) -> TradeResult:
    atr = candle["high"] - candle["low"]
    sl_distance = atr * 0.5
    tp_distance = sl_distance * rr_ratio

    stop_loss = entry - sl_distance if direction == "BUY" else entry + sl_distance
    take_profit = entry + tp_distance if direction == "BUY" else entry - tp_distance

    future_candles = await get_historical_data(symbol="BTCUSDT", interval="1h", days=days_ahead)
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

    return TradeResult(entry, stop_loss, take_profit, None, None, "none", 0.0, 0.0)


# === GET CURRENT SIGNAL (for /api/signal/current) ===
from app.services.indicators import compute_indicators
from app.services.candlestick_analyzer import detect_patterns

async def get_current_signal(symbol: str, interval: str):
    """
    Get current trading signal for a symbol and interval.
    
    Note: This function does not use a 'mode' parameter (scalp, swing).
    Those trading modes are not needed for this implementation.
    """
    candles = await get_historical_data(symbol, interval, days=2)
    latest = candles[-1]

    # Get current real-time price
    current_price_data = await get_current_price(symbol)
    current_price = current_price_data["price"]

    indicators = compute_indicators(latest)
    pattern, score = detect_patterns(latest)

    direction = "BUY" if pattern in ["Hammer", "Bullish Engulfing"] else "SELL"

    result = await simulate_trade(entry=latest["close"], direction=direction, candle=latest)

    return {
        "symbol": symbol,
        "interval": interval,
        "signal": direction,
        "entry_price": result.entry_price,
        "current_price": current_price,  # Real-time current price
        "stop_loss": result.stop_loss,
        "take_profit": result.take_profit,
        "pattern": pattern,  # Send None instead of "None" string
        "score": score,
        "trend": indicators["trend"],
        "confidence": 85 if score >= 3 else 65,  # Percentage as number
        "timestamp": datetime.now()
    }
