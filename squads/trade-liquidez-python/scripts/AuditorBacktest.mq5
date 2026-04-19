//+------------------------------------------------------------------+
//|                                            AuditorBacktest.mq5   |
//|                                     v3.0 Visual Path Edition      |
//+------------------------------------------------------------------+
#property copyright "AIOX Squad"
#property version   "3.00"
#property script_show_inputs

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
   string symbol = Symbol();
   string filename = "audit_backtest_" + symbol + ".csv";
   
   // Tenta abrir o arquivo na pasta MQL5/Files
   int handle = FileOpen(filename, FILE_READ|FILE_CSV|FILE_ANSI|FILE_SHARE_READ, ',');
   
   if(handle == INVALID_HANDLE) 
   {
      MessageBox("Arquivo " + filename + " nao encontrado.\nCertifique-se de que rodou o Backtest no Python.", "Erro de Auditoria", MB_ICONERROR);
      return;
   }

   // Limpa auditorias anteriores
   ObjectsDeleteAll(0, "AUDIT_");

   int count = 0;
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double offset = 20 * point;

   // Pula cabecalho (9 colunas)
   for(int j=0; j<9; j++) FileReadString(handle);

   while(!FileIsEnding(handle))
   {
      string type = FileReadString(handle);
      if(type == "" || FileIsEnding(handle)) continue;
      
      double price = StringToDouble(FileReadString(handle));
      datetime t_time = StringToTime(FileReadString(handle));
      double pnl = StringToDouble(FileReadString(handle));
      double z_price = StringToDouble(FileReadString(handle));
      string rsi = FileReadString(handle);
      string trend = FileReadString(handle);
      double exit_p = StringToDouble(FileReadString(handle));
      datetime exit_t = StringToTime(FileReadString(handle));

      string name = "AUDIT_" + symbol + "_" + (string)count;
      color path_color = (pnl > 0) ? clrLime : clrRed;
      
      // 1. Desenha a Zona de Liquidez (Retângulo)
      string zone_name = name + "_Z";
      ObjectCreate(0, zone_name, OBJ_RECTANGLE, 0, t_time - 3600, z_price + 10*point, t_time, z_price - 10*point);
      ObjectSetInteger(0, zone_name, OBJPROP_COLOR, (type == "SIGNAL_SELL") ? clrLightCoral : clrLightGreen);
      ObjectSetInteger(0, zone_name, OBJPROP_FILL, true);
      ObjectSetInteger(0, zone_name, OBJPROP_BACK, true);
      ObjectSetInteger(0, zone_name, OBJPROP_SELECTABLE, false);

      // 2. Desenha a Seta de ENTRADA
      if(type == "SIGNAL_SELL")
         ObjectCreate(0, name + "_ENT", OBJ_ARROW_DOWN, 0, t_time, price + offset);
      else
         ObjectCreate(0, name + "_ENT", OBJ_ARROW_UP, 0, t_time, price - offset);
      ObjectSetInteger(0, name + "_ENT", OBJPROP_COLOR, path_color);
      ObjectSetInteger(0, name + "_ENT", OBJPROP_WIDTH, 2);

      // 3. Desenha a Linha de CONEXÃO (Trendline)
      string line_name = name + "_PATH";
      ObjectCreate(0, line_name, OBJ_TREND, 0, t_time, price, exit_t, exit_p);
      ObjectSetInteger(0, line_name, OBJPROP_COLOR, path_color);
      ObjectSetInteger(0, line_name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, line_name, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, line_name, OBJPROP_RAY_RIGHT, false);

      // 4. Desenha o Ponto de SAÍDA (Marcador)
      string exit_name = name + "_EXIT";
      ObjectCreate(0, exit_name, OBJ_ARROW, 0, exit_t, exit_p);
      ObjectSetInteger(0, exit_name, OBJPROP_ARROWCODE, 159);
      ObjectSetInteger(0, exit_name, OBJPROP_COLOR, path_color);

      // 5. Rótulo de Racional
      string lab_name = name + "_L";
      ObjectCreate(0, lab_name, OBJ_TEXT, 0, t_time, (type == "SIGNAL_SELL") ? price + 3*offset : price - 3*offset);
      string trend_txt = (trend == "1") ? "T:UP" : (trend == "-1") ? "T:DOWN" : "T:NEUT";
      ObjectSetString(0, lab_name, OBJPROP_TEXT, DoubleToString(pnl, 2) + " USD (RSI:" + rsi + " " + trend_txt + ")");
      ObjectSetInteger(0, lab_name, OBJPROP_COLOR, path_color);
      ObjectSetInteger(0, lab_name, OBJPROP_FONTSIZE, 7);
      ObjectSetDouble(0, lab_name, OBJPROP_ANGLE, 90);

      count++;
   }

   FileClose(handle);
   ChartRedraw(0);
   MessageBox("Auditoria Visual v3.0 Concluida!\nEntradas, Saídas e Caminhos desenhados: " + (string)count, "Sucesso");
}
