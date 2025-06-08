"""
Trading API Router
Endpoints for automatic trading functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.services.binance_trading import (
    execute_automatic_trade,
    get_trading_account_status,
    close_trading_position,
    initialize_global_trader,
    get_binance_trade_history,
    get_binance_order_history,
    switch_trading_environment,
    get_trading_environment_info
)
from app.services.signal_engine import get_current_signal
from app.services.trading_settings_service import trading_settings_service

router = APIRouter(prefix="/api/trading", tags=["trading"])


class TradeRequest(BaseModel):
    symbol: str
    interval: str = "1h"
    position_size_usd: Optional[float] = None
    force_execute: bool = False  # Override confidence checks


class ClosePositionRequest(BaseModel):
    position_id: str
    reason: str = "manual"


class TradingConfig(BaseModel):
    max_position_size: Optional[float] = None
    max_daily_trades: Optional[int] = None
    daily_loss_limit: Optional[float] = None
    testnet: Optional[bool] = None


class PositionSizeConfig(BaseModel):
    mode: str  # 'percentage' or 'fixed_usd'
    fixed_amount_usd: Optional[float] = None  # For fixed_usd mode
    max_percentage: Optional[float] = None    # For percentage mode (e.g., 2.5 for 2.5%)


@router.get("/account")
async def get_account_status():
    """Get trading account status and statistics"""
    try:
        status = await get_trading_account_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_trade(trade_request: TradeRequest):
    """
    Execute automatic trade based on current signal
    
    This endpoint:
    1. Gets current signal for the symbol
    2. Validates the signal quality
    3. Executes the trade with proper risk management
    4. Returns trade execution details
    """
    try:
        # Get current signal
        signal = await get_current_signal(trade_request.symbol, trade_request.interval)
        
        # Add force execute override
        if trade_request.force_execute:
            signal['confidence'] = max(signal.get('confidence', 0), 70)  # Override low confidence
        
        # Execute trade
        result = await execute_automatic_trade(signal, trade_request.position_size_usd)
        
        return {
            "success": True,
            "data": {
                "trade_result": result,
                "signal_used": {
                    "symbol": signal['symbol'],
                    "signal": signal['signal'],
                    "confidence": signal['confidence'],
                    "entry_price": signal['entry_price'],
                    "stop_loss": signal['stop_loss'],
                    "take_profit": signal['take_profit']
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExecuteSignalRequest(BaseModel):
    signal: Dict[str, Any]
    position_size_usd: Optional[float] = None


@router.post("/execute-signal")
async def execute_signal_trade(request: ExecuteSignalRequest):
    """
    Execute trade based on provided signal
    
    Use this endpoint to trade with a specific signal rather than getting current signal
    """
    try:
        result = await execute_automatic_trade(request.signal, request.position_size_usd)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_active_positions():
    """Get all active trading positions"""
    try:
        trader = initialize_global_trader()
        positions = await trader.get_active_positions()
        
        return {
            "success": True,
            "data": {
                "positions": positions,
                "count": len(positions)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-position")
async def close_position(close_request: ClosePositionRequest):
    """Close a specific trading position"""
    try:
        result = await close_trading_position(close_request.position_id, close_request.reason)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-all-positions")
async def close_all_positions(reason: str = "manual_close_all"):
    """Close all active trading positions"""
    try:
        trader = initialize_global_trader()
        positions = await trader.get_active_positions()
        results = []
        
        for position_id in positions.keys():
            result = await close_trading_position(position_id, reason)
            results.append({
                "position_id": position_id,
                "result": result
            })
        
        return {
            "success": True,
            "data": {
                "closed_positions": results,
                "total_closed": len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_trading_statistics():
    """Get detailed trading statistics and performance metrics"""
    try:
        trader = initialize_global_trader()
        stats = await trader.get_trading_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_trading_config(config: TradingConfig):
    """Update trading configuration and risk management settings"""
    try:
        # Update settings in database
        update_data = {}
        
        if config.max_position_size is not None:
            update_data['max_position_size'] = config.max_position_size
        
        if config.max_daily_trades is not None:
            update_data['max_daily_trades'] = config.max_daily_trades
        
        if config.daily_loss_limit is not None:
            update_data['daily_loss_limit'] = config.daily_loss_limit
        
        if config.testnet is not None:
            update_data['testnet_mode'] = config.testnet
        
        # Update risk management settings in database
        await trading_settings_service.update_risk_management_settings(update_data)
        
        # Also update trader for immediate effect
        trader = initialize_global_trader()
        if config.max_position_size is not None:
            trader.max_position_size = config.max_position_size
        
        if config.max_daily_trades is not None:
            trader.max_daily_trades = config.max_daily_trades
        
        if config.daily_loss_limit is not None:
            trader.daily_loss_limit = config.daily_loss_limit
        
        # Get current settings from database
        current_settings = await trading_settings_service.get_risk_management_settings()
        
        return {
            "success": True,
            "data": {
                "updated_settings": update_data,
                "current_config": {
                    "max_position_size": current_settings['max_position_size'],
                    "max_daily_trades": current_settings['max_daily_trades'],
                    "daily_loss_limit": current_settings['daily_loss_limit'],
                    "testnet": current_settings['testnet_mode']
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_trading_config():
    """Get current trading configuration"""
    try:
        # Get settings from database
        risk_settings = await trading_settings_service.get_risk_management_settings()
        position_settings = await trading_settings_service.get_position_size_settings()
        
        return {
            "success": True,
            "data": {
                "max_position_size": position_settings['max_position_size'],
                "max_daily_trades": risk_settings['max_daily_trades'],
                "daily_loss_limit": risk_settings['daily_loss_limit'],
                "testnet": risk_settings['testnet_mode'],
                "api_connected": initialize_global_trader().client is not None,
                "position_size_config": {
                    "mode": position_settings['mode'],
                    "fixed_amount_usd": position_settings['default_position_size_usd'],
                    "max_percentage": position_settings['max_position_size'] * 100 if position_settings['max_position_size'] else None  # Convert to percentage
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/position-size-config")
async def update_position_size_config(config: PositionSizeConfig):
    """Update position size configuration"""
    try:
        # Validate input
        if config.mode not in ['percentage', 'fixed_usd']:
            raise HTTPException(status_code=400, detail="Mode must be 'percentage' or 'fixed_usd'")
        
        if config.mode == 'fixed_usd' and not config.fixed_amount_usd:
            raise HTTPException(status_code=400, detail="fixed_amount_usd is required for fixed_usd mode")
        
        if config.mode == 'percentage' and not config.max_percentage:
            raise HTTPException(status_code=400, detail="max_percentage is required for percentage mode")
        
        # Validate ranges
        if config.fixed_amount_usd and (config.fixed_amount_usd < 1 or config.fixed_amount_usd > 10000):
            raise HTTPException(status_code=400, detail="Fixed amount must be between $1 and $10,000")
        
        if config.max_percentage and (config.max_percentage < 0.1 or config.max_percentage > 10):
            raise HTTPException(status_code=400, detail="Percentage must be between 0.1% and 10%")
        
        # Update configuration in database
        update_data = {
            'mode': config.mode,
            'max_percentage': config.max_percentage,  # Use the correct key for the service
            'fixed_amount_usd': config.fixed_amount_usd
        }
        
        await trading_settings_service.update_position_size_settings(update_data)
        
        # Also update trader for immediate effect
        trader = initialize_global_trader()
        trader.set_position_size_config(
            mode=config.mode,
            amount=config.fixed_amount_usd,
            max_percentage=config.max_percentage
        )
        
        # Get updated settings from database
        updated_settings = await trading_settings_service.get_position_size_settings()
        
        return {
            "success": True,
            "message": "Position size configuration updated successfully",
            "data": {
                "mode": updated_settings['mode'],
                "fixed_amount_usd": updated_settings['default_position_size_usd'],
                "max_percentage": updated_settings['max_position_size'] * 100 if updated_settings['max_position_size'] else None  # Convert to percentage
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position-size-config")
async def get_position_size_config():
    """Get current position size configuration"""
    try:
        # Get settings from database
        position_settings = await trading_settings_service.get_position_size_settings()
        
        return {
            "success": True,
            "data": {
                "mode": position_settings['mode'],
                "fixed_amount_usd": position_settings['default_position_size_usd'],
                "max_percentage": position_settings['max_position_size'] * 100 if position_settings['max_position_size'] else None,  # Convert to percentage
                "description": {
                    "percentage": "Position size calculated as percentage of total portfolio",
                    "fixed_usd": "Fixed USD amount per trade regardless of portfolio size"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-position-size")
async def validate_position_size_config(config: PositionSizeConfig):
    """Validate position size configuration before saving"""
    try:
        # Get current wallet balance
        trader = initialize_global_trader()
        account_info = await trader.get_account_info()
        total_balance = account_info.get('total_wallet_balance', 0)
        
        # Calculate what the position size would be
        if config.mode == 'percentage' and config.max_percentage:
            calculated_size = total_balance * (config.max_percentage / 100)
            mode_description = f"{config.max_percentage}% of wallet"
        elif config.mode == 'fixed_usd' and config.fixed_amount_usd:
            calculated_size = config.fixed_amount_usd
            mode_description = f"${config.fixed_amount_usd} fixed amount"
        else:
            return {
                "success": False,
                "error": "Invalid configuration",
                "details": {"message": "Either percentage or fixed amount must be specified"}
            }
            
        # Check if we're in mainnet mode and validate requirements
        if not trader.testnet:  # Only validate in mainnet mode
            # Get minimum requirements for common symbols
            symbols_to_check = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            validation_errors = []
            
            for symbol in symbols_to_check:
                min_required = trader._get_minimum_position_size(symbol)
                if calculated_size < min_required:
                    validation_errors.append({
                        'symbol': symbol,
                        'calculated_size': calculated_size,
                        'minimum_required': min_required
                    })
            
            # Additional check for fixed USD mode: ensure user has enough balance
            if config.mode == 'fixed_usd' and calculated_size > total_balance:
                return {
                    "success": False,
                    "error": "Insufficient wallet balance for fixed USD amount",
                    "details": {
                        "wallet_balance": total_balance,
                        "requested_amount": calculated_size,
                        "mode": mode_description,
                        "recommendation": f"Reduce fixed amount to ${total_balance:.2f} or add more funds to wallet"
                    }
                }
            
            if validation_errors:
                if config.mode == 'percentage':
                    recommendation = f"Increase wallet balance to at least ${max(err['minimum_required'] for err in validation_errors) / (config.max_percentage / 100):.2f} or use fixed USD mode with at least ${max(err['minimum_required'] for err in validation_errors):.2f}"
                else:  # fixed_usd
                    recommendation = f"Increase fixed amount to at least ${max(err['minimum_required'] for err in validation_errors):.2f}"
                
                return {
                    "success": False,
                    "error": "Position size too small for mainnet trading",
                    "details": {
                        "wallet_balance": total_balance,
                        "calculated_position_size": calculated_size,
                        "mode": mode_description,
                        "validation_errors": validation_errors,
                        "recommendation": recommendation
                    }
                }
        
        return {
            "success": True,
            "message": "Position size configuration is valid",
            "data": {
                "wallet_balance": total_balance,
                "calculated_position_size": calculated_size if config.mode == 'percentage' else config.fixed_amount_usd,
                "testnet": trader.testnet
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_binance_connection():
    """Test Binance API connection"""
    try:
        trader = initialize_global_trader()
        account_info = await trader.get_account_info()
        
        if 'error' in account_info:
            return {
                "success": False,
                "data": {
                    "connected": False,
                    "error": account_info['error'],
                    "testnet": binance_trader.testnet
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "connected": True,
                    "account_type": account_info.get('account_type'),
                    "can_trade": account_info.get('can_trade'),
                    "testnet": trader.testnet,
                    "total_balance": account_info.get('total_wallet_balance')
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-assessment")
async def get_risk_assessment():
    """Get current risk assessment and recommendations"""
    try:
        trader = initialize_global_trader()
        stats = await trader.get_trading_statistics()
        positions = await trader.get_active_positions()
        
        # Calculate risk metrics
        total_exposure = sum(
            pos.get('quantity', 0) * pos.get('entry_price', 0) 
            for pos in positions.values()
        )
        
        account_balance = stats.get('account_balance', 10000)
        exposure_percentage = (total_exposure / account_balance) * 100 if account_balance > 0 else 0
        
        # Risk recommendations
        recommendations = []
        
        if exposure_percentage > 50:
            recommendations.append("High exposure detected - consider reducing position sizes")
        
        if stats.get('daily_trades', 0) > stats.get('max_daily_trades', 10) * 0.8:
            recommendations.append("Approaching daily trade limit - be selective with new trades")
        
        if stats.get('daily_pnl', 0) < -stats.get('daily_loss_limit', 0.05) * 0.5:
            recommendations.append("Significant daily losses - consider stopping trading for today")
        
        risk_level = "LOW"
        if exposure_percentage > 30 or stats.get('daily_pnl', 0) < -0.02:
            risk_level = "MEDIUM"
        if exposure_percentage > 50 or stats.get('daily_pnl', 0) < -0.05:
            risk_level = "HIGH"
        
        return {
            "success": True,
            "data": {
                "risk_level": risk_level,
                "exposure_percentage": exposure_percentage,
                "total_exposure_usd": total_exposure,
                "daily_pnl": stats.get('daily_pnl', 0),
                "daily_pnl_percentage": (stats.get('daily_pnl', 0) / account_balance) * 100,
                "active_positions": len(positions),
                "recommendations": recommendations,
                "can_trade": stats.get('can_trade', True)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop - close all positions and disable trading"""
    try:
        # Close all positions
        trader = initialize_global_trader()
        positions = await trader.get_active_positions()
        closed_positions = []
        
        for position_id in positions.keys():
            result = await close_trading_position(position_id, "emergency_stop")
            closed_positions.append(result)
        
        # Set daily trades to maximum to prevent new trades
        trader.daily_trades = trader.max_daily_trades
        
        return {
            "success": True,
            "data": {
                "message": "Emergency stop executed",
                "closed_positions": len(closed_positions),
                "trading_disabled": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade-history")
async def get_real_trade_history(symbol: Optional[str] = None, limit: int = 100):
    """Get real trading history from Binance API"""
    try:
        result = await get_binance_trade_history(symbol, limit)
        
        if result['success']:
            return {
                "success": True,
                "data": result['data']
            }
        else:
            return {
                "success": False,
                "error": result['error']
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-history")
async def get_real_order_history(symbol: Optional[str] = None, limit: int = 100):
    """Get real order history from Binance API"""
    try:
        result = await get_binance_order_history(symbol, limit)
        
        if result['success']:
            return {
                "success": True,
                "data": result['data']
            }
        else:
            return {
                "success": False,
                "error": result['error']
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet-balance")
async def get_wallet_balance():
    """Get wallet balance from Binance API or simulated data"""
    try:
        # Debug logging
        trader = initialize_global_trader()
        print(f"DEBUG: binance_trader.testnet = {trader.testnet}")
        print(f"DEBUG: binance_trader.client = {trader.client}")
        
        account_info = await trader.get_account_info()
        print(f"DEBUG: account_info testnet flag = {account_info.get('testnet', 'NOT_SET')}")
        
        if 'error' in account_info:
            # Check if it's an API key error
            error_msg = account_info['error']
            if 'Invalid API-key' in error_msg or 'code=-2015' in error_msg:
                return {
                    "success": False,
                    "error": "Binance API kulcsok érvénytelenek vagy nincs megfelelő jogosultság. Ellenőrizd a .env fájlban a BINANCE_API_KEY és BINANCE_API_SECRET értékeket.",
                    "details": {
                        "error_code": "-2015",
                        "solution": "1. Ellenőrizd hogy a Binance API kulcsok helyesek-e\n2. Győződj meg róla hogy az IP cím engedélyezett a Binance fiókban\n3. Ellenőrizd hogy az API kulcsoknak van-e 'Spot & Margin Trading' jogosultsága",
                        "testnet": trader.testnet
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Binance API hiba: {error_msg}",
                    "testnet": trader.testnet
                }
        
        # If in testnet mode, use the simulated data directly
        if trader.testnet:
            # Use the total_wallet_balance from simulated account info
            total_balance = account_info.get('total_wallet_balance', 10000.0)
            balances = account_info.get('balances', {})
            
            # Convert balances format for frontend
            significant_balances = []
            for asset, balance_info in balances.items():
                if balance_info['total'] > 0:
                    # For simulated data, calculate USDT value
                    if asset in ['USDT', 'BUSD', 'USDC']:
                        usdt_value = balance_info['total']
                    elif asset == 'BTC':
                        usdt_value = balance_info['total'] * 50000  # Simulated BTC price
                    elif asset == 'ETH':
                        usdt_value = balance_info['total'] * 3000   # Simulated ETH price
                    else:
                        usdt_value = balance_info['total'] * 100    # Default simulated price
                    
                    significant_balances.append({
                        'asset': asset,
                        'free': balance_info['free'],
                        'locked': balance_info['locked'],
                        'total': balance_info['total'],
                        'usdt_value': usdt_value
                    })
            
            return {
                "success": True,
                "data": {
                    "total_balance_usdt": total_balance,
                    "balances": significant_balances,
                    "account_type": account_info.get('account_type'),
                    "can_trade": account_info.get('can_trade'),
                    "testnet": account_info.get('testnet', True)
                }
            }
        
        # Mainnet mode - calculate real balance with live prices
        balances = account_info.get('balances', {})
        total_balance_usdt = 0
        
        # Get current prices for conversion
        significant_balances = []
        for asset, balance_info in balances.items():
            if balance_info['total'] > 0:
                if asset in ['USDT', 'BUSD', 'USDC']:
                    # Stablecoins
                    usdt_value = balance_info['total']
                elif asset == 'BTC':
                    # Get BTC price
                    try:
                        btc_price = await trader._get_current_price('BTCUSDT')
                        usdt_value = balance_info['total'] * btc_price
                    except:
                        usdt_value = balance_info['total'] * 50000  # Fallback price
                elif asset == 'ETH':
                    # Get ETH price
                    try:
                        eth_price = await trader._get_current_price('ETHUSDT')
                        usdt_value = balance_info['total'] * eth_price
                    except:
                        usdt_value = balance_info['total'] * 3000  # Fallback price
                else:
                    # Try to get price for other assets
                    try:
                        price = await trader._get_current_price(f'{asset}USDT')
                        usdt_value = balance_info['total'] * price
                    except:
                        usdt_value = 0  # Skip if can't get price
                
                total_balance_usdt += usdt_value
                
                if usdt_value > 1:  # Only show balances worth more than $1
                    significant_balances.append({
                        'asset': asset,
                        'free': balance_info['free'],
                        'locked': balance_info['locked'],
                        'total': balance_info['total'],
                        'usdt_value': usdt_value
                    })
        
        return {
            "success": True,
            "data": {
                "total_balance_usdt": total_balance_usdt,
                "balances": significant_balances,
                "account_type": account_info.get('account_type'),
                "can_trade": account_info.get('can_trade'),
                "testnet": account_info.get('testnet', False)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TradingEnvironmentRequest(BaseModel):
    use_testnet: bool
    use_futures: bool = False


@router.post("/switch-environment")
async def switch_trading_environment_endpoint(request: TradingEnvironmentRequest):
    """
    Switch between different trading environments
    
    Args:
        use_testnet: True for testnet, False for mainnet
        use_futures: True for Futures API, False for Spot API
    """
    try:
        result = await switch_trading_environment(request.use_testnet, request.use_futures)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment")
async def get_trading_environment():
    """Get current trading environment information (testnet vs mainnet)"""
    try:
        environment_info = get_trading_environment_info()
        
        return {
            "success": True,
            "data": environment_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/minimum-requirements")
async def get_minimum_trading_requirements():
    """Get Binance minimum trading requirements for each symbol"""
    try:
        # Binance minimum trading requirements (approximate values)
        requirements = {
            "BTCUSDT": {
                "min_notional": 10.0,
                "min_qty": 0.00001,
                "step_size": 0.00001,
                "description": "Minimum $10 trade value"
            },
            "ETHUSDT": {
                "min_notional": 10.0,
                "min_qty": 0.0001,
                "step_size": 0.0001,
                "description": "Minimum $10 trade value"
            },
            "BNBUSDT": {
                "min_notional": 10.0,
                "min_qty": 0.001,
                "step_size": 0.001,
                "description": "Minimum $10 trade value"
            },
            "ADAUSDT": {
                "min_notional": 5.0,
                "min_qty": 0.1,
                "step_size": 0.1,
                "description": "Minimum $5 trade value"
            },
            "SOLUSDT": {
                "min_notional": 10.0,
                "min_qty": 0.001,
                "step_size": 0.001,
                "description": "Minimum $10 trade value"
            },
            "DOTUSDT": {
                "min_notional": 10.0,
                "min_qty": 0.01,
                "step_size": 0.01,
                "description": "Minimum $10 trade value"
            }
        }
        
        return {
            "success": True,
            "data": {
                "requirements": requirements,
                "current_position_size": initialize_global_trader().default_position_size_usd if initialize_global_trader().position_size_mode == 'fixed_usd' else None,
                "current_wallet_balance": (await initialize_global_trader().get_account_info()).get('total_wallet_balance', 0),
                "recommendation": "Use fixed position size of at least $15 USD to meet all minimum requirements"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))