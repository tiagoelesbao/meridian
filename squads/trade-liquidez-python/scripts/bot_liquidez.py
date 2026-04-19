import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz
import sys
import yaml
import os

# Carrega Configurações
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

from supabase_client import SupabaseManager
db_manager = SupabaseManager()

# Mapeamento de Timeframes
TF_MAP = {"H1": mt5.TIMEFRAME_H1, "M30": mt5.TIMEFRAME_M30, "M15": mt5.TIMEFRAME_M15, "M5": mt5.TIMEFRAME_M5}

# Configurações Globais
SYMBOLS = CFG.get('symbols', ["EURUSD"])
TIMEFRAME_ZONES = TF_MAP.get(CFG.get('zone_timeframe', 'M15'), mt5.TIMEFRAME_M15)
TIMEFRAME_M5 = mt5.TIMEFRAME_M5
MAGIC_NUMBER = CFG['magic_number']
LOOKBACK_ZONES = CFG.get('lookback_zones', 100)
MIN_DISPLACEMENT_CANDLES = CFG['min_displacement_candles']
EXIT_CANDLES_MAX = CFG['exit_candles_max']
BREAKEVEN_CANDLES = CFG['breakeven_candles']
ENTRY_RETRACEMENT_PCT = CFG['entry_retracement_pct']
STOP_BUFFER = CFG['stop_buffer_points']
ZONE_MERGE_POINTS = CFG['zone_merge_points']
COOLDOWN_CANDLES = CFG['cooldown_candles']

# Diretório de Files do MT5 para o Indicador
MT5_DATA_PATH = r"C:\Users\Pichau\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075"

def export_dynamic_data(symbol, zones, trigger):
    """Exporta dados para arquivo específico por ativo."""
    file_path = os.path.join(MT5_DATA_PATH, "MQL5", "Files", f"liquidez_data_{symbol}.csv")
    try:
        with open(file_path, "w", encoding="ansi") as f:
            f.write("HEADER\n") 
            for z in zones:
                f.write(f"ZONE_{z['type']},{z['price']},{z['time']}\n")
            if trigger:
                type_str = "SIGNAL_SELL" if trigger['type'] == mt5.ORDER_TYPE_SELL_LIMIT else "SIGNAL_BUY"
                f.write(f"{type_str},{trigger['price']},{datetime.now()}\n")
    except Exception as e:
        print(f"[{symbol}] Erro ao exportar indicador: {e}")

def initialize_mt5():
    if not mt5.initialize():
        print(f"Erro ao inicializar MT5: {mt5.last_error()}")
        return False
    return True

def get_rates(symbol, timeframe, count):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_validated_zones(df_zones, point):
    zones = []
    if df_zones is None or len(df_zones) < MIN_DISPLACEMENT_CANDLES + 1: return zones
    raw_zones = []
    for i in range(len(df_zones) - MIN_DISPLACEMENT_CANDLES - 1):
        high, low = df_zones.iloc[i]['high'], df_zones.iloc[i]['low']
        is_res = True
        for j in range(1, MIN_DISPLACEMENT_CANDLES + 1):
            if df_zones.iloc[i+j]['high'] > high: is_res = False; break
        if is_res: raw_zones.append({'type': 'RESISTANCE', 'price': high, 'time': df_zones.iloc[i]['time'], 'idx': i})
        is_sup = True
        for j in range(1, MIN_DISPLACEMENT_CANDLES + 1):
            if df_zones.iloc[i+j]['low'] < low: is_sup = False; break
        if is_sup: raw_zones.append({'type': 'SUPPORT', 'price': low, 'time': df_zones.iloc[i]['time'], 'idx': i})
    
    valid_zones = []
    for z in raw_zones:
        invalidated = False
        for k in range(z['idx'] + MIN_DISPLACEMENT_CANDLES + 1, len(df_zones)):
            if z['type'] == 'RESISTANCE' and df_zones.iloc[k]['close'] > z['price']: invalidated = True; break
            if z['type'] == 'SUPPORT' and df_zones.iloc[k]['close'] < z['price']: invalidated = True; break
        if not invalidated: valid_zones.append(z)
    return valid_zones

