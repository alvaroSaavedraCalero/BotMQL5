//+------------------------------------------------------------------+
//|                                               SessionManager.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

#include "Constants.mqh"

//+------------------------------------------------------------------+
//| Clase para Gestión de Sesiones de Trading                         |
//+------------------------------------------------------------------+
class CSessionManager
{
private:
   // Configuración de horarios (hora del servidor)
   int               m_london_start;           // Hora inicio Londres
   int               m_london_end;             // Hora fin Londres
   int               m_ny_start;               // Hora inicio Nueva York
   int               m_ny_end;                 // Hora fin Nueva York

   // Offset del broker
   int               m_broker_gmt_offset;      // Offset GMT del broker

   // Estado actual
   ENUM_TRADING_SESSION m_current_session;     // Sesión actual
   bool              m_is_trading_allowed;     // Si se permite trading

   // Calcular offset del broker
   int               CalculateBrokerOffset();

public:
   // Constructor y destructor
                     CSessionManager();
                    ~CSessionManager();

   // Inicialización
   bool              Init(int london_start, int london_end, int ny_start, int ny_end);

   // Actualización
   void              Update();

   // Verificaciones
   bool              IsTradingSession();
   bool              IsLondonSession();
   bool              IsNewYorkSession();
   bool              IsOverlapSession();

   // Getters
   ENUM_TRADING_SESSION GetCurrentSession()    { return m_current_session; }
   string            GetSessionName();
   int               GetMinutesToSessionStart();
   int               GetMinutesToSessionEnd();

