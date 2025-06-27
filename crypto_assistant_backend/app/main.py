from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.routers import signal, history, portfolio, ai, trading, ml_ai, auto_trading, websocket, backtest, settings, notifications

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
app.include_router(websocket.router)  # WebSocket endpoints
app.include_router(backtest.router)  # Backtest endpoints
app.include_router(settings.router)  # Settings endpoints
app.include_router(notifications.router, prefix="/api/notifications")  # Notifications endpoints


@app.on_event("startup")
async def startup_event():
    """Start background services on application startup"""
    logger.info("Starting Crypto Trading Assistant API...")
    
    # Load trading settings first to cache them
    try:
        from app.services.trading_settings_service import get_trading_settings_service
        from app.database import get_sync_db
        
        # Get database session and settings service
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        settings = settings_service.get_settings()
        testnet_mode = getattr(settings, 'testnet_mode', True) if settings else True
        logger.info(f"Trading settings loaded and cached: testnet_mode={testnet_mode}")
    except Exception as e:
        logger.error(f"Failed to load trading settings: {e}")
    
    # Initialize global trader with database settings
    try:
        from app.services.coinbase_trading import initialize_global_trader
        trader = initialize_global_trader()
        logger.info(f"Global trader initialized: {'Sandbox' if trader.use_sandbox else 'Production'} mode")
    except Exception as e:
        logger.error(f"Failed to initialize global trader: {e}")
    
    # Run startup tests - OPTIONAL: Can be disabled via environment variables
    try:
        from app.startup_tests import run_startup_tests
        test_results = await run_startup_tests()
        
        # Store test results for health check endpoint
        app.state.startup_tests = test_results
        
        # Log summary
        summary = test_results["startup_tests"]
        
        # Check if tests were skipped
        if summary.get("skipped", False):
            logger.info(f"INFO Startup tests skipped by configuration")
            logger.info("INFO Application starting without startup validation")
        elif summary["failed"] == 0:
            logger.info(f"SUCCESS All startup tests passed ({summary['passed']}/{summary['total']})")
        else:
            # WARNING: Log failures but allow application to start (configurable behavior)
            failed_tests = []
            for result in test_results.get("results", []):
                if result.get("status") in ["FAIL", "ERROR"]:
                    failed_tests.append(f"{result.get('test', 'unknown')}: {result.get('error', 'unknown error')}")
            
            error_msg = f"WARNING: {summary['failed']} startup tests failed. Application starting with degraded functionality."
            logger.warning(error_msg)
            logger.warning("Failed tests:")
            for test_error in failed_tests:
                logger.warning(f"  - {test_error}")
            
            # Check if we should fail hard on test failures (production safety)
            import os
            fail_on_test_errors = os.getenv('FAIL_ON_STARTUP_TEST_ERRORS', 'false').lower() in ['true', '1', 'yes']
            
            if fail_on_test_errors:
                # Raise exception to prevent application startup
                raise RuntimeError(f"Startup tests failed: {summary['failed']}/{summary['total']} tests failed. "
                                 f"Critical systems are not operational. Check logs for details.")
            else:
                logger.warning("INFO Application starting despite test failures (set FAIL_ON_STARTUP_TEST_ERRORS=true to prevent this)")
            
    except Exception as e:
        error_msg = f"STARTUP WARNING: Could not run startup tests: {e}"
        logger.warning(error_msg)
        app.state.startup_tests = {"error": str(e)}
        
        # Check if we should fail hard on test execution errors
        import os
        fail_on_test_errors = os.getenv('FAIL_ON_STARTUP_TEST_ERRORS', 'false').lower() in ['true', '1', 'yes']
        
        if fail_on_test_errors:
            # Raise exception to prevent application startup
            raise RuntimeError(f"Startup tests could not be executed: {e}. Application cannot start safely.")
        else:
            logger.warning("INFO Application starting despite startup test execution error")
    
    # Auto-trading scheduler starts AUTOMATICALLY as background service
    try:
        from app.services.auto_trading_scheduler import auto_trading_scheduler
        asyncio.create_task(auto_trading_scheduler.start_monitoring())
        logger.info("SUCCESS Auto-trading scheduler started automatically as background service")
        logger.info("INFO Scheduler will monitor markets continuously (auto-trading can be enabled/disabled via settings)")
    except Exception as e:
        logger.error(f"Failed to start auto-trading scheduler: {e}")
    


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of background services"""
    logger.info("Shutting down Crypto Trading Assistant API...")
    
    # Scheduler will stop automatically when the application shuts down
    logger.info("Auto-trading scheduler will stop with application shutdown")


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
            "Real Coinbase Integration"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint with startup test results"""
    startup_tests = getattr(app.state, 'startup_tests', None)
    
    if startup_tests is None:
        return {
            "status": "unknown",
            "message": "Startup tests not yet completed",
            "startup_tests": None
        }
    
    if "error" in startup_tests:
        return {
            "status": "warning",
            "message": "Startup tests failed to run, but application is operational",
            "error": startup_tests["error"]
        }
    
    summary = startup_tests.get("startup_tests", {})
    failed_count = summary.get("failed", 0)
    skipped = summary.get("skipped", False)
    
    if skipped:
        status = "healthy"
        message = "Application operational (startup tests skipped by configuration)"
    elif failed_count == 0:
        status = "healthy"
        message = f"All systems operational ({summary.get('passed', 0)}/{summary.get('total', 0)} tests passed)"
    else:
        status = "degraded"
        message = f"Some systems have issues ({failed_count} tests failed, but application is running)"
    
    return {
        "status": status,
        "message": message,
        "startup_tests": startup_tests
    }
