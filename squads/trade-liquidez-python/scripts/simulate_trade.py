import time
import os
import random
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from supabase_client import SupabaseManager

def export_to_mt5(indicator_file, zones, order_data):
    """Escreve no arquivo que o indicador MQL5 lê."""
    try:
        with open(indicator_file, "w", encoding="ansi") as f:
            f.write("HEADER\n") 
            for z in zones:
                f.write(f"ZONE_{z['type']},{z['price']},{datetime.now()}\n")
            
            if order_data:
                type_str = "SIGNAL_BUY" if order_data['type'] == 2 else "SIGNAL_SELL"
                f.write(f"{type_str},{order_data['price']},{datetime.now()}\n")
        return True
    except Exception as e:
        print(f"[MT5 Sync Error] {e}")
        return False

def main():
    if not mt5.initialize():
        print("[ERRO] Não foi possível inicializar MetaTrader 5 para sincronia visual.")
        return

    try:
        data_path = mt5.terminal_info()._asdict().get('data_path')
        indicator_file = os.path.join(data_path, "MQL5", "Files", "liquidez_data.csv")
    except:
        indicator_file = "liquidez_data.csv" # Fallback local
    
    db_manager = SupabaseManager()
    symbol = "EURUSD"
    
    print("\n" + "="*60)
    print(f" 🧪 [QA SIMULADOR v2.0] CICLO COMPLETO DE OPERAÇÃO ")
    print("="*60)

    # 1. Simula Heartbeat
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 1. Enviando Heartbeat (Status: SCANNING)...")
    db_manager.log_heartbeat(symbol, "scanning", 3)
    
    fake_zones = [
        {'type': 'RESISTANCE', 'price': 1.08750},
        {'type': 'SUPPORT', 'price': 1.08500}
    ]
    export_to_mt5(indicator_file, fake_zones, None)
    time.sleep(2)

    # 2. Geração de Sinal (Awaiting Consensus)
    print("\n" + "-"*60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 2. GATILHO DETECTADO: Gerando sinal no Supabase...")
    
    order_data = {
        'symbol': symbol,
        'type': 2, # ORDER_TYPE_BUY_LIMIT
        'price': 1.08540,
        'sl': 1.08420,
        'tp': 1.08680,
        'comment': 'TESTE QA: Ciclo Completo'
    }
    
    res = db_manager.log_signal(order_data, 0.45, status="awaiting_consensus")
    if not res or not res.data:
        print("[ERRO] Falha ao registrar sinal no Supabase.")
        return
    
    signal_id = res.data[0]['id']
    export_to_mt5(indicator_file, fake_zones, order_data)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sinal {signal_id} registrado como 'awaiting_consensus'.")
    print(f"💡 DICA: Verifique a Sala de Guerra no Dashboard. Deve estar em 'EM ANÁLISE'.")

    # 3. Aguarda intervenção do auto_war_room (ou simula aqui se ele não estiver rodando)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 3. AGUARDANDO CONSENSO AGÊNTICO (30s timeout)...")
    approved = False
    for _ in range(30):
        check = db_manager.client.table("signals_liquidez").select("status", "agent_opinions").eq("id", signal_id).execute()
        if check.data and check.data[0]['status'] == 'approved':
            print(f"✅ CONSENSO OBTIDO: Agentes aprovaram o sinal {signal_id}!")
            approved = True
            break
        time.sleep(1)
    
    if not approved:
        print("⚠️ Timeout: auto_war_room.py não parece estar rodando. Forçando aprovação para continuar teste...")
        db_manager.update_signal_status(signal_id, "approved")

    # 4. Simula Ordem Colocada e Ativada
    time.sleep(3)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 4. EXECUTANDO: Transicionando para PLACED -> ACTIVE...")
    db_manager.update_signal_status(signal_id, "placed")
    time.sleep(2)
    db_manager.update_signal_status(signal_id, "active")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: ACTIVE. Verifique a tabela de Gatilhos (deve estar em verde/animado).")

    # 5. Simula Fechamento e P&L
    time.sleep(5)
    pnl_simulado = random.choice([25.50, -12.20, 45.00, 18.75])
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 5. FECHAMENTO: Encerrando operação com P&L de ${pnl_simulado:.2f}")
    db_manager.update_signal_pnl(signal_id, pnl_simulado)
    
    # Limpa MT5
    export_to_mt5(indicator_file, fake_zones, None)
    
    print("\n" + "="*60)
    print(f" ✅ [TESTE CONCLUÍDO] Sinal {signal_id} finalizado.")
    print(f" Verifique no Dashboard:")
    print(f" 1. Gráfico de Performance: Deve mostrar o P&L acumulado.")
    print(f" 2. Tabela de Gatilhos: Deve mostrar o status 'closed' e o resultado.")
    print(f" 3. Centro de Gatilhos: Esta operação deve aparecer no histórico detalhado.")
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
