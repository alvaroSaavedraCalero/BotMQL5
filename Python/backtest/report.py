"""
Generación de Reportes
=======================

Genera reportes detallados en diferentes formatos.
"""

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict
from .trade import Trade


class ReportGenerator:
    """
    Genera reportes de backtest en múltiples formatos
    """

    def __init__(self, output_dir: str = "./backtest_results"):
        """
        Inicializa el generador de reportes

        Args:
            output_dir: Directorio para guardar reportes
        """
        self.output_dir = output_dir

        import os
        os.makedirs(output_dir, exist_ok=True)

    def generate_text_report(
        self,
        stats: Dict,
        config: Dict,
        filename: str = "backtest_report.txt"
    ):
        """
        Genera reporte de texto

        Args:
            stats: Estadísticas del backtest
            config: Configuración utilizada
            filename: Nombre del archivo
        """
        filepath = f"{self.output_dir}/{filename}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE BACKTEST - Multi-TF Scalping Strategy\n")
            f.write("=" * 80 + "\n\n")

            # Información general
            f.write("CONFIGURACIÓN\n")
            f.write("-" * 80 + "\n")
            f.write(f"Símbolo: {config.get('symbol', 'N/A')}\n")
            f.write(f"Periodo: {config.get('start_date', 'N/A')} - {config.get('end_date', 'N/A')}\n")
            f.write(f"Balance Inicial: ${config.get('initial_balance', 0):,.2f}\n")
            f.write(f"Apalancamiento: 1:{config.get('leverage', 100)}\n")
            f.write(f"Spread: {config.get('spread_pips', 1)} pips\n")
            f.write(f"Comisión por Lote: ${config.get('commission_per_lot', 0):.2f}\n\n")

            # Estadísticas básicas
            f.write("ESTADÍSTICAS GENERALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total de Trades: {stats.get('total_trades', 0)}\n")
            f.write(f"Trades Ganadores: {stats.get('winning_trades', 0)}\n")
            f.write(f"Trades Perdedores: {stats.get('losing_trades', 0)}\n")
            f.write(f"Trades Break-even: {stats.get('breakeven_trades', 0)}\n")
            f.write(f"Win Rate: {stats.get('win_rate', 0):.2f}%\n\n")

            # Beneficios
            f.write("ANÁLISIS DE BENEFICIOS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Beneficio Neto: ${stats.get('net_profit', 0):,.2f}\n")
            f.write(f"Beneficio Bruto: ${stats.get('gross_profit', 0):,.2f}\n")
            f.write(f"Pérdida Bruta: ${stats.get('gross_loss', 0):,.2f}\n")
            f.write(f"Profit Factor: {stats.get('profit_factor', 0):.2f}\n")
            f.write(f"Expectativa por Trade: ${stats.get('expectancy', 0):.2f}\n")
            f.write(f"Ganancia Promedio: ${stats.get('avg_win', 0):.2f}\n")
            f.write(f"Pérdida Promedio: ${stats.get('avg_loss', 0):.2f}\n")
            f.write(f"Ratio Ganancia/Pérdida: {stats.get('avg_win_loss_ratio', 0):.2f}\n")
            f.write(f"Mayor Ganancia: ${stats.get('largest_win', 0):.2f}\n")
            f.write(f"Mayor Pérdida: ${stats.get('largest_loss', 0):.2f}\n\n")

            # Drawdown
            f.write("ANÁLISIS DE DRAWDOWN\n")
            f.write("-" * 80 + "\n")
            f.write(f"Max Drawdown: ${stats.get('max_drawdown', 0):,.2f}\n")
            f.write(f"Max Drawdown %: {stats.get('max_drawdown_percent', 0):.2f}%\n")
            f.write(f"Drawdown Promedio: ${stats.get('avg_drawdown', 0):,.2f}\n")
            f.write(f"Drawdown Promedio %: {stats.get('avg_drawdown_percent', 0):.2f}%\n")
            f.write(f"Recovery Factor: {stats.get('recovery_factor', 0):.2f}\n\n")

            # Métricas de riesgo
            f.write("MÉTRICAS DE RIESGO\n")
            f.write("-" * 80 + "\n")
            f.write(f"Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}\n")
            f.write(f"Sortino Ratio: {stats.get('sortino_ratio', 0):.2f}\n")
            f.write(f"Calmar Ratio: {stats.get('calmar_ratio', 0):.2f}\n\n")

            # Análisis temporal
            f.write("ANÁLISIS TEMPORAL\n")
            f.write("-" * 80 + "\n")
            f.write(f"Duración Promedio de Trade: {stats.get('avg_trade_duration', 0):.1f} min\n")
            f.write(f"Duración Promedio de Ganadores: {stats.get('avg_winning_duration', 0):.1f} min\n")
            f.write(f"Duración Promedio de Perdedores: {stats.get('avg_losing_duration', 0):.1f} min\n\n")

            # Balance final
            f.write("RESUMEN FINAL\n")
            f.write("-" * 80 + "\n")
            f.write(f"Balance Inicial: ${config.get('initial_balance', 0):,.2f}\n")
            final_balance = config.get('initial_balance', 0) + stats.get('net_profit', 0)
            f.write(f"Balance Final: ${final_balance:,.2f}\n")
            roi = (stats.get('net_profit', 0) / config.get('initial_balance', 1)) * 100
            f.write(f"ROI: {roi:.2f}%\n\n")

            f.write("=" * 80 + "\n")
            f.write(f"Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")

        print(f"Reporte de texto guardado en: {filepath}")

    def generate_trades_csv(
        self,
        trades: List[Trade],
        filename: str = "trades.csv"
    ):
        """
        Genera CSV con todos los trades

        Args:
            trades: Lista de trades
            filename: Nombre del archivo
        """
        if not trades:
            print("No hay trades para exportar")
            return

        filepath = f"{self.output_dir}/{filename}"

        # Convertir trades a DataFrame
        data = [t.to_dict() for t in trades]
        df = pd.DataFrame(data)

        # Guardar CSV
        df.to_csv(filepath, index=False)

        print(f"Trades exportados a: {filepath}")

    def generate_equity_csv(
        self,
        equity_curve: List[dict],
        filename: str = "equity_curve.csv"
    ):
        """
        Genera CSV con curva de equity

        Args:
            equity_curve: Histórico de equity
            filename: Nombre del archivo
        """
        if not equity_curve:
            print("No hay datos de equity para exportar")
            return

        filepath = f"{self.output_dir}/{filename}"

        # Convertir a DataFrame
        df = pd.DataFrame(equity_curve)

        # Guardar CSV
        df.to_csv(filepath, index=False)

        print(f"Equity curve exportada a: {filepath}")

    def generate_json_report(
        self,
        stats: Dict,
        config: Dict,
        trades: List[Trade],
        filename: str = "backtest_report.json"
    ):
        """
        Genera reporte en formato JSON

        Args:
            stats: Estadísticas
            config: Configuración
            trades: Lista de trades
            filename: Nombre del archivo
        """
        filepath = f"{self.output_dir}/{filename}"

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "strategy": "Multi-TF Scalping Strategy"
            },
            "config": config,
            "statistics": stats,
            "trades_summary": {
                "total": len(trades),
                "first_trade": trades[0].to_dict() if trades else None,
                "last_trade": trades[-1].to_dict() if trades else None,
            }
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Reporte JSON guardado en: {filepath}")

    def generate_html_report(
        self,
        stats: Dict,
        config: Dict,
        filename: str = "backtest_report.html"
    ):
        """
        Genera reporte HTML

        Args:
            stats: Estadísticas
            config: Configuración
            filename: Nombre del archivo
        """
        filepath = f"{self.output_dir}/{filename}"

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Backtest</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card.positive {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.negative {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Reporte de Backtest</h1>
        <p><strong>Estrategia:</strong> Multi-TF Scalping Strategy</p>
        <p><strong>Símbolo:</strong> {config.get('symbol', 'N/A')}</p>
        <p><strong>Periodo:</strong> {config.get('start_date', 'N/A')} - {config.get('end_date', 'N/A')}</p>

        <h2>Resultados Principales</h2>
        <div class="stat-grid">
            <div class="stat-card {'positive' if stats.get('net_profit', 0) > 0 else 'negative'}">
                <div class="stat-label">Beneficio Neto</div>
                <div class="stat-value">${stats.get('net_profit', 0):,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{stats.get('win_rate', 0):.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Profit Factor</div>
                <div class="stat-value">{stats.get('profit_factor', 0):.2f}</div>
            </div>
            <div class="stat-card negative">
                <div class="stat-label">Max Drawdown</div>
                <div class="stat-value">{stats.get('max_drawdown_percent', 0):.2f}%</div>
            </div>
        </div>

        <h2>Estadísticas Detalladas</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Total de Trades</td>
                <td>{stats.get('total_trades', 0)}</td>
            </tr>
            <tr>
                <td>Trades Ganadores</td>
                <td>{stats.get('winning_trades', 0)}</td>
            </tr>
            <tr>
                <td>Trades Perdedores</td>
                <td>{stats.get('losing_trades', 0)}</td>
            </tr>
            <tr>
                <td>Beneficio Bruto</td>
                <td>${stats.get('gross_profit', 0):,.2f}</td>
            </tr>
            <tr>
                <td>Pérdida Bruta</td>
                <td>${stats.get('gross_loss', 0):,.2f}</td>
            </tr>
            <tr>
                <td>Expectativa por Trade</td>
                <td>${stats.get('expectancy', 0):.2f}</td>
            </tr>
            <tr>
                <td>Sharpe Ratio</td>
                <td>{stats.get('sharpe_ratio', 0):.2f}</td>
            </tr>
            <tr>
                <td>Sortino Ratio</td>
                <td>{stats.get('sortino_ratio', 0):.2f}</td>
            </tr>
        </table>

        <div class="footer">
            <p>Reporte generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Reporte HTML guardado en: {filepath}")

    def generate_all_reports(
        self,
        stats: Dict,
        config: Dict,
        trades: List[Trade],
        equity_curve: List[dict]
    ):
        """
        Genera todos los reportes

        Args:
            stats: Estadísticas
            config: Configuración
            trades: Lista de trades
            equity_curve: Histórico de equity
        """
        print("\nGenerando reportes...")

        self.generate_text_report(stats, config)
        self.generate_json_report(stats, config, trades)
        self.generate_html_report(stats, config)
        self.generate_trades_csv(trades)
        self.generate_equity_csv(equity_curve)

        print(f"\nTodos los reportes guardados en: {self.output_dir}")
