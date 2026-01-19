"""
Multi-TF Scalping Bot for MetaTrader 5
Main Entry Point

This module initializes and runs all components:
- MT5 Connector
- Signal Engine
- Risk Manager
- News Filter
- Socket Server (for communication with MT5 EA)
- Dashboard (Dash web interface)
"""

import sys
import signal
import threading
import argparse
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from utils.logger import setup_logging, TradingLogger
from core.mt5_connector import MT5Connector
from core.signal_engine import SignalEngine
from core.risk_manager import RiskManager
from core.news_filter import NewsFilter
from communication.socket_server import SocketServer
from communication.message_handler import MessageHandler
from data.database import Database
from dashboard.app import create_dashboard, run_dashboard


# Global instances
logger = None
trading_logger = None
mt5_connector = None
signal_engine = None
risk_manager = None
news_filter = None
socket_server = None
message_handler = None
database = None
dashboard_app = None


def setup_components():
    """Initialize all system components"""
    global logger, trading_logger, mt5_connector, signal_engine
    global risk_manager, news_filter, socket_server, message_handler, database

    # Setup logging
    logger = setup_logging(
        log_level=config.system.log_level,
        log_dir=config.paths.logs_dir
    )
    trading_logger = TradingLogger("TradingBot")

    logger.info("=" * 60)
    logger.info("Multi-TF Scalping Bot for MetaTrader 5")
    logger.info("=" * 60)

    # Initialize database
    logger.info("Initializing database...")
    database = Database(config.database_url)

    # Initialize MT5 connector
    logger.info("Initializing MT5 connector...")
    mt5_connector = MT5Connector(config)
    if not mt5_connector.initialize():
        logger.warning("MT5 not available, running in file-only mode")

    # Initialize risk manager
    logger.info("Initializing risk manager...")
    risk_manager = RiskManager(config)

    # Get initial balance
    account = mt5_connector.get_account_info()
    if account:
        risk_manager.initialize(account.balance)
        logger.info(f"Account balance: ${account.balance:,.2f}")
    else:
        risk_manager.initialize(10000)  # Default for testing
        logger.warning("Using default balance for risk calculations")

    # Initialize signal engine
    logger.info("Initializing signal engine...")
    signal_engine = SignalEngine(config, mt5_connector)

    # Initialize news filter
    logger.info("Initializing news filter...")
    news_filter = NewsFilter(config)
    news_filter.fetch_news_sync()

    # Initialize message handler
    logger.info("Initializing message handler...")
    message_handler = MessageHandler()

    # Register message callbacks
    message_handler.register_status_callback(on_status_update)
    message_handler.register_trade_callback(on_trade_update)

    # Initialize socket server
    logger.info("Initializing socket server...")
    socket_server = SocketServer(config)
    socket_server.on_status_update = lambda data: message_handler.process_message(data)
    socket_server.on_trade_update = lambda data: message_handler.process_message(data)

    logger.info("All components initialized successfully")


def on_status_update(status):
    """Handle status updates from MT5"""
    global risk_manager

    try:
        account = status.account
        risk_manager.update(
            current_equity=account.get('equity', 0),
            current_balance=account.get('balance', 0)
        )

        # Check risk status
        risk_status = risk_manager.can_trade(account.get('equity', 0))
        if not risk_status.can_trade:
            trading_logger.risk_warning(
                risk_status.reason.split(':')[0],
                risk_status.current_drawdown if risk_status.max_dd_exceeded else risk_status.daily_drawdown,
                config.trading.max_drawdown if risk_status.max_dd_exceeded else config.trading.max_daily_drawdown
            )

        # Save equity snapshot
        if database:
            database.add_equity_snapshot(
                balance=account.get('balance', 0),
                equity=account.get('equity', 0),
                margin=account.get('margin', 0),
                free_margin=account.get('free_margin', 0),
                floating_profit=account.get('profit', 0),
                open_positions=account.get('open_positions', 0)
            )

    except Exception as e:
        logger.error(f"Error processing status update: {e}")


