"""
Multi-Timeframe Technical Analysis Service
Analyzes RSI, MACD, candlestick patterns across multiple timeframes
Similar to support/resistance analysis but for all technical indicators
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.utils.price_data import get_historical_data
from app.services.technical_indicators import TechnicalIndicators
from app.services.candlestick_analyzer import detect_patterns

logger = logging.getLogger(__name__)

class MultiTimeframeAnalyzer:
    """
    Multi-timeframe technical analysis for RSI, MACD, candlestick patterns
    Analyzes 4 timeframes: 1h, 6h, 1d, 1d (long-term)
    """
    
    def __init__(self):
        # Timeframes to analyze (similar to support/resistance)
        self.timeframes = {
            '1h': {'interval': '1h', 'days': 7, 'weight': 1.0},
            '6h': {'interval': '6h', 'days': 30, 'weight': 1.5},  # Changed from 4h to 6h for Coinbase compatibility
            '1d': {'interval': '1d', 'days': 90, 'weight': 2.0},
            '1d_long': {'interval': '1d', 'days': 300, 'weight': 2.5}  # Changed from 365 to 300 days (Coinbase limit)
        }
    
    async def analyze_multi_timeframe_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze technical indicators across multiple timeframes
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary containing multi-timeframe analysis
        """
        try:
            timeframe_data = {}
            
            # Analyze each timeframe
            for tf_name, tf_config in self.timeframes.items():
                try:
                    # Get historical data for this timeframe
                    candles = await get_historical_data(
                        symbol=symbol,
                        interval=tf_config['interval'],
                        days=tf_config['days']
                    )
                    
                    if len(candles) < 50:  # Need minimum data
                        continue
                    
                    # Calculate technical indicators for this timeframe
                    indicators = TechnicalIndicators(candles)
                    tf_indicators = indicators.get_latest_indicators()
                    
                    # Analyze candlestick patterns
                    latest = candles[-1]
                    previous = candles[-2] if len(candles) > 1 else None
                    pattern, score = detect_patterns(latest, previous)
                    
                    # Store timeframe analysis
                    timeframe_data[tf_name] = {
                        'interval': tf_config['interval'],
                        'weight': tf_config['weight'],
                        'rsi': tf_indicators['rsi'],
                        'macd': tf_indicators['macd'],
                        'moving_averages': tf_indicators['moving_averages'],
                        'adx': tf_indicators['adx'],
                        'stochastic': tf_indicators['stochastic'],
                        'bollinger_bands': tf_indicators['bollinger_bands'],
                        'volume': tf_indicators['volume'],
                        'candlestick_pattern': {
                            'name': pattern,
                            'score': score,
                            'signal': self._get_pattern_signal(pattern)
                        },
                        'market_assessment': tf_indicators['market_assessment']
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze {tf_name} timeframe for {symbol}: {e}")
                    continue
            
            # Generate multi-timeframe signals
            multi_tf_signals = self._generate_multi_timeframe_signals(timeframe_data)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'timeframe_analysis': timeframe_data,
                'multi_timeframe_signals': multi_tf_signals,
                'overall_assessment': self._assess_overall_multi_timeframe(timeframe_data)
            }
            
        except Exception as e:
            logger.error(f"Multi-timeframe analysis failed for {symbol}: {e}")
            return self._get_default_analysis(symbol)
    
    def _get_pattern_signal(self, pattern: str) -> str:
        """Convert candlestick pattern to signal"""
        bullish_patterns = ["Hammer", "Bullish Engulfing", "Morning Star", "Piercing Pattern"]
        bearish_patterns = ["Shooting Star", "Bearish Engulfing", "Evening Star", "Dark Cloud Cover"]
        
        if pattern in bullish_patterns:
            return "BUY"
        elif pattern in bearish_patterns:
            return "SELL"
        else:
            return "NEUTRAL"
    
    def _generate_multi_timeframe_signals(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate signals based on multi-timeframe analysis"""
        
        signals = {
            'rsi_confluence': self._analyze_rsi_confluence(timeframe_data),
            'macd_confluence': self._analyze_macd_confluence(timeframe_data),
            'trend_confluence': self._analyze_trend_confluence(timeframe_data),
            'pattern_confluence': self._analyze_pattern_confluence(timeframe_data),
            'momentum_confluence': self._analyze_momentum_confluence(timeframe_data)
        }
        
        # Calculate overall multi-timeframe signal strength
        signals['overall_signal'] = self._calculate_overall_signal(signals)
        
        return signals
    
    def _analyze_rsi_confluence(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RSI across multiple timeframes"""
        rsi_signals = []
        weighted_score = 0
        total_weight = 0
        
        for tf_name, tf_data in timeframe_data.items():
            rsi_data = tf_data.get('rsi', {})
            rsi_signal = rsi_data.get('signal', 'NEUTRAL')
            weight = tf_data.get('weight', 1.0)
            
            rsi_signals.append({
                'timeframe': tf_name,
                'signal': rsi_signal,
                'value': rsi_data.get('value', 50),
                'weight': weight
            })
            
            # Calculate weighted score
            if rsi_signal == 'BUY':
                weighted_score += weight
            elif rsi_signal == 'SELL':
                weighted_score -= weight
            
            total_weight += weight
        
        # Determine confluence signal
        if total_weight > 0:
            confluence_score = weighted_score / total_weight
            if confluence_score > 0.3:
                confluence_signal = 'BUY'
            elif confluence_score < -0.3:
                confluence_signal = 'SELL'
            else:
                confluence_signal = 'NEUTRAL'
        else:
            confluence_signal = 'NEUTRAL'
            confluence_score = 0
        
        return {
            'signal': confluence_signal,
            'strength': abs(confluence_score),
            'timeframe_signals': rsi_signals,
            'reasoning': f"RSI confluence across {len(rsi_signals)} timeframes: {confluence_signal}"
        }
    
    def _analyze_macd_confluence(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze MACD across multiple timeframes"""
        macd_signals = []
        weighted_score = 0
        total_weight = 0
        
        for tf_name, tf_data in timeframe_data.items():
            macd_data = tf_data.get('macd', {})
            macd_signal = macd_data.get('signal_type', 'NEUTRAL')
            weight = tf_data.get('weight', 1.0)
            
            macd_signals.append({
                'timeframe': tf_name,
                'signal': macd_signal,
                'macd': macd_data.get('macd', 0),
                'histogram': macd_data.get('histogram', 0),
                'weight': weight
            })
            
            # Calculate weighted score
            if macd_signal == 'BUY':
                weighted_score += weight
            elif macd_signal == 'SELL':
                weighted_score -= weight
            
            total_weight += weight
        
        # Determine confluence signal
        if total_weight > 0:
            confluence_score = weighted_score / total_weight
            if confluence_score > 0.3:
                confluence_signal = 'BUY'
            elif confluence_score < -0.3:
                confluence_signal = 'SELL'
            else:
                confluence_signal = 'NEUTRAL'
        else:
            confluence_signal = 'NEUTRAL'
            confluence_score = 0
        
        return {
            'signal': confluence_signal,
            'strength': abs(confluence_score),
            'timeframe_signals': macd_signals,
            'reasoning': f"MACD confluence across {len(macd_signals)} timeframes: {confluence_signal}"
        }
    
    def _analyze_trend_confluence(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend across multiple timeframes"""
        trend_signals = []
        weighted_score = 0
        total_weight = 0
        
        for tf_name, tf_data in timeframe_data.items():
            ma_data = tf_data.get('moving_averages', {})
            trend = ma_data.get('trend', 'NEUTRAL')
            weight = tf_data.get('weight', 1.0)
            
            trend_signals.append({
                'timeframe': tf_name,
                'trend': trend,
                'weight': weight
            })
            
            # Calculate weighted score
            if trend == 'BULLISH':
                weighted_score += weight
            elif trend == 'BEARISH':
                weighted_score -= weight
            
            total_weight += weight
        
        # Determine confluence signal
        if total_weight > 0:
            confluence_score = weighted_score / total_weight
            if confluence_score > 0.3:
                confluence_signal = 'BULLISH'
            elif confluence_score < -0.3:
                confluence_signal = 'BEARISH'
            else:
                confluence_signal = 'NEUTRAL'
        else:
            confluence_signal = 'NEUTRAL'
            confluence_score = 0
        
        return {
            'signal': confluence_signal,
            'strength': abs(confluence_score),
            'timeframe_signals': trend_signals,
            'reasoning': f"Trend confluence across {len(trend_signals)} timeframes: {confluence_signal}"
        }
    
    def _analyze_pattern_confluence(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze candlestick patterns across multiple timeframes"""
        pattern_signals = []
        weighted_score = 0
        total_weight = 0
        
        for tf_name, tf_data in timeframe_data.items():
            pattern_data = tf_data.get('candlestick_pattern', {})
            pattern_signal = pattern_data.get('signal', 'NEUTRAL')
            pattern_name = pattern_data.get('name', 'None')
            weight = tf_data.get('weight', 1.0)
            
            if pattern_name and pattern_name != 'None':
                pattern_signals.append({
                    'timeframe': tf_name,
                    'pattern': pattern_name,
                    'signal': pattern_signal,
                    'score': pattern_data.get('score', 0),
                    'weight': weight
                })
                
                # Calculate weighted score
                if pattern_signal == 'BUY':
                    weighted_score += weight
                elif pattern_signal == 'SELL':
                    weighted_score -= weight
                
                total_weight += weight
        
        # Determine confluence signal
        if total_weight > 0:
            confluence_score = weighted_score / total_weight
            if confluence_score > 0.3:
                confluence_signal = 'BUY'
            elif confluence_score < -0.3:
                confluence_signal = 'SELL'
            else:
                confluence_signal = 'NEUTRAL'
        else:
            confluence_signal = 'NEUTRAL'
            confluence_score = 0
        
        return {
            'signal': confluence_signal,
            'strength': abs(confluence_score),
            'timeframe_signals': pattern_signals,
            'reasoning': f"Pattern confluence across {len(pattern_signals)} timeframes: {confluence_signal}"
        }
    
    def _analyze_momentum_confluence(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze momentum across multiple timeframes using ADX and Stochastic"""
        momentum_signals = []
        weighted_score = 0
        total_weight = 0
        
        for tf_name, tf_data in timeframe_data.items():
            adx_data = tf_data.get('adx', {})
            stoch_data = tf_data.get('stochastic', {})
            weight = tf_data.get('weight', 1.0)
            
            # Combine ADX direction and Stochastic signal
            adx_direction = adx_data.get('trend_direction', 'NEUTRAL')
            stoch_signal = stoch_data.get('signal', 'NEUTRAL')
            
            # Determine momentum signal
            momentum_signal = 'NEUTRAL'
            if adx_direction == 'BULLISH' and stoch_signal in ['BUY', 'NEUTRAL']:
                momentum_signal = 'BUY'
            elif adx_direction == 'BEARISH' and stoch_signal in ['SELL', 'NEUTRAL']:
                momentum_signal = 'SELL'
            elif stoch_signal == 'BUY':
                momentum_signal = 'BUY'
            elif stoch_signal == 'SELL':
                momentum_signal = 'SELL'
            
            momentum_signals.append({
                'timeframe': tf_name,
                'signal': momentum_signal,
                'adx_direction': adx_direction,
                'stoch_signal': stoch_signal,
                'weight': weight
            })
            
            # Calculate weighted score
            if momentum_signal == 'BUY':
                weighted_score += weight
            elif momentum_signal == 'SELL':
                weighted_score -= weight
            
            total_weight += weight
        
        # Determine confluence signal
        if total_weight > 0:
            confluence_score = weighted_score / total_weight
            if confluence_score > 0.3:
                confluence_signal = 'BUY'
            elif confluence_score < -0.3:
                confluence_signal = 'SELL'
            else:
                confluence_signal = 'NEUTRAL'
        else:
            confluence_signal = 'NEUTRAL'
            confluence_score = 0
        
        return {
            'signal': confluence_signal,
            'strength': abs(confluence_score),
            'timeframe_signals': momentum_signals,
            'reasoning': f"Momentum confluence across {len(momentum_signals)} timeframes: {confluence_signal}"
        }
    
    def _calculate_overall_signal(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall multi-timeframe signal"""
        signal_weights = {
            'rsi_confluence': 1.0,
            'macd_confluence': 1.5,
            'trend_confluence': 2.0,
            'pattern_confluence': 1.0,
            'momentum_confluence': 1.0
        }
        
        total_score = 0
        total_weight = 0
        signal_breakdown = {}
        
        for signal_type, signal_data in signals.items():
            if signal_type == 'overall_signal':
                continue
                
            signal = signal_data.get('signal', 'NEUTRAL')
            strength = signal_data.get('strength', 0)
            weight = signal_weights.get(signal_type, 1.0)
            
            signal_breakdown[signal_type] = {
                'signal': signal,
                'strength': strength,
                'weight': weight
            }
            
            # Calculate weighted score
            if signal in ['BUY', 'BULLISH']:
                total_score += weight * strength
            elif signal in ['SELL', 'BEARISH']:
                total_score -= weight * strength
            
            total_weight += weight
        
        # Determine overall signal
        if total_weight > 0:
            overall_score = total_score / total_weight
            if overall_score > 0.4:
                overall_signal = 'BUY'
            elif overall_score < -0.4:
                overall_signal = 'SELL'
            else:
                overall_signal = 'NEUTRAL'
        else:
            overall_signal = 'NEUTRAL'
            overall_score = 0
        
        return {
            'signal': overall_signal,
            'strength': abs(overall_score),
            'confidence': min(95, max(25, 50 + abs(overall_score) * 50)),
            'signal_breakdown': signal_breakdown,
            'reasoning': f"Multi-timeframe analysis: {overall_signal} (strength: {abs(overall_score):.2f})"
        }
    
    def _assess_overall_multi_timeframe(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall multi-timeframe market condition"""
        if not timeframe_data:
            return {'status': 'insufficient_data', 'recommendation': 'HOLD'}
        
        # Count bullish/bearish signals across timeframes
        bullish_count = 0
        bearish_count = 0
        total_timeframes = len(timeframe_data)
        
        for tf_data in timeframe_data.values():
            market_assessment = tf_data.get('market_assessment', {})
            trend = market_assessment.get('trend', 'NEUTRAL')
            
            if trend == 'BULLISH':
                bullish_count += 1
            elif trend == 'BEARISH':
                bearish_count += 1
        
        # Determine overall assessment
        if bullish_count >= total_timeframes * 0.6:
            status = 'strong_bullish'
            recommendation = 'BUY'
        elif bearish_count >= total_timeframes * 0.6:
            status = 'strong_bearish'
            recommendation = 'SELL'
        elif bullish_count > bearish_count:
            status = 'weak_bullish'
            recommendation = 'BUY'
        elif bearish_count > bullish_count:
            status = 'weak_bearish'
            recommendation = 'SELL'
        else:
            status = 'neutral'
            recommendation = 'HOLD'
        
        return {
            'status': status,
            'recommendation': recommendation,
            'bullish_timeframes': bullish_count,
            'bearish_timeframes': bearish_count,
            'total_timeframes': total_timeframes,
            'consensus_strength': max(bullish_count, bearish_count) / total_timeframes
        }
    
    def _get_default_analysis(self, symbol: str) -> Dict[str, Any]:
        """Return default analysis when data is insufficient"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'timeframe_analysis': {},
            'multi_timeframe_signals': {
                'rsi_confluence': {'signal': 'NEUTRAL', 'strength': 0, 'reasoning': 'Insufficient data'},
                'macd_confluence': {'signal': 'NEUTRAL', 'strength': 0, 'reasoning': 'Insufficient data'},
                'trend_confluence': {'signal': 'NEUTRAL', 'strength': 0, 'reasoning': 'Insufficient data'},
                'pattern_confluence': {'signal': 'NEUTRAL', 'strength': 0, 'reasoning': 'Insufficient data'},
                'momentum_confluence': {'signal': 'NEUTRAL', 'strength': 0, 'reasoning': 'Insufficient data'},
                'overall_signal': {'signal': 'NEUTRAL', 'strength': 0, 'confidence': 25, 'reasoning': 'Insufficient data'}
            },
            'overall_assessment': {'status': 'insufficient_data', 'recommendation': 'HOLD'}
        }


# Main function for external use
async def analyze_multi_timeframe_indicators(symbol: str) -> Dict[str, Any]:
    """
    Analyze technical indicators across multiple timeframes
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        
    Returns:
        Dictionary containing comprehensive multi-timeframe analysis
    """
    analyzer = MultiTimeframeAnalyzer()
    return await analyzer.analyze_multi_timeframe_indicators(symbol)