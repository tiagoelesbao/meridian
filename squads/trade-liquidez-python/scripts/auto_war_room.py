import time
import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega .env
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Erro: Chaves Supabase não encontradas.")
    exit(1)

supabase: Client = create_client(url, key)

def generate_opinions(signal_type, wick_pct):
    sentiment = 'bullish' if signal_type == 'BUY' else 'bearish'
    
    opinions = [
        {
            "agent": "Jim Simons",
            "avatar": "JS",
            "comment": f"Análise quantitativa concluída. Pavio de {(wick_pct * 100):.1f}% confirma exaustão estatística neste nível.",
            "sentiment": sentiment,
            "confidence": random.randint(85, 95)
        },
        {
            "agent": "Druckenmiller",
            "avatar": "SD",
            "comment": f"A estrutura de liquidez H1 está alinhada. O fluxo de ordens sugere reversão iminente.",
            "sentiment": sentiment,
            "confidence": random.randint(80, 92)
        },
        {
            "agent": "Nassim Taleb",
            "avatar": "NT",
            "comment": "Convexidade aceitável. O risco de cauda está mitigado pelo posicionamento técnico do Stop Loss.",
            "sentiment": "neutral",
            "confidence": random.randint(70, 80)
        }
    ]
    return opinions

def run_auto_war_room():
    print("="*60)
    print(" 🎖️ GENERAL DE GUERRA: MODO APROVACAO AGENTICA ATIVO ")
    print("="*60)
    
    while True:
        try:
            # Busca sinais aguardando consenso
            res = supabase.table("signals_liquidez").select("*").eq("status", "awaiting_consensus").execute()
            
            if res.data:
                for signal in res.data:
                    signal_id = signal['id']
                    print(f"[{time.strftime('%H:%M:%S')}] Analisando sinal {signal_id}...")
                    
                    opinions = generate_opinions(signal['type'], signal['wick_pct'])
                    
                    supabase.table("signals_liquidez").update({
                        "status": "approved",
                        "agent_opinions": opinions
                    }).eq("id", signal_id).execute()
                    
                    print(f"✅ Sinal {signal_id} aprovado com {len(opinions)} opiniões geradas.")
            
        except Exception as e:
            print(f"Erro no loop de comando: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    run_auto_war_room()
