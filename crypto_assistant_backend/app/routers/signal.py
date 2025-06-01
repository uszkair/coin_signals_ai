from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.schema import SignalResponse
from app.services.signal_engine import get_current_signal
from app.services.fallback_service import fallback_service

# Try to import database services
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.database_service import DatabaseService
    from app.database import get_db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Database not available, using fallback service")

router = APIRouter()

@router.get("/", response_model=List[SignalResponse])
async def get_signals(symbols: str, interval: str = "1h", db=None):
    """
    Több szimbólum jelzéseinek lekérése egyszerre.
    symbols: vesszővel elválasztott szimbólumok (pl: BTCUSDT,ETHUSDT)
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        signals = []
        
        if DATABASE_AVAILABLE and db is not None:
            # Database mode
            try:
                # First try to get recent signals from database
                db_signals = await DatabaseService.get_signals_by_symbols(db, symbol_list, interval, hours=1)
                db_signal_symbols = {signal.symbol for signal in db_signals}
                
                # Add database signals
                for db_signal in db_signals:
                    signals.append(db_signal.to_dict())
                
                # Generate new signals for symbols not in database or outdated
                for symbol in symbol_list:
                    if symbol not in db_signal_symbols:
                        try:
                            # Generate new signal
                            signal_data = await get_current_signal(symbol, interval)
                            
                            # Save to database
                            await DatabaseService.save_signal(db, signal_data)
                            
                            signals.append(signal_data)
                        except Exception as e:
                            print(f"Error generating signal for {symbol}: {e}")
                            continue
            except Exception as e:
                print(f"Database error, falling back to cache: {e}")
                # Fall back to cache mode
                DATABASE_AVAILABLE = False
        
        if not DATABASE_AVAILABLE:
            # Fallback mode - use cache
            cached_signals = fallback_service.get_signals_by_symbols(symbol_list, interval)
            cached_symbols = {signal.get('symbol') for signal in cached_signals}
            
            # Add cached signals
            signals.extend(cached_signals)
            
            # Generate new signals for missing symbols
            for symbol in symbol_list:
                if symbol not in cached_symbols:
                    try:
                        signal_data = await get_current_signal(symbol, interval)
                        fallback_service.add_signal(signal_data)
                        signals.append(signal_data)
                    except Exception as e:
                        print(f"Error generating signal for {symbol}: {e}")
                        continue
                
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str, interval: str = "1h", db=None):
    try:
        if DATABASE_AVAILABLE and db is not None:
            # Database mode
            try:
                recent_signals = await DatabaseService.get_recent_signals(
                    db, hours=1, symbol=symbol, limit=1
                )
                
                if recent_signals:
                    return recent_signals[0].to_dict()
                
                # Generate new signal if not found in database
                signal_data = await get_current_signal(symbol, interval)
                
                # Save to database
                await DatabaseService.save_signal(db, signal_data)
                
                return signal_data
            except Exception as e:
                print(f"Database error, using fallback: {e}")
        
        # Fallback mode
        recent_signals = fallback_service.get_recent_signals(hours=1, symbol=symbol, limit=1)
        
        if recent_signals:
            return recent_signals[0]
        
        # Generate new signal
        signal_data = await get_current_signal(symbol, interval)
        fallback_service.add_signal(signal_data)
        
        return signal_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}", response_model=List[SignalResponse])
async def get_signal_history(
    symbol: str,
    hours: int = 24,
    limit: int = 50,
    db=None
):
    """Get signal history for a specific symbol"""
    try:
        if DATABASE_AVAILABLE and db is not None:
            # Database mode
            signals = await DatabaseService.get_recent_signals(
                db, hours=hours, symbol=symbol, limit=limit
            )
            return [signal.to_dict() for signal in signals]
        else:
            # Fallback mode
            signals = fallback_service.get_recent_signals(hours=hours, symbol=symbol, limit=limit)
            return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{symbol}")
async def get_signal_stats(symbol: str, days: int = 7, db=None):
    """Get signal statistics for a symbol"""
    try:
        if DATABASE_AVAILABLE and db is not None:
            # Database mode
            stats = await DatabaseService.get_signal_statistics(db, symbol=symbol, days=days)
            return stats
        else:
            # Fallback mode - basic stats
            signals = fallback_service.get_recent_signals(hours=days*24, symbol=symbol)
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s.get('signal_type') == 'BUY'])
            sell_signals = len([s for s in signals if s.get('signal_type') == 'SELL'])
            
            return {
                "symbol": symbol,
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "days": days
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/all")
async def get_all_signal_stats(days: int = 7, db=None):
    """Get overall signal statistics"""
    try:
        if DATABASE_AVAILABLE and db is not None:
            # Database mode
            stats = await DatabaseService.get_signal_statistics(db, days=days)
            return stats
        else:
            # Fallback mode - basic stats
            signals = fallback_service.get_recent_signals(hours=days*24)
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s.get('signal_type') == 'BUY'])
            sell_signals = len([s for s in signals if s.get('signal_type') == 'SELL'])
            
            # Group by symbol
            symbols = {}
            for signal in signals:
                symbol = signal.get('symbol')
                if symbol not in symbols:
                    symbols[symbol] = {'total': 0, 'buy': 0, 'sell': 0}
                symbols[symbol]['total'] += 1
                if signal.get('signal_type') == 'BUY':
                    symbols[symbol]['buy'] += 1
                elif signal.get('signal_type') == 'SELL':
                    symbols[symbol]['sell'] += 1
            
            return {
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "days": days,
                "symbols": symbols
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
