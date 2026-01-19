# CLAUDE.MD - Guía para Claude Code

Este documento proporciona contexto y guías para trabajar efectivamente con el proyecto BotMQL5.

## 📋 Resumen del Proyecto

Sistema de trading automatizado dual (MQL5 + Python) para scalping en Forex con:
- **Expert Advisor (EA)** en MQL5 que ejecuta la estrategia de trading
- **Backend Python** para análisis, dashboard y comunicación bidireccional
- **Estrategia**: Multi-Timeframe Momentum Scalper (M1/M5/M15)
- **Comunicación**: Archivos JSON compartidos entre MT5 y Python

## 🏗️ Arquitectura del Sistema

### Componentes Principales

#### 1. MQL5 (MetaTrader 5)
```
MQL5/
├── Experts/
│   └── MultiTF_Scalper.mq5          # EA principal (punto de entrada)
├── Include/
│   ├── Constants.mqh                 # Constantes globales y enums
│   ├── RiskManager.mqh              # Gestión de riesgo y capital
│   ├── SessionManager.mqh           # Control de sesiones de trading
│   ├── TradeManager.mqh             # Ejecución y gestión de trades
│   ├── SignalEngine.mqh             # Análisis técnico y señales
│   └── SocketClient.mqh             # Comunicación con Python
└── Libraries/
    └── JsonParser.mqh               # Parsing JSON (si se necesita)
```

**Flujo de ejecución MQL5:**
1. `OnInit()`: Inicialización, configuración, validaciones
2. `OnTick()`: Análisis de mercado, generación de señales, gestión de posiciones
3. `OnDeinit()`: Limpieza y cierre de recursos

#### 2. Python (Backend y Dashboard)
```
Python/
├── main.py                          # Entry point de la aplicación
├── config.py                        # Configuración centralizada
├── requirements.txt                 # Dependencias Python
├── core/
│   ├── risk_manager.py             # Cálculos de riesgo
│   ├── signal_analyzer.py          # Análisis de señales
│   └── strategy_validator.py       # Validación de estrategia
├── communication/
│   ├── file_bridge.py              # Lectura/escritura de archivos JSON
│   └── command_handler.py          # Procesamiento de comandos
├── dashboard/
│   ├── app.py                      # Aplicación Dash
│   ├── layouts.py                  # Layouts del dashboard
│   └── callbacks.py                # Callbacks interactivos
├── data/
│   ├── database.py                 # SQLite para histórico
│   └── models.py                   # Modelos de datos
└── utils/
    ├── logger.py                   # Logging centralizado
    └── helpers.py                  # Funciones auxiliares
```

### Comunicación MT5 ↔ Python

**Directorio de intercambio:**
```
%APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\
```

**Archivos JSON:**
- `mt5_status.json`: Estado del EA → Python (posiciones, balance, equity, etc.)
- `python_signals.json`: Señales Python → MT5 (confirmación/invalidación)
- `python_to_mt5.json`: Comandos Python → MT5 (PAUSE, RESUME, CLOSE_ALL)
- `mt5_to_python.json`: Eventos MT5 → Python (trades ejecutados)
- `heartbeat.json`: Latido de conexión (ambos direcciones)

**Protocolo:**
1. MT5 escribe estado cada tick en `mt5_status.json`
2. Python lee cada segundo y procesa
3. Python escribe comandos en `python_to_mt5.json`
4. MT5 lee comandos cada tick y ejecuta
5. Heartbeat cada 5 segundos para verificar conexión

## 🎯 Estrategia de Trading

### Lógica Multi-Timeframe

**M15 (Tendencia Principal):**
- EMA 9 y EMA 21
- Determina dirección general del mercado
- Long si EMA9 > EMA21, Short si EMA9 < EMA21

**M5 (Confirmación Intermedia):**
- EMA 9 y EMA 21
- RSI (14): Filtro de momentum (40-70 para long, 30-60 para short)
- VWAP: Nivel dinámico de referencia

**M1 (Timing de Entrada):**
- Stochastic (5,3,3): Señal de entrada precisa
- ATR (14): Validación de volatilidad mínima

### Gestión de Riesgo

**Reglas críticas:**
- **Máximo drawdown cuenta**: 10% (configurable)
- **Máximo drawdown diario**: 5% (configurable)
- **Máximo trades/día**: 10 (configurable)
- **Riesgo por trade**: 1% del balance (configurable)
- **Stop Loss**: 10-15 pips
- **Take Profit parcial**: R:R 1:2 (cierra 50% + move to BE)
- **Take Profit final**: R:R 1:3 (cierra el 50% restante)

