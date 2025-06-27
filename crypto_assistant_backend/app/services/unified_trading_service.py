"""
Unified Trading Service
Manages multiple exchange adapters and provides unified trading interface
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .exchanges import create_exchange, get_available_exchanges, BaseExchange

logger = logging.getLogger(__name__)

class UnifiedTradingService:
    """Unified trading service that manages multiple exchanges"""
    
    def __init__(self):
        """Initialize unified trading service"""
        self.exchanges: Dict[str, BaseExchange] = {}
        self.primary_exchange = 'coinbase'  # Only Coinbase supported now
        self.fallback_exchanges = []
        
        # Initialize available exchanges
        self._initialize_exchanges()
        
        logger.info(f"Unified Trading Service initialized with {len(self.exchanges)} exchanges")
        logger.info(f"Primary exchange: {self.primary_exchange}")
    
    def _initialize_exchanges(self):
        """Initialize all available exchanges"""
        available_exchanges = get_available_exchanges()
        
        for exchange_name in available_exchanges:
            try:
                exchange = create_exchange(exchange_name)
                self.exchanges[exchange_name] = exchange
                
                # Set fallback order
                if exchange_name != self.primary_exchange:
                    self.fallback_exchanges.append(exchange_name)
                    
                logger.info(f"SUCCESS: {exchange_name.capitalize()} exchange initialized")
                
            except Exception as e:
                logger.warning(f"ERROR: Failed to initialize {exchange_name}: {e}")
    
    def get_primary_exchange(self) -> Optional[BaseExchange]:
        """Get primary exchange adapter"""
        return self.exchanges.get(self.primary_exchange)
    
    def get_exchange(self, exchange_name: str) -> Optional[BaseExchange]:
        """Get specific exchange adapter"""
        return self.exchanges.get(exchange_name)
    
    def get_available_exchange_names(self) -> List[str]:
        """Get list of available exchange names"""
        return list(self.exchanges.keys())
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all exchanges"""
        results = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                is_connected = await exchange.test_connection()
                results[exchange_name] = is_connected
                status = "SUCCESS: Connected" if is_connected else "ERROR: Failed"
                logger.info(f"{exchange_name.capitalize()}: {status}")
            except Exception as e:
                results[exchange_name] = False
                logger.error(f"{exchange_name.capitalize()}: ERROR: Error - {e}")
        
        return results
    
    async def get_account_info(self, exchange_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account information from specified exchange or primary
        
        Args:
            exchange_name: Optional exchange name, defaults to primary
        
        Returns:
            Dict containing account information
        """
        exchange_name = exchange_name or self.primary_exchange
        exchange = self.exchanges.get(exchange_name)
        
        if not exchange:
            return {
                'error': f'Exchange {exchange_name} not available',
                'available_exchanges': list(self.exchanges.keys())
            }
        
        try:
            return await exchange.get_account_info()
        except Exception as e:
            logger.error(f"Account info error for {exchange_name}: {e}")
            return {'error': str(e), 'exchange': exchange_name}
    
    async def execute_trade_with_fallback(self, signal: Dict[str, Any], position_size: float, 
                                        preferred_exchange: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute trade with automatic fallback to other exchanges
        
        Args:
            signal: Trading signal
            position_size: Position size in USD
            preferred_exchange: Preferred exchange name
        
        Returns:
            Dict containing trade result
        """
        # Determine exchange order
        exchange_order = []
        
        if preferred_exchange and preferred_exchange in self.exchanges:
            exchange_order.append(preferred_exchange)
        
        # Add primary exchange if not already included
        if self.primary_exchange not in exchange_order:
            exchange_order.append(self.primary_exchange)
        
        # Add fallback exchanges
        for fallback in self.fallback_exchanges:
            if fallback not in exchange_order:
                exchange_order.append(fallback)
        
        # Try each exchange in order
        last_error = None
        
        for exchange_name in exchange_order:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                continue
            
            try:
                logger.info(f"Attempting trade on {exchange_name}: {signal['action']} {signal['symbol']}")
                result = await exchange.execute_trade(signal, position_size)
                
                if result.get('success'):
                    logger.info(f"SUCCESS: Trade successful on {exchange_name}")
                    result['executed_on'] = exchange_name
                    return result
                else:
                    last_error = result.get('error', 'Unknown error')
                    logger.warning(f"ERROR: Trade failed on {exchange_name}: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"ERROR: Trade error on {exchange_name}: {e}")
        
        # All exchanges failed
        return {
            'success': False,
            'error': f'All exchanges failed. Last error: {last_error}',
            'attempted_exchanges': exchange_order,
            'symbol': signal.get('symbol', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_current_price(self, symbol: str, exchange_name: Optional[str] = None) -> Optional[float]:
        """
        Get current price from specified exchange or primary
        
        Args:
            symbol: Trading symbol
            exchange_name: Optional exchange name
        
        Returns:
            Current price or None
        """
        exchange_name = exchange_name or self.primary_exchange
        exchange = self.exchanges.get(exchange_name)
        
        if not exchange:
            return None
        
        try:
            return await exchange.get_current_price(symbol)
        except Exception as e:
            logger.error(f"Price error for {symbol} on {exchange_name}: {e}")
            return None
    
    async def get_all_prices(self, symbol: str) -> Dict[str, Optional[float]]:
        """
        Get current price from all available exchanges
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Dict mapping exchange names to prices
        """
        prices = {}
        
        tasks = []
        for exchange_name in self.exchanges.keys():
            task = self.get_current_price(symbol, exchange_name)
            tasks.append((exchange_name, task))
        
        for exchange_name, task in tasks:
            try:
                price = await task
                prices[exchange_name] = price
            except Exception as e:
                logger.error(f"Price error for {symbol} on {exchange_name}: {e}")
                prices[exchange_name] = None
        
        return prices
    
    async def get_best_price(self, symbol: str, side: str) -> Dict[str, Any]:
        """
        Get best price across all exchanges
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
        
        Returns:
            Dict containing best price and exchange
        """
        prices = await self.get_all_prices(symbol)
        
        valid_prices = {exchange: price for exchange, price in prices.items() if price is not None}
        
        if not valid_prices:
            return {'error': 'No prices available'}
        
        if side.lower() == 'buy':
            # For buying, we want the lowest price
            best_exchange = min(valid_prices, key=valid_prices.get)
            best_price = valid_prices[best_exchange]
        else:
            # For selling, we want the highest price
            best_exchange = max(valid_prices, key=valid_prices.get)
            best_price = valid_prices[best_exchange]
        
        return {
            'symbol': symbol,
            'side': side,
            'best_price': best_price,
            'best_exchange': best_exchange,
            'all_prices': valid_prices
        }
    
    async def get_combined_portfolio(self) -> Dict[str, Any]:
        """
        Get combined portfolio from all exchanges
        
        Returns:
            Dict containing combined portfolio data
        """
        combined_balances = {}
        total_usd_value = 0.0
        exchange_data = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                account_info = await exchange.get_account_info()
                
                if 'error' not in account_info:
                    exchange_data[exchange_name] = account_info
                    
                    # Combine balances
                    balances = account_info.get('balances', {})
                    for currency, balance_info in balances.items():
                        if currency not in combined_balances:
                            combined_balances[currency] = {
                                'free': 0.0,
                                'locked': 0.0,
                                'total': 0.0,
                                'exchanges': {}
                            }
                        
                        free = float(balance_info.get('free', 0))
                        locked = float(balance_info.get('locked', 0))
                        total = float(balance_info.get('total', 0))
                        
                        combined_balances[currency]['free'] += free
                        combined_balances[currency]['locked'] += locked
                        combined_balances[currency]['total'] += total
                        combined_balances[currency]['exchanges'][exchange_name] = balance_info
                    
                    # Add to total USD value
                    usd_value = float(account_info.get('total_usd_value', 0))
                    total_usd_value += usd_value
                    
            except Exception as e:
                logger.error(f"Portfolio error for {exchange_name}: {e}")
                exchange_data[exchange_name] = {'error': str(e)}
        
        return {
            'combined_balances': combined_balances,
            'total_usd_value': total_usd_value,
            'exchange_data': exchange_data,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def switch_primary_exchange(self, new_primary: str) -> bool:
        """
        Switch primary exchange
        
        Args:
            new_primary: New primary exchange name
        
        Returns:
            bool: True if successful
        """
        if new_primary not in self.exchanges:
            logger.error(f"Cannot switch to {new_primary}: exchange not available")
            return False
        
        # Test connection first
        exchange = self.exchanges[new_primary]
        try:
            is_connected = await exchange.test_connection()
            if not is_connected:
                logger.error(f"Cannot switch to {new_primary}: connection test failed")
                return False
        except Exception as e:
            logger.error(f"Cannot switch to {new_primary}: {e}")
            return False
        
        old_primary = self.primary_exchange
        self.primary_exchange = new_primary
        
        # Update fallback list
        self.fallback_exchanges = [ex for ex in self.exchanges.keys() if ex != new_primary]
        
        logger.info(f"Primary exchange switched from {old_primary} to {new_primary}")
        return True
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """
        Get status of all exchanges
        
        Returns:
            Dict containing exchange status information
        """
        return {
            'primary_exchange': self.primary_exchange,
            'available_exchanges': list(self.exchanges.keys()),
            'fallback_exchanges': self.fallback_exchanges,
            'total_exchanges': len(self.exchanges)
        }