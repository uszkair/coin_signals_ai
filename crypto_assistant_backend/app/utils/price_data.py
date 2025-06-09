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
        
        # For price data, use Spot API for testnet (more reliable for price queries)
        # But use Futures for mainnet if available
        if use_testnet:
            use_futures = False  # Use Spot for testnet price data
        else:
            use_futures = False  # Use Spot for mainnet price data too (more symbols available)
        
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
        # Fallback to safe defaults (mainnet spot)
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
    Uses pagination to fetch large amounts of data beyond the 1000 candle API limit.
    
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
    # For historical data, always use mainnet API as it has more complete data
    # and doesn't require authentication for public endpoints
    base_url = "https://api.binance.com"
    print(f"📡 Using mainnet API for historical data: {base_url}")
    
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
    
    endpoint = f"/api/v3/klines"
    url = f"{base_url}{endpoint}"

    # Calculate total candles needed based on interval
    interval_hours = {
        '1m': 1/60, '3m': 3/60, '5m': 5/60, '15m': 15/60, '30m': 30/60,
        '1h': 1, '2h': 2, '4h': 4, '6h': 6, '8h': 8, '12h': 12,
        '1d': 24, '3d': 72, '1w': 168, '1M': 720  # Approximate for 1M
    }
    
    hours_per_candle = interval_hours.get(interval, 1)
    total_candles_needed = int((days * 24) / hours_per_candle)
    
    print(f"📊 Fetching {total_candles_needed} candles for {symbol} ({days} days, {interval} interval)")

    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

    # Historical data is public, no API key needed
    headers = {}

    all_candles = []
    current_end_time = end_time
    max_requests = 10  # Limit to prevent infinite loops
    request_count = 0
    
    async with httpx.AsyncClient() as client:
        while len(all_candles) < total_candles_needed and request_count < max_requests:
            request_count += 1
            limit = min(1000, total_candles_needed - len(all_candles))
            
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "endTime": current_end_time
            }
            
            print(f"📡 API request #{request_count}: fetching {limit} candles ending at {datetime.fromtimestamp(current_end_time/1000)}")

            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                raw_data = response.json()
                
                if not raw_data:
                    print(f"⚠️ No more data available from API")
                    break
                
                # Convert to our format
                batch_candles = []
                for item in raw_data:
                    batch_candles.append({
                        "timestamp": datetime.utcfromtimestamp(item[0] / 1000),
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5])
                    })
                
                # Add to beginning of list (since we're going backwards in time)
                all_candles = batch_candles + all_candles
                
                # Update end time for next request (use the timestamp of the first candle - 1ms)
                if raw_data:
                    current_end_time = raw_data[0][0] - 1
                    
                print(f"✅ Fetched {len(batch_candles)} candles, total: {len(all_candles)}")
                
                # Check if we've reached the start time
                if raw_data and raw_data[0][0] <= start_time:
                    print(f"📅 Reached start time, stopping")
                    break
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    raise ValueError(f"Bad request to Binance API for symbol '{symbol}': {e.response.text}")
                else:
                    raise
    
    # Filter to exact date range and sort by timestamp
    filtered_candles = [
        candle for candle in all_candles
        if start_time <= int(candle["timestamp"].timestamp() * 1000) <= end_time
    ]
    
    filtered_candles.sort(key=lambda x: x["timestamp"])
    
    print(f"📈 Final result: {len(filtered_candles)} candles for {symbol} from {filtered_candles[0]['timestamp'] if filtered_candles else 'N/A'} to {filtered_candles[-1]['timestamp'] if filtered_candles else 'N/A'}")
    
    return filtered_candles

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
