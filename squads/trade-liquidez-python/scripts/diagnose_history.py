import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pytz
import os
import yaml
import sys

# Adiciona o diretório de scripts ao path
sys.path.append(os.path.dirname(__file__))
from supabase_client import SupabaseManager

def diagnose_history():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        CFG = yaml.safe_load(f)

    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return

    magic = CFG.get('magic_number', 123456)
    db = SupabaseManager()
    
    print(f"--- DIAGNÓSTICO DE HISTÓRICO (Magic: {magic}) ---")
    
    # Busca o último sinal ativo no banco
    res = db.client.table("signals_liquidez").select("*").eq("status", "active").order("created_at", desc=True).limit(1).execute()
    
    if not res.data:
        print("Nenhum sinal marcado como 'active' no banco de dados.")
        # Tenta buscar os PLACED também
        res = db.client.table("signals_liquidez").select("*").eq("status", "placed").order("created_at", desc=True).limit(1).execute()
        if not res.data: return

    signal = res.data[0]
    sid = signal['id']
    print(f"Analisando sinal {sid} ({signal['type']} em {signal['price']})")

    # Busca deals de hoje
    from_date = datetime.now() - timedelta(days=1)
    to_date = datetime.now() + timedelta(hours=1)
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals:
        found = False
        for d in deals:
            # Verifica se o deal fechou a posição (entry out = 1) e bate com a magia
            if d.magic == magic and d.entry == 1:
                pnl = d.profit + d.commission + d.swap
                print(f"✅ Encontrei fechamento no histórico! PNL: ${pnl:.2f}")
                db.update_signal_pnl(sid, pnl)
                print(f"🚀 Dashboard atualizado para o sinal {sid}")
                found = True
                break
        if not found:
            print("❌ Nenhum deal de fechamento encontrado no histórico do MT5 para este Magic Number hoje.")
            print("Ordens encontradas no histórico:")
            for d in deals[-5:]:
                print(f" - Ticket: {d.ticket}, Magic: {d.magic}, Entry: {d.entry}, Profit: {d.profit}")
    else:
        print("❌ Histórico de deals do MT5 retornou vazio.")

    mt5.shutdown()

if __name__ == "__main__":
    diagnose_history()
