import json
import csv
import os
from datetime import datetime
from utils.binance import fetch_binance_data
from services.indicators import (
    calculate_rsi, calculate_ema,
    calculate_macd, calculate_bollinger_bands,
    calculate_stoch_rsi
)
from services.candlestick_analyzer import analyze_candlesticks

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

async def get_coin_data(symbol: str, interval: str = "1h", limit: int = 100):
    """Fetch and calculate indicators for a specific symbol and timeframe"""
    df = await fetch_binance_data(symbol, interval=interval, limit=limit)
    
    if df is None:
        print(f"Nincs elég adat: {symbol} ({interval})")
        return None
        
    # Calculate indicators
    df["rsi"] = calculate_rsi(df["close"])
    df["ema20"] = calculate_ema(df["close"], 20)
    df["ema50"] = calculate_ema(df["close"], 50)
    df["macd"], df["macd_signal"] = calculate_macd(df["close"])
    df["bb_upper"], df["bb_lower"] = calculate_bollinger_bands(df["close"])
    df["stoch_k"], df["stoch_d"] = calculate_stoch_rsi(df["close"])
    
    return df

async def get_coin_signal(symbol: str, interval: str = "1h", mode: str = "swing"):
    """Generate trading signal for a specific symbol, timeframe and trading mode"""
    df = await get_coin_data(symbol, interval)
    
    if df is None:
        return {"symbol": symbol, "interval": interval, "error": "Hiányzó adatok"}
    
    # Use candlestick analyzer for advanced pattern detection
    try:
        candlestick_analysis = analyze_candlesticks(df)
        
        # Create result dictionary with enhanced data
        result = {
            "symbol": symbol,
            "interval": interval,
            "price": float(df.iloc[-1]["close"]),
            "rsi": float(df.iloc[-1]["rsi"]),
            "ema20": float(df.iloc[-1]["ema20"]),
            "signal": candlestick_analysis["signal"],
            "timestamp": datetime.now().isoformat(),
            "trend": candlestick_analysis["trend"],
            "pattern": candlestick_analysis["pattern"],
            "score": candlestick_analysis["score"]
        }
        
        # Add entry, stop_loss and take_profit from candlestick analysis
        if candlestick_analysis["signal"] in ("BUY", "SELL"):
            result["entry"] = candlestick_analysis["entry"]
            result["stop_loss"] = candlestick_analysis["stop_loss"]
            result["take_profit"] = candlestick_analysis["take_profit"]
            
            # Log the signal
            log_signal(result)
            
            print(f"Signal detected: {symbol} ({interval}) - {result['signal']} at {result['entry']}")
            print(f"Pattern: {result['pattern']['name']} ({result['pattern']['direction']}, confidence: {result['pattern']['confidence']})")
        
    except Exception as e:
        print(f"Error in candlestick analysis for {symbol}: {e}")
        
        # Fall back to traditional signal generation if candlestick analysis fails
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Default values
        signal = "HOLD"
        entry = None
        stop_loss = None
        take_profit = None
        
        # Different conditions based on trading mode
        if mode == "scalp":
            # Scalping mode - more sensitive, shorter timeframes
            if (
                latest["rsi"] < 35 and prev["rsi"] < 30 and latest["rsi"] > prev["rsi"] and  # RSI oversold and turning up
                latest["close"] > latest["ema20"] and                                        # Price above EMA20
                latest["macd"] > latest["macd_signal"] and                                   # MACD crossover
                latest["stoch_k"] < 0.3 and latest["stoch_k"] > latest["stoch_d"]           # Stochastic turning up
            ):
                signal = "BUY"
                entry = float(latest["close"])
                stop_loss = entry * 0.99  # 1% stop loss for scalping
                take_profit = entry * 1.015  # 1.5% take profit for scalping
                
            elif (
                latest["rsi"] > 65 and prev["rsi"] > 70 and latest["rsi"] < prev["rsi"] and  # RSI overbought and turning down
                latest["close"] < latest["ema20"] and                                        # Price below EMA20
                latest["macd"] < latest["macd_signal"] and                                   # MACD crossover
                latest["stoch_k"] > 0.7 and latest["stoch_k"] < latest["stoch_d"]           # Stochastic turning down
            ):
                signal = "SELL"
                entry = float(latest["close"])
                stop_loss = entry * 1.01  # 1% stop loss for scalping
                take_profit = entry * 0.985  # 1.5% take profit for scalping
        
        else:  # swing mode
            # Swing mode - more conservative, longer timeframes
            if (
                latest["rsi"] < 30 and
                latest["close"] > latest["ema20"] and
                latest["macd"] > latest["macd_signal"] and
                latest["close"] < latest["bb_lower"] and
                latest["stoch_k"] < 0.2
            ):
                signal = "BUY"
                entry = float(latest["close"])
                stop_loss = min(df["close"].iloc[-5:]) * 0.98  # 2% below recent low
                take_profit = entry * 1.05  # 5% take profit for swing trading
                
            elif (
                latest["rsi"] > 70 and
                latest["close"] < latest["ema20"] and
                latest["macd"] < latest["macd_signal"] and
                latest["close"] > latest["bb_upper"] and
                latest["stoch_k"] > 0.8
            ):
                signal = "SELL"
                entry = float(latest["close"])
                stop_loss = max(df["close"].iloc[-5:]) * 1.02  # 2% above recent high
                take_profit = entry * 0.95  # 5% take profit for swing trading
        
        # Create result dictionary with traditional analysis
        result = {
            "symbol": symbol,
            "interval": interval,
            "price": float(latest["close"]),
            "rsi": float(latest["rsi"]),
            "ema20": float(latest["ema20"]),
            "signal": signal,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add entry, stop_loss and take_profit if we have a signal
        if signal in ("BUY", "SELL"):
            result["entry"] = round(entry, 2)
            result["stop_loss"] = round(stop_loss, 2)
            result["take_profit"] = round(take_profit, 2)
            
            # Log the signal
            log_signal(result)
            
            print(f"Signal detected (traditional): {symbol} ({interval}) - {signal} at {entry}")
    
    return result

async def get_coin_signal_multi_timeframe(symbol: str, mode: str = "swing"):
    """Generate signals across multiple timeframes for a symbol"""
    # Get data for multiple timeframes
    df_1h = await get_coin_data(symbol, interval="1h")
    df_4h = await get_coin_data(symbol, interval="4h")
    
    if df_1h is None or df_4h is None:
        return {"symbol": symbol, "error": "Hiányzó adatok"}
    
    # Get the primary signal from the 1h timeframe
    signal_1h = await get_coin_signal(symbol, interval="1h", mode=mode)
    
    # Add 4h confirmation data
    latest_4h = df_4h.iloc[-1]
    signal_1h["ema20_4h"] = float(latest_4h["ema20"])
    
    # Strengthen or weaken the signal based on 4h trend
    if signal_1h["signal"] == "BUY" and latest_4h["close"] < latest_4h["ema20"]:
        signal_1h["signal_strength"] = "weak"
    elif signal_1h["signal"] == "SELL" and latest_4h["close"] > latest_4h["ema20"]:
        signal_1h["signal_strength"] = "weak"
    else:
        signal_1h["signal_strength"] = "strong"
    
    return signal_1h

def log_signal(signal_data):
    """Log trading signals to JSON and CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # JSON logging
    json_file = f"logs/signals_{timestamp}.json"
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                signals = json.load(f)
        else:
            signals = []
            
        signals.append(signal_data)
        
        with open(json_file, 'w') as f:
            json.dump(signals, f, indent=2)
    except Exception as e:
        print(f"Error logging to JSON: {e}")
    
    # CSV logging
    csv_file = f"logs/signals_{timestamp}.csv"
    try:
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=signal_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(signal_data)
    except Exception as e:
        print(f"Error logging to CSV: {e}")

async def get_all_signals(symbols=None, interval="1h", mode="swing"):
    """Get signals for multiple symbols"""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
    
    # If symbols is a string (comma-separated), convert to list
    if isinstance(symbols, str):
        symbols = symbols.split(',')
    
    results = []
    for symbol in symbols:
        try:
            signal = await get_coin_signal(symbol, interval, mode)
            results.append(signal)
        except Exception as e:
            print(f"Error getting signal for {symbol}: {e}")
            # Add a placeholder signal with error information
            results.append({
                "symbol": symbol,
                "interval": interval,
                "error": str(e),
                "signal": "HOLD"
            })
    
    return results
