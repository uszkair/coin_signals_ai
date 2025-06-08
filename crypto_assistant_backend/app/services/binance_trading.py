"""
Binance Automatic Trading Service
Professional trading automation with risk management
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
import logging

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceTrader:
    """Professional Binance trading automation"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        """
        Initialize Binance trader
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet for safe testing (default: True)
        """
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
        self.testnet = testnet
        
        if not self.api_key or not self.api_secret:
            logger.warning("Binance API credentials not found. Trading will be simulated.")
            self.client = None
        else:
            try:
                self.client = Client(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet
                )
                logger.info(f"Binance client initialized (testnet: {self.testnet})")
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
            return self._simulate_account_info()
        
        try:
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
                'account_type': account.get('accountType', 'SPOT'),
                'can_trade': account.get('canTrade', False),
                'can_withdraw': account.get('canWithdraw', False),
                'can_deposit': account.get('canDeposit', False),
                'balances': balances,
                'total_wallet_balance': self._calculate_total_balance(balances),
                'maker_commission': account.get('makerCommission', 10),
                'taker_commission': account.get('takerCommission', 10)
            }
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting account info: {e}")
            return {'error': str(e)}
    
    async def execute_signal_trade(self, signal: Dict[str, Any], position_size_usd: float = None) -> Dict[str, Any]:
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
            
            return {
                'success': True,
                'position_id': position_id,
                'main_order': main_order,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'position_size_usd': position_size_usd,
                'quantity': quantity,
                'expected_profit': self._calculate_expected_profit(quantity, entry_price, take_profit, direction),
                'max_loss': self._calculate_max_loss(quantity, entry_price, stop_loss, direction)
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
            close_direction = SIDE_SELL if direction == 'BUY' else SIDE_BUY
            close_order = await self._place_market_order(symbol, close_direction, quantity)
            
            if close_order['success']:
                # Calculate P&L
                entry_price = position['entry_price']
                exit_price = close_order.get('price', 0)
                pnl = self._calculate_pnl(quantity, entry_price, exit_price, direction)
                
                # Update daily P&L
                self.daily_pnl += pnl
                
                # Remove from active positions
                del self.active_positions[position_id]
                
                return {
                    'success': True,
                    'position_id': position_id,
                    'close_order': close_order,
                    'pnl': pnl,
                    'pnl_percentage': (pnl / (quantity * entry_price)) * 100,
                    'reason': reason
                }
            else:
                return close_order
                
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions with current P&L"""
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
                
                positions_with_pnl[position_id] = {
                    **position,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percentage': (unrealized_pnl / (position['quantity'] * position['entry_price'])) * 100
                }
                
            except Exception as e:
                logger.error(f"Error calculating P&L for position {position_id}: {e}")
                positions_with_pnl[position_id] = position
        
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
            total_balance = account_info.get('total_wallet_balance', 10000)  # Default for simulation
            base_size = total_balance * self.max_position_size
        
        # Adjust based on confidence (optional)
        if self.position_size_mode == 'percentage':
            confidence_multiplier = min(confidence / 100, 1.0)
            return base_size * confidence_multiplier
        else:
            # For fixed USD mode, don't adjust by confidence
            return base_size
    
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
            return self._simulate_symbol_info(symbol)
        
        try:
            exchange_info = self.client.get_exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    return symbol_info
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def _calculate_quantity(self, position_size_usd: float, price: float, symbol_info: Dict[str, Any]) -> float:
        """Calculate order quantity with proper precision"""
        quantity = position_size_usd / price
        
        # Get step size for precision
        step_size = 0.001  # Default
        for filter_info in symbol_info.get('filters', []):
            if filter_info['filterType'] == 'LOT_SIZE':
                step_size = float(filter_info['stepSize'])
                break
        
        # Round down to step size
        precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
        return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    
    async def _place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order"""
        if not self.client:
            return self._simulate_order(symbol, side, quantity, 'MARKET')
        
        try:
            binance_side = SIDE_BUY if side == 'BUY' else SIDE_SELL
            
            order = self.client.order_market(
                symbol=symbol,
                side=binance_side,
                quantity=quantity
            )
            
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
            logger.error(f"Binance order error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _place_stop_loss_order(self, symbol: str, direction: str, quantity: float, stop_price: float, symbol_info: Dict[str, Any]) -> Dict[str, Any]:
        """Place a stop loss order"""
        if not self.client:
            return self._simulate_order(symbol, 'STOP_LOSS', quantity, 'STOP_LOSS_LIMIT')
        
        try:
            side = SIDE_SELL if direction == 'BUY' else SIDE_BUY
            
            order = self.client.order_stop_loss_limit(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stopPrice=stop_price,
                price=stop_price * 0.99 if side == SIDE_SELL else stop_price * 1.01  # Slight buffer
            )
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'type': 'STOP_LOSS',
                'stop_price': stop_price
            }
            
        except Exception as e:
            logger.error(f"Error placing stop loss order: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _place_take_profit_order(self, symbol: str, direction: str, quantity: float, take_profit_price: float, symbol_info: Dict[str, Any]) -> Dict[str, Any]:
        """Place a take profit order"""
        if not self.client:
            return self._simulate_order(symbol, 'TAKE_PROFIT', quantity, 'TAKE_PROFIT_LIMIT')
        
        try:
            side = SIDE_SELL if direction == 'BUY' else SIDE_BUY
            
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
            
        except Exception as e:
            logger.error(f"Error placing take profit order: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        if not self.client:
            return True  # Simulate success
        
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            return True
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        if not self.client:
            return 50000.0  # Simulate price
        
        try:
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
    
    # Simulation methods for testing without real API
    def _simulate_account_info(self) -> Dict[str, Any]:
        """Simulate account info for testing"""
        return {
            'account_type': 'SPOT',
            'can_trade': True,
            'can_withdraw': True,
            'can_deposit': True,
            'balances': {
                'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0},
                'BTC': {'free': 0.1, 'locked': 0.0, 'total': 0.1}
            },
            'total_wallet_balance': 10000.0,
            'maker_commission': 10,
            'taker_commission': 10
        }
    
    def _simulate_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Simulate symbol info for testing"""
        return {
            'symbol': symbol,
            'status': 'TRADING',
            'filters': [
                {'filterType': 'LOT_SIZE', 'stepSize': '0.00001000'},
                {'filterType': 'PRICE_FILTER', 'tickSize': '0.01000000'}
            ]
        }
    
    def _simulate_order(self, symbol: str, side: str, quantity: float, order_type: str) -> Dict[str, Any]:
        """Simulate order execution for testing"""
        import random
        
        return {
            'success': True,
            'order_id': f'SIM_{random.randint(100000, 999999)}',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': 50000.0 + random.uniform(-100, 100),  # Simulate price
            'commission': quantity * 0.001,  # 0.1% commission
            'status': 'FILLED',
            'type': order_type
        }


