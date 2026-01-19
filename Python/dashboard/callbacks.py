"""
Dashboard Callbacks Module
Handles all interactive callbacks for the dashboard
"""

import json
from datetime import datetime
from dash import html, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go


def register_callbacks(app):
    """
    Register all dashboard callbacks

    Args:
        app: Dash application instance
    """

    # ==================== DATA FETCHING ====================

    @app.callback(
        Output('status-store', 'data'),
        Input('interval-fast', 'n_intervals')
    )
    def fetch_status(n):
        """Fetch status data from socket server"""
        if app.socket_server:
            status = app.socket_server.get_status()
            if status:
                return status

        # Return default status if no data
        return {
            'account': {
                'balance': 0,
                'equity': 0,
                'profit': 0,
                'free_margin': 0,
                'drawdown': 0,
                'daily_drawdown': 0,
                'open_positions': 0,
                'bot_status': 'DISCONNECTED'
            },
            'daily_stats': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'gross_profit': 0,
                'gross_loss': 0,
                'net_profit': 0
            },
            'session': 'Unknown',
            'timestamp': datetime.now().timestamp()
        }

    # ==================== HEADER UPDATES ====================

    @app.callback(
        Output('connection-status', 'children'),
        Input('interval-fast', 'n_intervals')
    )
    def update_connection_status(n):
        """Update connection status indicator"""
        connected = False
        if app.socket_server:
            connected = app.socket_server.is_mt5_connected()

        if connected:
            return html.Span([
                html.I(className="fas fa-circle text-success me-1"),
                "MT5 Connected"
            ])
        else:
            return html.Span([
                html.I(className="fas fa-circle text-danger me-1"),
                "MT5 Disconnected"
            ])

    @app.callback(
        Output('current-time', 'children'),
        Input('interval-fast', 'n_intervals')
    )
    def update_time(n):
        """Update current time display"""
        return datetime.now().strftime("%H:%M:%S")

    # ==================== BOT STATUS ====================

    @app.callback(
        [Output('bot-status-indicator', 'className'),
         Output('bot-status-text', 'children'),
         Output('bot-status-text', 'className')],
        Input('status-store', 'data')
    )
    def update_bot_status(data):
        """Update bot status indicator"""
        if not data:
            return "status-indicator bg-secondary", "Disconnected", "mb-0 ms-3 text-secondary"

        status = data.get('account', {}).get('bot_status', 'UNKNOWN')

        status_map = {
            'ACTIVE': ('bg-success', 'Active', 'text-success'),
            'WAITING': ('bg-info', 'Waiting', 'text-info'),
            'PAUSED': ('bg-warning', 'Paused', 'text-warning'),
            'DD_LIMIT': ('bg-danger', 'DD Limit', 'text-danger'),
            'DAILY_DD_LIMIT': ('bg-danger', 'Daily DD Limit', 'text-danger'),
            'DAILY_OPS_LIMIT': ('bg-warning', 'Ops Limit', 'text-warning'),
            'NEWS_FILTER': ('bg-info', 'News Filter', 'text-info'),
            'SESSION_CLOSED': ('bg-secondary', 'Session Closed', 'text-secondary'),
            'SPREAD_HIGH': ('bg-warning', 'Spread High', 'text-warning'),
            'ERROR': ('bg-danger', 'Error', 'text-danger'),
        }

        indicator, text, text_class = status_map.get(
            status, ('bg-secondary', status, 'text-secondary')
        )

        return f"status-indicator {indicator}", text, f"mb-0 ms-3 {text_class}"

    @app.callback(
        Output('current-session', 'children'),
        Input('status-store', 'data')
    )
    def update_session(data):
        """Update current session display"""
        if data:
            return data.get('session', 'Unknown')
        return 'Unknown'

    @app.callback(
        Output('daily-trades-count', 'children'),
        Input('status-store', 'data')
    )
    def update_daily_trades(data):
        """Update daily trades count"""
        if data:
            stats = data.get('daily_stats', {})
            total = stats.get('total_trades', 0)
            max_ops = app.config.trading.max_daily_operations if app.config else 10
            return f"{total} / {max_ops}"
        return "0 / 10"

    # ==================== ACCOUNT INFO ====================

    @app.callback(
        [Output('account-balance', 'children'),
         Output('account-equity', 'children'),
         Output('floating-pl', 'children'),
         Output('floating-pl', 'className'),
         Output('free-margin', 'children')],
        Input('status-store', 'data')
    )
    def update_account_info(data):
        """Update account information"""
        if not data:
            return "$0.00", "$0.00", "$0.00", "mb-0 fw-bold", "$0.00"

        account = data.get('account', {})
        balance = account.get('balance', 0)
        equity = account.get('equity', 0)
        profit = account.get('profit', 0)
        free_margin = account.get('free_margin', 0)

        profit_class = "mb-0 fw-bold text-success" if profit >= 0 else "mb-0 fw-bold text-danger"
        profit_sign = "+" if profit >= 0 else ""

        return (
            f"${balance:,.2f}",
            f"${equity:,.2f}",
            f"{profit_sign}${profit:,.2f}",
            profit_class,
            f"${free_margin:,.2f}"
        )

    # ==================== RISK METRICS ====================

    @app.callback(
        [Output('current-dd-value', 'children'),
         Output('current-dd-progress', 'value'),
         Output('current-dd-progress', 'color')],
        Input('status-store', 'data')
    )
    def update_current_dd(data):
        """Update current drawdown display"""
        if not data:
            return "0.00%", 0, "success"

        dd = data.get('account', {}).get('drawdown', 0)
        max_dd = app.config.trading.max_drawdown if app.config else 10

        progress = min(100, (dd / max_dd) * 100) if max_dd > 0 else 0

        if dd < max_dd * 0.5:
            color = "success"
        elif dd < max_dd * 0.8:
            color = "warning"
        else:
            color = "danger"

        return f"{dd:.2f}% / {max_dd}%", progress, color

    @app.callback(
        [Output('daily-dd-value', 'children'),
         Output('daily-dd-progress', 'value'),
         Output('daily-dd-progress', 'color')],
        Input('status-store', 'data')
    )
    def update_daily_dd(data):
        """Update daily drawdown display"""
        if not data:
            return "0.00%", 0, "success"

        dd = data.get('account', {}).get('daily_drawdown', 0)
        max_dd = app.config.trading.max_daily_drawdown if app.config else 5

        progress = min(100, (dd / max_dd) * 100) if max_dd > 0 else 0

        if dd < max_dd * 0.5:
            color = "success"
        elif dd < max_dd * 0.8:
            color = "warning"
        else:
            color = "danger"

        return f"{dd:.2f}% / {max_dd}%", progress, color

    @app.callback(
        [Output('daily-ops-value', 'children'),
         Output('daily-ops-progress', 'value'),
         Output('daily-ops-progress', 'color')],
        Input('status-store', 'data')
    )
    def update_daily_ops(data):
        """Update daily operations display"""
        if not data:
            return "0 / 10", 0, "success"

        stats = data.get('daily_stats', {})
        ops = stats.get('total_trades', 0)
        max_ops = app.config.trading.max_daily_operations if app.config else 10

        progress = min(100, (ops / max_ops) * 100) if max_ops > 0 else 0

        if ops < max_ops * 0.5:
            color = "success"
        elif ops < max_ops * 0.8:
            color = "warning"
        else:
            color = "danger"

        return f"{ops} / {max_ops}", progress, color

    # ==================== EQUITY CHART ====================

    @app.callback(
        [Output('equity-chart', 'figure'),
         Output('equity-history-store', 'data')],
        [Input('status-store', 'data'),
         Input('interval-slow', 'n_intervals')],
        State('equity-history-store', 'data')
    )
    def update_equity_chart(data, n, history):
        """Update equity curve chart"""
        if history is None:
            history = []

        # Add new data point
        if data:
            equity = data.get('account', {}).get('equity', 0)
            timestamp = datetime.now().isoformat()

            history.append({
                'time': timestamp,
                'equity': equity
            })

            # Keep last 500 points
            if len(history) > 500:
                history = history[-500:]

        # Create figure
        if history:
            times = [h['time'] for h in history]
            equities = [h['equity'] for h in history]

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=times,
                y=equities,
                mode='lines',
                name='Equity',
                line=dict(color='#00d4aa', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 212, 170, 0.1)'
            ))

            fig.update_layout(
                margin=dict(l=40, r=20, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    showticklabels=True
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    tickformat='$,.0f'
                ),
                showlegend=False,
                hovermode='x unified'
            )
        else:
            fig = go.Figure()
            fig.update_layout(
                annotations=[{
                    'text': 'Waiting for data...',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 14, 'color': 'gray'}
                }],
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

        return fig, history

    # ==================== TRADES TABLE ====================

    @app.callback(
        [Output('trades-table', 'children'),
         Output('open-positions-count', 'children')],
        Input('status-store', 'data')
    )
    def update_trades_table(data):
        """Update open positions table"""
        if not data:
            return html.P("No open positions", className="text-muted text-center"), "0"

        positions = data.get('account', {}).get('open_positions', 0)

        # For now, show placeholder - in production, would get from MT5
        if positions == 0:
            return html.P("No open positions", className="text-muted text-center"), "0"

        # Placeholder table
        table = dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Ticket"),
                    html.Th("Symbol"),
                    html.Th("Type"),
                    html.Th("Volume"),
                    html.Th("Open"),
                    html.Th("Current"),
                    html.Th("P/L"),
                ])
            ]),
            html.Tbody(id="trades-tbody")
        ], striped=True, bordered=True, hover=True, size="sm", className="mb-0")

        return table, str(positions)

    # ==================== STATISTICS ====================

    @app.callback(
        [Output('win-rate', 'children'),
         Output('profit-factor', 'children'),
         Output('gross-profit', 'children'),
         Output('gross-loss', 'children'),
         Output('net-profit', 'children'),
         Output('net-profit', 'className'),
         Output('winning-trades', 'children'),
         Output('losing-trades', 'children'),
         Output('expectancy', 'children')],
        Input('status-store', 'data')
    )
    def update_statistics(data):
        """Update trading statistics"""
        if not data:
            return "0", "0", "0", "0", "0", "fs-5 fw-bold text-primary", "0", "0", "0"

        stats = data.get('daily_stats', {})

        total = stats.get('total_trades', 0)
        winners = stats.get('winning_trades', 0)
        losers = stats.get('losing_trades', 0)
        gross_profit = stats.get('gross_profit', 0)
        gross_loss = stats.get('gross_loss', 0)
        net_profit = stats.get('net_profit', 0)

        # Calculate metrics
        win_rate = (winners / total * 100) if total > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        expectancy = (net_profit / total) if total > 0 else 0

        net_class = "fs-5 fw-bold text-success" if net_profit >= 0 else "fs-5 fw-bold text-danger"

        return (
            f"{win_rate:.1f}",
            f"{profit_factor:.2f}",
            f"{gross_profit:.2f}",
            f"{gross_loss:.2f}",
            f"{net_profit:.2f}",
            net_class,
            str(winners),
            str(losers),
            f"{expectancy:.2f}"
        )

    # ==================== NEWS FILTER ====================

    @app.callback(
        [Output('news-filter-status', 'children'),
         Output('next-news-event', 'children'),
         Output('time-to-news', 'children')],
        Input('interval-slow', 'n_intervals')
    )
    def update_news_info(n):
        """Update news filter information"""
        if not app.news_filter:
            return (
                dbc.Badge("Disabled", color="secondary"),
                "No data",
                "N/A"
            )

        try:
            status = app.news_filter.get_news_status()

            # News filter status
            if status.get('is_blocked'):
                filter_badge = dbc.Badge("BLOCKED", color="danger")
            else:
                filter_badge = dbc.Badge("Clear", color="success")

            # Next event
            next_event = status.get('next_event')
            if next_event and next_event.get('name'):
                event_text = f"{next_event['currency']} - {next_event['name']}"
            else:
                event_text = "No upcoming events"

            # Time to news
            minutes = status.get('minutes_to_news')
            if minutes is not None:
                if minutes < 60:
                    time_text = f"{minutes} minutes"
                else:
                    hours = minutes // 60
                    mins = minutes % 60
                    time_text = f"{hours}h {mins}m"
            else:
                time_text = "N/A"

            return filter_badge, event_text, time_text

        except Exception as e:
            return (
                dbc.Badge("Error", color="warning"),
                "Error loading news",
                "N/A"
            )

    # ==================== CONTROL PANEL ====================

    @app.callback(
        Output('control-feedback', 'children'),
        [Input('btn-pause', 'n_clicks'),
         Input('btn-resume', 'n_clicks'),
         Input('btn-close-all', 'n_clicks'),
         Input('btn-refresh', 'n_clicks')]
    )
    def handle_control_buttons(pause, resume, close_all, refresh):
        """Handle control panel button clicks"""
        ctx = callback_context

        if not ctx.triggered:
            return ""

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if not app.socket_server:
            return dbc.Alert("Server not connected", color="warning", className="mb-0 py-1")

        try:
            if button_id == 'btn-pause':
                app.socket_server.pause_bot()
                return dbc.Alert("Pause command sent", color="warning", className="mb-0 py-1")

            elif button_id == 'btn-resume':
                app.socket_server.resume_bot()
                return dbc.Alert("Resume command sent", color="success", className="mb-0 py-1")

            elif button_id == 'btn-close-all':
                app.socket_server.close_all_positions()
                return dbc.Alert("Close all command sent", color="danger", className="mb-0 py-1")

            elif button_id == 'btn-refresh':
                app.socket_server.request_status()
                return dbc.Alert("Refresh requested", color="info", className="mb-0 py-1")

        except Exception as e:
            return dbc.Alert(f"Error: {str(e)}", color="danger", className="mb-0 py-1")

        return ""

    # ==================== FOOTER ====================

    @app.callback(
        [Output('footer-status', 'children'),
         Output('last-update-time', 'children')],
        Input('status-store', 'data')
    )
    def update_footer(data):
        """Update footer information"""
        if data:
            status = data.get('account', {}).get('bot_status', 'Unknown')
            timestamp = data.get('timestamp', 0)
            if timestamp:
                last_update = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            else:
                last_update = "Never"
        else:
            status = "Disconnected"
            last_update = "Never"

        return status, last_update
