//+------------------------------------------------------------------+
//|                                                    Constants.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

//+------------------------------------------------------------------+
//| Enumeraciones del Sistema                                         |
//+------------------------------------------------------------------+

// Estados del Bot
enum ENUM_BOT_STATUS
{
   BOT_STATUS_ACTIVE,           // Bot activo y operando
   BOT_STATUS_PAUSED,           // Bot pausado manualmente
   BOT_STATUS_WAITING,          // Esperando señal
   BOT_STATUS_DD_LIMIT,         // Pausado por drawdown máximo
   BOT_STATUS_DAILY_DD_LIMIT,   // Pausado por drawdown diario
   BOT_STATUS_DAILY_OPS_LIMIT,  // Pausado por máximo de operaciones
   BOT_STATUS_NEWS_FILTER,      // Pausado por noticias
   BOT_STATUS_SESSION_CLOSED,   // Fuera de horario de sesión
   BOT_STATUS_SPREAD_HIGH,      // Spread muy alto
   BOT_STATUS_ERROR             // Error del sistema
};

// Tipos de Señal
enum ENUM_SIGNAL_TYPE
{
   SIGNAL_NONE,                 // Sin señal
   SIGNAL_BUY,                  // Señal de compra
   SIGNAL_SELL                  // Señal de venta
};

// Estados de la Operación
enum ENUM_TRADE_STATE
{
   TRADE_STATE_NONE,            // Sin operación
   TRADE_STATE_OPEN,            // Operación abierta
   TRADE_STATE_PARTIAL_CLOSE,   // Cierre parcial ejecutado
   TRADE_STATE_BREAK_EVEN,      // Break-even activado
   TRADE_STATE_CLOSED           // Operación cerrada
};

// Sesiones de Trading
enum ENUM_TRADING_SESSION
{
   SESSION_NONE,                // Fuera de sesión
   SESSION_LONDON,              // Sesión de Londres
   SESSION_NEW_YORK,            // Sesión de Nueva York
   SESSION_OVERLAP              // Solapamiento Londres-NY
};

// Impacto de Noticias
enum ENUM_NEWS_IMPACT
{
   NEWS_IMPACT_NONE,            // Sin noticias
   NEWS_IMPACT_LOW,             // Bajo impacto
   NEWS_IMPACT_MEDIUM,          // Impacto medio
   NEWS_IMPACT_HIGH             // Alto impacto
};

// Tipos de Mensaje Socket
enum ENUM_MESSAGE_TYPE
{
   MSG_TYPE_STATUS,             // Estado del bot
   MSG_TYPE_TRADE,              // Información de trade
   MSG_TYPE_SIGNAL,             // Señal de trading
   MSG_TYPE_COMMAND,            // Comando de control
   MSG_TYPE_HEARTBEAT,          // Latido de conexión
   MSG_TYPE_ERROR               // Mensaje de error
};

//+------------------------------------------------------------------+
//| Constantes Globales                                               |
//+------------------------------------------------------------------+

// Versión del Bot
#define BOT_VERSION              "1.0.0"
#define BOT_NAME                 "MultiTF_Scalper"

// Timeframes utilizados
#define TF_ENTRY                 PERIOD_M1
#define TF_CONFIRMATION          PERIOD_M5
#define TF_TREND                 PERIOD_M15

// Valores por defecto de indicadores
#define DEFAULT_EMA_FAST         9
#define DEFAULT_EMA_SLOW         21
#define DEFAULT_RSI_PERIOD       14
#define DEFAULT_STOCH_K          5
#define DEFAULT_STOCH_D          3
#define DEFAULT_STOCH_SLOWING    3
#define DEFAULT_ATR_PERIOD       14

// Zonas de Stochastic
#define STOCH_OVERSOLD           20
#define STOCH_OVERBOUGHT         80

// Rangos de RSI para filtro
#define RSI_BUY_MIN              40
#define RSI_BUY_MAX              70
#define RSI_SELL_MIN             30
#define RSI_SELL_MAX             60

// Comunicación
#define SOCKET_TIMEOUT_MS        5000
#define HEARTBEAT_INTERVAL_SEC   30
#define MAX_MESSAGE_SIZE         4096

// Conversión de pips
#define PIP_MULTIPLIER_4DIGITS   0.0001
#define PIP_MULTIPLIER_2DIGITS   0.01
#define PIP_MULTIPLIER_3DIGITS   0.001
#define PIP_MULTIPLIER_5DIGITS   0.00001

// Límites de seguridad
#define MIN_LOT_SIZE             0.01
#define MAX_SPREAD_DEFAULT       3.0
#define MIN_EQUITY_PERCENT       50.0

// Intervalos de actualización (ms)
#define UPDATE_INTERVAL_MS       1000
#define STATUS_SEND_INTERVAL_MS  5000

//+------------------------------------------------------------------+
//| Estructuras de Datos                                              |
//+------------------------------------------------------------------+

// Estructura para información de señal
struct SignalInfo
{
   ENUM_SIGNAL_TYPE  type;           // Tipo de señal
   string            symbol;         // Símbolo
   double            entry_price;    // Precio de entrada
   double            stop_loss;      // Stop loss
   double            take_profit1;   // Take profit 1 (parcial)
   double            take_profit2;   // Take profit 2 (final)
   double            lot_size;       // Tamaño de lote
   datetime          signal_time;    // Hora de la señal
   int               sl_pips;        // SL en pips
   int               tp1_pips;       // TP1 en pips
   int               tp2_pips;       // TP2 en pips
   string            comment;        // Comentario
};

