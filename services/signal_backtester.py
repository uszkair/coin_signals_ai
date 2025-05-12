import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.candlestick_analyzer import analyze_candlesticks
from utils.binance import fetch_binance_data

async def backtest_signals(symbol="BTCUSDT", interval="1h", lookback_days=30, risk_reward_ratio=1.5):
    """
    Backtest trading signals on historical data for the specified period.
    
    Args:
        symbol (str): Trading pair symbol (e.g., "BTCUSDT")
        interval (str): Timeframe (e.g., "1h", "4h", "1d")
        lookback_days (int): Number of days to look back for historical data
        risk_reward_ratio (float): Risk-to-reward ratio for take profit calculation
        
    Returns:
        list: List of signal analysis dictionaries with backtest results
    """
    # Calculate the number of candles needed based on interval and lookback days
    candles_per_day = {
        "1m": 24 * 60,
        "5m": 24 * 12,
        "15m": 24 * 4,
        "30m": 24 * 2,
        "1h": 24,
        "4h": 6,
        "1d": 1
    }
    
    # Calculate limit with some buffer
    limit = candles_per_day.get(interval, 24) * lookback_days + 100
    
    # Fetch historical data
    print(f"Fetching {limit} candles of {interval} data for {symbol}...")
    df = await fetch_binance_data(symbol, interval=interval, limit=limit)
    
    if df is None or len(df) < 50:
        return {"error": f"Could not fetch enough data for {symbol}"}
    
    # Get trend data from higher timeframe if possible
    trend_df = None
    if interval in ["1m", "5m", "15m", "30m", "1h"]:
        # For lower timeframes, get 4h data for trend analysis
        trend_df = await fetch_binance_data(symbol, interval="4h", limit=100)
    elif interval in ["4h"]:
        # For 4h, get daily data for trend analysis
        trend_df = await fetch_binance_data(symbol, interval="1d", limit=100)
    
    # Filter data to lookback period
    end_date = df.index[-1]
    start_date = end_date - timedelta(days=lookback_days)
    historical_df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    print(f"Analyzing {len(historical_df)} candles from {start_date} to {end_date}")
    
    # List to store all signal analyses
    all_signals = []
    
    # Iterate through each day in the historical data
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Get data up to current date for analysis
        analysis_df = df[df.index <= current_date].tail(100)
        
        if len(analysis_df) < 50:
            current_date = next_date
            continue
        
        # Analyze candlestick patterns
        try:
            # Get the higher timeframe trend if available
            higher_trend = "UNKNOWN"
            if trend_df is not None:
                trend_analysis_df = trend_df[trend_df.index <= current_date].tail(100)
                if len(trend_analysis_df) >= 50:
                    trend_result = analyze_candlesticks(trend_analysis_df)
                    higher_trend = trend_result["trend"]
            
            # Analyze the current timeframe
            result = analyze_candlesticks(analysis_df)
            
            # Only process if we have a BUY or SELL signal
            if result["signal"] in ["BUY", "SELL"]:
                # Get the signal timestamp (last candle in analysis)
                signal_timestamp = analysis_df.index[-1]
                
                # Create signal analysis dictionary
                signal_analysis = {
                    "timestamp": signal_timestamp.isoformat(),
                    "signal": result["signal"],
                    "pattern": result["pattern"]["name"],
                    "entry": result["entry"],
                    "stop_loss": result["stop_loss"],
                    "take_profit": result["take_profit"],
                    "score": result["score"],
                    "trend": result["trend"],
                    "higher_timeframe_trend": higher_trend,
                    "rsi": float(analysis_df.iloc[-1]["rsi"]) if "rsi" in analysis_df.columns else None,
                    "macd": "bullish" if "macd" in analysis_df.columns and analysis_df.iloc[-1]["macd"] > analysis_df.iloc[-1]["macd_signal"] else "bearish",
                    "atr": float(analysis_df.iloc[-1]["atr"]) if "atr" in analysis_df.columns else None,
                    "volatility": classify_volatility(analysis_df),
                    "rr_ratio": risk_reward_ratio,
                    "confidence_level": classify_confidence(result["score"], result["pattern"]["confidence"]),
                }
                
                # Backtest the signal
                backtest_result = backtest_signal(
                    df, 
                    signal_timestamp, 
                    signal_analysis["signal"], 
                    signal_analysis["entry"], 
                    signal_analysis["stop_loss"], 
                    signal_analysis["take_profit"]
                )
                
                # Add backtest results to signal analysis
                signal_analysis.update(backtest_result)
                
                # Generate comment
                signal_analysis["comment"] = generate_comment(signal_analysis)
                
                # Add to list of signals
                all_signals.append(signal_analysis)
                
                print(f"Found {signal_analysis['signal']} signal at {signal_timestamp} - Outcome: {signal_analysis['outcome']}")
        
        except Exception as e:
            print(f"Error analyzing data for {current_date}: {e}")
        
        # Move to next day
        current_date = next_date
    
    return all_signals

