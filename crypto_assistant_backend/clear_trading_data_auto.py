#!/usr/bin/env python3
"""
Clear all trading data from the database - AUTOMATIC VERSION
This script will delete all signals, signal performance, and backtest data WITHOUT confirmation
"""

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

async def clear_all_trading_data():
    """Clear all trading data from the database"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🗑️ Starting to clear all trading data...")
            
            # Delete in correct order due to foreign key constraints
            
            # 1. Delete backtest trades first (references backtest_results)
            result = await session.execute(delete(BacktestTrade))
            backtest_trades_deleted = result.rowcount
            print(f"✅ Deleted {backtest_trades_deleted} backtest trades")
            
            # 2. Delete backtest results
            result = await session.execute(delete(BacktestResult))
            backtest_results_deleted = result.rowcount
            print(f"✅ Deleted {backtest_results_deleted} backtest results")
            
            # 3. Delete backtest data
            result = await session.execute(delete(BacktestData))
            backtest_data_deleted = result.rowcount
            print(f"✅ Deleted {backtest_data_deleted} backtest data records")
            
            # 4. Delete signal performance first (references signals)
            result = await session.execute(delete(SignalPerformance))
            performance_deleted = result.rowcount
            print(f"✅ Deleted {performance_deleted} signal performance records")
            
            # 5. Delete signals
            result = await session.execute(delete(Signal))
            signals_deleted = result.rowcount
            print(f"✅ Deleted {signals_deleted} signals")
            
            # Commit all changes
            await session.commit()
            
            print("\n🎉 Successfully cleared all trading data!")
            print(f"📊 Summary:")
            print(f"   - Signals: {signals_deleted}")
            print(f"   - Signal Performance: {performance_deleted}")
            print(f"   - Backtest Data: {backtest_data_deleted}")
            print(f"   - Backtest Results: {backtest_results_deleted}")
            print(f"   - Backtest Trades: {backtest_trades_deleted}")
            print(f"   - Total records deleted: {signals_deleted + performance_deleted + backtest_data_deleted + backtest_results_deleted + backtest_trades_deleted}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing trading data: {e}")
            await session.rollback()
            raise

async def main():
    """Main function - AUTOMATIC VERSION"""
    print("🚀 AUTOMATIC CLEANUP: Clearing all trading data...")
    print("This includes:")
    print("- All signals")
    print("- All signal performance records")
    print("- All backtest data")
    print("- All backtest results")
    print("- All backtest trades")
    print()
    
    try:
        success = await clear_all_trading_data()
        if success:
            print("\n✅ Database cleanup completed successfully!")
            print("🚀 You can now start fresh with auto trading!")
        
    except Exception as e:
        print(f"\n❌ Failed to clear trading data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())