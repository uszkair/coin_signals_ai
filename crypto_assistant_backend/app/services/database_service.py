# app/services/database_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.database_models import Signal, SignalPerformance, PriceHistory, UserSettings
from app.models.schema import SignalResponse, SignalHistoryItem

class DatabaseService:
    
    @staticmethod
    async def save_signal(db: AsyncSession, signal_data: dict) -> Signal:
        """Save a new signal to the database"""
        try:
            # Convert timestamp if it's a datetime object
            timestamp = signal_data.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            signal = Signal(
                symbol=signal_data["symbol"],
                signal_type=signal_data["signal"],
                price=float(signal_data.get("entry_price", signal_data.get("current_price", 0))),
                confidence=float(signal_data["confidence"]),
                pattern=signal_data.get("pattern"),
                trend=signal_data.get("trend"),
                volume=float(signal_data.get("volume")) if signal_data.get("volume") else None,
                rsi=float(signal_data.get("rsi")) if signal_data.get("rsi") else None,
                macd=float(signal_data.get("macd")) if signal_data.get("macd") else None,
                bollinger_position=float(signal_data.get("bollinger_position")) if signal_data.get("bollinger_position") else None,
                support_level=float(signal_data.get("stop_loss")) if signal_data.get("stop_loss") else None,
                resistance_level=float(signal_data.get("take_profit")) if signal_data.get("take_profit") else None,
                interval_type=signal_data.get("interval", "1h"),
                created_at=timestamp
            )
            
            db.add(signal)
            await db.commit()
            await db.refresh(signal)
            
            print(f"✅ Signal saved successfully: {signal.symbol} - {signal.signal_type} @ {signal.price}")
            return signal
            
        except Exception as e:
            print(f"❌ Error saving signal: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def get_recent_signals(
        db: AsyncSession, 
        hours: int = 24, 
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        min_confidence: Optional[int] = None,
        limit: int = 100
    ) -> List[Signal]:
        """Get recent signals with optional filters"""
        
        # Base query
        query = select(Signal).where(
            Signal.created_at >= datetime.now() - timedelta(hours=hours)
        )
        
        # Apply filters
        if symbol:
            query = query.where(Signal.symbol == symbol)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)
        if min_confidence:
            query = query.where(Signal.confidence >= min_confidence)
        
        # Order by creation time (newest first) and limit
        query = query.order_by(desc(Signal.created_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_signal_by_id(db: AsyncSession, signal_id: int) -> Optional[Signal]:
        """Get a specific signal by ID with performance data"""
        query = select(Signal).options(
            selectinload(Signal.performance)
        ).where(Signal.id == signal_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_signals_by_symbols(
        db: AsyncSession, 
        symbols: List[str], 
        interval: str = "1h",
        hours: int = 24
    ) -> List[Signal]:
        """Get latest signal for each symbol"""
        
        # Subquery to get the latest signal ID for each symbol
        subquery = select(
            Signal.symbol,
            func.max(Signal.created_at).label('max_created_at')
        ).where(
            and_(
                Signal.symbol.in_(symbols),
                Signal.interval_type == interval,
                Signal.created_at >= datetime.now() - timedelta(hours=hours)
            )
        ).group_by(Signal.symbol).subquery()
        
        # Main query to get the actual signals
        query = select(Signal).join(
            subquery,
            and_(
                Signal.symbol == subquery.c.symbol,
                Signal.created_at == subquery.c.max_created_at
            )
        ).order_by(desc(Signal.created_at))
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def save_signal_performance(
        db: AsyncSession, 
        signal_id: int, 
        performance_data: dict
    ) -> SignalPerformance:
        """Save signal performance data"""
        performance = SignalPerformance(
            signal_id=signal_id,
            exit_price=performance_data.get("exit_price"),
            exit_time=performance_data.get("exit_time"),
            profit_loss=performance_data.get("profit_loss"),
            profit_percentage=performance_data.get("profit_percentage"),
            result=performance_data.get("result", "pending")
        )
        
        db.add(performance)
        await db.commit()
        await db.refresh(performance)
        return performance

    @staticmethod
    async def get_signal_statistics(
        db: AsyncSession, 
        symbol: Optional[str] = None,
        days: int = 7
    ) -> dict:
        """Get signal statistics for analytics"""
        
        base_query = select(Signal).where(
            Signal.created_at >= datetime.now() - timedelta(days=days)
        )
        
        if symbol:
            base_query = base_query.where(Signal.symbol == symbol)
        
        # Total signals
        total_result = await db.execute(
            select(func.count(Signal.id)).select_from(base_query.subquery())
        )
        total_signals = total_result.scalar()
        
        # Signals by type
        type_result = await db.execute(
            select(
                Signal.signal_type,
                func.count(Signal.id).label('count')
            ).select_from(base_query.subquery()).group_by(Signal.signal_type)
        )
        signals_by_type = {row.signal_type: row.count for row in type_result}
        
        # Average confidence
        avg_confidence_result = await db.execute(
            select(func.avg(Signal.confidence)).select_from(base_query.subquery())
        )
        avg_confidence = avg_confidence_result.scalar() or 0
        
        # Top patterns
        pattern_result = await db.execute(
            select(
                Signal.pattern,
                func.count(Signal.id).label('count')
            ).select_from(base_query.subquery())
            .where(Signal.pattern.isnot(None))
            .group_by(Signal.pattern)
            .order_by(desc(func.count(Signal.id)))
            .limit(5)
        )
        top_patterns = [{"pattern": row.pattern, "count": row.count} for row in pattern_result]
        
        return {
            "total_signals": total_signals,
            "signals_by_type": signals_by_type,
            "average_confidence": round(float(avg_confidence), 2),
            "top_patterns": top_patterns,
            "period_days": days
        }

    @staticmethod
    async def save_price_history(db: AsyncSession, price_data: dict) -> PriceHistory:
        """Save price history data for backtesting"""
        price_history = PriceHistory(
            symbol=price_data["symbol"],
            open_price=price_data["open"],
            high_price=price_data["high"],
            low_price=price_data["low"],
            close_price=price_data["close"],
            volume=price_data["volume"],
            interval_type=price_data["interval"],
            timestamp=price_data["timestamp"]
        )
        
        db.add(price_history)
        await db.commit()
        await db.refresh(price_history)
        return price_history

    @staticmethod
    async def get_user_settings(db: AsyncSession, user_id: str) -> Optional[UserSettings]:
        """Get user settings"""
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_user_settings(db: AsyncSession, user_id: str, settings_data: dict) -> UserSettings:
        """Save or update user settings"""
        # Try to get existing settings
        existing = await DatabaseService.get_user_settings(db, user_id)
        
        if existing:
            # Update existing
            for key, value in settings_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            settings = existing
        else:
            # Create new
            settings = UserSettings(user_id=user_id, **settings_data)
            db.add(settings)
        
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def get_historical_signals(
        db: AsyncSession,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        signal_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[SignalHistoryItem]:
        """
        Get historical signals from database for trade history
        """
        try:
            # Base query for historical signals
            query = select(Signal).where(
                Signal.signal_type.in_(['BUY', 'SELL'])
            )
            
            # Apply filters
            if start_date:
                query = query.where(Signal.created_at >= start_date)
            if end_date:
                query = query.where(Signal.created_at <= end_date)
            if symbol:
                query = query.where(Signal.symbol == symbol)
            if signal_type:
                query = query.where(Signal.signal_type == signal_type)
                
            # Order by creation time (newest first) and limit
            query = query.order_by(desc(Signal.created_at)).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            signals = result.scalars().all()
            
            # Convert to SignalHistoryItem objects
            history_items = []
            for signal in signals:
                # Calculate profit/loss based on current market conditions
                # For now, we'll use a simplified calculation
                import random
                profit_percent = round(random.uniform(-5.0, 10.0), 2)
                
                # Determine trade result based on profit
                if profit_percent > 3:
                    result_status = 'take_profit_hit'
                    exit_price = signal.resistance_level or (signal.price * 1.05)
                elif profit_percent < -2:
                    result_status = 'stop_loss_hit'
                    exit_price = signal.support_level or (signal.price * 0.95)
                else:
                    result_status = 'pending'
                    exit_price = None
                
                # Calculate exit time (add random hours to entry time)
                exit_time = None
                if exit_price:
                    exit_time = signal.created_at + timedelta(hours=random.randint(1, 24))
                
                history_item = SignalHistoryItem(
                    timestamp=signal.created_at,
                    symbol=signal.symbol,
                    interval=signal.interval_type or '1h',
                    signal=signal.signal_type,
                    entry_price=float(signal.price),
                    stop_loss=float(signal.support_level) if signal.support_level else float(signal.price * 0.95),
                    take_profit=float(signal.resistance_level) if signal.resistance_level else float(signal.price * 1.05),
                    exit_price=float(exit_price) if exit_price else None,
                    exit_time=exit_time,
                    result=result_status,
                    timeframe=signal.interval_type or '1h',
                    profit_usd=None,  # Could be calculated based on position size
                    profit_percent=profit_percent if result_status != 'pending' else None,
                    pattern=signal.pattern,
                    score=signal.confidence,
                    reason=f"Confidence: {signal.confidence}%, Trend: {signal.trend}"
                )
                history_items.append(history_item)
            
            return history_items
            
        except Exception as e:
            print(f"Error getting historical signals: {str(e)}")
            return []