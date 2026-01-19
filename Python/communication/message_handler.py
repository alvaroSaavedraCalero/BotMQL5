"""
Message Handler Module
Processes messages between MT5 and Python components
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types"""
    STATUS = "STATUS"
    TRADE = "TRADE"
    SIGNAL = "SIGNAL"
    COMMAND = "COMMAND"
    HEARTBEAT = "HEARTBEAT"
    ERROR = "ERROR"


class TradeAction(Enum):
    """Trade action types"""
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    MODIFY = "MODIFY"


@dataclass
class StatusMessage:
    """Status message from MT5"""
    timestamp: datetime
    account: Dict
    daily_stats: Dict
    session: str
    bot_status: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'StatusMessage':
        return cls(
            timestamp=datetime.fromtimestamp(data.get('timestamp', 0)),
            account=data.get('account', {}),
            daily_stats=data.get('daily_stats', {}),
            session=data.get('session', 'Unknown'),
            bot_status=data.get('account', {}).get('bot_status', 'UNKNOWN')
        )


@dataclass
class TradeMessage:
    """Trade message from MT5"""
    timestamp: datetime
    action: TradeAction
    ticket: int
    symbol: str = ""
    trade_type: str = ""
    volume: float = 0.0
    price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    profit: float = 0.0
    reason: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> 'TradeMessage':
        return cls(
            timestamp=datetime.fromtimestamp(data.get('timestamp', 0)),
            action=TradeAction(data.get('action', 'OPEN')),
            ticket=data.get('ticket', 0),
            symbol=data.get('symbol', ''),
            trade_type=data.get('trade_type', ''),
            volume=data.get('volume', 0.0),
            price=data.get('open_price', data.get('price', 0.0)),
            sl=data.get('stop_loss', 0.0),
            tp=data.get('take_profit', 0.0),
            profit=data.get('profit', 0.0),
            reason=data.get('reason', '')
        )


@dataclass
class HeartbeatMessage:
    """Heartbeat message from MT5"""
    timestamp: datetime
    bot_name: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'HeartbeatMessage':
        return cls(
            timestamp=datetime.fromtimestamp(data.get('timestamp', 0)),
            bot_name=data.get('bot_name', 'Unknown'),
            version=data.get('version', '0.0.0')
        )


class MessageHandler:
    """
    Handles message parsing and event dispatching

    Provides a unified interface for processing messages
    from MT5 and triggering appropriate callbacks.
    """

    def __init__(self):
        """Initialize Message Handler"""
        # Callback registries
        self._status_callbacks: List[Callable] = []
        self._trade_callbacks: List[Callable] = []
        self._heartbeat_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []

        # Message history
        self._status_history: List[StatusMessage] = []
        self._trade_history: List[TradeMessage] = []
        self._max_history = 1000

        # Current state
        self.last_status: Optional[StatusMessage] = None
        self.last_heartbeat: Optional[HeartbeatMessage] = None
        self.open_trades: Dict[int, TradeMessage] = {}

    def register_status_callback(self, callback: Callable):
        """Register callback for status updates"""
        self._status_callbacks.append(callback)

    def register_trade_callback(self, callback: Callable):
        """Register callback for trade updates"""
        self._trade_callbacks.append(callback)

    def register_heartbeat_callback(self, callback: Callable):
        """Register callback for heartbeat updates"""
        self._heartbeat_callbacks.append(callback)

    def register_error_callback(self, callback: Callable):
        """Register callback for error messages"""
        self._error_callbacks.append(callback)

    def process_message(self, data: Dict):
        """
        Process incoming message

        Args:
            data: Raw message data
        """
        msg_type = data.get('type', '').upper()

        try:
            if msg_type == MessageType.STATUS.value:
                self._handle_status(data)
            elif msg_type == MessageType.TRADE.value:
                self._handle_trade(data)
            elif msg_type == MessageType.HEARTBEAT.value:
                self._handle_heartbeat(data)
            elif msg_type == MessageType.ERROR.value:
                self._handle_error(data)
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._trigger_error_callbacks({'error': str(e), 'data': data})

    def _handle_status(self, data: Dict):
        """Handle status message"""
        status = StatusMessage.from_dict(data)
        self.last_status = status

        # Add to history
        self._status_history.append(status)
        if len(self._status_history) > self._max_history:
            self._status_history.pop(0)

        # Trigger callbacks
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")

    def _handle_trade(self, data: Dict):
        """Handle trade message"""
        trade = TradeMessage.from_dict(data)

        # Update open trades tracking
        if trade.action == TradeAction.OPEN:
            self.open_trades[trade.ticket] = trade
        elif trade.action in [TradeAction.CLOSE, TradeAction.PARTIAL_CLOSE]:
            if trade.ticket in self.open_trades:
                if trade.action == TradeAction.CLOSE:
                    del self.open_trades[trade.ticket]
                else:
                    # Update volume for partial close
                    existing = self.open_trades[trade.ticket]
                    existing.volume = data.get('remaining_volume', existing.volume)

        # Add to history
        self._trade_history.append(trade)
        if len(self._trade_history) > self._max_history:
            self._trade_history.pop(0)

        # Trigger callbacks
        for callback in self._trade_callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")

    def _handle_heartbeat(self, data: Dict):
        """Handle heartbeat message"""
        heartbeat = HeartbeatMessage.from_dict(data)
        self.last_heartbeat = heartbeat

        # Trigger callbacks
        for callback in self._heartbeat_callbacks:
            try:
                callback(heartbeat)
            except Exception as e:
                logger.error(f"Heartbeat callback error: {e}")

    def _handle_error(self, data: Dict):
        """Handle error message"""
        self._trigger_error_callbacks(data)

    def _trigger_error_callbacks(self, data: Dict):
        """Trigger error callbacks"""
        for callback in self._error_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error callback error: {e}")

    def get_status_history(self, limit: int = 100) -> List[StatusMessage]:
        """Get recent status history"""
        return self._status_history[-limit:]

    def get_trade_history(self, limit: int = 100) -> List[TradeMessage]:
        """Get recent trade history"""
        return self._trade_history[-limit:]

    def get_open_trades(self) -> List[TradeMessage]:
        """Get currently open trades"""
        return list(self.open_trades.values())

    def get_stats_from_history(self) -> Dict:
        """Calculate stats from trade history"""
        if not self._trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }

        closed_trades = [
            t for t in self._trade_history
            if t.action == TradeAction.CLOSE
        ]

        total = len(closed_trades)
        winning = sum(1 for t in closed_trades if t.profit > 0)
        losing = sum(1 for t in closed_trades if t.profit < 0)
        total_profit = sum(t.profit for t in closed_trades)

        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'total_profit': round(total_profit, 2),
            'win_rate': round((winning / total * 100) if total > 0 else 0, 2)
        }

    def clear_history(self):
        """Clear message history"""
        self._status_history.clear()
        self._trade_history.clear()
        self.open_trades.clear()
