# app/services/ai_service.py

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
import json
import yfinance as yf
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import ta
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import requests
from bs4 import BeautifulSoup
import os
from app.utils.price_data import get_historical_data, get_current_price

class RealAIService:
    """Real AI-powered trading analysis service using actual data and ML models"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.scaler = MinMaxScaler()
        self.price_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_trained = False
        
    async def analyze_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze real market sentiment from news and social sources"""
        
        try:
            # Get crypto news from multiple sources
            news_sentiment = await self._get_news_sentiment(symbol)
            
            # Get Fear & Greed Index (real data)
            fear_greed = await self._get_fear_greed_index()
            
            # Get Reddit sentiment
            reddit_sentiment = await self._get_reddit_sentiment(symbol)
            
            # Calculate overall sentiment
            overall_sentiment = (
                news_sentiment * 0.4 + 
                reddit_sentiment * 0.3 + 
                (fear_greed - 50) / 50 * 0.3  # Normalize fear/greed to -1,1 range
            )
            
            sentiment_label = "Bullish" if overall_sentiment > 0.2 else "Bearish" if overall_sentiment < -0.2 else "Neutral"
            confidence = min(abs(overall_sentiment) * 100, 100)
            
            return {
                "overall_sentiment": overall_sentiment,
                "sentiment_label": sentiment_label,
                "confidence": confidence,
                "news_sentiment": news_sentiment,
                "reddit_sentiment": reddit_sentiment,
                "fear_greed_index": fear_greed,
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {
                "overall_sentiment": 0,
                "sentiment_label": "Neutral",
                "confidence": 0,
                "error": str(e)
            }
    
    async def _get_news_sentiment(self, symbol: str) -> float:
        """Get sentiment from crypto news sources"""
        try:
            # CoinDesk news scraping
            search_term = symbol.replace("USDT", "").replace("BTC", "Bitcoin").replace("ETH", "Ethereum")
            url = f"https://www.coindesk.com/search?s={search_term}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                headlines = []
                for headline in soup.find_all(['h2', 'h3', 'h4'], limit=10):
                    if headline.text.strip():
                        headlines.append(headline.text.strip())
                
                if not headlines:
                    return 0
                
                # Analyze sentiment of headlines
                sentiments = []
                for headline in headlines:
                    blob = TextBlob(headline)
                    vader_score = self.sentiment_analyzer.polarity_scores(headline)
                    
                    # Combine TextBlob and VADER
                    combined_sentiment = (blob.sentiment.polarity + vader_score['compound']) / 2
                    sentiments.append(combined_sentiment)
                
                return sum(sentiments) / len(sentiments) if sentiments else 0
                
        except Exception as e:
            print(f"News sentiment error: {e}")
            return 0
    
    async def _get_fear_greed_index(self) -> int:
        """Get real Fear & Greed Index from API"""
        try:
            url = "https://api.alternative.me/fng/"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
                return int(data['data'][0]['value'])
        except Exception as e:
            print(f"Fear & Greed Index error: {e}")
            return 50  # Neutral fallback
    
    async def _get_reddit_sentiment(self, symbol: str) -> float:
        """Get sentiment from Reddit crypto discussions"""
        try:
            # Reddit API would require authentication, using web scraping as fallback
            search_term = symbol.replace("USDT", "").lower()
            url = f"https://www.reddit.com/r/cryptocurrency/search.json?q={search_term}&sort=new&limit=25"
            
            async with httpx.AsyncClient() as client:
                headers = {'User-Agent': 'CryptoAI/1.0'}
                response = await client.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    return 0
                
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                sentiments = []
                for post in posts:
                    title = post['data'].get('title', '')
                    if title:
                        vader_score = self.sentiment_analyzer.polarity_scores(title)
                        sentiments.append(vader_score['compound'])
                
                return sum(sentiments) / len(sentiments) if sentiments else 0
                
        except Exception as e:
            print(f"Reddit sentiment error: {e}")
            return 0
    
    async def predict_price_movement(self, symbol: str, timeframe: str = "24h") -> Dict[str, Any]:
        """Real ML-based price prediction using historical data"""
        
        try:
            # Get extensive historical data
            candles = await get_historical_data(symbol, "1h", days=30)
            current_price = float(await get_current_price(symbol))
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(candles)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Calculate technical indicators using TA library
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
            df['macd'] = ta.trend.MACD(df['close']).macd()
            df['bb_high'] = ta.volatility.BollingerBands(df['close']).bollinger_hband()
            df['bb_low'] = ta.volatility.BollingerBands(df['close']).bollinger_lband()
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
            
            # Prepare features for ML model
            features = ['rsi', 'macd', 'bb_high', 'bb_low', 'sma_20', 'ema_12', 'atr', 'obv']
            df_clean = df[features].dropna()
            
            if len(df_clean) < 50:  # Need enough data for training
                raise ValueError("Insufficient data for prediction")
            
            # Prepare training data
            X = df_clean[:-1].values  # All but last row as features
            y = df['close'].iloc[1:len(df_clean)].values  # Next price as target
            
            # Train model if not already trained
            if not self.model_trained:
                X_scaled = self.scaler.fit_transform(X)
                self.price_model.fit(X_scaled, y)
                self.model_trained = True
            else:
                X_scaled = self.scaler.transform(X)
            
            # Make prediction
            latest_features = df_clean.iloc[-1:].values
            latest_scaled = self.scaler.transform(latest_features)
            predicted_price = self.price_model.predict(latest_scaled)[0]
            
            # Calculate prediction metrics
            price_change_percent = ((predicted_price - current_price) / current_price) * 100
            
            # Calculate model confidence based on recent accuracy
            recent_predictions = self.price_model.predict(X_scaled[-10:])
            recent_actual = y[-10:]
            accuracy_scores = [1 - abs(pred - actual) / actual for pred, actual in zip(recent_predictions, recent_actual)]
            confidence = max(60, min(95, np.mean(accuracy_scores) * 100))
            
            # Calculate support and resistance using pivot points
            support_resistance = self._calculate_support_resistance(df)
            
            # Calculate volatility
            volatility = df['close'].pct_change().std() * np.sqrt(24)  # 24h volatility
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "price_change_percent": price_change_percent,
                "confidence": confidence,
                "timeframe": timeframe,
                "support_level": support_resistance['support'],
                "resistance_level": support_resistance['resistance'],
                "volatility": volatility,
                "technical_indicators": {
                    "rsi": float(df['rsi'].iloc[-1]),
                    "macd": float(df['macd'].iloc[-1]),
                    "bb_position": self._get_bollinger_position(df),
                    "trend": self._determine_trend(df)
                },
                "prediction_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Price prediction error: {e}")
            return {
                "error": f"Prediction failed: {str(e)}",
                "symbol": symbol,
                "confidence": 0
            }
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels using pivot points"""
        try:
            recent_data = df.tail(20)
            high = recent_data['high'].max()
            low = recent_data['low'].min()
            close = recent_data['close'].iloc[-1]
            
            # Pivot point calculation
            pivot = (high + low + close) / 3
            support = 2 * pivot - high
            resistance = 2 * pivot - low
            
            return {
                "support": float(support),
                "resistance": float(resistance),
                "pivot": float(pivot)
            }
        except:
            current_price = df['close'].iloc[-1]
            return {
                "support": float(current_price * 0.95),
                "resistance": float(current_price * 1.05),
                "pivot": float(current_price)
            }
    
    def _get_bollinger_position(self, df: pd.DataFrame) -> str:
        """Determine position relative to Bollinger Bands"""
        try:
            latest_close = df['close'].iloc[-1]
            bb_high = df['bb_high'].iloc[-1]
            bb_low = df['bb_low'].iloc[-1]
            
            if latest_close > bb_high:
                return "above_upper"
            elif latest_close < bb_low:
                return "below_lower"
            else:
                return "within_bands"
        except:
            return "unknown"
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine overall trend using multiple indicators"""
        try:
            sma_20 = df['sma_20'].iloc[-1]
            ema_12 = df['ema_12'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if current_price > sma_20 and ema_12 > sma_20:
                return "bullish"
            elif current_price < sma_20 and ema_12 < sma_20:
                return "bearish"
            else:
                return "sideways"
        except:
            return "unknown"
    
    async def detect_anomalies(self, symbol: str) -> Dict[str, Any]:
        """Detect real volume and price anomalies using statistical analysis"""
        
        try:
            candles = await get_historical_data(symbol, "1h", days=7)
            df = pd.DataFrame(candles)
            df['volume'] = df['volume'].astype(float)
            df['close'] = df['close'].astype(float)
            
            # Volume anomaly detection using Z-score
            volume_mean = df['volume'].mean()
            volume_std = df['volume'].std()
            latest_volume = df['volume'].iloc[-1]
            volume_zscore = (latest_volume - volume_mean) / volume_std if volume_std > 0 else 0
            
            # Price movement anomaly
            df['price_change'] = df['close'].pct_change() * 100
            price_change_std = df['price_change'].std()
            latest_price_change = df['price_change'].iloc[-1]
            price_zscore = abs(latest_price_change) / price_change_std if price_change_std > 0 else 0
            
            # Anomaly thresholds
            volume_anomaly = abs(volume_zscore) > 2.0
            price_anomaly = price_zscore > 2.0
            
            return {
                "symbol": symbol,
                "volume_anomaly": volume_anomaly,
                "volume_zscore": float(volume_zscore),
                "volume_ratio": float(latest_volume / volume_mean),
                "price_anomaly": price_anomaly,
                "price_zscore": float(price_zscore),
                "price_change": float(latest_price_change),
                "anomaly_score": float((abs(volume_zscore) + price_zscore) / 2),
                "detection_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return {
                "error": f"Anomaly detection failed: {str(e)}",
                "symbol": symbol
            }
    
    async def generate_ai_insights(self, symbol: str) -> Dict[str, Any]:
        """Generate comprehensive AI insights using real data analysis"""
        
        try:
            # Get all AI analyses
            sentiment = await self.analyze_market_sentiment(symbol)
            prediction = await self.predict_price_movement(symbol)
            anomalies = await self.detect_anomalies(symbol)
            
            # Generate trading recommendation
            recommendation = self._generate_recommendation(sentiment, prediction, anomalies)
            
            # Risk assessment
            risk_score = self._calculate_risk_score(sentiment, prediction, anomalies)
            
            return {
                "symbol": symbol,
                "sentiment": sentiment,
                "prediction": prediction,
                "anomalies": anomalies,
                "recommendation": recommendation,
                "risk_score": risk_score,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"AI insights generation error: {e}")
            return {
                "error": f"AI insights failed: {str(e)}",
                "symbol": symbol
            }
    
    def _generate_recommendation(self, sentiment: Dict, prediction: Dict, anomalies: Dict) -> Dict[str, Any]:
        """Generate trading recommendation based on real AI analysis"""
        
        score = 0
        reasoning_parts = []
        
        # Sentiment scoring
        if sentiment.get("overall_sentiment", 0) > 0.3:
            score += 2
            reasoning_parts.append("Strong bullish sentiment detected")
        elif sentiment.get("overall_sentiment", 0) < -0.3:
            score -= 2
            reasoning_parts.append("Bearish sentiment prevailing")
        
        # Prediction scoring
        price_change = prediction.get("price_change_percent", 0)
        if price_change > 3:
            score += 2
            reasoning_parts.append(f"AI predicts {price_change:.1f}% price increase")
        elif price_change < -3:
            score -= 2
            reasoning_parts.append(f"AI predicts {price_change:.1f}% price decrease")
        elif abs(price_change) > 1:
            score += 1 if price_change > 0 else -1
            reasoning_parts.append(f"Moderate price movement predicted ({price_change:.1f}%)")
        
        # Technical indicators
        tech_indicators = prediction.get("technical_indicators", {})
        rsi = tech_indicators.get("rsi", 50)
        if rsi > 70:
            score -= 1
            reasoning_parts.append("RSI indicates overbought conditions")
        elif rsi < 30:
            score += 1
            reasoning_parts.append("RSI indicates oversold conditions")
        
        # Anomaly scoring
        if anomalies.get("volume_anomaly"):
            if sentiment.get("overall_sentiment", 0) > 0:
                score += 1
                reasoning_parts.append("Unusual volume supports bullish sentiment")
            else:
                score -= 1
                reasoning_parts.append("Unusual volume with bearish sentiment")
        
        # Generate final recommendation
        if score >= 3:
            action = "STRONG_BUY"
            confidence = min(90, 70 + score * 5)
        elif score >= 1:
            action = "BUY"
            confidence = min(80, 60 + score * 5)
        elif score <= -3:
            action = "STRONG_SELL"
            confidence = min(90, 70 + abs(score) * 5)
        elif score <= -1:
            action = "SELL"
            confidence = min(80, 60 + abs(score) * 5)
        else:
            action = "HOLD"
            confidence = 60
        
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "reasoning": ". ".join(reasoning_parts) if reasoning_parts else "Mixed signals detected"
        }
    
    def _calculate_risk_score(self, sentiment: Dict, prediction: Dict, anomalies: Dict) -> int:
        """Calculate risk score based on real market analysis"""
        
        risk = 30  # Base risk
        
        # Volatility risk
        volatility = prediction.get("volatility", 0.02)
        risk += min(volatility * 1000, 30)  # Cap volatility contribution
        
        # Prediction confidence risk
        pred_confidence = prediction.get("confidence", 0)
        if pred_confidence < 70:
            risk += 20
        
        # Sentiment uncertainty risk
        sentiment_confidence = sentiment.get("confidence", 0)
        if sentiment_confidence < 50:
            risk += 15
        
        # Anomaly risk
        anomaly_score = anomalies.get("anomaly_score", 0)
        if anomaly_score > 2:
            risk += 15
        
        return min(max(int(risk), 0), 100)

# Global AI service instance
ai_service = RealAIService()