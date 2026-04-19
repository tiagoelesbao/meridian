import os
import sys
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
import random

# Carregar Config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

sys.path.append(os.path.dirname(__file__))
import bot_liquidez

def run_replay_for_symbol(symbol, local_cfg):
    # Otimização: Tenta baixar o máximo de histórico que a corretora permitir (Visando 1 ano)
    target_candles = 90000 
    m5_rates = None
    
    while target_candles >= 10000:
        m5_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, target_candles)
        if m5_rates is not None and len(m5_rates) > 1000:
            break
        target_candles -= 10000
    
    if m5_rates is None:
        print(f"❌ Erro: Não foi possível obter histórico M5 para {symbol}.")
        return 0, []

    actual_count = len(m5_rates)
    m15_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, int(actual_count/3))
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, int(actual_count/12))
    
    if h1_rates is None or m15_rates is None:
        print(f"❌ Erro: Timeframes superiores ausentes para {symbol}.")
        return 0, []

    s_info = mt5.symbol_info(symbol)
    point = s_info.point
    pip_val = 10.0 if "JPY" not in symbol else 7.5
    # Spread Realista: Majors (1.5 pips) / Crosses e JPY (2.5 pips)
    fixed_spread = (1.5 if "JPY" not in symbol else 2.5)
    cost_usd = fixed_spread * 10.0 
    
    mt5.shutdown()

    df_m5 = pd.DataFrame(m5_rates); df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s', utc=True)
    df_m15 = pd.DataFrame(m15_rates); df_m15['time'] = pd.to_datetime(df_m15['time'], unit='s', utc=True)
    df_h1 = pd.DataFrame(h1_rates); df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s', utc=True)

    df_m5['rsi'] = bot_liquidez.calculate_rsi(df_m5['close'])
    df_h1['sma20'] = df_h1['close'].rolling(20).mean()
    all_zones = bot_liquidez.get_validated_zones(df_m15 if local_cfg['zone_timeframe'] == "M15" else df_h1, point)

    balance, history, cooldowns, active_pos = 0.0, [], {}, None
    rsi_ob, rsi_os = local_cfg['rsi_overbought'], local_cfg['rsi_oversold']
    
    for i in range(500, len(df_m5) - 1):
        candle = df_m5.iloc[i]
        curr_t = candle['time']
        
        if active_pos:
            pos = active_pos
            p_diff, closed, exit_p = 0, False, 0
            if pos['type'] == 'BUY':
                if candle['low'] <= pos['sl']: p_diff = (pos['sl'] - pos['entry']) / (point * 10); closed = True; reason = 'SL'; exit_p = pos['sl']
                elif candle['high'] >= pos['tp']: p_diff = (pos['tp'] - pos['entry']) / (point * 10); closed = True; reason = 'TP'; exit_p = pos['tp']
            else:
                if candle['high'] >= pos['sl']: p_diff = (pos['entry'] - pos['sl']) / (point * 10); closed = True; reason = 'SL'; exit_p = pos['sl']
                elif candle['low'] <= pos['tp']: p_diff = (pos['entry'] - pos['tp']) / (point * 10); closed = True; reason = 'TP'; exit_p = pos['tp']
            
            if not closed and (i - pos['idx']) >= local_cfg['exit_candles_max']:
                p_diff = (candle['close'] - pos['entry']) / (point * 10) if pos['type'] == 'BUY' else (pos['entry'] - candle['close']) / (point * 10); closed = True; reason = 'TIME'; exit_p = candle['close']
                
            if closed:
                # Realismo: Slippage randômico (0 a 0.2 pips) + Spread fixo
                slippage = random.uniform(0, 0.2) * 10.0
                pnl_real = (p_diff * pip_val) - cost_usd - slippage
                balance += pnl_real
                history.append({**pos, 'pnl': pnl_real, 'reason': reason, 'exit_p': exit_p, 'exit_t': curr_t})
                active_pos = None
            continue

        h1_avail = df_h1[df_h1['time'] < curr_t]
        if len(h1_avail) < 20: continue
        trend = 1 if h1_avail.iloc[-1]['close'] > h1_avail.iloc[-1]['sma20'] else -1
        
        for z in [z for z in all_zones if z['time'] < curr_t]:
            z_key = f"{symbol}_{z['type']}_{round(z['price'], 5)}"
            if z_key in cooldowns and curr_t - cooldowns[z_key] < timedelta(hours=1): continue
            
            if z['type'] == 'RESISTANCE' and candle['high'] >= z['price'] and candle['rsi'] >= rsi_ob and trend == -1:
                e = candle['close']; sl = candle['high'] + (local_cfg['stop_buffer_points'] * point)
                active_pos = {'type': 'SELL', 'entry': e, 'sl': sl, 'tp': e - ((sl-e)*1.5), 'idx': i, 'time': curr_t, 'z_price': z['price'], 'rsi': candle['rsi'], 'trend': trend}
                cooldowns[z_key] = curr_t; break
            
            if z['type'] == 'SUPPORT' and candle['low'] <= z['price'] and candle['rsi'] <= rsi_os and trend == 1:
                e = candle['close']; sl = candle['low'] - (local_cfg['stop_buffer_points'] * point)
                active_pos = {'type': 'BUY', 'entry': e, 'sl': sl, 'tp': e + ((e-sl)*1.5), 'idx': i, 'time': curr_t, 'z_price': z['price'], 'rsi': candle['rsi'], 'trend': trend}
                cooldowns[z_key] = curr_t; break

    # Exporta para Auditoria v3.0 (Mantém paridade)
    if not mt5.initialize(): mt5.initialize()
    terminal_info = mt5.terminal_info()._asdict()
    mt5_path = terminal_info.get('data_path')
    audit_file = os.path.join(mt5_path, "MQL5", "Files", f"audit_backtest_{symbol}.csv")
    try:
        with open(audit_file, "w", encoding="ansi") as f:
            f.write("type,price,time,pnl,z_price,rsi,trend,exit_p,exit_t\n")
            for t in history:
                t_type = "SIGNAL_BUY" if t['type'] == 'BUY' else "SIGNAL_SELL"
                f.write(f"{t_type},{t['entry']},{t['time'].strftime('%Y.%m.%d %H:%M')},{t['pnl']:.2f},{t['z_price']},{t['rsi']:.1f},{t['trend']},{t['exit_p']},{t['exit_t'].strftime('%Y.%m.%d %H:%M')}\n")
    except: pass

    return balance, history

