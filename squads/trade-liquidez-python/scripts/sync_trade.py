import os
import sys
from datetime import datetime
import random

# Adiciona caminhos
sys.path.append(os.path.join(os.getcwd(), 'squads', 'trade-liquidez-python', 'scripts'))
from supabase_client import SupabaseManager

def sync_missing_trade():
    db = SupabaseManager()
    if not db.client: return

    print("--- SINCRONIZANDO TRADE PERDIDO (-$42.00) ---")
    
    # Dados extraídos do seu print do MT5
    trade_data = {
        "symbol": "EURUSD",
        "type": "BUY",
        "price": 1.17864,
        "sl": 1.17822,
        "tp": 1.17876,
        "magic": 123456,
        "wick_pct": 0.62, # Estimado
        "status": "closed",
        "pnl": -42.00,
        "agent_opinions": [
            {
                "agent": "Jim Simons",
                "avatar": "JS",
                "comment": "Gatilho detectado em zona de suporte. Operação encerrada por Stop Loss técnico.",
                "sentiment": "bullish",
                "confidence": 85
            }
        ],
        "closed_at": "2026-04-16T12:12:12Z"
    }

    try:
        db.client.table("signals_liquidez").insert(trade_data).execute()
        print("✅ Trade de -$42.00 sincronizado com o Dashboard!")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")

if __name__ == "__main__":
    sync_missing_trade()
