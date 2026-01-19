//+------------------------------------------------------------------+
//|                                                 SocketClient.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

#include "Constants.mqh"

//+------------------------------------------------------------------+
//| Clase para Comunicación via Archivos con Python                   |
//| Nota: MQL5 no soporta sockets nativos, usamos archivos compartidos|
//+------------------------------------------------------------------+
class CSocketClient
{
private:
   // Configuración
   string            m_base_path;              // Ruta base para archivos
   string            m_outgoing_file;          // Archivo para mensajes salientes (MT5 -> Python)
   string            m_incoming_file;          // Archivo para mensajes entrantes (Python -> MT5)
   string            m_signal_file;            // Archivo para señales de Python
   string            m_status_file;            // Archivo para estado del bot

   // Estado de conexión
   bool              m_is_connected;
   datetime          m_last_heartbeat;
   int               m_heartbeat_interval;     // Segundos

   // Buffer de mensajes
   string            m_message_queue[];
   int               m_queue_size;

   // Métodos privados
   bool              WriteToFile(string filename, string content);
   string            ReadFromFile(string filename);
   void              ClearFile(string filename);
   string            BuildStatusJSON(AccountInfo &account, DailyStats &stats, string session);

public:
   // Constructor y destructor
                     CSocketClient();
                    ~CSocketClient();

   // Inicialización
   bool              Init(string base_path = "");

   // Conexión (simulada via archivos)
   bool              Connect();
   void              Disconnect();
   bool              IsConnected()             { return m_is_connected; }

   // Envío de datos
   bool              SendStatus(AccountInfo &account, DailyStats &stats, string session);
   bool              SendTradeOpen(TradeInfo &trade);
   bool              SendTradeClose(ulong ticket, double profit, string reason);
   bool              SendTradePartialClose(ulong ticket, double closed_volume, double remaining_volume);
   bool              SendHeartbeat();
   bool              SendError(string error_message);

   // Recepción de datos
   bool              HasIncomingSignal();
   bool              ReadSignal(SignalInfo &signal);
   bool              HasCommand();
   string            ReadCommand();

