"""
Professional Technical Indicators Service
Using the 'ta' library for accurate technical analysis calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from ta import add_all_ta_features
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator, ADXIndicator
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
from ta.others import DailyReturnIndicator


class TechnicalIndicators:
    """Professional technical indicators calculator"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        """
        Initialize with OHLCV data
        
        Args:
            data: List of candle data with keys: open, high, low, close, volume, timestamp
        """
        self.df = self._prepare_dataframe(data)
        self._calculate_all_indicators()
    
    def _prepare_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert candle data to pandas DataFrame"""
        df = pd.DataFrame(data)
        
        # Ensure proper column names and types
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # Sort by timestamp to ensure chronological order
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def _calculate_all_indicators(self):
        """Calculate all technical indicators"""
        if len(self.df) < 50:  # Need minimum data for reliable indicators
            return
        
        # RSI (Relative Strength Index)
        rsi = RSIIndicator(close=self.df['close'], window=14)
        self.df['rsi'] = rsi.rsi()
        
        # MACD (Moving Average Convergence Divergence)
        macd = MACD(close=self.df['close'], window_slow=26, window_fast=12, window_sign=9)
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_histogram'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = BollingerBands(close=self.df['close'], window=20, window_dev=2)
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        self.df['bb_percent'] = bb.bollinger_pband()
        
        # Moving Averages
        self.df['sma_20'] = SMAIndicator(close=self.df['close'], window=20).sma_indicator()
        self.df['sma_50'] = SMAIndicator(close=self.df['close'], window=50).sma_indicator()
        self.df['ema_12'] = EMAIndicator(close=self.df['close'], window=12).ema_indicator()
        self.df['ema_26'] = EMAIndicator(close=self.df['close'], window=26).ema_indicator()
        
        # ADX (Average Directional Index) - Trend Strength
        adx = ADXIndicator(high=self.df['high'], low=self.df['low'], close=self.df['close'], window=14)
        self.df['adx'] = adx.adx()
        self.df['adx_pos'] = adx.adx_pos()
        self.df['adx_neg'] = adx.adx_neg()
        
        # Stochastic Oscillator
        stoch = StochasticOscillator(high=self.df['high'], low=self.df['low'], close=self.df['close'])
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
        
        # Volume Indicators
        self.df['vwap'] = VolumeWeightedAveragePrice(high=self.df['high'], low=self.df['low'], close=self.df['close'], volume=self.df['volume']).volume_weighted_average_price()
        self.df['obv'] = OnBalanceVolumeIndicator(close=self.df['close'], volume=self.df['volume']).on_balance_volume()
        
        # Calculate simple volume moving average manually
        self.df['volume_sma'] = self.df['volume'].rolling(window=20).mean()
        
        # Price Action
        self.df['daily_return'] = DailyReturnIndicator(close=self.df['close']).daily_return()
    
    def get_latest_indicators(self) -> Dict[str, Any]:
        """Get the latest calculated indicators"""
        if len(self.df) == 0:
            return self._get_default_indicators()
        
        latest = self.df.iloc[-1]
        previous = self.df.iloc[-2] if len(self.df) > 1 else latest
        
        return {
            # RSI Analysis
            'rsi': {
                'value': float(latest.get('rsi', 50)),
                'signal': self._get_rsi_signal(latest.get('rsi', 50)),
                'overbought': bool(latest.get('rsi', 50) > 70),
                'oversold': bool(latest.get('rsi', 50) < 30),
                'divergence': bool(self._check_rsi_divergence())
            },
            
            # MACD Analysis
            'macd': {
                'macd': float(latest.get('macd', 0)),
                'signal': float(latest.get('macd_signal', 0)),
                'histogram': float(latest.get('macd_histogram', 0)),
                'signal_type': self._get_macd_signal(latest, previous),
                'bullish_crossover': bool(self._is_macd_bullish_crossover(latest, previous)),
                'bearish_crossover': bool(self._is_macd_bearish_crossover(latest, previous))
            },
            
            # Bollinger Bands
            'bollinger_bands': {
                'upper': float(latest.get('bb_upper', 0)),
                'middle': float(latest.get('bb_middle', 0)),
                'lower': float(latest.get('bb_lower', 0)),
                'width': float(latest.get('bb_width', 0)),
                'percent_b': float(latest.get('bb_percent', 0)),
                'squeeze': bool(latest.get('bb_width', 1) < 0.1),
                'breakout': self._check_bb_breakout(latest)
            },
            
            # Moving Averages
            'moving_averages': {
                'sma_20': float(latest.get('sma_20', 0)),
                'sma_50': float(latest.get('sma_50', 0)),
                'ema_12': float(latest.get('ema_12', 0)),
                'ema_26': float(latest.get('ema_26', 0)),
                'trend': self._get_ma_trend(latest),
                'golden_cross': bool(self._check_golden_cross(latest, previous)),
                'death_cross': bool(self._check_death_cross(latest, previous))
            },
            
            # ADX (Trend Strength)
            'adx': {
                'value': float(latest.get('adx', 25)),
                'strength': self._get_adx_strength(latest.get('adx', 25)),
                'trend_direction': self._get_adx_direction(latest),
                'trending': bool(latest.get('adx', 25) > 25)
            },
            
            # Stochastic
            'stochastic': {
                'k': float(latest.get('stoch_k', 50)),
                'd': float(latest.get('stoch_d', 50)),
                'signal': self._get_stochastic_signal(latest),
                'overbought': bool(latest.get('stoch_k', 50) > 80),
                'oversold': bool(latest.get('stoch_k', 50) < 20)
            },
            
            # Volume Analysis
            'volume': {
                'current': float(latest.get('volume', 0)),
                'sma': float(latest.get('volume_sma', 0)),
                'vwap': float(latest.get('vwap', 0)),
                'obv': float(latest.get('obv', 0)),
                'volume_trend': self._get_volume_trend(latest),
                'high_volume': bool(self._is_high_volume(latest))
            },
            
            # Overall Market Assessment
            'market_assessment': {
                'trend': self._assess_overall_trend(),
                'momentum': self._assess_momentum(),
                'volatility': self._assess_volatility(),
                'volume_confirmation': bool(self._assess_volume_confirmation()),
                'signal_strength': self._calculate_signal_strength()
            }
        }
    
    def _get_default_indicators(self) -> Dict[str, Any]:
        """Return default indicators when insufficient data"""
        return {
            'rsi': {'value': 50, 'signal': 'NEUTRAL', 'overbought': False, 'oversold': False, 'divergence': False},
            'macd': {'macd': 0, 'signal': 0, 'histogram': 0, 'signal_type': 'NEUTRAL', 'bullish_crossover': False, 'bearish_crossover': False},
            'bollinger_bands': {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0, 'percent_b': 0.5, 'squeeze': False, 'breakout': 'NONE'},
            'moving_averages': {'sma_20': 0, 'sma_50': 0, 'ema_12': 0, 'ema_26': 0, 'trend': 'NEUTRAL', 'golden_cross': False, 'death_cross': False},
            'adx': {'value': 25, 'strength': 'WEAK', 'trend_direction': 'NEUTRAL', 'trending': False},
            'stochastic': {'k': 50, 'd': 50, 'signal': 'NEUTRAL', 'overbought': False, 'oversold': False},
            'volume': {'current': 0, 'sma': 0, 'vwap': 0, 'obv': 0, 'volume_trend': 'NEUTRAL', 'high_volume': False},
            'market_assessment': {'trend': 'NEUTRAL', 'momentum': 'NEUTRAL', 'volatility': 'NORMAL', 'volume_confirmation': False, 'signal_strength': 0}
        }
    
    # Signal interpretation methods
    def _get_rsi_signal(self, rsi_value: float) -> str:
        if rsi_value > 70:
            return 'SELL'
        elif rsi_value < 30:
            return 'BUY'
        else:
            return 'NEUTRAL'
    
    def _get_macd_signal(self, latest: pd.Series, previous: pd.Series) -> str:
        macd_current = latest.get('macd', 0)
        signal_current = latest.get('macd_signal', 0)
        macd_prev = previous.get('macd', 0)
        signal_prev = previous.get('macd_signal', 0)
        
        if macd_current > signal_current and macd_prev <= signal_prev:
            return 'BUY'
        elif macd_current < signal_current and macd_prev >= signal_prev:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    def _is_macd_bullish_crossover(self, latest: pd.Series, previous: pd.Series) -> bool:
        return (latest.get('macd', 0) > latest.get('macd_signal', 0) and 
                previous.get('macd', 0) <= previous.get('macd_signal', 0))
    
    def _is_macd_bearish_crossover(self, latest: pd.Series, previous: pd.Series) -> bool:
        return (latest.get('macd', 0) < latest.get('macd_signal', 0) and 
                previous.get('macd', 0) >= previous.get('macd_signal', 0))
    
    def _check_bb_breakout(self, latest: pd.Series) -> str:
        close = latest.get('close', 0)
        upper = latest.get('bb_upper', 0)
        lower = latest.get('bb_lower', 0)
        
        if close > upper:
            return 'UPPER'
        elif close < lower:
            return 'LOWER'
        else:
            return 'NONE'
    
    def _get_ma_trend(self, latest: pd.Series) -> str:
        close = latest.get('close', 0)
        sma_20 = latest.get('sma_20', 0)
        sma_50 = latest.get('sma_50', 0)
        
        if close > sma_20 > sma_50:
            return 'BULLISH'
        elif close < sma_20 < sma_50:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _check_golden_cross(self, latest: pd.Series, previous: pd.Series) -> bool:
        return (latest.get('sma_20', 0) > latest.get('sma_50', 0) and 
                previous.get('sma_20', 0) <= previous.get('sma_50', 0))
    
    def _check_death_cross(self, latest: pd.Series, previous: pd.Series) -> bool:
        return (latest.get('sma_20', 0) < latest.get('sma_50', 0) and 
                previous.get('sma_20', 0) >= previous.get('sma_50', 0))
    
    def _get_adx_strength(self, adx_value: float) -> str:
        if adx_value > 50:
            return 'VERY_STRONG'
        elif adx_value > 25:
            return 'STRONG'
        elif adx_value > 20:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _get_adx_direction(self, latest: pd.Series) -> str:
        pos_di = latest.get('adx_pos', 0)
        neg_di = latest.get('adx_neg', 0)
        
        if pos_di > neg_di:
            return 'BULLISH'
        elif neg_di > pos_di:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _get_stochastic_signal(self, latest: pd.Series) -> str:
        k = latest.get('stoch_k', 50)
        d = latest.get('stoch_d', 50)
        
        if k > 80 and d > 80:
            return 'SELL'
        elif k < 20 and d < 20:
            return 'BUY'
        else:
            return 'NEUTRAL'
    
    def _get_volume_trend(self, latest: pd.Series) -> str:
        current_volume = latest.get('volume', 0)
        avg_volume = latest.get('volume_sma', 0)
        
        if current_volume > avg_volume * 1.5:
            return 'HIGH'
        elif current_volume < avg_volume * 0.5:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def _is_high_volume(self, latest: pd.Series) -> bool:
        current_volume = latest.get('volume', 0)
        avg_volume = latest.get('volume_sma', 0)
        return current_volume > avg_volume * 1.2
    
    def _check_rsi_divergence(self) -> bool:
        # Simplified divergence check - would need more sophisticated implementation
        if len(self.df) < 20:
            return False
        
        recent_rsi = self.df['rsi'].tail(10)
        recent_close = self.df['close'].tail(10)
        
        # Basic divergence detection (simplified)
        rsi_trend = recent_rsi.iloc[-1] - recent_rsi.iloc[0]
        price_trend = recent_close.iloc[-1] - recent_close.iloc[0]
        
        return (rsi_trend > 0 and price_trend < 0) or (rsi_trend < 0 and price_trend > 0)
    
    def _assess_overall_trend(self) -> str:
        if len(self.df) == 0:
            return 'NEUTRAL'
        
        latest = self.df.iloc[-1]
        
        # Multiple timeframe trend analysis
        bullish_signals = 0
        bearish_signals = 0
        
        # MA trend
        ma_trend = self._get_ma_trend(latest)
        if ma_trend == 'BULLISH':
            bullish_signals += 1
        elif ma_trend == 'BEARISH':
            bearish_signals += 1
        
        # ADX direction
        adx_direction = self._get_adx_direction(latest)
        if adx_direction == 'BULLISH':
            bullish_signals += 1
        elif adx_direction == 'BEARISH':
            bearish_signals += 1
        
        # Price vs Bollinger Bands
        close = latest.get('close', 0)
        bb_middle = latest.get('bb_middle', 0)
        if close > bb_middle:
            bullish_signals += 1
        elif close < bb_middle:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            return 'BULLISH'
        elif bearish_signals > bullish_signals:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _assess_momentum(self) -> str:
        if len(self.df) == 0:
            return 'NEUTRAL'
        
        latest = self.df.iloc[-1]
        
        rsi = latest.get('rsi', 50)
        macd_histogram = latest.get('macd_histogram', 0)
        stoch_k = latest.get('stoch_k', 50)
        
        momentum_score = 0
        
        if rsi > 60:
            momentum_score += 1
        elif rsi < 40:
            momentum_score -= 1
        
        if macd_histogram > 0:
            momentum_score += 1
        elif macd_histogram < 0:
            momentum_score -= 1
        
        if stoch_k > 60:
            momentum_score += 1
        elif stoch_k < 40:
            momentum_score -= 1
        
        if momentum_score > 1:
            return 'BULLISH'
        elif momentum_score < -1:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _assess_volatility(self) -> str:
        if len(self.df) == 0:
            return 'NORMAL'
        
        latest = self.df.iloc[-1]
        bb_width = latest.get('bb_width', 0.1)
        
        if bb_width > 0.2:
            return 'HIGH'
        elif bb_width < 0.05:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def _assess_volume_confirmation(self) -> bool:
        if len(self.df) == 0:
            return False
        
        latest = self.df.iloc[-1]
        return self._is_high_volume(latest)
    
    def _calculate_signal_strength(self) -> int:
        """Calculate overall signal strength from -5 to +5"""
        if len(self.df) == 0:
            return 0
        
        latest = self.df.iloc[-1]
        previous = self.df.iloc[-2] if len(self.df) > 1 else latest
        
        strength = 0
        
        # RSI contribution
        rsi_signal = self._get_rsi_signal(latest.get('rsi', 50))
        if rsi_signal == 'BUY':
            strength += 1
        elif rsi_signal == 'SELL':
            strength -= 1
        
        # MACD contribution
        macd_signal = self._get_macd_signal(latest, previous)
        if macd_signal == 'BUY':
            strength += 1
        elif macd_signal == 'SELL':
            strength -= 1
        
        # Moving Average contribution
        ma_trend = self._get_ma_trend(latest)
        if ma_trend == 'BULLISH':
            strength += 1
        elif ma_trend == 'BEARISH':
            strength -= 1
        
        # ADX contribution (trend strength)
        adx_direction = self._get_adx_direction(latest)
        adx_strength = self._get_adx_strength(latest.get('adx', 25))
        if adx_direction == 'BULLISH' and adx_strength in ['STRONG', 'VERY_STRONG']:
            strength += 1
        elif adx_direction == 'BEARISH' and adx_strength in ['STRONG', 'VERY_STRONG']:
            strength -= 1
        
        # Volume confirmation
        if self._is_high_volume(latest):
            if strength > 0:
                strength += 1
            elif strength < 0:
                strength -= 1
        
        return max(-5, min(5, strength))


def calculate_professional_indicators(candle_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate professional technical indicators for given candle data
    
    Args:
        candle_data: List of OHLCV candle data
        
    Returns:
        Dictionary containing all calculated indicators
    """
    try:
        indicators = TechnicalIndicators(candle_data)
        return indicators.get_latest_indicators()
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return TechnicalIndicators([])._get_default_indicators()