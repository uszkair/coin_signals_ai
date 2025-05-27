from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.schema import SignalResponse
from app.services.signal_engine import get_current_signal

router = APIRouter()

@router.get("/", response_model=List[SignalResponse])
async def get_signals(symbols: str, interval: str = "1h"):
    """
    Több szimbólum jelzéseinek lekérése egyszerre.
    symbols: vesszővel elválasztott szimbólumok (pl: BTCUSDT,ETHUSDT)
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        signals = []
        
        for symbol in symbol_list:
            try:
                signal = await get_current_signal(symbol, interval)
                signals.append(signal)
            except Exception as e:
                # Continue with other symbols if one fails
                continue
                
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str, interval: str = "1h"):
    try:
        signal = await get_current_signal(symbol, interval)
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
