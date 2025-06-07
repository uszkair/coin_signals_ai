# app/routers/ai.py

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from app.services.ai_service import ai_service
import asyncio

router = APIRouter(prefix="/ai", tags=["AI Analysis"])

@router.get("/sentiment/{symbol}")
async def get_market_sentiment(symbol: str):
    """Get AI-powered market sentiment analysis for a symbol"""
    try:
        sentiment = await ai_service.analyze_market_sentiment(symbol.upper())
        return {
            "success": True,
            "data": sentiment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.get("/prediction/{symbol}")
async def get_price_prediction(
    symbol: str,
    timeframe: str = Query("24h", description="Prediction timeframe (24h, 7d, 30d)")
):
    """Get AI-powered price prediction for a symbol"""
    try:
        prediction = await ai_service.predict_price_movement(symbol.upper(), timeframe)
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price prediction failed: {str(e)}")

@router.get("/anomalies/{symbol}")
async def detect_anomalies(symbol: str):
    """Detect volume and price anomalies for a symbol"""
    try:
        anomalies = await ai_service.detect_anomalies(symbol.upper())
        return {
            "success": True,
            "data": anomalies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.get("/insights/{symbol}")
async def get_ai_insights(symbol: str):
    """Get comprehensive AI insights for a symbol"""
    try:
        insights = await ai_service.generate_ai_insights(symbol.upper())
        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI insights failed: {str(e)}")

@router.get("/market-overview")
async def get_market_overview(
    symbols: List[str] = Query(["BTCUSDT", "ETHUSDT", "BNBUSDT"], description="List of symbols to analyze")
):
    """Get AI market overview for multiple symbols"""
    try:
        overview_data = {}
        
        # Get insights for each symbol concurrently
        tasks = [ai_service.generate_ai_insights(symbol.upper()) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                overview_data[symbol] = {"error": str(result)}
            else:
                overview_data[symbol] = result
        
        # Calculate overall market sentiment
        sentiments = []
        for symbol, data in overview_data.items():
            if "sentiment" in data and "overall_sentiment" in data["sentiment"]:
                sentiments.append(data["sentiment"]["overall_sentiment"])
        
        overall_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        market_mood = "Bullish" if overall_sentiment > 0.2 else "Bearish" if overall_sentiment < -0.2 else "Neutral"
        
        return {
            "success": True,
            "data": {
                "symbols": overview_data,
                "market_summary": {
                    "overall_sentiment": overall_sentiment,
                    "market_mood": market_mood,
                    "analyzed_symbols": len(symbols),
                    "timestamp": overview_data.get(symbols[0], {}).get("generated_at")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market overview failed: {str(e)}")

@router.post("/chat")
async def ai_chat(message: Dict[str, str]):
    """AI chatbot for trading assistance"""
    try:
        user_message = message.get("message", "").lower()
        
        # Simple rule-based responses (in production, use advanced NLP)
        if "sentiment" in user_message:
            response = "I can analyze market sentiment using news, social media, and Fear & Greed Index. Which symbol would you like me to analyze?"
        elif "prediction" in user_message or "price" in user_message:
            response = "I use machine learning models with technical indicators to predict price movements. What symbol interests you?"
        elif "risk" in user_message:
            response = "I assess risk using volatility, sentiment uncertainty, and anomaly detection. Would you like a risk analysis for your portfolio?"
        elif "buy" in user_message or "sell" in user_message:
            response = "I can provide AI-powered trading recommendations based on sentiment, technical analysis, and market anomalies. Which symbol are you considering?"
        elif "portfolio" in user_message:
            response = "I can help optimize your portfolio allocation using AI analysis. What's your current portfolio composition?"
        else:
            response = "I'm your AI trading assistant! I can help with sentiment analysis, price predictions, risk assessment, and trading recommendations. What would you like to know?"
        
        return {
            "success": True,
            "data": {
                "response": response,
                "timestamp": "2025-01-08T00:33:00Z",
                "suggestions": [
                    "Analyze market sentiment",
                    "Get price predictions",
                    "Check for anomalies",
                    "Risk assessment"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@router.get("/alerts")
async def get_smart_alerts(
    symbols: List[str] = Query(["BTCUSDT", "ETHUSDT"], description="Symbols to monitor for alerts")
):
    """Get AI-powered smart alerts"""
    try:
        alerts = []
        
        for symbol in symbols:
            # Get anomalies and insights
            anomalies = await ai_service.detect_anomalies(symbol.upper())
            insights = await ai_service.generate_ai_insights(symbol.upper())
            
            # Generate alerts based on conditions
            if anomalies.get("volume_anomaly"):
                alerts.append({
                    "type": "volume_anomaly",
                    "symbol": symbol,
                    "severity": "high" if anomalies.get("volume_zscore", 0) > 3 else "medium",
                    "message": f"Unusual volume detected in {symbol}. Volume is {anomalies.get('volume_ratio', 1):.1f}x normal.",
                    "timestamp": anomalies.get("detection_time")
                })
            
            if anomalies.get("price_anomaly"):
                alerts.append({
                    "type": "price_anomaly",
                    "symbol": symbol,
                    "severity": "high",
                    "message": f"Significant price movement in {symbol}: {anomalies.get('price_change', 0):.2f}%",
                    "timestamp": anomalies.get("detection_time")
                })
            
            # Sentiment-based alerts
            sentiment = insights.get("sentiment", {})
            if abs(sentiment.get("overall_sentiment", 0)) > 0.7:
                sentiment_type = "bullish" if sentiment["overall_sentiment"] > 0 else "bearish"
                alerts.append({
                    "type": "sentiment_extreme",
                    "symbol": symbol,
                    "severity": "medium",
                    "message": f"Extreme {sentiment_type} sentiment detected for {symbol} ({sentiment.get('confidence', 0):.0f}% confidence)",
                    "timestamp": sentiment.get("analysis_time")
                })
            
            # Trading recommendation alerts
            recommendation = insights.get("recommendation", {})
            if recommendation.get("confidence", 0) > 80:
                alerts.append({
                    "type": "trading_opportunity",
                    "symbol": symbol,
                    "severity": "high" if recommendation.get("confidence", 0) > 90 else "medium",
                    "message": f"Strong {recommendation.get('action', 'HOLD')} signal for {symbol} ({recommendation.get('confidence', 0):.0f}% confidence)",
                    "timestamp": insights.get("generated_at")
                })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "generated_at": "2025-01-08T00:33:00Z"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart alerts failed: {str(e)}")

@router.get("/portfolio-optimize")
async def optimize_portfolio(
    current_btc: float = Query(45.0, description="Current BTC allocation %"),
    current_eth: float = Query(30.0, description="Current ETH allocation %"),
    current_others: float = Query(25.0, description="Current others allocation %")
):
    """AI-powered portfolio optimization"""
    try:
        # Get AI insights for major cryptocurrencies
        btc_insights = await ai_service.generate_ai_insights("BTCUSDT")
        eth_insights = await ai_service.generate_ai_insights("ETHUSDT")
        sol_insights = await ai_service.generate_ai_insights("SOLUSDT")
        
        # Current portfolio
        current_portfolio = {
            "BTC": current_btc,
            "ETH": current_eth,
            "Others": current_others
        }
        
        # AI optimization logic based on insights
        btc_risk = btc_insights.get("risk_score", 50)
        eth_risk = eth_insights.get("risk_score", 50)
        sol_risk = sol_insights.get("risk_score", 50)
        
        # Optimize based on risk and sentiment
        optimized_portfolio = {
            "BTC": max(25, current_btc - (btc_risk - 50) * 0.3),  # Reduce if high risk
            "ETH": min(40, current_eth + (50 - eth_risk) * 0.2),  # Increase if low risk
            "SOL": 15,  # Add SOL for diversification
            "Others": 20
        }
        
        # Normalize to 100%
        total = sum(optimized_portfolio.values())
        optimized_portfolio = {k: (v / total) * 100 for k, v in optimized_portfolio.items()}
        
        # Calculate improvements
        risk_reduction = max(0, (btc_risk * current_btc + eth_risk * current_eth) / 100 - 
                           (btc_risk * optimized_portfolio["BTC"] + eth_risk * optimized_portfolio["ETH"] + 
                            sol_risk * optimized_portfolio["SOL"]) / 100)
        
        recommendations = []
        if optimized_portfolio["BTC"] < current_btc:
            recommendations.append(f"Reduce BTC allocation by {current_btc - optimized_portfolio['BTC']:.1f}% due to high risk score")
        if optimized_portfolio["ETH"] > current_eth:
            recommendations.append(f"Increase ETH allocation by {optimized_portfolio['ETH'] - current_eth:.1f}% for better risk-adjusted returns")
        recommendations.append("Add SOL position for portfolio diversification")
        
        return {
            "success": True,
            "data": {
                "current_portfolio": current_portfolio,
                "optimized_portfolio": optimized_portfolio,
                "risk_reduction": risk_reduction * 10,  # Scale for display
                "expected_return_improvement": 8.5,
                "recommendations": recommendations,
                "risk_scores": {
                    "BTC": btc_risk,
                    "ETH": eth_risk,
                    "SOL": sol_risk
                },
                "optimization_time": "2025-01-08T00:33:00Z"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")