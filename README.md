# Multi-TF Scalping Bot for MetaTrader 5

Sistema de trading automatizado dual (MQL5 + Python) para scalping en Forex, con gestión avanzada de riesgo, dashboard en tiempo real y comunicación bidireccional entre componentes.

## 🎯 Estrategia: Multi-TF Momentum Scalper

### Concepto
Estrategia basada en confluencia de múltiples timeframes usando momentum y estructura de mercado. Opera en M1 con confirmaciones de M5 y M15.

### Indicadores Técnicos

| Indicador | Timeframe | Propósito |
|-----------|-----------|-----------|
| EMA 9 y EMA 21 | M15 | Tendencia principal |
| EMA 9 y EMA 21 | M5 | Tendencia intermedia |
| RSI (14) | M5 | Filtro de sobrecompra/sobreventa |
| VWAP | M5 | Nivel dinámico de soporte/resistencia |
| Stochastic (5,3,3) | M1 | Timing de entrada |
| ATR (14) | M1 | Validación de volatilidad mínima |

### Reglas de Entrada

**COMPRA (Long):**
1. M15: EMA 9 > EMA 21 (tendencia alcista)
2. M5: EMA 9 > EMA 21 + Precio > VWAP + RSI entre 40-70
3. M1: Stochastic cruza hacia arriba desde zona < 20

**VENTA (Short):**
1. M15: EMA 9 < EMA 21 (tendencia bajista)
2. M5: EMA 9 < EMA 21 + Precio < VWAP + RSI entre 30-60
3. M1: Stochastic cruza hacia abajo desde zona > 80

### Gestión de Operaciones
- **Stop Loss**: 10-15 pips (configurable)
- **Take Profit 1**: Ratio 1:2 → Cierre 50% de la posición + Break-even
- **Take Profit 2**: Ratio 1:3 → Cierre del 50% restante

## 📁 Estructura del Proyecto

```
BotMQL5/
├── MQL5/
│   ├── Experts/
│   │   └── MultiTF_Scalper.mq5      # EA Principal
│   ├── Include/
│   │   ├── Constants.mqh             # Constantes globales
│   │   ├── RiskManager.mqh           # Gestión de riesgo
│   │   ├── SessionManager.mqh        # Control de sesiones
│   │   ├── TradeManager.mqh          # Gestión de operaciones
│   │   ├── SignalEngine.mqh          # Motor de señales
│   │   └── SocketClient.mqh          # Comunicación con Python
│   └── Libraries/
│       └── JsonParser.mqh            # Parser JSON
│
├── Python/
│   ├── main.py                       # Entry point
│   ├── config.py                     # Configuración
│   ├── requirements.txt              # Dependencias
│   ├── core/                         # Módulos principales
│   ├── communication/                # Comunicación MT5
│   ├── dashboard/                    # Dashboard web
│   ├── data/                         # Base de datos
│   ├── utils/                        # Utilidades
│   ├── backtest/                     # Sistema de backtesting
│   │   ├── backtester.py             # Motor de simulación
│   │   ├── signal_engine_bt.py       # Motor de señales
│   │   ├── portfolio.py              # Gestión de cuenta
│   │   ├── trade.py                  # Gestión de trades
│   │   ├── data_loader.py            # Carga de datos históricos
│   │   ├── statistics.py             # Cálculo de métricas
│   │   ├── visualizer.py             # Generación de gráficos
│   │   └── report.py                 # Generación de reportes
│   ├── run_backtest.py               # Script principal de backtest
│   ├── example_backtest.py           # Ejemplos de uso
│   └── backtest_requirements.txt     # Dependencias backtest
│
├── .gitignore
├── README.md
└── BACKTEST_README.md                # Documentación del backtesting
```

## 🚀 Instalación

### Requisitos Previos
- MetaTrader 5 instalado
- Python 3.9+
- pip (gestor de paquetes Python)

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/yourusername/BotMQL5.git
cd BotMQL5
```

### Paso 2: Instalar dependencias de Python

#### Para el sistema completo (Dashboard + Trading)
```bash
cd Python
pip install -r requirements.txt
```

#### Para backtesting (opcional pero recomendado)
```bash
pip install -r backtest_requirements.txt
```

### Paso 3: Instalar EA en MetaTrader 5
1. Copiar la carpeta `MQL5` al directorio de datos de MT5:
   - Windows: `%APPDATA%\MetaQuotes\Terminal\[ID]\MQL5\`
2. En MetaEditor, abrir `MultiTF_Scalper.mq5` y compilar (F7)
3. Reiniciar MetaTrader 5

### Paso 4: Configurar el EA
1. Arrastrar el EA al gráfico deseado (cualquier timeframe)
2. Configurar los parámetros según necesidades
3. Habilitar "Permitir trading algorítmico"

## ⚙️ Configuración

### Parámetros del EA (MQL5)

| Parámetro | Defecto | Descripción |
|-----------|---------|-------------|
| MaxDrawDown | 10% | Drawdown máximo de la cuenta |
| MaxDailyDrawDown | 5% | Drawdown máximo diario |
| MaxDailyOperations | 10 | Operaciones máximas por día |
| RiskPerTrade | 1% | Riesgo por operación |
| StopLossPips | 12 | Stop Loss en pips |
| RR_Partial | 2.0 | R:R para cierre parcial |
| RR_Final | 3.0 | R:R para cierre total |
| PartialClosePercent | 50% | Porcentaje de cierre parcial |

### Sesiones de Trading
- **Londres**: 08:00 - 12:00 (hora servidor)
- **Nueva York**: 13:00 - 17:00 (hora servidor)

### Filtro de Noticias
- Buffer de 45 minutos antes/después de noticias de alto impacto
- Consulta automática del calendario económico

## 📊 Dashboard

El dashboard web proporciona monitoreo en tiempo real:

### Iniciar Dashboard
```bash
cd Python
python main.py
```

Acceder en: `http://localhost:8050`

