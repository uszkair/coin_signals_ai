"""
Multi-Timeframe Support/Resistance Analyzer
Analyzes key support and resistance levels across multiple timeframes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
from app.utils.price_data import get_historical_data

logger = logging.getLogger(__name__)


class SupportResistanceLevel:
    """Represents a support or resistance level"""
    
    def __init__(self, price: float, level_type: str, strength: int, 
                 timeframe: str, touches: int, last_touch: datetime):
        self.price = price
        self.level_type = level_type  # 'support' or 'resistance'
        self.strength = strength  # 1-5 (5 being strongest)
        self.timeframe = timeframe
        self.touches = touches  # Number of times price touched this level
        self.last_touch = last_touch
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'price': self.price,
            'type': self.level_type,
            'strength': self.strength,
            'timeframe': self.timeframe,
            'touches': self.touches,
            'last_touch': self.last_touch.isoformat() if self.last_touch else None,
            'distance_percent': 0  # Will be calculated relative to current price
        }


class MultiTimeframeSupportResistance:
    """Multi-timeframe support and resistance analyzer"""
    
    def __init__(self):
        self.timeframes = {
            '1h': {'days': 7, 'weight': 1.0},    # 1 hour - last 7 days
            '4h': {'days': 30, 'weight': 1.5},   # 4 hours - last 30 days  
            '1d': {'days': 90, 'weight': 2.0},   # 1 day - last 90 days
            '1w': {'days': 365, 'weight': 2.5}   # 1 week - last 365 days
        }
        
    async def analyze_levels(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Analyze support and resistance levels across multiple timeframes
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            current_price: Current market price
            
        Returns:
            Dictionary containing support/resistance analysis
        """
        try:
            all_levels = []
            timeframe_analysis = {}
            
            # Analyze each timeframe
            for timeframe, config in self.timeframes.items():
                try:
                    logger.info(f"Analyzing {timeframe} timeframe for {symbol}")
                    
                    # Get historical data for this timeframe
                    candles = await get_historical_data(
                        symbol=symbol, 
                        interval=timeframe, 
                        days=config['days']
                    )
                    
                    if len(candles) < 20:  # Need minimum data
                        continue
                        
                    # Find support and resistance levels
                    levels = self._find_levels(candles, timeframe, config['weight'])
                    all_levels.extend(levels)
                    
                    # Analyze this timeframe
                    timeframe_analysis[timeframe] = {
                        'levels_found': len(levels),
                        'strongest_support': self._get_strongest_level(levels, 'support'),
                        'strongest_resistance': self._get_strongest_level(levels, 'resistance'),
                        'current_zone': self._analyze_current_zone(levels, current_price)
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing {timeframe} for {symbol}: {e}")
                    continue
            
            # Consolidate and rank all levels
            consolidated_levels = self._consolidate_levels(all_levels, current_price)
            
            # Find the most relevant levels near current price
            nearby_levels = self._find_nearby_levels(consolidated_levels, current_price)
            
            # Analyze current price position
            price_analysis = self._analyze_price_position(consolidated_levels, current_price)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'analysis_timestamp': datetime.now().isoformat(),
                'timeframe_analysis': timeframe_analysis,
                'all_levels': [level.to_dict() for level in consolidated_levels],
                'nearby_levels': {
                    'support': [level.to_dict() for level in nearby_levels['support']],
                    'resistance': [level.to_dict() for level in nearby_levels['resistance']]
                },
                'price_position': price_analysis,
                'trading_signals': self._generate_trading_signals(consolidated_levels, current_price)
            }
            
        except Exception as e:
            logger.error(f"Error in support/resistance analysis for {symbol}: {e}")
            return self._get_default_analysis(symbol, current_price)
    
    def _find_levels(self, candles: List[Dict], timeframe: str, weight: float) -> List[SupportResistanceLevel]:
        """Find support and resistance levels in candle data"""
        levels = []
        
        if len(candles) < 20:
            return levels
            
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(candles)
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Find pivot highs and lows
        window = 5  # Look for pivots in 5-candle windows
        
        # Find resistance levels (pivot highs)
        for i in range(window, len(df) - window):
            current_high = df.iloc[i]['high']
            is_pivot_high = True
            
            # Check if this is a local maximum
            for j in range(i - window, i + window + 1):
                if j != i and df.iloc[j]['high'] >= current_high:
                    is_pivot_high = False
                    break
            
            if is_pivot_high:
                # Count how many times price touched this level
                touches = self._count_touches(df, current_high, 'resistance')
                if touches >= 2:  # Only consider levels touched at least twice
                    strength = min(5, touches + int(weight))
                    levels.append(SupportResistanceLevel(
                        price=current_high,
                        level_type='resistance',
                        strength=strength,
                        timeframe=timeframe,
                        touches=touches,
                        last_touch=df.iloc[i]['timestamp']
                    ))
        
        # Find support levels (pivot lows)
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            is_pivot_low = True
            
            # Check if this is a local minimum
            for j in range(i - window, i + window + 1):
                if j != i and df.iloc[j]['low'] <= current_low:
                    is_pivot_low = False
                    break
            
            if is_pivot_low:
                # Count how many times price touched this level
                touches = self._count_touches(df, current_low, 'support')
                if touches >= 2:  # Only consider levels touched at least twice
                    strength = min(5, touches + int(weight))
                    levels.append(SupportResistanceLevel(
                        price=current_low,
                        level_type='support',
                        strength=strength,
                        timeframe=timeframe,
                        touches=touches,
                        last_touch=df.iloc[i]['timestamp']
                    ))
        
        return levels
    
    def _count_touches(self, df: pd.DataFrame, level_price: float, level_type: str) -> int:
        """Count how many times price touched a specific level"""
        tolerance = level_price * 0.005  # 0.5% tolerance
        touches = 0
        
        for _, candle in df.iterrows():
            if level_type == 'resistance':
                # Check if high touched the resistance level
                if abs(candle['high'] - level_price) <= tolerance:
                    touches += 1
            else:  # support
                # Check if low touched the support level
                if abs(candle['low'] - level_price) <= tolerance:
                    touches += 1
        
        return touches
    
    def _consolidate_levels(self, all_levels: List[SupportResistanceLevel], 
                          current_price: float) -> List[SupportResistanceLevel]:
        """Consolidate similar levels and remove weak ones"""
        if not all_levels:
            return []
        
        # Group similar levels (within 1% of each other)
        consolidated = []
        tolerance = current_price * 0.01  # 1% tolerance
        
        # Sort levels by price
        sorted_levels = sorted(all_levels, key=lambda x: x.price)
        
        i = 0
        while i < len(sorted_levels):
            current_level = sorted_levels[i]
            similar_levels = [current_level]
            
            # Find all levels within tolerance
            j = i + 1
            while j < len(sorted_levels) and abs(sorted_levels[j].price - current_level.price) <= tolerance:
                similar_levels.append(sorted_levels[j])
                j += 1
            
            # Consolidate similar levels into the strongest one
            if len(similar_levels) > 1:
                # Find the strongest level
                strongest = max(similar_levels, key=lambda x: x.strength)
                
                # Combine touches and update strength
                total_touches = sum(level.touches for level in similar_levels)
                combined_strength = min(5, strongest.strength + len(similar_levels) - 1)
                
                # Create consolidated level
                consolidated_level = SupportResistanceLevel(
                    price=strongest.price,
                    level_type=strongest.level_type,
                    strength=combined_strength,
                    timeframe=strongest.timeframe,
                    touches=total_touches,
                    last_touch=max(level.last_touch for level in similar_levels if level.last_touch)
                )
                consolidated.append(consolidated_level)
            else:
                consolidated.append(current_level)
            
            i = j
        
        # Filter out weak levels (strength < 2) and sort by strength
        strong_levels = [level for level in consolidated if level.strength >= 2]
        return sorted(strong_levels, key=lambda x: x.strength, reverse=True)
    
    def _find_nearby_levels(self, levels: List[SupportResistanceLevel], 
                          current_price: float) -> Dict[str, List[SupportResistanceLevel]]:
        """Find support and resistance levels near current price"""
        nearby_range = current_price * 0.05  # 5% range
        
        nearby_support = []
        nearby_resistance = []
        
        for level in levels:
            distance = abs(level.price - current_price)
            if distance <= nearby_range:
                level_dict = level.to_dict()
                level_dict['distance_percent'] = ((level.price - current_price) / current_price) * 100
                
                if level.level_type == 'support' and level.price < current_price:
                    nearby_support.append(level)
                elif level.level_type == 'resistance' and level.price > current_price:
                    nearby_resistance.append(level)
        
        # Sort by distance from current price
        nearby_support.sort(key=lambda x: abs(x.price - current_price))
        nearby_resistance.sort(key=lambda x: abs(x.price - current_price))
        
        return {
            'support': nearby_support[:3],  # Top 3 closest support levels
            'resistance': nearby_resistance[:3]  # Top 3 closest resistance levels
        }
    
    def _analyze_price_position(self, levels: List[SupportResistanceLevel], 
                              current_price: float) -> Dict[str, Any]:
        """Analyze current price position relative to support/resistance levels"""
        
        # Find nearest support and resistance
        nearest_support = None
        nearest_resistance = None
        
        for level in levels:
            if level.level_type == 'support' and level.price < current_price:
                if nearest_support is None or level.price > nearest_support.price:
                    nearest_support = level
            elif level.level_type == 'resistance' and level.price > current_price:
                if nearest_resistance is None or level.price < nearest_resistance.price:
                    nearest_resistance = level
        
        analysis = {
            'nearest_support': nearest_support.to_dict() if nearest_support else None,
            'nearest_resistance': nearest_resistance.to_dict() if nearest_resistance else None,
            'position': 'neutral'
        }
        
        # Determine position
        if nearest_support and nearest_resistance:
            support_distance = current_price - nearest_support.price
            resistance_distance = nearest_resistance.price - current_price
            total_range = nearest_resistance.price - nearest_support.price
            
            position_ratio = support_distance / total_range if total_range > 0 else 0.5
            
            if position_ratio < 0.2:
                analysis['position'] = 'near_support'
            elif position_ratio > 0.8:
                analysis['position'] = 'near_resistance'
            else:
                analysis['position'] = 'middle_range'
                
            analysis['support_distance_percent'] = (support_distance / current_price) * 100
            analysis['resistance_distance_percent'] = (resistance_distance / current_price) * 100
        
        return analysis
    
    def _generate_trading_signals(self, levels: List[SupportResistanceLevel], 
                                current_price: float) -> Dict[str, Any]:
        """Generate trading signals based on support/resistance analysis"""
        signals = {
            'breakout_potential': 'none',
            'signal_strength': 0,
            'recommended_action': 'hold',
            'key_levels': {
                'support': None,
                'resistance': None
            },
            'reasoning': []
        }
        
        # Find the strongest nearby levels
        nearby_levels = self._find_nearby_levels(levels, current_price)
        
        if nearby_levels['resistance']:
            strongest_resistance = max(nearby_levels['resistance'], key=lambda x: x.strength)
            signals['key_levels']['resistance'] = strongest_resistance.price
            
            # Check for resistance breakout potential
            distance_to_resistance = ((strongest_resistance.price - current_price) / current_price) * 100
            if distance_to_resistance < 1:  # Within 1% of resistance
                signals['breakout_potential'] = 'resistance_test'
                signals['signal_strength'] += strongest_resistance.strength
                signals['reasoning'].append(f"Price testing strong resistance at {strongest_resistance.price:.2f}")
        
        if nearby_levels['support']:
            strongest_support = max(nearby_levels['support'], key=lambda x: x.strength)
            signals['key_levels']['support'] = strongest_support.price
            
            # Check for support bounce potential
            distance_to_support = ((current_price - strongest_support.price) / current_price) * 100
            if distance_to_support < 1:  # Within 1% of support
                signals['breakout_potential'] = 'support_test'
                signals['signal_strength'] += strongest_support.strength
                signals['reasoning'].append(f"Price testing strong support at {strongest_support.price:.2f}")
        
        # Generate recommendation
        if signals['signal_strength'] >= 4:
            if signals['breakout_potential'] == 'resistance_test':
                signals['recommended_action'] = 'watch_for_breakout'
            elif signals['breakout_potential'] == 'support_test':
                signals['recommended_action'] = 'watch_for_bounce'
        
        return signals
    
    def _get_strongest_level(self, levels: List[SupportResistanceLevel], 
                           level_type: str) -> Optional[Dict[str, Any]]:
        """Get the strongest level of specified type"""
        filtered_levels = [level for level in levels if level.level_type == level_type]
        if not filtered_levels:
            return None
        
        strongest = max(filtered_levels, key=lambda x: x.strength)
        return strongest.to_dict()
    
    def _analyze_current_zone(self, levels: List[SupportResistanceLevel], 
                            current_price: float) -> str:
        """Analyze what zone the current price is in"""
        support_levels = [level for level in levels if level.level_type == 'support' and level.price < current_price]
        resistance_levels = [level for level in levels if level.level_type == 'resistance' and level.price > current_price]
        
        if not support_levels and not resistance_levels:
            return 'no_clear_zone'
        elif not support_levels:
            return 'below_all_support'
        elif not resistance_levels:
            return 'above_all_resistance'
        else:
            return 'between_levels'
    
    def _get_default_analysis(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Return default analysis when data is insufficient"""
        return {
            'symbol': symbol,
            'current_price': current_price,
            'analysis_timestamp': datetime.now().isoformat(),
            'timeframe_analysis': {},
            'all_levels': [],
            'nearby_levels': {'support': [], 'resistance': []},
            'price_position': {
                'nearest_support': None,
                'nearest_resistance': None,
                'position': 'insufficient_data'
            },
            'trading_signals': {
                'breakout_potential': 'none',
                'signal_strength': 0,
                'recommended_action': 'hold',
                'key_levels': {'support': None, 'resistance': None},
                'reasoning': ['Insufficient data for support/resistance analysis']
            }
        }


# Global instance for easy access
support_resistance_analyzer = MultiTimeframeSupportResistance()


async def analyze_support_resistance(symbol: str, current_price: float) -> Dict[str, Any]:
    """
    Analyze support and resistance levels for a symbol
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        current_price: Current market price
        
    Returns:
        Dictionary containing comprehensive support/resistance analysis
    """
    return await support_resistance_analyzer.analyze_levels(symbol, current_price)