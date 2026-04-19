import os
from supabase_client import SupabaseManager
from dotenv import load_dotenv

def clean_test_data():
    db = SupabaseManager()
    if not db.client:
        print("Erro: Supabase não configurado.")
        return

    print("--- LIMPANDO AMBIENTE DE TRADING ---")
    
    # 1. Limpa Sinais de Teste
    try:
        # Apaga todos os sinais para começar do zero (ou apenas os de hoje se preferir)
        res_signals = db.client.table("signals_liquidez").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Sinais de teste removidos.")
    except Exception as e:
        print(f"Erro ao limpar sinais: {e}")

    # 2. Limpa Heartbeats antigos
    try:
        res_hb = db.client.table("bot_heartbeats").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Heartbeats antigos removidos.")
    except Exception as e:
        print(f"Erro ao limpar heartbeats: {e}")

    print("--- AMBIENTE PRONTO PARA OPERAÇÃO REAL ---")

if __name__ == "__main__":
    clean_test_data()
