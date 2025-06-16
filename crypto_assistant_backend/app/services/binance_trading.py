"""
Binance Automatic Trading Service
Professional trading automation with risk management
"""

import os
import asyncio
import random
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceTrader:
    """Professional Binance trading automation"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = None, use_futures: bool = None):
        """
        Initialize Binance trader
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet for safe testing (default: from database)
            use_futures: Use Futures API instead of Spot (default: True for trading)
        """
        # Get settings from database if not explicitly provided
        if testnet is None:
            try:
                # Import here to avoid circular imports
                from app.services.trading_settings_service import get_trading_settings_service
                from app.database import get_sync_db
                
                # Always try to get from database first
                try:
                    # Get database session and settings service
                    db = next(get_sync_db())
                    settings_service = get_trading_settings_service(db)
                    risk_settings = settings_service.get_risk_management_settings()
                    db_testnet = risk_settings.get('testnet_mode', True)
                    logger.info(f"Database settings loaded: testnet_mode = {db_testnet}")
                    
                except Exception as db_error:
                    logger.warning(f"Could not get database settings: {db_error}")
                    db_testnet = True  # Default to testnet for safety if database fails
                
                testnet = db_testnet
                
            except Exception as e:
                logger.warning(f"Could not get database settings, using testnet=True: {e}")
                testnet = True  # Default to testnet for safety
        
        # Set API credentials based on testnet mode
        if testnet:
            self.api_key = api_key or os.environ.get("BINANCE_TESTNET_API_KEY")
            self.api_secret = api_secret or os.environ.get("BINANCE_TESTNET_API_SECRET")
        else:
            self.api_key = api_key or os.environ.get("BINANCE_API_KEY")
            self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
        
        # Set testnet and use_futures
        self.testnet = testnet
        if use_futures is None:
            # For testnet, always use futures since spot testnet keys often don't work
            if self.testnet:
                self.use_futures = True
                logger.info("Testnet mode: automatically using Futures API")
            else:
                try:
                    # Import here to avoid circular imports
                    from app.services.trading_settings_service import get_trading_settings_service
                    from app.database import get_sync_db
                    
                    # Get database session and settings service
                    db = next(get_sync_db())
                    settings_service = get_trading_settings_service(db)
                    risk_settings = settings_service.get_risk_management_settings()
                    db_use_futures = risk_settings.get('use_futures', True if self.testnet else False)
                    logger.info(f"Database settings loaded: use_futures = {db_use_futures}")
                    
                    self.use_futures = db_use_futures
                    
                except Exception as e:
                    logger.warning(f"Could not get database settings for futures, using default: {e}")
                    self.use_futures = False  # Default to Spot for mainnet
        else:
            self.use_futures = use_futures
        
        # Get URLs from environment
        if self.testnet:
            if self.use_futures:
                self.base_url = os.environ.get("BINANCE_FUTURES_TESTNET_URL", "https://testnet.binancefuture.com")
            else:
                self.base_url = os.environ.get("BINANCE_SPOT_TESTNET_URL", "https://testnet.binance.vision")
        else:
            if self.use_futures:
                self.base_url = os.environ.get("BINANCE_FUTURES_URL", "https://fapi.binance.com")
            else:
                self.base_url = os.environ.get("BINANCE_SPOT_URL", "https://api.binance.com")
        
        # Initialize client based on mode
        if not self.api_key or not self.api_secret:
            logger.error("Binance API credentials not found. Trading operations will fail.")
            self.client = None
        else:
            try:
                # Initialize client with testnet flag
                self.client = Client(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet
                )
                
                # Set custom base URL from environment for futures testnet
                if self.use_futures and self.testnet:
                    # For futures testnet, we need to set the API_URL manually
                    # The python-binance library will automatically add /fapi/v1 prefix
                    self.client.API_URL = self.base_url
                    logger.info(f"Set Futures Testnet API URL: {self.base_url}")
                
                # Log initialization
                env_type = "Futures" if self.use_futures else "Spot"
                net_type = "Testnet" if self.testnet else "Mainnet"
                logger.info(f"Binance {env_type} {net_type} client initialized")
                logger.info(f"Base URL: {self.base_url}")
                        
            except Exception as e:
                logger.error(f"Failed to initialize Binance client: {e}")
                self.client = None
        
        # Trading configuration
        self.max_position_size = 0.02  # Maximum 2% of portfolio per trade
        self.default_position_size_usd = None  # Fixed USD amount per trade (if set, overrides percentage)
        self.position_size_mode = 'percentage'  # 'percentage' or 'fixed_usd'
        self.max_daily_trades = 10     # Maximum trades per day
        self.min_profit_threshold = 0.005  # Minimum 0.5% profit threshold
        
        # Risk management
        self.daily_loss_limit = 0.05   # Stop trading if daily loss > 5%
        self.max_drawdown = 0.10       # Maximum 10% drawdown
        
        # Trade tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.active_positions = {}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balances"""
        if not self.client:
            raise Exception("Binance API client not initialized. Please check your API credentials.")
        
        try:
            if self.use_futures:
                # Futures account info
                account = self.client.futures_account()
                balances = {}
                
                # Handle futures account assets properly
                if 'assets' in account:
                    for balance in account['assets']:
                        if float(balance.get('walletBalance', 0)) > 0:
                            balances[balance['asset']] = {
                                'free': float(balance.get('availableBalance', 0)),
                                'locked': float(balance.get('walletBalance', 0)) - float(balance.get('availableBalance', 0)),
                                'total': float(balance.get('walletBalance', 0))
                            }
                
                return {
                    'account_type': 'FUTURES',
                    'can_trade': account.get('canTrade', False),
                    'can_withdraw': account.get('canWithdraw', False),
                    'can_deposit': account.get('canDeposit', False),
                    'balances': balances,
                    'total_wallet_balance': float(account.get('totalWalletBalance', 0)),
                    'total_unrealized_pnl': float(account.get('totalUnrealizedProfit', 0)),
                    'total_margin_balance': float(account.get('totalMarginBalance', 0)),
                    'maker_commission': 0.02,  # 0.02% for futures
                    'taker_commission': 0.04,  # 0.04% for futures
                    'testnet': self.testnet,
                    'futures': True
                }
            else:
                # Spot account info
                account = self.client.get_account()
                balances = {
                    balance['asset']: {
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    }
                    for balance in account['balances']
                    if float(balance['free']) > 0 or float(balance['locked']) > 0
                }
                
                return {
                    'account_type': 'SPOT',
                    'can_trade': account.get('canTrade', False),
                    'can_withdraw': account.get('canWithdraw', False),
                    'can_deposit': account.get('canDeposit', False),
                    'balances': balances,
                    'total_wallet_balance': self._calculate_total_balance(balances),
                    'maker_commission': account.get('makerCommission', 10),
                    'taker_commission': account.get('takerCommission', 10),
                    'testnet': self.testnet,
                    'futures': False
                }
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting account info: {e}")
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
            return validation_result
        
        # Calculate position size
        if position_size_usd is None:
            position_size_usd = await self._calculate_position_size(symbol, confidence)
        
        # Get symbol info for precision
        symbol_info = await self._get_symbol_info(symbol)
        if not symbol_info:
            return {'success': False, 'error': f'Symbol {symbol} not found'}
        
        # Calculate quantity
        quantity = self._calculate_quantity(position_size_usd, entry_price, symbol_info)
        
        try:
            # Execute main order
            main_order = await self._place_market_order(symbol, direction, quantity)
            if not main_order['success']:
                # Save failed order to trading history
                if save_to_history:
                    await self._save_failed_trade_to_history(signal, position_size_usd, quantity, main_order.get('error', 'Unknown order error'))
                return main_order
            
            # Place stop loss order
            stop_loss_order = await self._place_stop_loss_order(
                symbol, direction, quantity, stop_loss, symbol_info
            )
            
            # Place take profit order
            take_profit_order = await self._place_take_profit_order(
                symbol, direction, quantity, take_profit, symbol_info
            )
            
            # Track position
            position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_positions[position_id] = {
                'symbol': symbol,
                'direction': direction,
                'quantity': quantity,
                'entry_price': main_order.get('price', entry_price),
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'main_order_id': main_order.get('order_id'),
                'stop_loss_order_id': stop_loss_order.get('order_id'),
                'take_profit_order_id': take_profit_order.get('order_id'),
                'timestamp': datetime.now(),
                'signal_confidence': confidence
            }
            
            # Update daily tracking
            self.daily_trades += 1
            
            # SAVE OPEN POSITION TO PERFORMANCE TABLE IMMEDIATELY
            trade_history_id = await self._save_open_position_to_history(
                signal, position_size_usd, quantity, main_order, stop_loss_order, take_profit_order
            )
            
            # Send notification for new position
            try:
                from app.services.notification_service import notify_new_position
                position_notification_data = {
                    'symbol': symbol,
                    'direction': direction,
                    'quantity': quantity,
                    'entry_price': main_order.get('price', entry_price),
                    'position_size_usd': position_size_usd,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'main_order_id': main_order.get('order_id'),
                    'stop_loss_order_id': stop_loss_order.get('order_id'),
                    'take_profit_order_id': take_profit_order.get('order_id'),
                    'testnet': self.testnet,
                    'confidence': confidence,
                    'position_id': position_id
                }
                await notify_new_position(position_notification_data)
                logger.info(f"✅ New position notification sent for {symbol}")
            except Exception as notification_error:
                logger.error(f"❌ Failed to send new position notification: {notification_error}")
            
            # Broadcast new position via WebSocket
            try:
                from app.routers.websocket import broadcast_position_status
                await broadcast_position_status({
                    'action': 'opened',
                    'symbol': symbol,
                    'position_id': position_id,
                    'direction': direction,
                    'entry_price': main_order.get('price', entry_price),
                    'position_size_usd': position_size_usd,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
                logger.info(f"✅ New position broadcasted via WebSocket for {symbol}")
            except Exception as ws_error:
                logger.error(f"❌ Failed to broadcast new position via WebSocket: {ws_error}")
            
            # Update position table
            try:
                from app.services.position_service import update_position_table
                await update_position_table(position_notification_data)
                logger.info(f"✅ Position table updated for {symbol}")
            except Exception as table_error:
                logger.error(f"❌ Failed to update position table: {table_error}")
            
            return {
                'success': True,
                'position_id': position_id,
                'main_order': main_order,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'position_size_usd': position_size_usd,
                'quantity': quantity,
                'expected_profit': self._calculate_expected_profit(quantity, entry_price, take_profit, direction),
                'max_loss': self._calculate_max_loss(quantity, entry_price, stop_loss, direction),
                'trade_history_id': trade_history_id if save_to_history else None
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
            # Cancel pending orders
            if position.get('stop_loss_order_id'):
                await self._cancel_order(symbol, position['stop_loss_order_id'])
            
            if position.get('take_profit_order_id'):
                await self._cancel_order(symbol, position['take_profit_order_id'])
            
            # Close position with market order
            close_direction = 'SELL' if direction == 'BUY' else 'BUY'
            close_order = await self._place_market_order(symbol, close_direction, quantity)
            
            if close_order['success']:
                # Calculate P&L with zero division protection
                entry_price = position['entry_price']
                exit_price = close_order.get('price', 0)
                pnl = self._calculate_pnl(quantity, entry_price, exit_price, direction)
                
                # Protect against division by zero
                if quantity > 0 and entry_price > 0:
                    pnl_percentage = (pnl / (quantity * entry_price)) * 100
                else:
                    pnl_percentage = 0.0
                
                # Update daily P&L
                self.daily_pnl += pnl
                
                # Update existing OPEN position to CLOSED status
                await self._update_position_to_closed(
                    position.get('main_order_id'),
                    exit_price,
                    pnl,
                    pnl_percentage,
                    reason
                )
                
                # Send notification for closed position
                try:
                    from app.services.notification_service import notify_position_closed
                    closed_position_data = {
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percentage': pnl_percentage,
                        'reason': reason,
                        'position_id': position_id
                    }
                    await notify_position_closed(closed_position_data)
                    logger.info(f"✅ Position closed notification sent for {symbol}")
                except Exception as notification_error:
                    logger.error(f"❌ Failed to send position closed notification: {notification_error}")
                
                # Broadcast position closure via WebSocket
                try:
                    from app.routers.websocket import broadcast_position_status
                    await broadcast_position_status({
                        'action': 'closed',
                        'symbol': symbol,
                        'position_id': position_id,
                        'reason': reason,
                        'pnl': pnl,
                        'pnl_percentage': pnl_percentage
                    })
                    logger.info(f"✅ Position closure broadcasted via WebSocket for {symbol}")
                except Exception as ws_error:
                    logger.error(f"❌ Failed to broadcast position closure via WebSocket: {ws_error}")
                
                # Remove position from table
                try:
                    from app.services.position_service import remove_position_from_table
                    await remove_position_from_table(closed_position_data)
                    logger.info(f"✅ Position removed from table for {symbol}")
                except Exception as table_error:
                    logger.error(f"❌ Failed to remove position from table: {table_error}")
                
                # Remove from active positions
                del self.active_positions[position_id]
                
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
        """Get all active positions with current P&L from Binance API"""
        if not self.client or not self.use_futures:
            # Fallback to stored positions for non-futures or no client
            positions_with_pnl = {}
            
            for position_id, position in self.active_positions.items():
                try:
                    # Get current price
                    current_price = await self._get_current_price(position['symbol'])
                    
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
                        'unrealized_pnl_percentage': unrealized_pnl_percentage
                    }
                    
                except Exception as e:
                    logger.error(f"Error calculating P&L for position {position_id}: {e}")
                    positions_with_pnl[position_id] = position
            
            return positions_with_pnl
        
        # For Futures, get live positions from Binance API
        try:
            positions = self.client.futures_position_information()
            live_positions = {}
            
            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    symbol = pos.get('symbol')
                    entry_price = float(pos.get('entryPrice', 0))
                    
                    # Get current price
                    try:
                        current_price = await self._get_current_price(symbol)
                    except:
                        current_price = float(pos.get('markPrice', 0))
                    
                    # USE BINANCE CALCULATED P&L - this is always accurate
                    unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                    
                    # Calculate percentage based on Binance P&L for accuracy
                    if abs(position_amt) > 0 and entry_price > 0:
                        position_value = abs(position_amt) * entry_price
                        pnl_percentage = (unrealized_pnl / position_value) * 100
                    else:
                        pnl_percentage = 0.0
                    
                    position_id = f"{symbol}_live"
                    live_positions[position_id] = {
                        'symbol': symbol,
                        'direction': 'BUY' if position_amt > 0 else 'SELL',
                        'quantity': abs(position_amt),
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'unrealized_pnl': unrealized_pnl,
                        'unrealized_pnl_percentage': pnl_percentage,
                        'position_type': 'FUTURES',
                        'leverage': float(pos.get('leverage', 1)),
                        'margin_type': pos.get('marginType', 'cross'),
                        'timestamp': datetime.now()
                    }
            
            return live_positions
            
        except Exception as e:
            logger.error(f"Error getting live positions from Binance: {e}")
            # Fallback to stored positions
            return await self.get_active_positions()
    
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
            'risk_level': self._assess_risk_level()
        }
    
    # Private helper methods
    async def _validate_trade(self, signal: Dict[str, Any], position_size_usd: float) -> Dict[str, Any]:
        """Validate trade before execution"""
        # Check daily limits
        if self.daily_trades >= self.max_daily_trades:
            return {'valid': False, 'error': 'Daily trade limit reached'}
        
        if self.daily_pnl <= -self.daily_loss_limit:
            return {'valid': False, 'error': 'Daily loss limit reached'}
        
        # Check signal quality
        confidence = signal.get('confidence', 0)
        if confidence < 60:
            return {'valid': False, 'error': f'Signal confidence too low: {confidence}%'}
        
        # Check required fields
        required_fields = ['symbol', 'signal', 'entry_price', 'stop_loss', 'take_profit']
        for field in required_fields:
            if field not in signal:
                return {'valid': False, 'error': f'Missing required field: {field}'}
        
        return {'valid': True}
    
    async def _calculate_position_size(self, symbol: str, confidence: float) -> float:
        """Calculate position size based on configuration and risk management"""
        if self.position_size_mode == 'fixed_usd' and self.default_position_size_usd:
            # Use fixed USD amount
            base_size = self.default_position_size_usd
        else:
            # Use percentage of portfolio
            account_info = await self.get_account_info()
            total_balance = account_info.get('total_wallet_balance', 0)  # Require real balance
            if total_balance <= 0:
                raise Exception("No wallet balance available - cannot calculate position size")
            base_size = total_balance * self.max_position_size
        
        # Adjust based on confidence (optional)
        if self.position_size_mode == 'percentage':
            confidence_multiplier = min(confidence / 100, 1.0)
            calculated_size = base_size * confidence_multiplier
            
            # VALIDATION: Check minimum requirements in mainnet mode
            if not self.testnet:  # Mainnet mode - enforce Binance minimums
                min_required = self._get_minimum_position_size(symbol)
                if calculated_size < min_required:
                    error_msg = f"Position size ${calculated_size:.2f} is below Binance minimum ${min_required:.2f} for {symbol}. Please increase wallet balance or use fixed USD mode with at least ${min_required:.2f}."
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            return calculated_size
        else:
            # For fixed USD mode, don't adjust by confidence
            return base_size
    
    def _get_minimum_position_size(self, symbol: str) -> float:
        """Get minimum position size for symbol based on Binance requirements"""
        # Binance minimum trading requirements
        minimums = {
            'BTCUSDT': 10.0,
            'ETHUSDT': 10.0,
            'BNBUSDT': 10.0,
            'ADAUSDT': 5.0,
            'SOLUSDT': 10.0,
            'DOTUSDT': 10.0
        }
        
        # Default to $15 for unknown symbols to be safe
        return minimums.get(symbol, 15.0)
    
    def set_position_size_config(self, mode: str, amount: float = None, max_percentage: float = None):
        """
        Configure position sizing
        
        Args:
            mode: 'percentage' or 'fixed_usd'
            amount: Fixed USD amount per trade (for fixed_usd mode)
            max_percentage: Maximum percentage of portfolio per trade (for percentage mode)
        """
        if mode == 'fixed_usd':
            self.position_size_mode = 'fixed_usd'
            if amount:
                self.default_position_size_usd = amount
        elif mode == 'percentage':
            self.position_size_mode = 'percentage'
            if max_percentage:
                self.max_position_size = max_percentage / 100  # Convert percentage to decimal
        
        logger.info(f"Position size config updated: mode={mode}, amount={amount}, max_percentage={max_percentage}")
    
    async def _get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol trading information"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot get symbol info without API connection.")
        
        try:
            if self.use_futures:
                # Futures exchange info
                exchange_info = self.client.futures_exchange_info()
                logger.info(f"Got futures exchange info for {symbol}")
            else:
                # Spot exchange info
                exchange_info = self.client.get_exchange_info()
                logger.info(f"Got spot exchange info for {symbol}")
                
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    logger.info(f"Found symbol info for {symbol}: filters={len(symbol_info.get('filters', []))}")
                    return symbol_info
            
            logger.warning(f"Symbol {symbol} not found in exchange info")
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            raise Exception(f"Cannot get symbol info for {symbol} without valid API connection: {e}")
    
    def _calculate_quantity(self, position_size_usd: float, price: float, symbol_info: Dict[str, Any]) -> float:
        """Calculate order quantity with proper precision"""
        quantity = position_size_usd / price
        
        # Get step size for precision
        step_size = 0.001  # Default
        min_qty = 0.001    # Default minimum
        
        for filter_info in symbol_info.get('filters', []):
            if filter_info['filterType'] == 'LOT_SIZE':
                step_size = float(filter_info['stepSize'])
                min_qty = float(filter_info.get('minQty', step_size))
                break
        
        # Ensure quantity meets minimum requirement
        if quantity < min_qty:
            quantity = min_qty
        
        # Round down to step size with proper precision
        if step_size >= 1:
            # For step sizes >= 1, round to integer
            precision = 0
        else:
            # Count decimal places in step size
            step_str = f"{step_size:.10f}".rstrip('0')
            if '.' in step_str:
                precision = len(step_str.split('.')[1])
            else:
                precision = 0
        
        # Use Decimal for precise calculation
        decimal_quantity = Decimal(str(quantity))
        decimal_step = Decimal(str(step_size))
        
        # Round down to nearest step size
        steps = decimal_quantity // decimal_step
        final_quantity = float(steps * decimal_step)
        
        # Ensure we don't go below minimum
        if final_quantity < min_qty:
            final_quantity = min_qty
        
        # Round to appropriate precision
        return round(final_quantity, precision)
    
    async def _place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order with price validation"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot place orders without API connection.")
        
        try:
            # Get current market price for validation
            current_price = await self._get_current_price(symbol)
            if current_price <= 0:
                return {'success': False, 'error': f'Could not get current price for {symbol}'}
            
            # Get symbol info for price filters
            symbol_info = await self._get_symbol_info(symbol)
            if not symbol_info:
                return {'success': False, 'error': f'Could not get symbol info for {symbol}'}
            
            # Validate price against PERCENT_PRICE filter
            price_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PERCENT_PRICE':
                    price_filter = filter_info
                    break
            
            if price_filter:
                multiplier_up = float(price_filter.get('multiplierUp', 5.0))
                multiplier_down = float(price_filter.get('multiplierDown', 0.2))
                
                max_price = current_price * multiplier_up
                min_price = current_price * multiplier_down
                
                logger.info(f"Price validation for {symbol}: current={current_price}, range=[{min_price:.8f}, {max_price:.8f}]")
            
            binance_side = SIDE_BUY if side == 'BUY' else SIDE_SELL
            
            # Use appropriate order method based on API type
            if self.use_futures:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=binance_side,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                
                # Futures API response format
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': float(order['executedQty']),
                    'price': float(order.get('avgPrice', order.get('price', 0))),
                    'commission': 0,  # Commission calculated separately in futures
                    'status': order['status']
                }
            else:
                order = self.client.order_market(
                    symbol=symbol,
                    side=binance_side,
                    quantity=quantity
                )
                
                # Spot API response format
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': float(order['executedQty']),
                    'price': float(order['fills'][0]['price']) if order['fills'] else 0,
                    'commission': sum(float(fill['commission']) for fill in order['fills']),
                    'status': order['status']
                }
            
        except BinanceOrderException as e:
            error_msg = str(e)
            logger.error(f"Binance order error for {symbol}: {error_msg}")
            
            # Provide more helpful error messages
            if "PERCENT_PRICE" in error_msg:
                return {'success': False, 'error': f'Price validation failed for {symbol}. Market order rejected due to price limits. This usually happens when the market is very volatile or the symbol has trading restrictions.'}
            elif "MIN_NOTIONAL" in error_msg:
                return {'success': False, 'error': f'Order value too small for {symbol}. Please increase position size.'}
            elif "LOT_SIZE" in error_msg:
                return {'success': False, 'error': f'Invalid quantity for {symbol}. Please adjust position size.'}
            else:
                return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Unexpected error placing order for {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _place_stop_loss_order(self, symbol: str, direction: str, quantity: float, stop_price: float, symbol_info: Dict[str, Any]) -> Dict[str, Any]:
        """Place a stop loss order with price validation"""
        if not self.client:
            logger.warning("Binance API client not initialized. Cannot place stop loss orders without API connection.")
            return {'success': False, 'error': 'Binance API client not initialized'}
        
        try:
            # Get current market price for validation
            current_price = await self._get_current_price(symbol)
            if current_price <= 0:
                logger.warning(f"Could not get current price for {symbol}, skipping stop loss order")
                return {'success': False, 'error': f'Could not get current price for {symbol}'}
            
            # TESTNET SAFETY: Check if we're in testnet mode and adjust behavior
            if self.testnet:
                logger.info(f"TESTNET MODE: Attempting to place stop loss order for {symbol}")
            
            # Round stop price to proper precision based on PRICE_FILTER
            price_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PRICE_FILTER':
                    price_filter = filter_info
                    break
            
            if price_filter:
                tick_size = float(price_filter.get('tickSize', '0.01'))
                # Round to tick size precision
                if tick_size >= 1:
                    precision = 0
                else:
                    tick_str = f"{tick_size:.10f}".rstrip('0')
                    if '.' in tick_str:
                        precision = len(tick_str.split('.')[1])
                    else:
                        precision = 0
                
                # Round stop price to proper precision
                stop_price = round(stop_price / tick_size) * tick_size
                stop_price = round(stop_price, precision)
                logger.info(f"Rounded stop price for {symbol}: {stop_price} (precision: {precision})")
            
            # Validate stop price against PERCENT_PRICE filter
            percent_price_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PERCENT_PRICE':
                    percent_price_filter = filter_info
                    break
            
            if percent_price_filter:
                multiplier_up = float(percent_price_filter.get('multiplierUp', 5.0))
                multiplier_down = float(percent_price_filter.get('multiplierDown', 0.2))
                
                max_price = current_price * multiplier_up
                min_price = current_price * multiplier_down
                
                # Adjust stop price if it's outside the allowed range
                if stop_price > max_price:
                    logger.warning(f"Stop price {stop_price} too high for {symbol}, adjusting to {max_price}")
                    stop_price = max_price * 0.95  # 5% buffer
                    stop_price = round(stop_price, precision) if 'precision' in locals() else stop_price
                elif stop_price < min_price:
                    logger.warning(f"Stop price {stop_price} too low for {symbol}, adjusting to {min_price}")
                    stop_price = min_price * 1.05  # 5% buffer
                    stop_price = round(stop_price, precision) if 'precision' in locals() else stop_price
            
            # For stop loss: LONG position needs SELL order to close, SHORT position needs BUY order to close
            # Normal logic (same for both testnet and mainnet)
            side = SIDE_SELL if direction == 'BUY' else SIDE_BUY
            logger.info(f"Stop loss order: {direction} position -> {side} order to close")
            
            if self.use_futures:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    quantity=quantity,
                    stopPrice=stop_price
                )
            else:
                # For spot, use a more conservative approach
                limit_price = stop_price * 0.99 if side == SIDE_SELL else stop_price * 1.01
                order = self.client.order_stop_loss_limit(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    stopPrice=stop_price,
                    price=limit_price
                )
            
            logger.info(f"✅ Stop loss order created successfully for {symbol}: {order['orderId']}")
            return {
                'success': True,
                'order_id': order['orderId'],
                'type': 'STOP_LOSS',
                'stop_price': stop_price
            }
            
        except BinanceOrderException as e:
            error_msg = str(e)
            logger.error(f"Binance stop loss order error for {symbol}: {error_msg}")
            
            if "PERCENT_PRICE" in error_msg:
                return {'success': False, 'error': f'Stop loss price validation failed for {symbol}. Price too far from market price.'}
            else:
                return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Error placing stop loss order for {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _place_take_profit_order(self, symbol: str, direction: str, quantity: float, take_profit_price: float, symbol_info: Dict[str, Any]) -> Dict[str, Any]:
        """Place a take profit order with price validation"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot place take profit orders without API connection.")
        
        try:
            # Get current market price for validation
            current_price = await self._get_current_price(symbol)
            if current_price <= 0:
                logger.warning(f"Could not get current price for {symbol}, skipping take profit order")
                return {'success': False, 'error': f'Could not get current price for {symbol}'}
            
            # Round take profit price to proper precision based on PRICE_FILTER
            price_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PRICE_FILTER':
                    price_filter = filter_info
                    break
            
            if price_filter:
                tick_size = float(price_filter.get('tickSize', '0.01'))
                # Round to tick size precision
                if tick_size >= 1:
                    precision = 0
                else:
                    tick_str = f"{tick_size:.10f}".rstrip('0')
                    if '.' in tick_str:
                        precision = len(tick_str.split('.')[1])
                    else:
                        precision = 0
                
                # Round take profit price to proper precision
                take_profit_price = round(take_profit_price / tick_size) * tick_size
                take_profit_price = round(take_profit_price, precision)
                logger.info(f"Rounded take profit price for {symbol}: {take_profit_price} (precision: {precision})")
            
            # Validate take profit price against PERCENT_PRICE filter
            percent_price_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PERCENT_PRICE':
                    percent_price_filter = filter_info
                    break
            
            if percent_price_filter:
                multiplier_up = float(percent_price_filter.get('multiplierUp', 5.0))
                multiplier_down = float(percent_price_filter.get('multiplierDown', 0.2))
                
                max_price = current_price * multiplier_up
                min_price = current_price * multiplier_down
                
                # Adjust take profit price if it's outside the allowed range
                if take_profit_price > max_price:
                    logger.warning(f"Take profit price {take_profit_price} too high for {symbol}, adjusting to {max_price}")
                    take_profit_price = max_price * 0.95  # 5% buffer
                    take_profit_price = round(take_profit_price, precision) if 'precision' in locals() else take_profit_price
                elif take_profit_price < min_price:
                    logger.warning(f"Take profit price {take_profit_price} too low for {symbol}, adjusting to {min_price}")
                    take_profit_price = min_price * 1.05  # 5% buffer
                    take_profit_price = round(take_profit_price, precision) if 'precision' in locals() else take_profit_price
            
            # For take profit: LONG position needs SELL order to close, SHORT position needs BUY order to close
            # Normal logic (same for both testnet and mainnet)
            side = SIDE_SELL if direction == 'BUY' else SIDE_BUY
            logger.info(f"Take profit order: {direction} position -> {side} order to close")
            
            if self.use_futures:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                    quantity=quantity,
                    stopPrice=take_profit_price
                )
            else:
                order = self.client.order_take_profit_limit(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    stopPrice=take_profit_price,
                    price=take_profit_price
                )
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'type': 'TAKE_PROFIT',
                'take_profit_price': take_profit_price
            }
            
        except BinanceOrderException as e:
            error_msg = str(e)
            logger.error(f"Binance take profit order error for {symbol}: {error_msg}")
            
            if "PERCENT_PRICE" in error_msg:
                return {'success': False, 'error': f'Take profit price validation failed for {symbol}. Price too far from market price.'}
            else:
                return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Error placing take profit order for {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot cancel orders without API connection.")
        
        try:
            if self.use_futures:
                self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            else:
                self.client.cancel_order(symbol=symbol, orderId=order_id)
            return True
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    async def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order status from Binance API"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot get order status without API connection.")
        
        try:
            if self.use_futures:
                order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'status': order['status'],
                    'side': order['side'],
                    'type': order['type'],
                    'original_qty': float(order['origQty']),
                    'executed_qty': float(order['executedQty']),
                    'cumulative_quote_qty': float(order['cumQuote']),
                    'price': float(order['price']) if order['price'] != '0' else None,
                    'avg_price': float(order['avgPrice']) if order['avgPrice'] != '0' else None,
                    'stop_price': float(order['stopPrice']) if order.get('stopPrice') and order['stopPrice'] != '0' else None,
                    'time': datetime.fromtimestamp(order['time'] / 1000),
                    'update_time': datetime.fromtimestamp(order['updateTime'] / 1000),
                    'time_in_force': order['timeInForce'],
                    'reduce_only': order.get('reduceOnly', False),
                    'close_position': order.get('closePosition', False)
                }
            else:
                order = self.client.get_order(symbol=symbol, orderId=order_id)
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'status': order['status'],
                    'side': order['side'],
                    'type': order['type'],
                    'original_qty': float(order['origQty']),
                    'executed_qty': float(order['executedQty']),
                    'cumulative_quote_qty': float(order['cummulativeQuoteQty']),
                    'price': float(order['price']) if order['price'] != '0.00000000' else None,
                    'stop_price': float(order['stopPrice']) if order.get('stopPrice') and order['stopPrice'] != '0.00000000' else None,
                    'iceberg_qty': float(order['icebergQty']) if order.get('icebergQty') else None,
                    'time': datetime.fromtimestamp(order['time'] / 1000),
                    'update_time': datetime.fromtimestamp(order['updateTime'] / 1000),
                    'time_in_force': order['timeInForce'],
                    'is_working': order.get('isWorking', False)
                }
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error getting order {order_id}: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting order {order_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def refresh_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Refresh order status and update database if needed"""
        try:
            # Get fresh order status from Binance
            order_status = await self.get_order_status(symbol, order_id)
            
            if not order_status['success']:
                return order_status
            
            # Update database with fresh order data
            await self._update_order_in_database(order_id, order_status)
            
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'status': order_status['status'],
                'executed_qty': order_status['executed_qty'],
                'avg_price': order_status.get('avg_price'),
                'update_time': order_status['update_time'],
                'database_updated': True
            }
            
        except Exception as e:
            logger.error(f"Error refreshing order status {order_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_order_in_database(self, order_id: str, order_data: Dict[str, Any]):
        """Update order information in database"""
        try:
            from app.services.database_service import DatabaseService
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Find the performance entry by order ID
                performance = await DatabaseService.find_performance_by_order_id(db, order_id)
                
                if performance:
                    # Update with fresh order data (only use existing columns)
                    update_data = {}
                    
                    # Log the order status update for debugging
                    logger.info(f"Updating order {order_id}: status={order_data['status']}, executed_qty={order_data['executed_qty']}")
                    
                    # If order is filled and we don't have exit data yet, calculate P&L
                    if (order_data['status'] == 'FILLED' and
                        performance.result == 'pending' and
                        order_data.get('avg_price')):
                        
                        # This is a filled order, calculate final P&L
                        # Get entry price from the related signal
                        entry_price = float(performance.signal.price) if performance.signal else order_data.get('avg_price')
                        exit_price = order_data.get('avg_price')
                        quantity = order_data['executed_qty']
                        
                        # Get signal direction from the related signal
                        if performance.signal:
                            direction = performance.signal.signal_type
                            pnl = self._calculate_pnl(quantity, entry_price, exit_price, direction)
                            
                            # Protect against division by zero
                            if quantity > 0 and entry_price > 0:
                                pnl_percentage = (pnl / (quantity * entry_price)) * 100
                            else:
                                pnl_percentage = 0.0
                            
                            update_data.update({
                                'exit_price': exit_price,
                                'exit_time': order_data['update_time'],
                                'profit_loss': pnl,
                                'profit_percentage': pnl_percentage,
                                'result': 'profit' if pnl > 0 else 'loss' if pnl < 0 else 'breakeven'
                            })
                    
                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                    logger.info(f"Order {order_id} updated in database: status={order_data['status']}")
                else:
                    logger.warning(f"Performance not found for order ID: {order_id}")
                    
        except Exception as e:
            logger.error(f"Error updating order in database: {e}")
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        if not self.client:
            raise Exception("Binance API client not initialized. Cannot get current price without API connection.")
        
        try:
            if self.use_futures:
                # Futures price
                ticker = self.client.futures_symbol_ticker(symbol=symbol)
            else:
                # Spot price
                ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def _calculate_pnl(self, quantity: float, entry_price: float, exit_price: float, direction: str) -> float:
        """Calculate profit/loss"""
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
    
    def _calculate_total_balance(self, balances: Dict[str, Any]) -> float:
        """Calculate total wallet balance in USD"""
        total_usd_value = 0
        
        for asset, balance_info in balances.items():
            total = balance_info.get('total', 0)
            if total > 0:
                if asset in ['USDT', 'BUSD', 'USDC']:
                    # Stablecoins
                    usd_value = total
                elif asset == 'BTC':
                    try:
                        btc_price = float(self.client.get_symbol_ticker(symbol='BTCUSDT')['price'])
                        usd_value = total * btc_price
                    except:
                        usd_value = total * 50000  # Fallback price
                elif asset == 'ETH':
                    try:
                        eth_price = float(self.client.get_symbol_ticker(symbol='ETHUSDT')['price'])
                        usd_value = total * eth_price
                    except:
                        usd_value = total * 3000  # Fallback price
                else:
                    try:
                        price = float(self.client.get_symbol_ticker(symbol=f'{asset}USDT')['price'])
                        usd_value = total * price
                    except:
                        usd_value = 0  # Skip if can't get price
                
                total_usd_value += usd_value
        
        return total_usd_value
    
    def _assess_risk_level(self) -> str:
        """Assess current risk level"""
        if self.daily_pnl < -self.daily_loss_limit * 0.8:
            return 'HIGH'
        elif self.daily_pnl < -self.daily_loss_limit * 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    
    async def _save_open_position_to_history(self, signal: Dict[str, Any], position_size_usd: float, quantity: float, main_order: Dict, stop_loss_order: Dict, take_profit_order: Dict) -> Optional[int]:
        """Save open position to signal performance with OPEN status"""
        try:
            from app.services.database_service import DatabaseService
            
            # Check if signal already has an ID (already saved)
            signal_id = signal.get("id")
            if not signal_id:
                # Signal not yet saved, save it now for the trade
                from app.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    saved_signal = await DatabaseService.save_signal(db, signal)
                    signal_id = saved_signal.id
                    logger.info(f"✅ Signal saved to database for open position: {signal['symbol']}")
            else:
                logger.info(f"📊 Using existing signal ID {signal_id} for open position: {signal['symbol']}")
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                trade_data = {
                    "quantity": quantity,
                    "position_size_usd": position_size_usd,
                    "main_order_id": str(main_order.get("order_id")) if main_order.get("order_id") else None,
                    "stop_loss_order_id": str(stop_loss_order.get("order_id")) if stop_loss_order.get("order_id") else None,
                    "take_profit_order_id": str(take_profit_order.get("order_id")) if take_profit_order.get("order_id") else None,
                    "result": "open",  # New status for open positions
                    "testnet_mode": self.testnet
                }
                
                performance = await DatabaseService.save_trading_performance(db, signal_id, trade_data)
                logger.info(f"✅ Open position saved to performance table: Signal {signal_id}, Order {trade_data['main_order_id']}, Status: OPEN")
                return performance.id
                
        except Exception as e:
            logger.error(f"Error saving open position to performance: {e}")
            return None
    
    async def _save_successful_trade_to_history(self, signal: Dict[str, Any], position_size_usd: float, quantity: float, main_order: Dict, stop_loss_order: Dict, take_profit_order: Dict) -> Optional[int]:
        """Save successful trade to signal performance"""
        try:
            from app.services.database_service import DatabaseService
            
            # Check if signal already has an ID (already saved)
            signal_id = signal.get("id")
            if not signal_id:
                # Signal not yet saved, save it now for the trade
                from app.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    saved_signal = await DatabaseService.save_signal(db, signal)
                    signal_id = saved_signal.id
                    print(f"✅ Signal saved to database for trade: {signal['symbol']}")
            else:
                print(f"📊 Using existing signal ID {signal_id} for trade: {signal['symbol']}")
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                trade_data = {
                    "quantity": quantity,
                    "position_size_usd": position_size_usd,
                    "main_order_id": str(main_order.get("order_id")) if main_order.get("order_id") else None,
                    "stop_loss_order_id": str(stop_loss_order.get("order_id")) if stop_loss_order.get("order_id") else None,
                    "take_profit_order_id": str(take_profit_order.get("order_id")) if take_profit_order.get("order_id") else None,
                    "result": "pending",
                    "testnet_mode": self.testnet
                }
                
                performance = await DatabaseService.save_trading_performance(db, signal_id, trade_data)
                logger.info(f"✅ Trade saved to history: Signal {signal_id}, Order {trade_data['main_order_id']}")
                return performance.id
                
        except Exception as e:
            logger.error(f"Error saving trade to performance: {e}")
            return None
    
    async def _save_failed_trade_to_history(self, signal: Dict[str, Any], position_size_usd: float, quantity: float, failure_reason: str):
        """Save failed trade to signal performance"""
        try:
            from app.services.database_service import DatabaseService
            
            # First save the signal if it doesn't exist
            signal_id = signal.get("id")
            if not signal_id:
                from app.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    saved_signal = await DatabaseService.save_signal(db, signal)
                    signal_id = saved_signal.id
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                trade_data = {
                    "quantity": quantity,
                    "position_size_usd": position_size_usd,
                    "result": "failed_order",
                    "failure_reason": failure_reason,
                    "testnet_mode": self.testnet
                }
                
                await DatabaseService.save_trading_performance(db, signal_id, trade_data)
                logger.info(f"✅ Failed trade saved to history: {signal['symbol']} - {failure_reason}")
                
        except Exception as e:
            logger.error(f"Error saving failed trade to performance: {e}")
    
    async def _save_completed_trade_to_history(self, position: Dict[str, Any], exit_price: float, pnl: float, pnl_percentage: float, reason: str):
        """Save completed trade to database (only when trade is actually finished)"""
        try:
            from app.services.database_service import DatabaseService
            
            # Get signal data from position
            signal_data = {
                'symbol': position['symbol'],
                'signal': position['direction'],
                'entry_price': position['entry_price'],
                'stop_loss': position.get('stop_loss'),
                'take_profit': position.get('take_profit'),
                'confidence': position.get('signal_confidence', 70),
                'timestamp': position.get('timestamp', datetime.now())
            }
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # First save the signal
                saved_signal = await DatabaseService.save_signal(db, signal_data)
                
                # Determine trade result
                if pnl > 0:
                    trade_result = "profit"
                elif pnl < 0:
                    trade_result = "loss"
                else:
                    trade_result = "breakeven"
                
                # Now save the completed trade performance
                trade_data = {
                    "quantity": position['quantity'],
                    "position_size_usd": position['quantity'] * position['entry_price'],
                    "main_order_id": str(position.get('main_order_id')),
                    "stop_loss_order_id": str(position.get('stop_loss_order_id')) if position.get('stop_loss_order_id') else None,
                    "take_profit_order_id": str(position.get('take_profit_order_id')) if position.get('take_profit_order_id') else None,
                    "exit_price": exit_price,
                    "exit_time": datetime.now(),
                    "profit_loss": pnl,
                    "profit_percentage": pnl_percentage,
                    "result": trade_result,
                    "testnet_mode": self.testnet
                }
                
                performance = await DatabaseService.save_trading_performance(db, saved_signal.id, trade_data)
                logger.info(f"✅ Completed trade saved to history: {position['symbol']} - {trade_result} - ${pnl:.2f}")
                return performance.id
                
        except Exception as e:
            logger.error(f"❌ Error saving completed trade to history: {e}")
            return None
    
    async def _update_trade_history_on_exit(self, main_order_id: str, exit_price: float, pnl: float, pnl_percentage: float, reason: str):
        """Update signal performance when position is closed (DEPRECATED - use _save_completed_trade_to_history instead)"""
        try:
            from app.services.database_service import DatabaseService
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Find the performance entry by order ID
                performance = await DatabaseService.find_performance_by_order_id(db, main_order_id)
                
                if performance:
                    # Determine trade result
                    if pnl > 0:
                        trade_result = "profit"
                    elif pnl < 0:
                        trade_result = "loss"
                    else:
                        trade_result = "breakeven"
                    
                    # Update the performance
                    update_data = {
                        "exit_price": exit_price,
                        "exit_time": datetime.now(),
                        "profit_loss": pnl,
                        "profit_percentage": pnl_percentage,
                        "result": trade_result
                    }
                    
                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                    logger.info(f"Performance updated: Signal {performance.signal_id} - {trade_result} - ${pnl:.2f}")
                else:
                    logger.warning(f"Performance not found for order ID: {main_order_id}")
                    
        except Exception as e:
            logger.error(f"Error updating performance on exit: {e}")

    async def _update_position_to_closed(self, main_order_id: str, exit_price: float, pnl: float, pnl_percentage: float, reason: str):
        """Update existing OPEN position to CLOSED status"""
        try:
            from app.services.database_service import DatabaseService
            
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Find the performance entry by order ID
                performance = await DatabaseService.find_performance_by_order_id(db, main_order_id)
                
                if performance:
                    # Determine trade result
                    if pnl > 0:
                        trade_result = "profit"
                    elif pnl < 0:
                        trade_result = "loss"
                    else:
                        trade_result = "breakeven"
                    
                    # Update the existing OPEN position
                    update_data = {
                        "exit_price": exit_price,
                        "exit_time": datetime.now(),
                        "profit_loss": pnl,
                        "profit_percentage": pnl_percentage,
                        "result": trade_result  # Change from OPEN to profit/loss/breakeven
                    }
                    
                    await DatabaseService.update_trading_performance(db, performance.id, update_data)
                    logger.info(f"✅ Position updated from OPEN to {trade_result}: Signal {performance.signal_id} - ${pnl:.2f}")
                else:
                    logger.warning(f"❌ Performance not found for order ID: {main_order_id} - creating new entry")
                    # Fallback: create new entry if not found
                    await self._save_completed_trade_to_history({
                        'symbol': 'UNKNOWN',
                        'direction': 'UNKNOWN',
                        'entry_price': exit_price,  # Best guess
                        'quantity': 0,
                        'main_order_id': main_order_id
                    }, exit_price, pnl, pnl_percentage, reason)
                    
        except Exception as e:
            logger.error(f"Error updating position to closed: {e}")


# Global trader instance - will be initialized from database settings
binance_trader = None

def initialize_global_trader(force_reinit=False):
    """Initialize global trader with database settings"""
    global binance_trader
    if binance_trader is None or force_reinit:
        # Initialize with database settings (None means read from DB)
        binance_trader = BinanceTrader(testnet=None, use_futures=None)
        logger.info(f"Global trader {'reinitialized' if force_reinit else 'initialized'}: {'Testnet' if binance_trader.testnet else 'Mainnet'} mode")
    return binance_trader

# Function to switch between different trading environments
async def switch_trading_environment(use_testnet: bool = True, use_futures: bool = False):
    """
    Switch between different trading environments
    
    Args:
        use_testnet: True for testnet, False for mainnet
        use_futures: True for Futures API, False for Spot API
    """
    global binance_trader
    
    # Get current configuration if trader exists
    current_config = {}
    if binance_trader is not None:
        current_config = {
            'max_position_size': binance_trader.max_position_size,
            'max_daily_trades': binance_trader.max_daily_trades,
            'daily_loss_limit': binance_trader.daily_loss_limit,
            'position_size_mode': binance_trader.position_size_mode,
            'default_position_size_usd': binance_trader.default_position_size_usd
        }
    
    # Update database settings FIRST
    try:
        from app.services.trading_settings_service import get_trading_settings_service
        from app.database import get_sync_db
        
        # Get database session and settings service
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        settings_service.update_risk_management_settings({
            'testnet_mode': use_testnet,
            'use_futures': use_futures
        })
        logger.info(f"Database updated: testnet_mode = {use_testnet}, use_futures = {use_futures}")
    except Exception as e:
        logger.error(f"Failed to update database settings: {e}")
    
    # Create new trader instance with new environment
    binance_trader = BinanceTrader(testnet=use_testnet, use_futures=use_futures)
    
    # Force reload environment variables to ensure fresh credentials
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Override existing environment variables
        logger.info("Environment variables reloaded")
    except ImportError:
        pass
    
    # Restore configuration if we had previous settings
    if current_config:
        binance_trader.max_position_size = current_config['max_position_size']
        binance_trader.max_daily_trades = current_config['max_daily_trades']
        binance_trader.daily_loss_limit = current_config['daily_loss_limit']
        binance_trader.position_size_mode = current_config['position_size_mode']
        binance_trader.default_position_size_usd = current_config['default_position_size_usd']
    
    env_type = "Futures" if use_futures else "Spot"
    net_type = "Testnet" if use_testnet else "Mainnet"
    logger.info(f"Switched to {env_type} {net_type} trading environment")
    
    # Force reinitialize global trader to ensure all services use the new environment
    initialize_global_trader(force_reinit=True)
    
    # Verify the new trader settings
    final_trader = initialize_global_trader(force_reinit=False)
    logger.info(f"Final trader state: testnet={final_trader.testnet}, use_futures={final_trader.use_futures}")
    
    return {
        'success': True,
        'environment': f"{env_type.lower()}_{net_type.lower()}",
        'testnet': use_testnet,
        'futures': use_futures,
        'message': f"Trading environment switched to {env_type} {net_type}",
        'api_key_type': 'TESTNET' if use_testnet else 'MAINNET',
        'credentials_refreshed': True
    }


def get_trading_environment_info():
    """Get current trading environment information"""
    trader = initialize_global_trader(force_reinit=False)
    env_type = "Futures" if trader.use_futures else "Spot"
    net_type = "Testnet" if trader.testnet else "Mainnet"
    
    return {
        'testnet': trader.testnet,
        'futures': trader.use_futures,
        'environment': f"{env_type} {net_type}",
        'description': f"{env_type} API on {net_type}",
        'api_connected': trader.client is not None,
        'safe_mode': trader.testnet
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
            'testnet': trader.testnet,
            'max_position_size': trader.max_position_size,
            'max_daily_trades': trader.max_daily_trades,
            'daily_loss_limit': trader.daily_loss_limit
        }
    }