def on_trade_update(trade):
    """Handle trade updates from MT5"""
    global database, risk_manager

    try:
        if trade.action.value == "OPEN":
            trading_logger.trade_open(
                ticket=trade.ticket,
                symbol=trade.symbol,
                trade_type=trade.trade_type,
                volume=trade.volume,
                price=trade.price,
                sl=trade.sl,
                tp=trade.tp
            )

            if database:
                database.add_trade({
                    'ticket': trade.ticket,
                    'symbol': trade.symbol,
                    'trade_type': trade.trade_type,
                    'volume': trade.volume,
                    'open_price': trade.price,
                    'stop_loss': trade.sl,
                    'take_profit': trade.tp,
                    'magic_number': config.system.magic_number
                })

            risk_manager.record_trade_open()

        elif trade.action.value == "CLOSE":
            trading_logger.trade_close(
                ticket=trade.ticket,
                symbol=trade.symbol,
                profit=trade.profit,
                reason=trade.reason
            )

            if database:
                database.update_trade_close(
                    ticket=trade.ticket,
                    close_price=trade.price,
                    profit=trade.profit
                )

            risk_manager.record_trade_close(trade.profit)

        elif trade.action.value == "PARTIAL_CLOSE":
            trading_logger.trade_partial_close(
                ticket=trade.ticket,
                closed_volume=trade.volume,
                remaining=0  # Would need to track this
            )

    except Exception as e:
        logger.error(f"Error processing trade update: {e}")


def run_signal_scanner():
    """Background thread for scanning trading signals"""
    import time

    logger.info("Signal scanner started")

    while True:
        try:
            # Check if we can trade
            if not socket_server.is_mt5_connected():
                time.sleep(5)
                continue

            # Update news filter status to MT5
            news_filter.send_news_block_to_mt5(mt5_connector)

            # Check for signals (this would be enhanced to scan multiple symbols)
            for symbol in config.system.symbols[:3]:  # Limit for performance
                result = signal_engine.get_signal(symbol)

                if result.signal_type.value != "NONE":
                    trading_logger.signal(
                        signal_type=result.signal_type.value,
                        symbol=symbol,
                        confidence=result.confidence,
                        reason=result.reason
                    )

                    # Send signal to MT5
                    socket_server.send_signal(
                        signal_type=result.signal_type.value,
                        symbol=symbol,
                        sl_pips=config.trading.stop_loss_pips
                    )

        except Exception as e:
            logger.error(f"Signal scanner error: {e}")

        time.sleep(60)  # Scan every minute


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    cleanup()
    sys.exit(0)


def cleanup():
    """Cleanup on shutdown"""
    logger.info("Cleaning up...")

    if socket_server:
        socket_server.stop()

    if mt5_connector:
        mt5_connector.shutdown()

    if database:
        database.cleanup_old_snapshots()

    logger.info("Cleanup complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-TF Scalping Bot for MetaTrader 5")
    parser.add_argument("--no-dashboard", action="store_true", help="Run without dashboard")
    parser.add_argument("--no-signals", action="store_true", help="Run without signal scanner")
    parser.add_argument("--port", type=int, default=8050, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize components
        setup_components()

        # Start socket server
        socket_server.start()

        # Start signal scanner thread
        if not args.no_signals:
            signal_thread = threading.Thread(target=run_signal_scanner, daemon=True)
            signal_thread.start()
            logger.info("Signal scanner thread started")

        # Create and run dashboard
        if not args.no_dashboard:
            global dashboard_app
            dashboard_app = create_dashboard(
                config=config,
                socket_server=socket_server,
                risk_manager=risk_manager,
                news_filter=news_filter,
                mt5_connector=mt5_connector
            )

            logger.info(f"Starting dashboard on http://localhost:{args.port}")
            run_dashboard(dashboard_app, port=args.port, debug=args.debug)
        else:
            # Keep running without dashboard
            logger.info("Running without dashboard (press Ctrl+C to stop)")
            while True:
                import time
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
