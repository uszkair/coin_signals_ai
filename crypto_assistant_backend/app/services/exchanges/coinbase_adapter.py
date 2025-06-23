"""
Coinbase CDP API Adapter
Implements the BaseExchange interface for Coinbase Developer Platform API
"""

import os
import logging
import asyncio
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from coinbase.rest import RESTClient
    from coinbase.websocket import WSClient
except ImportError:
    RESTClient = None
    WSClient = None

from .base_exchange import BaseExchange

logger = logging.getLogger(__name__)

class CoinbaseAdapter(BaseExchange):
    """Coinbase CDP API implementation of BaseExchange"""
    
    def __init__(self):
        """Initialize Coinbase adapter with CDP API credentials"""
        if not RESTClient:
            raise ImportError("Coinbase CDP SDK not installed. Run: pip install coinbase-advanced-py")
        
        self.api_key = os.getenv('COINBASE_API_KEY')
        self.private_key = os.getenv('COINBASE_PRIVATE_KEY')
        self.environment = os.getenv('COINBASE_ENVIRONMENT', 'sandbox')
        
        if not self.api_key or not self.private_key:
            raise ValueError("Coinbase CDP API credentials not configured")
        
        # Initialize REST client
        self.client = RESTClient(
            api_key=self.api_key,
            api_secret=self.private_key,
            base_url=self._get_base_url()
        )
        
        # Cache for symbol info and account data
        self._symbol_cache = {}
        self._account_cache = {}
        self._last_cache_update = None
        
        logger.info(f"Coinbase CDP Adapter initialized ({self.environment})")
    
    def _get_base_url(self) -> str:
        """Get API base URL based on environment"""
        if self.environment == 'sandbox':
            return 'https://api.sandbox.coinbase.com'
        return 'https://api.coinbase.com'
    
    def _convert_symbol_to_coinbase(self, binance_symbol: str) -> str:
        """Convert Binance symbol format to Coinbase format
        
        Examples:
        BTCUSDT -> BTC-USD
        ETHUSDT -> ETH-USD
        ADAUSDT -> ADA-USD
        """
        if binance_symbol.endswith('USDT'):
            base = binance_symbol[:-4]
            return f"{base}-USD"
        elif binance_symbol.endswith('USDC'):
            base = binance_symbol[:-4]
            return f"{base}-USDC"
        elif binance_symbol.endswith('BTC'):
            base = binance_symbol[:-3]
            return f"{base}-BTC"
        elif binance_symbol.endswith('ETH'):
            base = binance_symbol[:-3]
            return f"{base}-ETH"
        
        # If no known suffix, return as-is with dash
        if len(binance_symbol) >= 6:
            return f"{binance_symbol[:-3]}-{binance_symbol[-3:]}"
        
        return binance_symbol
    
    def _convert_symbol_from_coinbase(self, coinbase_symbol: str) -> str:
        """Convert Coinbase symbol format to Binance format"""
        if '-' in coinbase_symbol:
            base, quote = coinbase_symbol.split('-', 1)
            if quote == 'USD':
                return f"{base}USDT"
            return f"{base}{quote}"
        return coinbase_symbol
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balances"""
        try:
            # Get all accounts
            accounts_response = self.client.get_accounts()
            accounts = accounts_response.get('accounts', [])
            
            # Process account data
            balances = {}
            total_usd_value = Decimal('0')
            
            for account in accounts:
                currency = account.get('currency', '')
                available = account.get('available_balance', {}).get('value', '0')
                hold = account.get('hold', {}).get('value', '0')
                
                if Decimal(available) > 0 or Decimal(hold) > 0:
                    balances[currency] = {
                        'free': str(available),
                        'locked': str(hold),
                        'total': str(Decimal(available) + Decimal(hold))
                    }
                    
                    # Estimate USD value (simplified)
                    if currency == 'USD' or currency == 'USDT' or currency == 'USDC':
                        total_usd_value += Decimal(available)
                    elif currency == 'BTC':
                        # Get BTC price for estimation
                        try:
                            ticker = self.client.get_product_ticker('BTC-USD')
                            btc_price = Decimal(ticker.get('price', '0'))
                            total_usd_value += Decimal(available) * btc_price
                        except:
                            pass
            
            return {
                'exchange': 'coinbase',
                'balances': balances,
                'total_usd_value': str(total_usd_value),
                'account_type': 'spot',
                'status': 'connected',
                'environment': self.environment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Coinbase get_account_info error: {e}")
            return {
                'exchange': 'coinbase',
                'error': str(e),
                'status': 'error'
            }
    
    async def execute_trade(self, signal: Dict[str, Any], position_size: float) -> Dict[str, Any]:
        """Execute trade based on signal"""
        try:
            # Convert symbol format
            coinbase_symbol = self._convert_symbol_to_coinbase(signal['symbol'])
            
            # Determine order side
            side = 'BUY' if signal['action'].lower() == 'buy' else 'SELL'
            
            # Prepare order configuration
            if side == 'BUY':
                # For buy orders, use quote_size (USD amount)
                order_config = {
                    'product_id': coinbase_symbol,
                    'side': side,
                    'order_configuration': {
                        'market_market_ioc': {
                            'quote_size': str(position_size)
                        }
                    }
                }
            else:
                # For sell orders, use base_size (crypto amount)
                # Need to convert USD position_size to crypto amount
                ticker = self.client.get_product_ticker(coinbase_symbol)
                current_price = Decimal(ticker.get('price', '0'))
                if current_price > 0:
                    base_size = Decimal(position_size) / current_price
                    order_config = {
                        'product_id': coinbase_symbol,
                        'side': side,
                        'order_configuration': {
                            'market_market_ioc': {
                                'base_size': str(base_size)
                            }
                        }
                    }
                else:
                    raise ValueError(f"Could not get price for {coinbase_symbol}")
            
            # Execute order
            logger.info(f"Executing Coinbase order: {side} {coinbase_symbol} size: {position_size}")
            order_response = self.client.create_order(**order_config)
            
            # Parse response
            order_id = order_response.get('order_id')
            status = order_response.get('status', 'unknown')
            
            # Get order details for more info
            if order_id:
                try:
                    order_details = self.client.get_order(order_id)
                    filled_size = order_details.get('filled_size', '0')
                    filled_value = order_details.get('filled_value', '0')
                    
                    return {
                        'success': True,
                        'exchange': 'coinbase',
                        'order_id': order_id,
                        'status': status,
                        'symbol': signal['symbol'],
                        'side': side.lower(),
                        'filled_size': filled_size,
                        'filled_value': filled_value,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                except Exception as detail_error:
                    logger.warning(f"Could not get order details: {detail_error}")
            
            return {
                'success': True,
                'exchange': 'coinbase',
                'order_id': order_id,
                'status': status,
                'symbol': signal['symbol'],
                'side': side.lower(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Coinbase execute_trade error: {e}")
            return {
                'success': False,
                'exchange': 'coinbase',
                'error': str(e),
                'symbol': signal.get('symbol', 'unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            coinbase_symbol = self._convert_symbol_to_coinbase(symbol)
            ticker = self.client.get_product_ticker(coinbase_symbol)
            price = ticker.get('price')
            return float(price) if price else None
            
        except Exception as e:
            logger.error(f"Coinbase get_current_price error for {symbol}: {e}")
            return None
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            coinbase_symbol = self._convert_symbol_to_coinbase(symbol)
            
            # Get product info
            products = self.client.get_products()
            for product in products.get('products', []):
                if product.get('product_id') == coinbase_symbol:
                    return {
                        'symbol': symbol,
                        'coinbase_symbol': coinbase_symbol,
                        'status': product.get('status'),
                        'base_currency': product.get('base_currency_id'),
                        'quote_currency': product.get('quote_currency_id'),
                        'min_market_funds': product.get('min_market_funds'),
                        'max_market_funds': product.get('max_market_funds'),
                        'trading_disabled': product.get('trading_disabled', False)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Coinbase get_symbol_info error for {symbol}: {e}")
            return None
    
    async def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get active positions (for Coinbase, this is account balances > 0)"""
        try:
            account_info = await self.get_account_info()
            if 'error' in account_info:
                return []
            
            positions = []
            balances = account_info.get('balances', {})
            
            for currency, balance_info in balances.items():
                total_balance = Decimal(balance_info.get('total', '0'))
                if total_balance > 0:
                    # Convert to Binance-style symbol for consistency
                    if currency not in ['USD', 'USDT', 'USDC']:
                        symbol = f"{currency}USDT"
                        
                        # Get current price
                        current_price = await self.get_current_price(symbol)
                        usd_value = float(total_balance * Decimal(str(current_price))) if current_price else 0
                        
                        positions.append({
                            'symbol': symbol,
                            'currency': currency,
                            'size': str(total_balance),
                            'current_price': current_price,
                            'usd_value': usd_value,
                            'exchange': 'coinbase'
                        })
            
            return positions
            
        except Exception as e:
            logger.error(f"Coinbase get_active_positions error: {e}")
            return []
    
    async def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close position (sell all of a currency)"""
        try:
            # For Coinbase, position_id is the currency symbol
            currency = position_id
            
            # Get current balance
            account_info = await self.get_account_info()
            balances = account_info.get('balances', {})
            
            if currency not in balances:
                return {'success': False, 'error': f'No position found for {currency}'}
            
            balance = balances[currency]['free']
            if Decimal(balance) <= 0:
                return {'success': False, 'error': f'No available balance for {currency}'}
            
            # Create sell order
            coinbase_symbol = f"{currency}-USD"
            
            order_config = {
                'product_id': coinbase_symbol,
                'side': 'SELL',
                'order_configuration': {
                    'market_market_ioc': {
                        'base_size': balance
                    }
                }
            }
            
            order_response = self.client.create_order(**order_config)
            
            return {
                'success': True,
                'exchange': 'coinbase',
                'order_id': order_response.get('order_id'),
                'currency': currency,
                'size': balance
            }
            
        except Exception as e:
            logger.error(f"Coinbase close_position error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            accounts = self.client.get_accounts()
            return 'accounts' in accounts
        except Exception as e:
            logger.error(f"Coinbase connection test failed: {e}")
            return False
    
    def get_exchange_name(self) -> str:
        """Get exchange name"""
        return 'coinbase'
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        try:
            products = self.client.get_products()
            symbols = []
            
            for product in products.get('products', []):
                coinbase_symbol = product.get('product_id', '')
                if coinbase_symbol and product.get('status') == 'online':
                    # Convert to Binance format
                    binance_symbol = self._convert_symbol_from_coinbase(coinbase_symbol)
                    symbols.append(binance_symbol)
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting supported symbols: {e}")
            return []