async def close_trading_position(position_id: str, reason: str = "manual") -> Dict[str, Any]:
    """Close a specific trading position"""
    trader = initialize_global_trader(force_reinit=False)
    return await trader.close_position(position_id, reason)


async def get_binance_trade_history(symbol: str = None, limit: int = 100) -> Dict[str, Any]:
    """Get real trading history from Binance API"""
    trader = initialize_global_trader(force_reinit=False)
    if not trader.client:
        return {'success': False, 'error': 'Binance client not connected'}
    
    try:
        # Get account trades from Binance
        if symbol:
            trades = trader.client.get_my_trades(symbol=symbol, limit=limit)
        else:
            # Get trades for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
            all_trades = []
            for sym in symbols:
                try:
                    sym_trades = trader.client.get_my_trades(symbol=sym, limit=20)
                    all_trades.extend(sym_trades)
                except:
                    continue
            trades = sorted(all_trades, key=lambda x: x['time'], reverse=True)[:limit]
        
        # Convert to our format
        formatted_trades = []
        for trade in trades:
            formatted_trade = {
                'timestamp': datetime.fromtimestamp(trade['time'] / 1000),
                'symbol': trade['symbol'],
                'signal': 'BUY' if trade['isBuyer'] else 'SELL',
                'entry_price': float(trade['price']),
                'quantity': float(trade['qty']),
                'commission': float(trade['commission']),
                'commission_asset': trade['commissionAsset'],
                'trade_id': trade['id'],
                'order_id': trade['orderId'],
                'is_maker': trade['isMaker'],
                'quote_qty': float(trade['quoteQty'])
            }
            formatted_trades.append(formatted_trade)
        
        return {
            'success': True,
            'data': {
                'trades': formatted_trades,
                'count': len(formatted_trades)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        return {'success': False, 'error': str(e)}


async def get_binance_order_history(symbol: str = None, limit: int = 100) -> Dict[str, Any]:
    """Get real order history from Binance API"""
    trader = initialize_global_trader(force_reinit=False)
    if not trader.client:
        return {'success': False, 'error': 'Binance client not connected'}
    
    try:
        if symbol:
            orders = trader.client.get_all_orders(symbol=symbol, limit=limit)
        else:
            # Get orders for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
            all_orders = []
            for sym in symbols:
                try:
                    sym_orders = trader.client.get_all_orders(symbol=sym, limit=20)
                    all_orders.extend(sym_orders)
                except:
                    continue
            orders = sorted(all_orders, key=lambda x: x['time'], reverse=True)[:limit]
        
        # Convert to our format
        formatted_orders = []
        for order in orders:
            formatted_order = {
                'timestamp': datetime.fromtimestamp(order['time'] / 1000),
                'symbol': order['symbol'],
                'order_id': order['orderId'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'price': float(order['price']) if order['price'] != '0.00000000' else None,
                'original_qty': float(order['origQty']),
                'executed_qty': float(order['executedQty']),
                'cumulative_quote_qty': float(order['cummulativeQuoteQty']),
                'time_in_force': order['timeInForce'],
                'update_time': datetime.fromtimestamp(order['updateTime'] / 1000) if order['updateTime'] else None
            }
            formatted_orders.append(formatted_order)
        
        return {
            'success': True,
            'data': {
                'orders': formatted_orders,
                'count': len(formatted_orders)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        return {'success': False, 'error': str(e)}