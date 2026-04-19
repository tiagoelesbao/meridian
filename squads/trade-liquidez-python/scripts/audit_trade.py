import MetaTrader5 as mt5
from datetime import datetime, timedelta

def audit_specific_trade():
    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return

    # Busca o histórico das últimas 24 horas
    from_date = datetime.now() - timedelta(days=1)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals:
        print(f"\n--- AUDITORIA DE ORDENS (ÚLTIMAS 24H) ---")
        for d in deals:
            # Focamos no trade de prejuízo alto que você mencionou (-$42.00)
            if d.profit < -5.0 or d.profit > 5.0: 
                print(f"\nORDEM DETECTADA:")
                print(f" - Ticket: {d.ticket}")
                print(f" - Símbolo: {d.symbol}")
                print(f" - Tipo: {'BUY' if d.type == 0 else 'SELL'}")
                print(f" - Lucro Real: ${d.profit:.2f}")
                print(f" - Comentário: '{d.comment}'")
                print(f" - Magic Number: {d.magic}")
                print(f" - Expert ID (Interno): {d.external_id}")
                
                if d.magic == 0:
                    print(" 🚩 ALERTA: Esta ordem tem Magic Number 0. Isso indica entrada MANUAL via terminal.")
                elif d.magic == 123456:
                    print(" ✅ INFO: Esta ordem foi enviada pelo nosso Robô de Liquidez.")
                else:
                    print(f" 🚩 ALERTA: Esta ordem foi enviada por OUTRO ROBÔ (Magic: {d.magic}).")
    else:
        print("Nenhum registro encontrado no histórico.")

    mt5.shutdown()

if __name__ == "__main__":
    audit_specific_trade()