### Características del Dashboard
- 📈 Curva de equity en tiempo real
- 💰 Balance, equity y P/L flotante
- 📉 Métricas de drawdown
- 📋 Tabla de posiciones abiertas
- 📊 Estadísticas de trading (win rate, profit factor, etc.)
- 📰 Estado del filtro de noticias
- 🎛️ Panel de control (pausar, reanudar, cerrar todo)

## 🔗 Comunicación MT5-Python

El sistema usa archivos compartidos para la comunicación:

```
%APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\
├── mt5_status.json        # Estado del bot → Python
├── python_signals.json    # Señales Python → MT5
├── python_to_mt5.json     # Comandos → MT5
├── mt5_to_python.json     # Trades → Python
└── heartbeat.json         # Latido de conexión
```

### Comandos Disponibles
- `PAUSE`: Pausar el bot
- `RESUME`: Reanudar el bot
- `CLOSE_ALL`: Cerrar todas las posiciones
- `STATUS`: Solicitar actualización de estado
- `NEWS_BLOCK:1/0`: Activar/desactivar bloqueo por noticias

## 📈 Uso

### 🔬 Paso 0: Backtest (RECOMENDADO)

Antes de usar en cuenta real o demo, ejecuta backtests para validar la estrategia:

```bash
cd Python
python run_backtest.py --symbol EURUSD --start 2023-01-01 --end 2023-12-31
```

