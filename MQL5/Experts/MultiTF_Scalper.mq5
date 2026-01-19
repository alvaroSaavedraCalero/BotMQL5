//+------------------------------------------------------------------+
//|                                              MultiTF_Scalper.mq5 |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property version   "1.00"
#property description "Multi-Timeframe Scalping Bot with Python Integration"
#property strict

//+------------------------------------------------------------------+
//| Includes                                                          |
//+------------------------------------------------------------------+
#include "../Include/Constants.mqh"
#include "../Include/RiskManager.mqh"
#include "../Include/SessionManager.mqh"
#include "../Include/TradeManager.mqh"
#include "../Include/SignalEngine.mqh"
#include "../Include/SocketClient.mqh"
#include "../Libraries/JsonParser.mqh"

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
// === GESTIÓN DE RIESGO ===
input group "=== Gestión de Riesgo ==="
input double   InpMaxDrawDown        = 10.0;    // Drawdown máximo cuenta (%)
input double   InpMaxDailyDrawDown   = 5.0;     // Drawdown máximo diario (%)
input int      InpMaxDailyOperations = 10;      // Operaciones máximas por día
input double   InpRiskPerTrade       = 1.0;     // Riesgo por operación (%)

// === CONFIGURACIÓN DE TRADING ===
input group "=== Configuración de Trading ==="
input int      InpStopLossPips       = 12;      // Stop Loss (pips) [10-15]
input double   InpRR_Partial         = 2.0;     // R:R para cierre parcial
input double   InpRR_Final           = 3.0;     // R:R para cierre total
input double   InpPartialClosePercent= 50.0;    // % de cierre parcial
input int      InpSlippage           = 3;       // Slippage máximo (puntos)
input double   InpSpreadMaximo       = 2.0;     // Spread máximo (pips)

// === SESIONES ===
input group "=== Horarios de Sesión ==="
input int      InpLondonStartHour    = 10;      // Inicio sesión Londres (hora servidor)
input int      InpLondonEndHour      = 14;      // Fin sesión Londres
input int      InpNYStartHour        = 15;      // Inicio sesión New York
input int      InpNYEndHour          = 19;      // Fin sesión New York

// === NOTICIAS ===
input group "=== Filtro de Noticias ==="
input int      InpNewsBufferMinutes  = 45;      // Minutos antes/después de noticias
input bool     InpUseNewsFilter      = true;    // Usar filtro de noticias

// === INDICADORES ===
input group "=== Parámetros de Indicadores ==="
input int      InpEMA_Fast           = 9;       // EMA rápida
input int      InpEMA_Slow           = 21;      // EMA lenta
input int      InpRSI_Period         = 14;      // Período RSI
input int      InpStoch_K            = 5;       // Stochastic %K
input int      InpStoch_D            = 3;       // Stochastic %D
input int      InpStoch_Slowing      = 3;       // Stochastic Slowing
input int      InpATR_Period         = 14;      // Período ATR

// === SISTEMA ===
input group "=== Configuración del Sistema ==="
input long     InpMagicNumber        = 123456;  // Magic Number
input bool     InpUsePythonSignals   = true;    // Recibir señales de Python
input bool     InpSendStatusToPython = true;    // Enviar estado a Python

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
// Managers
CRiskManager      g_riskManager;
CSessionManager   g_sessionManager;
CTradeManager     g_tradeManager;
CSignalEngine     g_signalEngine;
CSocketClient     g_socketClient;

// Estado del bot
ENUM_BOT_STATUS   g_botStatus = BOT_STATUS_WAITING;
bool              g_isInitialized = false;
bool              g_isPaused = false;
datetime          g_lastBarTime = 0;
datetime          g_lastStatusUpdate = 0;

// Estadísticas diarias
DailyStats        g_dailyStats;

