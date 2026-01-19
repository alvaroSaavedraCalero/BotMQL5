"""
Database Module
Handles SQLite database operations for trade history
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from contextlib import contextmanager

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Trade, DailyStats, EquitySnapshot, NewsEvent

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for trading bot

    Handles all database operations including:
    - Trade history storage and retrieval
    - Daily statistics
    - Equity snapshots for charting
    """

    def __init__(self, database_url: str):
        """
        Initialize database connection

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)

        logger.info(f"Database initialized: {database_url}")

    @contextmanager
    def get_session(self) -> Session:
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    # ==================== TRADE OPERATIONS ====================

    def add_trade(self, trade_data: Dict) -> Optional[Trade]:
        """
        Add a new trade to database

        Args:
            trade_data: Trade information dictionary

        Returns:
            Trade object or None if failed
        """
        with self.get_session() as session:
            trade = Trade(
                ticket=trade_data.get('ticket'),
                symbol=trade_data.get('symbol'),
                trade_type=trade_data.get('trade_type'),
                status='OPEN',
                initial_volume=trade_data.get('volume'),
                current_volume=trade_data.get('volume'),
                open_price=trade_data.get('open_price'),
                stop_loss=trade_data.get('stop_loss'),
                take_profit=trade_data.get('take_profit'),
                open_time=trade_data.get('open_time', datetime.utcnow()),
                magic_number=trade_data.get('magic_number'),
                comment=trade_data.get('comment')
            )

            session.add(trade)
            session.flush()

            logger.info(f"Trade added: {trade.ticket}")
            return trade

    def update_trade_close(self, ticket: int, close_price: float, profit: float,
                           close_time: datetime = None) -> bool:
        """
        Update trade as closed

        Args:
            ticket: Trade ticket number
            close_price: Closing price
            profit: Final profit/loss
            close_time: Close timestamp

        Returns:
            bool: Success status
        """
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.ticket == ticket).first()

            if trade:
                trade.status = 'CLOSED'
                trade.close_price = close_price
                trade.profit = profit
                trade.close_time = close_time or datetime.utcnow()
                trade.current_volume = 0

                logger.info(f"Trade closed: {ticket}, profit: {profit}")
                return True

            logger.warning(f"Trade not found: {ticket}")
            return False

    def update_trade_partial_close(self, ticket: int, remaining_volume: float) -> bool:
        """
        Update trade after partial close

        Args:
            ticket: Trade ticket number
            remaining_volume: Remaining volume

        Returns:
            bool: Success status
        """
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.ticket == ticket).first()

            if trade:
                trade.current_volume = remaining_volume
                trade.partial_closed = True
                trade.status = 'PARTIAL'

                logger.info(f"Trade partial close: {ticket}, remaining: {remaining_volume}")
                return True

            return False

    def get_trade(self, ticket: int) -> Optional[Trade]:
        """Get trade by ticket"""
        with self.get_session() as session:
            return session.query(Trade).filter(Trade.ticket == ticket).first()

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades"""
        with self.get_session() as session:
            return session.query(Trade).filter(
                Trade.status.in_(['OPEN', 'PARTIAL'])
            ).all()

    def get_trades_by_date(self, target_date: date) -> List[Trade]:
        """Get trades for a specific date"""
        with self.get_session() as session:
            start = datetime.combine(target_date, datetime.min.time())
            end = datetime.combine(target_date, datetime.max.time())

            return session.query(Trade).filter(
                Trade.open_time >= start,
                Trade.open_time <= end
            ).all()

    def get_trade_history(self, limit: int = 100, offset: int = 0) -> List[Trade]:
        """Get trade history with pagination"""
        with self.get_session() as session:
            return session.query(Trade).order_by(
                Trade.open_time.desc()
            ).offset(offset).limit(limit).all()

    # ==================== DAILY STATS OPERATIONS ====================

    def save_daily_stats(self, stats_data: Dict) -> Optional[DailyStats]:
        """
        Save or update daily statistics

        Args:
            stats_data: Statistics dictionary

        Returns:
            DailyStats object or None
        """
        with self.get_session() as session:
            target_date = stats_data.get('date', date.today())

            # Check if exists
            stats = session.query(DailyStats).filter(
                func.date(DailyStats.date) == target_date
            ).first()

            if stats:
                # Update existing
                for key, value in stats_data.items():
                    if hasattr(stats, key) and key != 'id':
                        setattr(stats, key, value)
            else:
                # Create new
                stats = DailyStats(
                    date=datetime.combine(target_date, datetime.min.time()),
                    **{k: v for k, v in stats_data.items() if k != 'date'}
                )
                session.add(stats)

            session.flush()
            return stats

    def get_daily_stats(self, target_date: date = None) -> Optional[DailyStats]:
        """Get daily stats for a specific date"""
        if target_date is None:
            target_date = date.today()

        with self.get_session() as session:
            return session.query(DailyStats).filter(
                func.date(DailyStats.date) == target_date
            ).first()

    def get_stats_range(self, start_date: date, end_date: date) -> List[DailyStats]:
        """Get daily stats for a date range"""
        with self.get_session() as session:
            return session.query(DailyStats).filter(
                DailyStats.date >= datetime.combine(start_date, datetime.min.time()),
                DailyStats.date <= datetime.combine(end_date, datetime.max.time())
            ).order_by(DailyStats.date).all()

    def calculate_period_stats(self, days: int = 30) -> Dict:
        """Calculate aggregate stats for a period"""
        with self.get_session() as session:
            start_date = date.today() - timedelta(days=days)

            stats = session.query(DailyStats).filter(
                DailyStats.date >= datetime.combine(start_date, datetime.min.time())
            ).all()

            if not stats:
                return {}

            total_trades = sum(s.total_trades for s in stats)
            winning_trades = sum(s.winning_trades for s in stats)
            losing_trades = sum(s.losing_trades for s in stats)
            total_profit = sum(s.net_profit for s in stats)
            gross_profit = sum(s.gross_profit for s in stats)
            gross_loss = sum(s.gross_loss for s in stats)

            return {
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'net_profit': round(total_profit, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2),
                'win_rate': round((winning_trades / total_trades * 100) if total_trades > 0 else 0, 2),
                'profit_factor': round((gross_profit / gross_loss) if gross_loss > 0 else 0, 2),
                'average_daily_profit': round(total_profit / len(stats) if stats else 0, 2)
            }

    # ==================== EQUITY SNAPSHOT OPERATIONS ====================

    def add_equity_snapshot(self, balance: float, equity: float,
                            margin: float = 0, free_margin: float = 0,
                            floating_profit: float = 0, open_positions: int = 0) -> EquitySnapshot:
        """Add equity snapshot for charting"""
        with self.get_session() as session:
            snapshot = EquitySnapshot(
                timestamp=datetime.utcnow(),
                balance=balance,
                equity=equity,
                margin=margin,
                free_margin=free_margin,
                floating_profit=floating_profit,
                open_positions=open_positions
            )

            session.add(snapshot)
            session.flush()

            return snapshot

    def get_equity_history(self, hours: int = 24) -> List[EquitySnapshot]:
        """Get equity history for charting"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=hours)

            return session.query(EquitySnapshot).filter(
                EquitySnapshot.timestamp >= cutoff
            ).order_by(EquitySnapshot.timestamp).all()

    def cleanup_old_snapshots(self, days: int = 30):
        """Remove old equity snapshots"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)

            deleted = session.query(EquitySnapshot).filter(
                EquitySnapshot.timestamp < cutoff
            ).delete()

            logger.info(f"Cleaned up {deleted} old equity snapshots")

    # ==================== NEWS OPERATIONS ====================

    def save_news_events(self, events: List[Dict]):
        """Save news events to database"""
        with self.get_session() as session:
            for event_data in events:
                # Check if exists
                existing = session.query(NewsEvent).filter(
                    NewsEvent.event_time == event_data.get('event_time'),
                    NewsEvent.event_name == event_data.get('event_name')
                ).first()

                if not existing:
                    event = NewsEvent(
                        event_time=event_data.get('event_time'),
                        currency=event_data.get('currency'),
                        event_name=event_data.get('event_name'),
                        impact=event_data.get('impact'),
                        actual=event_data.get('actual'),
                        forecast=event_data.get('forecast'),
                        previous=event_data.get('previous')
                    )
                    session.add(event)

    def get_upcoming_news(self, hours: int = 24) -> List[NewsEvent]:
        """Get upcoming news events"""
        with self.get_session() as session:
            now = datetime.utcnow()
            cutoff = now + timedelta(hours=hours)

            return session.query(NewsEvent).filter(
                NewsEvent.event_time >= now,
                NewsEvent.event_time <= cutoff
            ).order_by(NewsEvent.event_time).all()
