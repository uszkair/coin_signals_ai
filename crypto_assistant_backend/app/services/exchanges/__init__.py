"""
Exchange Adapters Package
Provides unified interface for multiple cryptocurrency exchanges
"""

from .base_exchange import BaseExchange
from .coinbase_adapter import CoinbaseAdapter

__all__ = [
    'BaseExchange',
    'CoinbaseAdapter'
]

# Exchange registry for factory pattern
EXCHANGE_REGISTRY = {
    'coinbase': CoinbaseAdapter,
}

def get_available_exchanges():
    """Get list of available exchange names"""
    return list(EXCHANGE_REGISTRY.keys())

def create_exchange(exchange_name: str) -> BaseExchange:
    """
    Factory function to create exchange adapter
    
    Args:
        exchange_name: str ('coinbase')
    
    Returns:
        BaseExchange: Exchange adapter instance
    
    Raises:
        ValueError: If exchange not supported
    """
    if exchange_name not in EXCHANGE_REGISTRY:
        available = ', '.join(get_available_exchanges())
        raise ValueError(f"Exchange '{exchange_name}' not supported. Available: {available}")
    
    exchange_class = EXCHANGE_REGISTRY[exchange_name]
    return exchange_class()