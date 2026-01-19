#!/usr/bin/env python3
"""
Ejemplo Simple de Backtest
===========================

Ejemplo básico de cómo usar el sistema de backtesting.
"""

from datetime import datetime, timedelta
import sys
import os

# Añadir path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest.data_loader import DataLoader
from backtest.backtester import Backtester


def ejemplo_basico():
    """Ejemplo más simple posible"""
    print("\n" + "="*70)
    print("EJEMPLO BÁSICO DE BACKTEST")
    print("="*70 + "\n")

    # 1. Configurar período (últimos 30 días)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"Símbolo: EURUSD")
    print(f"Balance Inicial: $10,000\n")

    # 2. Cargar datos
    print("Cargando datos históricos...")
    loader = DataLoader()

    try:
        data_m1 = loader.load_data("EURUSD=X", start_date, end_date, "1min")
        data_m5 = loader.load_data("EURUSD=X", start_date, end_date, "5min")
        data_m15 = loader.load_data("EURUSD=X", start_date, end_date, "15min")
    except Exception as e:
        print(f"\n❌ Error al cargar datos: {e}")
        print("\nConsejo: Intenta con un período más corto (7-14 días)")
        return

    print(f"  ✓ M1:  {len(data_m1)} barras")
    print(f"  ✓ M5:  {len(data_m5)} barras")
    print(f"  ✓ M15: {len(data_m15)} barras")

    if len(data_m1) == 0:
        print("\n❌ No se encontraron datos suficientes")
        print("Intenta con un período más reciente")
        return

    # 3. Crear backtester
    print("\nCreando backtester con configuración por defecto...")
    backtester = Backtester(
        symbol="EURUSD",
        initial_balance=10000.0,
        risk_per_trade=1.0,
        stop_loss_pips=12.0,
        spread_pips=1.0
    )

    # 4. Ejecutar backtest
    print("\nEjecutando backtest...\n")
    results = backtester.run(data_m1, data_m5, data_m15)

    # 5. Mostrar resultados resumidos
    stats = results["statistics"]
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    print(f"\n💰 BENEFICIOS:")
    print(f"   Balance Inicial:  ${10000:,.2f}")
    print(f"   Balance Final:    ${stats['final_balance']:,.2f}")
    print(f"   Beneficio Neto:   ${stats['net_profit']:,.2f}")
    print(f"   ROI:              {(stats['net_profit']/10000*100):.2f}%")

    print(f"\n📊 TRADES:")
    print(f"   Total:            {stats['total_trades']}")
    print(f"   Ganadores:        {stats['winning_trades']}")
    print(f"   Perdedores:       {stats['losing_trades']}")
    print(f"   Win Rate:         {stats['win_rate']:.1f}%")

    print(f"\n📈 MÉTRICAS:")
    print(f"   Profit Factor:    {stats['profit_factor']:.2f}")
    print(f"   Expectancy:       ${stats['expectancy']:.2f}")
    print(f"   Max Drawdown:     {stats['max_drawdown_percent']:.2f}%")

    print("\n" + "="*70 + "\n")

    # 6. Generar reportes
    print("¿Generar reportes completos y gráficos? (s/n): ", end="")
    try:
        respuesta = input().strip().lower()
        if respuesta == 's':
            print("\nGenerando reportes...")
            backtester.generate_reports(results, "./backtest_results")
            print("\n✅ Reportes guardados en: ./backtest_results")
    except:
        print("\nSaltando generación de reportes")

    print("\n✅ Ejemplo completado!\n")


def ejemplo_comparacion():
    """Ejemplo de comparación entre símbolos"""
    print("\n" + "="*70)
    print("EJEMPLO: COMPARACIÓN DE SÍMBOLOS")
    print("="*70 + "\n")

    symbols = [
        ("EURUSD", "EURUSD=X"),
        ("GBPUSD", "GBPUSD=X"),
        ("USDJPY", "USDJPY=X"),
    ]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=21)  # 3 semanas

    loader = DataLoader()
    results_comparison = {}

    for symbol, yf_symbol in symbols:
        print(f"\nProcesando {symbol}...")

        try:
            # Cargar datos
            data_m1 = loader.load_data(yf_symbol, start_date, end_date, "1min")
            data_m5 = loader.load_data(yf_symbol, start_date, end_date, "5min")
            data_m15 = loader.load_data(yf_symbol, start_date, end_date, "15min")

            if len(data_m1) == 0:
                print(f"  ❌ Sin datos suficientes")
                continue

            # Backtest
            backtester = Backtester(
                symbol=symbol,
                initial_balance=10000.0,
                risk_per_trade=1.0
            )

            results = backtester.run(
                data_m1, data_m5, data_m15,
                verbose=False
            )

            results_comparison[symbol] = results["statistics"]
            print(f"  ✓ Completado: {results['statistics']['total_trades']} trades")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Mostrar comparación
    if results_comparison:
        print("\n" + "="*70)
        print("COMPARACIÓN DE RESULTADOS")
        print("="*70 + "\n")

        print(f"{'Símbolo':<10} {'Trades':<8} {'Win Rate':<10} {'Profit':<12} {'PF':<8} {'DD%':<8}")
        print("-" * 70)

        for symbol, stats in results_comparison.items():
            print(
                f"{symbol:<10} "
                f"{stats['total_trades']:<8} "
                f"{stats['win_rate']:<10.1f}% "
                f"${stats['net_profit']:<11.2f} "
                f"{stats['profit_factor']:<8.2f} "
                f"{stats['max_drawdown_percent']:<8.2f}%"
            )

        print("\n" + "="*70 + "\n")


def menu_principal():
    """Menú principal de ejemplos"""
    print("\n" + "="*70)
    print("SISTEMA DE BACKTESTING - EJEMPLOS")
    print("="*70 + "\n")

    print("Ejemplos disponibles:")
    print("  1. Backtest Básico (EURUSD, 30 días)")
    print("  2. Comparación de Símbolos (EURUSD, GBPUSD, USDJPY)")
    print("  0. Salir")

    print("\nSelecciona una opción: ", end="")

    try:
        opcion = input().strip()

        if opcion == "1":
            ejemplo_basico()
        elif opcion == "2":
            ejemplo_comparacion()
        elif opcion == "0":
            print("\n¡Hasta luego!\n")
            return
        else:
            print("\n❌ Opción no válida")

    except KeyboardInterrupt:
        print("\n\n¡Hasta luego!\n")


if __name__ == "__main__":
    try:
        menu_principal()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
