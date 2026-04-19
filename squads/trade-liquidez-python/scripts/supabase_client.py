import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Localiza o .env na raiz do projeto usando caminho absoluto resolvido
env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"[ERRO CRÍTICO] Arquivo .env não encontrado em: {env_path}")

class SupabaseManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Bypasses RLS for backend bot
        if not url or not key:
            self.client = None
            print(f"[AVISO] Supabase desativado. Chaves ausentes no .env.")
        else:
            self.client = create_client(url, key)
            # Log de depuração mascarado para segurança
            masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
            print(f"[Supabase] Conectado. Chave: {masked_key} (Service Role)")

    def log_heartbeat(self, symbol, status, active_zones):
        """Envia batimento cardíaco para o dashboard."""
        if not self.client: return
        try:
            data = {
                "symbol": symbol,
                "status": status,
                "active_zones": active_zones
            }
            # Upsert para manter apenas um registro por símbolo se quiser apenas o status atual
            # Ou insert para histórico. Vamos usar upsert no ID fixo ou apenas insert para simplicidade.
            self.client.table("bot_heartbeats").insert(data).execute()
        except Exception as e:
            if "PGRST205" in str(e) or "not find the table" in str(e).lower():
                print("[Supabase ALERT] Tabela 'bot_heartbeats' ausente. Rode o SQL Editor no painel Supabase.")
            else:
                print(f"[Supabase] Erro ao enviar heartbeat: {e}")

    def log_signal(self, order_data, wick_pct, status="pending"):
        """Registra um novo sinal de liquidez."""
        if not self.client: return None
        try:
            # Identifica o tipo baseado no comentário ou no tipo da ordem MT5
            comment = order_data.get('comment', '').upper()
            order_type = order_data.get('type', 0)
            
            # Se for ordem tipo 1, 3, 5 (SELL) ou comentário tiver 'RESISTENCIA' ou 'SELL'
            is_sell = "SELL" in comment or "RESISTENCIA" in comment or order_type in [1, 3, 5]
            sig_type = "SELL" if is_sell else "BUY"

            data = {
                "symbol": order_data.get('symbol', 'EURUSD'),
                "type": sig_type,
                "price": order_data['price'],
                "sl": order_data['sl'],
                "tp": order_data['tp'],
                "magic": 123456,
                "wick_pct": wick_pct,
                "status": status,
                "pnl": 0.0,
                "agent_opinions": []
            }
            return self.client.table("signals_liquidez").insert(data).execute()
        except Exception as e:
            print(f"[Supabase] Erro ao registrar sinal: {e}")
            return None

    def update_signal_status(self, signal_id, status):
        """Atualiza o status de um sinal (ex: 'placed', 'active', 'closed')."""
        if not self.client: return
        try:
            self.client.table("signals_liquidez").update({"status": status}).eq("id", signal_id).execute()
        except Exception as e:
            print(f"[Supabase] Erro ao atualizar status: {e}")

    def update_signal_pnl(self, signal_id, pnl, status="closed"):
        """Registra o resultado final do sinal (Lucro/Prejuízo)."""
        if not self.client: return
        try:
            self.client.table("signals_liquidez").update({
                "pnl": pnl,
                "status": status,
                "closed_at": "now()"
            }).eq("id", signal_id).execute()
        except Exception as e:
            print(f"[Supabase] Erro ao registrar PNL: {e}")
