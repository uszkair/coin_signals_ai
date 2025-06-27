"""
Base Exchange Interface
Abstract base class for all exchange adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseExchange(ABC):
    """Abstract base class for exchange adapters"""
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information and balances
        
        Returns:
            Dict containing:
            - exchange: str (exchange name)
            - balances: Dict[str, Dict] (currency -> {free, locked, total})
            - total_usd_value: str (estimated total value in USD)
            - account_type: str (spot, futures, etc.)
            - status: str (connected, error, etc.)
            - error: str (if status is error)
        """
        pass
    
    @abstractmethod
    async def execute_trade(self, signal: Dict[str, Any], position_size: float) -> Dict[str, Any]:
        """
        Execute trade based on signal
        
        Args:
            signal: Dict containing:
                - symbol: str (e.g., 'BTCUSDT')
                - action: str ('buy' or 'sell')
                - confidence: float (0-1)
                - price: float (optional, for limit orders)
            position_size: float (USD amount for the trade)
        
        Returns:
            Dict containing:
            - success: bool
            - exchange: str
            - order_id: str (if successful)
            - status: str (order status)
            - symbol: str
            - side: str ('buy' or 'sell')
            - filled_size: str (amount filled)
            - filled_value: str (USD value filled)
            - error: str (if not successful)
            - timestamp: str (ISO format)
        """
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for symbol
        
        Args:
            symbol: str (e.g., 'BTCUSDT')
        
        Returns:
            float: Current price or None if error
        """
        pass
    
    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information (trading rules, precision, etc.)
        
        Args:
            symbol: str (e.g., 'BTCUSDT')
        
        Returns:
            Dict containing symbol information or None if not found
        """
        pass
    
    @abstractmethod
    async def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get active positions
        
        Returns:
            List of Dict containing:
            - symbol: str
            - size: str (position size)
            - current_price: float
            - usd_value: float
            - exchange: str
        """
        pass
    
    @abstractmethod
    async def close_position(self, position_id: str) -> Dict[str, Any]:
        """
        Close position
        
        Args:
            position_id: str (position identifier)
        
        Returns:
            Dict containing:
            - success: bool
            - exchange: str
            - order_id: str (if successful)
            - error: str (if not successful)
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            bool: True if connection successful
        """
        pass
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        Get exchange name
        
        Returns:
            str: Exchange name (e.g., 'coinbase')
        """
        pass
    
    # Optional methods with default implementations
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported symbols
        
        Returns:
            List[str]: List of supported trading symbols
        """
        return []
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get order history
        
        Args:
            symbol: str (optional, filter by symbol)
            limit: int (max number of orders to return)
        
        Returns:
            List of order dictionaries
        """
        return []
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel order
        
        Args:
            order_id: str
        
        Returns:
            Dict containing cancellation result
        """
        return {'success': False, 'error': 'Not implemented'}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status
        
        Args:
            order_id: str
        
        Returns:
            Dict containing order status
        """
        return {'error': 'Not implemented'}
    
    def format_quantity(self, quantity: float, symbol: str) -> str:
        """
        Format quantity according to exchange rules
        
        Args:
            quantity: float
            symbol: str
        
        Returns:
            str: Formatted quantity
        """
        # Default implementation - can be overridden
        return f"{quantity:.8f}".rstrip('0').rstrip('.')
    
    def format_price(self, price: float, symbol: str) -> str:
        """
        Format price according to exchange rules
        
        Args:
            price: float
            symbol: str
        
        Returns:
            str: Formatted price
        """
        # Default implementation - can be overridden
        return f"{price:.8f}".rstrip('0').rstrip('.')
    
    async def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """
        Get trading fees for symbol
        
        Args:
            symbol: str
        
        Returns:
            Dict containing maker and taker fees
        """
        return {'maker': 0.001, 'taker': 0.001}  # Default 0.1%
    
    async def get_24h_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get 24h statistics for symbol
        
        Args:
            symbol: str
        
        Returns:
            Dict containing 24h stats or None
        """
        return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if symbol is supported
        
        Args:
            symbol: str
        
        Returns:
            bool: True if symbol is valid
        """
        supported = self.get_supported_symbols()
        return symbol in supported if supported else True
    
    def get_min_trade_amount(self, symbol: str) -> float:
        """
        Get minimum trade amount for symbol
        
        Args:
            symbol: str
        
        Returns:
            float: Minimum trade amount in USD
        """
        return 10.0  # Default $10 minimum
    
    def get_max_trade_amount(self, symbol: str) -> float:
        """
        Get maximum trade amount for symbol
        
        Args:
            symbol: str
        
        Returns:
            float: Maximum trade amount in USD
        """
        return 1000000.0  # Default $1M maximum