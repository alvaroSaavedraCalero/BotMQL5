"""
Socket Server Module
Handles file-based communication with MT5 EA
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message structure for MT5 communication"""
    msg_type: str
    data: Dict
    timestamp: datetime


class SocketServer:
    """
    File-based communication server for MT5

    MT5 doesn't support direct socket connections in MQL5,
    so we use shared files for communication.
    """

    def __init__(self, config):
        """
        Initialize Socket Server

        Args:
            config: Configuration object
        """
        self.config = config

        # File paths
        self.status_file = config.status_file
        self.signal_file = config.signal_file
        self.command_file = config.command_file
        self.heartbeat_file = config.heartbeat_file
        self.trades_file = config.trades_file

        # Callbacks
        self.on_status_update: Optional[Callable] = None
        self.on_trade_update: Optional[Callable] = None
        self.on_heartbeat: Optional[Callable] = None

        # State
        self.running = False
        self.last_status: Optional[Dict] = None
        self.last_heartbeat: Optional[datetime] = None
        self.mt5_connected = False

        # Polling thread
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_interval = 1.0  # seconds

    def start(self):
        """Start the file polling server"""
        if self.running:
            logger.warning("Server already running")
            return

        self.running = True

        # Start polling thread
        self._poll_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._poll_thread.start()

        logger.info("Socket server started")

    def stop(self):
        """Stop the server"""
        self.running = False

        if self._poll_thread:
            self._poll_thread.join(timeout=5)

        logger.info("Socket server stopped")

    def _polling_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                # Check status file
                status = self._read_json_file(self.status_file)
                if status and status != self.last_status:
                    self.last_status = status
                    if self.on_status_update:
                        self.on_status_update(status)

                # Check trades file
                trades = self._read_json_file(self.trades_file)
                if trades:
                    if self.on_trade_update:
                        self.on_trade_update(trades)
                    # Clear file after reading
                    self._clear_file(self.trades_file)

                # Check heartbeat
                heartbeat = self._read_json_file(self.heartbeat_file)
                if heartbeat:
                    timestamp = heartbeat.get('timestamp', 0)
                    self.last_heartbeat = datetime.fromtimestamp(timestamp)
                    self.mt5_connected = (datetime.now().timestamp() - timestamp) < 60
                    if self.on_heartbeat:
                        self.on_heartbeat(heartbeat)

            except Exception as e:
                logger.error(f"Polling error: {e}")

            time.sleep(self._poll_interval)

    def _read_json_file(self, filepath: Path) -> Optional[Dict]:
        """Read JSON from file"""
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"Error reading {filepath}: {e}")

        return None

    def _write_json_file(self, filepath: Path, data: Dict) -> bool:
        """Write JSON to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing {filepath}: {e}")
            return False

    def _clear_file(self, filepath: Path):
        """Clear file contents"""
        try:
            with open(filepath, 'w') as f:
                f.write('')
        except Exception as e:
            logger.debug(f"Error clearing {filepath}: {e}")

    def send_signal(self, signal_type: str, symbol: str, sl_pips: int,
                    tp1_pips: int = None, tp2_pips: int = None) -> bool:
        """
        Send trading signal to MT5

        Args:
            signal_type: "BUY" or "SELL"
            symbol: Trading symbol
            sl_pips: Stop loss in pips
            tp1_pips: Take profit 1 in pips (optional)
            tp2_pips: Take profit 2 in pips (optional)

        Returns:
            bool: True if successful
        """
        if tp1_pips is None:
            tp1_pips = sl_pips * 2  # Default 1:2 R:R
        if tp2_pips is None:
            tp2_pips = sl_pips * 3  # Default 1:3 R:R

        data = {
            "type": "SIGNAL",
            "action": signal_type.upper(),
            "symbol": symbol,
            "sl_pips": sl_pips,
            "tp1_pips": tp1_pips,
            "tp2_pips": tp2_pips,
            "timestamp": int(datetime.now().timestamp())
        }

        return self._write_json_file(self.signal_file, data)

    def send_command(self, command: str, params: Dict = None) -> bool:
        """
        Send command to MT5

        Args:
            command: Command string
            params: Optional parameters

        Returns:
            bool: True if successful
        """
        data = {
            "type": "COMMAND",
            "command": command,
            "timestamp": int(datetime.now().timestamp())
        }

        if params:
            data["params"] = params

        return self._write_json_file(self.command_file, data)

    def pause_bot(self) -> bool:
        """Send pause command"""
        return self.send_command("PAUSE")

    def resume_bot(self) -> bool:
        """Send resume command"""
        return self.send_command("RESUME")

    def close_all_positions(self) -> bool:
        """Send close all command"""
        return self.send_command("CLOSE_ALL")

    def request_status(self) -> bool:
        """Request status update"""
        return self.send_command("STATUS")

    def set_news_block(self, blocked: bool) -> bool:
        """Set news block status"""
        return self.send_command(f"NEWS_BLOCK:{1 if blocked else 0}")

    def get_status(self) -> Optional[Dict]:
        """Get last status update"""
        return self.last_status

    def is_mt5_connected(self) -> bool:
        """Check if MT5 EA is connected"""
        return self.mt5_connected

    def get_connection_info(self) -> Dict:
        """Get connection status info"""
        return {
            'mt5_connected': self.mt5_connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'server_running': self.running,
            'last_status': self.last_status
        }


class AsyncSocketServer(SocketServer):
    """Async version of SocketServer"""

    async def start_async(self):
        """Start async polling"""
        self.running = True
        asyncio.create_task(self._async_polling_loop())
        logger.info("Async socket server started")

    async def _async_polling_loop(self):
        """Async polling loop"""
        while self.running:
            try:
                # Check status file
                status = self._read_json_file(self.status_file)
                if status and status != self.last_status:
                    self.last_status = status
                    if self.on_status_update:
                        if asyncio.iscoroutinefunction(self.on_status_update):
                            await self.on_status_update(status)
                        else:
                            self.on_status_update(status)

                # Check trades file
                trades = self._read_json_file(self.trades_file)
                if trades:
                    if self.on_trade_update:
                        if asyncio.iscoroutinefunction(self.on_trade_update):
                            await self.on_trade_update(trades)
                        else:
                            self.on_trade_update(trades)
                    self._clear_file(self.trades_file)

                # Check heartbeat
                heartbeat = self._read_json_file(self.heartbeat_file)
                if heartbeat:
                    timestamp = heartbeat.get('timestamp', 0)
                    self.last_heartbeat = datetime.fromtimestamp(timestamp)
                    self.mt5_connected = (datetime.now().timestamp() - timestamp) < 60

            except Exception as e:
                logger.error(f"Async polling error: {e}")

            await asyncio.sleep(self._poll_interval)
