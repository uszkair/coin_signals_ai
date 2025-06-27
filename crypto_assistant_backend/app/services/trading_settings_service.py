"""
Trading Settings Service
Manages trading settings stored in database
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.database_models import TradingSettings

logger = logging.getLogger(__name__)


class TradingSettingsService:
    """Service for managing trading settings in database"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cached_settings = None
    
    def get_settings(self, user_id: str = "default") -> Optional[TradingSettings]:
        """Get trading settings from database"""
        try:
            # Try to get existing settings
            settings = self.db.query(TradingSettings).filter(
                TradingSettings.user_id == user_id
            ).first()
            
            # If no settings exist, create default ones
            if not settings:
                settings = TradingSettings(user_id=user_id)
                self.db.add(settings)
                self.db.commit()
                self.db.refresh(settings)
            
            return settings
        except Exception as e:
            logger.error(f"Error getting trading settings: {e}")
            self.db.rollback()
            return None
    
    def update_settings(self, user_id: str, settings_data: Dict[str, Any]) -> TradingSettings:
        """Update trading settings in database"""
        try:
            # Get or create settings
            settings = self.get_settings(user_id)
            if not settings:
                settings = TradingSettings(user_id=user_id)
                self.db.add(settings)
            
            # Update fields
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            self.db.commit()
            self.db.refresh(settings)
            logger.info(f"Trading settings updated for user {user_id}: {list(settings_data.keys())}")
            return settings
        except Exception as e:
            logger.error(f"Error updating trading settings: {e}")
            self.db.rollback()
            raise
    
    def get_risk_management_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get risk management settings"""
        settings = self.get_settings(user_id)
        if settings:
            return {
                'testnet_mode': getattr(settings, 'testnet_mode', True),
                'use_futures': getattr(settings, 'use_futures', False),
                'max_daily_trades': getattr(settings, 'max_daily_trades', 10),
                'daily_loss_limit': getattr(settings, 'daily_loss_limit', 0.05),
                'max_position_size': getattr(settings, 'max_position_size', 0.02),
                'stop_loss_percentage': getattr(settings, 'stop_loss_percentage', 0.02),
                'take_profit_percentage': getattr(settings, 'take_profit_percentage', 0.04),
                'use_atr_based_sl_tp': getattr(settings, 'use_atr_based_sl_tp', False),
                'atr_multiplier_sl': getattr(settings, 'atr_multiplier_sl', 1.0),
                'atr_multiplier_tp': getattr(settings, 'atr_multiplier_tp', 2.0)
            }
        return {
            'testnet_mode': True,
            'use_futures': False,
            'max_daily_trades': 10,
            'daily_loss_limit': 0.05,
            'max_position_size': 0.02,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.04,
            'use_atr_based_sl_tp': False,
            'atr_multiplier_sl': 1.0,
            'atr_multiplier_tp': 2.0
        }
    
    def update_risk_management_settings(self, settings_data: Dict[str, Any], user_id: str = "default"):
        """Update risk management settings"""
        return self.update_settings(user_id, settings_data)
    
    def get_auto_trading_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get auto trading settings"""
        settings = self.get_settings(user_id)
        if settings:
            return {
                'enabled': getattr(settings, 'auto_trading_enabled', False),
                'symbols': getattr(settings, 'monitored_symbols', ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']),
                'interval': getattr(settings, 'check_interval', 300),
                'min_confidence': getattr(settings, 'min_signal_confidence', 70),
                'max_position_size': float(getattr(settings, 'max_position_size', 2.0))
            }
        return {
            'enabled': True,
            'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'],
            'interval': 300,
            'min_confidence': 70,
            'max_position_size': 100.0
        }
    
    def update_auto_trading_settings(self, settings_data: Dict[str, Any], user_id: str = "default"):
        """Update auto trading settings"""
        # Map the settings to the correct database column names
        db_settings = {}
        
        if 'enabled' in settings_data:
            db_settings['auto_trading_enabled'] = settings_data['enabled']
        if 'symbols' in settings_data:
            db_settings['monitored_symbols'] = settings_data['symbols']
        if 'interval' in settings_data:
            db_settings['check_interval'] = settings_data['interval']
        if 'min_confidence' in settings_data:
            db_settings['min_signal_confidence'] = settings_data['min_confidence']
        
        return self.update_settings(user_id, db_settings)
    
    def get_position_size_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get position size settings"""
        settings = self.get_settings(user_id)
        if settings:
            return {
                'mode': getattr(settings, 'position_size_mode', 'percentage'),
                'max_position_size': float(getattr(settings, 'max_position_size', 0.02)),
                'default_position_size_usd': float(getattr(settings, 'default_position_size_usd', 0)) if getattr(settings, 'default_position_size_usd', None) else None
            }
        return {
            'mode': 'percentage',
            'max_position_size': 0.02,
            'default_position_size_usd': None
        }
    
    def update_position_size_settings(self, settings_data: Dict[str, Any], user_id: str = "default"):
        """Update position size settings"""
        # Map the settings to the correct database column names
        db_settings = {}
        
        if 'mode' in settings_data:
            db_settings['position_size_mode'] = settings_data['mode']
        if 'max_position_size' in settings_data:
            db_settings['max_position_size'] = settings_data['max_position_size']
        if 'default_position_size_usd' in settings_data:
            db_settings['default_position_size_usd'] = settings_data['default_position_size_usd']
        if 'fixed_amount_usd' in settings_data:  # Alternative name
            db_settings['default_position_size_usd'] = settings_data['fixed_amount_usd']
        if 'max_percentage' in settings_data:  # Convert percentage to decimal
            db_settings['max_position_size'] = settings_data['max_percentage'] / 100.0
        
        return self.update_settings(user_id, db_settings)
    
    def get_technical_indicator_weights(self, user_id: str = "default") -> Dict[str, Any]:
        """Get technical indicator weights"""
        settings = self.get_settings(user_id)
        if settings and settings.technical_indicator_weights:
            return settings.technical_indicator_weights
        return {
            'rsi_weight': 1.0,
            'macd_weight': 1.0,
            'volume_weight': 1.0,
            'candlestick_weight': 2.0,
            'bollinger_weight': 1.0,
            'ma_weight': 1.0,
            'support_resistance_weight': 2.0
        }
    
    def get_rsi_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get RSI settings"""
        settings = self.get_settings(user_id)
        if settings and settings.rsi_settings:
            return settings.rsi_settings
        return {'period': 14, 'overbought': 70, 'oversold': 30}
    
    def get_macd_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get MACD settings"""
        settings = self.get_settings(user_id)
        if settings and settings.macd_settings:
            return settings.macd_settings
        return {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
    
    def get_bollinger_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get Bollinger Bands settings"""
        settings = self.get_settings(user_id)
        if settings and settings.bollinger_settings:
            return settings.bollinger_settings
        return {'period': 20, 'deviation': 2.0}
    
    def get_ma_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get Moving Average settings"""
        settings = self.get_settings(user_id)
        if settings and settings.ma_settings:
            return settings.ma_settings
        return {'short_ma': 20, 'long_ma': 50, 'ma_type': 'EMA'}
    
    def get_volume_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get Volume settings"""
        settings = self.get_settings(user_id)
        if settings and settings.volume_settings:
            return settings.volume_settings
        return {'volume_threshold_multiplier': 1.5, 'high_volume_threshold': 2.0}
    
    def get_candlestick_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get Candlestick pattern settings"""
        settings = self.get_settings(user_id)
        if settings and settings.candlestick_settings:
            return settings.candlestick_settings
        return {'sensitivity': 'medium', 'min_pattern_score': 0.7}
    
    def get_ai_ml_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get AI/ML settings"""
        settings = self.get_settings(user_id)
        if settings and settings.ai_ml_settings:
            return settings.ai_ml_settings
        return {
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
        }
    
    def get_notification_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get notification settings"""
        settings = self.get_settings(user_id)
        if settings and settings.notification_settings:
            return settings.notification_settings
        return {
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
        }
    
    def get_backtest_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get backtesting settings"""
        settings = self.get_settings(user_id)
        if settings and settings.backtest_settings:
            return settings.backtest_settings
        return {
            'default_period_days': 30,
            'default_symbols': ['BTCUSDT', 'ETHUSDT'],
            'commission_rate': 0.001,
            'slippage_bps': 5,
            'initial_capital': 10000,
            'benchmark_symbol': 'BTCUSDT'
        }
    
    def get_advanced_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get advanced settings"""
        settings = self.get_settings(user_id)
        if settings and settings.advanced_settings:
            return settings.advanced_settings
        return {
            'api_rate_limit': 1200,
            'retry_attempts': 3,
            'request_timeout': 30,
            'cache_duration': 300,
            'logging_level': 'INFO',
            'webhook_urls': []
        }
    
    def get_ui_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get UI/UX settings"""
        settings = self.get_settings(user_id)
        if settings and settings.ui_settings:
            return settings.ui_settings
        return {
            'dashboard_refresh_rate': 30,
            'chart_default_timeframe': '1h',
            'table_rows_per_page': 25,
            'theme': 'light',
            'language': 'hu',
            'decimal_places': 6
        }
    
    def get_stop_loss_take_profit_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get stop loss and take profit settings"""
        settings = self.get_settings(user_id)
        if settings:
            return {
                'stop_loss_percentage': float(getattr(settings, 'stop_loss_percentage', 0.02)),
                'take_profit_percentage': float(getattr(settings, 'take_profit_percentage', 0.04)),
                'use_atr_based_sl_tp': getattr(settings, 'use_atr_based_sl_tp', False),
                'atr_multiplier_sl': float(getattr(settings, 'atr_multiplier_sl', 1.0)),
                'atr_multiplier_tp': float(getattr(settings, 'atr_multiplier_tp', 2.0))
            }
        return {
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.04,
            'use_atr_based_sl_tp': False,
            'atr_multiplier_sl': 1.0,
            'atr_multiplier_tp': 2.0
        }
    
    def update_stop_loss_take_profit_settings(self, settings_data: Dict[str, Any], user_id: str = "default"):
        """Update stop loss and take profit settings"""
        # Map the settings to the correct database column names
        db_settings = {}
        
        if 'stop_loss_percentage' in settings_data:
            db_settings['stop_loss_percentage'] = settings_data['stop_loss_percentage']
        if 'take_profit_percentage' in settings_data:
            db_settings['take_profit_percentage'] = settings_data['take_profit_percentage']
        if 'use_atr_based_sl_tp' in settings_data:
            db_settings['use_atr_based_sl_tp'] = settings_data['use_atr_based_sl_tp']
        if 'atr_multiplier_sl' in settings_data:
            db_settings['atr_multiplier_sl'] = settings_data['atr_multiplier_sl']
        if 'atr_multiplier_tp' in settings_data:
            db_settings['atr_multiplier_tp'] = settings_data['atr_multiplier_tp']
        
        return self.update_settings(user_id, db_settings)


# Helper function to get settings service instance
def get_trading_settings_service(db: Session) -> TradingSettingsService:
    """Get trading settings service instance"""
    return TradingSettingsService(db)