   // Información de tiempo
   int               GetServerHour();
   int               GetServerMinute();
   string            GetTimeInfo();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CSessionManager::CSessionManager()
{
   // Valores por defecto (hora del servidor, ajustar según broker)
   // Asumiendo broker GMT+2 en invierno, GMT+3 en verano
   m_london_start = 10;   // 8:00 GMT = 10:00 GMT+2
   m_london_end = 14;     // 12:00 GMT = 14:00 GMT+2
   m_ny_start = 15;       // 13:00 GMT = 15:00 GMT+2
   m_ny_end = 19;         // 17:00 GMT = 19:00 GMT+2

   m_broker_gmt_offset = 2;
   m_current_session = SESSION_NONE;
   m_is_trading_allowed = false;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CSessionManager::~CSessionManager()
{
}

//+------------------------------------------------------------------+
//| Inicialización                                                    |
//+------------------------------------------------------------------+
bool CSessionManager::Init(int london_start, int london_end, int ny_start, int ny_end)
{
   m_london_start = london_start;
   m_london_end = london_end;
   m_ny_start = ny_start;
   m_ny_end = ny_end;

   // Calcular offset del broker
   m_broker_gmt_offset = CalculateBrokerOffset();

   Print("SessionManager inicializado - Londres: ", m_london_start, ":00 - ", m_london_end,
         ":00 | NY: ", m_ny_start, ":00 - ", m_ny_end, ":00 | Broker GMT offset: ", m_broker_gmt_offset);

   Update();

   return true;
}

//+------------------------------------------------------------------+
//| Calcular offset GMT del broker                                    |
//+------------------------------------------------------------------+
int CSessionManager::CalculateBrokerOffset()
{
   // Obtener hora local y hora del servidor
   datetime server_time = TimeCurrent();
   datetime local_time = TimeLocal();

   // Calcular diferencia en horas
   int diff = (int)((server_time - local_time) / 3600);

   // Obtener offset UTC local
   MqlDateTime local_dt;
   TimeToStruct(local_time, local_dt);

   // Nota: Esta es una aproximación, el offset real puede variar según DST
   // La mayoría de brokers usan GMT+2 o GMT+3
   return 2; // Valor por defecto conservador
}

//+------------------------------------------------------------------+
//| Actualización de estado                                           |
//+------------------------------------------------------------------+
void CSessionManager::Update()
{
   int current_hour = GetServerHour();

   // Determinar sesión actual
   bool in_london = (current_hour >= m_london_start && current_hour < m_london_end);
   bool in_ny = (current_hour >= m_ny_start && current_hour < m_ny_end);

   if(in_london && in_ny)
   {
      m_current_session = SESSION_OVERLAP;
      m_is_trading_allowed = true;
   }
   else if(in_london)
   {
      m_current_session = SESSION_LONDON;
      m_is_trading_allowed = true;
   }
   else if(in_ny)
   {
      m_current_session = SESSION_NEW_YORK;
      m_is_trading_allowed = true;
   }
   else
   {
      m_current_session = SESSION_NONE;
      m_is_trading_allowed = false;
   }
}

//+------------------------------------------------------------------+
//| Verificar si es horario de trading                                |
//+------------------------------------------------------------------+
bool CSessionManager::IsTradingSession()
{
   Update();
   return m_is_trading_allowed;
}

//+------------------------------------------------------------------+
//| Verificar si es sesión de Londres                                 |
//+------------------------------------------------------------------+
bool CSessionManager::IsLondonSession()
{
   Update();
   return (m_current_session == SESSION_LONDON || m_current_session == SESSION_OVERLAP);
}

//+------------------------------------------------------------------+
//| Verificar si es sesión de Nueva York                              |
//+------------------------------------------------------------------+
bool CSessionManager::IsNewYorkSession()
{
   Update();
   return (m_current_session == SESSION_NEW_YORK || m_current_session == SESSION_OVERLAP);
}

//+------------------------------------------------------------------+
//| Verificar si es solapamiento                                      |
//+------------------------------------------------------------------+
bool CSessionManager::IsOverlapSession()
{
   Update();
   return (m_current_session == SESSION_OVERLAP);
}

//+------------------------------------------------------------------+
//| Obtener nombre de la sesión actual                                |
//+------------------------------------------------------------------+
string CSessionManager::GetSessionName()
{
   switch(m_current_session)
   {
      case SESSION_LONDON:    return "London";
      case SESSION_NEW_YORK:  return "New York";
      case SESSION_OVERLAP:   return "London/NY Overlap";
      case SESSION_NONE:      return "Closed";
      default:                return "Unknown";
   }
}

//+------------------------------------------------------------------+
//| Obtener minutos hasta inicio de próxima sesión                    |
//+------------------------------------------------------------------+
int CSessionManager::GetMinutesToSessionStart()
{
   if(m_is_trading_allowed) return 0;

   int current_hour = GetServerHour();
   int current_minute = GetServerMinute();
   int total_minutes = current_hour * 60 + current_minute;

   int london_start_minutes = m_london_start * 60;
   int ny_start_minutes = m_ny_start * 60;

   int to_london = london_start_minutes - total_minutes;
   int to_ny = ny_start_minutes - total_minutes;

   // Si ya pasó Londres hoy, calcular para mañana
   if(to_london < 0) to_london += 24 * 60;
   if(to_ny < 0) to_ny += 24 * 60;

   return MathMin(to_london, to_ny);
}

//+------------------------------------------------------------------+
//| Obtener minutos hasta fin de sesión actual                        |
//+------------------------------------------------------------------+
int CSessionManager::GetMinutesToSessionEnd()
{
   if(!m_is_trading_allowed) return 0;

   int current_hour = GetServerHour();
   int current_minute = GetServerMinute();
   int total_minutes = current_hour * 60 + current_minute;

   int london_end_minutes = m_london_end * 60;
   int ny_end_minutes = m_ny_end * 60;

   int remaining = 0;

   switch(m_current_session)
   {
      case SESSION_LONDON:
         remaining = london_end_minutes - total_minutes;
         break;
      case SESSION_NEW_YORK:
         remaining = ny_end_minutes - total_minutes;
         break;
      case SESSION_OVERLAP:
         // En overlap, el fin es cuando termina NY
         remaining = ny_end_minutes - total_minutes;
         break;
   }

   return (remaining > 0) ? remaining : 0;
}

//+------------------------------------------------------------------+
//| Obtener hora del servidor                                         |
//+------------------------------------------------------------------+
int CSessionManager::GetServerHour()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.hour;
}

//+------------------------------------------------------------------+
//| Obtener minuto del servidor                                       |
//+------------------------------------------------------------------+
int CSessionManager::GetServerMinute()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.min;
}

//+------------------------------------------------------------------+
//| Obtener información de tiempo formateada                          |
//+------------------------------------------------------------------+
string CSessionManager::GetTimeInfo()
{
   string info = StringFormat("Hora servidor: %02d:%02d | Sesión: %s",
                              GetServerHour(), GetServerMinute(), GetSessionName());

   if(!m_is_trading_allowed)
   {
      int mins_to_start = GetMinutesToSessionStart();
      int hours = mins_to_start / 60;
      int mins = mins_to_start % 60;
      info += StringFormat(" | Próxima sesión en: %dh %dm", hours, mins);
   }
   else
   {
      int mins_to_end = GetMinutesToSessionEnd();
      int hours = mins_to_end / 60;
      int mins = mins_to_end % 60;
      info += StringFormat(" | Fin de sesión en: %dh %dm", hours, mins);
   }

   return info;
}
//+------------------------------------------------------------------+
