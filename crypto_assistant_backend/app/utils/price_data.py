# app/utils/price_data.py

import httpx
import os
from datetime import datetime, timedelta

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass

async def get_binance_config():
    """Get Binance configuration from database settings"""
    try:
        from app.services.trading_settings_service import trading_settings_service
        risk_settings = await trading_settings_service.get_risk_management_settings()
        use_testnet = risk_settings.get('testnet_mode', True)
        
        # For now, we'll use Spot API for price data (more reliable)
        use_futures = False
        
        # Select URL based on settings
        if use_testnet:
            if use_futures:
                base_url = os.environ.get("BINANCE_FUTURES_TESTNET_URL", "https://testnet.binancefuture.com")
            else:
                base_url = os.environ.get("BINANCE_SPOT_TESTNET_URL", "https://testnet.binance.vision")
        else:
            if use_futures:
                base_url = os.environ.get("BINANCE_FUTURES_URL", "https://fapi.binance.com")
            else:
                base_url = os.environ.get("BINANCE_SPOT_URL", "https://api.binance.com")
        
        return {
            'base_url': base_url,
            'use_testnet': use_testnet,
            'use_futures': use_futures
        }
    except Exception as e:
        print(f"Error getting database config, using defaults: {e}")
        # Fallback to safe defaults
        return {
            'base_url': os.environ.get("BINANCE_SPOT_URL", "https://api.binance.com"),
            'use_testnet': False,
            'use_futures': False
        }

def get_api_credentials(use_testnet=False):
    """Get appropriate API credentials based on testnet mode"""
    if use_testnet:
        return {
            'api_key': os.environ.get("BINANCE_TESTNET_API_KEY"),
            'api_secret': os.environ.get("BINANCE_TESTNET_API_SECRET")
        }
    else:
        return {
            'api_key': os.environ.get("BINANCE_API_KEY"),
            'api_secret': os.environ.get("BINANCE_API_SECRET")
        }

async def get_historical_data(symbol: str, interval: str, days: int):
    """
    Get historical candlestick data for a single symbol from Binance API.
    
    Args:
        symbol: Single trading symbol (e.g., 'BTCUSDT'). If multiple symbols are passed
                as comma-separated string, only the first one will be used.
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days of historical data to fetch
        
    Returns:
        List of candlestick data dictionaries
        
    Raises:
        ValueError: If symbol contains multiple symbols
        httpx.HTTPStatusError: If API request fails
    """
    # Get configuration from database
    config = await get_binance_config()
    base_url = config['base_url']
    
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
    
    # Validate symbol format
    if not symbol or not symbol.isalnum():
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    limit = min(days * 24, 1000)  # max 1000 gyertya
    endpoint = f"/api/v3/klines"
    url = f"{base_url}{endpoint}"

    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_time,
        "endTime": end_time
    }

    # Get appropriate API credentials
    credentials = get_api_credentials(config['use_testnet'])
    headers = {}
    if credentials['api_key']:
        headers["X-MBX-APIKEY"] = credentials['api_key']

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            raw_data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise ValueError(f"Bad request to Binance API for symbol '{symbol}': {e.response.text}")
        else:
            raise

    candles = []
    for item in raw_data:
        candles.append({
            "timestamp": datetime.utcfromtimestamp(item[0] / 1000),
            "open": float(item[1]),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
            "volume": float(item[5])
        })

    return candles

async def get_current_price(symbol: str):
    """
    Get current price for a single symbol from Binance API.
    
    Args:
        symbol: Single trading symbol (e.g., 'BTCUSDT'). If multiple symbols are passed
                as comma-separated string, only the first one will be used.
                
    Returns:
        Current price as float
        
    Raises:
        ValueError: If symbol contains multiple symbols or is invalid
        httpx.HTTPStatusError: If API request fails
    """
    # Get configuration from database
    config = await get_binance_config()
    base_url = config['base_url']
    
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
    
    # Validate symbol format
    if not symbol or not symbol.isalnum():
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    endpoint = f"/api/v3/ticker/price"
    url = f"{base_url}{endpoint}"
    
    params = {
        "symbol": symbol
    }
    
    # Get appropriate API credentials
    credentials = get_api_credentials(config['use_testnet'])
    headers = {}
    if credentials['api_key']:
        headers["X-MBX-APIKEY"] = credentials['api_key']
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise ValueError(f"Bad request to Binance API for symbol '{symbol}': {e.response.text}")
        else:
            raise
    
    return float(data["price"])


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
