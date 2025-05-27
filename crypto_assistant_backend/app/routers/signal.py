from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.schema import SignalResponse
from app.services.signal_engine import get_current_signal

router = APIRouter()

@router.get("/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str, interval: str = "1h"):
    try:
        signal = await get_current_signal(symbol, interval)
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
