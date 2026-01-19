# Configuración del Entorno - Multi-TF Scalping Bot

## ✅ Estado de la Instalación

El entorno de desarrollo ha sido configurado exitosamente:

- ✅ Python 3.11.14 instalado
- ✅ Entorno virtual creado en `venv/`
- ✅ Todas las dependencias de Python instaladas
- ✅ Directorios de datos y logs creados
- ✅ Scripts de inicio configurados

## 🖥️ Consideración Importante: Linux vs Windows

**Tu sistema actual:** Linux

**MetaTrader 5 requiere:** Windows (o macOS con limitaciones)

### El Problema

La biblioteca `MetaTrader5` de Python **solo funciona en Windows** porque se comunica directamente con la aplicación MetaTrader 5 a través de su API nativa. Aunque mencionaste que tienes MetaTrader 5 instalado, hay dos posibilidades:

1. **Tienes MT5 en Windows** (dual boot, otra máquina, etc.)
2. **Tienes MT5 en Wine/PlayOnLinux** en Linux

### Opciones de Configuración

#### Opción 1: Ejecutar Todo en Windows (RECOMENDADO)

**Ventajas:**
- ✅ Funcionalidad completa sin problemas
- ✅ Mejor rendimiento
- ✅ Soporte oficial de MT5

**Cómo hacerlo:**
1. Clona este repositorio en tu máquina Windows
2. Sigue las instrucciones en `INSTALACION_MT5.md`
3. Instala Python 3.9+ en Windows
4. Ejecuta:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   cd Python
   pip install -r requirements.txt
   python main.py
   ```

#### Opción 2: Arquitectura Híbrida (Linux + Windows)

**Ventajas:**
- ✅ Desarrollo en Linux, trading en Windows
- ✅ Usar tu entorno Linux preferido

**Arquitectura:**
```
┌─────────────────┐         ┌──────────────────┐
│  Linux (este)   │         │    Windows       │
│                 │         │                  │
│  - Dashboard    │◄───────►│  - MetaTrader 5  │
│  - Python core  │  JSON   │  - EA (MQL5)     │
│  - Análisis     │  Files  │                  │
└─────────────────┘         └──────────────────┘
```

**Cómo hacerlo:**

**En Windows:**
1. Instala MetaTrader 5
2. Copia la carpeta `MQL5/` según `INSTALACION_MT5.md`
3. Compila y activa el EA

**En Linux (este sistema):**
1. El entorno ya está configurado
2. Configura una carpeta compartida entre Linux y Windows (Samba, NFS, o carpeta compartida de VM)
3. Modifica `Python/config.py` línea 96-104 para apuntar a la carpeta compartida:
   ```python
   # En lugar de buscar en APPDATA, usa la carpeta compartida
   self.mt5_common_path = Path("/mnt/windows_share/ScalpingBot")
   ```

#### Opción 3: Solo Dashboard de Monitoreo (Limitado)

**Ventajas:**
- ✅ Puedes ejecutar el dashboard en Linux
- ✅ Útil para desarrollo y pruebas de UI

**Limitaciones:**
- ❌ No puede conectarse a MT5 sin configuración adicional
- ❌ Necesita archivos JSON creados por el EA en Windows

**Cómo hacerlo:**
1. Ejecuta el dashboard en modo desarrollo:
   ```bash
   ./start.sh
   ```
2. El dashboard mostrará datos de ejemplo o históricos

#### Opción 4: Wine/PlayOnLinux (No Recomendado)

**Nota:** MetaTrader 5 puede ejecutarse en Wine, pero:
- ⚠️ Rendimiento inconsistente
- ⚠️ Posibles problemas de estabilidad
- ⚠️ No recomendado para trading real

## 🚀 Inicio Rápido (Linux)

Si decides usar la **Opción 2** (Híbrida), sigue estos pasos:

### 1. Iniciar el Dashboard y Servicios Python

```bash
cd /home/user/BotMQL5
./start.sh
```

Esto iniciará:
- Dashboard web en `http://localhost:8050`
- Servidor de comunicación
- Sistema de monitoreo

### 2. En Windows (separado)

Sigue la guía `INSTALACION_MT5.md` para:
- Instalar el EA en MetaTrader 5
- Configurar parámetros
- Activar el trading algorítmico

## 📁 Estructura de Archivos de Comunicación

El bot se comunica mediante archivos JSON en:

**Windows:**
```
%APPDATA%\MetaQuotes\Terminal\Common\Files\ScalpingBot\
├── mt5_status.json        # Estado del EA → Python
├── python_signals.json    # Señales Python → EA
├── python_to_mt5.json     # Comandos → EA
├── mt5_to_python.json     # Trades → Python
└── heartbeat.json         # Latido de conexión
```

**Linux (configuración híbrida):**
```
/mnt/windows_share/ScalpingBot/  # o ruta que configures
├── (mismos archivos que arriba)
```

## 🔧 Personalización de Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
nano .env  # o tu editor preferido
```

Modifica los valores según tus necesidades.

### Modificar Configuración Directamente

Edita `Python/config.py` para cambiar:
- Parámetros de trading
- Sesiones de horario
- Símbolos a operar
- Puertos del dashboard

## 🧪 Probar el Sistema

### Solo Python (sin MT5)

Puedes probar el dashboard y componentes Python:

```bash
cd /home/user/BotMQL5
source venv/bin/activate
cd Python
python -c "from config import config; print(config.to_dict())"
```

Esto mostrará la configuración actual.

### Ejecutar Dashboard

```bash
./start.sh
```

Abre tu navegador en `http://localhost:8050`

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real

```bash
tail -f Python/logs/*.log
```

### Ubicación de Logs

- **Python:** `Python/logs/`
- **MetaTrader 5 (en Windows):**
  - Pestaña "Experts" en MT5
  - Archivos log en `[Datos MT5]/MQL5/Logs/`

## ⚙️ Scripts Disponibles

### `start.sh` - Iniciar el Bot

```bash
./start.sh
```

Inicia el dashboard y todos los servicios Python.

### Activar Entorno Virtual Manualmente

```bash
source venv/bin/activate
```

### Ejecutar Tests

```bash
source venv/bin/activate
cd Python
pytest tests/ -v
```

## 📝 Próximos Pasos Recomendados

1. **Decide tu arquitectura:**
   - ¿Todo en Windows? → Mueve el proyecto allí
   - ¿Híbrido? → Configura carpeta compartida

2. **Instala el EA en MT5:**
   - Sigue `INSTALACION_MT5.md` paso a paso

3. **Configura parámetros:**
   - Edita `.env` o `config.py`
   - Ajusta según tu estrategia y capital

4. **Prueba en Demo:**
   - **SIEMPRE** prueba primero en cuenta demo
   - Monitorea al menos 2 semanas

5. **Monitorea con el Dashboard:**
   - Ejecuta `./start.sh`
   - Observa métricas en tiempo real

## ❓ Preguntas Frecuentes

### ¿Puedo usar esto solo en Linux?

No completamente. Necesitas Windows para MetaTrader 5. Pero puedes desarrollar, probar el dashboard y mantener el código en Linux.

### ¿El EA funciona sin Python?

Sí, el EA puede funcionar de forma independiente en MT5, pero sin:
- Dashboard de monitoreo web
- Señales adicionales de Python
- Estadísticas avanzadas

### ¿Python funciona sin el EA?

Parcialmente. El dashboard se ejecutará pero no tendrá datos reales del mercado sin la conexión al EA.

### ¿Dónde cambio los parámetros de trading?

- **EA (MQL5):** Al agregar el EA al gráfico en MT5
- **Python:** En `Python/config.py` o archivo `.env`

## 🆘 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'MetaTrader5'"

**En Linux:**
- Normal, esta librería solo funciona en Windows
- El dashboard y otros componentes funcionarán sin ella
- Para funcionalidad completa, usa Windows

**En Windows:**
```cmd
pip install MetaTrader5>=5.0.45
```

### El dashboard no muestra datos

- Verifica que el EA esté activo en MT5
- Comprueba que los archivos JSON se están creando
- Revisa los logs: `tail -f Python/logs/*.log`

### Errores de permisos

```bash
chmod +x start.sh
chmod -R 755 /home/user/BotMQL5
```

## 📚 Documentación Adicional

- `README.md` - Descripción general del proyecto
- `INSTALACION_MT5.md` - Guía detallada de instalación del EA
- `Python/requirements.txt` - Lista de dependencias
- Código MQL5 en `MQL5/Experts/MultiTF_Scalper.mq5`

---

**¿Necesitas ayuda?** Abre un Issue en el repositorio de GitHub o consulta los logs para más detalles.