# Global trader instance
binance_trader = BinanceTrader(testnet=False)  # Use mainnet for real wallet data


async def execute_automatic_trade(signal: Dict[str, Any], position_size_usd: float = None) -> Dict[str, Any]:
    """
    Execute automatic trade based on signal
    
    Args:
        signal: Trading signal from signal engine
        position_size_usd: Optional position size override
        
    Returns:
        Trade execution result
    """
    return await binance_trader.execute_signal_trade(signal, position_size_usd)


async def get_trading_account_status() -> Dict[str, Any]:
    """Get current trading account status"""
    account_info = await binance_trader.get_account_info()
    trading_stats = await binance_trader.get_trading_statistics()
    active_positions = await binance_trader.get_active_positions()
    
    return {
        'account_info': account_info,
        'trading_statistics': trading_stats,
        'active_positions': active_positions,
        'trader_config': {
            'testnet': binance_trader.testnet,
            'max_position_size': binance_trader.max_position_size,
            'max_daily_trades': binance_trader.max_daily_trades,
            'daily_loss_limit': binance_trader.daily_loss_limit
        }
    }


async def close_trading_position(position_id: str, reason: str = "manual") -> Dict[str, Any]:
    """Close a specific trading position"""
    return await binance_trader.close_position(position_id, reason)


async def get_binance_trade_history(symbol: str = None, limit: int = 100) -> Dict[str, Any]:
    """Get real trading history from Binance API"""
    if not binance_trader.client:
        return {'success': False, 'error': 'Binance client not connected'}
    
    try:
        # Get account trades from Binance
        if symbol:
            trades = binance_trader.client.get_my_trades(symbol=symbol, limit=limit)
        else:
            # Get trades for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
            all_trades = []
            for sym in symbols:
                try:
                    sym_trades = binance_trader.client.get_my_trades(symbol=sym, limit=20)
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
    if not binance_trader.client:
        return {'success': False, 'error': 'Binance client not connected'}
    
    try:
        if symbol:
            orders = binance_trader.client.get_all_orders(symbol=symbol, limit=limit)
        else:
            # Get orders for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
            all_orders = []
            for sym in symbols:
                try:
                    sym_orders = binance_trader.client.get_all_orders(symbol=sym, limit=20)
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