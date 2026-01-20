# Configuración del Entorno - Multi-TF Scalping Bot

## ✅ Requisitos del Sistema

Este proyecto está diseñado para ejecutarse **exclusivamente en Windows**, ya que MetaTrader 5 y la biblioteca `MetaTrader5` de Python requieren este sistema operativo.

**Requisitos:**
- ✅ Windows 10 o superior
- ✅ Python 3.9 o superior
- ✅ MetaTrader 5 instalado
- ✅ Mínimo 4GB RAM
- ✅ Conexión a Internet estable

## 🚀 Instalación Inicial

### 1. Instalar Python

1. Descarga Python 3.9+ desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, **marca la opción "Add Python to PATH"**
3. Verifica la instalación:
   ```cmd
   python --version
   ```

### 2. Configurar el Entorno Virtual

Abre una terminal de PowerShell o CMD en la carpeta del proyecto:

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

```cmd
cd Python
pip install -r requirements.txt
```

Esto instalará:
- `MetaTrader5>=5.0.45` - Conexión con MT5
- `pandas>=2.0.0` - Análisis de datos
- `numpy>=1.24.0` - Cálculos numéricos
- `dash>=2.14.0` - Dashboard web
- `plotly>=5.17.0` - Gráficos interactivos
- Y otras dependencias necesarias

### 4. Instalar MetaTrader 5

Sigue la guía detallada en `INSTALACION_MT5.md` para:
- Instalar MetaTrader 5
- Copiar y compilar el Expert Advisor (EA)
- Configurar parámetros de trading

## 🚀 Inicio Rápido

### 1. Activar el Entorno Virtual

Cada vez que abras una nueva terminal:

```cmd
venv\Scripts\activate
```

### 2. Iniciar el Dashboard y Servicios Python

```cmd
cd Python
python main.py
```

Esto iniciará:
- Dashboard web en `http://localhost:8050`
- Servidor de comunicación con MT5
- Sistema de monitoreo y logging

### 3. Activar el EA en MetaTrader 5

1. Abre MetaTrader 5
2. Arrastra el EA `MultiTF_Scalper` a un gráfico
3. Configura los parámetros según tu estrategia
4. Habilita el trading algorítmico (botón "AutoTrading")

## 📁 Estructura de Archivos de Comunicación

El bot se comunica mediante archivos JSON ubicados en:

```
%APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\
├── mt5_status.json        # Estado del EA → Python
├── python_signals.json    # Señales Python → EA
├── python_to_mt5.json     # Comandos → EA
├── mt5_to_python.json     # Trades → Python
└── heartbeat.json         # Latido de conexión
```

**Ruta típica completa:**
```
C:\Users\[TuUsuario]\AppData\Roaming\MetaQuotes\Terminal\Common\Files\ScalpingBot\
```

## 🔧 Personalización de Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```cmd
copy .env.example .env
notepad .env
```

Modifica los valores según tus necesidades.

### Modificar Configuración Directamente

Edita `Python/config.py` para cambiar:
- Parámetros de trading
- Sesiones de horario
- Símbolos a operar
- Puertos del dashboard

## 🧪 Probar el Sistema

### Verificar Configuración

Puedes verificar que Python y las dependencias estén correctamente instaladas:

```cmd
venv\Scripts\activate
cd Python
python -c "from config import config; print(config.to_dict())"
```

Esto mostrará la configuración actual del sistema.

### Ejecutar Dashboard

```cmd
venv\Scripts\activate
cd Python
python main.py
```

Abre tu navegador en `http://localhost:8050`

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

Puedes usar PowerShell para ver logs en tiempo real:

```powershell
Get-Content Python\logs\*.log -Wait -Tail 50
```

O simplemente abre los archivos de log con un editor de texto.

### Ubicación de Logs

