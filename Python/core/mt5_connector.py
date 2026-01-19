"""
MetaTrader 5 Connector Module
Handles all communication with MT5 terminal
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class AccountInfo:
    """Account information structure"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    profit: float
    leverage: int
    currency: str


@dataclass
class Position:
    """Position information structure"""
    ticket: int
    symbol: str
    type: OrderType
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    open_time: datetime
    magic: int
    comment: str


@dataclass
class Signal:
    """Trading signal structure"""
    type: str  # "BUY" or "SELL"
    symbol: str
    sl_pips: int
    tp1_pips: int
    tp2_pips: int
    timestamp: int


class MT5Connector:
    """
    Connector class for MetaTrader 5
    Handles initialization, data retrieval, and order execution
    """

    def __init__(self, config):
        """
        Initialize MT5 Connector

        Args:
            config: Configuration object with paths and settings
        """
        self.config = config
        self.connected = False
        self.last_error = None

        # File paths for communication
        self.status_file = config.status_file
        self.signal_file = config.signal_file
        self.command_file = config.command_file
        self.heartbeat_file = config.heartbeat_file
        self.trades_file = config.trades_file

        # Cache
        self._account_info_cache = None
        self._positions_cache = []
        self._last_cache_update = None

    def initialize(self) -> bool:
        """
        Initialize connection to MT5

        Returns:
            bool: True if successful, False otherwise
        """
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available. Running in file-only mode.")
            return True  # Continue with file-based communication

        try:
            if not mt5.initialize():
                self.last_error = f"MT5 initialization failed: {mt5.last_error()}"
                logger.error(self.last_error)
                return False

            # Get terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                self.last_error = "Failed to get terminal info"
                logger.error(self.last_error)
                return False

            self.connected = True
            logger.info(f"MT5 connected: {terminal_info.name} - Build {terminal_info.build}")

            # Get account info
            account = self.get_account_info()
            if account:
                logger.info(f"Account: {account.balance} {account.currency} - Leverage 1:{account.leverage}")

            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"MT5 initialization error: {e}")
            return False

    def shutdown(self):
        """Shutdown MT5 connection"""
        if MT5_AVAILABLE and self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 connection closed")

    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get account information

        Returns:
            AccountInfo object or None if failed
        """
        if MT5_AVAILABLE and self.connected:
            try:
                info = mt5.account_info()
                if info is None:
                    return None

                return AccountInfo(
                    balance=info.balance,
                    equity=info.equity,
                    margin=info.margin,
                    free_margin=info.margin_free,
                    profit=info.profit,
                    leverage=info.leverage,
                    currency=info.currency
                )
            except Exception as e:
                logger.error(f"Error getting account info: {e}")
                return None

        # File-based fallback
        return self._read_account_from_file()

    def _read_account_from_file(self) -> Optional[AccountInfo]:
        """Read account info from status file"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    data = json.load(f)

                if 'account' in data:
                    acc = data['account']
                    return AccountInfo(
                        balance=acc.get('balance', 0),
                        equity=acc.get('equity', 0),
                        margin=acc.get('margin', 0),
                        free_margin=acc.get('free_margin', 0),
                        profit=acc.get('profit', 0),
                        leverage=100,  # Default
                        currency="USD"  # Default
                    )
        except Exception as e:
            logger.debug(f"Error reading account from file: {e}")

        return None

    def get_positions(self, symbol: str = None, magic: int = None) -> List[Position]:
        """
        Get open positions

        Args:
            symbol: Filter by symbol (optional)
            magic: Filter by magic number (optional)

        Returns:
            List of Position objects
        """
        positions = []

        if MT5_AVAILABLE and self.connected:
            try:
                if symbol:
                    mt5_positions = mt5.positions_get(symbol=symbol)
                else:
                    mt5_positions = mt5.positions_get()

                if mt5_positions is None:
                    return []

                for pos in mt5_positions:
                    if magic and pos.magic != magic:
                        continue

                    positions.append(Position(
                        ticket=pos.ticket,
                        symbol=pos.symbol,
                        type=OrderType.BUY if pos.type == mt5.ORDER_TYPE_BUY else OrderType.SELL,
                        volume=pos.volume,
                        open_price=pos.price_open,
                        current_price=pos.price_current,
                        sl=pos.sl,
                        tp=pos.tp,
                        profit=pos.profit,
                        open_time=datetime.fromtimestamp(pos.time),
                        magic=pos.magic,
                        comment=pos.comment
                    ))

            except Exception as e:
                logger.error(f"Error getting positions: {e}")

        return positions

    def get_ohlcv(self, symbol: str, timeframe: int, count: int = 100) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data

        Args:
            symbol: Trading symbol
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_M1)
            count: Number of bars to retrieve

        Returns:
            DataFrame with OHLCV data or None
        """
        if not MT5_AVAILABLE or not self.connected:
            logger.warning("MT5 not available for OHLCV data")
            return None

        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error getting OHLCV: {e}")
            return None

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with symbol info or None
        """
        if not MT5_AVAILABLE or not self.connected:
            return None

        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None

            return {
                'name': info.name,
                'digits': info.digits,
                'point': info.point,
                'spread': info.spread,
                'trade_mode': info.trade_mode,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'bid': info.bid,
                'ask': info.ask
            }

        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def send_signal(self, signal: Signal) -> bool:
        """
        Send trading signal to MT5 EA via file

        Args:
            signal: Signal object

        Returns:
            bool: True if successful
        """
        try:
            data = {
                "type": "SIGNAL",
                "action": signal.type,
                "symbol": signal.symbol,
                "sl_pips": signal.sl_pips,
                "tp1_pips": signal.tp1_pips,
                "tp2_pips": signal.tp2_pips,
                "timestamp": signal.timestamp
            }

            with open(self.signal_file, 'w') as f:
                json.dump(data, f)

            logger.info(f"Signal sent: {signal.type} {signal.symbol}")
            return True

        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            return False

    def send_command(self, command: str, params: Dict = None) -> bool:
        """
        Send command to MT5 EA

        Args:
            command: Command string (PAUSE, RESUME, CLOSE_ALL, etc.)
            params: Optional parameters

        Returns:
            bool: True if successful
        """
        try:
            data = {
                "type": "COMMAND",
                "command": command,
                "timestamp": int(datetime.now().timestamp())
            }

            if params:
                data["params"] = params

            with open(self.command_file, 'w') as f:
                json.dump(data, f)

            logger.info(f"Command sent: {command}")
            return True

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

    def read_status(self) -> Optional[Dict]:
        """
        Read status from MT5 EA

        Returns:
            Dictionary with status or None
        """
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
        except Exception as e:
            logger.debug(f"Error reading status: {e}")

        return None

    def read_trades(self) -> Optional[Dict]:
        """
        Read trade updates from MT5 EA

        Returns:
            Dictionary with trade info or None
        """
        try:
            if self.trades_file.exists():
                with open(self.trades_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
        except Exception as e:
            logger.debug(f"Error reading trades: {e}")

        return None

    def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        if MT5_AVAILABLE and self.connected:
            try:
                info = mt5.terminal_info()
                return info is not None and info.connected
            except:
                return False

        # File-based check - verify heartbeat
        return self._check_heartbeat()

    def _check_heartbeat(self) -> bool:
        """Check if EA is alive via heartbeat file"""
        try:
            if self.heartbeat_file.exists():
                with open(self.heartbeat_file, 'r') as f:
                    data = json.load(f)

                timestamp = data.get('timestamp', 0)
                # Consider alive if heartbeat within last 60 seconds
                if datetime.now().timestamp() - timestamp < 60:
                    return True
        except:
            pass

        return False

    def get_spread(self, symbol: str) -> float:
        """
        Get current spread in pips

        Args:
            symbol: Trading symbol

        Returns:
            Spread in pips
        """
        info = self.get_symbol_info(symbol)
        if info:
            # Convert spread from points to pips
            digits = info.get('digits', 5)
            spread_points = info.get('spread', 0)

            if digits == 5 or digits == 3:
                return spread_points / 10.0
            return float(spread_points)

        return 0.0
