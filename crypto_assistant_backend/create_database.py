#!/usr/bin/env python3
"""
Create SQLite database and tables for the crypto trading application
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.database_models import *

def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Create a default trading settings record
        from app.database import SessionLocal
        from app.models.database_models import TradingSettings
        
        db = SessionLocal()
        try:
            # Check if default settings exist
            existing_settings = db.query(TradingSettings).filter(TradingSettings.user_id == 'default').first()
            if not existing_settings:
                default_settings = TradingSettings(user_id='default')
                db.add(default_settings)
                db.commit()
                print("✅ Default trading settings created!")
            else:
                print("✅ Default trading settings already exist!")
        except Exception as e:
            print(f"❌ Error creating default settings: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n🎉 Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)