- **Python:** `Python\logs\`
- **MetaTrader 5:**
  - Pestaña "Experts" en MT5
  - Archivos log en `%APPDATA%\MetaQuotes\Terminal\[ID_Terminal]\MQL5\Logs\`

## ⚙️ Comandos Útiles

### Iniciar el Bot

```cmd
venv\Scripts\activate
cd Python
python main.py
```

Inicia el dashboard y todos los servicios Python.

### Activar Entorno Virtual

```cmd
venv\Scripts\activate
```

### Ejecutar Tests

```cmd
venv\Scripts\activate
cd Python
pytest tests\ -v
```

### Desactivar Entorno Virtual

```cmd
deactivate
```

## 📝 Próximos Pasos Recomendados

1. **Instala Python y dependencias:**
   - Sigue las instrucciones de instalación inicial
   - Verifica que todo funcione correctamente

2. **Instala el EA en MT5:**
   - Sigue `INSTALACION_MT5.md` paso a paso
   - Compila el Expert Advisor
   - Verifica que no haya errores de compilación

3. **Configura parámetros:**
   - Edita `.env` o `Python\config.py`
   - Ajusta según tu estrategia y capital
   - Configura símbolos, timeframes y gestión de riesgo

4. **Prueba en Cuenta Demo:**
   - **SIEMPRE** prueba primero en cuenta demo
   - Monitorea al menos 2 semanas
   - Verifica que la comunicación entre Python y MT5 funcione

5. **Monitorea con el Dashboard:**
   - Ejecuta `python main.py` desde la carpeta Python
   - Abre `http://localhost:8050` en tu navegador
   - Observa métricas en tiempo real

## ❓ Preguntas Frecuentes

### ¿Puedo usar este bot en Linux o macOS?

No. Este bot requiere Windows porque MetaTrader 5 y la biblioteca `MetaTrader5` de Python solo funcionan en este sistema operativo.

### ¿El EA funciona sin Python?

Sí, el EA puede funcionar de forma independiente en MT5, pero sin:
- Dashboard de monitoreo web
- Señales adicionales de Python
- Estadísticas avanzadas
- Sistema de gestión de riesgo mejorado

### ¿Python funciona sin el EA?

Parcialmente. El dashboard se ejecutará pero no tendrá datos reales del mercado sin la conexión al EA. Es útil solo para desarrollo y pruebas de la interfaz.

### ¿Dónde cambio los parámetros de trading?

- **EA (MQL5):** Al agregar el EA al gráfico en MT5 (ventana de parámetros)
- **Python:** En `Python\config.py` o archivo `.env`

### ¿Cómo sé si Python y MT5 están comunicándose?

1. Verifica que los archivos JSON se estén creando en `%APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\`
2. Revisa los logs de Python en `Python\logs\`
3. Observa la pestaña "Experts" en MT5
4. El dashboard mostrará el estado de conexión

## 🆘 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'MetaTrader5'"

Asegúrate de tener el entorno virtual activado e instala las dependencias:

```cmd
venv\Scripts\activate
cd Python
pip install -r requirements.txt
```

Si el error persiste:
```cmd
pip install MetaTrader5>=5.0.45
```

### El dashboard no muestra datos

1. Verifica que el EA esté activo en MT5 (botón "AutoTrading" encendido)
2. Comprueba que los archivos JSON se están creando en:
   ```
   %APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\
   ```
3. Revisa los logs de Python en `Python\logs\`
4. Revisa la pestaña "Experts" en MT5 para ver mensajes del EA

### Error: "Python no se reconoce como comando"

Durante la instalación de Python, debes marcar la opción "Add Python to PATH". Si no lo hiciste:

1. Desinstala Python
2. Reinstálalo marcando "Add Python to PATH"
3. O añade Python manualmente a las variables de entorno del sistema

### Error al activar el entorno virtual

Si `venv\Scripts\activate` no funciona en PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Luego intenta activar nuevamente:
```cmd
venv\Scripts\activate
```

### MetaTrader 5 no se conecta

1. Verifica tu conexión a Internet
2. Asegúrate de tener credenciales válidas del broker
3. Comprueba que el trading algorítmico esté habilitado en MT5
4. Verifica que el símbolo esté disponible en tu cuenta

## 📚 Documentación Adicional

- `README.md` - Descripción general del proyecto
- `INSTALACION_MT5.md` - Guía detallada de instalación del EA en Windows
- `Python\requirements.txt` - Lista de dependencias de Python
- Código MQL5 en `MQL5\Experts\MultiTF_Scalper.mq5`

## 🔐 Seguridad y Mejores Prácticas

### Protección de Credenciales

- **NUNCA** compartas tus credenciales de MT5
- **NO** subas archivos `.env` al repositorio (ya está en `.gitignore`)
- Usa cuentas demo para pruebas iniciales

### Gestión de Riesgo

- Comienza con lotes pequeños
- Nunca arriesgues más del 1-2% de tu capital por operación
- Monitorea constantemente el bot durante las primeras semanas
- Ten un plan de emergencia para detener el bot si es necesario

### Actualizaciones

Para actualizar el proyecto:

```cmd
git pull origin main
venv\Scripts\activate
cd Python
pip install -r requirements.txt --upgrade
```

---

**¿Necesitas ayuda?** Abre un Issue en el repositorio de GitHub o consulta los logs para más detalles.
