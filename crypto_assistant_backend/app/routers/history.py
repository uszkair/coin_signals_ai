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

@router.get("/trade-history")
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
    Kereskedési előzmények lekérése adatbázisból - INCLUDES FAILURE REASONS.
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
        
        # USE TRADING HISTORY METHOD THAT INCLUDES FAILURE REASONS
        trading_history = await DatabaseService.get_trading_history(
            db=db,
            symbol=trading_symbol,
            start_date=start_date,
            end_date=end_date,
            trade_result=None,  # Get all results including failed_order
            testnet_mode=None,  # Get both testnet and mainnet
            limit=1000
        )
        
        # Convert to the expected format for frontend
        formatted_history = []
        for trade in trading_history:
            formatted_trade = {
                "id": trade["id"],
                "timestamp": trade["entry_time"],
                "symbol": trade["symbol"],
                "interval": "1h",  # Default interval
                "signal": trade["signal"],
                "entry_price": trade["entry_price"],
                "stop_loss": trade["stop_loss"],
                "take_profit": trade["take_profit"],
                "exit_price": trade["exit_price"],
                "exit_time": trade["exit_time"],
                "result": trade["trade_result"],
                "timeframe": "1h",
                "profit_usd": trade["profit_loss_usd"],
                "profit_percent": trade["profit_loss_percentage"],
                "pattern": trade["pattern"],
                "score": trade["confidence"],
                "reason": trade["failure_reason"] if trade["failure_reason"] else f"Confidence: {trade['confidence']}%",
                "failure_reason": trade["failure_reason"]  # Add explicit failure_reason field
            }
            formatted_history.append(formatted_trade)
        
        return formatted_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