Ver sección [Sistema de Backtesting](#-sistema-de-backtesting-en-python) para más detalles.

### Modo Completo (EA + Dashboard)
1. Iniciar MetaTrader 5 con el EA adjunto al gráfico
2. Ejecutar `python main.py` en la carpeta Python
3. Abrir el dashboard en el navegador

### Solo EA (sin Python)
El EA puede funcionar de forma independiente sin Python, pero sin:
- Dashboard de monitoreo
- Señales adicionales de Python
- Filtro automático de noticias

### Solo Dashboard (monitoreo)
```bash
python main.py --no-signals
```

### Solo Backtesting (análisis histórico)
```bash
python run_backtest.py
# o ejecuta ejemplos interactivos
python example_backtest.py
```

## ⚠️ Advertencias

- **Backtesting Obligatorio**: Realiza backtesting extensivo con el sistema Python incluido antes de usar en real
- **Cuenta Demo**: Prueba siempre en cuenta demo durante al menos 1-2 meses
- **Validación**: Compara resultados del backtest con resultados reales en demo
- **Riesgo**: El trading conlleva riesgo de pérdida de capital
- **Supervisión**: Monitorea el bot regularmente, especialmente durante noticias
- **Optimización**: No confíes en una sola optimización, usa walk-forward analysis
- **Datos Históricos**: El rendimiento pasado no garantiza resultados futuros

## 🧪 Testing

### Backtest en MT5
1. Abrir Strategy Tester (Ctrl+R)
2. Seleccionar `MultiTF_Scalper`
3. Configurar símbolo y periodo
4. Ejecutar backtest

### Tests de Python
```bash
cd Python
pytest tests/
```

## 🔬 Sistema de Backtesting en Python

El proyecto incluye un **sistema completo de backtesting** que replica la estrategia MT5 para análisis histórico exhaustivo.

### ✨ Características del Backtester

- ✅ **Simulación tick-by-tick** con datos M1, M5 y M15
- ✅ **Réplica exacta** de la estrategia MT5
- ✅ **Gestión completa** de SL, TP parcial y TP final
- ✅ **Gestión de riesgo** avanzada con control de drawdown
- ✅ **Múltiples fuentes** de datos (Yahoo Finance, CSV, MT5)
- ✅ **Reportes detallados** en TXT, CSV, JSON y HTML
- ✅ **Visualizaciones** profesionales (equity, drawdown, distribución)
- ✅ **30+ métricas** (Sharpe, Sortino, Calmar, Profit Factor, etc.)

### 🚀 Instalación Rápida

```bash
cd Python
pip install -r backtest_requirements.txt
```

### 📊 Uso Básico

#### Backtest Simple
```bash
# Backtest de EURUSD (últimos 3 meses)
python run_backtest.py

# Backtest personalizado
python run_backtest.py --symbol GBPUSD --start 2023-01-01 --end 2023-12-31
```

#### Parámetros Disponibles
```bash
python run_backtest.py --help

Opciones:
  --symbol SYMBOL       Símbolo (EURUSD, GBPUSD, etc.)
  --start YYYY-MM-DD    Fecha inicial
  --end YYYY-MM-DD      Fecha final
  --balance FLOAT       Balance inicial [default: 10000]
  --leverage INT        Apalancamiento [default: 100]
  --risk FLOAT          Riesgo por trade % [default: 1.0]
  --spread FLOAT        Spread en pips [default: 1.0]
  --commission FLOAT    Comisión por lote [default: 0.0]
  --source {yfinance,csv,mt5}
  --output-dir PATH     Directorio de salida
```

### 💡 Ejemplo en Código Python

```python
from backtest.data_loader import DataLoader
from backtest.backtester import Backtester
from datetime import datetime, timedelta

# Cargar datos
loader = DataLoader()
end_date = datetime.now()
start_date = end_date - timedelta(days=60)

data_m1 = loader.load_data("EURUSD=X", start_date, end_date, "1min")
data_m5 = loader.load_data("EURUSD=X", start_date, end_date, "5min")
data_m15 = loader.load_data("EURUSD=X", start_date, end_date, "15min")

# Ejecutar backtest
backtester = Backtester(
    symbol="EURUSD",
    initial_balance=10000.0,
    risk_per_trade=1.0,
    stop_loss_pips=12.0
)

results = backtester.run(data_m1, data_m5, data_m15)

# Generar reportes y gráficos
backtester.generate_reports(results)
```

### 📈 Resultados Generados

El backtest genera automáticamente:

```
backtest_results/
├── backtest_report.txt          # Reporte detallado en texto
├── backtest_report.json         # Datos estructurados en JSON
├── backtest_report.html         # Reporte visual interactivo
├── trades.csv                   # Histórico completo de trades
├── equity_curve.csv             # Curva de equity
├── equity_curve.png             # Gráfico de equity y P/L
├── drawdown.png                 # Análisis de drawdown
├── trade_distribution.png       # Distribución de resultados
└── monthly_returns.png          # Retornos mensuales
```

### 📊 Métricas Calculadas

**Básicas:**
- Total de trades, Win rate, Profit factor
- Beneficio neto/bruto, Pérdida bruta
- Expectancy, Ratio ganancia/pérdida

**Drawdown:**
- Max drawdown ($ y %), Average drawdown
- Recovery factor

**Riesgo:**
- Sharpe ratio, Sortino ratio, Calmar ratio

**Temporales:**
- Duración promedio de trades
- Retornos mensuales y anuales
- Rachas de victorias/derrotas

### 🎯 Ejemplos Avanzados

#### Comparar Múltiples Símbolos
```python
symbols = ["EURUSD", "GBPUSD", "USDJPY"]
for symbol in symbols:
    # Cargar datos y ejecutar backtest
    results = backtester.run(data_m1, data_m5, data_m15)
    print(f"{symbol}: Net Profit = ${results['statistics']['net_profit']:.2f}")
```

#### Optimización de Parámetros
```python
best_profit = 0
for sl in [10, 12, 15]:
    for risk in [0.5, 1.0, 1.5]:
        backtester = Backtester(stop_loss_pips=sl, risk_per_trade=risk)
        results = backtester.run(data_m1, data_m5, data_m15, verbose=False)
        if results['statistics']['net_profit'] > best_profit:
            best_profit = results['statistics']['net_profit']
            print(f"Mejor combinación: SL={sl}, Risk={risk}")
```

### 📚 Documentación Completa

Para guía detallada, ejemplos avanzados y troubleshooting, consulta:

```bash
cat BACKTEST_README.md
```

O ejecuta ejemplos interactivos:
```bash
python example_backtest.py
```

### 🎨 Fuentes de Datos

**Yahoo Finance (Recomendado para empezar):**
- ✅ Gratis y sin instalación
- ✅ Fácil de usar
- ⚠️ Limitado a ~30-60 días para datos intraday

**Archivos CSV:**
- ✅ Control total de los datos
- ✅ Ideal para datos propios
- Formato: `time,open,high,low,close,volume`

**MetaTrader 5 Directo:**
- ✅ Datos oficiales del broker
- ✅ Sin límite de histórico
- ⚠️ Requiere MT5 instalado y conectado

### ⚡ Consejos de Uso

1. **Empieza con períodos cortos** (1-2 meses) para pruebas rápidas
2. **Usa cache de datos** para acelerar tests repetidos
3. **Compara con MT5 Strategy Tester** para validar resultados
4. **Analiza drawdown** antes que profit absoluto
5. **Haz walk-forward analysis** para validar robustez

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Haz commit de tus cambios
4. Abre un Pull Request

## 📧 Soporte

Para soporte o preguntas, abrir un Issue en GitHub.

---

**Disclaimer**: Este software es solo para fines educativos. El trading de forex conlleva riesgos significativos. Nunca inviertas dinero que no puedas permitirte perder.
