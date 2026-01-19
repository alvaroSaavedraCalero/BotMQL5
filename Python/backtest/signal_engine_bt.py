"""
Motor de Señales para Backtesting
==================================

Adaptación del signal engine para trabajar con datos históricos.
Replica la lógica de la estrategia Multi-TF implementada en MT5.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from enum import Enum


class SignalType(Enum):
    """Tipos de señal"""
    NONE = "NONE"
    BUY = "BUY"
    SELL = "SELL"


class SignalEngineBT:
    """
    Motor de señales para backtesting que replica la estrategia MT5
    """

    def __init__(
        self,
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_period: int = 14,
        stoch_k: int = 5,
        stoch_d: int = 3,
        stoch_slowing: int = 3,
        atr_period: int = 14,
        min_atr: float = 0.0003,
        rsi_buy_min: float = 40.0,
        rsi_buy_max: float = 70.0,
        rsi_sell_min: float = 30.0,
        rsi_sell_max: float = 60.0,
        stoch_oversold: float = 20.0,
        stoch_overbought: float = 80.0
    ):
        """
        Inicializa el motor de señales

        Args:
            ema_fast: Periodo EMA rápida
            ema_slow: Periodo EMA lenta
            rsi_period: Periodo RSI
            stoch_k: Periodo K del Stochastic
            stoch_d: Periodo D del Stochastic
            stoch_slowing: Slowing del Stochastic
            atr_period: Periodo ATR
            min_atr: ATR mínimo para operar
            rsi_buy_min: RSI mínimo para compra
            rsi_buy_max: RSI máximo para compra
            rsi_sell_min: RSI mínimo para venta
            rsi_sell_max: RSI máximo para venta
            stoch_oversold: Nivel de sobreventa
            stoch_overbought: Nivel de sobrecompra
        """
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.stoch_slowing = stoch_slowing
        self.atr_period = atr_period
        self.min_atr = min_atr
        self.rsi_buy_min = rsi_buy_min
        self.rsi_buy_max = rsi_buy_max
        self.rsi_sell_min = rsi_sell_min
        self.rsi_sell_max = rsi_sell_max
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought

    def calculate_indicators(
        self,
        data_m1: pd.DataFrame,
        data_m5: pd.DataFrame,
        data_m15: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Calcula todos los indicadores para los 3 timeframes

        Args:
            data_m1: Datos M1
            data_m5: Datos M5
            data_m15: Datos M15

        Returns:
            Tuple con (data_m1, data_m5, data_m15) con indicadores
        """
        # M15: Tendencia
        data_m15 = self._add_ema(data_m15, self.ema_fast, "ema_fast")
        data_m15 = self._add_ema(data_m15, self.ema_slow, "ema_slow")

        # M5: Confirmación
        data_m5 = self._add_ema(data_m5, self.ema_fast, "ema_fast")
        data_m5 = self._add_ema(data_m5, self.ema_slow, "ema_slow")
        data_m5 = self._add_rsi(data_m5, self.rsi_period)
        data_m5 = self._add_vwap(data_m5)

        # M1: Entry timing
        data_m1 = self._add_stochastic(
            data_m1,
            self.stoch_k,
            self.stoch_d,
            self.stoch_slowing
        )
        data_m1 = self._add_atr(data_m1, self.atr_period)

        return data_m1, data_m5, data_m15

    def get_signal(
        self,
        current_time: pd.Timestamp,
        data_m1: pd.DataFrame,
        data_m5: pd.DataFrame,
        data_m15: pd.DataFrame
    ) -> Tuple[SignalType, Dict]:
        """
        Obtiene señal de trading para un momento específico

        Args:
            current_time: Tiempo actual
            data_m1: Datos M1 con indicadores
            data_m5: Datos M5 con indicadores
            data_m15: Datos M15 con indicadores

        Returns:
            Tuple (SignalType, details_dict)
        """
        # Obtener valores actuales
        try:
            m1_current = data_m1[data_m1["time"] <= current_time].iloc[-1]
            m5_current = data_m5[data_m5["time"] <= current_time].iloc[-1]
            m15_current = data_m15[data_m15["time"] <= current_time].iloc[-1]

            # Obtener barra anterior M1 para detectar cruces
            m1_previous = data_m1[data_m1["time"] <= current_time].iloc[-2]

        except (IndexError, KeyError):
            return SignalType.NONE, {}

        # Verificar validez de indicadores
        if not self._indicators_valid(m1_current, m5_current, m15_current):
            return SignalType.NONE, {}

        # Analizar cada timeframe
        m15_trend = self._analyze_m15_trend(m15_current)
        m5_confirmation = self._analyze_m5_confirmation(m5_current, m15_trend)
        m1_entry = self._analyze_m1_entry(m1_current, m1_previous)

        # Detalles
        details = {
            "m15_trend": m15_trend,
            "m5_confirmation": m5_confirmation,
            "m1_entry": m1_entry,
            "atr": m1_current.get("atr", 0.0),
            "price": m1_current["close"],
            "m15_ema_fast": m15_current.get("ema_fast", 0.0),
            "m15_ema_slow": m15_current.get("ema_slow", 0.0),
            "m5_rsi": m5_current.get("rsi", 0.0),
            "m5_vwap": m5_current.get("vwap", 0.0),
            "m1_stoch_k": m1_current.get("stoch_k", 0.0),
            "m1_stoch_d": m1_current.get("stoch_d", 0.0),
        }

        # Señal BUY
        if (
            m15_trend == "BULLISH"
            and m5_confirmation == "BUY"
            and m1_entry == "BUY"
            and m1_current["atr"] >= self.min_atr
        ):
            return SignalType.BUY, details

        # Señal SELL
        if (
            m15_trend == "BEARISH"
            and m5_confirmation == "SELL"
            and m1_entry == "SELL"
            and m1_current["atr"] >= self.min_atr
        ):
            return SignalType.SELL, details

        return SignalType.NONE, details

    def _analyze_m15_trend(self, m15: pd.Series) -> str:
        """
        Analiza tendencia en M15

        Args:
            m15: Serie con datos M15

        Returns:
            "BULLISH", "BEARISH" o "NEUTRAL"
        """
        ema_fast = m15.get("ema_fast", 0.0)
        ema_slow = m15.get("ema_slow", 0.0)

        if ema_fast > ema_slow:
            return "BULLISH"
        elif ema_fast < ema_slow:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _analyze_m5_confirmation(self, m5: pd.Series, trend: str) -> str:
        """
        Analiza confirmación en M5

        Args:
            m5: Serie con datos M5
            trend: Tendencia de M15

        Returns:
            "BUY", "SELL" o "NONE"
        """
        ema_fast = m5.get("ema_fast", 0.0)
        ema_slow = m5.get("ema_slow", 0.0)
        rsi = m5.get("rsi", 50.0)
        vwap = m5.get("vwap", 0.0)
        price = m5["close"]

        # Confirmación BUY
        if trend == "BULLISH":
            if (
                ema_fast > ema_slow
                and price > vwap
                and self.rsi_buy_min <= rsi <= self.rsi_buy_max
            ):
                return "BUY"

        # Confirmación SELL
        if trend == "BEARISH":
            if (
                ema_fast < ema_slow
                and price < vwap
                and self.rsi_sell_min <= rsi <= self.rsi_sell_max
            ):
                return "SELL"

        return "NONE"

    def _analyze_m1_entry(
        self,
        m1_current: pd.Series,
        m1_previous: pd.Series
    ) -> str:
        """
        Analiza señal de entrada en M1

        Args:
            m1_current: Serie con datos M1 actuales
            m1_previous: Serie con datos M1 anteriores

        Returns:
            "BUY", "SELL" o "NONE"
        """
        stoch_k_current = m1_current.get("stoch_k", 50.0)
        stoch_d_current = m1_current.get("stoch_d", 50.0)
        stoch_k_previous = m1_previous.get("stoch_k", 50.0)
        stoch_d_previous = m1_previous.get("stoch_d", 50.0)

        # BUY: Cruce hacia arriba desde sobreventa
        if (
            stoch_k_previous <= self.stoch_oversold
            and stoch_k_current > stoch_d_current
            and stoch_k_previous <= stoch_d_previous
        ):
            return "BUY"

        # SELL: Cruce hacia abajo desde sobrecompra
        if (
            stoch_k_previous >= self.stoch_overbought
            and stoch_k_current < stoch_d_current
            and stoch_k_previous >= stoch_d_previous
        ):
            return "SELL"

        return "NONE"

    def _indicators_valid(
        self,
        m1: pd.Series,
        m5: pd.Series,
        m15: pd.Series
    ) -> bool:
        """
        Verifica que todos los indicadores estén calculados

        Args:
            m1: Serie M1
            m5: Serie M5
            m15: Serie M15

        Returns:
            True si todos los indicadores son válidos
        """
        # Verificar M15
        if pd.isna(m15.get("ema_fast")) or pd.isna(m15.get("ema_slow")):
            return False

        # Verificar M5
        if (
            pd.isna(m5.get("ema_fast"))
            or pd.isna(m5.get("ema_slow"))
            or pd.isna(m5.get("rsi"))
            or pd.isna(m5.get("vwap"))
        ):
            return False

        # Verificar M1
        if (
            pd.isna(m1.get("stoch_k"))
            or pd.isna(m1.get("stoch_d"))
            or pd.isna(m1.get("atr"))
        ):
            return False

        return True

    # ============ Cálculo de Indicadores ============

    def _add_ema(
        self,
        df: pd.DataFrame,
        period: int,
        column_name: str = "ema"
    ) -> pd.DataFrame:
        """Calcula EMA"""
        df = df.copy()
        df[column_name] = df["close"].ewm(span=period, adjust=False).mean()
        return df

    def _add_rsi(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        """Calcula RSI"""
        df = df.copy()

        # Calcular cambios
        delta = df["close"].diff()

        # Ganancias y pérdidas
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # Promedios
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # RSI
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        return df

    def _add_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int,
        d_period: int,
        slowing: int
    ) -> pd.DataFrame:
        """Calcula Stochastic"""
        df = df.copy()

        # %K
        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()

        df["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min)

        # Slowing
        df["stoch_k"] = df["stoch_k"].rolling(window=slowing).mean()

        # %D
        df["stoch_d"] = df["stoch_k"].rolling(window=d_period).mean()

        return df

    def _add_atr(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        """Calcula ATR"""
        df = df.copy()

        # True Range
        df["h-l"] = df["high"] - df["low"]
        df["h-pc"] = abs(df["high"] - df["close"].shift(1))
        df["l-pc"] = abs(df["low"] - df["close"].shift(1))

        df["tr"] = df[["h-l", "h-pc", "l-pc"]].max(axis=1)

        # ATR
        df["atr"] = df["tr"].ewm(span=period, adjust=False).mean()

        # Limpiar columnas temporales
        df = df.drop(columns=["h-l", "h-pc", "l-pc", "tr"])

        return df

    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula VWAP"""
        df = df.copy()

        # VWAP típico
        df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
        df["vwap"] = (df["typical_price"] * df["volume"]).cumsum() / df["volume"].cumsum()

        # Resetear VWAP diariamente
        if "time" in df.columns:
            df["date"] = pd.to_datetime(df["time"]).dt.date
            df["vwap"] = df.groupby("date").apply(
                lambda x: (x["typical_price"] * x["volume"]).cumsum() / x["volume"].cumsum()
            ).reset_index(level=0, drop=True)
            df = df.drop(columns=["date"])

        df = df.drop(columns=["typical_price"])

        return df
