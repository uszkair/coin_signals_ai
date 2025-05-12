import asyncio
import json
from services.signal_backtester import run_backtest, backtest_signals
import pandas as pd
from datetime import datetime

async def test_backtest():
    """Test the signal backtester with real data"""
    print("=== Signal Backtester Test ===")
    print("This will analyze historical data and backtest trading signals.")
    
    # Default parameters
    symbol = "BTCUSDT"
    interval = "1h"
    lookback_days = 30
    risk_reward_ratio = 1.5
    
    # Run the backtest
    print(f"\nRunning backtest for {symbol} on {interval} timeframe, looking back {lookback_days} days...")
    signals = await run_backtest(symbol, interval, lookback_days, risk_reward_ratio)
    
    if not signals or (isinstance(signals, dict) and "error" in signals):
        print("No signals found or error occurred.")
        return
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_results_{symbol}_{interval}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(signals, f, indent=2)
    
    print(f"\nDetailed results saved to {filename}")
    
    # Display a few example signals
    if len(signals) > 0:
        print("\n=== Example Signals ===")
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            print(f"\nSignal {i+1}:")
            print(f"Timestamp: {signal['timestamp']}")
            print(f"Type: {signal['signal']}")
            print(f"Pattern: {signal['pattern']}")
            print(f"Entry: {signal['entry']}")
            print(f"Stop Loss: {signal['stop_loss']}")
            print(f"Take Profit: {signal['take_profit']}")
            print(f"Outcome: {signal['outcome']}")
            print(f"Duration: {signal['duration_minutes']} minutes")
            print(f"Confidence: {signal['confidence_level']}")
            print(f"Comment: {signal['comment']}")

async def test_multiple_symbols():
    """Test backtesting on multiple symbols"""
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    interval = "1h"
    lookback_days = 30
    
    print("\n=== Multi-Symbol Backtest ===")
    
    results = {}
    for symbol in symbols:
        print(f"\nTesting {symbol}...")
        signals = await backtest_signals(symbol, interval, lookback_days)
        
        if isinstance(signals, dict) and "error" in signals:
            results[symbol] = {"error": signals["error"]}
            continue
            
        # Calculate statistics
        total_signals = len(signals)
        if total_signals == 0:
            results[symbol] = {"signals": 0}
            continue
            
        buy_signals = sum(1 for s in signals if s["signal"] == "BUY")
        sell_signals = sum(1 for s in signals if s["signal"] == "SELL")
        
        tp_hits = sum(1 for s in signals if s["outcome"] == "take_profit_hit")
        sl_hits = sum(1 for s in signals if s["outcome"] == "stop_loss_hit")
        
        win_rate = tp_hits / (tp_hits + sl_hits) * 100 if (tp_hits + sl_hits) > 0 else 0
        
        results[symbol] = {
            "signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "take_profit_hits": tp_hits,
            "stop_loss_hits": sl_hits,
            "win_rate": round(win_rate, 2)
        }
    
    # Display comparison table
    print("\n=== Symbol Comparison ===")
    print(f"{'Symbol':<10} {'Signals':<10} {'Buy':<6} {'Sell':<6} {'TP Hits':<10} {'SL Hits':<10} {'Win Rate':<10}")
    print("-" * 60)
    
    for symbol, stats in results.items():
        if "error" in stats:
            print(f"{symbol:<10} Error: {stats['error']}")
        elif stats["signals"] == 0:
            print(f"{symbol:<10} No signals found")
        else:
            print(f"{symbol:<10} {stats['signals']:<10} {stats['buy_signals']:<6} {stats['sell_signals']:<6} "
                  f"{stats['take_profit_hits']:<10} {stats['stop_loss_hits']:<10} {stats['win_rate']}%")

async def test_timeframes():
    """Test backtesting on different timeframes"""
    symbol = "BTCUSDT"
    intervals = ["15m", "1h", "4h"]
    lookback_days = 30
    
    print("\n=== Timeframe Comparison ===")
    
    results = {}
    for interval in intervals:
        print(f"\nTesting {interval} timeframe...")
        signals = await backtest_signals(symbol, interval, lookback_days)
        
        if isinstance(signals, dict) and "error" in signals:
            results[interval] = {"error": signals["error"]}
            continue
            
        # Calculate statistics
        total_signals = len(signals)
        if total_signals == 0:
            results[interval] = {"signals": 0}
            continue
            
        tp_hits = sum(1 for s in signals if s["outcome"] == "take_profit_hit")
        sl_hits = sum(1 for s in signals if s["outcome"] == "stop_loss_hit")
        
        win_rate = tp_hits / (tp_hits + sl_hits) * 100 if (tp_hits + sl_hits) > 0 else 0
        
        # Calculate average duration
        if tp_hits > 0:
            avg_win_duration = sum(s["duration_minutes"] for s in signals if s["outcome"] == "take_profit_hit") / tp_hits
        else:
            avg_win_duration = 0
            
        results[interval] = {
            "signals": total_signals,
            "take_profit_hits": tp_hits,
            "stop_loss_hits": sl_hits,
            "win_rate": round(win_rate, 2),
            "avg_win_duration": round(avg_win_duration, 2)
        }
    
    # Display comparison table
    print("\n=== Timeframe Comparison ===")
    print(f"{'Interval':<10} {'Signals':<10} {'TP Hits':<10} {'SL Hits':<10} {'Win Rate':<10} {'Avg Duration':<15}")
    print("-" * 65)
    
    for interval, stats in results.items():
        if "error" in stats:
            print(f"{interval:<10} Error: {stats['error']}")
        elif stats["signals"] == 0:
            print(f"{interval:<10} No signals found")
        else:
            print(f"{interval:<10} {stats['signals']:<10} {stats['take_profit_hits']:<10} {stats['stop_loss_hits']:<10} "
                  f"{stats['win_rate']}%{'':<5} {stats['avg_win_duration']} min")

if __name__ == "__main__":
    # Run the tests
    print("Signal Backtester Test Script")
    print("============================")
    print("This script will test the signal backtester with various parameters.")
    print("Choose a test to run:")
    print("1. Basic backtest (single symbol)")
    print("2. Multi-symbol comparison")
    print("3. Timeframe comparison")
    print("4. Run all tests")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        asyncio.run(test_backtest())
    elif choice == "2":
        asyncio.run(test_multiple_symbols())
    elif choice == "3":
        asyncio.run(test_timeframes())
    elif choice == "4":
        asyncio.run(test_backtest())
        asyncio.run(test_multiple_symbols())
        asyncio.run(test_timeframes())
    else:
        print("Invalid choice. Exiting.")