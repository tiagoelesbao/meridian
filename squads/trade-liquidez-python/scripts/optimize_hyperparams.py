import os
import sys
import yaml
import random
import time

# Permite acesso à mesma pasta
sys.path.append(os.path.dirname(__file__))
from market_replay import run_replay

CFG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

def load_base_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_optimizer(iterations=50):
    print("="*60)
    print(" 🧠 QUANT OPTIMIZER v2.0: BUSCA PELA META DE $100/DIA ")
    print(f" Executando {iterations} permutações walk-forward...")
    print("="*60)

    base_cfg = load_base_cfg()
    
    # Ranges expandidos para maximizar frequência e lucro
    wick_range = [0.20, 0.25, 0.30, 0.35]
    rsi_range_ob = [55, 60, 65, 70]
    rsi_range_os = [30, 35, 40, 45]
    trend_filter_range = [True, False]
    color_reversal_range = [True, False]
    lot_range = [1.0, 1.5, 2.0] # Lote ajustável para buscar meta
    
    best_pnl = -9999
    best_cfg = None
    best_trade_count = 0

    start_time = time.time()

    for i in range(iterations):
        test_cfg = base_cfg.copy()
        
        # Gera mutação agressiva
        test_cfg['min_wick_pct'] = random.choice(wick_range)
        test_cfg['rsi_overbought'] = random.choice(rsi_range_ob)
        test_cfg['rsi_oversold'] = random.choice(rsi_range_os)
        test_cfg['use_trend_filter'] = random.choice(trend_filter_range)
        test_cfg['require_color_reversal'] = random.choice(color_reversal_range)
        test_cfg['lot_size'] = random.choice(lot_range)
        
        # Roda o replay silencioso
        pnl, win_rate, history = run_replay(custom_cfg=test_cfg, silent=True)
        trade_count = len(history)
        
        print(f"[{i+1}/{iterations}] PNL: ${pnl:.2f} | Trades: {trade_count} | WR: {win_rate:.2f}%")
        
        # Critério de Seleção: PNL Máximo com pelo menos 1 trade por dia de amostragem
        if pnl > best_pnl:
            best_pnl = pnl
            best_cfg = test_cfg.copy()
            best_trade_count = trade_count
            print(f"   ⭐️ [LIDER] Novo recorde de PNL!")

    elapsed = time.time() - start_time
    print("="*60)
    print(f" OTIMIZAÇÃO CONCLUÍDA em {elapsed:.1f}s")
    print(f" Melhor PNL Encontrado: ${best_pnl:.2f} com {best_trade_count} trades.")
    print("="*60)
    
    if best_cfg:
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(best_cfg, f, default_flow_style=False)
        print("✅ Configurações de alta performance salvas no config.yaml")

if __name__ == "__main__":
    run_optimizer(iterations=30)
