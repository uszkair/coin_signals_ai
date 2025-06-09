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
    
    async def fetch_historical_data(self, symbols: List[str], days: int = 365, force_refresh: bool = False) -> Dict[str, bool]:
        """
        Intelligently fetch historical data - avoids API rate limits by only downloading missing data
        Returns dict with symbol -> success status
        """
        results = {}
        api_calls_made = 0
        
        try:
            async with AsyncSessionLocal() as session:
                for symbol in symbols:
                    try:
                        print(f"📊 Checking data for {symbol}...")
                        
                        # Check existing data coverage
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=days)
                        
                        # Get latest existing data
                        existing_result = await session.execute(
                            select(BacktestData)
                            .where(
                                BacktestData.symbol == symbol,
                                BacktestData.timestamp >= start_date
                            )
                            .order_by(BacktestData.timestamp.desc())
                            .limit(1)
                        )
                        latest_data = existing_result.scalar_one_or_none()
                        
                        # Count existing data points in range
                        count_result = await session.execute(
                            select(BacktestData)
                            .where(
                                BacktestData.symbol == symbol,
                                BacktestData.timestamp >= start_date,
                                BacktestData.timestamp <= end_date
                            )
                        )
                        existing_data = count_result.scalars().all()
                        existing_count = len(existing_data)
                        expected_count = days * 24  # 24 hours per day
                        
                        # Determine if we need to fetch data
                        should_fetch = force_refresh
                        fetch_reason = ""
                        
                        if not should_fetch:
                            if not latest_data:
                                should_fetch = True
                                fetch_reason = "No existing data found"
                            elif existing_count < (expected_count * 0.8):  # Less than 80% coverage
                                should_fetch = True
                                fetch_reason = f"Insufficient coverage ({existing_count}/{expected_count} points)"
                            else:
                                # Check if data is recent (within 2 hours)
                                time_diff = datetime.now() - latest_data.timestamp.replace(tzinfo=None)
                                if time_diff.total_seconds() > 7200:  # 2 hours
                                    should_fetch = True
                                    fetch_reason = f"Data outdated ({int(time_diff.total_seconds()/3600)}h old)"
                                else:
                                    print(f"✅ {symbol}: Data up-to-date ({existing_count} points, latest: {latest_data.timestamp})")
                                    results[symbol] = True
                                    continue
                        
                        # Rate limiting protection
                        if api_calls_made >= 100:  # Conservative limit
                            print(f"⚠️ API rate limit protection: Skipping {symbol} (made {api_calls_made} calls)")
                            results[symbol] = False
                            continue
                        
                        if should_fetch:
                            print(f"🔄 {symbol}: {fetch_reason}")
                            
                            if force_refresh:
                                # Only delete if force refresh requested
                                await session.execute(
                                    delete(BacktestData).where(BacktestData.symbol == symbol)
                                )
                                print(f"🗑️ {symbol}: Cleared existing data")
                            
                            # Fetch new data with rate limiting
                            print(f"📡 {symbol}: Downloading data (API call #{api_calls_made + 1})...")
                            candles = await get_historical_data(symbol=symbol, interval="1h", days=days)
                            api_calls_made += 1
                            
                            if not candles:
                                print(f"❌ {symbol}: No data received")
                                results[symbol] = False
                                continue
                            
                            # Save to database (only new data if not force refresh)
                            new_data_count = 0
                            for candle in candles:
                                # Skip if data already exists (unless force refresh)
                                if not force_refresh:
                                    existing_check = await session.execute(
                                        select(BacktestData)
                                        .where(
                                            BacktestData.symbol == symbol,
                                            BacktestData.timestamp == candle["timestamp"]
                                        )
                                    )
                                    if existing_check.scalar_one_or_none():
                                        continue
                                
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
                                session.add(backtest_data)
                                new_data_count += 1
                            
                            await session.commit()
                            print(f"✅ {symbol}: Saved {new_data_count} new candles")
                            results[symbol] = True
                            
                            # Rate limiting delay
                            if api_calls_made % 10 == 0:
                                print(f"⏱️ Rate limiting: Pausing after {api_calls_made} API calls...")
                                await asyncio.sleep(2)  # 2 second pause every 10 calls
                        
                    except Exception as e:
                        print(f"❌ Error processing {symbol}: {e}")
                        results[symbol] = False
                        await session.rollback()
                        
        except Exception as e:
            print(f"❌ General error in fetch_historical_data: {e}")
        
        print(f"📈 Data fetch completed: {api_calls_made} API calls made")
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
            
            if len(historical_data) < 720:
                return {
                    "error": f"Insufficient data for {symbol}. Need at least 720 candles (30 days), got {len(historical_data)}"
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
                breakeven_trades = 0
                equity_curve = [position_size]  # Track equity for drawdown calculation
                
                # Process each candle
                for i in range(720, len(historical_data)):  # Start from 720 to have enough history (30 days)
                    current_candle = historical_data[i]
                    
                    # Prepare data for signal engine (last 720 candles = 30 days)
                    candle_window = historical_data[i-719:i+1]
                    
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
                    
                    # Generate signal using the actual signal engine with historical data
                    try:
                        # Use the real signal engine by temporarily mocking the price data
                        signal_data = await self._get_signal_with_historical_data(
                            formatted_candles, symbol, '1h'
                        )
                        
                        # Debug: Log every 100th signal to see what's happening
                        if i % 100 == 0:
                            print(f"🔍 Debug {symbol} candle {i}: Signal={signal_data['signal']}, Confidence={signal_data['confidence']:.1f}%, Threshold={min_confidence}%")
                        
                        # Check if signal meets confidence threshold
                        if signal_data['confidence'] >= min_confidence and signal_data['signal'] in ['BUY', 'SELL']:
                            print(f"✅ {symbol} Trade Signal: {signal_data['signal']} at {signal_data['confidence']:.1f}% confidence (entry: ${signal_data['entry_price']:.2f})")
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
                                elif profit_usd < 0:
                                    losing_trades += 1
                                    result_status = 'loss'
                                else:
                                    breakeven_trades += 1
                                    result_status = 'breakeven'
                                
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
                            else:
                                # Handle no_exit case - treat as breakeven
                                print(f"⚠️ {symbol} Trade timeout: No exit found, treating as breakeven")
                                profit_usd = 0.0
                                profit_percent = 0.0
                                result_status = 'breakeven'
                                breakeven_trades += 1
                                
                                # No change to equity curve for breakeven
                                equity_curve.append(equity_curve[-1])
                                
                                # Create trade record with entry price as exit price
                                trade = BacktestTrade(
                                    backtest_result_id=backtest_result.id,
                                    symbol=symbol,
                                    signal_type=signal_data['signal'],
                                    entry_price=Decimal(str(entry_price)),
                                    exit_price=Decimal(str(entry_price)),  # Same as entry = breakeven
                                    stop_loss=Decimal(str(stop_loss)) if stop_loss else None,
                                    take_profit=Decimal(str(take_profit)) if take_profit else None,
                                    confidence=Decimal(str(signal_data['confidence'])),
                                    pattern=signal_data.get('pattern'),
                                    entry_time=datetime.fromisoformat(current_candle['timestamp'].replace('Z', '+00:00')),
                                    exit_time=None,  # No exit time for timeout
                                    profit_usd=Decimal('0.0'),
                                    profit_percent=Decimal('0.0'),
                                    result=result_status
                                )
                                trades.append(trade)
                    
                    except Exception as e:
                        print(f"Error processing candle {i}: {e}")
                        continue
                
                # Calculate final statistics
                total_trades = len(trades)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                print(f"📊 {symbol} Backtest Summary:")
                print(f"   Total trades: {total_trades}")
                print(f"   Winning: {winning_trades} ({win_rate:.1f}%)")
                print(f"   Losing: {losing_trades}")
                print(f"   Breakeven: {breakeven_trades}")
                print(f"   Total P&L: ${total_profit_usd:.2f} ({total_profit_percent:.2f}%)")
                
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
                
                # Store breakeven trades in notes field for now (until we add a dedicated column)
                backtest_result.notes = f"Breakeven trades: {breakeven_trades}"
                
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
    
    async def _get_signal_with_historical_data(self, candles: List[Dict], symbol: str, interval: str) -> Dict:
        """
        Use the real signal engine with historical data by temporarily mocking the data source
        This ensures 100% consistency with live trading signals
        """
        import unittest.mock
        from app.utils.price_data import get_historical_data, get_current_price
        
        # Mock the price data functions to return our historical data
        async def mock_get_historical_data(symbol_param, interval_param, days):
            return candles
        
        async def mock_get_current_price(symbol_param):
            return candles[-1]["close"]
        
        # Use the real signal engine with mocked price data only
        # Let AI signal generation use real data from database
        with unittest.mock.patch('app.utils.price_data.get_historical_data', side_effect=mock_get_historical_data), \
             unittest.mock.patch('app.utils.price_data.get_current_price', side_effect=mock_get_current_price):
            
            # Call the real signal engine - includes REAL AI analysis from database!
            signal_data = await get_current_signal(symbol, interval)
            
            return signal_data
    
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