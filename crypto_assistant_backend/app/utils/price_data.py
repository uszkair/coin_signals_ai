# app/utils/price_data.py

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    import os
    # Load .env from project root (4 levels up from this file)
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
    load_dotenv(env_path)
except ImportError:
    # dotenv not available, use environment variables directly
    pass

# No SDK imports needed - using direct REST API

async def get_coinbase_config():
    """Get Coinbase Advanced Trade API configuration"""
    try:
        from app.services.trading_settings_service import get_trading_settings_service
        from app.database import get_sync_db
        
        # Get database session and settings service
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        risk_settings = settings_service.get_risk_management_settings()
        use_sandbox = risk_settings.get('testnet_mode', False)  # Default to production
        
        # Coinbase Advanced Trade API only has production
        base_url = os.environ.get("COINBASE_REST_API_URL", "https://api.coinbase.com")
        
        return {
            'base_url': base_url,
            'use_sandbox': False  # Always production for Advanced Trade API
        }
    except Exception as e:
        print(f"Error getting database config, using defaults: {e}")
        # Fallback to production defaults
        return {
            'base_url': os.environ.get("COINBASE_REST_API_URL", "https://api.coinbase.com"),
            'use_sandbox': False
        }

def get_api_credentials(use_sandbox=True):
    """Get appropriate API credentials based on sandbox mode"""
    if use_sandbox:
        return {
            'api_key': os.environ.get("COINBASE_SANDBOX_API_KEY"),
            'api_secret': os.environ.get("COINBASE_SANDBOX_API_SECRET"),
            'passphrase': os.environ.get("COINBASE_SANDBOX_PASSPHRASE")
        }
    else:
        return {
            'api_key': os.environ.get("COINBASE_API_KEY"),
            'api_secret': os.environ.get("COINBASE_API_SECRET"),
            'passphrase': os.environ.get("COINBASE_PASSPHRASE")
        }

def _convert_symbol_to_coinbase(legacy_symbol: str) -> str:
    """Convert legacy symbol format to Coinbase format
    
    Args:
        legacy_symbol: Symbol in legacy format (e.g., 'BTCUSDT')
        
    Returns:
        Symbol in Coinbase format (e.g., 'BTC-USD')
    """
    # Handle known unsupported symbols
    unsupported_symbols = {
        'BNBUSDT': 'BNB-USD is not available on Coinbase. Try BTC-USD, ETH-USD, ADA-USD, or other supported pairs.',
        'BNBUSD': 'BNB-USD is not available on Coinbase. Try BTC-USD, ETH-USD, ADA-USD, or other supported pairs.',
        'BNB-USD': 'BNB-USD is not available on Coinbase. Try BTC-USD, ETH-USD, ADA-USD, or other supported pairs.'
    }
    
    if legacy_symbol.upper() in unsupported_symbols:
        raise ValueError(unsupported_symbols[legacy_symbol.upper()])
    
    if legacy_symbol.endswith('USDT'):
        base = legacy_symbol[:-4]
        return f"{base}-USD"
    elif legacy_symbol.endswith('USDC'):
        base = legacy_symbol[:-4]
        return f"{base}-USDC"
    elif legacy_symbol.endswith('BTC'):
        base = legacy_symbol[:-3]
        return f"{base}-BTC"
    elif legacy_symbol.endswith('ETH'):
        base = legacy_symbol[:-3]
        return f"{base}-ETH"
    else:
        # If no known suffix, return as-is with dash
        if len(legacy_symbol) >= 6:
            return f"{legacy_symbol[:-3]}-{legacy_symbol[-3:]}"
        
        return legacy_symbol

def _convert_symbol_from_coinbase(coinbase_symbol: str) -> str:
    """Convert Coinbase symbol format to legacy format"""
    if '-' in coinbase_symbol:
        parts = coinbase_symbol.split('-')
        if len(parts) == 2:
            base, quote = parts
            if quote == 'USD':
                return f"{base}USDT"
            else:
                return f"{base}{quote}"
    return coinbase_symbol

