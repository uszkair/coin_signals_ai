import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.database_models import (
    Signal, 
    SignalPerformance, 
    BacktestData, 
    BacktestResult, 
    BacktestTrade
)
from sqlalchemy import delete

async def clear_data():
    async with AsyncSessionLocal() as session:
        try:
            print("Clearing trading data...")
            
            # Delete in order
            await session.execute(delete(BacktestTrade))
            await session.execute(delete(BacktestResult))
            await session.execute(delete(BacktestData))
            await session.execute(delete(SignalPerformance))
            await session.execute(delete(Signal))
            
            await session.commit()
            print("✅ All trading data cleared!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(clear_data())