#!/usr/bin/env python3
"""
Script Principal de Backtesting
================================

Ejecuta el backtest de la estrategia Multi-TF Scalping.

Uso:
    python run_backtest.py
    python run_backtest.py --symbol EURUSD --start 2023-01-01 --end 2023-12-31
"""

import argparse
from datetime import datetime, timedelta
import sys
import os

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest.data_loader import DataLoader
from backtest.backtester import Backtester


def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Backtest de Multi-TF Scalping Strategy"
    )

    # Configuración básica
    parser.add_argument(
        "--symbol",
        type=str,
        default="EURUSD",
        help="Símbolo a testear (default: EURUSD)"
    )

    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Fecha inicial (YYYY-MM-DD). Default: últimos 3 meses"
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Fecha final (YYYY-MM-DD). Default: hoy"
    )

    parser.add_argument(
        "--balance",
        type=float,
        default=10000.0,
        help="Balance inicial (default: 10000)"
    )

    parser.add_argument(
        "--leverage",
        type=int,
        default=100,
        help="Apalancamiento (default: 100)"
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.0,
        help="Comisión por lote (default: 0.0)"
    )

    parser.add_argument(
        "--spread",
        type=float,
        default=1.0,
        help="Spread en pips (default: 1.0)"
    )

    parser.add_argument(
        "--risk",
        type=float,
        default=1.0,
        help="Riesgo por trade en % (default: 1.0)"
    )

    parser.add_argument(
        "--source",
        type=str,
        default="yfinance",
        choices=["yfinance", "csv", "mt5"],
        help="Fuente de datos (default: yfinance)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./backtest_results",
        help="Directorio de salida (default: ./backtest_results)"
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="No generar gráficos"
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        default="./data/cache",
        help="Directorio de cache (default: ./data/cache)"
    )

    return parser.parse_args()


def main():
    """Función principal"""
    args = parse_arguments()

    print("\n" + "="*70)
    print("BACKTEST - Multi-TF Scalping Strategy")
    print("="*70 + "\n")

    # Configurar fechas
    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end_date = datetime.now()

    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start_date = end_date - timedelta(days=90)  # 3 meses por default

    print(f"Símbolo: {args.symbol}")
    print(f"Periodo: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    print(f"Balance Inicial: ${args.balance:,.2f}")
    print(f"Fuente de datos: {args.source}")
    print()

    # Mapear símbolo a formato Yahoo Finance
    symbol_map = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "USDCHF": "USDCHF=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "NZDUSD": "NZDUSD=X",
        "EURGBP": "EURGBP=X",
    }

    yf_symbol = symbol_map.get(args.symbol, args.symbol)

    # Cargar datos
    try:
        loader = DataLoader(cache_dir=args.cache_dir)

        print("Descargando datos históricos...")
        print(f"  - Cargando M1...")
        data_m1 = loader.load_data(
            yf_symbol, start_date, end_date, "1min", args.source
        )

        print(f"  - Cargando M5...")
        data_m5 = loader.load_data(
            yf_symbol, start_date, end_date, "5min", args.source
        )

        print(f"  - Cargando M15...")
        data_m15 = loader.load_data(
            yf_symbol, start_date, end_date, "15min", args.source
        )

        print(f"\nDatos cargados:")
        print(f"  M1:  {len(data_m1)} barras")
        print(f"  M5:  {len(data_m5)} barras")
        print(f"  M15: {len(data_m15)} barras")

        if len(data_m1) == 0:
            print("\n❌ Error: No se encontraron datos para el periodo especificado")
            print("\nConsejo:")
            print("  - Para datos recientes, usa periodos más cortos (1-2 meses)")
            print("  - Yahoo Finance tiene límites de descarga para datos intraday")
            print("  - Considera usar --source mt5 si tienes MetaTrader 5 instalado")
            return 1

    except Exception as e:
        print(f"\n❌ Error al cargar datos: {e}")
        return 1

    # Crear backtester
    print("\nInicializando backtester...")
    backtester = Backtester(
        symbol=args.symbol,
        initial_balance=args.balance,
        leverage=args.leverage,
        commission_per_lot=args.commission,
        spread_pips=args.spread,
        risk_per_trade=args.risk,
    )

    # Ejecutar backtest
    try:
        results = backtester.run(
            data_m1=data_m1,
            data_m5=data_m5,
            data_m15=data_m15,
            start_date=start_date,
            end_date=end_date,
            verbose=True
        )
    except Exception as e:
        print(f"\n❌ Error durante el backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Generar reportes y gráficos
    if not args.no_plots:
        try:
            backtester.generate_reports(results, args.output_dir)
        except Exception as e:
            print(f"\n⚠️  Error al generar reportes: {e}")
            print("Los resultados están disponibles pero no se pudieron generar los gráficos")

    print("\n✅ Backtest completado exitosamente!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