### Sesiones de Trading

Solo opera durante:
- **Londres**: 08:00 - 12:00 (hora del servidor MT5)
- **Nueva York**: 13:00 - 17:00 (hora del servidor MT5)

### Filtro de Noticias

- Buffer de 45 minutos antes y después de noticias de alto impacto
- Consulta calendario económico (ForexFactory o similar)
- Bloquea nuevas entradas durante ventana de noticias
- Puede cerrar posiciones abiertas si hay exposición crítica

## 💻 Desarrollo y Modificaciones

### Modificar la Estrategia de Trading

**Cambiar indicadores o parámetros:**
1. Editar `MQL5/Include/SignalEngine.mqh`
2. Modificar funciones `AnalyzeM15()`, `AnalyzeM5()`, `AnalyzeM1()`
3. Actualizar constantes en `Constants.mqh` si es necesario
4. Recompilar en MetaEditor (F7)
5. Reiniciar EA en MT5

**Agregar nuevo indicador:**
1. Declarar handle en `SignalEngine.mqh` (sección de variables)
2. Inicializar en constructor o función de setup
3. Integrar lectura de valores en funciones de análisis
4. Liberar handle en destructor

### Modificar Gestión de Riesgo

**Cambiar cálculo de lote o SL/TP:**
1. Editar `MQL5/Include/RiskManager.mqh`
2. Modificar función `CalculateLotSize()` para lote
3. Modificar función `CalculateStopLoss()` o `CalculateTakeProfit()` para SL/TP
4. Asegurar que se respetan los límites del símbolo (volumen mínimo/máximo)

### Agregar Nueva Funcionalidad al Dashboard

**Añadir nuevo panel o gráfico:**
1. Crear layout en `Python/dashboard/layouts.py`
2. Agregar callback en `Python/dashboard/callbacks.py`
3. Actualizar función principal en `Python/dashboard/app.py`
4. Asegurar que los datos necesarios están en `mt5_status.json`

**Agregar nuevo comando desde dashboard:**
1. Crear botón/control en `layouts.py`
2. Crear callback en `callbacks.py` que escriba en `python_to_mt5.json`
3. Implementar handler en `MQL5/Include/SocketClient.mqh`
4. Agregar comando a lista de comandos válidos

### Base de Datos

**Agregar nuevo campo a histórico:**
1. Modificar modelo en `Python/data/models.py`
2. Crear migración de base de datos (si usa ORM) o alterar tabla manualmente
3. Actualizar función de inserción en `database.py`
4. Actualizar lectura desde MT5 en `communication/file_bridge.py`

## 🔧 Convenciones de Código

### MQL5

**Nomenclatura:**
- Clases: `PascalCase` (ej: `TradeManager`, `RiskManager`)
- Funciones: `PascalCase` (ej: `CalculateLotSize()`, `OpenTrade()`)
- Variables globales: `g_camelCase` (ej: `g_tradeManager`, `g_lastTickTime`)
- Variables locales: `camelCase` (ej: `lotSize`, `stopLoss`)
- Constantes: `UPPER_SNAKE_CASE` (ej: `MAX_SLIPPAGE`, `DEFAULT_MAGIC`)
- Enums: `PascalCase` con prefijo (ej: `ENUM_SIGNAL_TYPE`)

**Estilo:**
- Indentación: 3 espacios (estándar MQL5)
- Llaves en nueva línea para funciones
- Comentarios: `//` para línea, `/* */` para bloque
- Siempre validar retornos de funciones críticas

**Ejemplo:**
```mql5
class CTradeManager
  {
private:
   double            m_stopLoss;
   double            m_takeProfit;

public:
   bool              OpenTrade(ENUM_ORDER_TYPE orderType, double volume)
     {
      // Validación de parámetros
      if(volume <= 0)
        {
         Print("Error: Invalid volume");
         return false;
        }

      // Lógica de apertura
      // ...

      return true;
     }
  };
```

### Python

**Nomenclatura:**
- Clases: `PascalCase` (ej: `RiskManager`, `SignalAnalyzer`)
- Funciones: `snake_case` (ej: `calculate_lot_size()`, `process_signal()`)
- Variables: `snake_case` (ej: `lot_size`, `stop_loss`)
- Constantes: `UPPER_SNAKE_CASE` (ej: `MAX_RETRIES`, `DEFAULT_PORT`)
- Privadas: Prefijo `_` (ej: `_internal_method()`)

