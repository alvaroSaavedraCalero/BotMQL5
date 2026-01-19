# Guía de Instalación del Expert Advisor en MetaTrader 5

Esta guía te ayudará a instalar y configurar el Expert Advisor (EA) **MultiTF_Scalper** en MetaTrader 5.

## 📋 Requisitos Previos

- ✅ MetaTrader 5 instalado y funcionando
- ✅ Cuenta de trading (demo o real)
- ✅ Conexión a Internet estable

## 🔧 Instalación del EA

### Paso 1: Localizar el Directorio de Datos de MT5

1. Abre MetaTrader 5
2. Ve a **Archivo** → **Abrir carpeta de datos**
3. Se abrirá el explorador de archivos en una ruta similar a:
   - Windows: `C:\Users\[TuUsuario]\AppData\Roaming\MetaQuotes\Terminal\[ID_Terminal]\`

### Paso 2: Copiar los Archivos del Bot

1. Navega hasta el directorio `MQL5` que se abrió en el Paso 1

2. Copia la estructura completa de la carpeta `MQL5` de este proyecto:

   ```
   Desde:  BotMQL5/MQL5/
   Hacia:  [Carpeta de datos MT5]/MQL5/
   ```

3. La estructura final debe quedar así:

   ```
   [Carpeta de datos MT5]/MQL5/
   ├── Experts/
   │   └── MultiTF_Scalper.mq5
   ├── Include/
   │   ├── Constants.mqh
   │   ├── RiskManager.mqh
   │   ├── SessionManager.mqh
   │   ├── TradeManager.mqh
   │   ├── SignalEngine.mqh
   │   └── SocketClient.mqh
   └── Libraries/
       └── JsonParser.mqh
   ```

### Paso 3: Compilar el Expert Advisor

1. En MetaTrader 5, presiona **F4** o ve a **Herramientas** → **Editor MetaQuotes**

2. En el MetaEditor, en el panel **Navegador** (izquierda), busca:
   - **Experts** → **MultiTF_Scalper.mq5**

3. Haz doble clic para abrir el archivo

4. Presiona **F7** o haz clic en el botón **Compilar** (ícono de engranaje verde)

5. Verifica en la pestaña **Errores** (parte inferior) que la compilación fue exitosa:
   - ✅ **0 error(s), 0 warning(s)** = Compilación exitosa
   - ❌ Si hay errores, verifica que copiaste todos los archivos correctamente

6. Cierra el MetaEditor

### Paso 4: Configurar Permisos en MT5

1. En MetaTrader 5, ve a **Herramientas** → **Opciones** (o presiona Ctrl+O)

2. En la pestaña **Expert Advisors**:
   - ✅ Marca **"Permitir trading algorítmico"**
   - ✅ Marca **"Permitir importaciones de DLL"** (para comunicación con Python)
   - ✅ Marca **"Permitir WebRequest para las siguientes URLs"** y añade:
     - `https://www.investing.com`
     - `http://localhost:5555`

3. Haz clic en **OK**

### Paso 5: Agregar el EA al Gráfico

1. En MetaTrader 5, abre un gráfico del símbolo que deseas operar (ejemplo: EURUSD)

2. En el panel **Navegador** (Ctrl+N), busca:
   - **Expert Advisors** → **MultiTF_Scalper**

3. Arrastra el EA al gráfico del símbolo

4. Se abrirá una ventana de configuración con múltiples pestañas

### Paso 6: Configurar Parámetros del EA

#### Pestaña "Común"
- ✅ Marca **"Permitir trading algorítmico"**
- ✅ Marca **"Permitir importaciones DLL"**
- ✅ Configura **"Trading" → "Solo compras y ventas"**

#### Pestaña "Parámetros de entrada"

Configura los siguientes parámetros según tus necesidades:

