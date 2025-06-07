# app/utils/price_data.py

import httpx
import os
from datetime import datetime, timedelta

# Környezeti változók betöltése
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")

async def get_historical_data(symbol: str, interval: str, days: int):
    limit = min(days * 24, 1000)  # max 1000 gyertya
    endpoint = f"/api/v3/klines"
    url = f"{BINANCE_BASE_URL}{endpoint}"

    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_time,
        "endTime": end_time
    }

    headers = {}
    if BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = BINANCE_API_KEY

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        raw_data = response.json()

    candles = []
    for item in raw_data:
        candles.append({
            "timestamp": datetime.utcfromtimestamp(item[0] / 1000),
            "open": float(item[1]),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
            "volume": float(item[5])
        })

    return candles

async def get_current_price(symbol: str):
    """
    Get current price for a symbol from Binance API
    """
    endpoint = f"/api/v3/ticker/price"
    url = f"{BINANCE_BASE_URL}{endpoint}"
    
    params = {
        "symbol": symbol
    }
    
    headers = {}
    if BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = BINANCE_API_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    
    return float(data["price"])
