import httpx
import pandas as pd

async def fetch_market_data(coin_id: str, vs_currency='usd', days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "hourly"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            print("API hiba:", response.status_code)
            return None
        data = response.json()

    prices = data.get("prices", [])
    if not prices:
        print("Üres prices tömb jött vissza!")
        return None

    print(f"Lekért adatpontok száma: {len(prices)}")

    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df