// Control de noticias (simplificado - en producción usar calendario real)
datetime          g_nextNewsTime = 0;
bool              g_newsBlockActive = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("=== Iniciando ", BOT_NAME, " v", BOT_VERSION, " ===");

   // Validar parámetros
   if(InpStopLossPips < 5 || InpStopLossPips > 50)
   {
      Print("Error: Stop Loss debe estar entre 5 y 50 pips");
      return INIT_PARAMETERS_INCORRECT;
   }

   if(InpRiskPerTrade <= 0 || InpRiskPerTrade > 5)
   {
      Print("Error: Riesgo por operación debe estar entre 0.1% y 5%");
      return INIT_PARAMETERS_INCORRECT;
   }

   // Inicializar Risk Manager
   if(!g_riskManager.Init(InpMaxDrawDown, InpMaxDailyDrawDown, InpMaxDailyOperations,
                          InpRiskPerTrade, InpSpreadMaximo, InpMagicNumber))
   {
      Print("Error inicializando Risk Manager");
      return INIT_FAILED;
   }

   // Inicializar Session Manager
   if(!g_sessionManager.Init(InpLondonStartHour, InpLondonEndHour,
                             InpNYStartHour, InpNYEndHour))
   {
      Print("Error inicializando Session Manager");
      return INIT_FAILED;
   }

   // Inicializar Trade Manager
   if(!g_tradeManager.Init(InpMagicNumber, InpSlippage, InpStopLossPips,
                           InpRR_Partial, InpRR_Final, InpPartialClosePercent))
   {
      Print("Error inicializando Trade Manager");
      return INIT_FAILED;
   }

   // Inicializar Signal Engine
   if(!g_signalEngine.Init(_Symbol, InpEMA_Fast, InpEMA_Slow, InpRSI_Period,
                           InpStoch_K, InpStoch_D, InpStoch_Slowing, InpATR_Period))
   {
      Print("Error inicializando Signal Engine");
      return INIT_FAILED;
   }

   // Inicializar Socket Client para comunicación con Python
   if(InpUsePythonSignals || InpSendStatusToPython)
   {
      if(!g_socketClient.Init())
      {
         Print("Advertencia: No se pudo inicializar Socket Client");
         // No es fatal, el bot puede funcionar sin Python
      }
      else
      {
         g_socketClient.Connect();
      }
   }

   // Inicializar estadísticas diarias
   ResetDailyStats();

   g_isInitialized = true;
   g_botStatus = BOT_STATUS_WAITING;

   Print("=== ", BOT_NAME, " inicializado correctamente ===");
   Print("Símbolo: ", _Symbol, " | Magic: ", InpMagicNumber);
   Print("Riesgo: ", InpRiskPerTrade, "% | SL: ", InpStopLossPips, " pips");
   Print("Sesiones: Londres ", InpLondonStartHour, "-", InpLondonEndHour,
         " | NY ", InpNYStartHour, "-", InpNYEndHour);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Liberar recursos
   g_signalEngine.Deinit();
   g_socketClient.Disconnect();

   Print("=== ", BOT_NAME, " detenido. Razón: ", reason, " ===");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!g_isInitialized) return;

   // Actualizar managers
   g_riskManager.Update();
   g_sessionManager.Update();

   // Gestionar operaciones abiertas (siempre, independiente del estado)
   g_tradeManager.ManageOpenTrades();

   // Actualizar comunicación con Python
   if(InpSendStatusToPython)
   {
      UpdatePythonStatus();
   }

   // Verificar señales de Python
   if(InpUsePythonSignals)
   {
      CheckPythonSignals();
   }

   // Verificar si podemos operar
   if(!CanTrade())
   {
      return;
   }

   // Solo analizar en nueva barra de M1
   if(!IsNewBar(PERIOD_M1))
      return;

   // Buscar señal
   ENUM_SIGNAL_TYPE signal = g_signalEngine.GetSignal();

   if(signal != SIGNAL_NONE)
   {
      ExecuteSignal(signal);
   }
}

