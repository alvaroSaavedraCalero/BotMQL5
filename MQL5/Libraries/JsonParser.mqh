//+------------------------------------------------------------------+
//|                                                   JsonParser.mqh |
//|                                Multi-TF Scalping Bot for MT5     |
//|                                     Copyright 2024, TradingBot   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingBot"
#property link      "https://github.com/yourusername/ScalpingBot"
#property strict

//+------------------------------------------------------------------+
//| Clase simple para parseo de JSON                                  |
//+------------------------------------------------------------------+
class CJsonParser
{
private:
   string            m_json;
   int               m_pos;

   // Métodos de parseo
   void              SkipWhitespace();
   string            ParseString();
   double            ParseNumber();
   bool              ParseBool();

public:
   // Constructor
                     CJsonParser();
                    ~CJsonParser();

   // Cargar JSON
   void              Load(string json);

   // Obtener valores
   string            GetString(string key);
   double            GetDouble(string key);
   int               GetInt(string key);
   long              GetLong(string key);
   bool              GetBool(string key);

   // Verificar existencia
   bool              HasKey(string key);

   // Utilidades
   static string     EscapeString(string str);
   static string     UnescapeString(string str);
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CJsonParser::CJsonParser()
{
   m_json = "";
   m_pos = 0;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CJsonParser::~CJsonParser()
{
}

//+------------------------------------------------------------------+
//| Cargar JSON                                                       |
//+------------------------------------------------------------------+
void CJsonParser::Load(string json)
{
   m_json = json;
   m_pos = 0;
}

//+------------------------------------------------------------------+
//| Saltar espacios en blanco                                         |
//+------------------------------------------------------------------+
void CJsonParser::SkipWhitespace()
{
   while(m_pos < StringLen(m_json))
   {
      ushort c = StringGetCharacter(m_json, m_pos);
      if(c != ' ' && c != '\t' && c != '\n' && c != '\r')
         break;
      m_pos++;
   }
}

//+------------------------------------------------------------------+
//| Verificar si existe una clave                                     |
//+------------------------------------------------------------------+
bool CJsonParser::HasKey(string key)
{
   string search = "\"" + key + "\"";
   return (StringFind(m_json, search) >= 0);
}

//+------------------------------------------------------------------+
//| Obtener valor string                                              |
//+------------------------------------------------------------------+
string CJsonParser::GetString(string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(m_json, search);

   if(pos < 0) return "";

   pos += StringLen(search);

   // Saltar espacios
   while(pos < StringLen(m_json) && StringGetCharacter(m_json, pos) == ' ')
      pos++;

   // Verificar que empiece con comillas
   if(StringGetCharacter(m_json, pos) != '"')
      return "";

   pos++; // Saltar comilla inicial

   // Buscar comilla final
   int end = pos;
   while(end < StringLen(m_json))
   {
      ushort c = StringGetCharacter(m_json, end);
      if(c == '"' && StringGetCharacter(m_json, end - 1) != '\\')
         break;
      end++;
   }

   return UnescapeString(StringSubstr(m_json, pos, end - pos));
}

//+------------------------------------------------------------------+
//| Obtener valor double                                              |
//+------------------------------------------------------------------+
double CJsonParser::GetDouble(string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(m_json, search);

   if(pos < 0) return 0.0;

   pos += StringLen(search);

   // Saltar espacios
   while(pos < StringLen(m_json) && StringGetCharacter(m_json, pos) == ' ')
      pos++;

   // Leer número
   int end = pos;
   while(end < StringLen(m_json))
   {
      ushort c = StringGetCharacter(m_json, end);
      if((c < '0' || c > '9') && c != '.' && c != '-' && c != '+' && c != 'e' && c != 'E')
         break;
      end++;
   }

   return StringToDouble(StringSubstr(m_json, pos, end - pos));
}

//+------------------------------------------------------------------+
//| Obtener valor int                                                 |
//+------------------------------------------------------------------+
int CJsonParser::GetInt(string key)
{
   return (int)GetDouble(key);
}

//+------------------------------------------------------------------+
//| Obtener valor long                                                |
//+------------------------------------------------------------------+
long CJsonParser::GetLong(string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(m_json, search);

   if(pos < 0) return 0;

   pos += StringLen(search);

   // Saltar espacios
   while(pos < StringLen(m_json) && StringGetCharacter(m_json, pos) == ' ')
      pos++;

   // Leer número
   int end = pos;
   while(end < StringLen(m_json))
   {
      ushort c = StringGetCharacter(m_json, end);
      if((c < '0' || c > '9') && c != '-')
         break;
      end++;
   }

   return StringToInteger(StringSubstr(m_json, pos, end - pos));
}

//+------------------------------------------------------------------+
//| Obtener valor bool                                                |
//+------------------------------------------------------------------+
bool CJsonParser::GetBool(string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(m_json, search);

   if(pos < 0) return false;

   pos += StringLen(search);

   // Saltar espacios
   while(pos < StringLen(m_json) && StringGetCharacter(m_json, pos) == ' ')
      pos++;

   // Verificar valor
   if(StringSubstr(m_json, pos, 4) == "true")
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| Escapar string para JSON                                          |
//+------------------------------------------------------------------+
string CJsonParser::EscapeString(string str)
{
   string result = "";
   int len = StringLen(str);

   for(int i = 0; i < len; i++)
   {
      ushort c = StringGetCharacter(str, i);

      switch(c)
      {
         case '"':  result += "\\\""; break;
         case '\\': result += "\\\\"; break;
         case '\n': result += "\\n"; break;
         case '\r': result += "\\r"; break;
         case '\t': result += "\\t"; break;
         default:   result += ShortToString(c); break;
      }
   }

   return result;
}

//+------------------------------------------------------------------+
//| Desescapar string de JSON                                         |
//+------------------------------------------------------------------+
string CJsonParser::UnescapeString(string str)
{
   string result = "";
   int len = StringLen(str);

   for(int i = 0; i < len; i++)
   {
      ushort c = StringGetCharacter(str, i);

      if(c == '\\' && i + 1 < len)
      {
         ushort next = StringGetCharacter(str, i + 1);
         switch(next)
         {
            case '"':  result += "\""; i++; break;
            case '\\': result += "\\"; i++; break;
            case 'n':  result += "\n"; i++; break;
            case 'r':  result += "\r"; i++; break;
            case 't':  result += "\t"; i++; break;
            default:   result += ShortToString(c); break;
         }
      }
      else
      {
         result += ShortToString(c);
      }
   }

   return result;
}
//+------------------------------------------------------------------+
