"""
Startup Tests
Tests that run when the application starts to verify system health
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def test_binance_connectivity() -> Dict[str, Any]:
    """Test Binance API connectivity"""
    try:
        from app.utils.price_data import get_current_price, get_binance_config
        
        # Get current configuration
        config = await get_binance_config()
        
        # Test with a simple price request
        test_symbol = "BTCUSDT"
        price = await get_current_price(test_symbol)
        
        return {
            "test": "binance_connectivity",
            "status": "PASS",
            "config": config,
            "test_symbol": test_symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "test": "binance_connectivity",
            "status": "FAIL",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_database_settings() -> Dict[str, Any]:
    """Test database settings access"""
    try:
        from app.services.trading_settings_service import trading_settings_service
        
        # Test getting risk management settings
        risk_settings = await trading_settings_service.get_risk_management_settings()
        
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
        from app.services.binance_trading import BinanceTrader
        
        # Create trader instance
        trader = BinanceTrader()
        
        # Get account info (will be simulated if no API keys)
        account_info = await trader.get_account_info()
        
        return {
            "test": "trading_service",
            "status": "PASS",
            "testnet": trader.testnet,
            "use_futures": trader.use_futures,
            "base_url": trader.base_url,
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


async def run_startup_tests() -> Dict[str, Any]:
    """Run all startup tests"""
    logger.info("Running startup tests...")
    
    tests = [
        test_database_settings,
        test_binance_connectivity,
        test_trading_service
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
                logger.info(f"✅ {result['test']}: PASSED")
            else:
                failed += 1
                logger.error(f"❌ {result['test']}: FAILED - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            failed += 1
            error_result = {
                "test": test_func.__name__,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(error_result)
            logger.error(f"💥 {test_func.__name__}: ERROR - {str(e)}")
    
    summary = {
        "startup_tests": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed/len(tests)*100):.1f}%",
            "timestamp": datetime.now().isoformat()
        },
        "results": results
    }
    
    if failed == 0:
        logger.info(f"🎉 All startup tests passed! ({passed}/{len(tests)})")
    else:
        logger.warning(f"⚠️ {failed} startup test(s) failed. ({passed}/{len(tests)} passed)")
    
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