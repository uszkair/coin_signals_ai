"""
Trading Settings Service
Manages trading settings stored in database
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database_service import DatabaseService
from app.database import get_db

logger = logging.getLogger(__name__)


class TradingSettingsService:
    """Service for managing trading settings in database"""
    
    def __init__(self):
        self._cached_settings = None
        self._user_id = '1'  # Use user ID 1 for default user
    
    async def get_settings(self) -> Dict[str, Any]:
        """Get trading settings from database"""
        try:
            async for db in get_db():
                # Ensure default settings exist
                await DatabaseService.create_default_trading_settings(db, self._user_id)
                
                # Get settings
                settings = await DatabaseService.get_trading_settings(db, self._user_id)
                if settings:
                    self._cached_settings = settings.to_dict()
                    return self._cached_settings
                else:
                    # Return defaults if not found
                    return self._get_default_settings()
        except Exception as e:
            logger.error(f"Error getting trading settings: {e}")
            return self._get_default_settings()
    
    async def update_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update trading settings in database"""
        try:
            async for db in get_db():
                settings = await DatabaseService.save_trading_settings(db, self._user_id, settings_data)
                self._cached_settings = settings.to_dict()
                logger.info(f"Trading settings updated: {settings_data}")
                return self._cached_settings
        except Exception as e:
            logger.error(f"Error updating trading settings: {e}")
            raise
    
    async def get_auto_trading_settings(self) -> Dict[str, Any]:
        """Get auto-trading specific settings"""
        settings = await self.get_settings()
        return {
            'enabled': settings.get('auto_trading_enabled', False),
            'symbols': settings.get('monitored_symbols', ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']),
            'interval': settings.get('check_interval', 300),
            'min_confidence': settings.get('min_signal_confidence', 70)
        }
    
    async def update_auto_trading_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update auto-trading specific settings"""
        update_data = {}
        
        if 'enabled' in settings_data:
            update_data['auto_trading_enabled'] = settings_data['enabled']
        if 'symbols' in settings_data:
            update_data['monitored_symbols'] = settings_data['symbols']
        if 'interval' in settings_data:
            update_data['check_interval'] = max(60, settings_data['interval'])  # Minimum 1 minute
        if 'min_confidence' in settings_data:
            update_data['min_signal_confidence'] = max(50, min(95, settings_data['min_confidence']))
        
        return await self.update_settings(update_data)
    
    async def get_position_size_settings(self) -> Dict[str, Any]:
        """Get position size specific settings"""
        settings = await self.get_settings()
        return {
            'mode': settings.get('position_size_mode', 'percentage'),
            'max_position_size': settings.get('max_position_size', 0.02),  # Store as decimal in DB (0.02 = 2%)
            'default_position_size_usd': settings.get('default_position_size_usd')
        }
    
    async def update_position_size_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update position size specific settings"""
        update_data = {}
        
        if 'mode' in settings_data:
            update_data['position_size_mode'] = settings_data['mode']
        if 'max_percentage' in settings_data:
            update_data['max_position_size'] = settings_data['max_percentage'] / 100  # Convert to decimal
        if 'fixed_amount_usd' in settings_data:
            update_data['default_position_size_usd'] = settings_data['fixed_amount_usd']
        
        return await self.update_settings(update_data)
    
    async def get_risk_management_settings(self) -> Dict[str, Any]:
        """Get risk management specific settings"""
        settings = await self.get_settings()
        return {
            'max_daily_trades': settings.get('max_daily_trades', 10),
            'daily_loss_limit': settings.get('daily_loss_limit', 0.05),
            'max_position_size': settings.get('max_position_size', 0.02),
            'testnet_mode': settings.get('testnet_mode', True),  # Default to testnet for safety
            'use_futures': settings.get('use_futures', True)   # Default to Futures for testnet
        }
    
    async def update_risk_management_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update risk management specific settings"""
        update_data = {}
        
        if 'max_daily_trades' in settings_data:
            update_data['max_daily_trades'] = settings_data['max_daily_trades']
        if 'daily_loss_limit' in settings_data:
            update_data['daily_loss_limit'] = settings_data['daily_loss_limit']
        if 'max_position_size' in settings_data:
            update_data['max_position_size'] = settings_data['max_position_size']
        if 'testnet_mode' in settings_data:
            update_data['testnet_mode'] = settings_data['testnet_mode']
        if 'use_futures' in settings_data:
            update_data['use_futures'] = settings_data['use_futures']
        
        return await self.update_settings(update_data)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'user_id': self._user_id,
            'auto_trading_enabled': False,
            'monitored_symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
            'check_interval': 300,
            'min_signal_confidence': 70,
            'position_size_mode': 'percentage',
            'max_position_size': 0.02,
            'default_position_size_usd': None,
            'max_daily_trades': 10,
            'daily_loss_limit': 0.05,
            'testnet_mode': True,   # Default to testnet for safety
            'use_futures': True    # Default to Futures for testnet
        }
    
    def get_cached_settings(self) -> Optional[Dict[str, Any]]:
        """Get cached settings without database call"""
        return self._cached_settings


# Global instance
trading_settings_service = TradingSettingsService()