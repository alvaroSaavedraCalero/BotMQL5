//+------------------------------------------------------------------+
//|                                                 TradeManager.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include "Constants.mqh"

//+------------------------------------------------------------------+
//| Clase para Gestión de Operaciones                                 |
//+------------------------------------------------------------------+
class CTradeManager
{
private:
   // Objetos de trading
   CTrade            m_trade;
   CPositionInfo     m_position;

   // Parámetros de configuración
   long              m_magic_number;
   int               m_slippage;
   int               m_sl_pips;
   double            m_rr_partial;             // R:R para cierre parcial
   double            m_rr_final;               // R:R para cierre total
   double            m_partial_close_percent;  // % de cierre parcial

   // Estado de operaciones activas
   TradeInfo         m_active_trades[];        // Array de trades activos
   int               m_active_count;           // Contador de trades activos

   // Métodos privados
   double            CalculateSL(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol);
   double            CalculateTP1(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol);
   double            CalculateTP2(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol);
   bool              UpdateTradeInfo(ulong ticket);
   int               FindTradeIndex(ulong ticket);

public:
   // Constructor y destructor
                     CTradeManager();
                    ~CTradeManager();

   // Inicialización
   bool              Init(long magic, int slippage, int sl_pips,
                          double rr_partial, double rr_final, double partial_percent);

   // Operaciones de trading
   bool              OpenTrade(SignalInfo &signal);
   bool              CloseTrade(ulong ticket, string reason = "");
   bool              ClosePartial(ulong ticket, double percent);
   bool              SetBreakEven(ulong ticket);
   bool              ModifyStopLoss(ulong ticket, double new_sl);
   bool              ModifyTakeProfit(ulong ticket, double new_tp);

   // Gestión de operaciones abiertas
   void              ManageOpenTrades();
   void              CheckPartialClose(ulong ticket);
   void              CheckBreakEven(ulong ticket);

   // Información
   int               GetActiveTradesCount()    { return m_active_count; }
   bool              GetTradeInfo(ulong ticket, TradeInfo &info);
   void              GetAllActiveTrades(TradeInfo &trades[]);
   bool              HasOpenPosition(string symbol);
   int               CountPositionsByMagic();

   // Utilidades
   double            GetCurrentPrice(string symbol, ENUM_SIGNAL_TYPE type);
   bool              IsTradeAllowed(string symbol);
   string            GetLastError();

