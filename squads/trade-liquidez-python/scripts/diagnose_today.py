import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
import yaml

# Carrega config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

# Pega a lista de símbolos ou o símbolo único (compatibilidade)
SYMBOLS = CFG.get('symbols', [CFG.get('symbol', 'EURUSD')])

def calculate_wick_metrics(candle):
    high, low, open_p, close_p = candle['high'], candle['low'], candle['open'], candle['close']
    total_size = high - low
    if total_size == 0: return 0.00001, 0, 0
    top_wick = high - max(open_p, close_p)
    bottom_wick = min(open_p, close_p) - low
    return total_size, top_wick, bottom_wick

def diagnose_symbol(symbol):
    print(f"\n[DIAGNOSTICO] ANALISANDO: {symbol}")
    print("-" * 60)

    # 1. Busca Zonas (M15 ou H1 conforme config)
    tf_zones_str = CFG.get('zone_timeframe', 'H1')
    tf_zones = mt5.TIMEFRAME_M15 if tf_zones_str == "M15" else mt5.TIMEFRAME_H1
    
    rates_zones = mt5.copy_rates_from_pos(symbol, tf_zones, 0, 100)
    if rates_zones is None:
        print(f"Erro ao carregar dados {tf_zones_str} para {symbol}")
        return
        
    df_zones = pd.DataFrame(rates_zones)
    df_zones['time'] = pd.to_datetime(df_zones['time'], unit='s')
    
    zones = []
    min_dist = CFG.get('min_displacement_candles', 7)
    for i in range(len(df_zones) - min_dist - 1):
        if all(df_zones.iloc[i]['high'] >= df_zones.iloc[i+j]['high'] for j in range(1, min_dist+1)):
            zones.append({'type': 'RESISTANCE', 'price': df_zones.iloc[i]['high']})
        if all(df_zones.iloc[i]['low'] <= df_zones.iloc[i+j]['low'] for j in range(1, min_dist+1)):
            zones.append({'type': 'SUPPORT', 'price': df_zones.iloc[i]['low']})

    print(f"OK: Encontradas {len(zones)} zonas de {tf_zones_str} no historico recente.")

    # 2. Busca data de hoje
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    rates_m5 = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, today, datetime.now())
    
    if rates_m5 is None or len(rates_m5) < 3:
        print("Sem dados de M5 para hoje.")
        return

    df_m5 = pd.DataFrame(rates_m5)
    df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s')

    rejection_reasons = {"COLOR": 0, "WICK": 0, "NO_ZONE": 0}

    for i in range(2, len(df_m5)):
        last = df_m5.iloc[i-1]; prev = df_m5.iloc[i-2]

        if CFG.get('require_color_reversal', True):
            if (last['close'] > last['open']) == (prev['close'] > prev['open']):
                rejection_reasons["COLOR"] += 1; continue

        in_zone = False; zone_hit = None
        for z in zones:
            if z['type'] == 'RESISTANCE' and last['high'] >= z['price']: in_zone = True; zone_hit = z; break
            if z['type'] == 'SUPPORT' and last['low'] <= z['price']: in_zone = True; zone_hit = z; break

        if not in_zone:
            rejection_reasons["NO_ZONE"] += 1; continue

        total, top, bot = calculate_wick_metrics(last)
        wick_pct = top/total if zone_hit['type'] == 'RESISTANCE' else bot/total
        if wick_pct < CFG.get('min_wick_pct', 0.30):
            rejection_reasons["WICK"] += 1; continue

        print(f"SINAL ENCONTRADO! Time: {last['time']} | Price: {last['close']} | Wick: {wick_pct:.2f}")

    print(f"\nREJEIÇÕES EM {symbol}:")
    print(f" - Cor: {rejection_reasons['COLOR']} | Zona: {rejection_reasons['NO_ZONE']} | Pavio: {rejection_reasons['WICK']}")

def diagnose():
    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return
    
    for symbol in SYMBOLS:
        diagnose_symbol(symbol)
    
    mt5.shutdown()

if __name__ == "__main__":
    diagnose()
