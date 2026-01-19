"""
Database Models
SQLAlchemy models for trade history and statistics
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


class Trade(Base):
    """Trade model for storing trade history"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket = Column(Integer, unique=True, index=True)
    symbol = Column(String(20), index=True)
    trade_type = Column(String(10))  # BUY or SELL
    status = Column(String(10), default="OPEN")

    # Volumes
    initial_volume = Column(Float)
    current_volume = Column(Float)

    # Prices
    open_price = Column(Float)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float)

    # Results
    profit = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)

    # Timestamps
    open_time = Column(DateTime, default=datetime.utcnow)
    close_time = Column(DateTime, nullable=True)

    # Metadata
    magic_number = Column(Integer)
    comment = Column(String(100), nullable=True)

    # Flags
    partial_closed = Column(Boolean, default=False)
    break_even_set = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Trade(ticket={self.ticket}, symbol={self.symbol}, type={self.trade_type}, profit={self.profit})>"

    def to_dict(self):
        return {
            'id': self.id,
            'ticket': self.ticket,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'status': self.status,
            'initial_volume': self.initial_volume,
            'current_volume': self.current_volume,
            'open_price': self.open_price,
            'close_price': self.close_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'profit': self.profit,
            'commission': self.commission,
            'swap': self.swap,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'magic_number': self.magic_number,
            'comment': self.comment,
            'partial_closed': self.partial_closed,
            'break_even_set': self.break_even_set
        }


class DailyStats(Base):
    """Daily statistics model"""
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, unique=True, index=True)

    # Trade counts
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Profit/Loss
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)

    # Balance
    start_balance = Column(Float)
    end_balance = Column(Float)

    # Drawdown
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)

    # Metrics
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    expectancy = Column(Float, default=0.0)
    average_win = Column(Float, default=0.0)
    average_loss = Column(Float, default=0.0)

    def __repr__(self):
        return f"<DailyStats(date={self.date}, net_profit={self.net_profit}, win_rate={self.win_rate})>"

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'gross_profit': self.gross_profit,
            'gross_loss': self.gross_loss,
            'net_profit': self.net_profit,
            'start_balance': self.start_balance,
            'end_balance': self.end_balance,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_percent': self.max_drawdown_percent,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'expectancy': self.expectancy,
            'average_win': self.average_win,
            'average_loss': self.average_loss
        }


class EquitySnapshot(Base):
    """Equity snapshot for charting"""
    __tablename__ = 'equity_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    balance = Column(Float)
    equity = Column(Float)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)
    floating_profit = Column(Float, default=0.0)
    open_positions = Column(Integer, default=0)

    def __repr__(self):
        return f"<EquitySnapshot(timestamp={self.timestamp}, equity={self.equity})>"

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'free_margin': self.free_margin,
            'floating_profit': self.floating_profit,
            'open_positions': self.open_positions
        }


class NewsEvent(Base):
    """Stored news events"""
    __tablename__ = 'news_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_time = Column(DateTime, index=True)
    currency = Column(String(10))
    event_name = Column(String(200))
    impact = Column(String(10))  # low, medium, high
    actual = Column(String(50), nullable=True)
    forecast = Column(String(50), nullable=True)
    previous = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<NewsEvent(time={self.event_time}, currency={self.currency}, name={self.event_name})>"
