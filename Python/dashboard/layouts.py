"""
Dashboard Layouts Module
Defines the visual structure of the dashboard
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_layout(config):
    """
    Create the main dashboard layout

    Args:
        config: Configuration object

    Returns:
        Dash layout component
    """
    return dbc.Container([
        # Header
        create_header(),

        # Interval for real-time updates (1 second)
        dcc.Interval(
            id='interval-fast',
            interval=1000,  # 1 second
            n_intervals=0
        ),

        # Interval for slower updates (5 seconds)
        dcc.Interval(
            id='interval-slow',
            interval=5000,  # 5 seconds
            n_intervals=0
        ),

        # Store for data
        dcc.Store(id='status-store'),
        dcc.Store(id='trades-store'),
        dcc.Store(id='equity-history-store', data=[]),

        # Main content
        dbc.Row([
            # Left column - Status and Stats
            dbc.Col([
                create_status_card(),
                html.Br(),
                create_account_card(),
                html.Br(),
                create_risk_card(),
            ], width=4),

            # Right column - Charts and Tables
            dbc.Col([
                create_equity_chart_card(),
                html.Br(),
                create_trades_card(),
            ], width=8),
        ]),

        html.Br(),

        # Bottom row - Statistics and News
        dbc.Row([
            dbc.Col([
                create_stats_card(),
            ], width=6),
            dbc.Col([
                create_news_card(),
            ], width=6),
        ]),

        html.Br(),

        # Control panel
        create_control_panel(),

        # Footer
        create_footer(),

    ], fluid=True, className="p-4")


def create_header():
    """Create dashboard header"""
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="fas fa-robot me-2"),
                "Multi-TF Scalping Bot"
            ], className="text-primary mb-0"),
            html.Small("Real-time Trading Dashboard", className="text-muted"),
        ], width=6),
        dbc.Col([
            html.Div([
                html.Span(id="connection-status", className="me-3"),
                html.Span(id="current-time", className="text-muted"),
            ], className="text-end")
        ], width=6),
    ], className="mb-4 border-bottom pb-3")


def create_status_card():
    """Create bot status card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-heartbeat me-2"),
            "Bot Status"
        ]),
        dbc.CardBody([
            html.Div([
                html.Div(id="bot-status-indicator", className="status-indicator"),
                html.H3(id="bot-status-text", className="mb-0 ms-3"),
            ], className="d-flex align-items-center mb-3"),

            dbc.Row([
                dbc.Col([
                    html.Small("Session", className="text-muted"),
                    html.P(id="current-session", className="mb-0 fw-bold"),
                ], width=6),
                dbc.Col([
                    html.Small("Daily Trades", className="text-muted"),
                    html.P(id="daily-trades-count", className="mb-0 fw-bold"),
                ], width=6),
            ]),
        ])
    ], className="shadow-sm")


def create_account_card():
    """Create account info card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-wallet me-2"),
            "Account"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Small("Balance", className="text-muted"),
                    html.H4(id="account-balance", className="mb-0 text-success"),
                ], width=6),
                dbc.Col([
                    html.Small("Equity", className="text-muted"),
                    html.H4(id="account-equity", className="mb-0"),
                ], width=6),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    html.Small("Floating P/L", className="text-muted"),
                    html.P(id="floating-pl", className="mb-0 fw-bold"),
                ], width=6),
                dbc.Col([
                    html.Small("Free Margin", className="text-muted"),
                    html.P(id="free-margin", className="mb-0"),
                ], width=6),
            ]),
        ])
    ], className="shadow-sm")


def create_risk_card():
    """Create risk metrics card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-shield-alt me-2"),
            "Risk Metrics"
        ]),
        dbc.CardBody([
            # Current Drawdown
            html.Div([
                html.Div([
                    html.Small("Current Drawdown", className="text-muted"),
                    html.Span(id="current-dd-value", className="float-end"),
                ], className="d-flex justify-content-between"),
                dbc.Progress(
                    id="current-dd-progress",
                    value=0,
                    max=100,
                    className="mb-3",
                    style={"height": "8px"}
                ),
            ]),

            # Daily Drawdown
            html.Div([
                html.Div([
                    html.Small("Daily Drawdown", className="text-muted"),
                    html.Span(id="daily-dd-value", className="float-end"),
                ], className="d-flex justify-content-between"),
                dbc.Progress(
                    id="daily-dd-progress",
                    value=0,
                    max=100,
                    className="mb-3",
                    style={"height": "8px"}
                ),
            ]),

            # Daily Operations
            html.Div([
                html.Div([
                    html.Small("Daily Operations", className="text-muted"),
                    html.Span(id="daily-ops-value", className="float-end"),
                ], className="d-flex justify-content-between"),
                dbc.Progress(
                    id="daily-ops-progress",
                    value=0,
                    max=100,
                    className="mb-0",
                    style={"height": "8px"}
                ),
            ]),
        ])
    ], className="shadow-sm")