def backtest_signal(df, signal_timestamp, signal_type, entry, stop_loss, take_profit):
    """
    Backtest a single trading signal against future price action.
    
    Args:
        df (DataFrame): Price data with future candles
        signal_timestamp: Timestamp of the signal
        signal_type (str): "BUY" or "SELL"
        entry (float): Entry price
        stop_loss (float): Stop loss price
        take_profit (float): Take profit price
        
    Returns:
        dict: Backtest results
    """
    # Get future data after signal
    future_df = df[df.index > signal_timestamp]
    
    if len(future_df) == 0:
        return {
            "outcome": "undecided",
            "duration_minutes": 0,
            "exit_timestamp": None,
            "exit_price": None
        }
    
    # Initialize variables
    outcome = "undecided"
    duration_minutes = 0
    exit_timestamp = None
    exit_price = None
    
    # Check each future candle
    for idx, candle in future_df.iterrows():
        # For BUY signals
        if signal_type == "BUY":
            # Check if stop loss was hit (price went below stop loss)
            if candle["low"] <= stop_loss:
                outcome = "stop_loss_hit"
                exit_timestamp = idx
                exit_price = stop_loss
                break
            
            # Check if take profit was hit (price went above take profit)
            if candle["high"] >= take_profit:
                outcome = "take_profit_hit"
                exit_timestamp = idx
                exit_price = take_profit
                break
        
        # For SELL signals
        elif signal_type == "SELL":
            # Check if stop loss was hit (price went above stop loss)
            if candle["high"] >= stop_loss:
                outcome = "stop_loss_hit"
                exit_timestamp = idx
                exit_price = stop_loss
                break
            
            # Check if take profit was hit (price went below take profit)
            if candle["low"] <= take_profit:
                outcome = "take_profit_hit"
                exit_timestamp = idx
                exit_price = take_profit
                break
    
    # Calculate duration if we have an outcome
    if outcome != "undecided" and exit_timestamp is not None:
        duration = exit_timestamp - signal_timestamp
        duration_minutes = duration.total_seconds() / 60
    
    return {
        "outcome": outcome,
        "duration_minutes": duration_minutes,
        "exit_timestamp": exit_timestamp.isoformat() if exit_timestamp else None,
        "exit_price": exit_price
    }

def classify_volatility(df):
    """Classify volatility as 'low', 'medium', or 'high' based on ATR"""
    if "atr" not in df.columns:
        return "unknown"
    
    # Get the current ATR
    current_atr = df.iloc[-1]["atr"]
    
    # Get the average ATR for the last 20 periods
    avg_atr = df["atr"].tail(20).mean()
    
    # Calculate ATR as percentage of price
    price = df.iloc[-1]["close"]
    atr_percentage = (current_atr / price) * 100
    
    if atr_percentage < 0.5:
        return "low"
    elif atr_percentage < 1.5:
        return "medium"
    else:
        return "high"

def classify_confidence(score, pattern_confidence):
    """Classify confidence level based on score and pattern confidence"""
    if score >= 3 and pattern_confidence >= 3:
        return "high"
    elif score >= 2 or pattern_confidence >= 3:
        return "medium"
    else:
        return "low"

