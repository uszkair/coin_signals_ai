from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.schema import SignalHistoryItem
from app.services.backtester import get_signal_history

router = APIRouter()

@router.get("/", response_model=List[SignalHistoryItem])
async def get_history(
    symbol: str = "BTCUSDT",
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Kereskedési jelzések előzményeinek lekérése.
    """
    try:
        # Dátumok feldolgozása, ha meg vannak adva
        start = datetime.fromisoformat(start_date) if start_date else datetime.now() - timedelta(days=days)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        
        # Számítsuk ki a napok számát
        days_diff = (end - start).days + 1
        
        history = await get_signal_history(symbol, "1h", days_diff)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade-history", response_model=List[SignalHistoryItem])
async def get_trade_history(
    symbol: Optional[str] = None,
    coinPair: Optional[str] = None,
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Kereskedési előzmények lekérése (alias a get_history-hoz).
    Elfogadja mind a 'symbol' mind a 'coinPair' paramétert.
    """
    # coinPair paramétert előnyben részesítjük, ha meg van adva
    trading_symbol = coinPair or symbol or "BTCUSDT"
    return await get_history(trading_symbol, days, start_date, end_date)
