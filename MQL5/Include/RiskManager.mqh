//+------------------------------------------------------------------+
//|                                                  RiskManager.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

#include "Constants.mqh"

//+------------------------------------------------------------------+
//| Clase para Gestión de Riesgo                                      |
//+------------------------------------------------------------------+
class CRiskManager
{
private:
   // Parámetros de riesgo
   double            m_max_drawdown;           // Drawdown máximo permitido (%)
   double            m_max_daily_drawdown;     // Drawdown diario máximo (%)
   int               m_max_daily_operations;   // Operaciones máximas por día
   double            m_risk_per_trade;         // Riesgo por operación (%)
   double            m_max_spread;             // Spread máximo permitido

   // Estado actual
   double            m_initial_balance;        // Balance inicial de la cuenta
   double            m_daily_start_balance;    // Balance al inicio del día
   datetime          m_daily_start_date;       // Fecha del inicio del día
   int               m_daily_operations;       // Operaciones del día
   double            m_current_drawdown;       // Drawdown actual
   double            m_daily_drawdown;         // Drawdown diario actual
   double            m_max_equity_reached;     // Máximo equity alcanzado
   double            m_daily_max_equity;       // Máximo equity del día

   // Magic number para identificar operaciones propias
   long              m_magic_number;

   // Actualizar drawdown
   void              UpdateDrawdown();

public:
   // Constructor y destructor
                     CRiskManager();
                    ~CRiskManager();

   // Inicialización
   bool              Init(double max_dd, double max_daily_dd, int max_daily_ops,
                          double risk_per_trade, double max_spread, long magic);

   // Actualización diaria
   void              NewDayReset();
   void              Update();

   // Verificaciones de riesgo
   bool              CanTrade();
   bool              IsDrawdownExceeded();
   bool              IsDailyDrawdownExceeded();
   bool              IsDailyOperationsExceeded();
   bool              IsSpreadAcceptable(string symbol);

   // Cálculo de lote
   double            CalculateLotSize(string symbol, int sl_pips);
   double            NormalizeLot(string symbol, double lot);

   // Getters
   double            GetCurrentDrawdown()      { return m_current_drawdown; }
   double            GetDailyDrawdown()        { return m_daily_drawdown; }
   int               GetDailyOperations()      { return m_daily_operations; }
   double            GetMaxDrawdown()          { return m_max_drawdown; }
   double            GetMaxDailyDrawdown()     { return m_max_daily_drawdown; }
   int               GetMaxDailyOperations()   { return m_max_daily_operations; }
   double            GetRiskPerTrade()         { return m_risk_per_trade; }

   // Incrementar contador de operaciones
   void              IncrementDailyOperations() { m_daily_operations++; }

   // Obtener estado del bot basado en riesgo
   ENUM_BOT_STATUS   GetRiskStatus();

   // Obtener información de cuenta
   AccountInfo       GetAccountInfo();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CRiskManager::CRiskManager()
{
   m_max_drawdown = 10.0;
   m_max_daily_drawdown = 5.0;
   m_max_daily_operations = 10;
   m_risk_per_trade = 1.0;
   m_max_spread = 3.0;
   m_magic_number = 0;

   m_initial_balance = 0;
   m_daily_start_balance = 0;
   m_daily_start_date = 0;
   m_daily_operations = 0;
   m_current_drawdown = 0;
   m_daily_drawdown = 0;
   m_max_equity_reached = 0;
   m_daily_max_equity = 0;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CRiskManager::~CRiskManager()
{
}

//+------------------------------------------------------------------+
//| Inicialización del gestor de riesgo                               |
//+------------------------------------------------------------------+
bool CRiskManager::Init(double max_dd, double max_daily_dd, int max_daily_ops,
                        double risk_per_trade, double max_spread, long magic)
{
   m_max_drawdown = max_dd;
   m_max_daily_drawdown = max_daily_dd;
   m_max_daily_operations = max_daily_ops;
   m_risk_per_trade = risk_per_trade;
   m_max_spread = max_spread;
   m_magic_number = magic;

   // Obtener balance inicial
   m_initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   m_daily_start_balance = m_initial_balance;
   m_daily_start_date = TimeCurrent();
   m_max_equity_reached = AccountInfoDouble(ACCOUNT_EQUITY);
   m_daily_max_equity = m_max_equity_reached;
   m_daily_operations = 0;

   // Contar operaciones existentes del día
   datetime today_start = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));