def generate_comment(signal_analysis):
    """Generate a human-readable comment about the signal"""
    signal = signal_analysis["signal"]
    pattern = signal_analysis["pattern"]
    trend = signal_analysis["trend"]
    higher_trend = signal_analysis.get("higher_timeframe_trend", "UNKNOWN")
    outcome = signal_analysis["outcome"]
    confidence = signal_analysis["confidence_level"]
    volatility = signal_analysis.get("volatility", "unknown")
    
    comment = f"{signal} jelzés {pattern} alakzat alapján. "
    
    # Add trend information
    if signal == trend:
        comment += "A jelzés trendirányba történt. "
    else:
        comment += "A jelzés trend ellen történt. "
    
    # Add higher timeframe trend
    if higher_trend != "UNKNOWN":
        if higher_trend == signal:
            comment += f"A magasabb időkeret trendje ({higher_trend}) megerősíti a jelzést. "
        else:
            comment += f"A magasabb időkeret trendje ({higher_trend}) ellentmond a jelzésnek. "
    
    # Add volatility
    if volatility != "unknown":
        comment += f"{volatility.capitalize()} volatilitás mellett. "
    
    # Add confidence
    comment += f"{confidence.capitalize()} megbízhatóságú jelzés. "
    
    # Add outcome
    if outcome == "take_profit_hit":
        comment += "A jelzés sikeres volt, elérte a célpontot. "
    elif outcome == "stop_loss_hit":
        comment += "A jelzés sikertelen volt, elérte a stop loss szintet. "
    else:
        comment += "A jelzés kimenetele még nem dőlt el. "
    
    return comment

async def run_backtest(symbol="BTCUSDT", interval="1h", lookback_days=30, risk_reward_ratio=1.5):
    """Run a backtest and print summary statistics"""
    signals = await backtest_signals(symbol, interval, lookback_days, risk_reward_ratio)
    
    if isinstance(signals, dict) and "error" in signals:
        print(f"Error: {signals['error']}")
        return signals
    
    # Print summary statistics
    total_signals = len(signals)
    if total_signals == 0:
        print("No signals found in the specified period.")
        return []
    
    buy_signals = sum(1 for s in signals if s["signal"] == "BUY")
    sell_signals = sum(1 for s in signals if s["signal"] == "SELL")
    
    tp_hits = sum(1 for s in signals if s["outcome"] == "take_profit_hit")
    sl_hits = sum(1 for s in signals if s["outcome"] == "stop_loss_hit")
    undecided = sum(1 for s in signals if s["outcome"] == "undecided")
    
    win_rate = tp_hits / (tp_hits + sl_hits) * 100 if (tp_hits + sl_hits) > 0 else 0
    
    print("\n=== Backtest Summary ===")
    print(f"Symbol: {symbol}, Interval: {interval}, Lookback: {lookback_days} days")
    print(f"Total Signals: {total_signals} (Buy: {buy_signals}, Sell: {sell_signals})")
    print(f"Take Profit Hits: {tp_hits}")
    print(f"Stop Loss Hits: {sl_hits}")
    print(f"Undecided: {undecided}")
    print(f"Win Rate: {win_rate:.2f}%")
    
    # Calculate average duration for winning trades
    if tp_hits > 0:
        avg_win_duration = sum(s["duration_minutes"] for s in signals if s["outcome"] == "take_profit_hit") / tp_hits
        print(f"Average Winning Trade Duration: {avg_win_duration:.2f} minutes")
    
    # Calculate average duration for losing trades
    if sl_hits > 0:
        avg_loss_duration = sum(s["duration_minutes"] for s in signals if s["outcome"] == "stop_loss_hit") / sl_hits
        print(f"Average Losing Trade Duration: {avg_loss_duration:.2f} minutes")
    
    # Calculate profit factor
    if sl_hits > 0:
        profit_factor = (tp_hits * risk_reward_ratio) / sl_hits
        print(f"Profit Factor: {profit_factor:.2f}")
    
    # Calculate expectancy
    if (tp_hits + sl_hits) > 0:
        expectancy = ((win_rate / 100) * risk_reward_ratio) - ((1 - win_rate / 100) * 1)
        print(f"Expectancy: {expectancy:.2f}")
    
    return signals

if __name__ == "__main__":
    import asyncio
    
    # Example usage
    asyncio.run(run_backtest("BTCUSDT", "1h", 30, 1.5))