   // Sincronizar trades activos con posiciones reales
   void              SyncActiveTrades();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CTradeManager::CTradeManager()
{
   m_magic_number = 0;
   m_slippage = 3;
   m_sl_pips = 12;
   m_rr_partial = 2.0;
   m_rr_final = 3.0;
   m_partial_close_percent = 50.0;
   m_active_count = 0;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CTradeManager::~CTradeManager()
{
   ArrayFree(m_active_trades);
}

//+------------------------------------------------------------------+
//| Inicialización                                                    |
//+------------------------------------------------------------------+
bool CTradeManager::Init(long magic, int slippage, int sl_pips,
                         double rr_partial, double rr_final, double partial_percent)
{
   m_magic_number = magic;
   m_slippage = slippage;
   m_sl_pips = sl_pips;
   m_rr_partial = rr_partial;
   m_rr_final = rr_final;
   m_partial_close_percent = partial_percent;

   // Configurar objeto de trading
   m_trade.SetExpertMagicNumber(magic);
   m_trade.SetDeviationInPoints(slippage);
   m_trade.SetTypeFilling(ORDER_FILLING_IOC);
   m_trade.SetAsyncMode(false);

   // Sincronizar trades existentes
   SyncActiveTrades();

   Print("TradeManager inicializado - Magic: ", m_magic_number,
         " | SL: ", m_sl_pips, " pips | TP1 R:R: ", m_rr_partial,
         " | TP2 R:R: ", m_rr_final, " | Cierre parcial: ", m_partial_close_percent, "%");

   return true;
}

//+------------------------------------------------------------------+
//| Sincronizar trades activos con posiciones reales                  |
//+------------------------------------------------------------------+
void CTradeManager::SyncActiveTrades()
{
   ArrayResize(m_active_trades, 0);
   m_active_count = 0;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Magic() == m_magic_number)
         {
            ArrayResize(m_active_trades, m_active_count + 1);

            m_active_trades[m_active_count].ticket = m_position.Ticket();
            m_active_trades[m_active_count].symbol = m_position.Symbol();
            m_active_trades[m_active_count].type = (m_position.PositionType() == POSITION_TYPE_BUY) ?
                                                    SIGNAL_BUY : SIGNAL_SELL;
            m_active_trades[m_active_count].open_price = m_position.PriceOpen();
            m_active_trades[m_active_count].current_price = m_position.PriceCurrent();
            m_active_trades[m_active_count].stop_loss = m_position.StopLoss();
            m_active_trades[m_active_count].take_profit = m_position.TakeProfit();
            m_active_trades[m_active_count].initial_volume = m_position.Volume();
            m_active_trades[m_active_count].current_volume = m_position.Volume();
            m_active_trades[m_active_count].profit = m_position.Profit();
            m_active_trades[m_active_count].open_time = m_position.Time();
            m_active_trades[m_active_count].state = TRADE_STATE_OPEN;
            m_active_trades[m_active_count].partial_closed = false;
            m_active_trades[m_active_count].break_even_set = false;

            // Verificar si ya tiene break-even (SL = precio de entrada)
            if(MathAbs(m_position.StopLoss() - m_position.PriceOpen()) < SymbolInfoDouble(m_position.Symbol(), SYMBOL_POINT) * 5)
            {
               m_active_trades[m_active_count].break_even_set = true;
               m_active_trades[m_active_count].partial_closed = true;
               m_active_trades[m_active_count].state = TRADE_STATE_BREAK_EVEN;
            }

            m_active_count++;
         }
      }
   }

   Print("TradeManager: ", m_active_count, " posiciones activas sincronizadas");
}

//+------------------------------------------------------------------+
//| Abrir operación                                                   |
//+------------------------------------------------------------------+
bool CTradeManager::OpenTrade(SignalInfo &signal)
{
   // Verificar si ya hay posición abierta en este símbolo
   if(HasOpenPosition(signal.symbol))
   {
      Print("Ya existe una posición abierta en ", signal.symbol);
      return false;
   }

   // Verificar trading permitido
   if(!IsTradeAllowed(signal.symbol))
   {
      Print("Trading no permitido para ", signal.symbol);
      return false;
   }

   // Obtener precios
   double entry_price = GetCurrentPrice(signal.symbol, signal.type);
   if(entry_price == 0)
   {
      Print("Error obteniendo precio de entrada para ", signal.symbol);
      return false;
   }

   // Calcular SL y TP
   double sl = CalculateSL(signal.type, entry_price, signal.symbol);
   double tp = CalculateTP2(signal.type, entry_price, signal.symbol); // TP final

   // Normalizar precios
   int digits = (int)SymbolInfoInteger(signal.symbol, SYMBOL_DIGITS);
   entry_price = NormalizeDouble(entry_price, digits);
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   // Ejecutar orden
   bool result = false;
   string comment = StringFormat("%s_MTF", BOT_NAME);

   if(signal.type == SIGNAL_BUY)
   {
      result = m_trade.Buy(signal.lot_size, signal.symbol, entry_price, sl, tp, comment);
   }
   else if(signal.type == SIGNAL_SELL)
   {
      result = m_trade.Sell(signal.lot_size, signal.symbol, entry_price, sl, tp, comment);
   }

   if(result)
   {
      ulong ticket = m_trade.ResultOrder();
      Print("Orden ejecutada - Ticket: ", ticket, " | Tipo: ", SignalTypeToString(signal.type),
            " | Símbolo: ", signal.symbol, " | Lote: ", signal.lot_size,
            " | Precio: ", entry_price, " | SL: ", sl, " | TP: ", tp);

      // Añadir a trades activos
      ArrayResize(m_active_trades, m_active_count + 1);
      m_active_trades[m_active_count].ticket = ticket;
      m_active_trades[m_active_count].symbol = signal.symbol;
      m_active_trades[m_active_count].type = signal.type;
      m_active_trades[m_active_count].open_price = entry_price;
      m_active_trades[m_active_count].stop_loss = sl;
      m_active_trades[m_active_count].take_profit = tp;
      m_active_trades[m_active_count].initial_volume = signal.lot_size;
      m_active_trades[m_active_count].current_volume = signal.lot_size;
      m_active_trades[m_active_count].open_time = TimeCurrent();
      m_active_trades[m_active_count].state = TRADE_STATE_OPEN;
      m_active_trades[m_active_count].partial_closed = false;
      m_active_trades[m_active_count].break_even_set = false;
      m_active_count++;

      return true;
   }
   else
   {
      Print("Error ejecutando orden: ", m_trade.ResultRetcodeDescription());
      return false;
   }
}

