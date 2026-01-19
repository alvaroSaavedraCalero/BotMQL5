# Sistema de Backtesting - Multi-TF Scalping Strategy

Sistema completo de backtesting en Python que replica la estrategia de trading implementada en MetaTrader 5.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Configuración](#configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Ejemplos](#ejemplos)
- [Resultados y Reportes](#resultados-y-reportes)
- [Optimización](#optimización)
- [Solución de Problemas](#solución-de-problemas)

## ✨ Características

### Motor de Backtesting
- ✅ Simulación tick-by-tick con datos M1, M5 y M15
- ✅ Réplica exacta de la estrategia MT5
- ✅ Gestión completa de posiciones (SL, TP parcial, TP final)
- ✅ Gestión de riesgo avanzada
- ✅ Control de drawdown y límites diarios
- ✅ Simulación de spread y comisiones
- ✅ Horarios de sesión (Londres y NY)

### Análisis y Reportes
- 📊 Curva de equity en tiempo real
- 📈 Análisis de drawdown
- 📉 Distribución de trades
- 💰 Métricas detalladas (Sharpe, Sortino, Calmar)
- 📅 Retornos mensuales
- 📄 Reportes en múltiples formatos (TXT, CSV, JSON, HTML)

### Fuentes de Datos
- 🌐 Yahoo Finance (gratis, fácil)
- 💾 Archivos CSV personalizados
- 🔌 MetaTrader 5 directo (requiere instalación)

## 🚀 Instalación

### 1. Instalar dependencias

```bash
cd Python
pip install -r backtest_requirements.txt
```

### 2. Verificar instalación

```bash
python -c "import pandas, numpy, yfinance, matplotlib; print('✅ Todas las dependencias instaladas')"
```

## 📖 Uso Rápido

### Ejemplo Básico

```bash
# Backtest de EURUSD con configuración por defecto (últimos 3 meses)
python run_backtest.py
```

### Con Parámetros Personalizados

```bash
# Backtest de GBPUSD para todo 2023
python run_backtest.py --symbol GBPUSD --start 2023-01-01 --end 2023-12-31 --balance 5000 --risk 2.0
```

### Parámetros Disponibles

```bash
python run_backtest.py --help

Opciones:
  --symbol SYMBOL           Símbolo (EURUSD, GBPUSD, etc.) [default: EURUSD]
  --start YYYY-MM-DD        Fecha inicial [default: hace 3 meses]
  --end YYYY-MM-DD          Fecha final [default: hoy]
  --balance FLOAT           Balance inicial [default: 10000]
  --leverage INT            Apalancamiento [default: 100]
  --commission FLOAT        Comisión por lote [default: 0.0]
  --spread FLOAT            Spread en pips [default: 1.0]
  --risk FLOAT              Riesgo por trade (%) [default: 1.0]
  --source {yfinance,csv,mt5} Fuente de datos [default: yfinance]
  --output-dir PATH         Directorio de salida [default: ./backtest_results]
  --no-plots                No generar gráficos
  --cache-dir PATH          Directorio de cache [default: ./data/cache]
```

## ⚙️ Configuración

### Configuración de la Estrategia

Puedes personalizar la estrategia editando los parámetros en `run_backtest.py` o creando tu propio script:

```python
from backtest.backtester import Backtester
from backtest.data_loader import DataLoader

# Crear backtester con parámetros personalizados
backtester = Backtester(
    symbol="EURUSD",
    initial_balance=10000.0,
    leverage=100,
    commission_per_lot=0.0,
    spread_pips=1.0,
    risk_per_trade=1.0,          # Riesgo por trade
    max_drawdown_percent=10.0,    # Máximo drawdown
    max_daily_drawdown_percent=5.0,
    max_daily_trades=10,
    stop_loss_pips=12.0,          # Stop Loss
    rr_partial=2.0,               # R:R para TP parcial
    rr_final=3.0,                 # R:R para TP final
    partial_close_percent=50.0,
    # Sesiones de trading (UTC)
    london_start=8,
    london_end=12,
    ny_start=13,
    ny_end=17,
    # Parámetros de indicadores
    ema_fast=9,
    ema_slow=21,
    rsi_period=14,
    stoch_k=5,
    stoch_d=3,
    stoch_slowing=3,
    atr_period=14,
    min_atr=0.0003,
)
```

### Usando Datos Propios

#### Desde CSV

1. Crea archivos CSV con el formato:
```csv
time,open,high,low,close,volume
2023-01-01 00:00:00,1.0500,1.0510,1.0495,1.0505,100
```

2. Guárdalos en `./data/cache/` con nombre: `EURUSD_1min.csv`, `EURUSD_5min.csv`, etc.

3. Ejecuta con `--source csv`

#### Desde MetaTrader 5

```bash
# Requiere MetaTrader5 instalado y pip install MetaTrader5
python run_backtest.py --symbol EURUSD --source mt5
```

## 📁 Estructura del Proyecto

```
Python/
├── backtest/
│   ├── __init__.py              # Módulo principal
│   ├── backtester.py            # Motor de simulación
│   ├── trade.py                 # Gestión de trades
│   ├── portfolio.py             # Gestión de cuenta
│   ├── signal_engine_bt.py      # Motor de señales
│   ├── data_loader.py           # Descarga de datos
│   ├── statistics.py            # Cálculo de métricas
│   ├── visualizer.py            # Gráficos
│   └── report.py                # Generación de reportes
│
├── run_backtest.py              # Script principal
├── backtest_requirements.txt    # Dependencias
└── data/
    └── cache/                   # Cache de datos
```

## 💡 Ejemplos

### Ejemplo 1: Backtest Simple

```python
from datetime import datetime, timedelta
from backtest.data_loader import DataLoader
from backtest.backtester import Backtester

# Configurar fechas
end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # 2 meses

# Cargar datos
loader = DataLoader()
data_m1 = loader.load_data("EURUSD=X", start_date, end_date, "1min")
data_m5 = loader.load_data("EURUSD=X", start_date, end_date, "5min")
data_m15 = loader.load_data("EURUSD=X", start_date, end_date, "15min")

# Ejecutar backtest
backtester = Backtester(
    symbol="EURUSD",
    initial_balance=10000.0,
    risk_per_trade=1.0
)

results = backtester.run(data_m1, data_m5, data_m15)

# Generar reportes
backtester.generate_reports(results)
```

### Ejemplo 2: Comparar Múltiples Símbolos

```python
symbols = ["EURUSD", "GBPUSD", "USDJPY"]
results_comparison = {}

for symbol in symbols:
    yf_symbol = f"{symbol}=X"

    # Cargar datos
    data_m1 = loader.load_data(yf_symbol, start_date, end_date, "1min")
    data_m5 = loader.load_data(yf_symbol, start_date, end_date, "5min")
    data_m15 = loader.load_data(yf_symbol, start_date, end_date, "15min")

    # Backtest
    backtester = Backtester(symbol=symbol, initial_balance=10000.0)
    results = backtester.run(data_m1, data_m5, data_m15, verbose=False)

    results_comparison[symbol] = results["statistics"]

# Comparar resultados
for symbol, stats in results_comparison.items():
    print(f"\n{symbol}:")
    print(f"  Net Profit: ${stats['net_profit']:.2f}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Profit Factor: {stats['profit_factor']:.2f}")
```

### Ejemplo 3: Optimización de Parámetros

```python
import itertools

# Parámetros a testear
stop_losses = [10, 12, 15]
risk_levels = [0.5, 1.0, 1.5]
rr_partials = [1.5, 2.0, 2.5]

best_result = None
best_profit = float('-inf')

# Cargar datos una vez
data_m1 = loader.load_data("EURUSD=X", start_date, end_date, "1min")
data_m5 = loader.load_data("EURUSD=X", start_date, end_date, "5min")
data_m15 = loader.load_data("EURUSD=X", start_date, end_date, "15min")

# Probar combinaciones
for sl, risk, rr in itertools.product(stop_losses, risk_levels, rr_partials):
    backtester = Backtester(
        symbol="EURUSD",
        initial_balance=10000.0,
        stop_loss_pips=sl,
        risk_per_trade=risk,
        rr_partial=rr,
    )

    results = backtester.run(data_m1, data_m5, data_m15, verbose=False)
    profit = results["statistics"]["net_profit"]

    if profit > best_profit:
        best_profit = profit
        best_result = {
            "sl": sl,
            "risk": risk,
            "rr_partial": rr,
            "profit": profit
        }

print(f"\nMejor combinación:")
print(f"  SL: {best_result['sl']} pips")
print(f"  Risk: {best_result['risk']}%")
print(f"  R:R Partial: {best_result['rr_partial']}")
print(f"  Profit: ${best_result['profit']:.2f}")
```

## 📊 Resultados y Reportes

Después de ejecutar el backtest, se generan automáticamente:

### Archivos de Reporte

```
backtest_results/
├── backtest_report.txt          # Reporte detallado en texto
├── backtest_report.json         # Datos en JSON
├── backtest_report.html         # Reporte visual HTML
├── trades.csv                   # Lista de todos los trades
├── equity_curve.csv             # Histórico de equity
├── equity_curve.png             # Gráfico de equity
├── drawdown.png                 # Gráfico de drawdown
├── trade_distribution.png       # Distribución de resultados
└── monthly_returns.png          # Retornos mensuales
```

### Métricas Incluidas

**Básicas:**
- Total de trades
- Win rate
- Profit factor
- Expectancy
- Net profit

**Drawdown:**
- Max drawdown ($)
- Max drawdown (%)
- Average drawdown
- Recovery factor

**Riesgo:**
- Sharpe ratio
- Sortino ratio
- Calmar ratio

**Temporales:**
- Duración promedio de trades
- Retornos mensuales
- Rachas de victorias/derrotas

## 🎯 Optimización

### Walk-Forward Analysis

```python
from datetime import timedelta

# Dividir datos en períodos
total_days = (end_date - start_date).days
train_days = int(total_days * 0.7)  # 70% entrenamiento
test_days = total_days - train_days  # 30% test

train_end = start_date + timedelta(days=train_days)

# Fase 1: Optimizar en período de entrenamiento
# ... ejecutar optimización ...

# Fase 2: Validar en período de test
results_test = backtester.run(
    data_m1, data_m5, data_m15,
    start_date=train_end,
    end_date=end_date
)
```

### Monte Carlo Simulation

```python
import random

# Ejecutar múltiples simulaciones reordenando trades
original_results = backtester.run(data_m1, data_m5, data_m15)
original_trades = original_results["trades"]

mc_results = []
for i in range(1000):
    # Reordenar trades aleatoriamente
    shuffled_trades = random.sample(original_trades, len(original_trades))

    # Calcular equity con nuevo orden
    equity = initial_balance
    for trade in shuffled_trades:
        equity += trade.profit

    mc_results.append(equity)

# Analizar distribución
import numpy as np
print(f"Equity promedio: ${np.mean(mc_results):.2f}")
print(f"Peor caso (5%): ${np.percentile(mc_results, 5):.2f}")
print(f"Mejor caso (95%): ${np.percentile(mc_results, 95):.2f}")
```

## 🔧 Solución de Problemas

### Error: "No se encontraron datos"

**Problema:** Yahoo Finance no tiene datos para el período solicitado.

**Soluciones:**
1. Reduce el período (Yahoo Finance limita datos intraday a ~30-60 días)
2. Usa datos de MT5: `--source mt5`
3. Usa datos guardados: `--source csv`

### Error: "ImportError: No module named X"

**Solución:**
```bash
pip install -r backtest_requirements.txt
```

### Los gráficos no se muestran

**Solución:**
```bash
# Instalar backend de matplotlib
pip install PyQt5
# O ejecutar sin gráficos
python run_backtest.py --no-plots
```

### Backtest muy lento

**Soluciones:**
1. Reduce el período de análisis
2. Usa datos de menor frecuencia para pruebas rápidas
3. Desactiva verbose: `verbose=False`

### Resultados no realistas

**Verificar:**
1. Spread configurado correctamente
2. Comisiones incluidas
3. Slippage considerado
4. Horarios de sesión apropiados

## 📚 Referencias

### Estrategia
- La estrategia replica exactamente la lógica en `MQL5/Experts/MultiTF_Scalper.mq5`
- Documentación técnica en `CLAUDE.MD`

### Indicadores
- EMA: Exponential Moving Average
- RSI: Relative Strength Index
- Stochastic: Stochastic Oscillator
- ATR: Average True Range
- VWAP: Volume Weighted Average Price

### Métricas
- **Sharpe Ratio:** (Return - RiskFreeRate) / StdDev
- **Sortino Ratio:** (Return - RiskFreeRate) / DownsideStdDev
- **Calmar Ratio:** AnnualReturn / MaxDrawdown
- **Profit Factor:** GrossProfit / GrossLoss
- **Expectancy:** AvgWin * WinRate - AvgLoss * LossRate

## 🤝 Contribuciones

Para mejorar el backtester:

1. Añade nuevas fuentes de datos
2. Implementa más indicadores
3. Mejora la velocidad de simulación
4. Añade más métricas de análisis

## 📄 Licencia

Parte del proyecto BotMQL5 - Multi-TF Scalping Strategy

---

**Autor:** Implementado por Claude
**Fecha:** 2026-01-19
**Versión:** 1.0.0
