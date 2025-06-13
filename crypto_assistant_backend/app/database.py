# app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://crypto_user:crypto_password123@localhost:5432/crypto_signals"
)

ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://crypto_user:crypto_password123@localhost:5432/crypto_signals"
)

# Sync engine for migrations
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for FastAPI
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync dependency for testing
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()