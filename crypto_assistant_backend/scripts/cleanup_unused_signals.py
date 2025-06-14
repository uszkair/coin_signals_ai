#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Unused Signals
===============================================

This script removes signals from the database that don't have corresponding
trading performance entries. These are signals that were generated but never
actually traded.

Usage:
    python cleanup_unused_signals.py [--dry-run] [--confirm]
    
Options:
    --dry-run    Show what would be deleted without actually deleting
    --confirm    Skip confirmation prompt and proceed with deletion
"""

import asyncio
import argparse
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append('.')

from app.database import AsyncSessionLocal, engine
from app.models.database_models import Signal, SignalPerformance

async def get_unused_signals_count():
    """Get count of signals without performance entries"""
    async with AsyncSessionLocal() as db:
        query = text("""
            SELECT COUNT(*) as unused_count
            FROM crypto.signals s
            LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
            WHERE sp.signal_id IS NULL
        """)
        result = await db.execute(query)
        return result.fetchone()[0]

async def get_unused_signals_details():
    """Get details of signals without performance entries"""
    async with AsyncSessionLocal() as db:
        query = text("""
            SELECT s.id, s.symbol, s.signal_type, s.confidence, s.pattern, s.created_at
            FROM crypto.signals s
            LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
            WHERE sp.signal_id IS NULL
            ORDER BY s.created_at DESC
            LIMIT 10
        """)
        result = await db.execute(query)
        return result.fetchall()

async def delete_unused_signals():
    """Delete signals without performance entries"""
    async with AsyncSessionLocal() as db:
        try:
            # Delete unused signals
            query = text("""
                DELETE FROM crypto.signals
                WHERE id IN (
                    SELECT s.id
                    FROM crypto.signals s
                    LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
                    WHERE sp.signal_id IS NULL
                )
            """)
            result = await db.execute(query)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

async def get_trading_history_stats():
    """Get statistics about trading history"""
    async with AsyncSessionLocal() as db:
        query = text("""
            SELECT 
                COUNT(DISTINCT s.id) as total_signals,
                COUNT(DISTINCT sp.id) as traded_signals,
                COUNT(DISTINCT s.id) - COUNT(DISTINCT sp.id) as unused_signals
            FROM crypto.signals s
            LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
        """)
        result = await db.execute(query)
        return result.fetchone()

async def main():
    parser = argparse.ArgumentParser(description='Clean up unused signals from database')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt and proceed with deletion')
    
    args = parser.parse_args()
    
    print("🔍 Analyzing signal database...")
    print("=" * 50)
    
    # Get current statistics
    stats = await get_trading_history_stats()
    unused_count = await get_unused_signals_count()
    
    print(f"📊 Database Statistics:")
    print(f"   Total signals in database: {stats[0]}")
    print(f"   Signals with trading performance: {stats[1]}")
    print(f"   Unused signals (no trades): {unused_count}")
    print()
    
    if unused_count == 0:
        print("✅ No unused signals found. Database is clean!")
        return
    
    # Show sample of unused signals
    print(f"📋 Sample of unused signals (showing up to 10):")
    unused_details = await get_unused_signals_details()
    
    print(f"{'ID':<8} {'Symbol':<12} {'Type':<6} {'Confidence':<12} {'Pattern':<20} {'Created':<20}")
    print("-" * 80)
    
    for signal in unused_details:
        created_str = signal[5].strftime('%Y-%m-%d %H:%M') if signal[5] else 'N/A'
        print(f"{signal[0]:<8} {signal[1]:<12} {signal[2]:<6} {signal[3]:<12} {signal[4] or 'N/A':<20} {created_str:<20}")
    
    if len(unused_details) == 10:
        print(f"... and {unused_count - 10} more unused signals")
    
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print(f"Would delete {unused_count} unused signals")
        return
    
    # Confirmation
    if not args.confirm:
        print(f"⚠️  This will permanently delete {unused_count} unused signals from the database.")
        print("   These are signals that were generated but never actually traded.")
        print("   This action cannot be undone!")
        print()
        
        response = input("Do you want to proceed? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled.")
            return
    
    print(f"🗑️  Deleting {unused_count} unused signals...")
    
    try:
        deleted_count = await delete_unused_signals()
        print(f"✅ Successfully deleted {deleted_count} unused signals!")
        
        # Show updated statistics
        print("\n📊 Updated Database Statistics:")
        new_stats = await get_trading_history_stats()
        print(f"   Total signals in database: {new_stats[0]}")
        print(f"   Signals with trading performance: {new_stats[1]}")
        print(f"   Unused signals remaining: {new_stats[2]}")
        
        if new_stats[2] == 0:
            print("✅ Database cleanup complete! All remaining signals have trading performance data.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
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