   // Mantenimiento
   void              Update();
   void              ProcessIncomingMessages();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CSocketClient::CSocketClient()
{
   m_base_path = "";
   m_outgoing_file = "mt5_to_python.json";
   m_incoming_file = "python_to_mt5.json";
   m_signal_file = "python_signals.json";
   m_status_file = "mt5_status.json";

   m_is_connected = false;
   m_last_heartbeat = 0;
   m_heartbeat_interval = HEARTBEAT_INTERVAL_SEC;
   m_queue_size = 0;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CSocketClient::~CSocketClient()
{
   Disconnect();
   ArrayFree(m_message_queue);
}

//+------------------------------------------------------------------+
//| Inicialización                                                    |
//+------------------------------------------------------------------+
bool CSocketClient::Init(string base_path = "")
{
   // Usar carpeta común de archivos de MT5
   if(base_path == "")
      m_base_path = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\ScalpingBot\\";
   else
      m_base_path = base_path;

   // Crear directorio si no existe
   if(!FolderCreate("ScalpingBot", FILE_COMMON))
   {
      // Intentar con la carpeta local
      FolderCreate("ScalpingBot", 0);
   }

   Print("SocketClient inicializado - Ruta: ", m_base_path);

   return true;
}

//+------------------------------------------------------------------+
//| Conectar (crear archivos de comunicación)                         |
//+------------------------------------------------------------------+
bool CSocketClient::Connect()
{
   // Limpiar archivos existentes
   ClearFile(m_outgoing_file);
   ClearFile(m_status_file);

   // Enviar heartbeat inicial
   m_is_connected = SendHeartbeat();
   m_last_heartbeat = TimeCurrent();

   if(m_is_connected)
      Print("SocketClient conectado");
   else
      Print("Error conectando SocketClient");

   return m_is_connected;
}

//+------------------------------------------------------------------+
//| Desconectar                                                       |
//+------------------------------------------------------------------+
void CSocketClient::Disconnect()
{
   m_is_connected = false;
   Print("SocketClient desconectado");
}

//+------------------------------------------------------------------+
//| Escribir en archivo                                               |
//+------------------------------------------------------------------+
bool CSocketClient::WriteToFile(string filename, string content)
{
   string full_path = "ScalpingBot\\" + filename;

   int handle = FileOpen(full_path, FILE_WRITE | FILE_TXT | FILE_COMMON | FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      // Intentar sin FILE_COMMON
      handle = FileOpen(full_path, FILE_WRITE | FILE_TXT | FILE_ANSI);
      if(handle == INVALID_HANDLE)
      {
         Print("Error abriendo archivo para escritura: ", full_path, " - Error: ", GetLastError());
         return false;
      }
   }

   FileWriteString(handle, content);
   FileClose(handle);

   return true;
}

//+------------------------------------------------------------------+
//| Leer de archivo                                                   |
//+------------------------------------------------------------------+
string CSocketClient::ReadFromFile(string filename)
{
   string full_path = "ScalpingBot\\" + filename;
   string content = "";

   int handle = FileOpen(full_path, FILE_READ | FILE_TXT | FILE_COMMON | FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      // Intentar sin FILE_COMMON
      handle = FileOpen(full_path, FILE_READ | FILE_TXT | FILE_ANSI);
      if(handle == INVALID_HANDLE)
         return "";
   }

   while(!FileIsEnding(handle))
   {
      content += FileReadString(handle);
   }

   FileClose(handle);

   return content;
}

//+------------------------------------------------------------------+
//| Limpiar archivo                                                   |
//+------------------------------------------------------------------+
void CSocketClient::ClearFile(string filename)
{
   string full_path = "ScalpingBot\\" + filename;

   int handle = FileOpen(full_path, FILE_WRITE | FILE_TXT | FILE_COMMON | FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, "");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Construir JSON de estado                                          |
//+------------------------------------------------------------------+
string CSocketClient::BuildStatusJSON(AccountInfo &account, DailyStats &stats, string session)
{
   string json = "{";
   json += "\"type\":\"STATUS\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"account\":{";
   json += "\"balance\":" + DoubleToString(account.balance, 2) + ",";
   json += "\"equity\":" + DoubleToString(account.equity, 2) + ",";
   json += "\"margin\":" + DoubleToString(account.margin, 2) + ",";
   json += "\"free_margin\":" + DoubleToString(account.free_margin, 2) + ",";
   json += "\"profit\":" + DoubleToString(account.profit, 2) + ",";
   json += "\"open_positions\":" + IntegerToString(account.open_positions) + ",";
   json += "\"drawdown\":" + DoubleToString(account.drawdown, 2) + ",";
   json += "\"daily_drawdown\":" + DoubleToString(account.daily_drawdown, 2) + ",";
   json += "\"bot_status\":\"" + BotStatusToString(account.bot_status) + "\"";
   json += "},";
   json += "\"daily_stats\":{";
   json += "\"total_trades\":" + IntegerToString(stats.total_trades) + ",";
   json += "\"winning_trades\":" + IntegerToString(stats.winning_trades) + ",";
   json += "\"losing_trades\":" + IntegerToString(stats.losing_trades) + ",";
   json += "\"gross_profit\":" + DoubleToString(stats.gross_profit, 2) + ",";
   json += "\"gross_loss\":" + DoubleToString(stats.gross_loss, 2) + ",";
   json += "\"net_profit\":" + DoubleToString(stats.net_profit, 2) + ",";
   json += "\"max_drawdown\":" + DoubleToString(stats.max_drawdown, 2) + ",";
   json += "\"start_balance\":" + DoubleToString(stats.start_balance, 2) + ",";
   json += "\"current_balance\":" + DoubleToString(stats.current_balance, 2);
   json += "},";
   json += "\"session\":\"" + session + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Enviar estado del bot                                             |
//+------------------------------------------------------------------+
bool CSocketClient::SendStatus(AccountInfo &account, DailyStats &stats, string session)
{
   string json = BuildStatusJSON(account, stats, session);
   return WriteToFile(m_status_file, json);
}

//+------------------------------------------------------------------+
//| Enviar apertura de trade                                          |
//+------------------------------------------------------------------+
bool CSocketClient::SendTradeOpen(TradeInfo &trade)
{
   string json = "{";
   json += "\"type\":\"TRADE\",";
   json += "\"action\":\"OPEN\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"ticket\":" + IntegerToString(trade.ticket) + ",";
   json += "\"symbol\":\"" + trade.symbol + "\",";
   json += "\"trade_type\":\"" + SignalTypeToString(trade.type) + "\",";
   json += "\"volume\":" + DoubleToString(trade.initial_volume, 2) + ",";
   json += "\"open_price\":" + DoubleToString(trade.open_price, 5) + ",";
   json += "\"stop_loss\":" + DoubleToString(trade.stop_loss, 5) + ",";
   json += "\"take_profit\":" + DoubleToString(trade.take_profit, 5) + ",";
   json += "\"open_time\":" + IntegerToString((long)trade.open_time);
   json += "}";

   return WriteToFile(m_outgoing_file, json);
}

//+------------------------------------------------------------------+
//| Enviar cierre de trade                                            |
//+------------------------------------------------------------------+
bool CSocketClient::SendTradeClose(ulong ticket, double profit, string reason)
{
   string json = "{";
   json += "\"type\":\"TRADE\",";
   json += "\"action\":\"CLOSE\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"ticket\":" + IntegerToString(ticket) + ",";
   json += "\"profit\":" + DoubleToString(profit, 2) + ",";
   json += "\"reason\":\"" + reason + "\"";
   json += "}";

   return WriteToFile(m_outgoing_file, json);
}

//+------------------------------------------------------------------+
//| Enviar cierre parcial                                             |
//+------------------------------------------------------------------+
bool CSocketClient::SendTradePartialClose(ulong ticket, double closed_volume, double remaining_volume)
{
   string json = "{";
   json += "\"type\":\"TRADE\",";
   json += "\"action\":\"PARTIAL_CLOSE\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"ticket\":" + IntegerToString(ticket) + ",";
   json += "\"closed_volume\":" + DoubleToString(closed_volume, 2) + ",";
   json += "\"remaining_volume\":" + DoubleToString(remaining_volume, 2);
   json += "}";

   return WriteToFile(m_outgoing_file, json);
}

//+------------------------------------------------------------------+
//| Enviar heartbeat                                                  |
//+------------------------------------------------------------------+
bool CSocketClient::SendHeartbeat()
{
   string json = "{";
   json += "\"type\":\"HEARTBEAT\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"bot_name\":\"" + BOT_NAME + "\",";
   json += "\"version\":\"" + BOT_VERSION + "\"";
   json += "}";

   m_last_heartbeat = TimeCurrent();

   return WriteToFile("heartbeat.json", json);
}

//+------------------------------------------------------------------+
//| Enviar mensaje de error                                           |
//+------------------------------------------------------------------+
bool CSocketClient::SendError(string error_message)
{
   string json = "{";
   json += "\"type\":\"ERROR\",";
   json += "\"timestamp\":" + IntegerToString(GetUnixTimestamp()) + ",";
   json += "\"message\":\"" + error_message + "\"";
   json += "}";

   return WriteToFile(m_outgoing_file, json);
}

//+------------------------------------------------------------------+
//| Verificar si hay señal entrante                                   |
//+------------------------------------------------------------------+
bool CSocketClient::HasIncomingSignal()
{
   string content = ReadFromFile(m_signal_file);
   if(content == "") return false;

   // Verificar que contenga una señal válida
   if(StringFind(content, "\"type\":\"SIGNAL\"") >= 0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| Leer señal de Python                                              |
//+------------------------------------------------------------------+
bool CSocketClient::ReadSignal(SignalInfo &signal)
{
   string content = ReadFromFile(m_signal_file);
   if(content == "") return false;

   // Parsear JSON manualmente (simplificado)
   // En una implementación completa, usar un parser JSON

   // Buscar action
   int action_pos = StringFind(content, "\"action\":\"");
   if(action_pos < 0) return false;

   action_pos += 10;
   int action_end = StringFind(content, "\"", action_pos);
   string action = StringSubstr(content, action_pos, action_end - action_pos);

   signal.type = StringToSignalType(action);
   if(signal.type == SIGNAL_NONE) return false;

   // Buscar symbol
   int symbol_pos = StringFind(content, "\"symbol\":\"");
   if(symbol_pos >= 0)
   {
      symbol_pos += 10;
      int symbol_end = StringFind(content, "\"", symbol_pos);
      signal.symbol = StringSubstr(content, symbol_pos, symbol_end - symbol_pos);
   }

   // Buscar sl_pips
   int sl_pos = StringFind(content, "\"sl_pips\":");
   if(sl_pos >= 0)
   {
      sl_pos += 10;
      int sl_end = StringFind(content, ",", sl_pos);
      if(sl_end < 0) sl_end = StringFind(content, "}", sl_pos);
      signal.sl_pips = (int)StringToInteger(StringSubstr(content, sl_pos, sl_end - sl_pos));
   }

   signal.signal_time = TimeCurrent();

   // Limpiar archivo de señales después de leer
   ClearFile(m_signal_file);

   Print("Señal recibida de Python: ", SignalTypeToString(signal.type), " ", signal.symbol);

   return true;
}

//+------------------------------------------------------------------+
//| Verificar si hay comando entrante                                 |
//+------------------------------------------------------------------+
bool CSocketClient::HasCommand()
{
   string content = ReadFromFile(m_incoming_file);
   if(content == "") return false;

   if(StringFind(content, "\"type\":\"COMMAND\"") >= 0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| Leer comando de Python                                            |
//+------------------------------------------------------------------+
string CSocketClient::ReadCommand()
{
   string content = ReadFromFile(m_incoming_file);
   if(content == "") return "";

   // Buscar command
   int cmd_pos = StringFind(content, "\"command\":\"");
   if(cmd_pos < 0) return "";

   cmd_pos += 11;
   int cmd_end = StringFind(content, "\"", cmd_pos);
   string command = StringSubstr(content, cmd_pos, cmd_end - cmd_pos);

   // Limpiar archivo después de leer
   ClearFile(m_incoming_file);

   Print("Comando recibido de Python: ", command);

   return command;
}

//+------------------------------------------------------------------+
//| Actualización periódica                                           |
//+------------------------------------------------------------------+
void CSocketClient::Update()
{
   // Enviar heartbeat periódico
   if(TimeCurrent() - m_last_heartbeat > m_heartbeat_interval)
   {
      SendHeartbeat();
   }

   // Procesar mensajes entrantes
   ProcessIncomingMessages();
}

//+------------------------------------------------------------------+
//| Procesar mensajes entrantes                                       |
//+------------------------------------------------------------------+
void CSocketClient::ProcessIncomingMessages()
{
   // Verificar comandos
   if(HasCommand())
   {
      string cmd = ReadCommand();
      // El comando será procesado por el EA principal
   }
}
//+------------------------------------------------------------------+
