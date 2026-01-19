"""
Módulo de Backtesting para Multi-TF Scalping Strategy
=====================================================

Este módulo proporciona un sistema completo de backtesting que replica
la estrategia implementada en MetaTrader 5.

Componentes:
- data_loader: Descarga y gestión de datos históricos
- backtester: Motor principal de simulación
- trade: Gestión de operaciones individuales
- portfolio: Gestión de cuenta y posiciones
- signal_engine_bt: Motor de señales adaptado
- statistics: Cálculo de métricas de rendimiento
- visualizer: Generación de gráficos
- report: Generación de reportes detallados
"""

from .backtester import Backtester
from .trade import Trade, TradeType, TradeStatus
from .portfolio import Portfolio
from .statistics import Statistics
from .visualizer import Visualizer
from .report import ReportGenerator

__version__ = "1.0.0"
__all__ = [
    "Backtester",
    "Trade",
    "TradeType",
    "TradeStatus",
    "Portfolio",
    "Statistics",
    "Visualizer",
    "ReportGenerator",
]
