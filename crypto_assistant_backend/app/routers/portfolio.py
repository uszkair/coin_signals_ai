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

        # Get overall portfolio statistics from actual trading performance
        stats_query = text("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN s.signal_type = 'BUY' THEN 1 END) as buy_trades,
                COUNT(CASE WHEN s.signal_type = 'SELL' THEN 1 END) as sell_trades,
                AVG(s.confidence) as avg_confidence,
                COUNT(CASE WHEN s.confidence >= 80 THEN 1 END) as high_confidence_trades,
                COUNT(CASE WHEN s.confidence >= 60 AND s.confidence < 80 THEN 1 END) as medium_confidence_trades,
                COUNT(CASE WHEN s.confidence < 60 THEN 1 END) as low_confidence_trades,
                COUNT(CASE WHEN sp.result = 'profit' THEN 1 END) as profitable_trades,
                COUNT(CASE WHEN sp.result = 'loss' THEN 1 END) as loss_trades,
                COUNT(CASE WHEN sp.result = 'failed_order' THEN 1 END) as failed_orders,
                SUM(COALESCE(sp.profit_loss, 0)) as total_pnl_usd
            FROM crypto.signals s
            LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
            WHERE s.created_at >= :start_date AND s.created_at <= :end_date
            AND sp.id IS NOT NULL
        """)
        
        stats_result = await db.execute(stats_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        stats_row = stats_result.fetchone()

        # Get actual trading performance data
        profit_query = text("""
            SELECT
                s.symbol,
                s.signal_type,
                s.price,
                s.confidence,
                s.created_at,
                sp.result,
                COALESCE(sp.profit_loss, 0) as profit_loss_usd,
                COALESCE(sp.profit_percentage, 0) as profit_percentage,
                sp.position_size_usd,
                sp.main_order_id,
                sp.testnet_mode
            FROM crypto.signals s
            LEFT JOIN crypto.signal_performance sp ON s.id = sp.signal_id
            WHERE s.created_at >= :start_date AND s.created_at <= :end_date
            AND sp.id IS NOT NULL
            ORDER BY s.created_at
        """)
        
        profit_result = await db.execute(profit_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        profit_results = profit_result.fetchall()

        # Calculate portfolio statistics from actual trading data
        total_trades = stats_row.total_trades if stats_row else 0
        profitable_trades = stats_row.profitable_trades if stats_row else 0
        loss_trades = stats_row.loss_trades if stats_row else 0
        failed_orders = stats_row.failed_orders if stats_row else 0
        total_profit_usd = float(stats_row.total_pnl_usd or 0) if stats_row else 0.0
        
        best_coin = "N/A"
        worst_coin = "N/A"
        best_profit = float('-inf')
        worst_profit = float('inf')
        
        coin_profits = {}
        daily_profits = {}
        
        for row in profit_results:
            # Use actual profit data
            profit_usd = float(row.profit_loss_usd or 0)
            profit_percent = float(row.profit_percentage or 0)
            
            # Track best and worst coins by USD profit
            if profit_usd > best_profit:
                best_profit = profit_usd
                best_coin = row.symbol
            if profit_usd < worst_profit:
                worst_profit = profit_usd
                worst_coin = row.symbol
            
            # Aggregate by coin
            if row.symbol not in coin_profits:
                coin_profits[row.symbol] = {
                    'symbol': row.symbol,
                    'profit_usd': 0.0,
                    'profit_percent': 0.0,
                    'trade_count': 0,
                    'profitable_count': 0,
                    'pending_count': 0,
                    'failed_count': 0
                }
            
            coin_profits[row.symbol]['profit_usd'] += profit_usd
            coin_profits[row.symbol]['profit_percent'] += profit_percent
            coin_profits[row.symbol]['trade_count'] += 1
            
            if row.result == 'profit':
                coin_profits[row.symbol]['profitable_count'] += 1
            elif row.result == 'pending':
                coin_profits[row.symbol]['pending_count'] += 1
            elif row.result == 'failed_order':
                coin_profits[row.symbol]['failed_count'] += 1
            
            # Aggregate by day for timeline (use USD profit)
            day_key = row.created_at.strftime('%Y-%m-%d')
            if day_key not in daily_profits:
                daily_profits[day_key] = 0.0
            daily_profits[day_key] += profit_usd

        # Calculate win rate
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit_per_trade_usd = total_profit_usd / total_trades if total_trades > 0 else 0

        # Prepare coin profits with win rates
        coin_profits_list = []
        for coin_data in coin_profits.values():
            win_rate_coin = (coin_data['profitable_count'] / coin_data['trade_count'] * 100) if coin_data['trade_count'] > 0 else 0
            coin_profits_list.append({
                'symbol': coin_data['symbol'],
                'profit_usd': round(coin_data['profit_usd'], 2),
                'profit_percent': round(coin_data['profit_percent'], 2),
                'trade_count': coin_data['trade_count'],
                'profitable_count': coin_data['profitable_count'],
                'pending_count': coin_data['pending_count'],
                'failed_count': coin_data['failed_count'],
                'win_rate': round(win_rate_coin, 1)
            })
        
        # Sort by USD profit descending
        coin_profits_list.sort(key=lambda x: x['profit_usd'], reverse=True)

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

        # Prepare response with real trading data
        response = {
            "stats": {
                "total_profit_usd": round(total_profit_usd, 2),
                "profitable_trades": profitable_trades,
                "total_trades": total_trades,
                "loss_trades": loss_trades,
                "failed_orders": failed_orders,
                "pending_trades": total_trades - profitable_trades - loss_trades - failed_orders,
                "best_coin": best_coin if best_profit != float('-inf') else "N/A",
                "worst_coin": worst_coin if worst_profit != float('inf') else "N/A",
                "best_profit_usd": round(best_profit, 2) if best_profit != float('-inf') else 0,
                "worst_profit_usd": round(worst_profit, 2) if worst_profit != float('inf') else 0,
                "win_rate": round(win_rate, 1),
                "avg_profit_per_trade_usd": round(avg_profit_per_trade_usd, 2)
            },
            "profit_timeline": profit_timeline,
            "coin_profits": coin_profits_list,
            "data_source": "real_trading_performance"
        }

        return response

    except Exception as e:
        logger.error(f"Error getting portfolio trade stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting portfolio statistics: {str(e)}")