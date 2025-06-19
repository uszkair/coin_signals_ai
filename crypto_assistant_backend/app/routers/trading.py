"""
Trading API Router
Endpoints for automatic trading functionality
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
from app.services.trading_settings_service import get_trading_settings_service
from app.services.database_service import DatabaseService
from app.database import get_db, get_sync_db
from sqlalchemy.ext.asyncio import AsyncSession

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
        
        # Check if trade was rejected and return appropriate response
        if not result.get('success', False):
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "data": {
                    "trade_result": result,
                    "signal_used": {
                        "symbol": signal['symbol'],
                        "signal": signal['signal'],
                        "confidence": signal['confidence'],
                        "entry_price": signal['entry_price'],
                        "stop_loss": signal['stop_loss'],
                        "take_profit": signal['take_profit']
                    },
                    "saved_to_history": True,  # Rejected trades are now saved to history
                    "rejection_reason": result.get('rejection_reason', 'unknown')
                }
            }
        
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
        
        # Check if trade was rejected and return appropriate response
        if not result.get('success', False):
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "data": {
                    "trade_result": result,
                    "saved_to_history": True,  # Rejected trades are now saved to history
                    "rejection_reason": result.get('rejection_reason', 'unknown')
                }
            }
        
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
async def close_all_positions(reason: str = "manual_close_all", db: AsyncSession = Depends(get_db)):
    """Close all active trading positions and save to history"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        if not trader.use_futures:
            return {
                "success": False,
                "error": "Position closing is only supported for Futures trading"
            }
        
        # Get all active positions from Binance
        try:
            positions = trader.client.futures_position_information()
            active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]
            
            if not active_positions:
                return {
                    "success": True,
                    "data": {
                        "message": "No active positions to close",
                        "closed_positions": [],
                        "total_closed": 0
                    }
                }
            
            results = []
            
            for pos in active_positions:
                symbol = pos.get('symbol')
                position_amt = float(pos.get('positionAmt', 0))
                entry_price = float(pos.get('entryPrice', 0))
                
                try:
                    # Get current market price for P&L calculation
                    try:
                        current_price = await trader._get_current_price(symbol)
                        if current_price is None or current_price <= 0:
                            current_price = entry_price  # Fallback
                    except:
                        current_price = entry_price  # Fallback
                    
                    # Ensure we have valid prices
                    if current_price is None:
                        current_price = entry_price or 0
                    if entry_price is None:
                        entry_price = current_price or 0
                    
                    # Determine order side (opposite of position)
                    if position_amt > 0:
                        # LONG position -> SELL to close
                        side = 'SELL'
                        quantity = abs(position_amt)
                        position_side = 'BUY'  # Original position was BUY
                    else:
                        # SHORT position -> BUY to close
                        side = 'BUY'
                        quantity = abs(position_amt)
                        position_side = 'SELL'  # Original position was SELL
                    
                    # Calculate P&L before closing
                    # Safe P&L calculation with None checks
                    if current_price is not None and entry_price is not None:
                        if position_amt > 0:  # LONG position
                            pnl = quantity * (current_price - entry_price)
                        else:  # SHORT position
                            pnl = quantity * (entry_price - current_price)
                    else:
                        pnl = 0.0  # Default to 0 if prices are None
                    
                    # Calculate P&L percentage
                    if quantity > 0 and entry_price > 0:
                        pnl_percentage = (pnl / (quantity * entry_price)) * 100
                    else:
                        pnl_percentage = 0.0
                    
                    # Place market order to close position
                    order_result = trader.client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity,
                        reduceOnly=True  # This ensures we're closing, not opening new position
                    )
                    
                    # Get actual exit price from order result
                    exit_price = current_price
                    if order_result.get('avgPrice'):
                        exit_price = float(order_result.get('avgPrice'))
                    elif order_result.get('price'):
                        exit_price = float(order_result.get('price'))
                    
                    # Recalculate P&L with actual exit price
                    # Safe final P&L calculation with None checks
                    if exit_price is not None and entry_price is not None:
                        if position_amt > 0:  # LONG position
                            final_pnl = quantity * (exit_price - entry_price)
                        else:  # SHORT position
                            final_pnl = quantity * (entry_price - exit_price)
                    else:
                        final_pnl = 0.0  # Default to 0 if prices are None
                    
                    # Recalculate P&L percentage
                    if quantity > 0 and entry_price > 0:
                        final_pnl_percentage = (final_pnl / (quantity * entry_price)) * 100
                    else:
                        final_pnl_percentage = 0.0
                    
                    # Save closed position to database as a manual trade
                    try:
                        # Create a synthetic signal for the closed position
                        synthetic_signal = {
                            'symbol': symbol,
                            'signal': position_side,  # BUY or SELL (original position direction)
                            'price': entry_price,
                            'entry_price': entry_price,
                            'stop_loss': None,
                            'take_profit': None,
                            'confidence': 100,  # Manual close, so 100% confidence
                            'timestamp': datetime.now(),
                            'signal_type': position_side,
                            'source': 'emergency_stop',
                            'decision_factors': f'Emergency stop - close all positions - {reason}'
                        }
                        
                        # Save synthetic signal to database
                        saved_signal = await DatabaseService.save_signal(db, synthetic_signal)
                        
                        # Save trading performance for the closed position
                        trade_data = {
                            "quantity": quantity,
                            "position_size_usd": quantity * entry_price,
                            "main_order_id": str(order_result.get('orderId')),
                            "exit_price": exit_price,
                            "exit_time": datetime.now(),
                            "profit_loss": final_pnl,
                            "profit_percentage": final_pnl_percentage,
                            "result": "profit" if final_pnl > 0 else "loss" if final_pnl < 0 else "breakeven",
                            "testnet_mode": trader.testnet,
                            "close_reason": reason
                        }
                        
                        await DatabaseService.save_trading_performance(db, saved_signal.id, trade_data)
                        logger.info(f"✅ Emergency closed position saved to history: {symbol} - {trade_data['result']} - ${final_pnl:.2f}")
                        
                        # Send notification for closed position
                        try:
                            from app.services.notification_service import notify_position_closed
                            closed_position_data = {
                                'symbol': symbol,
                                'direction': position_side,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'pnl': final_pnl,
                                'pnl_percentage': final_pnl_percentage,
                                'reason': reason,
                                'position_id': f"{symbol}_emergency"
                            }
                            await notify_position_closed(closed_position_data, db)
                            logger.info(f"✅ Emergency position closed notification sent for {symbol}")
                        except Exception as notification_error:
                            logger.error(f"❌ Failed to send emergency position closed notification: {notification_error}")
                        
                    except Exception as db_error:
                        logger.error(f"Error saving emergency closed position to database: {db_error}")
                        # Don't fail the entire operation if database save fails
                    
                    results.append({
                        "symbol": symbol,
                        "success": True,
                        "side": side,
                        "quantity": quantity,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": final_pnl,
                        "pnl_percentage": final_pnl_percentage,
                        "order_id": order_result.get('orderId'),
                        "saved_to_history": True
                    })
                    
                except Exception as pos_error:
                    logger.error(f"Error closing position for {symbol}: {pos_error}")
                    results.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(pos_error),
                        "saved_to_history": False
                    })
            
            successful_closes = len([r for r in results if r.get('success', False)])
            
            return {
                "success": True,
                "data": {
                    "message": f"Emergency stop completed: {successful_closes}/{len(active_positions)} positions closed",
                    "closed_positions": results,
                    "total_closed": successful_closes,
                    "total_attempted": len(active_positions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return {
                "success": False,
                "error": f"Failed during emergency stop: {str(e)}"
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
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        settings_service.update_settings('default', update_data)
        
        # Also update trader for immediate effect
        trader = initialize_global_trader()
        if config.max_position_size is not None:
            trader.max_position_size = config.max_position_size
        
        if config.max_daily_trades is not None:
            trader.max_daily_trades = config.max_daily_trades
        
        if config.daily_loss_limit is not None:
            trader.daily_loss_limit = config.daily_loss_limit
        
        # Get current settings from database
        current_settings = settings_service.get_risk_management_settings()
        
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
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        risk_settings = settings_service.get_risk_management_settings()
        position_settings = settings_service.get_position_size_settings()
        
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
        
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        settings_service.update_position_size_settings(update_data)
        
        # Also update trader for immediate effect
        trader = initialize_global_trader()
        trader.set_position_size_config(
            mode=config.mode,
            amount=config.fixed_amount_usd,
            max_percentage=config.max_percentage
        )
        
        # Get updated settings from database
        updated_settings = settings_service.get_position_size_settings()
        
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
        # Get settings from database using sync session
        db = next(get_sync_db())
        settings_service = get_trading_settings_service(db)
        position_settings = settings_service.get_position_size_settings()
        
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
                    "testnet": trader.testnet
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
async def emergency_stop(db: AsyncSession = Depends(get_db)):
    """Emergency stop - close all positions and disable trading"""
    try:
        # Use the close_all_positions function which now saves to history
        result = await close_all_positions("emergency_stop", db)
        
        if result["success"]:
            # Set daily trades to maximum to prevent new trades
            trader = initialize_global_trader()
            trader.daily_trades = trader.max_daily_trades
            
            return {
                "success": True,
                "data": {
                    "message": "Emergency stop executed - all positions closed and saved to history",
                    "closed_positions": result["data"]["total_closed"],
                    "trading_disabled": True,
                    "details": result["data"]
                }
            }
        else:
            return result
        
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
    """Get wallet balance from Binance API"""
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
        
        # Calculate real balance with live prices
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


@router.get("/history")
async def get_trading_history(
    db: AsyncSession = Depends(get_db),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    trade_result: Optional[str] = Query(None, description="Filter by result: profit, loss, failed_order, pending"),
    testnet_mode: Optional[bool] = Query(None, description="Filter by testnet mode"),
    limit: int = Query(100, description="Maximum number of records")
):
    """Get trading history with detailed order results"""
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include full day
        
        # Get trading history from database (using signals + performance)
        history_data = await DatabaseService.get_trading_history(
            db=db,
            symbol=symbol,
            start_date=start_datetime,
            end_date=end_datetime,
            trade_result=trade_result,
            testnet_mode=testnet_mode,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "trades": history_data,
                "count": len(history_data),
                "filters": {
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "trade_result": trade_result,
                    "testnet_mode": testnet_mode,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/statistics")
async def get_trading_history_statistics(
    db: AsyncSession = Depends(get_db),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    days: int = Query(30, description="Number of days to analyze"),
    testnet_mode: Optional[bool] = Query(None, description="Filter by testnet mode")
):
    """Get trading statistics from history"""
    try:
        stats = await DatabaseService.get_trading_statistics(
            db=db,
            symbol=symbol,
            days=days,
            testnet_mode=testnet_mode
        )
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/daily-summary")
async def get_daily_trading_summary(
    db: AsyncSession = Depends(get_db),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    testnet_mode: Optional[bool] = Query(None, description="Filter by testnet mode")
):
    """Get daily trading summary"""
    try:
        # Parse date or use today
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_of_day = target_date
        end_of_day = target_date + timedelta(days=1)
        
        # Get trades for the day
        daily_trades_data = await DatabaseService.get_trading_history(
            db=db,
            start_date=start_of_day,
            end_date=end_of_day,
            testnet_mode=testnet_mode,
            limit=1000
        )
        
        # Calculate summary
        total_trades = len(daily_trades_data)
        successful_trades = len([t for t in daily_trades_data if t.get('trade_result') == 'profit'])
        failed_trades = len([t for t in daily_trades_data if t.get('trade_result') == 'loss'])
        failed_orders = len([t for t in daily_trades_data if t.get('trade_result') == 'failed_order'])
        pending_trades = len([t for t in daily_trades_data if t.get('trade_result') == 'pending'])
        
        total_pnl = sum([float(t.get('profit_loss_usd', 0)) for t in daily_trades_data if t.get('profit_loss_usd')])
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Group by symbol
        symbol_summary = {}
        for trade in daily_trades_data:
            symbol = trade.get('symbol')
            if symbol not in symbol_summary:
                symbol_summary[symbol] = {
                    'trades': 0,
                    'profit_trades': 0,
                    'loss_trades': 0,
                    'failed_orders': 0,
                    'total_pnl': 0
                }
            
            symbol_summary[symbol]['trades'] += 1
            if trade.get('trade_result') == 'profit':
                symbol_summary[symbol]['profit_trades'] += 1
            elif trade.get('trade_result') == 'loss':
                symbol_summary[symbol]['loss_trades'] += 1
            elif trade.get('trade_result') == 'failed_order':
                symbol_summary[symbol]['failed_orders'] += 1
            
            if trade.get('profit_loss_usd'):
                symbol_summary[symbol]['total_pnl'] += float(trade.get('profit_loss_usd', 0))
        
        return {
            "success": True,
            "data": {
                "date": target_date.strftime("%Y-%m-%d"),
                "summary": {
                    "total_trades": total_trades,
                    "successful_trades": successful_trades,
                    "failed_trades": failed_trades,
                    "failed_orders": failed_orders,
                    "pending_trades": pending_trades,
                    "win_rate": round(win_rate, 2),
                    "total_pnl_usd": round(total_pnl, 2)
                },
                "by_symbol": symbol_summary,
                "trades": daily_trades_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RefreshOrderRequest(BaseModel):
    order_id: str
    symbol: str


@router.post("/refresh-order-status")
async def refresh_order_status(request: RefreshOrderRequest):
    """Refresh order status from Binance API and update database"""
    try:
        trader = initialize_global_trader()
        result = await trader.refresh_order_status(request.order_id, request.symbol)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-all-pending-orders")
async def refresh_all_pending_orders(db: AsyncSession = Depends(get_db)):
    """Refresh status of all pending orders from database"""
    try:
        trader = initialize_global_trader()
        
        # Get all pending trading performances with order IDs
        pending_performances = await DatabaseService.get_pending_trading_performances(db)
        
        refresh_results = []
        for performance in pending_performances:
            if performance.main_order_id and performance.signal:
                try:
                    symbol = performance.signal.symbol
                    order_id = performance.main_order_id
                    
                    # Refresh order status from Binance
                    refresh_result = await trader.refresh_order_status(order_id, symbol)
                    
                    refresh_results.append({
                        "order_id": order_id,
                        "symbol": symbol,
                        "success": refresh_result.get('success', False),
                        "status": refresh_result.get('status'),
                        "error": refresh_result.get('error')
                    })
                    
                except Exception as e:
                    refresh_results.append({
                        "order_id": performance.main_order_id,
                        "symbol": performance.signal.symbol if performance.signal else "unknown",
                        "success": False,
                        "error": str(e)
                    })
        
        successful_refreshes = len([r for r in refresh_results if r['success']])
        
        return {
            "success": True,
            "data": {
                "total_orders_checked": len(refresh_results),
                "successful_refreshes": successful_refreshes,
                "failed_refreshes": len(refresh_results) - successful_refreshes,
                "results": refresh_results
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-status/{order_id}")
async def get_order_status(order_id: str, symbol: str = Query(..., description="Trading symbol")):
    """Get current order status from Binance API"""
    try:
        trader = initialize_global_trader()
        result = await trader.get_order_status(symbol, order_id)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-positions")
async def get_live_positions():
    """Get live positions from Binance API with stop loss and take profit prices"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        live_positions = []
        
        if trader.use_futures:
            # Get Futures positions from Binance
            try:
                positions = trader.client.futures_position_information()
                
                # Get current prices for all symbols to ensure fresh data
                price_cache = {}
                
                # Filter only active positions (non-zero position amount)
                for pos in positions:
                    position_amt = float(pos.get('positionAmt', 0))
                    if position_amt != 0:
                        symbol = pos.get('symbol')
                        entry_price = float(pos.get('entryPrice', 0))
                        
                        # Get fresh mark price from API instead of relying on position data
                        if symbol not in price_cache:
                            try:
                                ticker = trader.client.futures_symbol_ticker(symbol=symbol)
                                price_cache[symbol] = float(ticker['price'])
                            except:
                                price_cache[symbol] = float(pos.get('markPrice', 0))
                        
                        current_price = price_cache[symbol]
                        # USE BINANCE CALCULATED P&L - this is always accurate
                        unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                        
                        # Calculate percentage based on Binance P&L for accuracy
                        if abs(position_amt) > 0 and entry_price > 0:
                            position_value = abs(position_amt) * entry_price
                            pnl_percentage = (unrealized_pnl / position_value) * 100
                        else:
                            pnl_percentage = 0.0
                        
                        # Get open orders for this symbol to find stop loss and take profit
                        stop_loss_price = None
                        take_profit_price = None
                        
                        try:
                            open_orders = trader.client.futures_get_open_orders(symbol=symbol)
                            logger.info(f"Found {len(open_orders)} open orders for {symbol}")
                            
                            for order in open_orders:
                                order_type = order.get('type', '')
                                stop_price = float(order.get('stopPrice', 0)) if order.get('stopPrice') else None
                                price = float(order.get('price', 0)) if order.get('price') else None
                                side = order.get('side', '')
                                
                                logger.info(f"Order: type={order_type}, side={side}, stopPrice={stop_price}, price={price}")
                                
                                # Check for stop loss orders (STOP_MARKET, STOP, STOP_LOSS_LIMIT)
                                if order_type in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT'] and (stop_price or price):
                                    trigger_price = stop_price or price
                                    # For LONG positions, stop loss is SELL order below entry price
                                    # For SHORT positions, stop loss is BUY order above entry price
                                    if position_amt > 0 and side == 'SELL' and trigger_price < entry_price:  # LONG stop loss
                                        stop_loss_price = trigger_price
                                        logger.info(f"Found LONG stop loss: {trigger_price}")
                                    elif position_amt < 0 and side == 'BUY' and trigger_price > entry_price:  # SHORT stop loss
                                        stop_loss_price = trigger_price
                                        logger.info(f"Found SHORT stop loss: {trigger_price}")
                                
                                # Check for take profit orders (TAKE_PROFIT_MARKET, TAKE_PROFIT, LIMIT)
                                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT'] and (stop_price or price):
                                    trigger_price = stop_price or price
                                    # For LONG positions, take profit is SELL order above entry price
                                    # For SHORT positions, take profit is BUY order below entry price
                                    if position_amt > 0 and side == 'SELL' and trigger_price > entry_price:  # LONG take profit
                                        take_profit_price = trigger_price
                                        logger.info(f"Found LONG take profit: {trigger_price}")
                                    elif position_amt < 0 and side == 'BUY' and trigger_price < entry_price:  # SHORT take profit
                                        take_profit_price = trigger_price
                                        logger.info(f"Found SHORT take profit: {trigger_price}")
                                
                        except Exception as order_error:
                            logger.warning(f"Could not get open orders for {symbol}: {order_error}")
                        
                        live_positions.append({
                            'symbol': symbol,
                            'position_side': 'BUY' if position_amt > 0 else 'SELL',
                            'position_amt': abs(position_amt),
                            'entry_price': entry_price,
                            'mark_price': current_price,
                            'unrealized_pnl': unrealized_pnl,
                            'pnl_percentage': pnl_percentage,
                            'stop_loss_price': stop_loss_price,
                            'take_profit_price': take_profit_price,
                            'position_type': 'FUTURES',
                            'leverage': float(pos.get('leverage', 1)),
                            'margin_type': pos.get('marginType', 'cross'),
                            'update_time': pos.get('updateTime')
                        })
                
                # Sort positions by update_time (newest first) - represents position creation/modification time
                def safe_sort_key(pos):
                    update_time = pos.get('update_time', 0)
                    if update_time is None:
                        return 0
                    try:
                        return -int(update_time)
                    except (ValueError, TypeError):
                        return 0
                
                live_positions.sort(key=safe_sort_key)
                        
            except Exception as e:
                logger.error(f"Error getting Futures positions: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get Futures positions: {str(e)}"
                }
        else:
            # For Spot trading, we would need to track positions differently
            # Since Spot doesn't have "positions" in the same way as Futures
            pass
        
        return {
            "success": True,
            "data": {
                "positions": live_positions,
                "count": len(live_positions),
                "account_type": "FUTURES" if trader.use_futures else "SPOT",
                "testnet": trader.testnet
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-positions/pnl-only")
async def get_live_positions_pnl_only():
    """Get only P&L data and exit prices for live positions with fresh Binance data"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        pnl_updates = []
        
        if trader.use_futures:
            try:
                # OPTIMIZATION 1: Get all active positions in one call
                positions = trader.client.futures_position_information()
                active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]
                
                if not active_positions:
                    return {
                        "success": True,
                        "data": {
                            "pnl_updates": [],
                            "count": 0,
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                
                # OPTIMIZATION 2: Get all prices in one batch call
                active_symbols = [pos.get('symbol') for pos in active_positions]
                try:
                    # Get all ticker prices in one call
                    all_tickers = trader.client.futures_symbol_ticker()
                    price_map = {ticker['symbol']: float(ticker['price']) for ticker in all_tickers}
                except:
                    # Fallback to individual calls if batch fails
                    price_map = {}
                    for symbol in active_symbols:
                        try:
                            ticker = trader.client.futures_symbol_ticker(symbol=symbol)
                            price_map[symbol] = float(ticker['price'])
                        except:
                            price_map[symbol] = 0
                
                # OPTIMIZATION 3: Get all open orders in one call
                try:
                    all_open_orders = trader.client.futures_get_open_orders()
                    orders_by_symbol = {}
                    for order in all_open_orders:
                        symbol = order.get('symbol')
                        if symbol not in orders_by_symbol:
                            orders_by_symbol[symbol] = []
                        orders_by_symbol[symbol].append(order)
                except:
                    orders_by_symbol = {}
                
                # Process each active position
                for pos in active_positions:
                    position_amt = float(pos.get('positionAmt', 0))
                    symbol = pos.get('symbol')
                    entry_price = float(pos.get('entryPrice', 0))
                    
                    # Use cached price or fallback to position mark price
                    current_price = price_map.get(symbol, float(pos.get('markPrice', 0)))
                    # USE BINANCE CALCULATED P&L - this is always accurate
                    unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                    
                    # Calculate percentage based on Binance P&L for accuracy
                    if abs(position_amt) > 0 and entry_price > 0:
                        position_value = abs(position_amt) * entry_price
                        pnl_percentage = (unrealized_pnl / position_value) * 100
                    else:
                        pnl_percentage = 0.0
                    
                    # Get stop loss and take profit from cached orders
                    stop_loss_price = None
                    take_profit_price = None
                    
                    symbol_orders = orders_by_symbol.get(symbol, [])
                    for order in symbol_orders:
                        order_type = order.get('type', '')
                        stop_price = float(order.get('stopPrice', 0)) if order.get('stopPrice') else None
                        price = float(order.get('price', 0)) if order.get('price') else None
                        side = order.get('side', '')
                        
                        # Check for stop loss orders
                        if order_type in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT'] and (stop_price or price):
                            trigger_price = stop_price or price
                            # For LONG positions, stop loss is SELL order below entry price
                            # For SHORT positions, stop loss is BUY order above entry price
                            if position_amt > 0 and side == 'SELL' and trigger_price < entry_price:  # LONG stop loss
                                stop_loss_price = trigger_price
                            elif position_amt < 0 and side == 'BUY' and trigger_price > entry_price:  # SHORT stop loss
                                stop_loss_price = trigger_price
                        
                        # Check for take profit orders
                        elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT'] and (stop_price or price):
                            trigger_price = stop_price or price
                            # For LONG positions, take profit is SELL order above entry price
                            # For SHORT positions, take profit is BUY order below entry price
                            if position_amt > 0 and side == 'SELL' and trigger_price > entry_price:  # LONG take profit
                                take_profit_price = trigger_price
                            elif position_amt < 0 and side == 'BUY' and trigger_price < entry_price:  # SHORT take profit
                                take_profit_price = trigger_price
                    
                    pnl_updates.append({
                        'symbol': symbol,
                        'mark_price': current_price,
                        'unrealized_pnl': unrealized_pnl,
                        'pnl_percentage': pnl_percentage,
                        'stop_loss_price': stop_loss_price,
                        'take_profit_price': take_profit_price,
                        'update_time': int(time.time() * 1000)
                    })
                
                # Sort P&L updates by symbol to maintain consistent order
                pnl_updates.sort(key=lambda x: x.get('symbol', ''))
                        
            except Exception as e:
                logger.error(f"Error getting Futures P&L data: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get Futures P&L data: {str(e)}"
                }
        
        return {
            "success": True,
            "data": {
                "pnl_updates": pnl_updates,
                "count": len(pnl_updates),
                "timestamp": int(time.time() * 1000)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-orders")
async def get_open_orders(symbol: Optional[str] = Query(None, description="Filter by symbol")):
    """Get all open orders from Binance API"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        all_orders = []
        
        if trader.use_futures:
            try:
                if symbol:
                    # Get orders for specific symbol
                    orders = trader.client.futures_get_open_orders(symbol=symbol)
                else:
                    # Get all open orders
                    orders = trader.client.futures_get_open_orders()
                
                for order in orders:
                    formatted_order = {
                        'symbol': order.get('symbol'),
                        'order_id': order.get('orderId'),
                        'side': order.get('side'),
                        'type': order.get('type'),
                        'status': order.get('status'),
                        'price': float(order.get('price', 0)) if order.get('price') else None,
                        'stop_price': float(order.get('stopPrice', 0)) if order.get('stopPrice') else None,
                        'original_qty': float(order.get('origQty', 0)),
                        'executed_qty': float(order.get('executedQty', 0)),
                        'time_in_force': order.get('timeInForce'),
                        'reduce_only': order.get('reduceOnly', False),
                        'close_position': order.get('closePosition', False),
                        'working_type': order.get('workingType'),
                        'price_protect': order.get('priceProtect', False),
                        'time': datetime.fromtimestamp(order.get('time', 0) / 1000) if order.get('time') else None,
                        'update_time': datetime.fromtimestamp(order.get('updateTime', 0) / 1000) if order.get('updateTime') else None
                    }
                    all_orders.append(formatted_order)
                    
            except Exception as e:
                logger.error(f"Error getting Futures open orders: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get Futures open orders: {str(e)}"
                }
        else:
            try:
                if symbol:
                    # Get orders for specific symbol
                    orders = trader.client.get_open_orders(symbol=symbol)
                else:
                    # Get all open orders
                    orders = trader.client.get_open_orders()
                
                for order in orders:
                    formatted_order = {
                        'symbol': order.get('symbol'),
                        'order_id': order.get('orderId'),
                        'side': order.get('side'),
                        'type': order.get('type'),
                        'status': order.get('status'),
                        'price': float(order.get('price', 0)) if order.get('price') else None,
                        'stop_price': float(order.get('stopPrice', 0)) if order.get('stopPrice') else None,
                        'original_qty': float(order.get('origQty', 0)),
                        'executed_qty': float(order.get('executedQty', 0)),
                        'time_in_force': order.get('timeInForce'),
                        'iceberg_qty': float(order.get('icebergQty', 0)) if order.get('icebergQty') else None,
                        'time': datetime.fromtimestamp(order.get('time', 0) / 1000) if order.get('time') else None,
                        'update_time': datetime.fromtimestamp(order.get('updateTime', 0) / 1000) if order.get('updateTime') else None,
                        'is_working': order.get('isWorking', False)
                    }
                    all_orders.append(formatted_order)
                    
            except Exception as e:
                logger.error(f"Error getting Spot open orders: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get Spot open orders: {str(e)}"
                }
        
        return {
            "success": True,
            "data": {
                "orders": all_orders,
                "count": len(all_orders),
                "account_type": "FUTURES" if trader.use_futures else "SPOT",
                "testnet": trader.testnet
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-position-by-symbol")
async def close_position_by_symbol(symbol: str, reason: str = "manual_close", db: AsyncSession = Depends(get_db)):
    """Close position by symbol (for Futures trading) and save to history"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        if not trader.use_futures:
            return {
                "success": False,
                "error": "Position closing by symbol is only supported for Futures trading"
            }
        
        # Get current position for the symbol
        try:
            positions = trader.client.futures_position_information(symbol=symbol)
            active_position = None
            
            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    active_position = pos
                    break
            
            if not active_position:
                return {
                    "success": False,
                    "error": f"No active position found for {symbol}"
                }
            
            position_amt = float(active_position.get('positionAmt', 0))
            entry_price = float(active_position.get('entryPrice', 0))
            
            # Get current market price for P&L calculation
            try:
                current_price = await trader._get_current_price(symbol)
            except:
                current_price = entry_price  # Fallback
            
            # Determine order side (opposite of position)
            if position_amt > 0:
                # LONG position -> SELL to close
                side = 'SELL'
                quantity = abs(position_amt)
                position_side = 'BUY'  # Original position was BUY
            else:
                # SHORT position -> BUY to close
                side = 'BUY'
                quantity = abs(position_amt)
                position_side = 'SELL'  # Original position was SELL
            
            # Calculate P&L before closing
            # Safe P&L calculation with None checks
            if current_price is not None and entry_price is not None:
                if position_amt > 0:  # LONG position
                    pnl = quantity * (current_price - entry_price)
                else:  # SHORT position
                    pnl = quantity * (entry_price - current_price)
            else:
                pnl = 0.0  # Default to 0 if prices are None
            
            # Calculate P&L percentage
            if quantity > 0 and entry_price > 0:
                pnl_percentage = (pnl / (quantity * entry_price)) * 100
            else:
                pnl_percentage = 0.0
            
            # Place market order to close position
            order_result = trader.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=True  # This ensures we're closing, not opening new position
            )
            
            # Get actual exit price from order result
            exit_price = current_price
            if order_result.get('avgPrice'):
                exit_price = float(order_result.get('avgPrice'))
            elif order_result.get('price'):
                exit_price = float(order_result.get('price'))
            
            # Recalculate P&L with actual exit price
            # Safe final P&L calculation with None checks
            if exit_price is not None and entry_price is not None:
                if position_amt > 0:  # LONG position
                    final_pnl = quantity * (exit_price - entry_price)
                else:  # SHORT position
                    final_pnl = quantity * (entry_price - exit_price)
            else:
                final_pnl = 0.0  # Default to 0 if prices are None
            
            # Recalculate P&L percentage
            if quantity > 0 and entry_price > 0:
                final_pnl_percentage = (final_pnl / (quantity * entry_price)) * 100
            else:
                final_pnl_percentage = 0.0
            
            # Save closed position to database as a manual trade
            try:
                # Create a synthetic signal for the closed position
                synthetic_signal = {
                    'symbol': symbol,
                    'signal': position_side,  # BUY or SELL (original position direction)
                    'price': entry_price,
                    'entry_price': entry_price,
                    'stop_loss': None,
                    'take_profit': None,
                    'confidence': 100,  # Manual close, so 100% confidence
                    'timestamp': datetime.now(),
                    'signal_type': position_side,
                    'source': 'manual_close',
                    'decision_factors': f'Manual position close via UI - {reason}'
                }
                
                # Save synthetic signal to database
                saved_signal = await DatabaseService.save_signal(db, synthetic_signal)
                
                # Save trading performance for the closed position
                trade_data = {
                    "quantity": quantity,
                    "position_size_usd": quantity * entry_price,
                    "main_order_id": str(order_result.get('orderId')),
                    "exit_price": exit_price,
                    "exit_time": datetime.now(),
                    "profit_loss": final_pnl,
                    "profit_percentage": final_pnl_percentage,
                    "result": "profit" if final_pnl > 0 else "loss" if final_pnl < 0 else "breakeven",
                    "testnet_mode": trader.testnet,
                    "close_reason": reason
                }
                
                await DatabaseService.save_trading_performance(db, saved_signal.id, trade_data)
                logger.info(f"✅ Closed position saved to history: {symbol} - {trade_data['result']} - ${final_pnl:.2f}")
                
            except Exception as db_error:
                logger.error(f"Error saving closed position to database: {db_error}")
                # Don't fail the entire operation if database save fails
            
            return {
                "success": True,
                "data": {
                    "message": f"Position for {symbol} closed successfully",
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": final_pnl,
                    "pnl_percentage": final_pnl_percentage,
                    "order_id": order_result.get('orderId'),
                    "reason": reason,
                    "saved_to_history": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return {
                "success": False,
                "error": f"Failed to close position for {symbol}: {str(e)}"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-position/{symbol}")
async def debug_position_orders(symbol: str):
    """Debug endpoint to check position and orders for a specific symbol"""
    try:
        trader = initialize_global_trader()
        
        if not trader.client:
            return {
                "success": False,
                "error": "Binance API client not initialized"
            }
        
        debug_info = {
            "symbol": symbol,
            "position_info": None,
            "open_orders": [],
            "all_orders_last_24h": [],
            "analysis": {}
        }
        
        if trader.use_futures:
            # Get position info
            try:
                positions = trader.client.futures_position_information(symbol=symbol)
                for pos in positions:
                    position_amt = float(pos.get('positionAmt', 0))
                    if position_amt != 0:
                        debug_info["position_info"] = {
                            "symbol": pos.get('symbol'),
                            "positionAmt": position_amt,
                            "entryPrice": float(pos.get('entryPrice', 0)),
                            "markPrice": float(pos.get('markPrice', 0)),
                            "unRealizedProfit": float(pos.get('unRealizedProfit', 0)),
                            "leverage": float(pos.get('leverage', 1)),
                            "marginType": pos.get('marginType'),
                            "updateTime": pos.get('updateTime')
                        }
                        break
            except Exception as e:
                debug_info["position_error"] = str(e)
            
            # Get open orders
            try:
                open_orders = trader.client.futures_get_open_orders(symbol=symbol)
                debug_info["open_orders"] = []
                for order in open_orders:
                    debug_info["open_orders"].append({
                        "orderId": order.get('orderId'),
                        "symbol": order.get('symbol'),
                        "side": order.get('side'),
                        "type": order.get('type'),
                        "status": order.get('status'),
                        "price": float(order.get('price', 0)) if order.get('price') else None,
                        "stopPrice": float(order.get('stopPrice', 0)) if order.get('stopPrice') else None,
                        "origQty": float(order.get('origQty', 0)),
                        "executedQty": float(order.get('executedQty', 0)),
                        "reduceOnly": order.get('reduceOnly', False),
                        "timeInForce": order.get('timeInForce'),
                        "workingType": order.get('workingType'),
                        "time": order.get('time'),
                        "updateTime": order.get('updateTime')
                    })
            except Exception as e:
                debug_info["open_orders_error"] = str(e)
            
            # Get recent orders (last 24h)
            try:
                from datetime import datetime, timedelta
                start_time = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
                all_orders = trader.client.futures_get_all_orders(symbol=symbol, startTime=start_time, limit=50)
                debug_info["all_orders_last_24h"] = []
                for order in all_orders[-10:]:  # Last 10 orders
                    debug_info["all_orders_last_24h"].append({
                        "orderId": order.get('orderId'),
                        "side": order.get('side'),
                        "type": order.get('type'),
                        "status": order.get('status'),
                        "price": float(order.get('price', 0)) if order.get('price') else None,
                        "stopPrice": float(order.get('stopPrice', 0)) if order.get('stopPrice') else None,
                        "origQty": float(order.get('origQty', 0)),
                        "executedQty": float(order.get('executedQty', 0)),
                        "reduceOnly": order.get('reduceOnly', False),
                        "time": datetime.fromtimestamp(order.get('time', 0) / 1000).isoformat() if order.get('time') else None,
                        "updateTime": datetime.fromtimestamp(order.get('updateTime', 0) / 1000).isoformat() if order.get('updateTime') else None
                    })
            except Exception as e:
                debug_info["all_orders_error"] = str(e)
        
        # Analysis
        if debug_info["position_info"] and debug_info["open_orders"]:
            position_amt = debug_info["position_info"]["positionAmt"]
            entry_price = debug_info["position_info"]["entryPrice"]
            
            stop_loss_candidates = []
            take_profit_candidates = []
            
            for order in debug_info["open_orders"]:
                order_type = order["type"]
                side = order["side"]
                stop_price = order["stopPrice"]
                price = order["price"]
                trigger_price = stop_price or price
                
                if not trigger_price:
                    continue
                
                # Check for stop loss orders
                if order_type in ['STOP_MARKET', 'STOP', 'STOP_LOSS_LIMIT']:
                    if position_amt > 0 and side == 'SELL' and trigger_price < entry_price:  # LONG stop loss
                        stop_loss_candidates.append({
                            "orderId": order["orderId"],
                            "type": order_type,
                            "side": side,
                            "trigger_price": trigger_price,
                            "reason": "LONG stop loss (SELL below entry)"
                        })
                    elif position_amt < 0 and side == 'BUY' and trigger_price > entry_price:  # SHORT stop loss
                        stop_loss_candidates.append({
                            "orderId": order["orderId"],
                            "type": order_type,
                            "side": side,
                            "trigger_price": trigger_price,
                            "reason": "SHORT stop loss (BUY above entry)"
                        })
                
                # Check for take profit orders
                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT']:
                    if position_amt > 0 and side == 'SELL' and trigger_price > entry_price:  # LONG take profit
                        take_profit_candidates.append({
                            "orderId": order["orderId"],
                            "type": order_type,
                            "side": side,
                            "trigger_price": trigger_price,
                            "reason": "LONG take profit (SELL above entry)"
                        })
                    elif position_amt < 0 and side == 'BUY' and trigger_price < entry_price:  # SHORT take profit
                        take_profit_candidates.append({
                            "orderId": order["orderId"],
                            "type": order_type,
                            "side": side,
                            "trigger_price": trigger_price,
                            "reason": "SHORT take profit (BUY below entry)"
                        })
            
            debug_info["analysis"] = {
                "position_side": "LONG" if position_amt > 0 else "SHORT",
                "entry_price": entry_price,
                "stop_loss_candidates": stop_loss_candidates,
                "take_profit_candidates": take_profit_candidates,
                "stop_loss_found": len(stop_loss_candidates) > 0,
                "take_profit_found": len(take_profit_candidates) > 0
            }
        
        return {
            "success": True,
            "data": debug_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/refresh-table")
async def refresh_position_table():
    """Refresh the position table with current data"""
    try:
        from app.services.position_service import refresh_position_table
        result = await refresh_position_table()
        
        if result:
            return {
                "success": True,
                "message": "Position table refreshed successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to refresh position table"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/clear-all")
async def clear_all_trade_history(
    db: AsyncSession = Depends(get_db),
    testnet_only: bool = Query(True, description="Only delete testnet trades")
):
    """Clear all trade history (with safety option for testnet only)"""
    try:
        # Additional safety check - prevent accidental mainnet deletion
        if not testnet_only:
            logger.warning("⚠️ Attempting to delete ALL trading history (including mainnet)")
        
        deleted_count = await DatabaseService.clear_all_trading_history(db, testnet_only)
        
        environment = "testnet" if testnet_only else "all"
        logger.info(f"✅ Cleared {deleted_count} trades from {environment} history")
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} trades from {environment} history",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{trade_id}")
async def delete_trade_history(trade_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a specific trade from history"""
    try:
        # Delete the trading performance record
        deleted = await DatabaseService.delete_trading_performance(db, trade_id)
        
        if deleted:
            return {
                "success": True,
                "message": f"Trade {trade_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Trade {trade_id} not found"
            }
        
    except Exception as e:
        logger.error(f"Error deleting trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))