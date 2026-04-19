import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega o .env da raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

# Chaves necessárias para operação administrativa (Delete)
url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Service Role é necessária para DELETE sem RLS bypass

if not url or not key:
    print(f"❌ Erro: Chaves do Supabase não encontradas no .env em {env_path}")
    print(f"URL: {'OK' if url else 'MISSING'}")
    print(f"KEY: {'OK' if key else 'MISSING'}")
    exit(1)

supabase: Client = create_client(url, key)

def clean_production_db():
    print("="*60)
    print(" 🧹 LIMPANDO DADOS DE TESTE (PRODUCAO) ")
    print("="*60)
    
    try:
        # 1. Limpar Sinais de Teste
        # Como não temos coluna 'comment', limpamos sinais 'pending' de EURUSD (padrão de teste)
        # Se você quiser limpar TUDO para começar do zero, use .delete().neq("symbol", "NONE")
        res_signals = supabase.table("signals_liquidez").delete().eq("status", "pending").execute()
        count_signals = len(res_signals.data) if res_signals.data else 0
        print(f"✅ Sinais de teste (pending) removidos: {count_signals}")
        
        # 2. Limpar Heartbeats de Teste
        # Removemos todos os heartbeats para o dashboard resetar o status do robô
        res_hb = supabase.table("bot_heartbeats").delete().neq("symbol", "NONE").execute()
        count_hb = len(res_hb.data) if res_hb.data else 0
        print(f"✅ Heartbeats de teste removidos: {count_hb}")
        
        print("\n✨ Banco de dados limpo e pronto para a sessão real!")
        
        # 3. Limpar Logs de ML de Teste (se existirem na nuvem futuramente)
        # print("Opcional: Limpando logs de ML temporários...")
        
        print("\n✨ Banco de dados limpo e pronto para a sessão real!")
        
    except Exception as e:
        print(f"❌ Erro crítico durante a limpeza: {e}")

if __name__ == "__main__":
    clean_production_db()
