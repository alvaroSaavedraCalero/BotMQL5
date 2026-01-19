"""
Configuración global del sistema de trading
Multi-TF Scalping Bot for MT5
"""

import os
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class TradingConfig:
    """Configuración de parámetros de trading"""
    # Gestión de riesgo
    max_drawdown: float = 10.0  # Drawdown máximo cuenta (%)
    max_daily_drawdown: float = 5.0  # Drawdown máximo diario (%)
    max_daily_operations: int = 10  # Operaciones máximas por día
    risk_per_trade: float = 1.0  # Riesgo por operación (%)

    # Configuración de trading
    stop_loss_pips: int = 12  # Stop Loss (pips) [10-15]
    rr_partial: float = 2.0  # R:R para cierre parcial
    rr_final: float = 3.0  # R:R para cierre total
    partial_close_percent: float = 50.0  # % de cierre parcial
    slippage: int = 3  # Slippage máximo (puntos)
    spread_maximo: float = 2.0  # Spread máximo (pips)


@dataclass
class SessionConfig:
    """Configuración de sesiones de trading"""
    london_start_hour: int = 8  # Hora UTC
    london_end_hour: int = 12
    ny_start_hour: int = 13  # Hora UTC
    ny_end_hour: int = 17
    news_buffer_minutes: int = 45  # Minutos antes/después de noticias


@dataclass
class IndicatorConfig:
    """Configuración de indicadores técnicos"""
    ema_fast: int = 9
    ema_slow: int = 21
    rsi_period: int = 14
    stoch_k: int = 5
    stoch_d: int = 3
    stoch_slowing: int = 3
    atr_period: int = 14


@dataclass
class SystemConfig:
    """Configuración del sistema"""
    magic_number: int = 123456
    symbols: List[str] = None  # None = todos los disponibles
    dashboard_port: int = 8050
    socket_port: int = 5555
    update_interval_ms: int = 1000
    log_level: str = "INFO"

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [
                "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
                "AUDUSD", "NZDUSD", "USDCAD", "EURGBP"
            ]


@dataclass
class PathConfig:
    """Configuración de rutas"""
    # Rutas base
    base_dir: Path = None
    data_dir: Path = None
    logs_dir: Path = None

    # Archivos de comunicación MT5
    mt5_common_path: Path = None

    def __post_init__(self):
        if self.base_dir is None:
            self.base_dir = Path(__file__).parent

        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"

        if self.logs_dir is None:
            self.logs_dir = self.base_dir / "logs"

        # Crear directorios si no existen
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Ruta común de MT5 (Windows)
        if self.mt5_common_path is None:
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                self.mt5_common_path = Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / "ScalpingBot"
            else:
                # Fallback para desarrollo
                self.mt5_common_path = self.data_dir / "mt5_files"

        self.mt5_common_path.mkdir(parents=True, exist_ok=True)


class Config:
    """Clase principal de configuración"""

    def __init__(self):
        self.trading = TradingConfig()
        self.session = SessionConfig()
        self.indicators = IndicatorConfig()
        self.system = SystemConfig()
        self.paths = PathConfig()

        # Database
        self.database_url = f"sqlite:///{self.paths.data_dir}/trading_bot.db"

        # Archivos de comunicación
        self.status_file = self.paths.mt5_common_path / "mt5_status.json"
        self.signal_file = self.paths.mt5_common_path / "python_signals.json"
        self.command_file = self.paths.mt5_common_path / "python_to_mt5.json"
        self.heartbeat_file = self.paths.mt5_common_path / "heartbeat.json"
        self.trades_file = self.paths.mt5_common_path / "mt5_to_python.json"

    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario"""
        return {
            "trading": {
                "max_drawdown": self.trading.max_drawdown,
                "max_daily_drawdown": self.trading.max_daily_drawdown,
                "max_daily_operations": self.trading.max_daily_operations,
                "risk_per_trade": self.trading.risk_per_trade,
                "stop_loss_pips": self.trading.stop_loss_pips,
                "rr_partial": self.trading.rr_partial,
                "rr_final": self.trading.rr_final,
                "partial_close_percent": self.trading.partial_close_percent,
            },
            "session": {
                "london_start": self.session.london_start_hour,
                "london_end": self.session.london_end_hour,
                "ny_start": self.session.ny_start_hour,
                "ny_end": self.session.ny_end_hour,
                "news_buffer": self.session.news_buffer_minutes,
            },
            "indicators": {
                "ema_fast": self.indicators.ema_fast,
                "ema_slow": self.indicators.ema_slow,
                "rsi_period": self.indicators.rsi_period,
                "stoch_k": self.indicators.stoch_k,
                "stoch_d": self.indicators.stoch_d,
                "stoch_slowing": self.indicators.stoch_slowing,
                "atr_period": self.indicators.atr_period,
            },
            "system": {
                "magic_number": self.system.magic_number,
                "symbols": self.system.symbols,
                "dashboard_port": self.system.dashboard_port,
            }
        }


# Instancia global de configuración
config = Config()
