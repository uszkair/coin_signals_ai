#!/usr/bin/env python3
"""
Quick Signal Database Check
==========================

Quick check of signal database status without full cleanup functionality.
"""

import asyncio
import sys
from sqlalchemy import text

# Add the app directory to the path
sys.path.append('.')

from app.database import AsyncSessionLocal

async def quick_check():
    """Quick check of signal database"""
    try:
        async with AsyncSessionLocal() as db:
            # Get total signals
            total_query = text("SELECT COUNT(*) FROM crypto.signals")
            total_result = await db.execute(total_query)
            total_signals = total_result.fetchone()[0]
            
            # Get signals with performance
            with_perf_query = text("""
                SELECT COUNT(DISTINCT s.id) 
                FROM crypto.signals s 
                INNER JOIN crypto.signal_performance sp ON s.id = sp.signal_id
            """)
            with_perf_result = await db.execute(with_perf_query)
            signals_with_perf = with_perf_result.fetchone()[0]
            
            # Get signals without performance
            without_perf_query = text("""
                SELECT COUNT(*) 
                FROM crypto.signals s 
                LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id 
                WHERE sp.signal_id IS NULL
            """)
            without_perf_result = await db.execute(without_perf_query)
            signals_without_perf = without_perf_result.fetchone()[0]
            
            print(f"📊 Quick Database Check:")
            print(f"   Total signals: {total_signals}")
            print(f"   Signals with trading performance: {signals_with_perf}")
            print(f"   Signals without trading performance: {signals_without_perf}")
            print(f"   Percentage unused: {(signals_without_perf/total_signals*100):.1f}%" if total_signals > 0 else "   No signals found")
            
            return signals_without_perf
            
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return None

if __name__ == "__main__":
    try:
        unused_count = asyncio.run(quick_check())
        if unused_count is not None:
            print(f"\n✅ Database check complete. Found {unused_count} unused signals.")
        else:
            print("\n❌ Database check failed.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")