# app/routers/backtest.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.services.backtest_service import backtest_service
from app.services.trading_settings_service import get_trading_settings_service
from app.database import get_db

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    test_name: str
    symbol: str
    days_back: int = 365
    min_confidence: int = 70
    position_size: float = 100.0

class DataFetchRequest(BaseModel):
    symbols: List[str]
    days: int = 365
    force_refresh: bool = False

@router.post("/fetch-data")
async def fetch_historical_data(request: DataFetchRequest, background_tasks: BackgroundTasks):
    """
    Fetch historical data from Coinbase for backtesting
    This runs in the background to avoid timeout
    """
    try:
        # Start the data fetching in background
        background_tasks.add_task(
            backtest_service.fetch_historical_data,
            request.symbols,
            request.days,
            request.force_refresh
        )
        
        return {
            "message": f"Started fetching {request.days} days of data for {len(request.symbols)} symbols",
            "symbols": request.symbols,
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting data fetch: {str(e)}")

@router.get("/data-status/{symbol}")
async def get_data_status(symbol: str):
    """
    Check if historical data exists for a symbol
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        data = await backtest_service.get_backtest_data(symbol, start_date, end_date)
        
        return {
            "symbol": symbol,
            "has_data": len(data) > 0,
            "data_points": len(data),
            "date_range": {
                "start": data[0]["timestamp"] if data else None,
                "end": data[-1]["timestamp"] if data else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking data status: {str(e)}")

@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on historical data
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days_back)
        
        # Run the backtest
        result = await backtest_service.run_backtest(
            test_name=request.test_name,
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            min_confidence=request.min_confidence,
            position_size=request.position_size
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

@router.get("/results")
async def get_backtest_results():
    """
    Get all backtest results
    """
    try:
        results = await backtest_service.get_backtest_results()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching results: {str(e)}")

@router.get("/results/{backtest_id}")
async def get_backtest_details(backtest_id: int):
    """
    Get detailed backtest results including all trades
    """
    try:
        result = await backtest_service.get_backtest_details(backtest_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching backtest details: {str(e)}")

@router.delete("/results/{backtest_id}")
async def delete_backtest(backtest_id: int):
    """
    Delete a backtest and all its trades
    """
    try:
        success = await backtest_service.delete_backtest(backtest_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return {"message": "Backtest deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting backtest: {str(e)}")

@router.get("/symbols")
async def get_available_symbols():
    """
    Get list of symbols that the trading engine actually monitors for backtesting
    """
    try:
        # Get the actual symbols used by the auto trading system
        auto_settings = await trading_settings_service.get_auto_trading_settings()
        monitored_symbols = auto_settings['symbols']
        
        return {
            "symbols": monitored_symbols,
            "source": "auto_trading_settings",
            "description": "Symbols actively monitored by the trading engine"
        }
    except Exception as e:
        # Fallback to default symbols if settings service fails
        return {
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"],
            "source": "fallback",
            "description": "Default symbols (settings service unavailable)"
        }

@router.get("/health")
async def backtest_health():
    """
    Health check for backtest service
    """
    return {
        "status": "healthy",
        "service": "backtest",
        "timestamp": datetime.now().isoformat()
    }