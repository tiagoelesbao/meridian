import MetaTrader5 as mt5
import os
import sys

# Adiciona o diretório de scripts ao path
sys.path.append(os.path.dirname(__file__))

def validate_final_execution():
    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return

    symbol = "EURUSD"
    lot = 0.01
    
    print(f"--- VALIDANDO EXECUÇÃO REAL (MODO AUTO-FILLING) ---")
    
    # Busca preço atual
    tick = mt5.symbol_info_tick(symbol)
    
    # Modos para testar na sequência
    filling_modes = [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]
    
    success = False
    for f_mode in filling_modes:
        print(f"Tentando modo: {f_mode}...", end=" ")
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": tick.bid,
            "magic": 123456,
            "comment": "VALIDACAO FINAL",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": f_mode,
        }

        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ SUCESSO!")
            print(f"A corretora aceitou o modo {f_mode}. Ticket: {result.order}")
            
            # Fecha a posição imediatamente
            close_tick = mt5.symbol_info_tick(symbol)
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "position": result.order,
                "price": close_tick.ask,
                "magic": 123456,
                "comment": "FECHANDO VALIDACAO",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": f_mode,
            }
            mt5.order_send(close_request)
            print("Posição de teste encerrada.")
            success = True
            break
        else:
            print(f"❌ FALHOU ({result.comment})")

    if not success:
        print("\n[ALERTA CRÍTICO] Nenhum modo de preenchimento foi aceito pela corretora.")
    
    mt5.shutdown()

if __name__ == "__main__":
    validate_final_execution()