   if(HistorySelect(today_start, TimeCurrent()))
   {
      int total = HistoryDealsTotal();
      for(int i = 0; i < total; i++)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == m_magic_number)
         {
            ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);
            if(entry == DEAL_ENTRY_IN)
               m_daily_operations++;
         }
      }
   }

   Print("RiskManager inicializado - Balance: ", m_initial_balance,
         " | DD Max: ", m_max_drawdown, "% | DD Diario Max: ", m_max_daily_drawdown,
         "% | Ops Diarias Max: ", m_max_daily_operations);

   return true;
}

//+------------------------------------------------------------------+
//| Reset diario                                                      |
//+------------------------------------------------------------------+
void CRiskManager::NewDayReset()
{
   datetime current_date = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));
   datetime stored_date = StringToTime(TimeToString(m_daily_start_date, TIME_DATE));

   if(current_date > stored_date)
   {
      m_daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
      m_daily_start_date = TimeCurrent();
      m_daily_operations = 0;
      m_daily_max_equity = AccountInfoDouble(ACCOUNT_EQUITY);
      m_daily_drawdown = 0;

      Print("Nuevo día detectado - Reset de estadísticas diarias. Balance: ", m_daily_start_balance);
   }
}

//+------------------------------------------------------------------+
//| Actualización de estado                                           |
//+------------------------------------------------------------------+
void CRiskManager::Update()
{
   // Verificar si es nuevo día
   NewDayReset();

   // Actualizar drawdown
   UpdateDrawdown();
}

//+------------------------------------------------------------------+
//| Actualizar cálculos de drawdown                                   |
//+------------------------------------------------------------------+
void CRiskManager::UpdateDrawdown()
{
   double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);

   // Actualizar máximo equity alcanzado
   if(current_equity > m_max_equity_reached)
      m_max_equity_reached = current_equity;

   // Actualizar máximo equity diario
   if(current_equity > m_daily_max_equity)
      m_daily_max_equity = current_equity;

   // Calcular drawdown desde máximo
   if(m_max_equity_reached > 0)
      m_current_drawdown = ((m_max_equity_reached - current_equity) / m_max_equity_reached) * 100;
   else
      m_current_drawdown = 0;

   // Calcular drawdown diario
   if(m_daily_start_balance > 0)
   {
      double daily_loss = m_daily_start_balance - current_equity;
      if(daily_loss > 0)
         m_daily_drawdown = (daily_loss / m_daily_start_balance) * 100;
      else
         m_daily_drawdown = 0;
   }
}

