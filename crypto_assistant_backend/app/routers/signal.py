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
    DATABASE_AVAILABLE = True  # Use database instead of fallback
except ImportError:
    DATABASE_AVAILABLE = False
    AsyncSession = None
    get_db = None
    print("Database not available, using fallback service")

router = APIRouter()

if DATABASE_AVAILABLE:
    @router.get("/")
    async def get_signals(symbols: str, interval: str = "1h", db: AsyncSession = Depends(get_db)):
        """
        Trading signals lekérése adatbázisból.
        Ha nincs signal az adatbázisban, üres listát ad vissza.
        symbols: vesszővel elválasztott szimbólumok (pl: BTCUSDT,ETHUSDT)
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            signals = []
            
            # Ellenőrizzük az adatbázist minden szimbólumra
            for symbol in symbol_list:
                try:
                    recent_signals = await DatabaseService.get_recent_signals(
                        db, hours=72, symbol=symbol, limit=1
                    )
                    
                    if recent_signals:
                        # Van signal az adatbázisban
                        signal_dict = recent_signals[0].to_dict()
                        signals.append(signal_dict)
                    # Ha nincs signal, nem adunk hozzá semmit
                        
                except Exception as db_error:
                    print(f"Database error for {symbol}: {db_error}")
                    # Adatbázis hiba esetén sem adunk hozzá semmit
                    continue
                    
            return signals
            
        except Exception as e:
            print(f"Error in get_signals: {e}")
            # Ha minden hibázik, üres lista
            return []
else:
    @router.get("/", response_model=List[SignalResponse])
    async def get_signals(symbols: str, interval: str = "1h"):
        """
        Több szimbólum jelzéseinek lekérése egyszerre.
        symbols: vesszővel elválasztott szimbólumok (pl: BTCUSDT,ETHUSDT)
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            signals = []
            
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
                    except ValueError as e:
                        # Skip unsupported symbols but log the validation error
                        print(f"Validation error for {symbol}: {e}")
                        continue
                    except Exception as e:
                        print(f"Error generating signal for {symbol}: {e}")
                        continue
                    
            return signals
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if DATABASE_AVAILABLE:
    @router.get("/current")
    async def get_current_signal_live(symbol: str, interval: str = "1h", save_to_db: bool = False, db: AsyncSession = Depends(get_db)):
        """
        Generate a fresh signal in real-time
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            save_to_db: Whether to save signal to database (default: False - only save when explicitly requested)
        """
        try:
            # Generate fresh signal using signal engine
            signal_data = await get_current_signal(symbol, interval)
            
            # Only save signals to database when explicitly requested (e.g., for trading)
            if save_to_db:
                try:
                    await DatabaseService.save_signal(db, signal_data)
                    print(f"✅ Signal saved to database: {symbol} - {signal_data.get('signal', 'N/A')}")
                except Exception as save_error:
                    print(f"Warning: Could not save signal to database: {save_error}")
            else:
                print(f"📊 Signal generated for {symbol} (display only - not saved)")
            
            return signal_data
            
        except ValueError as e:
            # Handle validation errors (like unsupported symbols) with 400 Bad Request
            error_msg = str(e)
            print(f"Validation error for {symbol}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            # Handle other errors with 500 Internal Server Error
            print(f"Error generating current signal for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")

    @router.get("/{symbol}")
    async def get_signal(symbol: str, interval: str = "1h", db: AsyncSession = Depends(get_db)):
        try:
            # Database mode - csak lekérés, nincs generálás
            try:
                recent_signals = await DatabaseService.get_recent_signals(
                    db, hours=24, symbol=symbol, limit=1
                )
                
                if recent_signals:
                    return recent_signals[0].to_dict()
                else:
                    # Ha nincs signal az adatbázisban, üres válasz
                    print(f"No signal found for {symbol} in database, returning empty response")
                    raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")
                    
            except HTTPException:
                raise
            except Exception as e:
                print(f"Database error for {symbol}: {e}")
                raise HTTPException(status_code=500, detail="Database error")
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in get_signal: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/history/{symbol}", response_model=List[SignalResponse])
    async def get_signal_history(
        symbol: str,
        hours: int = 24,
        limit: int = 50,
        db: AsyncSession = Depends(get_db)
    ):
        """Get signal history for a specific symbol"""
        try:
            # Database mode
            signals = await DatabaseService.get_recent_signals(
                db, hours=hours, symbol=symbol, limit=limit
            )
            return [signal.to_dict() for signal in signals]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats/{symbol}")
    async def get_signal_stats(symbol: str, days: int = 7, db: AsyncSession = Depends(get_db)):
        """Get signal statistics for a symbol"""
        try:
            # Database mode
            stats = await DatabaseService.get_signal_statistics(db, symbol=symbol, days=days)
            return stats
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats/all")
    async def get_all_signal_stats(days: int = 7, db: AsyncSession = Depends(get_db)):
        """Get overall signal statistics"""
        try:
            # Database mode
            stats = await DatabaseService.get_signal_statistics(db, days=days)
            return stats
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
else:
    @router.get("/{symbol}", response_model=SignalResponse)
    async def get_signal(symbol: str, interval: str = "1h"):
        try:
            # Fallback mode
            recent_signals = fallback_service.get_recent_signals(hours=1, symbol=symbol, limit=1)
            
            if recent_signals:
                return recent_signals[0]
            
            # Generate new signal
            signal_data = await get_current_signal(symbol, interval)
            fallback_service.add_signal(signal_data)
            
            return signal_data
        except ValueError as e:
            # Handle validation errors (like unsupported symbols) with 400 Bad Request
            error_msg = str(e)
            print(f"Validation error for {symbol}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/history/{symbol}", response_model=List[SignalResponse])
    async def get_signal_history(
        symbol: str,
        hours: int = 24,
        limit: int = 50
    ):
        """Get signal history for a specific symbol"""
        try:
            # Fallback mode
            signals = fallback_service.get_recent_signals(hours=hours, symbol=symbol, limit=limit)
            return signals
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats/{symbol}")
    async def get_signal_stats(symbol: str, days: int = 7):
        """Get signal statistics for a symbol"""
        try:
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
    async def get_all_signal_stats(days: int = 7):
        """Get overall signal statistics"""
        try:
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