async def get_historical_data(symbol: str, interval: str, days: int):
    """
    Get historical candlestick data for a single symbol using Coinbase Advanced Trade SDK.
    
    Args:
        symbol: Single trading symbol (e.g., 'BTCUSDT'). If multiple symbols are passed
                as comma-separated string, only the first one will be used.
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days of historical data to fetch
        
    Returns:
        List of candlestick data dictionaries
        
    Raises:
        ValueError: If symbol contains multiple symbols
        Exception: If API request fails
    """
    try:
        from coinbase.rest import RESTClient
    except ImportError:
        raise ValueError("coinbase-advanced-py SDK not installed. Run: pip install coinbase-advanced-py")
    
    # Get API credentials
    api_key = os.environ.get("COINBASE_API_KEY")
    private_key = os.environ.get("COINBASE_PRIVATE_KEY")
    
    if not api_key or not private_key:
        raise ValueError("Coinbase API credentials not found in environment variables")
    
    print("SDK: Using Coinbase Advanced Trade SDK for historical data")
    
    # Handle case where multiple symbols might be passed accidentally
    if ',' in symbol:
        symbols = [s.strip() for s in symbol.split(',') if s.strip()]  # Filter out empty strings
        if len(symbols) > 1:
            print(f"Warning: Multiple symbols detected ({symbol}). Using only the first symbol: {symbols[0]}")
            symbol = symbols[0]
        elif len(symbols) == 1:
            symbol = symbols[0]
        else:
            raise ValueError(f"No valid symbols found in: {symbol}")
    
    # Convert symbol to Coinbase format
    coinbase_symbol = _convert_symbol_to_coinbase(symbol)
    
    # Validate symbol format
    if not symbol or not symbol.replace('-', '').isalnum():
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    # Map intervals to Coinbase SDK granularity strings
    interval_mapping = {
        '1m': 'ONE_MINUTE',
        '5m': 'FIVE_MINUTE',
        '15m': 'FIFTEEN_MINUTE',
        '1h': 'ONE_HOUR',
        '6h': 'SIX_HOUR',
        '1d': 'ONE_DAY'
    }
    
    granularity = interval_mapping.get(interval)
    if not granularity:
        raise ValueError(f"Unsupported interval: {interval}. Supported intervals: {list(interval_mapping.keys())}")
    
    # Calculate time range with Coinbase API limits
    # Coinbase has a 300 candle limit, so we need to adjust the time range
    max_days_for_interval = {
        'ONE_MINUTE': 12,      # 1m: max 12 days
        'FIVE_MINUTE': 62,     # 5m: max 62 days
        'FIFTEEN_MINUTE': 187, # 15m: max 187 days
        'ONE_HOUR': 12,        # 1h: max 12 days
        'SIX_HOUR': 75,        # 6h: max 75 days
        'ONE_DAY': 300         # 1d: max 300 days
    }
    
    # Limit days based on granularity to avoid exceeding 300 candles
    max_allowed_days = max_days_for_interval.get(granularity, days)
    if days > max_allowed_days:
        print(f"WARNING: Requested {days} days exceeds Coinbase limit for {interval} interval. Limiting to {max_allowed_days} days.")
        days = max_allowed_days
    
    # Calculate unix timestamps (SDK requires unix timestamps, not ISO format)
    import time
    end_time = int(time.time())
    start_time = end_time - (days * 24 * 3600)
    
    print(f"SDK: Fetching candles for {coinbase_symbol} ({days} days, {interval} interval)")
    print(f"SDK: Time range: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
    
    try:
        # Use Coinbase Advanced Trade SDK
        client = RESTClient(
            api_key=api_key,
            api_secret=private_key
        )
        
        print(f"SDK: Calling get_candles for {coinbase_symbol}...")
        response = client.get_candles(
            product_id=coinbase_symbol,
            start=start_time,
            end=end_time,
            granularity=granularity
        )
        
        # Extract candles from response
        if hasattr(response, 'candles'):
            raw_data = response.candles
        elif isinstance(response, dict) and 'candles' in response:
            raw_data = response['candles']
        else:
            print(f"WARNING: Unexpected response format: {type(response)}")
            raw_data = []
        
        if not raw_data:
            print(f"WARNING: No data available from SDK for {coinbase_symbol}")
            return []
        
        # Convert to our format
        # Coinbase SDK returns: {'start': '1750960800', 'low': '107179.42', 'high': '107654.74', 'open': '107249.96', 'close': '107356.5', 'volume': '97.08564877'}
        candles = []
        for item in raw_data:
            candles.append({
                "timestamp": datetime.utcfromtimestamp(int(item['start'])),
                "open": float(item['open']),
                "high": float(item['high']),
                "low": float(item['low']),
                "close": float(item['close']),
                "volume": float(item['volume'])
            })
        
        # Sort by timestamp (oldest first)
        candles.sort(key=lambda x: x["timestamp"])
        
        print(f"SDK: Final result: {len(candles)} candles for {coinbase_symbol}")
        return candles
        
    except Exception as e:
        print(f"SDK Error fetching historical data for {coinbase_symbol}: {e}")
        raise ValueError(f"Failed to get historical data for symbol '{coinbase_symbol}': {str(e)}")

async def get_current_price(symbol: str):
    """
    Get current price for a single symbol using Coinbase Advanced Trade SDK.
    
    Args:
        symbol: Single trading symbol (e.g., 'BTCUSDT'). If multiple symbols are passed
                as comma-separated string, only the first one will be used.
                
    Returns:
        Current price as float
        
    Raises:
        ValueError: If symbol contains multiple symbols or is invalid
        Exception: If API request fails
    """
    try:
        from coinbase.rest import RESTClient
    except ImportError:
        raise ValueError("coinbase-advanced-py SDK not installed. Run: pip install coinbase-advanced-py")
    
    # Get API credentials
    api_key = os.environ.get("COINBASE_API_KEY")
    private_key = os.environ.get("COINBASE_PRIVATE_KEY")
    
    if not api_key or not private_key:
        raise ValueError("Coinbase API credentials not found in environment variables")
    
    # Handle case where multiple symbols might be passed accidentally
    if ',' in symbol:
        symbols = [s.strip() for s in symbol.split(',') if s.strip()]  # Filter out empty strings
        if len(symbols) > 1:
            print(f"Warning: Multiple symbols detected ({symbol}). Using only the first symbol: {symbols[0]}")
            symbol = symbols[0]
        elif len(symbols) == 1:
            symbol = symbols[0]
        else:
            raise ValueError(f"No valid symbols found in: {symbol}")
    
    # Convert symbol to Coinbase format
    coinbase_symbol = _convert_symbol_to_coinbase(symbol)
    
    # Validate symbol format
    if not symbol or not symbol.replace('-', '').isalnum():
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    try:
        # Use Coinbase Advanced Trade SDK
        client = RESTClient(
            api_key=api_key,
            api_secret=private_key
        )
        
        print(f"SDK: Getting price for {coinbase_symbol}...")
        product = client.get_product(coinbase_symbol)
        
        # Extract price from response
        if hasattr(product, 'price'):
            price = float(product.price)
        elif isinstance(product, dict) and 'price' in product:
            price = float(product['price'])
        else:
            raise ValueError(f"No price data available for {coinbase_symbol}")
        
        print(f"SDK: Price for {coinbase_symbol} = ${price}")
        return price
            
    except Exception as e:
        print(f"Error fetching current price for {coinbase_symbol}: {e}")
        raise ValueError(f"Failed to get current price for symbol '{coinbase_symbol}': {str(e)}")

async def get_multiple_historical_data(symbols: str, interval: str, days: int):
    """
    Get historical data for multiple symbols.
    
    Args:
        symbols: Comma-separated string of symbols (e.g., 'BTCUSDT,ETHUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days of historical data to fetch
        
    Returns:
        Dictionary with symbol as key and candlestick data as value
        
    Example:
        data = await get_multiple_historical_data('BTCUSDT,ETHUSDT', '1h', 7)
        btc_data = data['BTCUSDT']
        eth_data = data['ETHUSDT']
    """
    symbol_list = [s.strip() for s in symbols.split(',')]
    results = {}
    
    for symbol in symbol_list:
        try:
            candles = await get_historical_data(symbol, interval, days)
            results[symbol] = candles
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            results[symbol] = []
    
    return results

async def get_multiple_current_prices(symbols: str):
    """
    Get current prices for multiple symbols.
    
    Args:
        symbols: Comma-separated string of symbols (e.g., 'BTCUSDT,ETHUSDT')
        
    Returns:
        Dictionary with symbol as key and current price as value
        
    Example:
        prices = await get_multiple_current_prices('BTCUSDT,ETHUSDT')
        btc_price = prices['BTCUSDT']
        eth_price = prices['ETHUSDT']
    """
    symbol_list = [s.strip() for s in symbols.split(',')]
    results = {}
    
    for symbol in symbol_list:
        try:
            price = await get_current_price(symbol)
            results[symbol] = price
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            results[symbol] = 0.0
    
    return results