//+------------------------------------------------------------------+
//| Verificar si se puede operar                                      |
//+------------------------------------------------------------------+
bool CRiskManager::CanTrade()
{
   Update();

   if(IsDrawdownExceeded())
   {
      Print("Trading bloqueado: Drawdown máximo excedido (", m_current_drawdown, "%)");
      return false;
   }

   if(IsDailyDrawdownExceeded())
   {
      Print("Trading bloqueado: Drawdown diario excedido (", m_daily_drawdown, "%)");
      return false;
   }

   if(IsDailyOperationsExceeded())
   {
      Print("Trading bloqueado: Máximo de operaciones diarias alcanzado (", m_daily_operations, ")");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Verificar si drawdown máximo excedido                             |
//+------------------------------------------------------------------+
bool CRiskManager::IsDrawdownExceeded()
{
   return m_current_drawdown >= m_max_drawdown;
}

//+------------------------------------------------------------------+
//| Verificar si drawdown diario excedido                             |
//+------------------------------------------------------------------+
bool CRiskManager::IsDailyDrawdownExceeded()
{
   return m_daily_drawdown >= m_max_daily_drawdown;
}

//+------------------------------------------------------------------+
//| Verificar si operaciones diarias excedidas                        |
//+------------------------------------------------------------------+
bool CRiskManager::IsDailyOperationsExceeded()
{
   return m_daily_operations >= m_max_daily_operations;
}

//+------------------------------------------------------------------+
//| Verificar si spread es aceptable                                  |
//+------------------------------------------------------------------+
bool CRiskManager::IsSpreadAcceptable(string symbol)
{
   double spread_points = SymbolInfoInteger(symbol, SYMBOL_SPREAD);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   // Convertir spread a pips
   double spread_pips;
   if(digits == 5 || digits == 3)
      spread_pips = spread_points / 10.0;
   else
      spread_pips = spread_points;

   if(spread_pips > m_max_spread)
   {
      Print("Spread alto: ", spread_pips, " pips > ", m_max_spread, " pips máximo");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Calcular tamaño de lote basado en riesgo                          |
//+------------------------------------------------------------------+
double CRiskManager::CalculateLotSize(string symbol, int sl_pips)
{
   if(sl_pips <= 0) return MIN_LOT_SIZE;

   double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = account_balance * (m_risk_per_trade / 100.0);

   // Obtener valor del tick
   double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);

   if(tick_value == 0 || tick_size == 0) return MIN_LOT_SIZE;

   // Calcular valor del pip
   double pip_value = tick_value * (GetPipMultiplier(symbol) / tick_size);

   // Calcular lote
   double lot_size = risk_amount / (sl_pips * pip_value);

   // Normalizar lote
   lot_size = NormalizeLot(symbol, lot_size);

   Print("Cálculo de lote - Balance: ", account_balance, " | Riesgo: ", risk_amount,
         " | SL: ", sl_pips, " pips | Lote: ", lot_size);

   return lot_size;
}

//+------------------------------------------------------------------+
//| Normalizar tamaño de lote según especificaciones del símbolo      |
//+------------------------------------------------------------------+
double CRiskManager::NormalizeLot(string symbol, double lot)
{
   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lot_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   // Asegurar mínimo
   if(lot < min_lot) lot = min_lot;

   // Asegurar máximo
   if(lot > max_lot) lot = max_lot;

   // Redondear al step más cercano
   if(lot_step > 0)
      lot = MathFloor(lot / lot_step) * lot_step;

   // Redondear a 2 decimales
   lot = NormalizeDouble(lot, 2);

   return lot;
}

//+------------------------------------------------------------------+
//| Obtener estado del bot basado en riesgo                           |
//+------------------------------------------------------------------+
ENUM_BOT_STATUS CRiskManager::GetRiskStatus()
{
   if(IsDrawdownExceeded())
      return BOT_STATUS_DD_LIMIT;

   if(IsDailyDrawdownExceeded())
      return BOT_STATUS_DAILY_DD_LIMIT;

   if(IsDailyOperationsExceeded())
      return BOT_STATUS_DAILY_OPS_LIMIT;

   return BOT_STATUS_ACTIVE;
}

//+------------------------------------------------------------------+
//| Obtener información de cuenta                                     |
//+------------------------------------------------------------------+
AccountInfo CRiskManager::GetAccountInfo()
{
   AccountInfo info;

   info.balance = AccountInfoDouble(ACCOUNT_BALANCE);
   info.equity = AccountInfoDouble(ACCOUNT_EQUITY);
   info.margin = AccountInfoDouble(ACCOUNT_MARGIN);
   info.free_margin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   info.profit = AccountInfoDouble(ACCOUNT_PROFIT);
   info.open_positions = PositionsTotal();
   info.drawdown = m_current_drawdown;
   info.daily_drawdown = m_daily_drawdown;
   info.bot_status = GetRiskStatus();

   return info;
}
//+------------------------------------------------------------------+