//+------------------------------------------------------------------+
//| Cerrar operación                                                  |
//+------------------------------------------------------------------+
bool CTradeManager::CloseTrade(ulong ticket, string reason = "")
{
   if(!m_position.SelectByTicket(ticket))
   {
      Print("Error: No se encontró la posición ", ticket);
      return false;
   }

   bool result = m_trade.PositionClose(ticket);

   if(result)
   {
      Print("Posición cerrada - Ticket: ", ticket, " | Razón: ", reason);

      // Remover de trades activos
      int index = FindTradeIndex(ticket);
      if(index >= 0)
      {
         for(int i = index; i < m_active_count - 1; i++)
            m_active_trades[i] = m_active_trades[i + 1];
         m_active_count--;
         ArrayResize(m_active_trades, m_active_count);
      }
   }
   else
   {
      Print("Error cerrando posición: ", m_trade.ResultRetcodeDescription());
   }

   return result;
}

//+------------------------------------------------------------------+
//| Cierre parcial                                                    |
//+------------------------------------------------------------------+
bool CTradeManager::ClosePartial(ulong ticket, double percent)
{
   if(!m_position.SelectByTicket(ticket))
   {
      Print("Error: No se encontró la posición ", ticket);
      return false;
   }

   double current_volume = m_position.Volume();
   double close_volume = NormalizeDouble(current_volume * (percent / 100.0), 2);

   // Verificar volumen mínimo
   double min_lot = SymbolInfoDouble(m_position.Symbol(), SYMBOL_VOLUME_MIN);
   if(close_volume < min_lot)
   {
      Print("Volumen de cierre parcial (", close_volume, ") menor que mínimo (", min_lot, ")");
      return false;
   }

   // Verificar que quede volumen suficiente
   double remaining = current_volume - close_volume;
   if(remaining < min_lot && remaining > 0)
   {
      // Ajustar para que quede al menos el mínimo
      close_volume = current_volume - min_lot;
   }

   bool result = m_trade.PositionClosePartial(ticket, close_volume);

   if(result)
   {
      Print("Cierre parcial ejecutado - Ticket: ", ticket, " | Volumen cerrado: ", close_volume,
            " | Volumen restante: ", (current_volume - close_volume));

      // Actualizar trade info
      int index = FindTradeIndex(ticket);
      if(index >= 0)
      {
         m_active_trades[index].partial_closed = true;
         m_active_trades[index].current_volume = current_volume - close_volume;
         m_active_trades[index].state = TRADE_STATE_PARTIAL_CLOSE;
      }
   }
   else
   {
      Print("Error en cierre parcial: ", m_trade.ResultRetcodeDescription());
   }

   return result;
}