def run():
    if not mt5.initialize():
        print("Erro: Não foi possível conectar ao terminal MetaTrader 5.")
        return

    print("🚀 Iniciando Backtest Anual DETALHADO v5.7.2...")
    all_res = []
    for s in CFG['symbols']:
        print(f"Analisando {s}...", end=" ", flush=True)
        pnl, hist = run_replay_for_symbol(s, CFG)
        print(f"✅ ${pnl:.2f} ({len(hist)} trades)")
        all_res.append({'symbol': s, 'pnl': pnl, 'history': hist})
    
    total_pnl = sum([r['pnl'] for r in all_res])
    total_trades = sum([len(r['history']) for r in all_res])
    
    report = f"# 💎 Relatório Anual Profissional Sniper v5.7.2\n\n"
    report += f"**Período:** ~1 Ano | **Meta:** $100/dia | **PNL TOTAL:** ${total_pnl:.2f}\n"
    report += f"**Média por Operação:** ${ (total_pnl / total_trades if total_trades > 0 else 0):.2f}\n\n"
    
    report += "## 📊 Performance por Ativo\n\n"
    report += "| Ativo | PNL USD | Win Rate | Trades |\n|:---:|:---:|:---:|:---:|\n"
    for res in all_res:
        if not res['history']: continue
        wins = len([t for t in res['history'] if t['pnl'] > 0])
        wr = (wins/len(res['history'])*100)
        report += f"| {res['symbol']} | ${res['pnl']:.2f} | {wr:.1f}% | {len(res['history'])} |\n"
    
    report += "\n## 🕵️ Detalhamento de Todas as Operações\n\n"
    for res in all_res:
        if not res['history']: continue
        report += f"### 🌐 {res['symbol']}\n"
        report += "| Entrada | Saída | Duração | Direção | PNL | Racional |\n|:---:|:---:|:---:|:---:|:---:|:---|\n"
        for t in res['history']:
            duracao = int((t['exit_t'] - t['time']).total_seconds() / 60)
            status = "✅" if t['pnl'] > 0 else "❌"
            report += f"| {t['time'].strftime('%d/%m %H:%M')} | {t['exit_t'].strftime('%H:%M')} | {duracao}m | {t['type']} | {t['pnl']:.2f} | {status} RSI:{t['rsi']:.1f} |\n"
        report += "\n---\n"

    with open("docs/relatorio_anual_sniper.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    mt5.shutdown()
    print(f"\n✨ SUCESSO! Relatório v5.7.2 com {total_trades} trades gerado.")

if __name__ == "__main__":
    run()
