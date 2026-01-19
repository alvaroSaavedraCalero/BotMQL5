"""
Helper Functions Module
Common utility functions for the trading bot
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
import pytz


def get_utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(pytz.UTC)


def get_local_now(timezone: str = "UTC") -> datetime:
    """Get current local time in specified timezone"""
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def is_trading_session(current_time: datetime = None,
                       london_start: int = 8, london_end: int = 12,
                       ny_start: int = 13, ny_end: int = 17) -> Tuple[bool, str]:
    """
    Check if current time is within trading session

    Args:
        current_time: Time to check (default: now UTC)
        london_start: London session start hour (UTC)
        london_end: London session end hour (UTC)
        ny_start: New York session start hour (UTC)
        ny_end: New York session end hour (UTC)

    Returns:
        Tuple of (is_session_active, session_name)
    """
    if current_time is None:
        current_time = get_utc_now()

    hour = current_time.hour

    in_london = london_start <= hour < london_end
    in_ny = ny_start <= hour < ny_end

    if in_london and in_ny:
        return True, "London/NY Overlap"
    elif in_london:
        return True, "London"
    elif in_ny:
        return True, "New York"
    else:
        return False, "Closed"


def pips_to_price(pips: int, digits: int) -> float:
    """
    Convert pips to price difference

    Args:
        pips: Number of pips
        digits: Symbol digits (4 or 5 typically)

    Returns:
        Price difference
    """
    if digits == 5 or digits == 3:
        return pips * 0.0001  # 5-digit broker
    elif digits == 4 or digits == 2:
        return pips * 0.001 if digits == 3 else pips * 0.0001
    return pips * 0.0001


def price_to_pips(price_diff: float, digits: int) -> int:
    """
    Convert price difference to pips

    Args:
        price_diff: Price difference
        digits: Symbol digits

    Returns:
        Number of pips
    """
    if digits == 5 or digits == 3:
        return int(round(price_diff / 0.0001))
    elif digits == 4 or digits == 2:
        return int(round(price_diff / 0.001 if digits == 3 else price_diff / 0.0001))
    return int(round(price_diff / 0.0001))


def calculate_pip_value(symbol: str, lot_size: float, account_currency: str = "USD") -> float:
    """
    Calculate pip value for a position

    Args:
        symbol: Trading symbol
        lot_size: Position size in lots
        account_currency: Account currency

    Returns:
        Pip value in account currency
    """
    # Simplified calculation for major USD pairs
    # For accurate calculation, need real-time exchange rates

    standard_lot = 100000
    position_size = lot_size * standard_lot

    # For pairs where USD is quote currency
    usd_quote_pairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD']
    # For pairs where USD is base currency
    usd_base_pairs = ['USDJPY', 'USDCHF', 'USDCAD']
    # JPY pairs
    jpy_pairs = ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY']

    if symbol in usd_quote_pairs:
        pip_value = position_size * 0.0001
    elif symbol in jpy_pairs:
        pip_value = position_size * 0.01 / 100  # Approximate
    else:
        pip_value = position_size * 0.0001  # Default

    return pip_value


def calculate_lot_size(balance: float, risk_percent: float, sl_pips: int,
                       pip_value_per_lot: float = 10.0) -> float:
    """
    Calculate lot size based on risk

    Args:
        balance: Account balance
        risk_percent: Risk percentage per trade
        sl_pips: Stop loss in pips
        pip_value_per_lot: Pip value for 1 standard lot

    Returns:
        Calculated lot size
    """
    if sl_pips <= 0:
        return 0.01  # Minimum

    risk_amount = balance * (risk_percent / 100)
    lot_size = risk_amount / (sl_pips * pip_value_per_lot)

    # Normalize to 0.01 increments
    lot_size = max(0.01, round(lot_size, 2))

    return lot_size


def format_currency(value: float, currency: str = "USD", decimals: int = 2) -> str:
    """Format value as currency string"""
    symbol_map = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    symbol = symbol_map.get(currency, currency + " ")
    return f"{symbol}{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage string"""
    return f"{value:.{decimals}f}%"


def format_time_delta(seconds: int) -> str:
    """Format seconds as human-readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def calculate_win_rate(winners: int, total: int) -> float:
    """Calculate win rate percentage"""
    if total == 0:
        return 0.0
    return (winners / total) * 100


def calculate_profit_factor(gross_profit: float, gross_loss: float) -> float:
    """Calculate profit factor"""
    if gross_loss == 0:
        return 0.0 if gross_profit == 0 else float('inf')
    return gross_profit / abs(gross_loss)


def calculate_expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Calculate expectancy per trade

    Args:
        win_rate: Win rate as percentage (0-100)
        avg_win: Average winning trade amount
        avg_loss: Average losing trade amount (positive value)

    Returns:
        Expected profit per trade
    """
    win_rate_decimal = win_rate / 100
    return (win_rate_decimal * avg_win) - ((1 - win_rate_decimal) * abs(avg_loss))


def is_market_open(symbol: str = None) -> bool:
    """
    Check if forex market is open

    Note: Forex market is open 24/5
    Closed from Friday 5pm ET to Sunday 5pm ET
    """
    now = get_utc_now()

    # Weekend check (Saturday or Sunday before 10pm UTC)
    if now.weekday() == 5:  # Saturday
        return False
    elif now.weekday() == 6:  # Sunday
        # Market opens at 10pm UTC Sunday
        if now.hour < 22:
            return False

    # Friday close check
    if now.weekday() == 4 and now.hour >= 22:  # Friday after 10pm UTC
        return False

    return True


def get_session_info() -> dict:
    """Get current trading session information"""
    now = get_utc_now()
    hour = now.hour

    # Session times (UTC)
    sessions = {
        'Sydney': (22, 7),     # 10pm - 7am UTC
        'Tokyo': (0, 9),       # 12am - 9am UTC
        'London': (8, 17),     # 8am - 5pm UTC
        'New York': (13, 22)   # 1pm - 10pm UTC
    }

    active_sessions = []

    for session, (start, end) in sessions.items():
        if start < end:
            if start <= hour < end:
                active_sessions.append(session)
        else:  # Crosses midnight
            if hour >= start or hour < end:
                active_sessions.append(session)

    return {
        'current_time_utc': now.strftime("%H:%M:%S"),
        'active_sessions': active_sessions,
        'is_market_open': is_market_open()
    }
