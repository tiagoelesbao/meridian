import os
import requests
from supabase_client import SupabaseManager

def check_tables():
    manager = SupabaseManager()
    if not manager.client:
        print("[ERRO] Supabase não configurado. Verifique o seu .env")
        return

    tables = ["bot_heartbeats", "signals_liquidez"]
    missing = []

    print("--- DIAGNÓSTICO DE BANCO DE DATA BASE ---")
    for table in tables:
        try:
            # Tenta um select de 0 linhas
            manager.client.table(table).select("*").limit(0).execute()
            print(f"[OK] Tabela '{table}' encontrada.")
        except Exception as e:
            if "PGRST205" in str(e) or "not find" in str(e).lower():
                print(f"[FALHA] Tabela '{table}' NÃO ENCONTRADA.")
                missing.append(table)
            else:
                print(f"[ERRO] Erro ao verificar '{table}': {e}")

    if missing:
        print("\n" + "!"*40)
        print("AÇÃO NECESSÁRIA: Crie as tabelas no SQL Editor do Supabase!")
        print("Copie e cole os comandos abaixo no seu painel Supabase:")
        print("!"*40 + "\n")
        
        sql = """
-- 1. Tabela de Sinais (ou Atualização)
CREATE TABLE IF NOT EXISTS signals_liquidez (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    symbol TEXT,
    type TEXT,
    price DECIMAL,
    sl DECIMAL,
    tp DECIMAL,
    magic INT8,
    wick_pct DECIMAL,
    status TEXT DEFAULT 'pending',
    pnl DECIMAL DEFAULT 0.0,
    agent_opinions JSONB DEFAULT '[]'::jsonb,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Script de Migração (Caso a tabela já exista)
-- ALTER TABLE signals_liquidez ADD COLUMN IF NOT EXISTS pnl DECIMAL DEFAULT 0.0;
-- ALTER TABLE signals_liquidez ADD COLUMN IF NOT EXISTS agent_opinions JSONB DEFAULT '[]'::jsonb;
-- ALTER TABLE signals_liquidez ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP WITH TIME ZONE;

-- 2. Tabela de Heartbeats
CREATE TABLE IF NOT EXISTS bot_heartbeats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    symbol TEXT,
    status TEXT,
    active_zones INT
);

-- Habilitar Realtime para as tabelas
alter publication supabase_realtime add table signals_liquidez;
alter publication supabase_realtime add table bot_heartbeats;
        """
        print(sql)
    else:
        print("\n[SUCESSO] Todas as tabelas estão prontas. O sistema está estável.")

if __name__ == "__main__":
    check_tables()
