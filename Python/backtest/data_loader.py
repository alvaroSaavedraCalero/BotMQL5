"""
Descarga y Gestión de Datos Históricos
=======================================

Proporciona funciones para descargar datos OHLCV de múltiples fuentes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import json


class DataLoader:
    """
    Carga datos históricos de múltiples fuentes
    """

    def __init__(self, cache_dir: str = "./data/cache"):
        """
        Inicializa el data loader

        Args:
            cache_dir: Directorio para cachear datos
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def load_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1min",
        source: str = "yfinance"
    ) -> pd.DataFrame:
        """
        Carga datos históricos

        Args:
            symbol: Símbolo (ej: EURUSD=X para Yahoo Finance)
            start_date: Fecha inicial
            end_date: Fecha final
            timeframe: Timeframe (1min, 5min, 15min, 1h, 1d)
            source: Fuente de datos (yfinance, csv, mt5)

        Returns:
            DataFrame con columnas: time, open, high, low, close, volume
        """
        # Verificar cache
        cache_file = self._get_cache_filename(symbol, start_date, end_date, timeframe)
        if os.path.exists(cache_file):
            print(f"Cargando datos desde cache: {cache_file}")
            return pd.read_csv(cache_file, parse_dates=["time"])

        # Cargar según fuente
        if source == "yfinance":
            df = self._load_from_yfinance(symbol, start_date, end_date, timeframe)
        elif source == "csv":
            df = self._load_from_csv(symbol, timeframe)
        elif source == "mt5":
            df = self._load_from_mt5(symbol, start_date, end_date, timeframe)
        else:
            raise ValueError(f"Fuente no soportada: {source}")

        # Guardar en cache
        df.to_csv(cache_file, index=False)
        print(f"Datos guardados en cache: {cache_file}")

        return df

    def load_multiple_timeframes(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframes: List[str] = ["1min", "5min", "15min"],
        source: str = "yfinance"
    ) -> Dict[str, pd.DataFrame]:
        """
        Carga datos de múltiples timeframes

        Args:
            symbol: Símbolo
            start_date: Fecha inicial
            end_date: Fecha final
            timeframes: Lista de timeframes
            source: Fuente de datos

        Returns:
            Dict con {timeframe: DataFrame}
        """
        data = {}
        for tf in timeframes:
            print(f"Cargando {symbol} {tf}...")
            data[tf] = self.load_data(symbol, start_date, end_date, tf, source)

        return data

    def _load_from_yfinance(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Carga datos de Yahoo Finance

        Args:
            symbol: Símbolo (formato Yahoo: EURUSD=X)
            start_date: Fecha inicial
            end_date: Fecha final
            timeframe: Timeframe

        Returns:
            DataFrame normalizado
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance no está instalado. Instálalo con: pip install yfinance"
            )

        # Mapear timeframe a formato yfinance
        interval_map = {
            "1min": "1m",
            "5min": "5m",
            "15min": "15m",
            "30min": "30m",
            "1h": "1h",
            "1d": "1d",
        }

        interval = interval_map.get(timeframe, "1m")

        # Descargar datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=True
        )

        if df.empty:
            raise ValueError(f"No se encontraron datos para {symbol}")

        # Normalizar columnas
        df = df.reset_index()
        df = df.rename(columns={
            "Datetime": "time",
            "Date": "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })

        df = df[["time", "open", "high", "low", "close", "volume"]]

        return df

    def _load_from_csv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Carga datos desde archivo CSV

        Args:
            symbol: Símbolo
            timeframe: Timeframe

        Returns:
            DataFrame normalizado
        """
        csv_file = os.path.join(self.cache_dir, f"{symbol}_{timeframe}.csv")

        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Archivo no encontrado: {csv_file}")

        df = pd.read_csv(csv_file, parse_dates=["time"])

        # Verificar columnas requeridas
        required = ["time", "open", "high", "low", "close"]
        if not all(col in df.columns for col in required):
            raise ValueError(f"CSV debe contener columnas: {required}")

        if "volume" not in df.columns:
            df["volume"] = 0

        return df[["time", "open", "high", "low", "close", "volume"]]

    def _load_from_mt5(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Carga datos desde MetaTrader 5

        Args:
            symbol: Símbolo
            start_date: Fecha inicial
            end_date: Fecha final
            timeframe: Timeframe

        Returns:
            DataFrame normalizado
        """
        try:
            import MetaTrader5 as mt5
        except ImportError:
            raise ImportError(
                "MetaTrader5 no está instalado. Instálalo con: pip install MetaTrader5"
            )

        # Mapear timeframe
        timeframe_map = {
            "1min": mt5.TIMEFRAME_M1,
            "5min": mt5.TIMEFRAME_M5,
            "15min": mt5.TIMEFRAME_M15,
            "30min": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "1d": mt5.TIMEFRAME_D1,
        }

        tf = timeframe_map.get(timeframe)
        if tf is None:
            raise ValueError(f"Timeframe no soportado: {timeframe}")

        # Inicializar MT5
        if not mt5.initialize():
            raise ConnectionError("No se pudo conectar a MT5")

        # Obtener datos
        rates = mt5.copy_rates_range(symbol, tf, start_date, end_date)

        mt5.shutdown()

        if rates is None or len(rates) == 0:
            raise ValueError(f"No se encontraron datos para {symbol}")

        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        # Renombrar columnas
        df = df.rename(columns={
            "tick_volume": "volume"
        })

        return df[["time", "open", "high", "low", "close", "volume"]]

    def _get_cache_filename(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> str:
        """
        Genera nombre de archivo de cache

        Args:
            symbol: Símbolo
            start_date: Fecha inicial
            end_date: Fecha final
            timeframe: Timeframe

        Returns:
            Path del archivo de cache
        """
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        filename = f"{symbol}_{timeframe}_{start_str}_{end_str}.csv"

        return os.path.join(self.cache_dir, filename)

    def resample_timeframe(
        self,
        df: pd.DataFrame,
        target_timeframe: str
    ) -> pd.DataFrame:
        """
        Resamplea datos a un timeframe superior

        Args:
            df: DataFrame con datos de timeframe menor
            target_timeframe: Timeframe objetivo (5min, 15min, etc.)

        Returns:
            DataFrame resampleado
        """
        # Mapear a formato pandas
        resample_map = {
            "1min": "1T",
            "5min": "5T",
            "15min": "15T",
            "30min": "30T",
            "1h": "1H",
            "1d": "1D",
        }

        freq = resample_map.get(target_timeframe)
        if freq is None:
            raise ValueError(f"Timeframe no soportado: {target_timeframe}")

        df = df.set_index("time")

        # Resamplear
        resampled = df.resample(freq).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        })

        # Eliminar NaN
        resampled = resampled.dropna()

        return resampled.reset_index()

    def add_spread(
        self,
        df: pd.DataFrame,
        spread_pips: float = 1.0
    ) -> pd.DataFrame:
        """
        Añade spread a los datos (simula bid/ask)

        Args:
            df: DataFrame con datos
            spread_pips: Spread en pips

        Returns:
            DataFrame con columnas bid y ask
        """
        df = df.copy()

        # Convertir pips a precio
        spread = spread_pips * 0.0001

        df["bid"] = df["close"]
        df["ask"] = df["close"] + spread

        return df

    def get_forex_symbols(self) -> List[Dict[str, str]]:
        """
        Retorna lista de símbolos forex populares

        Returns:
            Lista de dicts con symbol y yfinance_symbol
        """
        return [
            {"symbol": "EURUSD", "yfinance": "EURUSD=X"},
            {"symbol": "GBPUSD", "yfinance": "GBPUSD=X"},
            {"symbol": "USDJPY", "yfinance": "USDJPY=X"},
            {"symbol": "USDCHF", "yfinance": "USDCHF=X"},
            {"symbol": "AUDUSD", "yfinance": "AUDUSD=X"},
            {"symbol": "USDCAD", "yfinance": "USDCAD=X"},
            {"symbol": "NZDUSD", "yfinance": "NZDUSD=X"},
            {"symbol": "EURGBP", "yfinance": "EURGBP=X"},
        ]