//+------------------------------------------------------------------+
//| Verificar si podemos operar                                       |
//+------------------------------------------------------------------+
bool CanTrade()
{
   // Verificar si está pausado manualmente
   if(g_isPaused)
   {
      g_botStatus = BOT_STATUS_PAUSED;
      return false;
   }

   // Verificar gestión de riesgo
   if(!g_riskManager.CanTrade())
   {
      g_botStatus = g_riskManager.GetRiskStatus();
      return false;
   }

   // Verificar sesión de trading
   if(!g_sessionManager.IsTradingSession())
   {
      g_botStatus = BOT_STATUS_SESSION_CLOSED;
      return false;
   }

   // Verificar spread
   if(!g_riskManager.IsSpreadAcceptable(_Symbol))
   {
      g_botStatus = BOT_STATUS_SPREAD_HIGH;
      return false;
   }

   // Verificar noticias
   if(InpUseNewsFilter && IsNewsBlocking())
   {
      g_botStatus = BOT_STATUS_NEWS_FILTER;
      return false;
   }

   // Verificar si ya hay posición abierta
   if(g_tradeManager.HasOpenPosition(_Symbol))
   {
      g_botStatus = BOT_STATUS_ACTIVE;
      return false; // Ya tenemos posición, no abrir más
   }

   g_botStatus = BOT_STATUS_WAITING;
   return true;
}

