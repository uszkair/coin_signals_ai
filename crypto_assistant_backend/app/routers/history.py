from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema import SignalHistoryItem
from app.services.database_service import DatabaseService
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[SignalHistoryItem])
async def get_history(
    symbol: str = "BTCUSDT",
    days: int = 7,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Kereskedési jelzések előzményeinek lekérése adatbázisból.
    Alapértelmezetten 7 nap (1 hét), maximum 30 nap.
    """
    try:
        # Maximum 30 napra korlátozzuk a teljesítmény miatt
        if days > 30:
            days = 30
            
        # Dátumok feldolgozása, ha meg vannak adva
        start = datetime.fromisoformat(start_date) if start_date else datetime.now() - timedelta(days=days)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        
        # Adatbázisból történeti signalok lekérése
        history = await DatabaseService.get_historical_signals(
            db=db,
            symbol=symbol,
            start_date=start,
            end_date=end,
            limit=1000
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade-history", response_model=List[SignalHistoryItem])
async def get_trade_history(
    symbol: Optional[str] = None,
    coinPair: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    type: Optional[str] = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Kereskedési előzmények lekérése adatbázisból.
    Elfogadja mind a 'symbol' mind a 'coinPair' paramétert.
    Alapértelmezetten 7 nap (1 hét), maximum 30 nap.
    """
    try:
        # coinPair paramétert előnyben részesítjük, ha meg van adva
        trading_symbol = coinPair or symbol
        
        # Maximum 30 napra korlátozzuk a teljesítmény miatt
        if days > 30:
            days = 30
            
        # Dátumok feldolgozása
        start_date = None
        end_date = None
        
        if startDate:
            start_date = datetime.fromisoformat(startDate)
        elif not startDate and not endDate:
            start_date = datetime.now() - timedelta(days=days)
            
        if endDate:
            end_date = datetime.fromisoformat(endDate)
        elif not endDate and not startDate:
            end_date = datetime.now()
        
        # Adatbázisból történeti signalok lekérése
        history = await DatabaseService.get_historical_signals(
            db=db,
            symbol=trading_symbol,
            start_date=start_date,
            end_date=end_date,
            signal_type=type,
            limit=1000
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
