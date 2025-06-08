"""
Machine Learning & AI API Router
Endpoints for AI-based signal generation and model training
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.ml_signal_generator import (
    generate_ai_signal,
    train_ai_models,
    ml_signal_generator
)

router = APIRouter(prefix="/api/ai", tags=["ai-ml"])


class AISignalRequest(BaseModel):
    symbol: str
    interval: str = "1h"


class TrainingRequest(BaseModel):
    symbols: Optional[List[str]] = None
    days: int = 90
    background: bool = True


class ModelStatusResponse(BaseModel):
    ml_available: bool
    models_trained: bool
    available_models: List[str]
    training_in_progress: bool


@router.get("/signal/{symbol}")
async def get_ai_signal(symbol: str, interval: str = "1h"):
    """
    Get AI-generated trading signal for a symbol
    
    This endpoint uses machine learning models to analyze:
    - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
    - Price action patterns
    - Market regime detection
    - Risk assessment
    - Feature importance analysis
    """
    try:
        ai_signal = await generate_ai_signal(symbol, interval)
        
        return {
            "success": True,
            "data": ai_signal
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal")
async def get_ai_signal_post(request: AISignalRequest):
    """
    Get AI-generated trading signal (POST version)
    
    Allows for more complex request parameters
    """
    try:
        ai_signal = await generate_ai_signal(request.symbol, request.interval)
        
        return {
            "success": True,
            "data": ai_signal
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/batch")
async def get_batch_ai_signals(symbols: str, interval: str = "1h"):
    """
    Get AI signals for multiple symbols
    
    Args:
        symbols: Comma-separated list of symbols (e.g., "BTCUSDT,ETHUSDT,ADAUSDT")
        interval: Time interval for analysis
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        results = {}
        
        for symbol in symbol_list:
            try:
                ai_signal = await generate_ai_signal(symbol, interval)
                results[symbol] = ai_signal
            except Exception as e:
                results[symbol] = {
                    'error': str(e),
                    'symbol': symbol,
                    'ai_signal': 'HOLD',
                    'ai_confidence': 0
                }
        
        return {
            "success": True,
            "data": {
                "signals": results,
                "total_symbols": len(symbol_list),
                "successful": len([r for r in results.values() if 'error' not in r])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/status")
async def get_model_status():
    """
    Get current ML model status and capabilities
    """
    try:
        return {
            "success": True,
            "data": {
                "ml_available": ml_signal_generator.ML_AVAILABLE if hasattr(ml_signal_generator, 'ML_AVAILABLE') else False,
                "models_trained": ml_signal_generator.is_trained,
                "available_models": list(ml_signal_generator.models.keys()) if ml_signal_generator.models else [],
                "model_path": ml_signal_generator.model_path,
                "training_features": [
                    "RSI", "MACD", "Bollinger Bands", "ADX", "Stochastic",
                    "Price Action", "Volume Analysis", "Momentum", "Volatility",
                    "Support/Resistance", "Time Features"
                ],
                "supported_intervals": ["1h", "4h", "1d"],
                "market_regimes": ["TRENDING", "RANGING", "VOLATILE"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/train")
async def train_models(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Train ML models on historical data
    
    This process:
    1. Collects historical price data for specified symbols
    2. Extracts technical features (21 different indicators)
    3. Creates labels based on future price movements
    4. Trains multiple ML models (Random Forest, Gradient Boosting, etc.)
    5. Saves trained models for future use
    
    Args:
        symbols: List of symbols to train on (default: major cryptos)
        days: Number of days of historical data (default: 90)
        background: Run training in background (default: True)
    """
    try:
        if request.background:
            # Run training in background
            background_tasks.add_task(
                _background_training,
                request.symbols,
                request.days
            )
            
            return {
                "success": True,
                "data": {
                    "message": "Model training started in background",
                    "symbols": request.symbols or ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT"],
                    "training_days": request.days,
                    "estimated_time_minutes": len(request.symbols or 5) * 2,
                    "status": "training_started"
                }
            }
        else:
            # Run training synchronously (may take several minutes)
            result = await train_ai_models(request.symbols, request.days)
            
            return {
                "success": True,
                "data": result
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _background_training(symbols: Optional[List[str]], days: int):
    """Background task for model training"""
    try:
        result = await train_ai_models(symbols, days)
        # In a real application, you might want to store this result
        # or send a notification when training is complete
        print(f"Background training completed: {result}")
    except Exception as e:
        print(f"Background training failed: {e}")


@router.get("/analysis/market-regime/{symbol}")
async def analyze_market_regime(symbol: str, interval: str = "1h"):
    """
    Analyze current market regime for a symbol
    
    Returns:
        - Market regime (TRENDING, RANGING, VOLATILE)
        - Trend strength and direction
        - Volatility metrics
        - Regime confidence
    """
    try:
        ai_signal = await generate_ai_signal(symbol, interval)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "market_regime": ai_signal.get('market_regime', 'UNKNOWN'),
                "risk_score": ai_signal.get('risk_score', 50),
                "confidence": ai_signal.get('ai_confidence', 50),
                "analysis_timestamp": ai_signal.get('timestamp'),
                "regime_indicators": {
                    "volatility": "High" if ai_signal.get('risk_score', 50) > 70 else "Normal",
                    "trend_strength": "Strong" if ai_signal.get('ai_confidence', 50) > 75 else "Weak",
                    "market_structure": ai_signal.get('market_regime', 'UNKNOWN')
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/feature-importance/{symbol}")
async def get_feature_importance(symbol: str, interval: str = "1h"):
    """
    Get feature importance analysis for AI signal generation
    
    Shows which technical indicators are most influential
    in the current market conditions for the given symbol
    """
    try:
        ai_signal = await generate_ai_signal(symbol, interval)
        
        feature_importance = ai_signal.get('feature_importance', {})
        
        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "feature_importance": dict(sorted_features),
                "top_features": sorted_features[:5],
                "analysis_timestamp": ai_signal.get('timestamp'),
                "total_features": len(feature_importance),
                "interpretation": {
                    "most_important": sorted_features[0][0] if sorted_features else "unknown",
                    "importance_score": sorted_features[0][1] if sorted_features else 0,
                    "signal_drivers": [f[0] for f in sorted_features[:3]]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/risk-assessment/{symbol}")
async def get_risk_assessment(symbol: str, interval: str = "1h"):
    """
    Get comprehensive risk assessment for a symbol
    
    Analyzes:
    - Market volatility
    - Signal confidence
    - Market regime risks
    - Position sizing recommendations
    """
    try:
        ai_signal = await generate_ai_signal(symbol, interval)
        
        risk_score = ai_signal.get('risk_score', 50)
        confidence = ai_signal.get('ai_confidence', 50)
        market_regime = ai_signal.get('market_regime', 'UNKNOWN')
        
        # Risk level classification
        if risk_score > 80:
            risk_level = "VERY_HIGH"
            recommendation = "Avoid trading or use very small position sizes"
        elif risk_score > 60:
            risk_level = "HIGH"
            recommendation = "Use reduced position sizes and tight stops"
        elif risk_score > 40:
            risk_level = "MEDIUM"
            recommendation = "Normal position sizing with standard risk management"
        elif risk_score > 20:
            risk_level = "LOW"
            recommendation = "Favorable conditions for trading"
        else:
            risk_level = "VERY_LOW"
            recommendation = "Excellent conditions for larger positions"
        
        # Position sizing recommendation
        base_position = 2.0  # 2% of portfolio
        risk_multiplier = max(0.1, min(2.0, (100 - risk_score) / 50))
        recommended_position = base_position * risk_multiplier
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence": confidence,
                "market_regime": market_regime,
                "recommendation": recommendation,
                "position_sizing": {
                    "recommended_percentage": round(recommended_position, 2),
                    "risk_multiplier": round(risk_multiplier, 2),
                    "max_recommended": "2.0%",
                    "reasoning": f"Based on {risk_level.lower()} risk and {confidence}% confidence"
                },
                "risk_factors": {
                    "volatility": "High" if risk_score > 70 else "Normal",
                    "market_regime": market_regime,
                    "signal_quality": "High" if confidence > 75 else "Medium" if confidence > 50 else "Low"
                },
                "analysis_timestamp": ai_signal.get('timestamp')
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/performance")
async def get_model_performance():
    """
    Get ML model performance metrics and statistics
    """
    try:
        return {
            "success": True,
            "data": {
                "models_available": ml_signal_generator.is_trained,
                "model_types": list(ml_signal_generator.models.keys()) if ml_signal_generator.models else [],
                "training_status": "trained" if ml_signal_generator.is_trained else "not_trained",
                "performance_metrics": {
                    "note": "Performance metrics available after training completion",
                    "features_used": 21,
                    "prediction_classes": ["BUY", "SELL", "HOLD"],
                    "ensemble_method": "voting_classifier"
                },
                "model_info": {
                    "random_forest": "100 trees, max_depth=10",
                    "gradient_boosting": "100 estimators, learning_rate=0.1",
                    "logistic_regression": "L2 regularization, balanced classes",
                    "svm": "RBF kernel, probability estimates enabled"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))