// Estructura para estado de operación
struct TradeInfo
{
   ulong             ticket;         // Ticket de la orden
   ENUM_TRADE_STATE  state;          // Estado actual
   ENUM_SIGNAL_TYPE  type;           // Tipo (buy/sell)
   string            symbol;         // Símbolo
   double            open_price;     // Precio de apertura
   double            current_price;  // Precio actual
   double            stop_loss;      // Stop loss
   double            take_profit;    // Take profit actual
   double            initial_volume; // Volumen inicial
   double            current_volume; // Volumen actual
   double            profit;         // Beneficio actual
   datetime          open_time;      // Hora de apertura
   bool              partial_closed; // Si ya se cerró parcialmente
   bool              break_even_set; // Si ya se puso break-even
};

// Estructura para estadísticas diarias
struct DailyStats
{
   datetime          date;           // Fecha
   int               total_trades;   // Total de operaciones
   int               winning_trades; // Operaciones ganadoras
   int               losing_trades;  // Operaciones perdedoras
   double            gross_profit;   // Beneficio bruto
   double            gross_loss;     // Pérdida bruta
   double            net_profit;     // Beneficio neto
   double            max_drawdown;   // Drawdown máximo del día
   double            start_balance;  // Balance inicial del día
   double            current_balance;// Balance actual
};

// Estructura para información de cuenta
struct AccountInfo
{
   double            balance;        // Balance
   double            equity;         // Equity
   double            margin;         // Margen usado
   double            free_margin;    // Margen libre
   double            profit;         // Beneficio flotante
   int               open_positions; // Posiciones abiertas
   double            drawdown;       // Drawdown actual (%)
   double            daily_drawdown; // Drawdown diario (%)
   ENUM_BOT_STATUS   bot_status;     // Estado del bot
};

// Estructura para evento de noticias
struct NewsEvent
{
   datetime          event_time;     // Hora del evento
   string            currency;       // Moneda afectada
   string            event_name;     // Nombre del evento
   ENUM_NEWS_IMPACT  impact;         // Impacto
   bool              is_blocking;    // Si bloquea trading
};

// Estructura para configuración de sesión
struct SessionConfig
{
   int               london_start_hour;
   int               london_end_hour;
   int               ny_start_hour;
   int               ny_end_hour;
   int               news_buffer_minutes;
};

//+------------------------------------------------------------------+
//| Funciones de Utilidad                                             |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Convierte estado del bot a string                                 |
//+------------------------------------------------------------------+
string BotStatusToString(ENUM_BOT_STATUS status)
{
   switch(status)
   {
      case BOT_STATUS_ACTIVE:          return "ACTIVE";
      case BOT_STATUS_PAUSED:          return "PAUSED";
      case BOT_STATUS_WAITING:         return "WAITING";
      case BOT_STATUS_DD_LIMIT:        return "DD_LIMIT";
      case BOT_STATUS_DAILY_DD_LIMIT:  return "DAILY_DD_LIMIT";
      case BOT_STATUS_DAILY_OPS_LIMIT: return "DAILY_OPS_LIMIT";
      case BOT_STATUS_NEWS_FILTER:     return "NEWS_FILTER";
      case BOT_STATUS_SESSION_CLOSED:  return "SESSION_CLOSED";
      case BOT_STATUS_SPREAD_HIGH:     return "SPREAD_HIGH";
      case BOT_STATUS_ERROR:           return "ERROR";
      default:                         return "UNKNOWN";
   }
}

//+------------------------------------------------------------------+
//| Convierte tipo de señal a string                                  |
//+------------------------------------------------------------------+
string SignalTypeToString(ENUM_SIGNAL_TYPE signal)
{
   switch(signal)
   {
      case SIGNAL_BUY:  return "BUY";
      case SIGNAL_SELL: return "SELL";
      default:          return "NONE";
   }
}

//+------------------------------------------------------------------+
//| Convierte string a tipo de señal                                  |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE StringToSignalType(string signal)
{
   if(signal == "BUY")  return SIGNAL_BUY;
   if(signal == "SELL") return SIGNAL_SELL;
   return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| Obtiene multiplicador de pip según dígitos del símbolo            |
//+------------------------------------------------------------------+
double GetPipMultiplier(string symbol)
{
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   if(digits == 5 || digits == 3)
      return (digits == 5) ? PIP_MULTIPLIER_5DIGITS * 10 : PIP_MULTIPLIER_3DIGITS * 10;
   else if(digits == 4 || digits == 2)
      return (digits == 4) ? PIP_MULTIPLIER_4DIGITS : PIP_MULTIPLIER_2DIGITS;

   return PIP_MULTIPLIER_4DIGITS;
}

//+------------------------------------------------------------------+
//| Convierte pips a precio                                           |
//+------------------------------------------------------------------+
double PipsToPrice(string symbol, int pips)
{
   return pips * GetPipMultiplier(symbol);
}

//+------------------------------------------------------------------+
//| Convierte precio a pips                                           |
//+------------------------------------------------------------------+
int PriceToPips(string symbol, double price_diff)
{
   double pip_mult = GetPipMultiplier(symbol);
   if(pip_mult == 0) return 0;
   return (int)MathRound(price_diff / pip_mult);
}

//+------------------------------------------------------------------+
//| Obtiene timestamp actual en formato Unix                          |
//+------------------------------------------------------------------+
long GetUnixTimestamp()
{
   return (long)TimeCurrent();
}
//+------------------------------------------------------------------+
