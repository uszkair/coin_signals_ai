from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from services.market_data import get_coin_signal_multi_timeframe

WATCHED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def start_scheduler():
    scheduler = AsyncIOScheduler(timezone=utc)

    @scheduler.scheduled_job("interval", hours=1)
    async def check_signals():
        print(">> Óránkénti futás indul...")
        for symbol in WATCHED_SYMBOLS:
            await get_coin_signal_multi_timeframe(symbol)

    scheduler.start()
