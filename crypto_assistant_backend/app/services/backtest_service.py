# app/services/backtest_service.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.database_models import BacktestData, BacktestResult, BacktestTrade
from app.services.signal_engine import get_current_signal
from app.utils.price_data import get_historical_data

class BacktestService:
    def __init__(self):
        pass
    
    async def fetch_historical_data(self, symbols: List[str], days: int = 365) -> Dict[str, bool]:
        """
        Fetch 1 year of historical data using existing get_historical_data function
        Returns dict with symbol -> success status
        """
        results = {}
        
        try:
            async with AsyncSessionLocal() as session:
                for symbol in symbols:
                    try:
                        print(f"Fetching data for {symbol}...")
                        
                        # Delete existing backtest data for this symbol
                        await session.execute(
                            delete(BacktestData).where(BacktestData.symbol == symbol)
                        )
                        
                        # Use existing get_historical_data function
                        candles = await get_historical_data(symbol=symbol, interval="1h", days=days)
                        
                        if not candles:
                            results[symbol] = False
                            continue
                        
                        # Save to database
                        backtest_data_objects = []
                        for candle in candles:
                            backtest_data = BacktestData(
                                symbol=symbol,
                                open_price=Decimal(str(candle["open"])),
                                high_price=Decimal(str(candle["high"])),
                                low_price=Decimal(str(candle["low"])),
                                close_price=Decimal(str(candle["close"])),
                                volume=Decimal(str(candle["volume"])),
                                interval_type='1h',
                                timestamp=candle["timestamp"]
                            )
                            backtest_data_objects.append(backtest_data)
                        
                        # Bulk insert
                        session.add_all(backtest_data_objects)
                        await session.commit()
                        
                        results[symbol] = True
                        print(f"Successfully saved {len(backtest_data_objects)} candles for {symbol}")
                        
                    except Exception as e:
                        print(f"Error processing {symbol}: {e}")
                        results[symbol] = False
                        await session.rollback()
                        
        except Exception as e:
            print(f"General error in fetch_historical_data: {e}")
                
        return results
    
    async def get_backtest_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get backtest data for a symbol within date range"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BacktestData)
                .where(
                    BacktestData.symbol == symbol,
                    BacktestData.timestamp >= start_date,
                    BacktestData.timestamp <= end_date
                )
                .order_by(BacktestData.timestamp)
            )
            data = result.scalars().all()
            return [item.to_dict() for item in data]
    
    async def run_backtest(self, 
                          test_name: str,
                          symbol: str, 
                          start_date: datetime, 
                          end_date: datetime,
                          min_confidence: int = 70,
                          position_size: float = 100.0) -> Dict:
        """
        Run backtest on historical data using the signal engine
        """
        try:
            # Get historical data
            historical_data = await self.get_backtest_data(symbol, start_date, end_date)
            
            if len(historical_data) < 50:
                return {
                    "error": f"Insufficient data for {symbol}. Need at least 50 candles, got {len(historical_data)}"
                }
            
            # Initialize backtest result
            async with AsyncSessionLocal() as session:
                backtest_result = BacktestResult(
                    test_name=test_name,
                    symbol=symbol,
                    interval_type='1h',
                    start_date=start_date,
                    end_date=end_date,
                    min_confidence=min_confidence,
                    position_size=Decimal(str(position_size))
                )
                session.add(backtest_result)
                await session.flush()  # Get the ID
                
                trades = []
                total_profit_usd = 0.0
                total_profit_percent = 0.0
                winning_trades = 0
                losing_trades = 0
                equity_curve = [position_size]  # Track equity for drawdown calculation
                
                # Process each candle
                for i in range(50, len(historical_data)):  # Start from 50 to have enough history
                    current_candle = historical_data[i]
                    
                    # Prepare data for signal engine (last 50 candles)
                    candle_window = historical_data[i-49:i+1]
                    
                    # Convert to format expected by signal engine
                    formatted_candles = []
                    for candle in candle_window:
                        formatted_candles.append({
                            'open': candle['open'],
                            'high': candle['high'],
                            'low': candle['low'],
                            'close': candle['close'],
                            'volume': candle['volume'],
                            'timestamp': datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
                        })
                    
                    # Generate signal using existing signal engine logic
                    try:
                        # Mock the signal generation with our historical data
                        signal_data = await self._generate_signal_from_historical_data(
                            formatted_candles, symbol, '1h'
                        )
                        
                        # Check if signal meets confidence threshold
                        if signal_data['confidence'] >= min_confidence and signal_data['signal'] in ['BUY', 'SELL']:
                            # Simulate trade execution
                            entry_price = signal_data['entry_price']
                            stop_loss = signal_data['stop_loss']
                            take_profit = signal_data['take_profit']
                            
                            # Look ahead to find exit point
                            exit_result = await self._simulate_trade_exit(
                                historical_data[i+1:], 
                                signal_data['signal'],
                                entry_price,
                                stop_loss,
                                take_profit
                            )
                            
                            # Calculate profit/loss
                            if exit_result['exit_price']:
                                if signal_data['signal'] == 'BUY':
                                    profit_percent = ((exit_result['exit_price'] - entry_price) / entry_price) * 100
                                else:  # SELL
                                    profit_percent = ((entry_price - exit_result['exit_price']) / entry_price) * 100
                                
                                profit_usd = (profit_percent / 100) * position_size
                                
                                # Update totals
                                total_profit_usd += profit_usd
                                total_profit_percent += profit_percent
                                
                                if profit_usd > 0:
                                    winning_trades += 1
                                    result_status = 'profit'
                                else:
                                    losing_trades += 1
                                    result_status = 'loss'
                                
                                # Update equity curve
                                current_equity = equity_curve[-1] + profit_usd
                                equity_curve.append(current_equity)
                                
                                # Create trade record
                                trade = BacktestTrade(
                                    backtest_result_id=backtest_result.id,
                                    symbol=symbol,
                                    signal_type=signal_data['signal'],
                                    entry_price=Decimal(str(entry_price)),
                                    exit_price=Decimal(str(exit_result['exit_price'])),
                                    stop_loss=Decimal(str(stop_loss)) if stop_loss else None,
                                    take_profit=Decimal(str(take_profit)) if take_profit else None,
                                    confidence=Decimal(str(signal_data['confidence'])),
                                    pattern=signal_data.get('pattern'),
                                    entry_time=datetime.fromisoformat(current_candle['timestamp'].replace('Z', '+00:00')),
                                    exit_time=exit_result['exit_time'],
                                    profit_usd=Decimal(str(profit_usd)),
                                    profit_percent=Decimal(str(profit_percent)),
                                    result=result_status
                                )
                                trades.append(trade)
                    
                    except Exception as e:
                        print(f"Error processing candle {i}: {e}")
                        continue
                
                # Calculate final statistics
                total_trades = len(trades)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate max drawdown
                max_drawdown = 0.0
                peak = position_size
                for equity in equity_curve:
                    if equity > peak:
                        peak = equity
                    drawdown = ((peak - equity) / peak) * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                
                # Update backtest result
                backtest_result.total_trades = total_trades
                backtest_result.winning_trades = winning_trades
                backtest_result.losing_trades = losing_trades
                backtest_result.total_profit_usd = Decimal(str(total_profit_usd))
                backtest_result.total_profit_percent = Decimal(str(total_profit_percent))
                backtest_result.win_rate = Decimal(str(win_rate))
                backtest_result.max_drawdown = Decimal(str(max_drawdown))
                
                # Save all trades
                session.add_all(trades)
                await session.commit()
                
                return {
                    "backtest_id": backtest_result.id,
                    "summary": backtest_result.to_dict(),
                    "trades": [trade.to_dict() for trade in trades],
                    "equity_curve": equity_curve
                }
                
        except Exception as e:
            print(f"Error in run_backtest: {e}")
            return {"error": str(e)}
    
    async def _generate_signal_from_historical_data(self, candles: List[Dict], symbol: str, interval: str) -> Dict:
        """Generate signal using historical data (simplified version of signal engine)"""
        from app.services.indicators import compute_indicators
        from app.services.candlestick_analyzer import detect_patterns
        from app.services.technical_indicators import calculate_professional_indicators
        
        latest = candles[-1]
        previous = candles[-2] if len(candles) > 1 else None
        
        # Calculate indicators
        professional_indicators = calculate_professional_indicators(candles)
        indicators = compute_indicators(latest)
        pattern, score = detect_patterns(latest, previous)
        
        # Simplified signal generation logic
        signal_score = 0
        
        # Pattern-based signals
        if pattern in ["Hammer", "Bullish Engulfing"]:
            signal_score += 2
        elif pattern in ["Shooting Star", "Bearish Engulfing"]:
            signal_score -= 2
        
        # Trend-based signals
        if indicators["trend"] == "bullish":
            signal_score += 1
        elif indicators["trend"] == "bearish":
            signal_score -= 1
        
        # Professional indicators
        rsi_data = professional_indicators.get('rsi', {})
        if rsi_data.get('signal') == 'BUY':
            signal_score += 1
        elif rsi_data.get('signal') == 'SELL':
            signal_score -= 1
        
        # Determine direction
        if signal_score > 0:
            direction = "BUY"
        elif signal_score < 0:
            direction = "SELL"
        else:
            direction = "HOLD"
        
        # Calculate stop loss and take profit
        atr = latest["high"] - latest["low"]
        sl_distance = atr * 0.5
        tp_distance = sl_distance * 1.5
        
        entry_price = latest["close"]
        stop_loss = entry_price - sl_distance if direction == "BUY" else entry_price + sl_distance
        take_profit = entry_price + tp_distance if direction == "BUY" else entry_price - tp_distance
        
        return {
            "symbol": symbol,
            "interval": interval,
            "signal": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "pattern": pattern,
            "confidence": min(95, max(5, 50 + abs(signal_score) * 10)),
            "timestamp": latest["timestamp"].isoformat()
        }
    
    async def _simulate_trade_exit(self, future_candles: List[Dict], direction: str, 
                                 entry_price: float, stop_loss: float, take_profit: float) -> Dict:
        """Simulate trade exit by looking at future candles"""
        for candle in future_candles:
            low = candle["low"]
            high = candle["high"]
            timestamp = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
            
            if direction == "BUY":
                if low <= stop_loss:
                    return {"exit_price": stop_loss, "exit_time": timestamp, "reason": "stop_loss"}
                elif high >= take_profit:
                    return {"exit_price": take_profit, "exit_time": timestamp, "reason": "take_profit"}
            else:  # SELL
                if high >= stop_loss:
                    return {"exit_price": stop_loss, "exit_time": timestamp, "reason": "stop_loss"}
                elif low <= take_profit:
                    return {"exit_price": take_profit, "exit_time": timestamp, "reason": "take_profit"}
        
        # No exit found in available data
        return {"exit_price": None, "exit_time": None, "reason": "no_exit"}
    
    async def get_backtest_results(self) -> List[Dict]:
        """Get all backtest results"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BacktestResult).order_by(BacktestResult.created_at.desc())
            )
            results = result.scalars().all()
            return [item.to_dict() for item in results]
    
    async def get_backtest_details(self, backtest_id: int) -> Dict:
        """Get detailed backtest results including trades"""
        async with AsyncSessionLocal() as session:
            # Get backtest result
            result = await session.execute(
                select(BacktestResult).where(BacktestResult.id == backtest_id)
            )
            backtest_result = result.scalar_one_or_none()
            
            if not backtest_result:
                return {"error": "Backtest not found"}
            
            # Get trades
            trades_result = await session.execute(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_result_id == backtest_id)
                .order_by(BacktestTrade.entry_time)
            )
            trades = trades_result.scalars().all()
            
            return {
                "summary": backtest_result.to_dict(),
                "trades": [trade.to_dict() for trade in trades]
            }
    
    async def delete_backtest(self, backtest_id: int) -> bool:
        """Delete a backtest and all its trades"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BacktestResult).where(BacktestResult.id == backtest_id)
            )
            backtest_result = result.scalar_one_or_none()
            
            if not backtest_result:
                return False
            
            await session.delete(backtest_result)
            await session.commit()
            return True

# Global instance
backtest_service = BacktestService()