def calculate_wick_metrics(candle):
    high, low, open_p, close_p = candle['high'], candle['low'], candle['open'], candle['close']
    total_size = high - low
    if total_size == 0: return 0, 0, 0
    top_wick = high - max(open_p, close_p)
    bottom_wick = min(open_p, close_p) - low
    return total_size, top_wick, bottom_wick

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def check_trigger(symbol, df_m5, zones, point, cooldowns, now_utc, df_h1=None):
    if df_m5 is None or len(df_m5) < 15 or not zones: return None, None
    last = df_m5.iloc[-2]; prev = df_m5.iloc[-3]
    df_m5['rsi'] = calculate_rsi(df_m5['close'])
    rsi = df_m5['rsi'].iloc[-2]
    
    trend = 0
    if CFG.get('use_trend_filter', True) and df_h1 is not None and len(df_h1) >= 20:
        sma = df_h1['close'].rolling(20).mean().iloc[-1]
        trend = 1 if df_h1['close'].iloc[-1] > sma else -1

    total, top, bot = calculate_wick_metrics(last)
    if total == 0: return None, None
    
    rsi_ob = CFG.get('rsi_overbought', 60); rsi_os = CFG.get('rsi_oversold', 40)
    min_w = CFG.get('min_wick_pct', 0.30)

    for z in zones:
        z_key = f"{symbol}_{z['type']}_{round(z['price'], 5)}"
        if z_key in cooldowns and now_utc - cooldowns[z_key] < timedelta(hours=1): continue

        if z['type'] == 'RESISTANCE' and last['high'] >= z['price']:
            if (top / total) >= min_w and rsi >= rsi_ob and trend <= 0:
                entry = last['high'] - (top * ENTRY_RETRACEMENT_PCT)
                return {'type': mt5.ORDER_TYPE_SELL_LIMIT, 'price': entry, 'sl': last['high'] + (STOP_BUFFER * point), 'tp': prev['low'], 'comment': f"LIQ-{symbol}-S"}, z
        elif z['type'] == 'SUPPORT' and last['low'] <= z['price']:
            if (bot / total) >= min_w and rsi <= rsi_os and trend >= 0:
                entry = last['low'] + (bot * ENTRY_RETRACEMENT_PCT)
                return {'type': mt5.ORDER_TYPE_BUY_LIMIT, 'price': entry, 'sl': last['low'] - (STOP_BUFFER * point), 'tp': prev['high'], 'comment': f"LIQ-{symbol}-B"}, z
    return None, None

def send_order(symbol, order_data):
    mode = CFG.get('execution_mode', 'limit').lower()
    point = mt5.symbol_info(symbol).point
    tick = mt5.symbol_info_tick(symbol)
    
    if mode == 'market':
        price = tick.bid if order_data['type'] == mt5.ORDER_TYPE_SELL_LIMIT else tick.ask
        order_type = mt5.ORDER_TYPE_SELL if order_data['type'] == mt5.ORDER_TYPE_SELL_LIMIT else mt5.ORDER_TYPE_BUY
        action = mt5.TRADE_ACTION_DEAL
        sl = order_data['sl']
        risk = abs(price - sl) if abs(price - sl) > 0 else point * 15
        tp = price - (risk * 1.5) if order_type == mt5.ORDER_TYPE_SELL else price + (risk * 1.5)
    else:
        price, sl, tp, order_type, action = order_data['price'], order_data['sl'], order_data['tp'], order_data['type'], mt5.TRADE_ACTION_PENDING

    for f_mode in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
        request = {"action": action, "symbol": symbol, "volume": CFG.get('lot_size', 1.0), "type": order_type, "price": price, "sl": sl, "tp": tp, "magic": MAGIC_NUMBER, "comment": order_data['comment'], "type_time": mt5.ORDER_TIME_GTC, "type_filling": f_mode}
        res = mt5.order_send(request)
        if res.retcode == mt5.TRADE_RETCODE_DONE: return res
    return res

