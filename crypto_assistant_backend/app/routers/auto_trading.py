"""
Auto Trading API Router
Endpoints for automatic trading control and monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.auto_trading_scheduler import (
    auto_trading_scheduler,
    enable_auto_trading,
    disable_auto_trading,
    get_auto_trading_status,
    update_auto_trading_settings
)

router = APIRouter(prefix="/api/auto-trading", tags=["auto-trading"])


class AutoTradingSettings(BaseModel):
    symbols: List[str] = None
    interval: int = None  # seconds
    min_confidence: int = None


@router.get("/status")
async def get_status():
    """Get current auto-trading status"""
    try:
        status = await get_auto_trading_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable")
async def enable():
    """Enable automatic trading"""
    try:
        await enable_auto_trading()
        return {
            "success": True,
            "message": "Auto-trading enabled",
            "data": await get_auto_trading_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable")
async def disable():
    """Disable automatic trading"""
    try:
        await disable_auto_trading()
        return {
            "success": True,
            "message": "Auto-trading disabled",
            "data": await get_auto_trading_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_settings(settings: AutoTradingSettings):
    """Update auto-trading settings"""
    try:
        settings_dict = {}
        
        if settings.symbols is not None:
            settings_dict['symbols'] = settings.symbols
        
        if settings.interval is not None:
            settings_dict['interval'] = settings.interval
        
        if settings.min_confidence is not None:
            settings_dict['min_confidence'] = settings.min_confidence
        
        await update_auto_trading_settings(settings_dict)
        
        return {
            "success": True,
            "message": "Auto-trading settings updated",
            "data": await get_auto_trading_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_settings():
    """Get current auto-trading settings"""
    try:
        status = await get_auto_trading_status()
        return {
            "success": True,
            "data": {
                "symbols": status["monitored_symbols"],
                "interval": status["check_interval"],
                "min_confidence": status["min_signal_confidence"],
                "enabled": status["auto_trading_enabled"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_auto_trading_history():
    """Get auto-trading execution history"""
    try:
        # Get last signals from scheduler
        last_signals = auto_trading_scheduler.last_signals
        
        history = []
        for symbol, signal_data in last_signals.items():
            history.append({
                "symbol": symbol,
                "signal": signal_data["signal"]["signal"],
                "confidence": signal_data["signal"]["confidence"],
                "entry_price": signal_data["signal"]["entry_price"],
                "timestamp": signal_data["timestamp"].isoformat(),
                "result": signal_data["result"]
            })
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "history": history,
                "count": len(history)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop - disable auto-trading and close all positions (scheduler keeps running)"""
    try:
        # Disable auto-trading (scheduler continues monitoring but won't execute trades)
        await disable_auto_trading()
        
        # Close all positions (import from trading router)
        from app.services.binance_trading import initialize_global_trader, close_trading_position
        
        trader = initialize_global_trader()
        positions = await trader.get_active_positions()
        closed_positions = []
        
        for position_id in positions.keys():
            result = await close_trading_position(position_id, "emergency_auto_stop")
            closed_positions.append(result)
        
        return {
            "success": True,
            "message": "Emergency stop executed - auto-trading disabled and all positions closed (scheduler continues monitoring)",
            "data": {
                "auto_trading_disabled": True,
                "scheduler_running": True,
                "closed_positions": len(closed_positions),
                "status": await get_auto_trading_status()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics():
    """Get auto-trading performance metrics"""
    try:
        from app.services.binance_trading import initialize_global_trader
        
        # Get trading statistics
        trader = initialize_global_trader()
        stats = await trader.get_trading_statistics()
        
        # Get auto-trading specific metrics
        status = await get_auto_trading_status()
        
        return {
            "success": True,
            "data": {
                "auto_trading_status": status,
                "trading_statistics": stats,
                "performance_summary": {
                    "total_auto_trades": len(auto_trading_scheduler.last_signals),
                    "daily_pnl": stats.get("daily_pnl", 0),
                    "daily_trades": stats.get("daily_trades", 0),
                    "active_positions": stats.get("active_positions_count", 0),
                    "risk_level": stats.get("risk_level", "UNKNOWN")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))