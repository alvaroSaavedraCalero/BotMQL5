"""
Signal Engine Module
Generates trading signals based on multi-timeframe analysis
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Tuple
from enum import Enum
from dataclasses import dataclass

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Signal types"""
    NONE = "NONE"
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class IndicatorValues:
    """Container for indicator values"""
    ema_fast_m15: float = 0.0
    ema_slow_m15: float = 0.0
    ema_fast_m5: float = 0.0
    ema_slow_m5: float = 0.0
    rsi_m5: float = 50.0
    vwap_m5: float = 0.0
    stoch_k_m1: float = 50.0
    stoch_d_m1: float = 50.0
    stoch_k_prev_m1: float = 50.0
    atr_m1: float = 0.0
    close_m5: float = 0.0


@dataclass
class SignalResult:
    """Signal analysis result"""
    signal_type: SignalType
    confidence: float
    m15_trend: str
    m5_confirmed: bool
    m1_entry: bool
    indicators: IndicatorValues
    reason: str


class SignalEngine:
    """
    Multi-Timeframe Signal Engine

    Strategy:
    - M15: Trend direction (EMA 9 vs EMA 21)
    - M5: Confirmation (EMA crossover, RSI filter, price vs VWAP)
    - M1: Entry timing (Stochastic crossover from oversold/overbought)
    """

    # Indicator parameters
    EMA_FAST = 9
    EMA_SLOW = 21
    RSI_PERIOD = 14
    STOCH_K = 5
    STOCH_D = 3
    STOCH_SLOWING = 3
    ATR_PERIOD = 14

    # Signal thresholds
    STOCH_OVERSOLD = 20
    STOCH_OVERBOUGHT = 80
    RSI_BUY_MIN = 40
    RSI_BUY_MAX = 70
    RSI_SELL_MIN = 30
    RSI_SELL_MAX = 60

    def __init__(self, config, mt5_connector=None):
        """
        Initialize Signal Engine

        Args:
            config: Configuration object
            mt5_connector: MT5Connector instance (optional)
        """
        self.config = config
        self.mt5 = mt5_connector
        self.last_signal_time = {}  # Per-symbol signal cooldown

        # Load parameters from config
        self.EMA_FAST = config.indicators.ema_fast
        self.EMA_SLOW = config.indicators.ema_slow
        self.RSI_PERIOD = config.indicators.rsi_period
        self.STOCH_K = config.indicators.stoch_k
        self.STOCH_D = config.indicators.stoch_d
        self.STOCH_SLOWING = config.indicators.stoch_slowing
        self.ATR_PERIOD = config.indicators.atr_period

    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                             k_period: int = 5, d_period: int = 3, slowing: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k = k.rolling(window=slowing).mean()  # Slow K
        d = k.rolling(window=d_period).mean()  # Slow D

        return k, d

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series,
                       volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price (approximation for forex)"""
        # For forex, we approximate VWAP using typical price
        typical_price = (high + low + close) / 3

        if volume is not None and len(volume) > 0 and volume.sum() > 0:
            cumulative_tp_volume = (typical_price * volume).cumsum()
            cumulative_volume = volume.cumsum()
            vwap = cumulative_tp_volume / cumulative_volume
        else:
            # Fallback: Use simple moving average of typical price
            vwap = typical_price.rolling(window=20).mean()

        return vwap

    def get_indicator_values(self, symbol: str) -> Optional[IndicatorValues]:
        """
        Get current indicator values for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            IndicatorValues object or None if data unavailable
        """
        if not MT5_AVAILABLE or self.mt5 is None:
            return None

        try:
            # Get M15 data
            rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
            if rates_m15 is None or len(rates_m15) < 30:
                return None

            df_m15 = pd.DataFrame(rates_m15)

            # Get M5 data
            rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            if rates_m5 is None or len(rates_m5) < 30:
                return None

            df_m5 = pd.DataFrame(rates_m5)

            # Get M1 data
            rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 30)
            if rates_m1 is None or len(rates_m1) < 20:
                return None

            df_m1 = pd.DataFrame(rates_m1)

            # Calculate indicators
            values = IndicatorValues()

            # M15 EMAs
            ema_fast_m15 = self.calculate_ema(df_m15['close'], self.EMA_FAST)
            ema_slow_m15 = self.calculate_ema(df_m15['close'], self.EMA_SLOW)
            values.ema_fast_m15 = ema_fast_m15.iloc[-1]
            values.ema_slow_m15 = ema_slow_m15.iloc[-1]

            # M5 Indicators
            ema_fast_m5 = self.calculate_ema(df_m5['close'], self.EMA_FAST)
            ema_slow_m5 = self.calculate_ema(df_m5['close'], self.EMA_SLOW)
            rsi_m5 = self.calculate_rsi(df_m5['close'], self.RSI_PERIOD)

            values.ema_fast_m5 = ema_fast_m5.iloc[-1]
            values.ema_slow_m5 = ema_slow_m5.iloc[-1]
            values.rsi_m5 = rsi_m5.iloc[-1]
            values.close_m5 = df_m5['close'].iloc[-1]

            # VWAP approximation
            tick_volume = df_m5['tick_volume'] if 'tick_volume' in df_m5 else None
            vwap = self.calculate_vwap(df_m5['high'], df_m5['low'], df_m5['close'], tick_volume)
            values.vwap_m5 = vwap.iloc[-1]

            # M1 Stochastic and ATR
            stoch_k, stoch_d = self.calculate_stochastic(
                df_m1['high'], df_m1['low'], df_m1['close'],
                self.STOCH_K, self.STOCH_D, self.STOCH_SLOWING
            )
            atr_m1 = self.calculate_atr(df_m1['high'], df_m1['low'], df_m1['close'], self.ATR_PERIOD)

            values.stoch_k_m1 = stoch_k.iloc[-1]
            values.stoch_d_m1 = stoch_d.iloc[-1]
            values.stoch_k_prev_m1 = stoch_k.iloc[-2] if len(stoch_k) > 1 else stoch_k.iloc[-1]
            values.atr_m1 = atr_m1.iloc[-1]

            return values

        except Exception as e:
            logger.error(f"Error getting indicator values for {symbol}: {e}")
            return None

    def analyze_m15_trend(self, values: IndicatorValues) -> str:
        """
        Analyze M15 trend direction

        Returns:
            "BULLISH", "BEARISH", or "NEUTRAL"
        """
        if values.ema_fast_m15 > values.ema_slow_m15:
            return "BULLISH"
        elif values.ema_fast_m15 < values.ema_slow_m15:
            return "BEARISH"
        return "NEUTRAL"

    def analyze_m5_confirmation(self, values: IndicatorValues, trend: str) -> bool:
        """
        Check M5 confirmation for the trend

        Args:
            values: Indicator values
            trend: M15 trend direction

        Returns:
            True if confirmed, False otherwise
        """
        if trend == "BULLISH":
            # Buy conditions:
            # 1. EMA fast > EMA slow
            # 2. Price > VWAP
            # 3. RSI between 40-70
            ema_ok = values.ema_fast_m5 > values.ema_slow_m5
            vwap_ok = values.close_m5 > values.vwap_m5
            rsi_ok = self.RSI_BUY_MIN <= values.rsi_m5 <= self.RSI_BUY_MAX

            return ema_ok and vwap_ok and rsi_ok

        elif trend == "BEARISH":
            # Sell conditions:
            # 1. EMA fast < EMA slow
            # 2. Price < VWAP
            # 3. RSI between 30-60
            ema_ok = values.ema_fast_m5 < values.ema_slow_m5
            vwap_ok = values.close_m5 < values.vwap_m5
            rsi_ok = self.RSI_SELL_MIN <= values.rsi_m5 <= self.RSI_SELL_MAX

            return ema_ok and vwap_ok and rsi_ok

        return False

    def analyze_m1_entry(self, values: IndicatorValues, trend: str) -> Tuple[bool, str]:
        """
        Check M1 entry timing

        Args:
            values: Indicator values
            trend: M15 trend direction

        Returns:
            Tuple of (entry_valid, reason)
        """
        k_current = values.stoch_k_m1
        k_prev = values.stoch_k_prev_m1
        d_current = values.stoch_d_m1

        # Check minimum ATR (volatility)
        min_atr = 0.0003  # Minimum ATR threshold
        if values.atr_m1 < min_atr:
            return False, "ATR too low"

        if trend == "BULLISH":
            # Buy entry: Stochastic crosses up from oversold
            if k_prev < self.STOCH_OVERSOLD and k_current > k_prev and k_current > d_current:
                return True, "Stochastic bullish cross from oversold"

        elif trend == "BEARISH":
            # Sell entry: Stochastic crosses down from overbought
            if k_prev > self.STOCH_OVERBOUGHT and k_current < k_prev and k_current < d_current:
                return True, "Stochastic bearish cross from overbought"

        return False, "No entry signal"

    def get_signal(self, symbol: str) -> SignalResult:
        """
        Get trading signal for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            SignalResult object
        """
        # Default result
        default_result = SignalResult(
            signal_type=SignalType.NONE,
            confidence=0.0,
            m15_trend="NEUTRAL",
            m5_confirmed=False,
            m1_entry=False,
            indicators=IndicatorValues(),
            reason="No signal"
        )

        # Check cooldown (prevent multiple signals in short time)
        current_time = datetime.now().timestamp()
        last_signal = self.last_signal_time.get(symbol, 0)
        if current_time - last_signal < 60:  # 60 second cooldown
            default_result.reason = "Cooldown active"
            return default_result

        # Get indicator values
        values = self.get_indicator_values(symbol)
        if values is None:
            default_result.reason = "Cannot get indicator values"
            return default_result

        # Step 1: M15 Trend
        m15_trend = self.analyze_m15_trend(values)
        if m15_trend == "NEUTRAL":
            return SignalResult(
                signal_type=SignalType.NONE,
                confidence=0.0,
                m15_trend=m15_trend,
                m5_confirmed=False,
                m1_entry=False,
                indicators=values,
                reason="No clear M15 trend"
            )

        # Step 2: M5 Confirmation
        m5_confirmed = self.analyze_m5_confirmation(values, m15_trend)
        if not m5_confirmed:
            return SignalResult(
                signal_type=SignalType.NONE,
                confidence=0.0,
                m15_trend=m15_trend,
                m5_confirmed=False,
                m1_entry=False,
                indicators=values,
                reason="M5 not confirmed"
            )

        # Step 3: M1 Entry
        m1_entry, entry_reason = self.analyze_m1_entry(values, m15_trend)
        if not m1_entry:
            return SignalResult(
                signal_type=SignalType.NONE,
                confidence=0.0,
                m15_trend=m15_trend,
                m5_confirmed=True,
                m1_entry=False,
                indicators=values,
                reason=f"M1 entry not valid: {entry_reason}"
            )

        # All conditions met - generate signal
        signal_type = SignalType.BUY if m15_trend == "BULLISH" else SignalType.SELL

        # Update cooldown
        self.last_signal_time[symbol] = current_time

        # Calculate confidence based on indicator alignment
        confidence = self._calculate_confidence(values, m15_trend)

        return SignalResult(
            signal_type=signal_type,
            confidence=confidence,
            m15_trend=m15_trend,
            m5_confirmed=True,
            m1_entry=True,
            indicators=values,
            reason=entry_reason
        )

    def _calculate_confidence(self, values: IndicatorValues, trend: str) -> float:
        """Calculate signal confidence score (0-100)"""
        confidence = 50.0  # Base confidence

        # EMA alignment bonus
        if trend == "BULLISH":
            if values.ema_fast_m15 > values.ema_slow_m15:
                confidence += 10
            if values.ema_fast_m5 > values.ema_slow_m5:
                confidence += 10
        else:
            if values.ema_fast_m15 < values.ema_slow_m15:
                confidence += 10
            if values.ema_fast_m5 < values.ema_slow_m5:
                confidence += 10

        # RSI position bonus
        if trend == "BULLISH" and 45 <= values.rsi_m5 <= 55:
            confidence += 5
        elif trend == "BEARISH" and 45 <= values.rsi_m5 <= 55:
            confidence += 5

        # Stochastic extremes bonus
        if trend == "BULLISH" and values.stoch_k_prev_m1 < 15:
            confidence += 10
        elif trend == "BEARISH" and values.stoch_k_prev_m1 > 85:
            confidence += 10

        # ATR strength bonus
        if values.atr_m1 > 0.0005:
            confidence += 5

        return min(100.0, confidence)

    def get_indicators_status(self, symbol: str) -> Dict:
        """Get formatted indicator status for display"""
        values = self.get_indicator_values(symbol)
        if values is None:
            return {"error": "Cannot get indicator values"}

        m15_trend = self.analyze_m15_trend(values)

        return {
            "symbol": symbol,
            "m15_trend": m15_trend,
            "m15": {
                "ema_fast": round(values.ema_fast_m15, 5),
                "ema_slow": round(values.ema_slow_m15, 5)
            },
            "m5": {
                "ema_fast": round(values.ema_fast_m5, 5),
                "ema_slow": round(values.ema_slow_m5, 5),
                "rsi": round(values.rsi_m5, 2),
                "vwap": round(values.vwap_m5, 5),
                "close": round(values.close_m5, 5)
            },
            "m1": {
                "stoch_k": round(values.stoch_k_m1, 2),
                "stoch_d": round(values.stoch_d_m1, 2),
                "atr": round(values.atr_m1, 6)
            }
        }
