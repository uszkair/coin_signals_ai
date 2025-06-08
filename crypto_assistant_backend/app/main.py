from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.routers import signal, history, portfolio, ai, trading, ml_ai, auto_trading
from app.services.auto_trading_scheduler import start_auto_trading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Trading Assistant API")

# CORS beállítások (React frontend localhost:5173-hoz)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerek regisztrálása
app.include_router(signal.router, prefix="/api/signal", tags=["Signal"])
app.include_router(signal.router, prefix="/api/signals", tags=["Signals"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(history.router, prefix="/api", tags=["Trade History"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(ai.router, prefix="/api", tags=["AI"])
app.include_router(trading.router)
app.include_router(ml_ai.router)
app.include_router(auto_trading.router)  # Auto-trading endpoints


@app.on_event("startup")
async def startup_event():
    """Start background services on application startup"""
    logger.info("Starting Crypto Trading Assistant API...")
    
    # Start auto-trading scheduler in background
    asyncio.create_task(start_auto_trading())
    logger.info("Auto-trading scheduler started in background")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of background services"""
    logger.info("Shutting down Crypto Trading Assistant API...")
    
    from app.services.auto_trading_scheduler import stop_auto_trading
    stop_auto_trading()
    logger.info("Auto-trading scheduler stopped")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Crypto Trading Assistant API running with Auto-Trading support",
        "features": [
            "Signal Generation",
            "Manual Trading",
            "Auto Trading Scheduler",
            "Risk Management",
            "Real Binance Integration"
        ]
    }
