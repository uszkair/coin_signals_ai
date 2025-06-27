"""
Coinbase Trading Service
Professional trading automation with Coinbase Advanced Trade API using coinbase-advanced-py SDK
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_DOWN
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    import os
    # Load .env from project root (3 levels up from this file)
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(env_path)
except ImportError:
    # dotenv not available, use environment variables directly
    pass

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Coinbase Advanced Trade SDK
try:
    from coinbase.rest import RESTClient
    from coinbase.websocket import WSClient
    SDK_AVAILABLE = True
    logger.info("SUCCESS: Coinbase Advanced Trade SDK imported successfully")
except ImportError:
    RESTClient = None
    WSClient = None
    SDK_AVAILABLE = False
    logger.error("ERROR: coinbase-advanced-py SDK not found! Install with: pip install coinbase-advanced-py")


class CoinbaseTrader:
    """Professional Coinbase trading automation"""
    
    def __init__(self, api_key: str = None, private_key: str = None):
        """
        Initialize Coinbase trader using coinbase-advanced-py SDK
        
        Args:
            api_key: Coinbase API key (organizations/... format)
            private_key: Coinbase private key (EC private key)
        """
        # Set API credentials
        self.api_key = api_key or os.environ.get("COINBASE_API_KEY")
        self.private_key = private_key or os.environ.get("COINBASE_PRIVATE_KEY")
        
        # Initialize SDK client
        if not self.api_key or not self.private_key:
            logger.error("Coinbase API credentials not found. Trading operations will fail.")
            logger.error("Required: COINBASE_API_KEY, COINBASE_PRIVATE_KEY")
            self.client = None
        elif not SDK_AVAILABLE:
            logger.error("Coinbase SDK not available. Install with: pip install coinbase-advanced-py")
            self.client = None
        else:
            try:
                # Initialize Coinbase Advanced Trade SDK
                # Based on our successful test: api_key + api_secret (private_key as secret)
                self.client = RESTClient(
                    api_key=self.api_key,
                    api_secret=self.private_key
                )
                
                # Log initialization
                logger.info("=" * 80)
                logger.info("COINBASE SDK INICIALIZÁLÁS")
                logger.info("=" * 80)
                logger.info(f"API Key: {self.api_key[:30]}...")
                logger.info(f"Private Key: {'Found (' + str(len(self.private_key)) + ' chars)' if self.private_key else 'Missing'}")
                logger.info("SUCCESS: Coinbase Developer Platform SDK client initialized successfully")
                        
            except Exception as e:
                logger.error(f"Failed to initialize Coinbase SDK: {e}")
                self.client = None
        
        # Environment configuration - Coinbase production only
        self.use_sandbox = False  # Coinbase doesn't have sandbox, always production
        self.use_futures = False  # Coinbase Advanced Trade is spot-only, no futures
        
        # Trading configuration
        self.max_position_size = 0.02  # Maximum 2% of portfolio per trade
        self.default_position_size_usd = None  # Fixed USD amount per trade (if set, overrides percentage)
        self.position_size_mode = 'percentage'  # 'percentage' or 'fixed_usd'
        self.max_daily_trades = 10     # Maximum trades per day
        self.min_profit_threshold = 0.005  # Minimum 0.5% profit threshold
        
        # Risk management
        self.daily_loss_limit = 0.05   # Stop trading if daily loss > 5%
        self.max_drawdown = 0.10       # Maximum 10% drawdown
        
        # Trade tracking - load from persistent storage
        self._load_daily_counters()
        self._load_active_positions()
        self._load_configuration()
    
    def _load_private_key_from_file(self):
        """Load private key from PEM file"""
        private_key_path = os.environ.get("COINBASE_PRIVATE_KEY_PATH")
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, 'r') as f:
                return f.read()
        return os.environ.get("COINBASE_PRIVATE_KEY")
    
    def _convert_symbol_to_coinbase(self, legacy_symbol: str) -> str:
        """Convert legacy symbol format to Coinbase format"""
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
        
        # If no known suffix, return as-is with dash
        if len(legacy_symbol) >= 6:
            return f"{legacy_symbol[:-3]}-{legacy_symbol[-3:]}"
        
        return legacy_symbol
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balances using SDK"""
        if not self.client:
            raise Exception("Coinbase SDK client not initialized. Please check your API credentials.")
        
        try:
            logger.info("=" * 80)
            logger.info("COINBASE SDK ACCOUNT INFO HÍVÁS")
            logger.info("=" * 80)
            logger.info("Calling client.get_accounts()...")
            
            # Get all accounts using SDK
            accounts_response = self.client.get_accounts()
            logger.info(f"SDK Response type: {type(accounts_response)}")
            logger.info(f"SDK Response: {accounts_response}")
            
            # Extract accounts from response
            if hasattr(accounts_response, 'accounts'):
                accounts = accounts_response.accounts
                logger.info(f"SUCCESS: Successfully retrieved {len(accounts)} accounts via SDK")
            else:
                # Handle different response formats
                accounts = accounts_response.get('accounts', []) if isinstance(accounts_response, dict) else []
                logger.info(f"SUCCESS: Successfully retrieved {len(accounts)} accounts (dict format)")
            
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
                    
                    # Estimate USD value
                    if currency == 'USD' or currency == 'USDT' or currency == 'USDC':
                        total_usd_value += Decimal(available)
                    elif currency == 'BTC':
                        # Get BTC price for estimation
                        try:
                            product = self.client.get_product(product_id='BTC-USD')
                            btc_price = Decimal(product.get('price', '0'))
                            total_usd_value += Decimal(available) * btc_price
                        except:
                            pass
            
            return {
                'account_type': 'SPOT',
                'can_trade': True,
                'can_withdraw': True,
                'can_deposit': True,
                'balances': balances,
                'total_wallet_balance': float(total_usd_value),
                'maker_commission': 0.005,  # 0.5% for Coinbase
                'taker_commission': 0.005,  # 0.5% for Coinbase
                'exchange': 'coinbase'
            }
                
        except Exception as e:
            logger.error(f"Coinbase API error: {e}")
            return {'error': str(e)}
    
    async def execute_signal_trade(self, signal: Dict[str, Any], position_size_usd: float = None, save_to_history: bool = True) -> Dict[str, Any]:
        """
        Execute a trade based on a trading signal
        
        Args:
            signal: Trading signal with symbol, direction, entry_price, stop_loss, take_profit
            position_size_usd: Position size in USD (if None, uses default risk management)
            
        Returns:
            Trade execution result
        """
        symbol = signal.get('symbol')
        direction = signal.get('signal')  # BUY or SELL
        entry_price = signal.get('entry_price')
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        confidence = signal.get('confidence', 50)
        
        # Pre-trade validation
        validation_result = await self._validate_trade(signal, position_size_usd)
        if not validation_result['valid']:
            # Save rejected trade to history with failed_order status
            if save_to_history:
                await self._save_rejected_trade_to_history(signal, position_size_usd, validation_result.get('rejection_reason', 'validation_failed'), validation_result['error'])
            return validation_result
        
        # Calculate position size
        if position_size_usd is None:
            position_size_usd = await self._calculate_position_size(symbol, confidence)
        
        # Convert symbol to Coinbase format
        coinbase_symbol = self._convert_symbol_to_coinbase(symbol)
        
        try:
            # Execute main order
            main_order = await self._place_market_order(coinbase_symbol, direction, position_size_usd)
            if not main_order['success']:
                # Save failed order to trading history
                if save_to_history:
                    await self._save_failed_trade_to_history(signal, position_size_usd, 0, main_order.get('error', 'Unknown order error'))
                return main_order
            
            # Track position
            position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_positions[position_id] = {
                'symbol': symbol,
                'direction': direction,
                'quantity': main_order.get('filled_size', 0),
                'entry_price': main_order.get('price', entry_price),
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'main_order_id': main_order.get('order_id'),
                'timestamp': datetime.now(),
                'signal_confidence': confidence
            }
            
            # Update daily tracking and save persistent data
            self.daily_trades += 1
            self._save_daily_counters()
            self._save_active_positions()
            
            # Save open position to performance table
            trade_history_id = await self._save_open_position_to_history(
                signal, position_size_usd, main_order.get('filled_size', 0), main_order, {}, {}
            )
            
            # Send notification for new position
            try:
                from app.services.notification_service import notify_new_position
                position_notification_data = {
                    'symbol': symbol,
                    'direction': direction,
                    'quantity': main_order.get('filled_size', 0),
                    'entry_price': main_order.get('price', entry_price),
                    'position_size_usd': position_size_usd,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'main_order_id': main_order.get('order_id'),
                    'confidence': confidence,
                    'position_id': position_id,
                    'exchange': 'coinbase'
                }
                await notify_new_position(position_notification_data)
                logger.info(f"SUCCESS: New position notification sent for {symbol}")
                
            except Exception as notification_error:
                logger.error(f"ERROR: Failed to send new position notification: {notification_error}")
            
            return {
                'success': True,
                'position_id': position_id,
                'main_order': main_order,
                'position_size_usd': position_size_usd,
                'quantity': main_order.get('filled_size', 0),
                'expected_profit': self._calculate_expected_profit(main_order.get('filled_size', 0), entry_price, take_profit, direction),
                'max_loss': self._calculate_max_loss(main_order.get('filled_size', 0), entry_price, stop_loss, direction),
                'trade_history_id': trade_history_id if save_to_history else None,
                'exchange': 'coinbase'
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_position(self, position_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Close an active position"""
        if position_id not in self.active_positions:
            return {'success': False, 'error': 'Position not found'}
        
        position = self.active_positions[position_id]
        symbol = position['symbol']
        direction = position['direction']
        quantity = position['quantity']
        
        try:
            # Convert symbol to Coinbase format
            coinbase_symbol = self._convert_symbol_to_coinbase(symbol)
            
            # Close position with market order
            close_direction = 'SELL' if direction == 'BUY' else 'BUY'
            
            if close_direction == 'SELL':
                # Sell order - use base_size (crypto amount)
                close_order = await self._place_sell_order(coinbase_symbol, quantity)
            else:
                # Buy order - need to calculate USD amount
                current_price = await self._get_current_price(coinbase_symbol)
                usd_amount = quantity * current_price if current_price else 0
                close_order = await self._place_buy_order(coinbase_symbol, usd_amount)
            
            if close_order['success']:
                # Calculate P&L
                entry_price = position['entry_price']
                exit_price = close_order.get('price', 0)
                pnl = self._calculate_pnl(quantity, entry_price, exit_price, direction)
                
                # Protect against division by zero
                if quantity > 0 and entry_price > 0:
                    pnl_percentage = (pnl / (quantity * entry_price)) * 100
                else:
                    pnl_percentage = 0.0
                
                # Update daily P&L and save persistent data
                self.daily_pnl += pnl
                self._save_daily_counters()
                
                # Update existing OPEN position to CLOSED status
                await self._update_position_to_closed(
                    position.get('main_order_id'),
                    exit_price,
                    pnl,
                    pnl_percentage,
                    reason
                )
                
                # Remove from active positions and save persistent data
                del self.active_positions[position_id]
                self._save_active_positions()
                
                return {
                    'success': True,
                    'position_id': position_id,
                    'close_order': close_order,
                    'pnl': pnl,
                    'pnl_percentage': pnl_percentage,
                    'reason': reason
                }
            else:
                return close_order
                
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions with current P&L"""
        
        # Lazy loading: Load positions from database if not already loaded
        if not self.active_positions:
            await self._load_active_positions_from_database()
        
        positions_with_pnl = {}
        
        for position_id, position in self.active_positions.items():
            try:
                # Get current price
                coinbase_symbol = self._convert_symbol_to_coinbase(position['symbol'])
                current_price = await self._get_current_price(coinbase_symbol)
                
                # Calculate unrealized P&L
                unrealized_pnl = self._calculate_pnl(
                    position['quantity'],
                    position['entry_price'],
                    current_price,
                    position['direction']
                )
                
                # Protect against division by zero for unrealized P&L percentage
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                
                if quantity > 0 and entry_price > 0:
                    unrealized_pnl_percentage = (unrealized_pnl / (quantity * entry_price)) * 100
                else:
                    unrealized_pnl_percentage = 0.0
                
                positions_with_pnl[position_id] = {
                    **position,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percentage': unrealized_pnl_percentage,
                    'stop_loss': position.get('stop_loss', 0.0),
                    'take_profit': position.get('take_profit', 0.0),
                    'exchange': 'coinbase'
                }
                
            except Exception as e:
                logger.error(f"Error calculating P&L for position {position_id}: {e}")
                positions_with_pnl[position_id] = {
                    **position,
                    'stop_loss': position.get('stop_loss', 0.0),
                    'take_profit': position.get('take_profit', 0.0),
                    'exchange': 'coinbase'
                }
        
        return positions_with_pnl
    
    async def get_trading_statistics(self) -> Dict[str, Any]:
        """Get trading statistics and performance metrics"""
        account_info = await self.get_account_info()
        active_positions = await self.get_active_positions()
        
        total_unrealized_pnl = sum(
            pos.get('unrealized_pnl', 0) for pos in active_positions.values()
        )
        
        return {
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'active_positions_count': len(active_positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'account_balance': account_info.get('total_wallet_balance', 0),
            'max_daily_trades': self.max_daily_trades,
            'daily_loss_limit': self.daily_loss_limit,
            'can_trade': self.daily_trades < self.max_daily_trades and self.daily_pnl > -self.daily_loss_limit,
            'risk_level': self._assess_risk_level(),
            'exchange': 'coinbase'
        }
    
    # Private helper methods
    async def _validate_trade(self, signal: Dict[str, Any], position_size_usd: float) -> Dict[str, Any]:
        """Validate trade before execution"""
        # Check daily limits
        if self.daily_trades >= self.max_daily_trades:
            return {'valid': False, 'error': 'Daily trade limit reached', 'rejection_reason': 'daily_limit_exceeded'}
        
        if self.daily_pnl <= -self.daily_loss_limit:
            return {'valid': False, 'error': 'Daily loss limit reached', 'rejection_reason': 'daily_loss_limit_exceeded'}
        
        # Check signal quality
        confidence = signal.get('confidence', 0)
        if confidence < 60:
            return {'valid': False, 'error': f'Signal confidence too low: {confidence}%', 'rejection_reason': 'low_confidence'}
        
        # Check required fields
        required_fields = ['symbol', 'signal', 'entry_price']
        for field in required_fields:
            if field not in signal:
                return {'valid': False, 'error': f'Missing required field: {field}', 'rejection_reason': 'missing_required_field'}
        
        return {'valid': True}
    
    async def _calculate_position_size(self, symbol: str, confidence: float) -> float:
        """Calculate position size based on configuration and risk management"""
        if self.position_size_mode == 'fixed_usd' and self.default_position_size_usd:
            # Use fixed USD amount
            base_size = self.default_position_size_usd
        else:
            # Use percentage of portfolio
            account_info = await self.get_account_info()
            total_balance = account_info.get('total_wallet_balance', 0)
            if total_balance <= 0:
                raise Exception("No wallet balance available - cannot calculate position size")
            base_size = total_balance * self.max_position_size
        
        # Adjust based on confidence (optional)
        if self.position_size_mode == 'percentage':
            confidence_multiplier = min(confidence / 100, 1.0)
            calculated_size = base_size * confidence_multiplier
            
            # Minimum position size check
            min_required = 10.0  # $10 minimum for Coinbase
            if calculated_size < min_required:
                error_msg = f"Position size ${calculated_size:.2f} is below minimum ${min_required:.2f}. Please increase wallet balance or use fixed USD mode."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            return calculated_size
        else:
            # For fixed USD mode, don't adjust by confidence
            return base_size
    
    async def _place_market_order(self, coinbase_symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """Place a market order using SDK"""
        if not self.client:
            raise Exception("Coinbase SDK client not initialized.")
        
        try:
            logger.info("=" * 80)
            logger.info("COINBASE SDK ORDER LÉTREHOZÁS")
            logger.info("=" * 80)
            logger.info(f"Symbol: {coinbase_symbol}")
            logger.info(f"Side: {side}")
            logger.info(f"Amount: {amount}")
            
            if side == 'BUY':
                # For buy orders, use quote_size (USD amount)
                order_config = {
                    'product_id': coinbase_symbol,
                    'side': side,
                    'order_configuration': {
                        'market_market_ioc': {
                            'quote_size': str(amount)
                        }
                    }
                }
            else:
                # For sell orders, use base_size (crypto amount)
                order_config = {
                    'product_id': coinbase_symbol,
                    'side': side,
                    'order_configuration': {
                        'market_market_ioc': {
                            'base_size': str(amount)
                        }
                    }
                }
            
            logger.info(f"Order config: {order_config}")
            logger.info("Calling client.create_order()...")
            
            order_response = self.client.create_order(**order_config)
            logger.info(f"SDK Order response: {order_response}")
            
            # Parse response
            if hasattr(order_response, 'order_id'):
                order_id = order_response.order_id
                status = getattr(order_response, 'status', 'unknown')
            else:
                order_id = order_response.get('order_id') if isinstance(order_response, dict) else None
                status = order_response.get('status', 'unknown') if isinstance(order_response, dict) else 'unknown'
            
            logger.info(f"Order ID: {order_id}")
            logger.info(f"Status: {status}")
            
            # Get order details for more info
            if order_id:
                try:
                    logger.info(f"Calling client.get_order('{order_id}')...")
                    order_details = self.client.get_order(order_id)
                    logger.info(f"Order details: {order_details}")
                    
                    if hasattr(order_details, 'filled_size'):
                        filled_size = float(order_details.filled_size or '0')
                        filled_value = float(getattr(order_details, 'filled_value', '0') or '0')
                    else:
                        filled_size = float(order_details.get('filled_size', '0'))
                        filled_value = float(order_details.get('filled_value', '0'))
                    
                    avg_price = filled_value / filled_size if filled_size > 0 else 0
                    
                    logger.info("SUCCESS: Order executed successfully:")
                    logger.info(f"   Filled size: {filled_size}")
                    logger.info(f"   Filled value: {filled_value}")
                    logger.info(f"   Average price: {avg_price}")
                    
                    return {
                        'success': True,
                        'order_id': order_id,
                        'symbol': coinbase_symbol,
                        'side': side,
                        'filled_size': filled_size,
                        'price': avg_price,
                        'status': status
                    }
                except Exception as detail_error:
                    logger.warning(f"Could not get order details: {detail_error}")
            
            return {
                'success': True,
                'order_id': order_id,
                'symbol': coinbase_symbol,
                'side': side,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Coinbase SDK order error for {coinbase_symbol}: {e}")
            logger.error(f"Error type: {type(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _place_buy_order(self, coinbase_symbol: str, usd_amount: float) -> Dict[str, Any]:
        """Place a buy order with USD amount"""
        return await self._place_market_order(coinbase_symbol, 'BUY', usd_amount)
    
    async def _place_sell_order(self, coinbase_symbol: str, crypto_amount: float) -> Dict[str, Any]:
        """Place a sell order with crypto amount"""
        return await self._place_market_order(coinbase_symbol, 'SELL', crypto_amount)
    
    async def _get_current_price(self, coinbase_symbol: str) -> float:
        """Get current market price using SDK"""
        if not self.client:
            logger.error("Coinbase SDK client not initialized")
            return 0.0
            
        try:
            logger.info("=" * 80)
            logger.info(f"COINBASE SDK PRICE HÍVÁS - {coinbase_symbol}")
            logger.info("=" * 80)
            logger.info(f"Calling client.get_product('{coinbase_symbol}')...")
            
            # Get product info using SDK
            product = self.client.get_product(coinbase_symbol)
            logger.info(f"SDK Response type: {type(product)}")
            logger.info(f"SDK Response: {product}")
            
            # Extract price from response
            if hasattr(product, 'price'):
                price = float(product.price)
                logger.info(f"SUCCESS: Price found via SDK: {price}")
                return price
            elif isinstance(product, dict) and 'price' in product:
                price = float(product['price'])
                logger.info(f"SUCCESS: Price found (dict format): {price}")
                return price
            else:
                logger.error(f"ERROR: No price data available in response: {product}")
                return 0.0
                        
        except Exception as e:
            logger.error(f"Error getting current price for {coinbase_symbol}: {e}")
            return 0.0
    
    async def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order status using SDK"""
        if not self.client:
            logger.error("Coinbase SDK client not initialized")
            return {
                'success': False,
                'error': 'Coinbase SDK client not initialized',
                'order_id': order_id,
                'symbol': symbol
            }
            
        try:
            logger.info("=" * 80)
            logger.info("COINBASE SDK ORDER STATUS HÍVÁS")
            logger.info("=" * 80)
            logger.info(f"Order ID: {order_id}")
            logger.info(f"Symbol: {symbol}")
            logger.info(f"Calling client.get_order('{order_id}')...")
            
            # Get order details using SDK
            order_details = self.client.get_order(order_id)
            logger.info(f"SDK Response type: {type(order_details)}")
            logger.info(f"SDK Response: {order_details}")
            
            # Extract order information
            if hasattr(order_details, 'order_id'):
                # Object response format
                result = {
                    'success': True,
                    'order_id': order_details.order_id,
                    'symbol': symbol,
                    'status': getattr(order_details, 'status', 'unknown'),
                    'side': getattr(order_details, 'side', ''),
                    'filled_size': float(getattr(order_details, 'filled_size', '0') or '0'),
                    'filled_value': float(getattr(order_details, 'filled_value', '0') or '0'),
                    'created_time': getattr(order_details, 'created_time', ''),
                    'completion_time': getattr(order_details, 'completion_time', ''),
                    'order_details': order_details.__dict__ if hasattr(order_details, '__dict__') else str(order_details)
                }
            elif isinstance(order_details, dict):
                # Dictionary response format
                result = {
                    'success': True,
                    'order_id': order_details.get('order_id', order_id),
                    'symbol': symbol,
                    'status': order_details.get('status', 'unknown'),
                    'side': order_details.get('side', ''),
                    'filled_size': float(order_details.get('filled_size', '0') or '0'),
                    'filled_value': float(order_details.get('filled_value', '0') or '0'),
                    'created_time': order_details.get('created_time', ''),
                    'completion_time': order_details.get('completion_time', ''),
                    'order_details': order_details
                }
            else:
                logger.error(f"ERROR: Unexpected response format: {type(order_details)}")
                return {
                    'success': False,
                    'error': f'Unexpected response format: {type(order_details)}',
                    'order_id': order_id,
                    'symbol': symbol
                }
            
            logger.info(f"SUCCESS: Order status result: {result}")
            return result
                
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'symbol': symbol
            }
    
    async def refresh_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Refresh order status and update database if needed"""
        try:
            # Get current order status from Coinbase
            order_status = await self.get_order_status(symbol, order_id)
            
            if not order_status['success']:
                return order_status
            
            # Here you could add database update logic if needed
            # For now, just return the status
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'status': order_status.get('status'),
                'updated': True
            }
            
        except Exception as e:
            logger.error(f"Error refreshing order status for {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'symbol': symbol
            }
    
    def set_position_size_config(self, mode: str, amount: float = None, max_percentage: float = None):
        """Set position size configuration"""
        self.position_size_mode = mode
        
        if mode == 'fixed_usd' and amount:
            self.default_position_size_usd = amount
        elif mode == 'percentage' and max_percentage:
            self.max_position_size = max_percentage / 100  # Convert percentage to decimal
        
        # Save configuration
        self._save_configuration()
        
        logger.info(f"Position size config updated: mode={mode}, amount={amount}, max_percentage={max_percentage}")
    
    def _get_minimum_position_size(self, symbol: str) -> float:
        """Get minimum position size for a symbol (Coinbase requirements)"""
        # Coinbase minimum trading requirements
        minimums = {
            'BTCUSDT': 1.0,   # $1 minimum
            'BTC-USD': 1.0,   # $1 minimum
            'ETHUSDT': 1.0,   # $1 minimum
            'ETH-USD': 1.0,   # $1 minimum
            'ADAUSDT': 1.0,   # $1 minimum
            'ADA-USD': 1.0,   # $1 minimum
            'SOLUSDT': 1.0,   # $1 minimum
            'SOL-USD': 1.0,   # $1 minimum
            'DOTUSDT': 1.0,   # $1 minimum
            'DOT-USD': 1.0,   # $1 minimum
        }
        
        # Convert legacy symbol to Coinbase format for lookup
        coinbase_symbol = self._convert_symbol_to_coinbase(symbol)
        
        # Return minimum for symbol or default $1
        return minimums.get(symbol, minimums.get(coinbase_symbol, 1.0))
    
    def _calculate_pnl(self, quantity: float, entry_price: float, exit_price: float, direction: str) -> float:
        """Calculate profit/loss with None value protection"""
        # Protect against None values
        if entry_price is None or exit_price is None or quantity is None:
            return 0.0
        
        if direction == 'BUY':
            return quantity * (exit_price - entry_price)
        else:  # SELL
            return quantity * (entry_price - exit_price)
    
    def _calculate_expected_profit(self, quantity: float, entry_price: float, take_profit: float, direction: str) -> float:
        """Calculate expected profit at take profit level"""
        return self._calculate_pnl(quantity, entry_price, take_profit, direction)
    
    def _calculate_max_loss(self, quantity: float, entry_price: float, stop_loss: float, direction: str) -> float:
        """Calculate maximum loss at stop loss level"""
        return abs(self._calculate_pnl(quantity, entry_price, stop_loss, direction))
    
    def _assess_risk_level(self) -> str:
        """Assess current risk level"""
        if self.daily_pnl < -self.daily_loss_limit * 0.8:
            return 'HIGH'
        elif self.daily_pnl < -self.daily_loss_limit * 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    # Placeholder methods for database operations (to be implemented)
    async def _save_open_position_to_history(self, signal, position_size_usd, quantity, main_order, stop_loss_order, take_profit_order):
        """Save open position to database"""
        # Implementation would go here
        return None
    
    async def _save_rejected_trade_to_history(self, signal, position_size_usd, rejection_reason, error_message):
        """Save rejected trade to database"""
        # Implementation would go here
        pass
    
    async def _save_failed_trade_to_history(self, signal, position_size_usd, quantity, failure_reason):
        """Save failed trade to database"""
        # Implementation would go here
        pass
    
    async def _update_position_to_closed(self, main_order_id, exit_price, pnl, pnl_percentage, reason):
        """Update position to closed in database"""
        # Implementation would go here
        pass
    
    async def _load_active_positions_from_database(self):
        """Load active positions from database"""
        # Implementation would go here
        self.active_positions = {}
    
    def _load_daily_counters(self):
        """Load daily trading counters"""
        self.daily_trades = 0
        self.daily_pnl = 0.0
    
    def _save_daily_counters(self):
        """Save daily trading counters"""
        pass
    
    def _load_active_positions(self):
        """Load active positions"""
        self.active_positions = {}
    
    def _save_active_positions(self):
        """Save active positions"""
        pass
    
    def _load_configuration(self):
        """Load trader configuration"""
        pass
    
    def _save_configuration(self):
        """Save trader configuration"""
        pass


# Global trader instance
coinbase_trader = None

def initialize_global_trader(force_reinit=False):
    """Initialize global trader"""
    global coinbase_trader
    if coinbase_trader is None or force_reinit:
        coinbase_trader = CoinbaseTrader()
        logger.info(f"Global Coinbase trader {'reinitialized' if force_reinit else 'initialized'}: Production mode")
    return coinbase_trader

# Function removed - sandbox environment not available

def get_trading_environment_info():
    """Get current trading environment information"""
    trader = initialize_global_trader(force_reinit=False)
    
    return {
        'environment': "Coinbase Production",
        'description': "Coinbase Advanced Trade API on Production",
        'api_connected': trader.client is not None,
        'exchange': 'coinbase'
    }

async def execute_automatic_trade(signal: Dict[str, Any], position_size_usd: float = None) -> Dict[str, Any]:
    """
    Execute automatic trade based on signal
    
    Args:
        signal: Trading signal from signal engine
        position_size_usd: Optional position size override
        
    Returns:
        Trade execution result
    """
    trader = initialize_global_trader(force_reinit=False)
    return await trader.execute_signal_trade(signal, position_size_usd)


async def get_trading_account_status() -> Dict[str, Any]:
    """Get current trading account status"""
    trader = initialize_global_trader(force_reinit=False)
    account_info = await trader.get_account_info()
    trading_stats = await trader.get_trading_statistics()
    active_positions = await trader.get_active_positions()
    
    return {
        'account_info': account_info,
        'trading_statistics': trading_stats,
        'active_positions': active_positions,
        'trader_config': {
            'max_position_size': trader.max_position_size,
            'max_daily_trades': trader.max_daily_trades,
            'daily_loss_limit': trader.daily_loss_limit,
            'exchange': 'coinbase'
        }
    }


async def close_trading_position(position_id: str, reason: str = "manual") -> Dict[str, Any]:
    """Close a specific trading position"""
    trader = initialize_global_trader(force_reinit=False)
    return await trader.close_position(position_id, reason)


async def get_coinbase_trade_history(symbol: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Get real trading history from Coinbase API"""
    try:
        trader = initialize_global_trader(force_reinit=False)
        
        if not trader.client:
            return {
                'success': False,
                'error': 'Coinbase API client not initialized'
            }
        
        # Get fills (executed trades) from Coinbase
        try:
            fills_response = trader.client.get_fills(limit=limit)
            fills = fills_response.get('fills', [])
            
            # Filter by symbol if provided
            if symbol:
                coinbase_symbol = trader._convert_symbol_to_coinbase(symbol)
                fills = [fill for fill in fills if fill.get('product_id') == coinbase_symbol]
            
            # Format fills for consistency
            formatted_fills = []
            for fill in fills:
                formatted_fills.append({
                    'symbol': fill.get('product_id', ''),
                    'orderId': fill.get('order_id', ''),
                    'price': float(fill.get('price', 0)),
                    'qty': float(fill.get('size', 0)),
                    'quoteQty': float(fill.get('value', 0)),
                    'commission': float(fill.get('fee', 0)),
                    'commissionAsset': fill.get('fee_currency', ''),
                    'time': fill.get('trade_time', ''),
                    'isBuyer': fill.get('side') == 'BUY',
                    'isMaker': fill.get('liquidity_indicator') == 'M',
                    'exchange': 'coinbase'
                })
            
            return {
                'success': True,
                'data': formatted_fills
            }
            
        except Exception as e:
            logger.error(f"Error getting Coinbase trade history: {e}")
            return {
                'success': False,
                'error': f"Failed to get trade history: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in get_coinbase_trade_history: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def get_coinbase_order_history(symbol: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Get real order history from Coinbase API"""
    try:
        trader = initialize_global_trader(force_reinit=False)
        
        if not trader.client:
            return {
                'success': False,
                'error': 'Coinbase API client not initialized'
            }
        
        # Get orders from Coinbase
        try:
            orders_response = trader.client.list_orders(limit=limit)
            orders = orders_response.get('orders', [])
            
            # Filter by symbol if provided
            if symbol:
                coinbase_symbol = trader._convert_symbol_to_coinbase(symbol)
                orders = [order for order in orders if order.get('product_id') == coinbase_symbol]
            
            # Format orders for consistency
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'symbol': order.get('product_id', ''),
                    'orderId': order.get('order_id', ''),
                    'orderListId': -1,  # Not applicable for Coinbase
                    'clientOrderId': order.get('client_order_id', ''),
                    'price': float(order.get('order_configuration', {}).get('limit_limit_gtc', {}).get('limit_price', 0)),
                    'origQty': float(order.get('order_configuration', {}).get('market_market_ioc', {}).get('base_size', 0)),
                    'executedQty': float(order.get('filled_size', 0)),
                    'cummulativeQuoteQty': float(order.get('filled_value', 0)),
                    'status': order.get('status', ''),
                    'timeInForce': 'IOC',  # Most Coinbase orders are IOC
                    'type': 'MARKET' if 'market' in str(order.get('order_configuration', {})) else 'LIMIT',
                    'side': order.get('side', ''),
                    'stopPrice': 0.0,  # Not directly available
                    'icebergQty': 0.0,  # Not applicable
                    'time': order.get('created_time', ''),
                    'updateTime': order.get('completion_time', order.get('created_time', '')),
                    'isWorking': order.get('status') in ['OPEN', 'PENDING'],
                    'exchange': 'coinbase'
                })
            
            return {
                'success': True,
                'data': formatted_orders
            }
            
        except Exception as e:
            logger.error(f"Error getting Coinbase order history: {e}")
            return {
                'success': False,
                'error': f"Failed to get order history: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in get_coinbase_order_history: {e}")
        return {
            'success': False,
            'error': str(e)
        }