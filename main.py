from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import uvicorn
import pandas as pd
import json
from scheduler import start_scheduler, WATCHED_SYMBOLS

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create directory for React frontend if it doesn't exist
os.makedirs("static/dist", exist_ok=True)

app = FastAPI(
    title="Crypto Trading Assistant API",
    description="AI-alapú kriptokereskedési asszisztens API",
    version="1.0.0"
)

# CORS engedélyezés React frontendhez
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],  # Development mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import services
from services.market_data import (
    get_coin_signal,
    get_coin_signal_multi_timeframe,
    get_all_signals,
    get_coin_data
)

# Endpoints
@app.get("/")
async def root():
    return {"message": "Crypto Trading Assistant API is running"}

@app.get("/api/signal/{symbol}")
async def signal(
    symbol: str,
    interval: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    mode: str = Query("swing", description="Trading mode (scalp, swing)")
):
    """Get trading signal for a specific symbol and timeframe"""
    return await get_coin_signal(symbol, interval, mode)

@app.get("/api/signal-mtf/{symbol}")
async def signal_mtf(
    symbol: str,
    mode: str = Query("swing", description="Trading mode (scalp, swing)")
):
    """Get multi-timeframe trading signal for a specific symbol"""
    return await get_coin_signal_multi_timeframe(symbol, mode)

@app.get("/api/signals")
async def signals(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols to check"),
    interval: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    mode: str = Query("swing", description="Trading mode (scalp, swing)")
):
    """Get trading signals for multiple symbols"""
    # Convert comma-separated string to list if provided
    symbol_list = symbols.split(',') if symbols else None
    return await get_all_signals(symbol_list, interval, mode)

@app.get("/api/marketdata/{symbol}")
async def marketdata(
    symbol: str,
    interval: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, description="Number of candles to fetch")
):
    """Get market data with indicators for a specific symbol and timeframe"""
    df = await get_coin_data(symbol, interval, limit)
    if df is None:
        return {"error": "No data available"}
    
    # Convert DataFrame to dict for JSON response
    result = []
    for idx, row in df.iterrows():
        entry = {
            "timestamp": idx.isoformat(),
            "close": float(row["close"]),
            "rsi": float(row["rsi"]) if not pd.isna(row["rsi"]) else None,
            "ema20": float(row["ema20"]) if not pd.isna(row["ema20"]) else None,
            "ema50": float(row["ema50"]) if not pd.isna(row["ema50"]) else None,
            "macd": float(row["macd"]) if not pd.isna(row["macd"]) else None,
            "macd_signal": float(row["macd_signal"]) if not pd.isna(row["macd_signal"]) else None,
            "bb_upper": float(row["bb_upper"]) if not pd.isna(row["bb_upper"]) else None,
            "bb_lower": float(row["bb_lower"]) if not pd.isna(row["bb_lower"]) else None,
        }
        result.append(entry)
    
    return result

@app.get("/api/symbols")
async def get_symbols():
    """Get list of watched symbols"""
    return {"symbols": WATCHED_SYMBOLS}

@app.get("/api/history/{date}")
async def signal_history(date: str):
    """Get signal history for a specific date (format: YYYYMMDD)"""
    try:
        json_file = f"logs/signals_{date}.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                signals = json.load(f)
            return signals
        else:
            return []
    except Exception as e:
        return {"error": str(e)}

# Mount static files for React frontend
# In production, this would serve the built React app
app.mount("/", StaticFiles(directory="static/dist", html=True), name="static")

# Start the scheduler when the app starts
@app.on_event("startup")
async def startup_event():
    start_scheduler()

# Run the app if executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
