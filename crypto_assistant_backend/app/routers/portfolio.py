from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.schema import PortfolioItem, PortfolioSummary, TradeStatsResponse, PortfolioStats, ProfitTimeline, CoinProfit
from app.services.backtester import get_signal_history

router = APIRouter()

@router.get("/", response_model=PortfolioSummary)
async def get_portfolio():
    """
    Portfólió összegzés lekérése.
    Ez az endpoint későbbre van tervezve.
    """
    # Placeholder a jövőbeli implementációhoz
    return PortfolioSummary(
        total_value=10000.0,
        profit_loss=500.0,
        profit_loss_percentage=5.0,
        assets=[
            PortfolioItem(
                symbol="BTCUSDT",
                amount=0.5,
                value=8000.0,
                purchase_price=7500.0,
                current_price=16000.0,
                profit_loss=500.0,
                profit_loss_percentage=6.67
            ),
            PortfolioItem(
                symbol="ETHUSDT",
                amount=1.0,
                value=2000.0,
                purchase_price=2000.0,
                current_price=2000.0,
                profit_loss=0.0,
                profit_loss_percentage=0.0
            )
        ]
    )

@router.get("/trade-stats", response_model=TradeStatsResponse)
async def get_trade_stats(timeframe: str = "30d"):
    """
    Kereskedési statisztikák lekérése.
    """
    try:
        # Parse timeframe
        if timeframe.endswith('d'):
            days = int(timeframe[:-1])
        else:
            days = 30
        
        # Limit to maximum 90 days
        days = min(days, 90)
        
        # Get trade history for multiple symbols
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
        all_trades = []
        
        for symbol in symbols:
            try:
                trades = await get_signal_history(symbol, "1h", days)
                all_trades.extend(trades)
            except Exception as e:
                # Continue with other symbols if one fails
                continue
        
        # Calculate statistics
        total_trades = len(all_trades)
        profitable_trades = sum(1 for trade in all_trades if trade.profit_percent and trade.profit_percent > 0)
        loss_trades = sum(1 for trade in all_trades if trade.profit_percent and trade.profit_percent < 0)
        
        total_profit_percent = sum(trade.profit_percent or 0 for trade in all_trades)
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit_per_trade = total_profit_percent / total_trades if total_trades > 0 else 0
        
        # Find best and worst performing coins
        coin_performance = defaultdict(list)
        for trade in all_trades:
            if trade.profit_percent is not None:
                coin_performance[trade.symbol].append(trade.profit_percent)
        
        coin_avg_profits = {}
        for symbol, profits in coin_performance.items():
            coin_avg_profits[symbol] = sum(profits) / len(profits) if profits else 0
        
        best_coin = max(coin_avg_profits.items(), key=lambda x: x[1])[0] if coin_avg_profits else "N/A"
        worst_coin = min(coin_avg_profits.items(), key=lambda x: x[1])[0] if coin_avg_profits else "N/A"
        
        # Create profit timeline (simplified)
        profit_timeline = []
        cumulative_profit = 0
        for i in range(min(days, 30)):  # Last 30 days max
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_profit = 0  # Simplified - would need actual daily calculation
            profit_timeline.append(ProfitTimeline(
                date=date,
                cumulative_profit=cumulative_profit,
                daily_profit=daily_profit
            ))
        
        # Create coin profits summary
        coin_profits = []
        for symbol, profits in coin_performance.items():
            if profits:
                profit_percent = sum(profits)
                trade_count = len(profits)
                wins = sum(1 for p in profits if p > 0)
                coin_win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
                
                coin_profits.append(CoinProfit(
                    symbol=symbol,
                    profit_percent=profit_percent,
                    trade_count=trade_count,
                    win_rate=coin_win_rate
                ))
        
        stats = PortfolioStats(
            total_profit_percent=total_profit_percent,
            profitable_trades=profitable_trades,
            total_trades=total_trades,
            loss_trades=loss_trades,
            best_coin=best_coin,
            worst_coin=worst_coin,
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit_per_trade
        )
        
        return TradeStatsResponse(
            stats=stats,
            profit_timeline=profit_timeline,
            coin_profits=coin_profits
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))