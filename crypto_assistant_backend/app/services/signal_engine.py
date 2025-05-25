# app/services/signal_engine.py

from datetime import datetime, timedelta
from typing import Optional
from app.utils.price_data import get_historical_data

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
    candles = await get_historical_data(symbol, interval, days=2)
    latest = candles[-1]

    indicators = compute_indicators(latest)
    pattern, score = detect_patterns(latest)

    direction = "BUY" if pattern in ["Hammer", "Bullish Engulfing"] else "SELL"

    result = await simulate_trade(entry=latest["close"], direction=direction, candle=latest)

    return {
        "symbol": symbol,
        "interval": interval,
        "signal": direction,
        "entry_price": result.entry_price,
        "stop_loss": result.stop_loss,
        "take_profit": result.take_profit,
        "pattern": pattern or "None",
        "score": score,
        "trend": indicators["trend"],
        "confidence": "high" if score >= 3 else "medium"
    }
