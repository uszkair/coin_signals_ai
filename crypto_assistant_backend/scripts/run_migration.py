#!/usr/bin/env python3
"""
Database migration script to add decision_factors and total_score columns
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    """Run the database migration"""
    
    # Database connection parameters
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/crypto_trading')
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Read migration SQL
        migration_file = Path(__file__).parent / "migrations" / "add_decision_factors.sql"
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("📄 Migration SQL loaded")
        
        # Execute migration
        await conn.execute(migration_sql)
        print("✅ Migration executed successfully")
        
        # Verify the changes
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_schema = 'crypto' 
              AND table_name = 'signals' 
              AND column_name IN ('decision_factors', 'total_score')
            ORDER BY column_name;
        """)
        
        print("\n📊 Verification results:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']}, default: {row['column_default']})")
        
        await conn.close()
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)