//+------------------------------------------------------------------+
//| Establecer Break-Even                                             |
//+------------------------------------------------------------------+
bool CTradeManager::SetBreakEven(ulong ticket)
{
   if(!m_position.SelectByTicket(ticket))
   {
      Print("Error: No se encontró la posición ", ticket);
      return false;
   }

   double open_price = m_position.PriceOpen();
   double current_sl = m_position.StopLoss();
   double current_tp = m_position.TakeProfit();
   string symbol = m_position.Symbol();

   // Añadir un pequeño buffer (1-2 pips de ganancia asegurada)
   double buffer = GetPipMultiplier(symbol) * 2; // 2 pips de buffer
   double new_sl;

   if(m_position.PositionType() == POSITION_TYPE_BUY)
   {
      new_sl = open_price + buffer;
      // Verificar que el nuevo SL esté por debajo del precio actual
      if(new_sl >= SymbolInfoDouble(symbol, SYMBOL_BID))
      {
         Print("No se puede establecer break-even: precio actual muy cerca de entrada");
         return false;
      }
   }
   else
   {
      new_sl = open_price - buffer;
      // Verificar que el nuevo SL esté por encima del precio actual
      if(new_sl <= SymbolInfoDouble(symbol, SYMBOL_ASK))
      {
         Print("No se puede establecer break-even: precio actual muy cerca de entrada");
         return false;
      }
   }

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   new_sl = NormalizeDouble(new_sl, digits);

   bool result = m_trade.PositionModify(ticket, new_sl, current_tp);

   if(result)
   {
      Print("Break-even establecido - Ticket: ", ticket, " | Nuevo SL: ", new_sl);

      int index = FindTradeIndex(ticket);
      if(index >= 0)
      {
         m_active_trades[index].break_even_set = true;
         m_active_trades[index].stop_loss = new_sl;
         m_active_trades[index].state = TRADE_STATE_BREAK_EVEN;
      }
   }
   else
   {
      Print("Error estableciendo break-even: ", m_trade.ResultRetcodeDescription());
   }

   return result;
}

//+------------------------------------------------------------------+
//| Modificar Stop Loss                                               |
//+------------------------------------------------------------------+
bool CTradeManager::ModifyStopLoss(ulong ticket, double new_sl)
{
   if(!m_position.SelectByTicket(ticket))
      return false;

   int digits = (int)SymbolInfoInteger(m_position.Symbol(), SYMBOL_DIGITS);
   new_sl = NormalizeDouble(new_sl, digits);

   return m_trade.PositionModify(ticket, new_sl, m_position.TakeProfit());
}

//+------------------------------------------------------------------+
//| Modificar Take Profit                                             |
//+------------------------------------------------------------------+
bool CTradeManager::ModifyTakeProfit(ulong ticket, double new_tp)
{
   if(!m_position.SelectByTicket(ticket))
      return false;

   int digits = (int)SymbolInfoInteger(m_position.Symbol(), SYMBOL_DIGITS);
   new_tp = NormalizeDouble(new_tp, digits);

   return m_trade.PositionModify(ticket, m_position.StopLoss(), new_tp);
}