**Estilo:**
- Seguir PEP 8
- Indentación: 4 espacios
- Imports: agrupados (stdlib, third-party, local)
- Docstrings: Google Style
- Type hints donde sea apropiado

**Ejemplo:**
```python
from typing import Optional, Dict
import json

class RiskManager:
    """Gestiona el riesgo y cálculo de tamaño de posición.

    Attributes:
        max_risk_percent: Porcentaje máximo de riesgo por trade
        account_balance: Balance actual de la cuenta
    """

    def __init__(self, max_risk_percent: float = 1.0):
        self.max_risk_percent = max_risk_percent
        self._account_balance = 0.0

    def calculate_position_size(
        self,
        stop_loss_pips: float,
        pip_value: float
    ) -> Optional[float]:
        """Calcula el tamaño de posición basado en riesgo.

        Args:
            stop_loss_pips: Stop loss en pips
            pip_value: Valor de un pip

        Returns:
            Tamaño de posición en lotes, o None si hay error
        """
        if stop_loss_pips <= 0 or pip_value <= 0:
            return None

        risk_amount = self._account_balance * (self.max_risk_percent / 100)
        position_size = risk_amount / (stop_loss_pips * pip_value)

        return position_size
```

## 🐛 Debugging

### MQL5

**Logs:**
- Usar `Print()` para mensajes generales
- Usar `Comment()` para mostrar en gráfico
- Logs se guardan en: `Terminal\[ID]\MQL5\Logs\`

**Errores comunes:**
- `Trade context is busy`: Esperar un tick o usar retry logic
- `Invalid stops`: Verificar distancia mínima del broker (SYMBOL_TRADE_STOPS_LEVEL)
- `Not enough money`: Reducir tamaño de lote o verificar balance
- `Market closed`: Verificar horarios de trading del símbolo

### Python

**Logs:**
- Configurar logging en `utils/logger.py`
- Niveles: DEBUG para desarrollo, INFO para producción
- Logs rotativos para evitar archivos grandes

**Errores comunes:**
- `File not found`: Verificar ruta de archivos JSON (usar Path de pathlib)
- `JSON decode error`: Archivo corrupto o escritura incompleta (implementar retry)
- `Connection timeout`: MT5 no está escribiendo heartbeat (verificar que EA esté corriendo)

## 📝 Testing

### MQL5

**Strategy Tester:**
1. Ctrl+R para abrir Strategy Tester
2. Seleccionar EA, símbolo, periodo
3. Usar "Every tick" o "1 minute OHLC" según necesidad
4. Revisar reporte: Profit Factor, Drawdown, Win Rate

**Optimización:**
- Usar optimización genética para parámetros
- Validar en período fuera de muestra (out-of-sample)
- Evitar over-fitting

### Python

**Unit tests:**
```bash
cd Python
pytest tests/ -v
pytest tests/test_risk_manager.py -v  # Test específico
```

**Integración:**
- Simular archivos JSON de MT5 para testing
- Usar mocking para dependencias externas
- Validar todos los comandos y respuestas

## 🚨 Consideraciones Importantes

### Seguridad

- **Nunca** commitear claves API o credenciales
- Usar variables de entorno para configuración sensible
- Revisar `.gitignore` para excluir archivos de configuración local

### Performance

**MQL5:**
- Minimizar cálculos en `OnTick()` (se ejecuta cada cambio de precio)
- Cachear valores de indicadores cuando sea posible
- Usar timers (`OnTimer()`) para tareas periódicas no críticas

**Python:**
- Usar async/await para I/O bound operations
- Implementar rate limiting para archivos JSON
- Considerar usar base de datos para histórico grande

### Mantenimiento

- **Backups**: Respaldar configuración y datos antes de cambios mayores
- **Versionado**: Usar semantic versioning (MAJOR.MINOR.PATCH)
- **Changelog**: Documentar cambios significativos
- **Code review**: Revisar cambios antes de desplegar en cuenta real

## 🎓 Recursos de Aprendizaje

### MQL5
- [Documentación oficial MQL5](https://www.mql5.com/en/docs)
- [MQL5 Reference](https://www.mql5.com/en/docs/references)
- [Artículos sobre estrategias](https://www.mql5.com/en/articles)

### Python
- [Dash Documentation](https://dash.plotly.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

## 📞 Contacto y Soporte

Para problemas o preguntas:
1. Revisar Issues existentes en GitHub
2. Crear nuevo Issue con detalles: versión, logs, pasos para reproducir
3. Proporcionar archivos de log relevantes

---

**Última actualización**: 2026-01-19
**Versión del proyecto**: 1.0.0
