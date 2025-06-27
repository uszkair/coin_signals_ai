"""
Machine Learning Signal Generator
Advanced AI-based trading signal generation using multiple ML models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import os
from dataclasses import dataclass

# ML imports (will be available after installation)
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available. Using fallback signal generation.")

from app.services.technical_indicators import calculate_professional_indicators
from app.utils.price_data import get_historical_data

logger = logging.getLogger(__name__)


@dataclass
class MLSignalResult:
    """ML Signal Generation Result"""
    signal: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    probability_buy: float
    probability_sell: float
    probability_hold: float
    model_predictions: Dict[str, Any]
    feature_importance: Dict[str, float]
    market_regime: str  # TRENDING, RANGING, VOLATILE
    risk_score: float  # 0-100


class MLSignalGenerator:
    """Advanced Machine Learning Signal Generator"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
        
        # Initialize models
        if ML_AVAILABLE:
            self._initialize_models()
            self._load_models()
        
    def _initialize_models(self):
        """Initialize ML models"""
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42,
                class_weight='balanced'
            )
        }
        
        self.scalers = {
            name: StandardScaler() for name in self.models.keys()
        }
    
    async def generate_ml_signal(self, symbol: str, interval: str = "1h") -> MLSignalResult:
        """
        Generate ML-based trading signal
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            interval: Time interval (1h, 4h, 1d)
            
        Returns:
            MLSignalResult with predictions and analysis
        """
        try:
            # Get historical data for feature engineering
            candles = await get_historical_data(symbol, interval, days=30)
            
            if len(candles) < 50:
                return self._fallback_signal(symbol)
            
            # Extract features
            features = await self._extract_features(candles)
            
            if not ML_AVAILABLE or not self.is_trained:
                return await self._generate_ensemble_signal(features, symbol)
            
            # Generate predictions from all models
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.models.items():
                try:
                    # Scale features
                    scaled_features = self.scalers[model_name].transform([features])
                    
                    # Get prediction and probabilities
                    pred = model.predict(scaled_features)[0]
                    proba = model.predict_proba(scaled_features)[0]
                    
                    predictions[model_name] = pred
                    probabilities[model_name] = proba
                    
                except Exception as e:
                    logger.warning(f"Error with model {model_name}: {e}")
                    continue
            
            # Ensemble prediction
            ensemble_result = self._ensemble_predictions(predictions, probabilities)
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(features)
            
            # Determine market regime
            market_regime = self._determine_market_regime(candles)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(features, ensemble_result)
            
            return MLSignalResult(
                signal=ensemble_result['signal'],
                confidence=ensemble_result['confidence'],
                probability_buy=ensemble_result['prob_buy'],
                probability_sell=ensemble_result['prob_sell'],
                probability_hold=ensemble_result['prob_hold'],
                model_predictions=predictions,
                feature_importance=feature_importance,
                market_regime=market_regime,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"Error generating ML signal: {e}")
            return self._fallback_signal(symbol)
    
    async def _extract_features(self, candles: List[Dict]) -> List[float]:
        """Extract ML features from price data"""
        # Calculate technical indicators
        indicators = calculate_professional_indicators(candles)
        
        # Price-based features
        df = pd.DataFrame(candles)
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['price_ma_ratio'] = df['close'] / df['close'].rolling(20).mean()
        
        # Technical indicator features
        rsi = indicators.get('rsi', {}).get('value', 50)
        macd = indicators.get('macd', {}).get('macd', 0)
        macd_signal = indicators.get('macd', {}).get('signal', 0)
        bb_percent = indicators.get('bollinger_bands', {}).get('percent_b', 0.5)
        bb_width = indicators.get('bollinger_bands', {}).get('width', 0.1)
        adx = indicators.get('adx', {}).get('value', 25)
        stoch_k = indicators.get('stochastic', {}).get('k', 50)
        volume_trend = 1 if indicators.get('volume', {}).get('volume_trend') == 'HIGH' else 0
        
        # Price action features
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        price_change = (latest['close'] - prev['close']) / prev['close']
        volume_change = (latest['volume'] - prev['volume']) / prev['volume'] if prev['volume'] > 0 else 0
        
        # Trend features
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
        trend_strength = (latest['close'] - sma_50) / sma_50 if sma_50 > 0 else 0
        
        # Momentum features
        momentum_5 = (latest['close'] - df['close'].iloc[-6]) / df['close'].iloc[-6] if len(df) > 5 else 0
        momentum_10 = (latest['close'] - df['close'].iloc[-11]) / df['close'].iloc[-11] if len(df) > 10 else 0
        
        # Volatility features
        volatility_20 = df['returns'].rolling(20).std().iloc[-1]
        volatility_ratio = volatility_20 / df['returns'].rolling(50).std().iloc[-1] if len(df) >= 50 else 1
        
        # Support/Resistance features
        high_20 = df['high'].rolling(20).max().iloc[-1]
        low_20 = df['low'].rolling(20).min().iloc[-1]
        price_position = (latest['close'] - low_20) / (high_20 - low_20) if high_20 != low_20 else 0.5
        
        # Time-based features
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        features = [
            # Technical indicators
            rsi / 100,  # Normalize to 0-1
            macd,
            macd_signal,
            bb_percent,
            bb_width,
            adx / 100,
            stoch_k / 100,
            volume_trend,
            
            # Price action
            price_change,
            volume_change,
            trend_strength,
            
            # Momentum
            momentum_5,
            momentum_10,
            
            # Volatility
            volatility_20,
            volatility_ratio,
            
            # Support/Resistance
            price_position,
            
            # Market structure
            (latest['close'] - sma_20) / sma_20 if sma_20 > 0 else 0,  # Distance from SMA20
            (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0,  # SMA slope
            
            # Time features
            hour / 24,
            day_of_week / 7,
            
            # Volume features
            latest['volume'] / df['volume'].rolling(20).mean().iloc[-1] if df['volume'].rolling(20).mean().iloc[-1] > 0 else 1
        ]
        
        # Handle NaN values
        features = [0 if pd.isna(x) or np.isinf(x) else float(x) for x in features]
        
        return features
    
    async def _generate_ensemble_signal(self, features: List[float], symbol: str) -> MLSignalResult:
        """Generate signal using ensemble of simple rules when ML is not available"""
        
        # Simple rule-based ensemble
        signals = []
        confidences = []
        
        # RSI-based signal
        rsi = features[0] * 100
        if rsi > 70:
            signals.append('SELL')
            confidences.append(min(80, (rsi - 70) * 2 + 60))
        elif rsi < 30:
            signals.append('BUY')
            confidences.append(min(80, (30 - rsi) * 2 + 60))
        else:
            signals.append('HOLD')
            confidences.append(50)
        
        # Trend-based signal
        trend_strength = features[10]
        if trend_strength > 0.02:
            signals.append('BUY')
            confidences.append(min(75, trend_strength * 1000 + 60))
        elif trend_strength < -0.02:
            signals.append('SELL')
            confidences.append(min(75, abs(trend_strength) * 1000 + 60))
        else:
            signals.append('HOLD')
            confidences.append(50)
        
        # MACD-based signal
        macd = features[1]
        macd_signal = features[2]
        if macd > macd_signal and macd > 0:
            signals.append('BUY')
            confidences.append(65)
        elif macd < macd_signal and macd < 0:
            signals.append('SELL')
            confidences.append(65)
        else:
            signals.append('HOLD')
            confidences.append(50)
        
        # Ensemble decision
        buy_votes = signals.count('BUY')
        sell_votes = signals.count('SELL')
        hold_votes = signals.count('HOLD')
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            final_signal = 'BUY'
            confidence = np.mean([c for s, c in zip(signals, confidences) if s == 'BUY'])
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_signal = 'SELL'
            confidence = np.mean([c for s, c in zip(signals, confidences) if s == 'SELL'])
        else:
            final_signal = 'HOLD'
            confidence = np.mean(confidences)
        
        return MLSignalResult(
            signal=final_signal,
            confidence=confidence,
            probability_buy=buy_votes / len(signals),
            probability_sell=sell_votes / len(signals),
            probability_hold=hold_votes / len(signals),
            model_predictions={'ensemble_rules': final_signal},
            feature_importance={'rsi': 0.3, 'trend': 0.4, 'macd': 0.3},
            market_regime='UNKNOWN',
            risk_score=50.0
        )
    
    def _ensemble_predictions(self, predictions: Dict, probabilities: Dict) -> Dict[str, Any]:
        """Combine predictions from multiple models"""
        if not predictions:
            return {
                'signal': 'HOLD',
                'confidence': 50.0,
                'prob_buy': 0.33,
                'prob_sell': 0.33,
                'prob_hold': 0.34
            }
        
        # Count votes
        votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        total_proba = np.zeros(3)  # [BUY, SELL, HOLD]
        
        for model_name, pred in predictions.items():
            votes[pred] += 1
            if model_name in probabilities:
                total_proba += probabilities[model_name]
        
        # Average probabilities
        avg_proba = total_proba / len(predictions)
        
        # Determine final signal
        max_votes = max(votes.values())
        final_signal = [k for k, v in votes.items() if v == max_votes][0]
        
        # Calculate confidence based on agreement
        agreement = max_votes / len(predictions)
        confidence = agreement * 100
        
        return {
            'signal': final_signal,
            'confidence': confidence,
            'prob_buy': avg_proba[0],
            'prob_sell': avg_proba[1],
            'prob_hold': avg_proba[2]
        }
    
    def _calculate_feature_importance(self, features: List[float]) -> Dict[str, float]:
        """Calculate feature importance (simplified)"""
        feature_names = [
            'rsi', 'macd', 'macd_signal', 'bb_percent', 'bb_width',
            'adx', 'stoch_k', 'volume_trend', 'price_change', 'volume_change',
            'trend_strength', 'momentum_5', 'momentum_10', 'volatility_20',
            'volatility_ratio', 'price_position', 'sma_distance', 'sma_slope',
            'hour', 'day_of_week', 'volume_ratio'
        ]
        
        # Simple importance based on feature magnitude
        importances = {}
        for i, name in enumerate(feature_names[:len(features)]):
            importances[name] = abs(features[i]) if i < len(features) else 0
        
        # Normalize
        total = sum(importances.values())
        if total > 0:
            importances = {k: v/total for k, v in importances.items()}
        
        return importances
    
    def _determine_market_regime(self, candles: List[Dict]) -> str:
        """Determine current market regime"""
        df = pd.DataFrame(candles)
        
        # Calculate volatility
        returns = df['close'].pct_change()
        volatility = returns.rolling(20).std().iloc[-1]
        
        # Calculate trend strength
        sma_20 = df['close'].rolling(20).mean()
        trend_slope = (sma_20.iloc[-1] - sma_20.iloc[-10]) / sma_20.iloc[-10] if len(sma_20) > 10 else 0
        
        if volatility > 0.03:  # High volatility threshold
            return 'VOLATILE'
        elif abs(trend_slope) > 0.02:  # Strong trend threshold
            return 'TRENDING'
        else:
            return 'RANGING'
    
    def _calculate_risk_score(self, features: List[float], ensemble_result: Dict) -> float:
        """Calculate risk score for the signal"""
        # Base risk from volatility
        volatility = features[13] if len(features) > 13 else 0.02
        volatility_risk = min(50, volatility * 1000)
        
        # Confidence risk (lower confidence = higher risk)
        confidence_risk = 100 - ensemble_result['confidence']
        
        # Market structure risk
        trend_strength = abs(features[10]) if len(features) > 10 else 0
        structure_risk = 30 if trend_strength < 0.01 else 10  # Higher risk in ranging markets
        
        # Combine risks
        total_risk = (volatility_risk * 0.4 + confidence_risk * 0.4 + structure_risk * 0.2)
        
        return min(100, max(0, total_risk))
    
    def _fallback_signal(self, symbol: str) -> MLSignalResult:
        """Fallback signal when ML is not available"""
        return MLSignalResult(
            signal='HOLD',
            confidence=50.0,
            probability_buy=0.33,
            probability_sell=0.33,
            probability_hold=0.34,
            model_predictions={'fallback': 'HOLD'},
            feature_importance={'technical': 1.0},
            market_regime='UNKNOWN',
            risk_score=50.0
        )
    
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            for model_name in self.models.keys():
                model_file = os.path.join(self.model_path, f"{model_name}.pkl")
                scaler_file = os.path.join(self.model_path, f"{model_name}_scaler.pkl")
                
                if os.path.exists(model_file) and os.path.exists(scaler_file):
                    self.models[model_name] = joblib.load(model_file)
                    self.scalers[model_name] = joblib.load(scaler_file)
                    self.is_trained = True
                    logger.info(f"Loaded model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load models: {e}")
    
    async def train_models(self, symbols: List[str], days: int = 90):
        """Train ML models on historical data"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available for training")
            return False
        
        try:
            # Collect training data
            X, y = await self._prepare_training_data(symbols, days)
            
            if len(X) < 100:
                logger.warning("Insufficient training data")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train models
            for model_name, model in self.models.items():
                logger.info(f"Training {model_name}...")
                
                # Scale features
                scaler = self.scalers[model_name]
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                logger.info(f"{model_name} accuracy: {accuracy:.3f}")
                
                # Save model
                joblib.dump(model, os.path.join(self.model_path, f"{model_name}.pkl"))
                joblib.dump(scaler, os.path.join(self.model_path, f"{model_name}_scaler.pkl"))
            
            self.is_trained = True
            logger.info("Model training completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    async def _prepare_training_data(self, symbols: List[str], days: int) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical prices"""
        X, y = [], []
        
        for symbol in symbols:
            try:
                candles = await get_historical_data(symbol, "1h", days=days)
                
                if len(candles) < 50:
                    continue
                
                # Generate features and labels for each time point
                for i in range(50, len(candles) - 24):  # Leave 24h for future price calculation
                    current_candles = candles[:i+1]
                    features = await self._extract_features(current_candles)
                    
                    # Calculate future return (24h ahead)
                    current_price = candles[i]['close']
                    future_price = candles[i + 24]['close']
                    future_return = (future_price - current_price) / current_price
                    
                    # Create label based on future return
                    if future_return > 0.02:  # 2% gain
                        label = 'BUY'
                    elif future_return < -0.02:  # 2% loss
                        label = 'SELL'
                    else:
                        label = 'HOLD'
                    
                    X.append(features)
                    y.append(label)
                    
            except Exception as e:
                logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        if not X:
            return np.array([]), np.array([])
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        return np.array(X), y_encoded


# Global ML signal generator instance
ml_signal_generator = MLSignalGenerator()


async def generate_ai_signal(symbol: str, interval: str = "1h") -> Dict[str, Any]:
    """
    Generate AI-based trading signal
    
    Args:
        symbol: Trading symbol
        interval: Time interval
        
    Returns:
        AI signal with ML predictions and analysis
    """
    try:
        ml_result = await ml_signal_generator.generate_ml_signal(symbol, interval)
        
        return {
            'symbol': symbol,
            'interval': interval,
            'ai_signal': ml_result.signal,
            'ai_confidence': ml_result.confidence,
            'probabilities': {
                'buy': ml_result.probability_buy,
                'sell': ml_result.probability_sell,
                'hold': ml_result.probability_hold
            },
            'model_predictions': ml_result.model_predictions,
            'feature_importance': ml_result.feature_importance,
            'market_regime': ml_result.market_regime,
            'risk_score': ml_result.risk_score,
            'timestamp': datetime.now().isoformat(),
            'ml_available': ML_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"Error generating AI signal: {e}")
        return {
            'symbol': symbol,
            'interval': interval,
            'ai_signal': 'HOLD',
            'ai_confidence': 50.0,
            'error': str(e),
            'ml_available': False
        }


async def train_ai_models(symbols: List[str] = None, days: int = 90) -> Dict[str, Any]:
    """
    Train AI models on historical data
    
    Args:
        symbols: List of symbols to train on
        days: Number of days of historical data
        
    Returns:
        Training results
    """
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']
    
    try:
        success = await ml_signal_generator.train_models(symbols, days)
        
        return {
            'success': success,
            'symbols_trained': symbols,
            'training_days': days,
            'ml_available': ML_AVAILABLE,
            'models_trained': list(ml_signal_generator.models.keys()) if success else [],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error training AI models: {e}")
        return {
            'success': False,
            'error': str(e),
            'ml_available': ML_AVAILABLE
        }