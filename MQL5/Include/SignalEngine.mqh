//+------------------------------------------------------------------+
//|                                                 SignalEngine.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

#include "Constants.mqh"

//+------------------------------------------------------------------+
//| Clase para Generación de Señales Multi-Timeframe                  |
//+------------------------------------------------------------------+
class CSignalEngine
{
private:
   // Parámetros de indicadores
   int               m_ema_fast_period;
   int               m_ema_slow_period;
   int               m_rsi_period;
   int               m_stoch_k;
   int               m_stoch_d;
   int               m_stoch_slowing;
   int               m_atr_period;

   // Handles de indicadores para cada timeframe
   // M15 (Tendencia)
   int               m_ema_fast_m15_handle;
   int               m_ema_slow_m15_handle;

   // M5 (Confirmación)
   int               m_ema_fast_m5_handle;
   int               m_ema_slow_m5_handle;
   int               m_rsi_m5_handle;

   // M1 (Entrada)
   int               m_stoch_m1_handle;
   int               m_atr_m1_handle;

   // Símbolo actual
   string            m_symbol;

   // Umbrales
   double            m_min_atr;                // ATR mínimo para operar

   // Métodos de análisis
   bool              AnalyzeM15Trend(ENUM_SIGNAL_TYPE &trend);
   bool              AnalyzeM5Confirmation(ENUM_SIGNAL_TYPE trend, bool &confirmed);
   bool              AnalyzeM1Entry(ENUM_SIGNAL_TYPE trend, ENUM_SIGNAL_TYPE &signal);

   // Obtener valores de indicadores
   double            GetIndicatorValue(int handle, int shift = 0, int buffer = 0);
   bool              GetStochValues(double &k_current, double &k_prev, double &d_current);

public:
   // Constructor y destructor
                     CSignalEngine();
                    ~CSignalEngine();

   // Inicialización
   bool              Init(string symbol, int ema_fast, int ema_slow, int rsi_period,
                          int stoch_k, int stoch_d, int stoch_slowing, int atr_period);

   // Liberar recursos
   void              Deinit();

   // Análisis de señales
   ENUM_SIGNAL_TYPE  GetSignal();
   SignalInfo        GenerateSignalInfo(ENUM_SIGNAL_TYPE signal_type, double lot_size, int sl_pips);

   // Información de indicadores (para debug/dashboard)
   double            GetEMAFast(ENUM_TIMEFRAMES tf, int shift = 0);
   double            GetEMASlow(ENUM_TIMEFRAMES tf, int shift = 0);
   double            GetRSI(int shift = 0);
   double            GetStochK(int shift = 0);
   double            GetStochD(int shift = 0);
   double            GetATR(int shift = 0);
   double            GetVWAP(int shift = 0);