def create_equity_chart_card():
    """Create equity chart card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-line me-2"),
            "Equity Curve"
        ]),
        dbc.CardBody([
            dcc.Graph(
                id='equity-chart',
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ], className="shadow-sm")


def create_trades_card():
    """Create trades table card"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Span([
                    html.I(className="fas fa-exchange-alt me-2"),
                    "Open Positions"
                ]),
                dbc.Badge(id="open-positions-count", color="primary", className="ms-2"),
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            html.Div(id="trades-table", className="table-responsive")
        ])
    ], className="shadow-sm")


def create_stats_card():
    """Create statistics card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-bar me-2"),
            "Daily Statistics"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    create_stat_item("Win Rate", "win-rate", "%", "success"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Profit Factor", "profit-factor", "", "info"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Gross Profit", "gross-profit", "$", "success"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Gross Loss", "gross-loss", "$", "danger"),
                ], width=3),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    create_stat_item("Net Profit", "net-profit", "$", "primary"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Winners", "winning-trades", "", "success"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Losers", "losing-trades", "", "danger"),
                ], width=3),
                dbc.Col([
                    create_stat_item("Expectancy", "expectancy", "$", "info"),
                ], width=3),
            ]),
        ])
    ], className="shadow-sm")


def create_stat_item(label, stat_id, suffix, color):
    """Create a statistics item"""
    return html.Div([
        html.Small(label, className="text-muted d-block"),
        html.Span([
            html.Span(id=stat_id, className=f"fs-5 fw-bold text-{color}"),
            html.Span(suffix, className="text-muted ms-1") if suffix else None
        ])
    ], className="text-center")


def create_news_card():
    """Create news filter card"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-newspaper me-2"),
            "Economic Calendar"
        ]),
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span("News Filter:", className="text-muted me-2"),
                    html.Span(id="news-filter-status"),
                ], className="mb-3"),

                html.Div([
                    html.Small("Next High-Impact Event:", className="text-muted d-block"),
                    html.P(id="next-news-event", className="mb-0"),
                ], className="mb-3"),

                html.Div([
                    html.Small("Time to Event:", className="text-muted d-block"),
                    html.Span(id="time-to-news", className="fw-bold"),
                ]),
            ])
        ])
    ], className="shadow-sm")


def create_control_panel():
    """Create control panel"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-sliders-h me-2"),
            "Control Panel"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-pause me-2"),
                        "Pause Bot"
                    ], id="btn-pause", color="warning", className="w-100"),
                ], width=2),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-play me-2"),
                        "Resume Bot"
                    ], id="btn-resume", color="success", className="w-100"),
                ], width=2),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-times-circle me-2"),
                        "Close All"
                    ], id="btn-close-all", color="danger", className="w-100"),
                ], width=2),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-sync me-2"),
                        "Refresh"
                    ], id="btn-refresh", color="info", className="w-100"),
                ], width=2),
                dbc.Col([
                    html.Div(id="control-feedback", className="text-center pt-2")
                ], width=4),
            ])
        ])
    ], className="shadow-sm")


def create_footer():
    """Create dashboard footer"""
    return html.Footer([
        html.Hr(),
        html.Div([
            html.Small([
                "Multi-TF Scalping Bot v1.0.0 | ",
                html.Span(id="footer-status"),
                " | Last Update: ",
                html.Span(id="last-update-time")
            ], className="text-muted")
        ], className="text-center pb-3")
    ])
