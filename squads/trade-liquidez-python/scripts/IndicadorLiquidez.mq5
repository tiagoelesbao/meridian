//+------------------------------------------------------------------+
//|                                            IndicadorLiquidez.mq5 |
//|                                     v5.5 Multi-Pair LIVE Edition  |
//+------------------------------------------------------------------+
#property copyright "AIOX Squad"
#property link      ""
#property version   "5.50"
#property indicator_chart_window

int OnInit()
{
   EventSetTimer(5);
   UpdateDrawing();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "LIQ_");
   EventKillTimer();
}

void OnTimer()
{
   UpdateDrawing();
}

void UpdateDrawing()
{
   string symbol = Symbol();
   string filename = "liquidez_data_" + symbol + ".csv";
   int handle = FileOpen(filename, FILE_READ|FILE_CSV|FILE_ANSI|FILE_SHARE_READ, ',');
   if(handle == INVALID_HANDLE) return;

   ObjectsDeleteAll(0, "LIQ_");

   int i = 0;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   while(!FileIsEnding(handle))
   {
      string type = FileReadString(handle);
      if(type == "" || type == "HEADER" || type == "type") continue;
      
      double price = StringToDouble(FileReadString(handle));
      string time_str = FileReadString(handle);
      if(time_str == "") continue;
      datetime t_start = StringToTime(time_str);

      string name = "LIQ_" + symbol + "_" + (string)i;
      
      if(type == "ZONE_RESISTANCE")
      {
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, t_start, price + 10*point, TimeCurrent(), price - 10*point);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLightCoral);
         ObjectSetInteger(0, name, OBJPROP_FILL, true);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
         ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      }
      else if(type == "ZONE_SUPPORT")
      {
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, t_start, price + 10*point, TimeCurrent(), price - 10*point);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLightGreen);
         ObjectSetInteger(0, name, OBJPROP_FILL, true);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
         ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      }
      else if(type == "SIGNAL_SELL")
      {
         ObjectCreate(0, name, OBJ_ARROW_DOWN, 0, TimeCurrent(), price);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, name, OBJPROP_WIDTH, 5);
      }
      else if(type == "SIGNAL_BUY")
      {
         ObjectCreate(0, name, OBJ_ARROW_UP, 0, TimeCurrent(), price);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLime);
         ObjectSetInteger(0, name, OBJPROP_WIDTH, 5);
      }
      i++;
   }
   FileClose(handle);
   ChartRedraw(0);
}

int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[], const double &high[], const double &low[], const double &close[], const long &tick_volume[], const long &volume[], const int &spread[])
{//+------------------------------------------------------------------+
//|                                            IndicadorLiquidez.mq5 |
//|                                     v5.5 Multi-Pair LIVE Edition  |
//+------------------------------------------------------------------+
#property copyright "AIOX Squad"
#property link      ""
#property version   "5.50"
#property indicator_chart_window

int OnInit()
{
   EventSetTimer(5);
   UpdateDrawing();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "LIQ_");
   EventKillTimer();
}

void OnTimer()
{
   UpdateDrawing();
}

void UpdateDrawing()
{
   string symbol = Symbol();
   string filename = "liquidez_data_" + symbol + ".csv";
   int handle = FileOpen(filename, FILE_READ|FILE_CSV|FILE_ANSI|FILE_SHARE_READ, ',');
   if(handle == INVALID_HANDLE) return;

   ObjectsDeleteAll(0, "LIQ_");

   int i = 0;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   while(!FileIsEnding(handle))
   {
      string type = FileReadString(handle);
      if(type == "" || type == "HEADER" || type == "type") continue;
      
      double price = StringToDouble(FileReadString(handle));
      string time_str = FileReadString(handle);
      if(time_str == "") continue;
      datetime t_start = StringToTime(time_str);

      string name = "LIQ_" + symbol + "_" + (string)i;
      
      if(type == "ZONE_RESISTANCE")
      {
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, t_start, price + 10*point, TimeCurrent(), price - 10*point);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLightCoral);
         ObjectSetInteger(0, name, OBJPROP_FILL, true);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
         ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      }
      else if(type == "ZONE_SUPPORT")
      {
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, t_start, price + 10*point, TimeCurrent(), price - 10*point);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLightGreen);
         ObjectSetInteger(0, name, OBJPROP_FILL, true);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
         ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      }
      else if(type == "SIGNAL_SELL")
      {
         ObjectCreate(0, name, OBJ_ARROW_DOWN, 0, TimeCurrent(), price);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, name, OBJPROP_WIDTH, 5);
      }
      else if(type == "SIGNAL_BUY")
      {
         ObjectCreate(0, name, OBJ_ARROW_UP, 0, TimeCurrent(), price);
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrLime);
         ObjectSetInteger(0, name, OBJPROP_WIDTH, 5);
      }
      i++;
   }
   FileClose(handle);
   ChartRedraw(0);
}

int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[], const double &high[], const double &low[], const double &close[], const long &tick_volume[], const long &volume[], const int &spread[])
{
   return(rates_total);
}

   return(rates_total);
}