| Parámetro | Valor Recomendado | Descripción |
|-----------|-------------------|-------------|
| **MaxDrawDown** | 10.0 | Drawdown máximo de cuenta (%) |
| **MaxDailyDrawDown** | 5.0 | Drawdown máximo diario (%) |
| **MaxDailyOperations** | 10 | Máximo de operaciones por día |
| **RiskPerTrade** | 1.0 | Riesgo por operación (% de cuenta) |
| **StopLossPips** | 12 | Stop Loss en pips |
| **RR_Partial** | 2.0 | Ratio riesgo/beneficio para cierre parcial |
| **RR_Final** | 3.0 | Ratio riesgo/beneficio para cierre final |
| **PartialClosePercent** | 50 | Porcentaje de posición a cerrar en TP parcial |
| **MagicNumber** | 123456 | Número mágico para identificar operaciones |

**⚠️ IMPORTANTE para cuentas pequeñas:**
- Si tu cuenta es menor a $1000, reduce `RiskPerTrade` a 0.5% o menos
- Ajusta `MaxDailyOperations` según tu capital disponible

5. Haz clic en **OK**

### Paso 7: Verificar que el EA está Activo

1. En la esquina superior derecha del gráfico, deberías ver:
   - ✅ Un ícono de "carita feliz" (😊) = EA activo y funcionando
   - ⚠️ Un ícono de "carita triste" o una X = EA no está operativo

2. Si el EA no está activo:
   - Verifica que "Permitir trading algorítmico" esté habilitado (botón en la barra superior)
   - Revisa la pestaña **Experts** en la parte inferior para ver mensajes de error

3. En la pestaña **Experts** deberías ver mensajes como:
   ```
   MultiTF_Scalper EURUSD,M1: Initialized successfully
   MultiTF_Scalper EURUSD,M1: Trading enabled
   ```

## 🔄 Comunicación con Python (Opcional)

El EA puede comunicarse con el componente Python del bot para funciones avanzadas:

### Crear Carpeta de Comunicación

1. Navega a:
   - `[Carpeta de datos MT5]/MQL5/Files/`

2. Crea una carpeta llamada: **ScalpingBot**

3. La ruta completa debe ser:
   - `[Carpeta de datos MT5]/MQL5/Files/ScalpingBot/`

El EA creará automáticamente archivos JSON en esta carpeta para comunicarse con Python.

## ✅ Verificación Final

Checklist de verificación:

- [ ] EA compilado sin errores en MetaEditor
- [ ] "Permitir trading algorítmico" habilitado en Opciones
- [ ] "Permitir importaciones DLL" habilitado
- [ ] EA adjunto al gráfico con parámetros configurados
- [ ] Ícono de "carita feliz" visible en el gráfico
- [ ] Mensajes de inicialización visibles en pestaña Experts
- [ ] Carpeta ScalpingBot creada en MQL5/Files/ (si usas Python)

## 🎯 Próximos Pasos

1. **Modo Demo**: Prueba el EA en una cuenta demo durante al menos 2 semanas
2. **Monitoreo**: Observa el comportamiento del bot y ajusta parámetros si es necesario
3. **Dashboard Python**: Si deseas usar el dashboard web, ejecuta `./start.sh` en Linux

## ⚠️ Solución de Problemas

### Error: "Cannot open file MultiTF_Scalper.mq5"
- **Solución**: Verifica que copiaste correctamente todos los archivos .mqh en la carpeta Include/

### Error: "Trading is not allowed"
- **Solución**: Habilita "Permitir trading algorítmico" en Herramientas → Opciones → Expert Advisors

### El EA no abre operaciones
- Verifica que estés en horario de sesión de trading (Londres: 08:00-12:00 UTC, NY: 13:00-17:00 UTC)
- Revisa que el spread no sea demasiado alto
- Comprueba que no haya noticias de alto impacto próximas
- Verifica los logs en la pestaña Experts para más detalles

### El EA se desactiva automáticamente
- Revisa los límites de drawdown configurados
- Verifica que no se haya alcanzado el límite de operaciones diarias
- Comprueba la conexión a Internet

## 📞 Soporte

Si encuentras problemas durante la instalación:
1. Revisa los logs en la pestaña **Experts** de MT5
2. Consulta el archivo README.md del proyecto
3. Abre un Issue en el repositorio de GitHub

---

**¡Éxito con tu trading! Recuerda siempre probar en demo primero.**
