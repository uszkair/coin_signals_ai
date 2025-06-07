from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/trade-stats")
async def get_trade_stats(
    timeframe: str = Query("30d", description="Timeframe: 7d, 30d, 90d, 1y"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get portfolio trade statistics and performance data
    """
    try:
        # Calculate date range based on timeframe
        end_date = datetime.utcnow()
        if timeframe == "7d":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "30d":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "90d":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 30 days

        # Get overall portfolio statistics
        stats_query = text("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_trades,
                COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_trades,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN confidence >= 80 THEN 1 END) as high_confidence_trades,
                COUNT(CASE WHEN confidence >= 60 AND confidence < 80 THEN 1 END) as medium_confidence_trades,
                COUNT(CASE WHEN confidence < 60 THEN 1 END) as low_confidence_trades
            FROM crypto.signals
            WHERE created_at >= :start_date AND created_at <= :end_date
        """)
        
        stats_result = await db.execute(stats_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        stats_row = stats_result.fetchone()

        # Calculate simulated profit based on signal performance
        # This is a simplified calculation - in real scenario you'd track actual trades
        profit_query = text("""
            SELECT
                symbol,
                signal_type,
                price,
                confidence,
                created_at,
                CASE
                    WHEN signal_type = 'BUY' THEN
                        CASE
                            WHEN confidence >= 80 THEN RANDOM() * 8 - 2
                            WHEN confidence >= 60 THEN RANDOM() * 6 - 1
                            ELSE RANDOM() * 4 - 2
                        END
                    WHEN signal_type = 'SELL' THEN
                        CASE
                            WHEN confidence >= 80 THEN RANDOM() * 8 - 2
                            WHEN confidence >= 60 THEN RANDOM() * 6 - 1
                            ELSE RANDOM() * 4 - 2
                        END
                    ELSE 0
                END as simulated_profit_percent
            FROM crypto.signals
            WHERE created_at >= :start_date AND created_at <= :end_date
            ORDER BY created_at
        """)
        
        profit_result = await db.execute(profit_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        profit_results = profit_result.fetchall()

        # Calculate portfolio statistics
        total_trades = stats_row.total_trades if stats_row else 0
        profitable_trades = 0
        loss_trades = 0
        total_profit = 0.0
        best_coin = "N/A"
        worst_coin = "N/A"
        best_profit = float('-inf')
        worst_profit = float('inf')
        
        coin_profits = {}
        daily_profits = {}
        
        for row in profit_results:
            profit = float(row.simulated_profit_percent or 0)
            total_profit += profit
            
            if profit > 0:
                profitable_trades += 1
            elif profit < 0:
                loss_trades += 1
            
            # Track best and worst coins
            if profit > best_profit:
                best_profit = profit
                best_coin = row.symbol
            if profit < worst_profit:
                worst_profit = profit
                worst_coin = row.symbol
            
            # Aggregate by coin
            if row.symbol not in coin_profits:
                coin_profits[row.symbol] = {
                    'symbol': row.symbol,
                    'profit_percent': 0.0,
                    'trade_count': 0,
                    'profitable_count': 0
                }
            
            coin_profits[row.symbol]['profit_percent'] += profit
            coin_profits[row.symbol]['trade_count'] += 1
            if profit > 0:
                coin_profits[row.symbol]['profitable_count'] += 1
            
            # Aggregate by day for timeline
            day_key = row.created_at.strftime('%Y-%m-%d')
            if day_key not in daily_profits:
                daily_profits[day_key] = 0.0
            daily_profits[day_key] += profit

        # Calculate win rate
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0

        # Prepare coin profits with win rates
        coin_profits_list = []
        for coin_data in coin_profits.values():
            win_rate_coin = (coin_data['profitable_count'] / coin_data['trade_count'] * 100) if coin_data['trade_count'] > 0 else 0
            coin_profits_list.append({
                'symbol': coin_data['symbol'],
                'profit_percent': round(coin_data['profit_percent'], 2),
                'trade_count': coin_data['trade_count'],
                'win_rate': round(win_rate_coin, 1)
            })
        
        # Sort by profit descending
        coin_profits_list.sort(key=lambda x: x['profit_percent'], reverse=True)

        # Prepare profit timeline
        profit_timeline = []
        cumulative_profit = 0.0
        
        # Sort daily profits by date
        sorted_days = sorted(daily_profits.keys())
        for day in sorted_days:
            daily_profit = daily_profits[day]
            cumulative_profit += daily_profit
            profit_timeline.append({
                'date': day,
                'daily_profit': round(daily_profit, 2),
                'cumulative_profit': round(cumulative_profit, 2)
            })

        # Prepare response
        response = {
            "stats": {
                "total_profit_percent": round(total_profit, 2),
                "profitable_trades": profitable_trades,
                "total_trades": total_trades,
                "loss_trades": loss_trades,
                "best_coin": best_coin,
                "worst_coin": worst_coin,
                "win_rate": round(win_rate, 1),
                "avg_profit_per_trade": round(avg_profit_per_trade, 2)
            },
            "profit_timeline": profit_timeline,
            "coin_profits": coin_profits_list
        }

        return response

    except Exception as e:
        logger.error(f"Error getting portfolio trade stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting portfolio statistics: {str(e)}")