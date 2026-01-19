"""
Motor Principal de Backtesting
===============================

Orquesta la simulación completa del backtest.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
from .trade import Trade, TradeType, TradeStatus
from .portfolio import Portfolio
from .signal_engine_bt import SignalEngineBT, SignalType
from .statistics import Statistics
from .visualizer import Visualizer
from .report import ReportGenerator


class Backtester:
    """
    Motor principal de backtesting que simula la estrategia Multi-TF
    """

    def __init__(
        self,
        symbol: str,
        initial_balance: float = 10000.0,
        leverage: int = 100,
        commission_per_lot: float = 0.0,
        spread_pips: float = 1.0,
        risk_per_trade: float = 1.0,
        max_drawdown_percent: float = 10.0,
        max_daily_drawdown_percent: float = 5.0,
        max_daily_trades: int = 10,
        stop_loss_pips: float = 12.0,
        rr_partial: float = 2.0,
        rr_final: float = 3.0,
        partial_close_percent: float = 50.0,
        # Horarios de sesión (UTC)
        london_start: int = 8,
        london_end: int = 12,
        ny_start: int = 13,
        ny_end: int = 17,
        # Parámetros de indicadores
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_period: int = 14,
        stoch_k: int = 5,
        stoch_d: int = 3,
        stoch_slowing: int = 3,
        atr_period: int = 14,
        min_atr: float = 0.0003,
    ):
        """
        Inicializa el backtester

        Args:
            symbol: Símbolo a testear
            initial_balance: Balance inicial
            leverage: Apalancamiento
            commission_per_lot: Comisión por lote
            spread_pips: Spread en pips
            risk_per_trade: Riesgo por trade en %
            max_drawdown_percent: Máximo drawdown permitido
            max_daily_drawdown_percent: Máximo drawdown diario
            max_daily_trades: Máximo de trades por día
            stop_loss_pips: Stop loss en pips
            rr_partial: Risk:Reward para cierre parcial
            rr_final: Risk:Reward para cierre final
            partial_close_percent: % de cierre parcial
            london_start: Hora inicio sesión Londres
            london_end: Hora fin sesión Londres
            ny_start: Hora inicio sesión NY
            ny_end: Hora fin sesión NY
            ... (parámetros de indicadores)
        """
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.commission_per_lot = commission_per_lot
        self.spread_pips = spread_pips
        self.risk_per_trade = risk_per_trade
        self.max_drawdown_percent = max_drawdown_percent
        self.max_daily_drawdown_percent = max_daily_drawdown_percent
        self.max_daily_trades = max_daily_trades
        self.stop_loss_pips = stop_loss_pips
        self.rr_partial = rr_partial
        self.rr_final = rr_final
        self.partial_close_percent = partial_close_percent / 100.0

        # Sesiones
        self.london_start = time(london_start, 0)
        self.london_end = time(london_end, 0)
        self.ny_start = time(ny_start, 0)
        self.ny_end = time(ny_end, 0)

        # Portfolio
        self.portfolio = Portfolio(
            initial_balance=initial_balance,
            leverage=leverage,
            commission_per_lot=commission_per_lot,
            spread_pips=spread_pips
        )

        # Signal Engine
        self.signal_engine = SignalEngineBT(
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            rsi_period=rsi_period,
            stoch_k=stoch_k,
            stoch_d=stoch_d,
            stoch_slowing=stoch_slowing,
            atr_period=atr_period,
            min_atr=min_atr
        )

        # Control
        self.ticket_counter = 1
        self.current_date: Optional[datetime] = None

    def run(
        self,
        data_m1: pd.DataFrame,
        data_m5: pd.DataFrame,
        data_m15: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Ejecuta el backtest

        Args:
            data_m1: Datos M1
            data_m5: Datos M5
            data_m15: Datos M15
            start_date: Fecha inicial (opcional)
            end_date: Fecha final (opcional)
            verbose: Mostrar progreso

        Returns:
            Dict con resultados
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"INICIANDO BACKTEST: {self.symbol}")
            print(f"{'='*70}\n")

        # Filtrar fechas si se especifican
        if start_date:
            data_m1 = data_m1[data_m1["time"] >= start_date]
            data_m5 = data_m5[data_m5["time"] >= start_date]
            data_m15 = data_m15[data_m15["time"] >= start_date]

        if end_date:
            data_m1 = data_m1[data_m1["time"] <= end_date]
            data_m5 = data_m5[data_m5["time"] <= end_date]
            data_m15 = data_m15[data_m15["time"] <= end_date]

        # Calcular indicadores
        if verbose:
            print("Calculando indicadores...")

        data_m1, data_m5, data_m15 = self.signal_engine.calculate_indicators(
            data_m1, data_m5, data_m15
        )

        # Simular tick por tick (cada barra M1)
        if verbose:
            print(f"Simulando {len(data_m1)} barras M1...\n")

        total_bars = len(data_m1)
        progress_step = max(1, total_bars // 20)  # 5% progress

        for idx, row in data_m1.iterrows():
            current_time = pd.Timestamp(row["time"])
            current_price = row["close"]

            # Progreso
            if verbose and idx % progress_step == 0:
                progress = (idx / total_bars) * 100
                print(f"Progreso: {progress:.1f}% - {current_time} - Balance: ${self.portfolio.balance:.2f}")

            # Control diario
            if self.current_date is None or current_time.date() != self.current_date:
                self.current_date = current_time.date()
                self.portfolio.reset_daily_stats()

            # Actualizar equity
            prices = {self.symbol: current_price}
            self.portfolio.update_equity(current_time, prices)

            # Gestionar posiciones abiertas
            self._manage_open_positions(row, current_time)

            # Verificar límites
            if not self._check_limits():
                if verbose and idx % (progress_step * 5) == 0:
                    print(f"  -> Límites alcanzados, no se abren nuevas posiciones")
                continue

            # Verificar sesión de trading
            if not self._is_trading_session(current_time):
                continue

            # Obtener señal
            signal, details = self.signal_engine.get_signal(
                current_time, data_m1, data_m5, data_m15
            )

            # Ejecutar trade si hay señal
            if signal != SignalType.NONE:
                self._open_trade(signal, row, current_time, details)

        # Cerrar todas las posiciones al final
        if self.portfolio.open_trades:
            if verbose:
                print(f"\nCerrando {len(self.portfolio.open_trades)} posiciones al final del backtest...")

            final_price = data_m1.iloc[-1]["close"]
            final_time = pd.Timestamp(data_m1.iloc[-1]["time"])
            self.portfolio.close_all_trades(final_price, final_time, "End of backtest")

        # Calcular estadísticas
        if verbose:
            print("\nCalculando estadísticas...")

        stats = self.portfolio.get_statistics()

        if verbose:
            print(f"\n{'='*70}")
            print("BACKTEST COMPLETADO")
            print(f"{'='*70}")
            print(f"Balance Inicial: ${self.initial_balance:,.2f}")
            print(f"Balance Final: ${stats['final_balance']:,.2f}")
            print(f"Beneficio Neto: ${stats['net_profit']:,.2f}")
            print(f"Total Trades: {stats['total_trades']}")
            print(f"Win Rate: {stats['win_rate']:.2f}%")
            print(f"Profit Factor: {stats['profit_factor']:.2f}")
            print(f"Max Drawdown: {stats['max_drawdown_percent']:.2f}%")
            print(f"{'='*70}\n")

        return {
            "statistics": stats,
            "trades": self.portfolio.closed_trades,
            "equity_curve": self.portfolio.equity_curve,
            "config": self._get_config()
        }

    def _manage_open_positions(self, bar: pd.Series, current_time: datetime):
        """
        Gestiona posiciones abiertas (SL, TP parcial, TP final)

        Args:
            bar: Barra actual M1
            current_time: Tiempo actual
        """
        trades_to_close = []
        trades_to_partial_close = []

        high = bar["high"]
        low = bar["low"]
        close_price = bar["close"]

        for trade in self.portfolio.open_trades:
            # Verificar Stop Loss
            if trade.check_stop_loss(low if trade.trade_type == TradeType.BUY else high):
                trades_to_close.append((trade, trade.stop_loss, "Stop Loss"))
                continue

            # Verificar Take Profit Final
            if trade.check_take_profit_final(high if trade.trade_type == TradeType.BUY else low):
                tp_price = trade.take_profit_final
                trades_to_close.append((trade, tp_price, "Take Profit Final"))
                continue

            # Verificar Take Profit Parcial
            if trade.check_take_profit_partial(high if trade.trade_type == TradeType.BUY else low):
                tp_price = trade.take_profit_partial
                trades_to_partial_close.append((trade, tp_price))

        # Ejecutar cierres parciales
        for trade, price in trades_to_partial_close:
            self.portfolio.partial_close_trade(
                trade, price, current_time, self.partial_close_percent
            )

        # Ejecutar cierres completos
        for trade, price, reason in trades_to_close:
            self.portfolio.close_trade(trade, price, current_time, reason)

    def _open_trade(
        self,
        signal: SignalType,
        bar: pd.Series,
        current_time: datetime,
        details: Dict
    ):
        """
        Abre un nuevo trade

        Args:
            signal: Tipo de señal
            bar: Barra actual
            current_time: Tiempo actual
            details: Detalles de la señal
        """
        # Precio de entrada (considerar spread)
        if signal == SignalType.BUY:
            entry_price = bar["close"] + (self.spread_pips * 0.0001)
            trade_type = TradeType.BUY
        else:
            entry_price = bar["close"]
            trade_type = TradeType.SELL

        # Calcular SL y TP
        sl_distance = self.stop_loss_pips * 0.0001

        if trade_type == TradeType.BUY:
            stop_loss = entry_price - sl_distance
            take_profit_partial = entry_price + (sl_distance * self.rr_partial)
            take_profit_final = entry_price + (sl_distance * self.rr_final)
        else:
            stop_loss = entry_price + sl_distance
            take_profit_partial = entry_price - (sl_distance * self.rr_partial)
            take_profit_final = entry_price - (sl_distance * self.rr_final)

        # Calcular volumen (lote)
        volume = self._calculate_lot_size(entry_price, stop_loss)

        if volume <= 0:
            return

        # Crear trade
        trade = Trade(
            ticket=self.ticket_counter,
            symbol=self.symbol,
            trade_type=trade_type,
            entry_time=current_time,
            entry_price=entry_price,
            volume=volume,
            stop_loss=stop_loss,
            take_profit_partial=take_profit_partial,
            take_profit_final=take_profit_final,
            comment=f"Signal: {signal.value}"
        )

        self.ticket_counter += 1

        # Añadir al portfolio
        self.portfolio.add_trade(trade)

    def _calculate_lot_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Calcula el tamaño del lote basado en el riesgo

        Args:
            entry_price: Precio de entrada
            stop_loss: Precio del stop loss

        Returns:
            Tamaño del lote
        """
        # Riesgo en dinero
        risk_amount = self.portfolio.balance * (self.risk_per_trade / 100.0)

        # Distancia del SL en pips
        sl_distance_pips = abs(entry_price - stop_loss) * 10000

        if sl_distance_pips == 0:
            return 0.01

        # Valor del pip (para 1 lote estándar)
        pip_value = 10.0  # Para pares con USD como quote currency

        # Calcular lote
        lot_size = risk_amount / (sl_distance_pips * pip_value)

        # Normalizar (mínimo 0.01, múltiplos de 0.01)
        lot_size = max(0.01, round(lot_size, 2))

        return lot_size

    def _check_limits(self) -> bool:
        """
        Verifica límites de trading

        Returns:
            True si se puede seguir operando
        """
        # Verificar límites diarios
        if not self.portfolio.check_daily_limits(
            self.max_daily_trades,
            self.max_daily_drawdown_percent
        ):
            return False

        # Verificar drawdown global
        if not self.portfolio.check_global_drawdown(self.max_drawdown_percent):
            return False

        # Verificar que no haya más de 1 posición abierta (scalping)
        if len(self.portfolio.open_trades) >= 1:
            return False

        return True

    def _is_trading_session(self, current_time: datetime) -> bool:
        """
        Verifica si está en horario de trading

        Args:
            current_time: Tiempo actual

        Returns:
            True si está en sesión
        """
        current_hour = current_time.time()

        # Sesión de Londres
        in_london = self.london_start <= current_hour < self.london_end

        # Sesión de NY
        in_ny = self.ny_start <= current_hour < self.ny_end

        return in_london or in_ny

    def _get_config(self) -> Dict:
        """
        Obtiene configuración del backtest

        Returns:
            Dict con configuración
        """
        return {
            "symbol": self.symbol,
            "initial_balance": self.initial_balance,
            "leverage": self.leverage,
            "commission_per_lot": self.commission_per_lot,
            "spread_pips": self.spread_pips,
            "risk_per_trade": self.risk_per_trade,
            "max_drawdown_percent": self.max_drawdown_percent,
            "max_daily_drawdown_percent": self.max_daily_drawdown_percent,
            "max_daily_trades": self.max_daily_trades,
            "stop_loss_pips": self.stop_loss_pips,
            "rr_partial": self.rr_partial,
            "rr_final": self.rr_final,
            "partial_close_percent": self.partial_close_percent * 100,
        }

    def generate_reports(
        self,
        results: Dict,
        output_dir: str = "./backtest_results"
    ):
        """
        Genera reportes y gráficos

        Args:
            results: Resultados del backtest
            output_dir: Directorio de salida
        """
        print("\n" + "="*70)
        print("GENERANDO REPORTES Y VISUALIZACIONES")
        print("="*70)

        # Estadísticas detalladas
        stats_calc = Statistics(
            results["trades"],
            results["equity_curve"]
        )
        detailed_stats = stats_calc.calculate_all()
        monthly_returns = stats_calc.calculate_monthly_returns()
        consecutive_stats = stats_calc.calculate_consecutive_stats()

        # Añadir estadísticas adicionales
        detailed_stats.update(consecutive_stats)
        detailed_stats.update(results["config"])

        # Reportes
        report_gen = ReportGenerator(output_dir)
        report_gen.generate_all_reports(
            detailed_stats,
            results["config"],
            results["trades"],
            results["equity_curve"]
        )

        # Visualizaciones
        viz = Visualizer()
        viz.plot_all(
            results["equity_curve"],
            results["trades"],
            self.initial_balance,
            monthly_returns,
            output_dir
        )

        print(f"\n{'='*70}")
        print(f"Resultados guardados en: {output_dir}")
        print(f"{'='*70}\n")
