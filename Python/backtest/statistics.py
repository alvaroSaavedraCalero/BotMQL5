"""
Cálculo de Estadísticas de Backtest
====================================

Calcula métricas de rendimiento para análisis de resultados.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from .trade import Trade, TradeStatus


class Statistics:
    """
    Calcula estadísticas de rendimiento del backtest
    """

    def __init__(self, trades: List[Trade], equity_curve: List[dict]):
        """
        Inicializa el módulo de estadísticas

        Args:
            trades: Lista de trades cerrados
            equity_curve: Historial de equity
        """
        self.trades = trades
        self.equity_curve = equity_curve

    def calculate_all(self) -> Dict:
        """
        Calcula todas las estadísticas

        Returns:
            Dict con todas las métricas
        """
        if not self.trades:
            return self._empty_stats()

        return {
            **self._basic_stats(),
            **self._profit_stats(),
            **self._drawdown_stats(),
            **self._risk_metrics(),
            **self._time_analysis(),
            **self._distribution_stats(),
        }

    def _empty_stats(self) -> Dict:
        """Retorna estadísticas vacías"""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_percent": 0.0,
        }

    def _basic_stats(self) -> Dict:
        """Estadísticas básicas"""
        total = len(self.trades)
        winners = sum(1 for t in self.trades if t.profit > 0)
        losers = sum(1 for t in self.trades if t.profit < 0)
        breakeven = sum(1 for t in self.trades if t.profit == 0)

        win_rate = (winners / total * 100) if total > 0 else 0.0

        return {
            "total_trades": total,
            "winning_trades": winners,
            "losing_trades": losers,
            "breakeven_trades": breakeven,
            "win_rate": win_rate,
        }

    def _profit_stats(self) -> Dict:
        """Estadísticas de beneficios"""
        profits = [t.profit for t in self.trades]
        winning_profits = [p for p in profits if p > 0]
        losing_profits = [p for p in profits if p < 0]

        net_profit = sum(profits)
        gross_profit = sum(winning_profits) if winning_profits else 0.0
        gross_loss = abs(sum(losing_profits)) if losing_profits else 0.0

        profit_factor = (
            gross_profit / gross_loss if gross_loss > 0 else 0.0
        )

        expectancy = net_profit / len(profits) if profits else 0.0

        avg_win = (
            sum(winning_profits) / len(winning_profits)
            if winning_profits
            else 0.0
        )

        avg_loss = (
            abs(sum(losing_profits)) / len(losing_profits)
            if losing_profits
            else 0.0
        )

        largest_win = max(profits) if profits else 0.0
        largest_loss = min(profits) if profits else 0.0

        return {
            "net_profit": net_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "avg_win": avg_win,
            "avg_loss": abs(avg_loss),
            "largest_win": largest_win,
            "largest_loss": abs(largest_loss),
            "avg_win_loss_ratio": avg_win / avg_loss if avg_loss > 0 else 0.0,
        }

    def _drawdown_stats(self) -> Dict:
        """Estadísticas de drawdown"""
        if not self.equity_curve:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_percent": 0.0,
                "avg_drawdown": 0.0,
                "avg_drawdown_percent": 0.0,
                "recovery_factor": 0.0,
            }

        # Convertir a DataFrame
        df = pd.DataFrame(self.equity_curve)

        # Calcular drawdowns
        df["peak"] = df["equity"].cummax()
        df["drawdown"] = df["peak"] - df["equity"]
        df["drawdown_pct"] = (df["drawdown"] / df["peak"]) * 100

        max_dd = df["drawdown"].max()
        max_dd_pct = df["drawdown_pct"].max()

        # Drawdowns promedio (solo cuando hay drawdown)
        dd_mask = df["drawdown"] > 0
        avg_dd = df.loc[dd_mask, "drawdown"].mean() if dd_mask.any() else 0.0
        avg_dd_pct = df.loc[dd_mask, "drawdown_pct"].mean() if dd_mask.any() else 0.0

        # Recovery factor
        net_profit = sum(t.profit for t in self.trades)
        recovery_factor = net_profit / max_dd if max_dd > 0 else 0.0

        return {
            "max_drawdown": max_dd,
            "max_drawdown_percent": max_dd_pct,
            "avg_drawdown": avg_dd,
            "avg_drawdown_percent": avg_dd_pct,
            "recovery_factor": recovery_factor,
        }

    def _risk_metrics(self) -> Dict:
        """Métricas de riesgo"""
        if not self.equity_curve or len(self.equity_curve) < 2:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
            }

        df = pd.DataFrame(self.equity_curve)

        # Retornos
        df["returns"] = df["equity"].pct_change()
        returns = df["returns"].dropna()

        if len(returns) == 0:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
            }

        # Sharpe Ratio (asumiendo risk-free rate = 0)
        mean_return = returns.mean()
        std_return = returns.std()
        sharpe = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0

        # Sortino Ratio (solo downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        sortino = (
            (mean_return / downside_std) * np.sqrt(252)
            if downside_std > 0 and len(downside_returns) > 0
            else 0.0
        )

        # Calmar Ratio (return / max drawdown)
        annual_return = mean_return * 252
        max_dd_pct = self._drawdown_stats()["max_drawdown_percent"]
        calmar = (
            annual_return / (max_dd_pct / 100)
            if max_dd_pct > 0
            else 0.0
        )

        return {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
        }

    def _time_analysis(self) -> Dict:
        """Análisis temporal"""
        if not self.trades:
            return {
                "avg_trade_duration": 0.0,
                "avg_winning_duration": 0.0,
                "avg_losing_duration": 0.0,
            }

        durations = []
        winning_durations = []
        losing_durations = []

        for trade in self.trades:
            if trade.exit_time and trade.entry_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 60
                durations.append(duration)

                if trade.profit > 0:
                    winning_durations.append(duration)
                elif trade.profit < 0:
                    losing_durations.append(duration)

        return {
            "avg_trade_duration": np.mean(durations) if durations else 0.0,
            "avg_winning_duration": (
                np.mean(winning_durations) if winning_durations else 0.0
            ),
            "avg_losing_duration": (
                np.mean(losing_durations) if losing_durations else 0.0
            ),
        }

    def _distribution_stats(self) -> Dict:
        """Estadísticas de distribución"""
        profits = [t.profit for t in self.trades]

        if not profits:
            return {
                "median_profit": 0.0,
                "std_profit": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0,
            }

        return {
            "median_profit": np.median(profits),
            "std_profit": np.std(profits),
            "skewness": pd.Series(profits).skew(),
            "kurtosis": pd.Series(profits).kurtosis(),
        }

    def calculate_monthly_returns(self) -> pd.DataFrame:
        """
        Calcula retornos mensuales

        Returns:
            DataFrame con retornos por mes
        """
        if not self.trades:
            return pd.DataFrame()

        # Crear DataFrame de trades
        data = []
        for trade in self.trades:
            if trade.exit_time:
                data.append({
                    "date": trade.exit_time,
                    "profit": trade.profit,
                })

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["year_month"] = df["date"].dt.to_period("M")

        # Agrupar por mes
        monthly = df.groupby("year_month").agg({
            "profit": "sum"
        }).reset_index()

        monthly["year_month"] = monthly["year_month"].astype(str)

        return monthly

    def calculate_consecutive_stats(self) -> Dict:
        """
        Calcula rachas de victorias/derrotas

        Returns:
            Dict con estadísticas de rachas
        """
        if not self.trades:
            return {
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "current_streak": 0,
            }

        # Analizar rachas
        current_wins = 0
        current_losses = 0
        max_wins = 0
        max_losses = 0

        for trade in self.trades:
            if trade.profit > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.profit < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0

        # Racha actual
        last_trade = self.trades[-1]
        if last_trade.profit > 0:
            current_streak = current_wins
        elif last_trade.profit < 0:
            current_streak = -current_losses
        else:
            current_streak = 0

        return {
            "max_consecutive_wins": max_wins,
            "max_consecutive_losses": max_losses,
            "current_streak": current_streak,
        }

    def format_report(self, stats: Dict) -> str:
        """
        Formatea estadísticas como reporte de texto

        Args:
            stats: Dict con estadísticas

        Returns:
            Reporte formateado
        """
        report = []
        report.append("=" * 70)
        report.append("RESULTADOS DEL BACKTEST")
        report.append("=" * 70)

        report.append("\n--- Estadísticas Básicas ---")
        report.append(f"Total de Trades: {stats['total_trades']}")
        report.append(f"Trades Ganadores: {stats['winning_trades']}")
        report.append(f"Trades Perdedores: {stats['losing_trades']}")
        report.append(f"Win Rate: {stats['win_rate']:.2f}%")

        report.append("\n--- Beneficios ---")
        report.append(f"Beneficio Neto: ${stats['net_profit']:.2f}")
        report.append(f"Beneficio Bruto: ${stats['gross_profit']:.2f}")
        report.append(f"Pérdida Bruta: ${stats['gross_loss']:.2f}")
        report.append(f"Profit Factor: {stats['profit_factor']:.2f}")
        report.append(f"Expectativa por Trade: ${stats['expectancy']:.2f}")
        report.append(f"Ganancia Promedio: ${stats.get('avg_win', 0):.2f}")
        report.append(f"Pérdida Promedio: ${stats.get('avg_loss', 0):.2f}")

        report.append("\n--- Drawdown ---")
        report.append(f"Max Drawdown: ${stats['max_drawdown']:.2f}")
        report.append(f"Max Drawdown %: {stats['max_drawdown_percent']:.2f}%")
        report.append(f"Recovery Factor: {stats.get('recovery_factor', 0):.2f}")

        report.append("\n--- Métricas de Riesgo ---")
        report.append(f"Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}")
        report.append(f"Sortino Ratio: {stats.get('sortino_ratio', 0):.2f}")
        report.append(f"Calmar Ratio: {stats.get('calmar_ratio', 0):.2f}")

        report.append("\n" + "=" * 70)

        return "\n".join(report)