   // Estado de indicadores
   string            GetIndicatorsStatus();
   bool              AreIndicatorsReady();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CSignalEngine::CSignalEngine()
{
   m_ema_fast_period = DEFAULT_EMA_FAST;
   m_ema_slow_period = DEFAULT_EMA_SLOW;
   m_rsi_period = DEFAULT_RSI_PERIOD;
   m_stoch_k = DEFAULT_STOCH_K;
   m_stoch_d = DEFAULT_STOCH_D;
   m_stoch_slowing = DEFAULT_STOCH_SLOWING;
   m_atr_period = DEFAULT_ATR_PERIOD;

   m_ema_fast_m15_handle = INVALID_HANDLE;
   m_ema_slow_m15_handle = INVALID_HANDLE;
   m_ema_fast_m5_handle = INVALID_HANDLE;
   m_ema_slow_m5_handle = INVALID_HANDLE;
   m_rsi_m5_handle = INVALID_HANDLE;
   m_stoch_m1_handle = INVALID_HANDLE;
   m_atr_m1_handle = INVALID_HANDLE;

   m_symbol = "";
   m_min_atr = 0.0005; // ATR mínimo por defecto
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CSignalEngine::~CSignalEngine()
{
   Deinit();
}

//+------------------------------------------------------------------+
//| Inicialización de indicadores                                     |
//+------------------------------------------------------------------+
bool CSignalEngine::Init(string symbol, int ema_fast, int ema_slow, int rsi_period,
                         int stoch_k, int stoch_d, int stoch_slowing, int atr_period)
{
   m_symbol = symbol;
   m_ema_fast_period = ema_fast;
   m_ema_slow_period = ema_slow;
   m_rsi_period = rsi_period;
   m_stoch_k = stoch_k;
   m_stoch_d = stoch_d;
   m_stoch_slowing = stoch_slowing;
   m_atr_period = atr_period;

   // Crear handles de indicadores M15
   m_ema_fast_m15_handle = iMA(symbol, PERIOD_M15, ema_fast, 0, MODE_EMA, PRICE_CLOSE);
   m_ema_slow_m15_handle = iMA(symbol, PERIOD_M15, ema_slow, 0, MODE_EMA, PRICE_CLOSE);

   // Crear handles de indicadores M5
   m_ema_fast_m5_handle = iMA(symbol, PERIOD_M5, ema_fast, 0, MODE_EMA, PRICE_CLOSE);
   m_ema_slow_m5_handle = iMA(symbol, PERIOD_M5, ema_slow, 0, MODE_EMA, PRICE_CLOSE);
   m_rsi_m5_handle = iRSI(symbol, PERIOD_M5, rsi_period, PRICE_CLOSE);

   // Crear handles de indicadores M1
   m_stoch_m1_handle = iStochastic(symbol, PERIOD_M1, stoch_k, stoch_d, stoch_slowing, MODE_SMA, STO_LOWHIGH);
   m_atr_m1_handle = iATR(symbol, PERIOD_M1, atr_period);

   // Verificar que todos los handles sean válidos
   if(m_ema_fast_m15_handle == INVALID_HANDLE || m_ema_slow_m15_handle == INVALID_HANDLE ||
      m_ema_fast_m5_handle == INVALID_HANDLE || m_ema_slow_m5_handle == INVALID_HANDLE ||
      m_rsi_m5_handle == INVALID_HANDLE || m_stoch_m1_handle == INVALID_HANDLE ||
      m_atr_m1_handle == INVALID_HANDLE)
   {
      Print("Error creando handles de indicadores");
      Deinit();
      return false;
   }

   // Calcular ATR mínimo basado en el símbolo
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   m_min_atr = point * (digits == 5 || digits == 3 ? 30 : 3); // ~3 pips mínimo

   Print("SignalEngine inicializado para ", symbol);
   Print("Indicadores: EMA(", ema_fast, "/", ema_slow, ") | RSI(", rsi_period,
         ") | Stoch(", stoch_k, ",", stoch_d, ",", stoch_slowing, ") | ATR(", atr_period, ")");

   return true;
}

//+------------------------------------------------------------------+
//| Liberar recursos                                                  |
//+------------------------------------------------------------------+
void CSignalEngine::Deinit()
{
   if(m_ema_fast_m15_handle != INVALID_HANDLE) IndicatorRelease(m_ema_fast_m15_handle);
   if(m_ema_slow_m15_handle != INVALID_HANDLE) IndicatorRelease(m_ema_slow_m15_handle);
   if(m_ema_fast_m5_handle != INVALID_HANDLE) IndicatorRelease(m_ema_fast_m5_handle);
   if(m_ema_slow_m5_handle != INVALID_HANDLE) IndicatorRelease(m_ema_slow_m5_handle);
   if(m_rsi_m5_handle != INVALID_HANDLE) IndicatorRelease(m_rsi_m5_handle);
   if(m_stoch_m1_handle != INVALID_HANDLE) IndicatorRelease(m_stoch_m1_handle);
   if(m_atr_m1_handle != INVALID_HANDLE) IndicatorRelease(m_atr_m1_handle);

   m_ema_fast_m15_handle = INVALID_HANDLE;
   m_ema_slow_m15_handle = INVALID_HANDLE;
   m_ema_fast_m5_handle = INVALID_HANDLE;
   m_ema_slow_m5_handle = INVALID_HANDLE;
   m_rsi_m5_handle = INVALID_HANDLE;
   m_stoch_m1_handle = INVALID_HANDLE;
   m_atr_m1_handle = INVALID_HANDLE;
}

//+------------------------------------------------------------------+
//| Obtener señal                                                     |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE CSignalEngine::GetSignal()
{
   if(!AreIndicatorsReady())
   {
      Print("Indicadores no están listos");
      return SIGNAL_NONE;
   }

   // Paso 1: Analizar tendencia en M15
   ENUM_SIGNAL_TYPE trend = SIGNAL_NONE;
   if(!AnalyzeM15Trend(trend))
      return SIGNAL_NONE;

   // Paso 2: Confirmar en M5
   bool confirmed = false;
   if(!AnalyzeM5Confirmation(trend, confirmed))
      return SIGNAL_NONE;

   if(!confirmed)
      return SIGNAL_NONE;

   // Paso 3: Buscar entrada en M1
   ENUM_SIGNAL_TYPE signal = SIGNAL_NONE;
   if(!AnalyzeM1Entry(trend, signal))
      return SIGNAL_NONE;

   return signal;
}

//+------------------------------------------------------------------+
//| Analizar tendencia en M15                                         |
//+------------------------------------------------------------------+
bool CSignalEngine::AnalyzeM15Trend(ENUM_SIGNAL_TYPE &trend)
{
   double ema_fast = GetIndicatorValue(m_ema_fast_m15_handle, 1);
   double ema_slow = GetIndicatorValue(m_ema_slow_m15_handle, 1);

   if(ema_fast == 0 || ema_slow == 0)
      return false;

   if(ema_fast > ema_slow)
      trend = SIGNAL_BUY;
   else if(ema_fast < ema_slow)
      trend = SIGNAL_SELL;
   else
      trend = SIGNAL_NONE;

   return true;
}

//+------------------------------------------------------------------+
//| Confirmar en M5                                                   |
//+------------------------------------------------------------------+
bool CSignalEngine::AnalyzeM5Confirmation(ENUM_SIGNAL_TYPE trend, bool &confirmed)
{
   confirmed = false;

   double ema_fast = GetIndicatorValue(m_ema_fast_m5_handle, 1);
   double ema_slow = GetIndicatorValue(m_ema_slow_m5_handle, 1);
   double rsi = GetIndicatorValue(m_rsi_m5_handle, 1);
   double close = iClose(m_symbol, PERIOD_M5, 1);

   if(ema_fast == 0 || ema_slow == 0 || rsi == 0)
      return false;

   // Calcular VWAP aproximado (usando EMA 20 como proxy para simplicidad)
   // En una implementación más avanzada, se calcularía el VWAP real
   double vwap = (ema_fast + ema_slow) / 2; // Simplificación

   if(trend == SIGNAL_BUY)
   {
      // Condiciones de compra:
      // 1. EMA rápida > EMA lenta
      // 2. Precio > VWAP (aproximado)
      // 3. RSI entre 40 y 70
      if(ema_fast > ema_slow && close > vwap && rsi >= RSI_BUY_MIN && rsi <= RSI_BUY_MAX)
         confirmed = true;
   }
   else if(trend == SIGNAL_SELL)
   {
      // Condiciones de venta:
      // 1. EMA rápida < EMA lenta
      // 2. Precio < VWAP (aproximado)
      // 3. RSI entre 30 y 60
      if(ema_fast < ema_slow && close < vwap && rsi >= RSI_SELL_MIN && rsi <= RSI_SELL_MAX)
         confirmed = true;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Buscar entrada en M1                                              |
//+------------------------------------------------------------------+
bool CSignalEngine::AnalyzeM1Entry(ENUM_SIGNAL_TYPE trend, ENUM_SIGNAL_TYPE &signal)
{
   signal = SIGNAL_NONE;

   // Obtener valores de Stochastic
   double k_current, k_prev, d_current;
   if(!GetStochValues(k_current, k_prev, d_current))
      return false;

   // Verificar ATR mínimo (volatilidad suficiente)
   double atr = GetIndicatorValue(m_atr_m1_handle, 1);
   if(atr < m_min_atr)
   {
      // Volatilidad muy baja, no operar
      return true; // Retornar true pero sin señal
   }

   if(trend == SIGNAL_BUY)
   {
      // Señal de compra:
      // Stochastic cruza hacia arriba desde zona de sobreventa (<20)
      if(k_prev < STOCH_OVERSOLD && k_current > k_prev && k_current > d_current)
      {
         signal = SIGNAL_BUY;
         Print("Señal BUY detectada - Stoch K: ", k_current, " (prev: ", k_prev, ") | ATR: ", atr);
      }
   }
   else if(trend == SIGNAL_SELL)
   {
      // Señal de venta:
      // Stochastic cruza hacia abajo desde zona de sobrecompra (>80)
      if(k_prev > STOCH_OVERBOUGHT && k_current < k_prev && k_current < d_current)
      {
         signal = SIGNAL_SELL;
         Print("Señal SELL detectada - Stoch K: ", k_current, " (prev: ", k_prev, ") | ATR: ", atr);
      }
   }

   return true;
}

//+------------------------------------------------------------------+
//| Obtener valores de Stochastic                                     |
//+------------------------------------------------------------------+
bool CSignalEngine::GetStochValues(double &k_current, double &k_prev, double &d_current)
{
   double k_buffer[], d_buffer[];
   ArraySetAsSeries(k_buffer, true);
   ArraySetAsSeries(d_buffer, true);

   if(CopyBuffer(m_stoch_m1_handle, 0, 0, 3, k_buffer) < 3)
      return false;

   if(CopyBuffer(m_stoch_m1_handle, 1, 0, 2, d_buffer) < 2)
      return false;

   k_current = k_buffer[1];
   k_prev = k_buffer[2];
   d_current = d_buffer[1];

   return true;
}

//+------------------------------------------------------------------+
//| Obtener valor de indicador                                        |
//+------------------------------------------------------------------+
double CSignalEngine::GetIndicatorValue(int handle, int shift = 0, int buffer = 0)
{
   if(handle == INVALID_HANDLE)
      return 0;

   double value[];
   ArraySetAsSeries(value, true);

   if(CopyBuffer(handle, buffer, shift, 1, value) < 1)
      return 0;

   return value[0];
}

//+------------------------------------------------------------------+
//| Generar información de señal completa                             |
//+------------------------------------------------------------------+
SignalInfo CSignalEngine::GenerateSignalInfo(ENUM_SIGNAL_TYPE signal_type, double lot_size, int sl_pips)
{
   SignalInfo info;

   info.type = signal_type;
   info.symbol = m_symbol;
   info.lot_size = lot_size;
   info.sl_pips = sl_pips;
   info.tp1_pips = (int)(sl_pips * 2); // R:R 1:2
   info.tp2_pips = (int)(sl_pips * 3); // R:R 1:3
   info.signal_time = TimeCurrent();

   // Obtener precio de entrada
   if(signal_type == SIGNAL_BUY)
      info.entry_price = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
   else
      info.entry_price = SymbolInfoDouble(m_symbol, SYMBOL_BID);

   // Calcular niveles
   double pip_value = GetPipMultiplier(m_symbol);

   if(signal_type == SIGNAL_BUY)
   {
      info.stop_loss = info.entry_price - (sl_pips * pip_value);
      info.take_profit1 = info.entry_price + (info.tp1_pips * pip_value);
      info.take_profit2 = info.entry_price + (info.tp2_pips * pip_value);
   }
   else
   {
      info.stop_loss = info.entry_price + (sl_pips * pip_value);
      info.take_profit1 = info.entry_price - (info.tp1_pips * pip_value);
      info.take_profit2 = info.entry_price - (info.tp2_pips * pip_value);
   }

   info.comment = StringFormat("%s_%s", BOT_NAME, SignalTypeToString(signal_type));

   return info;
}

//+------------------------------------------------------------------+
//| Obtener EMA rápida                                                |
//+------------------------------------------------------------------+
double CSignalEngine::GetEMAFast(ENUM_TIMEFRAMES tf, int shift = 0)
{
   int handle = (tf == PERIOD_M15) ? m_ema_fast_m15_handle : m_ema_fast_m5_handle;
   return GetIndicatorValue(handle, shift);
}

//+------------------------------------------------------------------+
//| Obtener EMA lenta                                                 |
//+------------------------------------------------------------------+
double CSignalEngine::GetEMASlow(ENUM_TIMEFRAMES tf, int shift = 0)
{
   int handle = (tf == PERIOD_M15) ? m_ema_slow_m15_handle : m_ema_slow_m5_handle;
   return GetIndicatorValue(handle, shift);
}

//+------------------------------------------------------------------+
//| Obtener RSI                                                       |
//+------------------------------------------------------------------+
double CSignalEngine::GetRSI(int shift = 0)
{
   return GetIndicatorValue(m_rsi_m5_handle, shift);
}

//+------------------------------------------------------------------+
//| Obtener Stochastic K                                              |
//+------------------------------------------------------------------+
double CSignalEngine::GetStochK(int shift = 0)
{
   return GetIndicatorValue(m_stoch_m1_handle, shift, 0);
}

//+------------------------------------------------------------------+
//| Obtener Stochastic D                                              |
//+------------------------------------------------------------------+
double CSignalEngine::GetStochD(int shift = 0)
{
   return GetIndicatorValue(m_stoch_m1_handle, shift, 1);
}

//+------------------------------------------------------------------+
//| Obtener ATR                                                       |
//+------------------------------------------------------------------+
double CSignalEngine::GetATR(int shift = 0)
{
   return GetIndicatorValue(m_atr_m1_handle, shift);
}

//+------------------------------------------------------------------+
//| Obtener VWAP aproximado                                           |
//+------------------------------------------------------------------+
double CSignalEngine::GetVWAP(int shift = 0)
{
   // VWAP aproximado usando promedio de EMAs
   double ema_fast = GetIndicatorValue(m_ema_fast_m5_handle, shift);
   double ema_slow = GetIndicatorValue(m_ema_slow_m5_handle, shift);
   return (ema_fast + ema_slow) / 2;
}

//+------------------------------------------------------------------+
//| Verificar si indicadores están listos                             |
//+------------------------------------------------------------------+
bool CSignalEngine::AreIndicatorsReady()
{
   return (m_ema_fast_m15_handle != INVALID_HANDLE &&
           m_ema_slow_m15_handle != INVALID_HANDLE &&
           m_ema_fast_m5_handle != INVALID_HANDLE &&
           m_ema_slow_m5_handle != INVALID_HANDLE &&
           m_rsi_m5_handle != INVALID_HANDLE &&
           m_stoch_m1_handle != INVALID_HANDLE &&
           m_atr_m1_handle != INVALID_HANDLE);
}

//+------------------------------------------------------------------+
//| Obtener estado de indicadores                                     |
//+------------------------------------------------------------------+
string CSignalEngine::GetIndicatorsStatus()
{
   string status = "";

   status += StringFormat("M15 - EMA(%d): %.5f | EMA(%d): %.5f\n",
                          m_ema_fast_period, GetEMAFast(PERIOD_M15, 1),
                          m_ema_slow_period, GetEMASlow(PERIOD_M15, 1));

   status += StringFormat("M5  - EMA(%d): %.5f | EMA(%d): %.5f | RSI: %.2f\n",
                          m_ema_fast_period, GetEMAFast(PERIOD_M5, 1),
                          m_ema_slow_period, GetEMASlow(PERIOD_M5, 1),
                          GetRSI(1));

   status += StringFormat("M1  - Stoch K: %.2f | Stoch D: %.2f | ATR: %.5f",
                          GetStochK(1), GetStochD(1), GetATR(1));

   return status;
}
//+------------------------------------------------------------------+
