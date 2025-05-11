import httpx
import pandas as pd

async def fetch_binance_data(symbol: str, interval: str = "1h", limit: int = 100):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            print(f"Hiba {response.status_code} - hibás kérés a szimbólumra: {symbol} ({interval})")
            return None
        data = response.json()

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])

    df["timestamp"] = pd.to_datetime(df["close_time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df.set_index("timestamp", inplace=True)
    return df[["close"]]
