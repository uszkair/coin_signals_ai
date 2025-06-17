from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_sync_db
from app.models.database_models import TradingSettings
from app.services.trading_settings_service import TradingSettingsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/")
async def get_all_settings(
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Get all trading settings for a user"""
    try:
        settings_service = TradingSettingsService(db)
        settings = settings_service.get_settings(user_id)
        return settings.to_dict() if settings else {}
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update_all_settings(
    settings_data: Dict[str, Any],
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Update all trading settings for a user"""
    try:
        settings_service = TradingSettingsService(db)
        updated_settings = settings_service.update_settings(user_id, settings_data)
        return {"message": "Settings updated successfully", "settings": updated_settings.to_dict()}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_settings_category(
    category: str,
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Get specific category of settings"""
    try:
        settings_service = TradingSettingsService(db)
        settings = settings_service.get_settings(user_id)
        
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        settings_dict = settings.to_dict()
        
        # Map category names to database fields
        category_mapping = {
            "signal_generation": "technical_indicator_weights",
            "technical_analysis": ["rsi_settings", "macd_settings", "bollinger_settings", "ma_settings", "volume_settings", "candlestick_settings"],
            "ai_ml": "ai_ml_settings",
            "auto_trading": ["auto_trading_enabled", "monitored_symbols", "check_interval", "min_signal_confidence"],
            "risk_management": ["max_daily_trades", "daily_loss_limit", "position_size_mode", "max_position_size", "default_position_size_usd", "stop_loss_percentage", "take_profit_percentage", "use_atr_based_sl_tp", "atr_multiplier_sl", "atr_multiplier_tp"],
            "notifications": "notification_settings",
            "backtesting": "backtest_settings",
            "data_history": "data_history_settings",
            "advanced": "advanced_settings",
            "ui_ux": "ui_settings",
            "trading_environment": ["testnet_mode", "use_futures"]
        }
        
        if category not in category_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        fields = category_mapping[category]
        if isinstance(fields, str):
            fields = [fields]
        
        result = {}
        for field in fields:
            if field in settings_dict:
                result[field] = settings_dict[field]
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting settings category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/category/{category}")
async def update_settings_category(
    category: str,
    category_data: Dict[str, Any],
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Update specific category of settings"""
    try:
        settings_service = TradingSettingsService(db)
        
        # Map category names to database fields
        category_mapping = {
            "signal_generation": "technical_indicator_weights",
            "technical_analysis": ["rsi_settings", "macd_settings", "bollinger_settings", "ma_settings", "volume_settings", "candlestick_settings"],
            "ai_ml": "ai_ml_settings",
            "auto_trading": ["auto_trading_enabled", "monitored_symbols", "check_interval", "min_signal_confidence"],
            "risk_management": ["max_daily_trades", "daily_loss_limit", "position_size_mode", "max_position_size", "default_position_size_usd", "stop_loss_percentage", "take_profit_percentage", "use_atr_based_sl_tp", "atr_multiplier_sl", "atr_multiplier_tp"],
            "notifications": "notification_settings",
            "backtesting": "backtest_settings",
            "data_history": "data_history_settings",
            "advanced": "advanced_settings",
            "ui_ux": "ui_settings",
            "trading_environment": ["testnet_mode", "use_futures"]
        }
        
        if category not in category_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        # Update only the fields for this category
        updated_settings = settings_service.update_settings(user_id, category_data)
        return {"message": f"Category {category} updated successfully", "settings": updated_settings.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_settings_to_defaults(
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Reset all settings to default values"""
    try:
        settings_service = TradingSettingsService(db)
        
        # Delete existing settings to trigger default values
        existing_settings = settings_service.get_settings(user_id)
        if existing_settings:
            db.delete(existing_settings)
            db.commit()
        
        # Create new settings with defaults
        new_settings = settings_service.get_settings(user_id)
        return {"message": "Settings reset to defaults", "settings": new_settings.to_dict()}
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/defaults")
async def get_default_settings():
    """Get default settings values"""
    try:
        # Return the default values as defined in the model
        defaults = {
            "auto_trading_enabled": True,
            "monitored_symbols": ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
            "check_interval": 300,
            "min_signal_confidence": 70,
            "position_size_mode": 'percentage',
            "max_position_size": 0.02,
            "default_position_size_usd": None,
            "max_daily_trades": 10,
            "daily_loss_limit": 0.05,
            "stop_loss_percentage": 0.02,
            "take_profit_percentage": 0.04,
            "use_atr_based_sl_tp": False,
            "atr_multiplier_sl": 1.0,
            "atr_multiplier_tp": 2.0,
            "testnet_mode": True,
            "use_futures": True,
            "technical_indicator_weights": {
                'rsi_weight': 1.0,
                'macd_weight': 1.0,
                'volume_weight': 1.0,
                'candlestick_weight': 2.0,
                'bollinger_weight': 1.0,
                'ma_weight': 1.0
            },
            "rsi_settings": {
                'period': 14,
                'overbought': 70,
                'oversold': 30
            },
            "macd_settings": {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            "bollinger_settings": {
                'period': 20,
                'deviation': 2.0
            },
            "ma_settings": {
                'short_ma': 20,
                'long_ma': 50,
                'ma_type': 'EMA'
            },
            "volume_settings": {
                'volume_threshold_multiplier': 1.5,
                'high_volume_threshold': 2.0
            },
            "candlestick_settings": {
                'sensitivity': 'medium',
                'min_pattern_score': 0.7
            },
            "ai_ml_settings": {
                'ai_signal_weight': 2.0,
                'ai_confidence_threshold': 60.0,
                'ml_models': {
                    'lstm_enabled': True,
                    'random_forest_enabled': True,
                    'gradient_boosting_enabled': True
                },
                'market_regime_detection': True,
                'sentiment_analysis': False,
                'ensemble_method': 'weighted'
            },
            "notification_settings": {
                'signal_notifications': {
                    'enabled': True,
                    'email': False,
                    'push': True,
                    'in_app': True,
                    'min_confidence': 70
                },
                'trade_notifications': {
                    'enabled': True,
                    'execution_alerts': True,
                    'profit_loss_alerts': True,
                    'risk_alerts': True
                },
                'system_notifications': {
                    'enabled': True,
                    'connection_issues': True,
                    'error_alerts': True,
                    'maintenance_alerts': False
                }
            },
            "backtest_settings": {
                'default_period_days': 30,
                'default_symbols': ['BTCUSDT', 'ETHUSDT'],
                'commission_rate': 0.001,
                'slippage_bps': 5,
                'initial_capital': 10000,
                'benchmark_symbol': 'BTCUSDT'
            },
            "data_history_settings": {
                'retention_period_days': 90,
                'auto_cleanup': True,
                'export_format': 'JSON',
                'performance_tracking_period': 30,
                'max_signals_stored': 1000
            },
            "advanced_settings": {
                'api_rate_limit': 1200,
                'retry_attempts': 3,
                'request_timeout': 30,
                'cache_duration': 300,
                'logging_level': 'INFO',
                'webhook_urls': []
            },
            "ui_settings": {
                'dashboard_refresh_rate': 30,
                'chart_default_timeframe': '1h',
                'table_rows_per_page': 25,
                'theme': 'light',
                'language': 'hu',
                'decimal_places': 6
            }
        }
        return defaults
    except Exception as e:
        logger.error(f"Error getting default settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop-loss-take-profit")
async def get_stop_loss_take_profit_settings(
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Get stop loss and take profit settings"""
    try:
        settings_service = TradingSettingsService(db)
        sl_tp_settings = settings_service.get_stop_loss_take_profit_settings(user_id)
        return {"success": True, "data": sl_tp_settings}
    except Exception as e:
        logger.error(f"Error getting stop loss/take profit settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stop-loss-take-profit")
async def update_stop_loss_take_profit_settings(
    settings_data: Dict[str, Any],
    user_id: str = "default",
    db: Session = Depends(get_sync_db)
):
    """Update stop loss and take profit settings"""
    try:
        settings_service = TradingSettingsService(db)
        updated_settings = settings_service.update_stop_loss_take_profit_settings(settings_data, user_id)
        return {
            "success": True,
            "message": "Stop loss/take profit settings updated successfully",
            "data": settings_service.get_stop_loss_take_profit_settings(user_id)
        }
    except Exception as e:
        logger.error(f"Error updating stop loss/take profit settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))