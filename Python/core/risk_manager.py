"""
Risk Manager Module
Handles risk calculations and position sizing
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DailyStats:
    """Daily trading statistics"""
    date: date = field(default_factory=date.today)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    max_drawdown: float = 0.0
    start_balance: float = 0.0
    current_balance: float = 0.0

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def profit_factor(self) -> float:
        """Calculate profit factor"""
        if self.gross_loss == 0:
            return 0.0 if self.gross_profit == 0 else float('inf')
        return self.gross_profit / self.gross_loss

    @property
    def expectancy(self) -> float:
        """Calculate expectancy per trade"""
        if self.total_trades == 0:
            return 0.0
        return self.net_profit / self.total_trades


@dataclass
class RiskStatus:
    """Current risk status"""
    can_trade: bool = True
    max_dd_exceeded: bool = False
    daily_dd_exceeded: bool = False
    daily_ops_exceeded: bool = False
    reason: str = ""
    current_drawdown: float = 0.0
    daily_drawdown: float = 0.0
    daily_operations: int = 0


class RiskManager:
    """
    Risk Manager for trading operations

    Manages:
    - Position sizing based on risk percentage
    - Drawdown tracking and limits
    - Daily operation limits
    - Trade statistics
    """

    def __init__(self, config):
        """
        Initialize Risk Manager

        Args:
            config: Configuration object
        """
        self.config = config

        # Risk parameters
        self.max_drawdown = config.trading.max_drawdown
        self.max_daily_drawdown = config.trading.max_daily_drawdown
        self.max_daily_operations = config.trading.max_daily_operations
        self.risk_per_trade = config.trading.risk_per_trade
        self.max_spread = config.trading.spread_maximo

        # State tracking
        self.initial_balance = 0.0
        self.daily_start_balance = 0.0
        self.max_equity_reached = 0.0
        self.daily_max_equity = 0.0

        # Daily stats
        self.daily_stats = DailyStats()

        # History
        self.trade_history: List[Dict] = []

    def initialize(self, balance: float):
        """
        Initialize with starting balance

        Args:
            balance: Account starting balance
        """
        self.initial_balance = balance
        self.daily_start_balance = balance
        self.max_equity_reached = balance
        self.daily_max_equity = balance

        self.daily_stats = DailyStats(
            date=date.today(),
            start_balance=balance,
            current_balance=balance
        )

        logger.info(f"RiskManager initialized - Balance: {balance}")

    def new_day_reset(self, current_balance: float):
        """
        Reset daily statistics for new trading day

        Args:
            current_balance: Current account balance
        """
        today = date.today()

        if self.daily_stats.date != today:
            # Save previous day stats to history
            self._save_daily_stats()

            # Reset for new day
            self.daily_start_balance = current_balance
            self.daily_max_equity = current_balance

            self.daily_stats = DailyStats(
                date=today,
                start_balance=current_balance,
                current_balance=current_balance
            )

            logger.info(f"New day reset - Balance: {current_balance}")

    def _save_daily_stats(self):
        """Save daily stats to history"""
        if self.daily_stats.total_trades > 0:
            self.trade_history.append({
                'date': self.daily_stats.date.isoformat(),
                'total_trades': self.daily_stats.total_trades,
                'winning_trades': self.daily_stats.winning_trades,
                'losing_trades': self.daily_stats.losing_trades,
                'net_profit': self.daily_stats.net_profit,
                'win_rate': self.daily_stats.win_rate,
                'profit_factor': self.daily_stats.profit_factor
            })

    def update(self, current_equity: float, current_balance: float):
        """
        Update risk calculations

        Args:
            current_equity: Current account equity
            current_balance: Current account balance
        """
        # Check for new day
        self.new_day_reset(current_balance)

        # Update max equity reached
        if current_equity > self.max_equity_reached:
            self.max_equity_reached = current_equity

        if current_equity > self.daily_max_equity:
            self.daily_max_equity = current_equity

        # Update daily stats
        self.daily_stats.current_balance = current_balance

    def calculate_drawdown(self, current_equity: float) -> float:
        """
        Calculate current drawdown from max equity

        Args:
            current_equity: Current account equity

        Returns:
            Drawdown percentage
        """
        if self.max_equity_reached == 0:
            return 0.0

        drawdown = ((self.max_equity_reached - current_equity) / self.max_equity_reached) * 100
        return max(0.0, drawdown)

    def calculate_daily_drawdown(self, current_equity: float) -> float:
        """
        Calculate daily drawdown

        Args:
            current_equity: Current account equity

        Returns:
            Daily drawdown percentage
        """
        if self.daily_start_balance == 0:
            return 0.0

        daily_loss = self.daily_start_balance - current_equity
        if daily_loss <= 0:
            return 0.0

        return (daily_loss / self.daily_start_balance) * 100

    def can_trade(self, current_equity: float) -> RiskStatus:
        """
        Check if trading is allowed based on risk limits

        Args:
            current_equity: Current account equity

        Returns:
            RiskStatus object
        """
        status = RiskStatus()

        # Calculate current drawdowns
        status.current_drawdown = self.calculate_drawdown(current_equity)
        status.daily_drawdown = self.calculate_daily_drawdown(current_equity)
        status.daily_operations = self.daily_stats.total_trades

        # Check max drawdown
        if status.current_drawdown >= self.max_drawdown:
            status.can_trade = False
            status.max_dd_exceeded = True
            status.reason = f"Max drawdown exceeded: {status.current_drawdown:.2f}% >= {self.max_drawdown}%"
            return status

        # Check daily drawdown
        if status.daily_drawdown >= self.max_daily_drawdown:
            status.can_trade = False
            status.daily_dd_exceeded = True
            status.reason = f"Daily drawdown exceeded: {status.daily_drawdown:.2f}% >= {self.max_daily_drawdown}%"
            return status

        # Check daily operations
        if self.daily_stats.total_trades >= self.max_daily_operations:
            status.can_trade = False
            status.daily_ops_exceeded = True
            status.reason = f"Daily operations limit reached: {self.daily_stats.total_trades} >= {self.max_daily_operations}"
            return status

        status.can_trade = True
        return status

    def calculate_lot_size(self, balance: float, sl_pips: int, symbol_info: Dict) -> float:
        """
        Calculate position size based on risk percentage

        Args:
            balance: Account balance
            sl_pips: Stop loss in pips
            symbol_info: Symbol information dict

        Returns:
            Lot size (normalized)
        """
        if sl_pips <= 0:
            logger.warning("Invalid SL pips, using minimum lot")
            return symbol_info.get('volume_min', 0.01)

        # Calculate risk amount
        risk_amount = balance * (self.risk_per_trade / 100.0)

        # Get pip value (approximate for major pairs)
        # For accurate calculation, need symbol-specific tick value
        digits = symbol_info.get('digits', 5)
        point = symbol_info.get('point', 0.00001)

        # Pip value calculation (simplified for USD account)
        # For a more accurate calculation, would need to consider account currency
        if digits == 5 or digits == 3:
            pip_value = point * 10  # 5-digit broker
        else:
            pip_value = point

        # Estimate pip value per lot (standard lot = 100,000 units)
        pip_value_per_lot = pip_value * 100000

        # For JPY pairs, adjust
        if 'JPY' in symbol_info.get('name', ''):
            pip_value_per_lot = pip_value * 1000

        # Calculate lot size
        if pip_value_per_lot > 0:
            lot_size = risk_amount / (sl_pips * pip_value_per_lot)
        else:
            lot_size = symbol_info.get('volume_min', 0.01)

        # Normalize lot size
        lot_size = self.normalize_lot(lot_size, symbol_info)

        logger.debug(f"Lot calculation - Balance: {balance}, Risk: {risk_amount}, SL: {sl_pips} pips, Lot: {lot_size}")

        return lot_size

    def normalize_lot(self, lot: float, symbol_info: Dict) -> float:
        """
        Normalize lot size according to symbol specifications

        Args:
            lot: Raw lot size
            symbol_info: Symbol information dict

        Returns:
            Normalized lot size
        """
        min_lot = symbol_info.get('volume_min', 0.01)
        max_lot = symbol_info.get('volume_max', 100.0)
        lot_step = symbol_info.get('volume_step', 0.01)

        # Ensure minimum
        lot = max(lot, min_lot)

        # Ensure maximum
        lot = min(lot, max_lot)

        # Round to lot step
        if lot_step > 0:
            lot = int(lot / lot_step) * lot_step

        # Round to 2 decimal places
        lot = round(lot, 2)

        return lot

    def record_trade_open(self):
        """Record a new trade opened"""
        self.daily_stats.total_trades += 1
        logger.info(f"Trade opened - Daily total: {self.daily_stats.total_trades}")

    def record_trade_close(self, profit: float):
        """
        Record a trade closure

        Args:
            profit: Trade profit/loss
        """
        if profit > 0:
            self.daily_stats.winning_trades += 1
            self.daily_stats.gross_profit += profit
        else:
            self.daily_stats.losing_trades += 1
            self.daily_stats.gross_loss += abs(profit)

        self.daily_stats.net_profit = self.daily_stats.gross_profit - self.daily_stats.gross_loss

        # Update max drawdown if applicable
        if self.daily_stats.net_profit < -self.daily_stats.max_drawdown:
            self.daily_stats.max_drawdown = abs(self.daily_stats.net_profit)

        logger.info(f"Trade closed - Profit: {profit}, Net: {self.daily_stats.net_profit}")

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            'date': self.daily_stats.date.isoformat(),
            'total_trades': self.daily_stats.total_trades,
            'winning_trades': self.daily_stats.winning_trades,
            'losing_trades': self.daily_stats.losing_trades,
            'win_rate': round(self.daily_stats.win_rate, 2),
            'gross_profit': round(self.daily_stats.gross_profit, 2),
            'gross_loss': round(self.daily_stats.gross_loss, 2),
            'net_profit': round(self.daily_stats.net_profit, 2),
            'profit_factor': round(self.daily_stats.profit_factor, 2) if self.daily_stats.profit_factor != float('inf') else 'N/A',
            'expectancy': round(self.daily_stats.expectancy, 2),
            'max_drawdown': round(self.daily_stats.max_drawdown, 2),
            'start_balance': round(self.daily_stats.start_balance, 2),
            'current_balance': round(self.daily_stats.current_balance, 2)
        }

    def get_risk_limits(self) -> Dict:
        """Get risk limit settings"""
        return {
            'max_drawdown': self.max_drawdown,
            'max_daily_drawdown': self.max_daily_drawdown,
            'max_daily_operations': self.max_daily_operations,
            'risk_per_trade': self.risk_per_trade,
            'max_spread': self.max_spread
        }
