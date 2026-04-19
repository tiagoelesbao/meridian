import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega .env
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Erro: Chaves Supabase não encontradas.")
    exit(1)

supabase: Client = create_client(url, key)

def list_pending():
    res = supabase.table("signals_liquidez").select("*").eq("status", "awaiting_consensus").execute()
    return res.data if res.data else []

def vote(signal_id, decision, reason=""):
    status = "approved" if decision == "yes" else "rejected"
    supabase.table("signals_liquidez").update({"status": status}).eq("id", signal_id).execute()
    print(f"Sinal {signal_id} {status.upper()} | Motivo: {reason}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        pending = list_pending()
        if not pending:
            print("Nenhum sinal aguardando consenso.")
        for s in pending:
            print(f"ID: {s['id']} | {s['type']} @ {s['price']} | Wick: {s['wick_pct']}")
    else:
        # Uso: python war_room_voter.py <id> <yes/no> <reason>
        sid = sys.argv[1]
        dec = sys.argv[2]
        msg = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "No reason"
        vote(sid, dec, msg)
