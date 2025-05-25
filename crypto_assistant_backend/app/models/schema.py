# app/models/schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SignalResponse(BaseModel):
    symbol: str
    interval: str
    signal: str  # BUY, SELL, HOLD
    entry_price: float
    stop_loss: float
    take_profit: float
    pattern: Optional[str]
    score: Optional[int]
    trend: Optional[str]
    confidence: Optional[str]

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
