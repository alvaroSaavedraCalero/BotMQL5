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
│   └── utils/                        # Utilidades
│
├── .gitignore
└── README.md
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
```bash
cd Python
pip install -r requirements.txt
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

## ⚠️ Advertencias

- **Cuenta Demo**: Prueba siempre en cuenta demo primero
- **Backtesting**: Realiza backtesting extensivo antes de usar en real
- **Riesgo**: El trading conlleva riesgo de pérdida de capital
- **Supervisión**: Monitorea el bot regularmente

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
