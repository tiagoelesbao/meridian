import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def test_anon_access():
    env_path = Path('.env')
    load_dotenv(dotenv_path=env_path)
    
    url = os.environ.get('SUPABASE_URL')
    anon_key = os.environ.get('SUPABASE_ANON_KEY')
    
    print(f"Testando acesso ANON para {url}")
    client = create_client(url, anon_key)
    
    try:
        res = client.table('bot_heartbeats').select('*').limit(1).execute()
        print(f"[SUCESSO] Leitura anonima ok: {res.data}")
    except Exception as e:
        print(f"[FALHA] Erro de leitura anonima: {e}")

if __name__ == "__main__":
    test_anon_access()