//+------------------------------------------------------------------+
//| Gestionar operaciones abiertas                                    |
//+------------------------------------------------------------------+
void CTradeManager::ManageOpenTrades()
{
   SyncActiveTrades();

   for(int i = 0; i < m_active_count; i++)
   {
      ulong ticket = m_active_trades[i].ticket;

      // Verificar cierre parcial y break-even
      if(!m_active_trades[i].partial_closed)
      {
         CheckPartialClose(ticket);
      }

      if(m_active_trades[i].partial_closed && !m_active_trades[i].break_even_set)
      {
         CheckBreakEven(ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Verificar si debe hacer cierre parcial                            |
//+------------------------------------------------------------------+
void CTradeManager::CheckPartialClose(ulong ticket)
{
   int index = FindTradeIndex(ticket);
   if(index < 0) return;

   if(!m_position.SelectByTicket(ticket)) return;

   string symbol = m_position.Symbol();
   double open_price = m_position.PriceOpen();
   double current_price = m_position.PriceCurrent();
   double sl = m_position.StopLoss();

   // Calcular distancia al SL en precio
   double sl_distance = MathAbs(open_price - sl);

   // Calcular TP1 (R:R para cierre parcial)
   double tp1_distance = sl_distance * m_rr_partial;
   double tp1_price;

   if(m_position.PositionType() == POSITION_TYPE_BUY)
   {
      tp1_price = open_price + tp1_distance;
      if(current_price >= tp1_price)
      {
         Print("TP1 alcanzado para ticket ", ticket, " - Ejecutando cierre parcial");
         ClosePartial(ticket, m_partial_close_percent);
      }
   }
   else
   {
      tp1_price = open_price - tp1_distance;
      if(current_price <= tp1_price)
      {
         Print("TP1 alcanzado para ticket ", ticket, " - Ejecutando cierre parcial");
         ClosePartial(ticket, m_partial_close_percent);
      }
   }
}

//+------------------------------------------------------------------+
//| Verificar si debe establecer break-even                           |
//+------------------------------------------------------------------+
void CTradeManager::CheckBreakEven(ulong ticket)
{
   int index = FindTradeIndex(ticket);
   if(index < 0) return;

   // Solo establecer BE después del cierre parcial
   if(!m_active_trades[index].partial_closed) return;

   SetBreakEven(ticket);
}

//+------------------------------------------------------------------+
//| Calcular Stop Loss                                                |
//+------------------------------------------------------------------+
double CTradeManager::CalculateSL(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol)
{
   double sl_value = PipsToPrice(symbol, m_sl_pips);

   if(signal_type == SIGNAL_BUY)
      return entry_price - sl_value;
   else
      return entry_price + sl_value;
}

//+------------------------------------------------------------------+
//| Calcular Take Profit 1 (parcial)                                  |
//+------------------------------------------------------------------+
double CTradeManager::CalculateTP1(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol)
{
   double sl_value = PipsToPrice(symbol, m_sl_pips);
   double tp_value = sl_value * m_rr_partial;

   if(signal_type == SIGNAL_BUY)
      return entry_price + tp_value;
   else
      return entry_price - tp_value;
}

//+------------------------------------------------------------------+
//| Calcular Take Profit 2 (final)                                    |
//+------------------------------------------------------------------+
double CTradeManager::CalculateTP2(ENUM_SIGNAL_TYPE signal_type, double entry_price, string symbol)
{
   double sl_value = PipsToPrice(symbol, m_sl_pips);
   double tp_value = sl_value * m_rr_final;

   if(signal_type == SIGNAL_BUY)
      return entry_price + tp_value;
   else
      return entry_price - tp_value;
}

//+------------------------------------------------------------------+
//| Buscar índice de trade por ticket                                 |
//+------------------------------------------------------------------+
int CTradeManager::FindTradeIndex(ulong ticket)
{
   for(int i = 0; i < m_active_count; i++)
   {
      if(m_active_trades[i].ticket == ticket)
         return i;
   }
   return -1;
}

//+------------------------------------------------------------------+
//| Obtener información de trade                                      |
//+------------------------------------------------------------------+
bool CTradeManager::GetTradeInfo(ulong ticket, TradeInfo &info)
{
   int index = FindTradeIndex(ticket);
   if(index < 0) return false;

   info = m_active_trades[index];
   return true;
}

//+------------------------------------------------------------------+
//| Obtener todos los trades activos                                  |
//+------------------------------------------------------------------+
void CTradeManager::GetAllActiveTrades(TradeInfo &trades[])
{
   ArrayResize(trades, m_active_count);
   for(int i = 0; i < m_active_count; i++)
      trades[i] = m_active_trades[i];
}

//+------------------------------------------------------------------+
//| Verificar si hay posición abierta en símbolo                      |
//+------------------------------------------------------------------+
bool CTradeManager::HasOpenPosition(string symbol)
{
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Magic() == m_magic_number && m_position.Symbol() == symbol)
            return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Contar posiciones por Magic Number                                |
//+------------------------------------------------------------------+
int CTradeManager::CountPositionsByMagic()
{
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Magic() == m_magic_number)
            count++;
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Obtener precio actual                                             |
//+------------------------------------------------------------------+
double CTradeManager::GetCurrentPrice(string symbol, ENUM_SIGNAL_TYPE type)
{
   if(type == SIGNAL_BUY)
      return SymbolInfoDouble(symbol, SYMBOL_ASK);
   else
      return SymbolInfoDouble(symbol, SYMBOL_BID);
}

//+------------------------------------------------------------------+
//| Verificar si trading está permitido                               |
//+------------------------------------------------------------------+
bool CTradeManager::IsTradeAllowed(string symbol)
{
   // Verificar trading habilitado en terminal
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   {
      Print("Trading no permitido en terminal");
      return false;
   }

   // Verificar trading habilitado para el símbolo
   if(!SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE))
   {
      Print("Trading no permitido para ", symbol);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Obtener último error                                              |
//+------------------------------------------------------------------+
string CTradeManager::GetLastError()
{
   return m_trade.ResultRetcodeDescription();
}
//+------------------------------------------------------------------+
