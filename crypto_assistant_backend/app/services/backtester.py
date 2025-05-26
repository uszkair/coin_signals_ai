# app/services/backtester.py

from datetime import datetime, timedelta
from typing import List
from app.models.schema import SignalHistoryItem
from app.services.indicators import compute_indicators
from app.services.candlestick_analyzer import detect_patterns
from app.services.signal_engine import simulate_trade
from app.utils.price_data import get_historical_data

async def get_signal_history(symbol: str, interval: str, days: int) -> List[SignalHistoryItem]:
    candles = await get_historical_data(symbol, interval, days)
    results = []

    for candle in candles:
        timestamp = candle["timestamp"]
        open_price = candle["open"]
        high = candle["high"]
        low = candle["low"]
        close = candle["close"]

        indicators = compute_indicators(candle)
        pattern, score = detect_patterns(candle)

        if pattern and score >= 2:
            trade_result = await simulate_trade(entry=close, direction="BUY", candle=candle)

            results.append(SignalHistoryItem(
                timestamp=timestamp,
                symbol=symbol,
                interval=interval,
                signal="BUY",
                entry_price=trade_result.entry_price,
                stop_loss=trade_result.stop_loss,
                take_profit=trade_result.take_profit,
                exit_price=trade_result.exit_price,
                exit_time=trade_result.exit_time,
                result=trade_result.result,
                timeframe=interval,
                profit_usd=trade_result.profit_usd,
                profit_percent=trade_result.profit_percent,
                pattern=pattern,
                score=score,
                reason=indicators["reason"]
            ))

    return results
