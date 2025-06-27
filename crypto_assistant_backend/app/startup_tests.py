"""
Startup Tests
Tests that run when the application starts to verify system health
"""

import asyncio
import logging
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def should_run_startup_tests() -> bool:
    """
    Determine if startup tests should be run based on environment variables or settings.
    
    Environment variables checked (in order of priority):
    1. SKIP_STARTUP_TESTS=true/false - explicit control
    2. RUN_STARTUP_TESTS=true/false - explicit control
    3. ENVIRONMENT=production/development - auto-decide
    4. Default: True (run tests)
    
    Returns:
        bool: True if tests should run, False to skip
    """
    # Check explicit skip flag
    skip_tests = os.getenv('SKIP_STARTUP_TESTS', '').lower()
    if skip_tests in ['true', '1', 'yes']:
        logger.info("STARTUP TESTS SKIPPED: SKIP_STARTUP_TESTS=true")
        return False
    elif skip_tests in ['false', '0', 'no']:
        logger.info("STARTUP TESTS ENABLED: SKIP_STARTUP_TESTS=false")
        return True
    
    # Check explicit run flag
    run_tests = os.getenv('RUN_STARTUP_TESTS', '').lower()
    if run_tests in ['true', '1', 'yes']:
        logger.info("STARTUP TESTS ENABLED: RUN_STARTUP_TESTS=true")
        return True
    elif run_tests in ['false', '0', 'no']:
        logger.info("STARTUP TESTS SKIPPED: RUN_STARTUP_TESTS=false")
        return False
    
    # Check environment type
    environment = os.getenv('ENVIRONMENT', '').lower()
    if environment == 'production':
        logger.info("STARTUP TESTS ENABLED: Production environment detected")
        return True
    elif environment == 'development':
        logger.info("STARTUP TESTS OPTIONAL: Development environment (use RUN_STARTUP_TESTS to control)")
        # In development, default to True but can be overridden
        return True
    
    # Default behavior: run tests
    logger.info("STARTUP TESTS ENABLED: Default behavior (use SKIP_STARTUP_TESTS=true to disable)")
    return True