def get_session_pnl(start_time):
    # Busca deals desde o momento exato que o robô foi ligado
    from_date = start_time
    to_date = datetime.now() + timedelta(hours=2)
    deals = mt5.history_deals_get(from_date, to_date)
    if not deals: return 0.0
    # Soma apenas trades deste robô (Magic Number)
    return sum([d.profit + d.commission + d.swap for d in deals if d.magic == MAGIC_NUMBER])

def main():
    if not initialize_mt5(): return
    mode = CFG.get('execution_mode', 'limit').upper()
    
    # Marca o momento exato do início da sessão
    SESSION_START = datetime.now() - timedelta(seconds=1)
    active_signals = {} # {symbol: signal_id}
    cooldowns = {}
    
    print(f"🚀 CENTRAL MULTI-PAIR ATIVA: {len(SYMBOLS)} ATIVOS")
    try:
        while True:
            # P&L da Sessão agora é calculado de forma absoluta desde o start
            session_pnl = get_session_pnl(SESSION_START)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print("="*65)
            print(f" SQUAD LIQUIDEZ v5.5.1 | {datetime.now().strftime('%H:%M:%S')} | P&L SESSÃO: ${session_pnl:.2f}")
            print(f" ATIVOS: {', '.join(SYMBOLS[:5])}...")
            print("="*65)

            if session_pnl >= CFG.get('daily_profit_target', 100.0):
                print("🏆 META DIÁRIA BATIDA! ENCERRANDO SESSÃO."); break

            for symbol in SYMBOLS:
                point = mt5.symbol_info(symbol).point
                df_h1 = get_rates(symbol, mt5.TIMEFRAME_H1, 50)
                df_zones = get_rates(symbol, TIMEFRAME_ZONES, LOOKBACK_ZONES)
                zones = get_validated_zones(df_zones, point)
                df_m5 = get_rates(symbol, mt5.TIMEFRAME_M5, 100)
                
                trigger, z_trig = check_trigger(symbol, df_m5, zones, point, cooldowns, datetime.now(pytz.utc), df_h1)
                
                # Gerencia posições existentes para este símbolo
                pos = mt5.positions_get(symbol=symbol, magic=MAGIC_NUMBER)
                if pos:
                    if symbol in active_signals: db_manager.update_signal_status(active_signals[symbol], "active")
                elif symbol in active_signals:
                    # Se tinha sinal mas não tem posição, verifica se fechou
                    from_d = datetime.now() - timedelta(days=1)
                    deals = mt5.history_deals_get(from_d, datetime.now() + timedelta(hours=2), group=f"*{symbol}*")
                    relevant = [d for d in deals if d.magic == MAGIC_NUMBER and d.entry == 1]
                    if relevant:
                        db_manager.update_signal_pnl(active_signals[symbol], relevant[-1].profit + relevant[-1].commission + relevant[-1].swap)
                        del active_signals[symbol]

                # Tenta nova entrada se não houver posição ou ordem pendente
                if trigger and not pos and not mt5.orders_get(symbol=symbol, magic=MAGIC_NUMBER):
                    # Registra no Supabase
                    wick_pct = 0.5 # Simplificado para multi-pair
                    res = db_manager.log_signal(trigger, wick_pct, status="awaiting_consensus")
                    if res and res.data:
                        sid = res.data[0]['id']
                        if CFG.get('use_agent_consensus') and db_manager: # Fallback simples
                             db_manager.client.table("signals_liquidez").update({"status": "approved"}).eq("id", sid).execute()
                        
                        exec_res = send_order(symbol, trigger)
                        if exec_res.retcode == mt5.TRADE_RETCODE_DONE:
                            active_signals[symbol] = sid
                            db_manager.update_signal_status(sid, "active" if CFG['execution_mode'] == 'market' else "placed")
                            cooldowns[f"{symbol}_{z_trig['type']}_{round(z_trig['price'], 5)}"] = datetime.now(pytz.utc)

                export_dynamic_data(symbol, zones, trigger)
                db_manager.log_heartbeat(symbol, "scanning", len(zones))
            
            time.sleep(30) # Varredura mais rápida para multi-pair
    finally: mt5.shutdown()

if __name__ == "__main__":
    main()
