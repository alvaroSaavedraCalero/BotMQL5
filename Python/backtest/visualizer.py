"""
Visualización de Resultados
============================

Genera gráficos y visualizaciones de los resultados del backtest.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

try:
    import seaborn as sns
    sns.set_style("darkgrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


class Visualizer:
    """
    Genera visualizaciones de resultados del backtest
    """

    def __init__(self, figsize=(14, 8), style="darkgrid"):
        """
        Inicializa el visualizador

        Args:
            figsize: Tamaño de las figuras
            style: Estilo de los gráficos
        """
        self.figsize = figsize
        if HAS_SEABORN:
            sns.set_style(style)

    def plot_equity_curve(
        self,
        equity_curve: List[dict],
        initial_balance: float,
        save_path: Optional[str] = None
    ):
        """
        Grafica curva de equity

        Args:
            equity_curve: Lista con histórico de equity
            initial_balance: Balance inicial
            save_path: Path para guardar gráfico
        """
        if not equity_curve:
            print("No hay datos de equity para graficar")
            return

        df = pd.DataFrame(equity_curve)
        df["time"] = pd.to_datetime(df["time"])

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # Equity y Balance
        ax1.plot(df["time"], df["balance"], label="Balance", linewidth=2, color="blue")
        ax1.plot(df["time"], df["equity"], label="Equity", linewidth=1.5, color="orange", alpha=0.8)
        ax1.axhline(y=initial_balance, color="red", linestyle="--", label="Balance Inicial", alpha=0.5)
        ax1.set_ylabel("Valor ($)", fontsize=12)
        ax1.set_title("Curva de Equity", fontsize=14, fontweight="bold")
        ax1.legend(loc="best")
        ax1.grid(True, alpha=0.3)

        # P/L Flotante
        ax2.plot(df["time"], df["floating_pl"], label="P/L Flotante", linewidth=1, color="green")
        ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax2.fill_between(
            df["time"],
            df["floating_pl"],
            0,
            where=(df["floating_pl"] >= 0),
            color="green",
            alpha=0.3,
            interpolate=True
        )
        ax2.fill_between(
            df["time"],
            df["floating_pl"],
            0,
            where=(df["floating_pl"] < 0),
            color="red",
            alpha=0.3,
            interpolate=True
        )
        ax2.set_xlabel("Fecha", fontsize=12)
        ax2.set_ylabel("P/L Flotante ($)", fontsize=12)
        ax2.legend(loc="best")
        ax2.grid(True, alpha=0.3)

        # Formato de fechas
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Gráfico guardado en: {save_path}")

        plt.show()

    def plot_drawdown(
        self,
        equity_curve: List[dict],
        save_path: Optional[str] = None
    ):
        """
        Grafica drawdown

        Args:
            equity_curve: Lista con histórico de equity
            save_path: Path para guardar gráfico
        """
        if not equity_curve:
            print("No hay datos para graficar drawdown")
            return

        df = pd.DataFrame(equity_curve)
        df["time"] = pd.to_datetime(df["time"])

        # Calcular drawdown
        df["peak"] = df["equity"].cummax()
        df["drawdown"] = df["peak"] - df["equity"]
        df["drawdown_pct"] = (df["drawdown"] / df["peak"]) * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # Equity con peaks
        ax1.plot(df["time"], df["equity"], label="Equity", linewidth=2, color="blue")
        ax1.plot(df["time"], df["peak"], label="Peak", linewidth=1, color="green", linestyle="--", alpha=0.7)
        ax1.fill_between(
            df["time"],
            df["peak"],
            df["equity"],
            color="red",
            alpha=0.2,
            label="Drawdown"
        )
        ax1.set_ylabel("Equity ($)", fontsize=12)
        ax1.set_title("Equity y Drawdown", fontsize=14, fontweight="bold")
        ax1.legend(loc="best")
        ax1.grid(True, alpha=0.3)

        # Drawdown %
        ax2.fill_between(
            df["time"],
            0,
            -df["drawdown_pct"],
            color="red",
            alpha=0.5
        )
        ax2.plot(df["time"], -df["drawdown_pct"], color="darkred", linewidth=1)
        ax2.set_xlabel("Fecha", fontsize=12)
        ax2.set_ylabel("Drawdown (%)", fontsize=12)
        ax2.grid(True, alpha=0.3)

        # Formato de fechas
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Gráfico guardado en: {save_path}")

        plt.show()

    def plot_trade_distribution(
        self,
        trades: List,
        save_path: Optional[str] = None
    ):
        """
        Grafica distribución de trades

        Args:
            trades: Lista de trades
            save_path: Path para guardar gráfico
        """
        if not trades:
            print("No hay trades para graficar")
            return

        profits = [t.profit for t in trades]

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)

        # Histograma de profits
        ax1.hist(profits, bins=30, color="skyblue", edgecolor="black", alpha=0.7)
        ax1.axvline(x=0, color="red", linestyle="--", linewidth=2)
        ax1.set_xlabel("Profit ($)", fontsize=11)
        ax1.set_ylabel("Frecuencia", fontsize=11)
        ax1.set_title("Distribución de Profits", fontsize=12, fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # Profits acumulados
        cumulative_profits = np.cumsum(profits)
        ax2.plot(range(len(cumulative_profits)), cumulative_profits, linewidth=2, color="green")
        ax2.axhline(y=0, color="red", linestyle="--", linewidth=1)
        ax2.set_xlabel("Número de Trade", fontsize=11)
        ax2.set_ylabel("Profit Acumulado ($)", fontsize=11)
        ax2.set_title("Profit Acumulado por Trade", fontsize=12, fontweight="bold")
        ax2.grid(True, alpha=0.3)

        # Ganadores vs Perdedores
        winners = sum(1 for p in profits if p > 0)
        losers = sum(1 for p in profits if p < 0)
        breakeven = sum(1 for p in profits if p == 0)

        ax3.pie(
            [winners, losers, breakeven],
            labels=["Ganadores", "Perdedores", "Break-even"],
            autopct="%1.1f%%",
            colors=["green", "red", "gray"],
            startangle=90
        )
        ax3.set_title("Distribución de Resultados", fontsize=12, fontweight="bold")

        # Box plot
        winning_profits = [p for p in profits if p > 0]
        losing_profits = [p for p in profits if p < 0]

        ax4.boxplot(
            [winning_profits, losing_profits],
            labels=["Ganadores", "Perdedores"],
            patch_artist=True,
            boxprops=dict(facecolor="lightblue", alpha=0.7),
            medianprops=dict(color="red", linewidth=2)
        )
        ax4.set_ylabel("Profit ($)", fontsize=11)
        ax4.set_title("Distribución de Ganadores vs Perdedores", fontsize=12, fontweight="bold")
        ax4.grid(True, alpha=0.3, axis="y")
        ax4.axhline(y=0, color="red", linestyle="--", linewidth=1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Gráfico guardado en: {save_path}")

        plt.show()

    def plot_monthly_returns(
        self,
        monthly_returns: pd.DataFrame,
        save_path: Optional[str] = None
    ):
        """
        Grafica retornos mensuales

        Args:
            monthly_returns: DataFrame con retornos mensuales
            save_path: Path para guardar gráfico
        """
        if monthly_returns.empty:
            print("No hay datos mensuales para graficar")
            return

        fig, ax = plt.subplots(figsize=self.figsize)

        colors = ["green" if x >= 0 else "red" for x in monthly_returns["profit"]]

        ax.bar(
            monthly_returns["year_month"],
            monthly_returns["profit"],
            color=colors,
            alpha=0.7,
            edgecolor="black"
        )

        ax.axhline(y=0, color="black", linewidth=1)
        ax.set_xlabel("Mes", fontsize=12)
        ax.set_ylabel("Profit ($)", fontsize=12)
        ax.set_title("Retornos Mensuales", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")

        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Gráfico guardado en: {save_path}")

        plt.show()

    def plot_all(
        self,
        equity_curve: List[dict],
        trades: List,
        initial_balance: float,
        monthly_returns: pd.DataFrame,
        output_dir: str = "./backtest_results"
    ):
        """
        Genera todos los gráficos

        Args:
            equity_curve: Histórico de equity
            trades: Lista de trades
            initial_balance: Balance inicial
            monthly_returns: Retornos mensuales
            output_dir: Directorio para guardar gráficos
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        print("\nGenerando gráficos...")

        # Equity curve
        print("1. Curva de Equity...")
        self.plot_equity_curve(
            equity_curve,
            initial_balance,
            save_path=f"{output_dir}/equity_curve.png"
        )

        # Drawdown
        print("2. Drawdown...")
        self.plot_drawdown(
            equity_curve,
            save_path=f"{output_dir}/drawdown.png"
        )

        # Distribución de trades
        print("3. Distribución de Trades...")
        self.plot_trade_distribution(
            trades,
            save_path=f"{output_dir}/trade_distribution.png"
        )

        # Retornos mensuales
        if not monthly_returns.empty:
            print("4. Retornos Mensuales...")
            self.plot_monthly_returns(
                monthly_returns,
                save_path=f"{output_dir}/monthly_returns.png"
            )

        print(f"\nTodos los gráficos guardados en: {output_dir}")