//+------------------------------------------------------------------+
//| Ejecutar señal                                                    |
//+------------------------------------------------------------------+
void ExecuteSignal(ENUM_SIGNAL_TYPE signal_type)
{
   // Calcular tamaño de lote
   double lot_size = g_riskManager.CalculateLotSize(_Symbol, InpStopLossPips);

   if(lot_size <= 0)
   {
      Print("Error: Tamaño de lote inválido");
      return;
   }

   // Generar información de señal
   SignalInfo signal = g_signalEngine.GenerateSignalInfo(signal_type, lot_size, InpStopLossPips);

   // Ejecutar trade
   if(g_tradeManager.OpenTrade(signal))
   {
      g_botStatus = BOT_STATUS_ACTIVE;
      g_riskManager.IncrementDailyOperations();
      g_dailyStats.total_trades++;

      // Enviar a Python
      if(InpSendStatusToPython)
      {
         TradeInfo trade_info;
         // Obtener info del último trade abierto
         TradeInfo trades[];
         g_tradeManager.GetAllActiveTrades(trades);
         if(ArraySize(trades) > 0)
         {
            g_socketClient.SendTradeOpen(trades[ArraySize(trades) - 1]);
         }
      }

      Print("Trade ejecutado: ", SignalTypeToString(signal_type), " ", _Symbol,
            " @ ", signal.entry_price, " | Lote: ", lot_size);
   }
   else
   {
      Print("Error ejecutando trade: ", g_tradeManager.GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Verificar si hay nueva barra                                      |
//+------------------------------------------------------------------+
bool IsNewBar(ENUM_TIMEFRAMES tf)
{
   datetime current_bar_time = iTime(_Symbol, tf, 0);

   if(current_bar_time != g_lastBarTime)
   {
      g_lastBarTime = current_bar_time;
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Verificar si hay bloqueo por noticias                             |
//+------------------------------------------------------------------+
bool IsNewsBlocking()
{
   // Implementación simplificada
   // En producción, esto debería consultar el calendario económico real
   // que se maneja desde Python

   // Por ahora, verificar el archivo de noticias de Python
   // Python escribe las próximas noticias en un archivo

   return g_newsBlockActive;
}

//+------------------------------------------------------------------+
//| Actualizar estado a Python                                        |
//+------------------------------------------------------------------+
void UpdatePythonStatus()
{
   // Solo actualizar cada 5 segundos
   if(TimeCurrent() - g_lastStatusUpdate < 5)
      return;

   g_lastStatusUpdate = TimeCurrent();

   AccountInfo account = g_riskManager.GetAccountInfo();
   account.bot_status = g_botStatus;

   g_socketClient.SendStatus(account, g_dailyStats, g_sessionManager.GetSessionName());
   g_socketClient.Update();
}

//+------------------------------------------------------------------+
//| Verificar señales de Python                                       |
//+------------------------------------------------------------------+
void CheckPythonSignals()
{
   // Verificar comandos
   if(g_socketClient.HasCommand())
   {
      string cmd = g_socketClient.ReadCommand();
      ProcessCommand(cmd);
   }

   // Verificar señales de trading
   if(g_socketClient.HasIncomingSignal())
   {
      SignalInfo signal;
      if(g_socketClient.ReadSignal(signal))
      {
         // Verificar que el símbolo coincida
         if(signal.symbol == _Symbol || signal.symbol == "")
         {
            // Calcular lote si no viene especificado
            if(signal.lot_size <= 0)
            {
               signal.lot_size = g_riskManager.CalculateLotSize(_Symbol,
                                 signal.sl_pips > 0 ? signal.sl_pips : InpStopLossPips);
            }

            // Ejecutar señal de Python
            if(CanTrade())
            {
               g_tradeManager.OpenTrade(signal);
               g_riskManager.IncrementDailyOperations();
               g_dailyStats.total_trades++;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Procesar comando de Python                                        |
//+------------------------------------------------------------------+
void ProcessCommand(string command)
{
   if(command == "PAUSE")
   {
      g_isPaused = true;
      Print("Bot pausado por comando de Python");
   }
   else if(command == "RESUME")
   {
      g_isPaused = false;
      Print("Bot reanudado por comando de Python");
   }
   else if(command == "CLOSE_ALL")
   {
      CloseAllPositions();
   }
   else if(command == "STATUS")
   {
      // Forzar actualización de estado
      g_lastStatusUpdate = 0;
      UpdatePythonStatus();
   }
   else if(StringFind(command, "NEWS_BLOCK:") == 0)
   {
      // Formato: NEWS_BLOCK:1 o NEWS_BLOCK:0
      string value = StringSubstr(command, 11);
      g_newsBlockActive = (value == "1");
      Print("Bloqueo por noticias: ", g_newsBlockActive ? "ACTIVO" : "INACTIVO");
   }
}

//+------------------------------------------------------------------+
//| Cerrar todas las posiciones                                       |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   TradeInfo trades[];
   g_tradeManager.GetAllActiveTrades(trades);

   for(int i = 0; i < ArraySize(trades); i++)
   {
      g_tradeManager.CloseTrade(trades[i].ticket, "Cierre por comando");
   }

   Print("Todas las posiciones cerradas");
}

//+------------------------------------------------------------------+
//| Resetear estadísticas diarias                                     |
//+------------------------------------------------------------------+
void ResetDailyStats()
{
   g_dailyStats.date = TimeCurrent();
   g_dailyStats.total_trades = 0;
   g_dailyStats.winning_trades = 0;
   g_dailyStats.losing_trades = 0;
   g_dailyStats.gross_profit = 0;
   g_dailyStats.gross_loss = 0;
   g_dailyStats.net_profit = 0;
   g_dailyStats.max_drawdown = 0;
   g_dailyStats.start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_dailyStats.current_balance = g_dailyStats.start_balance;
}

//+------------------------------------------------------------------+
//| Trade transaction handler                                         |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
   // Detectar cierre de posiciones para actualizar estadísticas
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      ulong deal_ticket = trans.deal;

      if(HistoryDealSelect(deal_ticket))
      {
         long magic = HistoryDealGetInteger(deal_ticket, DEAL_MAGIC);

         if(magic == InpMagicNumber)
         {
            ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);

            if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
            {
               double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);

               if(profit > 0)
               {
                  g_dailyStats.winning_trades++;
                  g_dailyStats.gross_profit += profit;
               }
               else
               {
                  g_dailyStats.losing_trades++;
                  g_dailyStats.gross_loss += MathAbs(profit);
               }

               g_dailyStats.net_profit = g_dailyStats.gross_profit - g_dailyStats.gross_loss;
               g_dailyStats.current_balance = AccountInfoDouble(ACCOUNT_BALANCE);

               // Enviar cierre a Python
               if(InpSendStatusToPython)
               {
                  g_socketClient.SendTradeClose(trans.position, profit, "Normal close");
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Timer function (opcional, para actualizaciones periódicas)        |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Actualizar estado periódicamente
   UpdatePythonStatus();
}

//+------------------------------------------------------------------+
//| Chart event handler                                               |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   // Manejar eventos del gráfico si es necesario
   // Por ejemplo, botones de control visual
}
//+------------------------------------------------------------------+
