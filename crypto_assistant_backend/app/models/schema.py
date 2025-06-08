# app/models/schema.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DecisionFactor(BaseModel):
    signal: str  # BUY, SELL, NEUTRAL
    reasoning: str
    weight: int

class CandlestickPatternFactor(DecisionFactor):
    name: Optional[str]
    score: Optional[int]

class TrendAnalysisFactor(DecisionFactor):
    trend: Optional[str]

class MomentumStrengthFactor(DecisionFactor):
    strength: Optional[str]

class RSIAnalysisFactor(DecisionFactor):
    value: Optional[float]

class MACDAnalysisFactor(DecisionFactor):
    value: Optional[float]

class DecisionFactors(BaseModel):
    candlestick_pattern: Optional[CandlestickPatternFactor]
    trend_analysis: Optional[TrendAnalysisFactor]
    momentum_strength: Optional[MomentumStrengthFactor]
    rsi_analysis: Optional[RSIAnalysisFactor]
    macd_analysis: Optional[MACDAnalysisFactor]
    volume_analysis: Optional[DecisionFactor]
    support_resistance: Optional[DecisionFactor]

class SignalResponse(BaseModel):
    symbol: str
    interval: str
    signal: str  # BUY, SELL, HOLD
    entry_price: float
    current_price: float  # Real-time current price
    stop_loss: float
    take_profit: float
    pattern: Optional[str]
    score: Optional[int]
    trend: Optional[str]
    confidence: Optional[int]  # Percentage as integer
    timestamp: Optional[datetime]
    decision_factors: Optional[DecisionFactors]
    total_score: Optional[int]

class SignalHistoryItem(BaseModel):
    timestamp: datetime
    symbol: str
    interval: str
    signal: str
    entry_price: float
    stop_loss: float
    take_profit: float
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    result: Optional[str]
    timeframe: Optional[str]
    profit_usd: Optional[float]
    profit_percent: Optional[float]
    pattern: Optional[str]
    score: Optional[int]
    reason: Optional[str]

class NewsItem(BaseModel):
    id: str
    title: str
    content: str
    source: str
    published_at: str
    url: str
    symbol: str

class PortfolioItem(BaseModel):
    symbol: str
    amount: float
    value: float
    purchase_price: float
    current_price: float
    profit_loss: float
    profit_loss_percentage: float

class PortfolioSummary(BaseModel):
    total_value: float
    profit_loss: float
    profit_loss_percentage: float
    assets: list[PortfolioItem]

class PortfolioStats(BaseModel):
    total_profit_percent: float
    profitable_trades: int
    total_trades: int
    loss_trades: int
    best_coin: str
    worst_coin: str
    win_rate: float
    avg_profit_per_trade: float

class ProfitTimeline(BaseModel):
    date: str
    cumulative_profit: float
    daily_profit: float

class CoinProfit(BaseModel):
    symbol: str
    profit_percent: float
    trade_count: int
    win_rate: float

class TradeStatsResponse(BaseModel):
    stats: PortfolioStats
    profit_timeline: list[ProfitTimeline]
    coin_profits: list[CoinProfit]
