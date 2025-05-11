from utils.binance import fetch_binance_data
from services.indicators import (
    calculate_rsi, calculate_ema,
    calculate_macd, calculate_bollinger_bands,
    calculate_stoch_rsi
)
from utils.telegram import send_signal_message

async def get_coin_signal_multi_timeframe(symbol: str):
    # Lekérjük az 1h és a 4h adatsorokat
    df_1h = await fetch_binance_data(symbol, interval="1h", limit=100)
    df_4h = await fetch_binance_data(symbol, interval="4h", limit=100)

    if df_1h is None or df_4h is None:
        print(f"Nincs elég adat: {symbol}")
        return {"symbol": symbol, "error": "Hiányzik valamelyik idősík"}

    # --- 1h indikátorok ---
    df_1h["rsi"] = calculate_rsi(df_1h["close"])
    df_1h["ema20"] = calculate_ema(df_1h["close"], 20)
    df_1h["macd"], df_1h["macd_signal"] = calculate_macd(df_1h["close"])
    df_1h["bb_upper"], df_1h["bb_lower"] = calculate_bollinger_bands(df_1h["close"])
    df_1h["stoch_k"], df_1h["stoch_d"] = calculate_stoch_rsi(df_1h["close"])

    latest_1h = df_1h.iloc[-1]

    # --- 4h EMA a trend megerősítéshez ---
    df_4h["ema20"] = calculate_ema(df_4h["close"], 20)
    latest_4h = df_4h.iloc[-1]

    signal = "HOLD"

    # BUY feltétel: 1h szignál + 4h emelkedő trend
    if (
        latest_1h["rsi"] < 30
        and latest_1h["close"] > latest_1h["ema20"]
        and latest_1h["macd"] > latest_1h["macd_signal"]
        and latest_1h["close"] < latest_1h["bb_lower"]
        and latest_1h["stoch_k"] < 0.2
        and latest_4h["close"] > latest_4h["ema20"]
    ):
        signal = "BUY"

    # SELL feltétel: 1h szignál + 4h csökkenő trend
    elif (
        latest_1h["rsi"] > 70
        and latest_1h["close"] < latest_1h["ema20"]
        and latest_1h["macd"] < latest_1h["macd_signal"]
        and latest_1h["close"] > latest_1h["bb_upper"]
        and latest_1h["stoch_k"] > 0.8
        and latest_4h["close"] < latest_4h["ema20"]
    ):
        signal = "SELL"

    if signal in ("BUY", "SELL"):
        await send_signal_message(
            symbol=symbol,
            price=latest_1h["close"],
            signal=signal,
            rsi=latest_1h["rsi"],
            ema=latest_1h["ema20"]
        )

    return {
        "symbol": symbol,
        "price": float(latest_1h["close"]),
        "rsi": float(latest_1h["rsi"]),
        "ema20": float(latest_1h["ema20"]),
        "ema20_4h": float(latest_4h["ema20"]),
        "signal": signal
    }
