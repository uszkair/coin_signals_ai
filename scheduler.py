from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from services.market_data import get_coin_signal, get_coin_signal_multi_timeframe
import asyncio
import json
import os
from datetime import datetime

# Symbols to watch
WATCHED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "XRPUSDT", "DOTUSDT"]

# Timeframes to monitor
TIMEFRAMES = {
    "scalp": ["5m", "15m"],
    "swing": ["1h", "4h"]
}

def start_scheduler():
    """Start the scheduler for periodic signal checking"""
    scheduler = AsyncIOScheduler(timezone=utc)
    
    # Check for scalping signals every 5 minutes
    @scheduler.scheduled_job("interval", minutes=5)
    async def check_scalp_signals():
        print(f">> Scalping signal check started at {datetime.now().isoformat()}")
        for symbol in WATCHED_SYMBOLS:
            for timeframe in TIMEFRAMES["scalp"]:
                await get_coin_signal(symbol, timeframe, "scalp")
            # Small delay to avoid API rate limits
            await asyncio.sleep(1)
    
    # Check for swing trading signals every hour
    @scheduler.scheduled_job("interval", hours=1)
    async def check_swing_signals():
        print(f">> Swing trading signal check started at {datetime.now().isoformat()}")
        for symbol in WATCHED_SYMBOLS:
            for timeframe in TIMEFRAMES["swing"]:
                await get_coin_signal(symbol, timeframe, "swing")
            # Small delay to avoid API rate limits
            await asyncio.sleep(1)
    
    # Multi-timeframe analysis every 4 hours
    @scheduler.scheduled_job("interval", hours=4)
    async def check_mtf_signals():
        print(f">> Multi-timeframe analysis started at {datetime.now().isoformat()}")
        for symbol in WATCHED_SYMBOLS:
            await get_coin_signal_multi_timeframe(symbol, "swing")
            # Small delay to avoid API rate limits
            await asyncio.sleep(1)
    
    # Daily summary at midnight
    @scheduler.scheduled_job("cron", hour=0, minute=0)
    async def generate_daily_summary():
        print(f">> Generating daily summary at {datetime.now().isoformat()}")
        
        # Get yesterday's date
        yesterday = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) -
                    datetime.timedelta(days=1)).strftime("%Y%m%d")
        
        # Check if we have signals from yesterday
        json_file = f"logs/signals_{yesterday}.json"
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    signals = json.load(f)
                
                # Count signals by type
                buy_signals = sum(1 for s in signals if s.get("signal") == "BUY")
                sell_signals = sum(1 for s in signals if s.get("signal") == "SELL")
                
                print(f"Daily summary for {yesterday}:")
                print(f"Total signals: {len(signals)}")
                print(f"Buy signals: {buy_signals}")
                print(f"Sell signals: {sell_signals}")
                
                # TODO: Add more analysis and potentially send a summary email
                
            except Exception as e:
                print(f"Error generating daily summary: {e}")
    
    scheduler.start()
    print("Scheduler started successfully")
