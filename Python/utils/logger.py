"""
Logging Configuration Module
Sets up colored logging for the application
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logging(log_level: str = "INFO", log_dir: Optional[Path] = None,
                  log_file: str = "trading_bot.log") -> logging.Logger:
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        log_file: Log file name

    Returns:
        Root logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    if COLORLOG_AVAILABLE:
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )

    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_dir provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Daily rotating log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = log_dir / f"{today}_{log_file}"

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING)

    logger.info(f"Logging initialized - Level: {log_level}")

    return logger


class TradingLogger:
    """
    Specialized logger for trading operations

    Provides structured logging for trades, signals, and errors
    """

    def __init__(self, name: str = "TradingBot"):
        self.logger = logging.getLogger(name)

    def trade_open(self, ticket: int, symbol: str, trade_type: str,
                   volume: float, price: float, sl: float, tp: float):
        """Log trade opening"""
        self.logger.info(
            f"TRADE OPEN | Ticket: {ticket} | {trade_type} {symbol} | "
            f"Vol: {volume} | Price: {price} | SL: {sl} | TP: {tp}"
        )

    def trade_close(self, ticket: int, symbol: str, profit: float, reason: str = ""):
        """Log trade closing"""
        profit_str = f"+{profit}" if profit >= 0 else str(profit)
        self.logger.info(
            f"TRADE CLOSE | Ticket: {ticket} | {symbol} | "
            f"P/L: {profit_str} | Reason: {reason}"
        )

    def trade_partial_close(self, ticket: int, closed_volume: float, remaining: float):
        """Log partial close"""
        self.logger.info(
            f"PARTIAL CLOSE | Ticket: {ticket} | "
            f"Closed: {closed_volume} | Remaining: {remaining}"
        )

    def signal(self, signal_type: str, symbol: str, confidence: float, reason: str):
        """Log trading signal"""
        self.logger.info(
            f"SIGNAL | {signal_type} {symbol} | "
            f"Confidence: {confidence:.1f}% | {reason}"
        )

    def risk_warning(self, warning_type: str, current: float, limit: float):
        """Log risk warning"""
        self.logger.warning(
            f"RISK WARNING | {warning_type} | "
            f"Current: {current:.2f} | Limit: {limit:.2f}"
        )

    def session_change(self, session: str, status: str):
        """Log session status change"""
        self.logger.info(f"SESSION | {session} | Status: {status}")

    def news_event(self, event_name: str, currency: str, impact: str, action: str):
        """Log news event"""
        self.logger.info(
            f"NEWS | {impact.upper()} | {currency} | {event_name} | Action: {action}"
        )

    def error(self, context: str, error: str):
        """Log error"""
        self.logger.error(f"ERROR | {context} | {error}")

    def connection_status(self, component: str, status: bool):
        """Log connection status"""
        status_str = "Connected" if status else "Disconnected"
        self.logger.info(f"CONNECTION | {component} | {status_str}")
