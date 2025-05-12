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
from services.candlestick_analyzer import analyze_candlesticks
from services.signal_backtester import backtest_signals

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

@app.get("/api/candlestick-analysis/{symbol}")
async def candlestick_analysis(
    symbol: str,
    interval: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, description="Number of candles to fetch")
):
    """Get candlestick pattern analysis for a specific symbol and timeframe"""
    df = await get_coin_data(symbol, interval, limit)
    if df is None:
        return {"error": "No data available"}
    
    try:
        # Analyze candlestick patterns
        result = analyze_candlesticks(df)
        
        # Add symbol and interval information
        result["symbol"] = symbol
        result["interval"] = interval
        
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "interval": interval}

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

@app.get("/api/history/month/{year}/{month}")
async def signal_history_month(year: int, month: int):
    """Get signal history for an entire month (format: YYYY/MM)"""
    try:
        # Validate month
        if month < 1 or month > 12:
            return {"error": "Invalid month. Must be between 1 and 12."}
            
        # Get all signals for the month
        all_signals = []
        
        # Get days in month
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Loop through each day in the month
        for day in range(1, days_in_month + 1):
            # Format date as YYYYMMDD
            date_str = f"{year}{month:02d}{day:02d}"
            json_file = f"logs/signals_{date_str}.json"
            
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    try:
                        signals = json.load(f)
                        all_signals.extend(signals)
                    except json.JSONDecodeError:
                        # Skip invalid JSON files
                        continue
        
        return all_signals
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/backtest")
async def backtest(
    symbol: str = Query("BTCUSDT", description="Trading pair symbol"),
    interval: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    lookback_days: int = Query(30, description="Number of days to look back"),
    risk_reward_ratio: float = Query(1.5, description="Risk-to-reward ratio")
):
    """Backtest trading signals on historical data"""
    try:
        # Run the backtest
        signals = await backtest_signals(symbol, interval, lookback_days, risk_reward_ratio)
        
        if isinstance(signals, dict) and "error" in signals:
            return {"error": signals["error"]}
        
        # Calculate summary statistics
        total_signals = len(signals)
        if total_signals == 0:
            return {"message": "No signals found in the specified period.", "signals": []}
        
        buy_signals = sum(1 for s in signals if s["signal"] == "BUY")
        sell_signals = sum(1 for s in signals if s["signal"] == "SELL")
        
        tp_hits = sum(1 for s in signals if s["outcome"] == "take_profit_hit")
        sl_hits = sum(1 for s in signals if s["outcome"] == "stop_loss_hit")
        undecided = sum(1 for s in signals if s["outcome"] == "undecided")
        
        win_rate = tp_hits / (tp_hits + sl_hits) * 100 if (tp_hits + sl_hits) > 0 else 0
        
        # Calculate profit factor
        profit_factor = 0
        if sl_hits > 0:
            profit_factor = (tp_hits * risk_reward_ratio) / sl_hits
        
        # Calculate expectancy
        expectancy = 0
        if (tp_hits + sl_hits) > 0:
            expectancy = ((win_rate / 100) * risk_reward_ratio) - ((1 - win_rate / 100) * 1)
        
        # Return results
        return {
            "summary": {
                "symbol": symbol,
                "interval": interval,
                "lookback_days": lookback_days,
                "risk_reward_ratio": risk_reward_ratio,
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "take_profit_hits": tp_hits,
                "stop_loss_hits": sl_hits,
                "undecided": undecided,
                "win_rate": round(win_rate, 2),
                "profit_factor": round(profit_factor, 2),
                "expectancy": round(expectancy, 2)
            },
            "signals": signals
        }
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
