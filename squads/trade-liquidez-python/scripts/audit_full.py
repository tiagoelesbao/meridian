import MetaTrader5 as mt5
from datetime import datetime, timedelta

def audit_full_history():
    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return

    # Busca TODO o histórico disponível
    from_date = datetime.now() - timedelta(days=365)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals:
        print(f"\n--- RELATÓRIO COMPLETO DE HISTÓRICO (MT5) ---")
        # Mostra os últimos 20 deals para vermos o que aconteceu recentemente
        for d in deals[-20:]:
            type_str = "BUY" if d.type == 0 else "SELL"
            print(f"[{datetime.fromtimestamp(d.time)}] Ticket: {d.ticket} | {d.symbol} | {type_str} | Lucro: ${d.profit:.2f} | Magic: {d.magic} | Comentário: '{d.comment}'")
    else:
        print("Nenhum registro encontrado.")

    mt5.shutdown()

if __name__ == "__main__":
    audit_full_history()
