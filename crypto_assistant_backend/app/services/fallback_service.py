# app/services/fallback_service.py

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import os

class FallbackService:
    """
    Fallback service when database is not available.
    Stores signals in memory and optionally in JSON files.
    """
    
    def __init__(self):
        self.signals_cache = []
        self.cache_file = "signals_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Load signals from cache file if exists"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.signals_cache = data.get('signals', [])
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.signals_cache = []
    
    def save_cache(self):
        """Save signals to cache file"""
        try:
            data = {
                'signals': self.signals_cache[-100:],  # Keep only last 100
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def add_signal(self, signal_data: Dict[str, Any]):
        """Add a signal to the cache"""
        # Convert datetime to string for JSON serialization
        if 'timestamp' in signal_data and isinstance(signal_data['timestamp'], datetime):
            signal_data['timestamp'] = signal_data['timestamp'].isoformat()
        
        # Add ID if not present
        if 'id' not in signal_data:
            signal_data['id'] = len(self.signals_cache) + 1
        
        self.signals_cache.append(signal_data)
        
        # Keep only last 100 signals
        if len(self.signals_cache) > 100:
            self.signals_cache = self.signals_cache[-100:]
        
        self.save_cache()
    
    def get_recent_signals(self, hours: int = 24, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent signals with optional filtering"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_signals = []
        for signal in self.signals_cache:
            # Parse timestamp
            try:
                if isinstance(signal.get('timestamp'), str):
                    signal_time = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                else:
                    signal_time = signal.get('timestamp', datetime.now())
                
                # Check time filter
                if signal_time < cutoff_time:
                    continue
                
                # Check symbol filter
                if symbol and signal.get('symbol') != symbol:
                    continue
                
                filtered_signals.append(signal)
            except Exception as e:
                print(f"Error parsing signal timestamp: {e}")
                continue
        
        # Sort by timestamp (newest first) and limit
        filtered_signals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return filtered_signals[:limit]
    
    def get_signals_by_symbols(self, symbols: List[str], interval: str = "1h") -> List[Dict[str, Any]]:
        """Get latest signal for each symbol"""
        latest_signals = {}
        
        for signal in reversed(self.signals_cache):  # Start from newest
            symbol = signal.get('symbol')
            if symbol in symbols and symbol not in latest_signals:
                if signal.get('interval') == interval:
                    latest_signals[symbol] = signal
        
        return list(latest_signals.values())
    
    def clear_old_signals(self, days: int = 7):
        """Remove signals older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        filtered_signals = []
        for signal in self.signals_cache:
            try:
                if isinstance(signal.get('timestamp'), str):
                    signal_time = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                else:
                    signal_time = signal.get('timestamp', datetime.now())
                
                if signal_time >= cutoff_time:
                    filtered_signals.append(signal)
            except Exception:
                # Keep signal if timestamp parsing fails
                filtered_signals.append(signal)
        
        self.signals_cache = filtered_signals
        self.save_cache()

# Global instance
fallback_service = FallbackService()