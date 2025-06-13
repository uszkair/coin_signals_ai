#!/usr/bin/env python3
"""
Run settings migration to add comprehensive settings to trading_settings table
"""

import asyncio
import logging
from sqlalchemy import text
from app.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the settings migration"""
    try:
        # Read migration SQL
        with open('migrations/add_comprehensive_settings.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.strip():
                    logger.info(f"Executing: {statement[:100]}...")
                    conn.execute(text(statement))
            
            conn.commit()
        
        logger.info("✅ Settings migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    if not success:
        exit(1)