#!/usr/bin/env python3
"""
Clear All Trading History
========================

This script completely clears all trading history from the database:
- All signals
- All signal performance data
- All trading history

⚠️ WARNING: This operation is IRREVERSIBLE! ⚠️

Usage:
    python clear_all_trading_history.py [--confirm]
    
Options:
    --confirm    Skip confirmation prompt and proceed with deletion
"""

import asyncio
import argparse
import sys
from datetime import datetime
from sqlalchemy import text

# Add the app directory to the path
sys.path.append('.')

from app.database import AsyncSessionLocal

async def get_current_counts():
    """Get current counts of all trading data"""
    async with AsyncSessionLocal() as db:
        try:
            # Get signal performance count
            perf_query = text("SELECT COUNT(*) FROM crypto.signal_performance")
            perf_result = await db.execute(perf_query)
            perf_count = perf_result.fetchone()[0]
            
            # Get signals count
            signals_query = text("SELECT COUNT(*) FROM crypto.signals")
            signals_result = await db.execute(signals_query)
            signals_count = signals_result.fetchone()[0]
            
            return {
                'signals': signals_count,
                'performance': perf_count
            }
        except Exception as e:
            print(f"❌ Error getting counts: {str(e)}")
            return None

async def clear_all_trading_data():
    """Clear all trading history data"""
    async with AsyncSessionLocal() as db:
        try:
            # Start transaction
            await db.begin()
            
            # Delete signal performance first (due to foreign key constraint)
            perf_query = text("DELETE FROM crypto.signal_performance")
            perf_result = await db.execute(perf_query)
            perf_deleted = perf_result.rowcount
            
            # Delete all signals
            signals_query = text("DELETE FROM crypto.signals")
            signals_result = await db.execute(signals_query)
            signals_deleted = signals_result.rowcount
            
            # Commit transaction
            await db.commit()
            
            return {
                'signals_deleted': signals_deleted,
                'performance_deleted': perf_deleted
            }
            
        except Exception as e:
            await db.rollback()
            raise e

async def reset_sequences():
    """Reset auto-increment sequences"""
    async with AsyncSessionLocal() as db:
        try:
            # Reset signals sequence
            await db.execute(text("ALTER SEQUENCE crypto.signals_id_seq RESTART WITH 1"))
            
            # Reset signal_performance sequence
            await db.execute(text("ALTER SEQUENCE crypto.signal_performance_id_seq RESTART WITH 1"))
            
            await db.commit()
            print("✅ Database sequences reset to start from 1")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not reset sequences: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description='Clear all trading history from database')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt and proceed with deletion')
    
    args = parser.parse_args()
    
    print("🗑️  CLEAR ALL TRADING HISTORY")
    print("=" * 50)
    print("⚠️  WARNING: This will permanently delete ALL trading data!")
    print("   - All signals")
    print("   - All signal performance data")
    print("   - Complete trading history")
    print()
    
    # Get current counts
    print("📊 Checking current database content...")
    counts = await get_current_counts()
    
    if counts is None:
        print("❌ Could not connect to database. Exiting.")
        return 1
    
    print(f"   Signals in database: {counts['signals']}")
    print(f"   Performance records: {counts['performance']}")
    print()
    
    if counts['signals'] == 0 and counts['performance'] == 0:
        print("✅ Database is already empty. Nothing to delete.")
        return 0
    
    # Confirmation
    if not args.confirm:
        print("⚠️  This action is IRREVERSIBLE!")
        print("   All trading history will be permanently lost.")
        print("   You will need to start fresh with new trading data.")
        print()
        
        response = input("Are you absolutely sure you want to delete ALL trading history? (type 'DELETE ALL' to confirm): ").strip()
        if response != 'DELETE ALL':
            print("❌ Operation cancelled. Trading history preserved.")
            return 0
    
    print(f"🗑️  Deleting all trading history...")
    
    try:
        result = await clear_all_trading_data()
        
        print(f"✅ Successfully deleted all trading history!")
        print(f"   Signals deleted: {result['signals_deleted']}")
        print(f"   Performance records deleted: {result['performance_deleted']}")
        
        # Reset sequences
        await reset_sequences()
        
        # Verify deletion
        print("\n🔍 Verifying deletion...")
        final_counts = await get_current_counts()
        if final_counts:
            print(f"   Signals remaining: {final_counts['signals']}")
            print(f"   Performance records remaining: {final_counts['performance']}")
            
            if final_counts['signals'] == 0 and final_counts['performance'] == 0:
                print("✅ Database successfully cleared! Ready for fresh trading data.")
            else:
                print("⚠️  Some data may still remain in database.")
        
    except Exception as e:
        print(f"❌ Error during deletion: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)