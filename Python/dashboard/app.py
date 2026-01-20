"""
Main Dashboard Application
Real-time trading dashboard using Dash and Plotly
"""

import logging
from datetime import datetime
from typing import Optional

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from .layouts import create_layout
from .callbacks import register_callbacks

logger = logging.getLogger(__name__)


def create_dashboard(config, socket_server=None, risk_manager=None,
                     news_filter=None, mt5_connector=None):
    """
    Create and configure the Dash dashboard application

    Args:
        config: Configuration object
        socket_server: SocketServer instance
        risk_manager: RiskManager instance
        news_filter: NewsFilter instance
        mt5_connector: MT5Connector instance

    Returns:
        Dash application instance
    """

    # Create Dash app with Bootstrap theme
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.DARKLY,  # Dark theme
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ],
        suppress_callback_exceptions=True,
        update_title=None  # Disable "Updating..." title
    )

    app.title = "Multi-TF Scalping Bot Dashboard"

    # Store components in app
    app.socket_server = socket_server
    app.risk_manager = risk_manager
    app.news_filter = news_filter
    app.mt5_connector = mt5_connector
    app.bot_config = config

    # Create layout
    app.layout = create_layout(config)

    # Register callbacks
    register_callbacks(app)

    return app


def run_dashboard(app, host='0.0.0.0', port=8050, debug=False):
    """
    Run the dashboard server

    Args:
        app: Dash application instance
        host: Host address
        port: Port number
        debug: Enable debug mode
    """
    logger.info(f"Starting dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))

    from config import Config

    config = Config()
    app = create_dashboard(config)
    run_dashboard(app, debug=True)