async def test_coinbase_connectivity() -> Dict[str, Any]:
    """Test Coinbase API connectivity"""
    try:
        from app.utils.price_data import get_current_price, get_coinbase_config
        
        # Get current configuration
        config = await get_coinbase_config()
        
        # Test with a simple price request
        test_symbol = "BTCUSDT"
        price = await get_current_price(test_symbol)
        
        # TEMPORARY: Force failure to test startup prevention
        # raise Exception("SIMULATED FAILURE - Testing startup prevention")
        
        return {
            "test": "coinbase_connectivity",
            "status": "PASS",
            "config": config,
            "test_symbol": test_symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "coinbase_connectivity",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_database_settings() -> Dict[str, Any]:
    """Test database settings access"""
    try:
        from app.services.trading_settings_service import get_trading_settings_service
        from app.database import get_sync_db
        
        # Get database session and settings service
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        
        # Test getting risk management settings
        risk_settings = settings_service.get_risk_management_settings()
        
        return {
            "test": "database_settings",
            "status": "PASS",
            "testnet_mode": risk_settings.get('testnet_mode'),
            "max_daily_trades": risk_settings.get('max_daily_trades'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "database_settings",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_trading_service() -> Dict[str, Any]:
    """Test trading service initialization"""
    try:
        from app.services.coinbase_trading import CoinbaseTrader
        
        # Create trader instance
        trader = CoinbaseTrader()
        
        # Get account info (requires valid API keys)
        account_info = await trader.get_account_info()
        
        return {
            "test": "trading_service",
            "status": "PASS",
            "use_sandbox": trader.use_sandbox,
            "environment": "Coinbase Production (SDK)",
            "api_connected": trader.client is not None,
            "account_type": account_info.get('account_type', 'UNKNOWN'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "trading_service",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_historical_data() -> Dict[str, Any]:
    """Test historical data retrieval with SDK"""
    try:
        from app.utils.price_data import get_historical_data
        
        # Test historical data for multiple symbols
        test_symbols = ["BTCUSDT", "ADAUSDT"]
        results = {}
        
        for symbol in test_symbols:
            candles = await get_historical_data(symbol, "1h", 7)
            results[symbol] = {
                "candles_count": len(candles),
                "has_data": len(candles) > 0,
                "latest_price": candles[-1]["close"] if candles else None
            }
        
        return {
            "test": "historical_data",
            "status": "PASS",
            "symbols_tested": test_symbols,
            "results": results,
            "sdk_integration": "PASS - Using Coinbase SDK",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "historical_data",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_signal_generation() -> Dict[str, Any]:
    """Test signal generation functionality"""
    try:
        from app.services.signal_engine import get_current_signal
        
        # Test signal generation for multiple symbols
        test_symbols = ["BTCUSDT", "ADAUSDT"]
        results = {}
        
        for symbol in test_symbols:
            signal = await get_current_signal(symbol, "1h")
            results[symbol] = {
                "signal": signal.get("signal"),
                "confidence": signal.get("confidence"),
                "entry_price": signal.get("entry_price"),
                "current_price": signal.get("current_price"),
                "pattern": signal.get("pattern"),
                "trend": signal.get("trend")
            }
        
        return {
            "test": "signal_generation",
            "status": "PASS",
            "symbols_tested": test_symbols,
            "results": results,
            "sdk_integration": "PASS - Using Coinbase SDK for data",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "signal_generation",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_coinbase_adapter() -> Dict[str, Any]:
    """Test Coinbase adapter service"""
    try:
        from app.services.exchanges.coinbase_adapter import CoinbaseAdapter
        
        # Create adapter instance
        adapter = CoinbaseAdapter()
        
        # Test connection and price fetch
        test_symbol = "BTCUSDT"
        price = await adapter.get_current_price(test_symbol)
        
        return {
            "test": "coinbase_adapter",
            "status": "PASS",
            "adapter_initialized": adapter.client is not None,
            "test_symbol": test_symbol,
            "price": price,
            "sdk_integration": "PASS - Using Coinbase SDK",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "coinbase_adapter",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_ai_ml_services() -> Dict[str, Any]:
    """Test AI/ML signal generation services"""
    try:
        from app.services.ml_signal_generator import generate_ai_signal
        
        # Test AI signal generation
        test_symbol = "BTCUSDT"
        ai_signal = await generate_ai_signal(test_symbol, "1h")
        
        return {
            "test": "ai_ml_services",
            "status": "PASS",
            "test_symbol": test_symbol,
            "ai_signal": ai_signal.get("ai_signal"),
            "ai_confidence": ai_signal.get("ai_confidence"),
            "ml_available": ai_signal.get("ml_available"),
            "market_regime": ai_signal.get("market_regime"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "ai_ml_services",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_technical_indicators() -> Dict[str, Any]:
    """Test technical indicators calculation"""
    try:
        from app.services.technical_indicators import calculate_professional_indicators
        from app.utils.price_data import get_historical_data
        
        # Get historical data for indicators
        candles = await get_historical_data("BTCUSDT", "1h", 7)
        
        # Calculate indicators
        indicators = calculate_professional_indicators(candles)
        
        return {
            "test": "technical_indicators",
            "status": "PASS",
            "candles_used": len(candles),
            "indicators_available": list(indicators.keys()),
            "rsi_value": indicators.get("rsi", {}).get("value"),
            "macd_signal": indicators.get("macd", {}).get("signal_type"),
            "market_assessment": indicators.get("market_assessment", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "technical_indicators",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def run_startup_tests() -> Dict[str, Any]:
    """Run all startup tests (if enabled)"""
    
    # Check if startup tests should be run
    if not should_run_startup_tests():
        logger.info("Startup tests skipped by configuration")
        return {
            "startup_tests": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": True,
                "success_rate": "100.0%",
                "message": "Tests skipped by configuration",
                "timestamp": datetime.now().isoformat()
            },
            "results": []
        }
    
    logger.info("Running comprehensive startup tests...")
    
    tests = [
        test_database_settings,
        test_coinbase_connectivity,
        test_trading_service,
        test_coinbase_adapter,
        test_historical_data,
        test_signal_generation,
        test_technical_indicators,
        test_ai_ml_services
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
            
            if result["status"] == "PASS":
                passed += 1
                logger.info(f"PASS {result['test']}: PASSED")
            else:
                failed += 1
                logger.error(f"FAIL {result['test']}: FAILED - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            failed += 1
            error_result = {
                "test": test_func.__name__,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(error_result)
            logger.error(f"ERROR {test_func.__name__}: ERROR - {str(e)}")
    
    summary = {
        "startup_tests": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "skipped": False,
            "success_rate": f"{(passed/len(tests)*100):.1f}%",
            "timestamp": datetime.now().isoformat()
        },
        "results": results
    }
    
    if failed == 0:
        logger.info(f"SUCCESS All startup tests passed! ({passed}/{len(tests)})")
    else:
        logger.warning(f"WARNING {failed} startup test(s) failed. ({passed}/{len(tests)} passed)")
    
    return summary


def run_startup_tests_sync():
    """Synchronous wrapper for startup tests"""
    try:
        return asyncio.run(run_startup_tests())
    except Exception as e:
        logger.error(f"Failed to run startup tests: {e}")
        return {
            "startup_tests": {
                "total": 0,
                "passed": 0,
                "failed": 1,
                "success_rate": "0.0%",
                "timestamp": datetime.now().isoformat()
            },
            "results": [{
                "test": "startup_tests_runner",
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }]
        }


if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.path.append('.')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    results = run_startup_tests_sync()
    
    # Print summary
    print("\n" + "="*60)
    print("STARTUP TESTS SUMMARY")
    print("="*60)
    summary = results["startup_tests"]
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success rate: {summary['success_rate']}")
    print("="*60)