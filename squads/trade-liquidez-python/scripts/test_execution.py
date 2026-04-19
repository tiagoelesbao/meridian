import MetaTrader5 as mt5
import os
import yaml

def test_order_execution():
    if not mt5.initialize():
        print("Erro ao inicializar MT5")
        return

    symbol = "EURUSD"
    lot = 0.01 # Teste com lote mínimo para segurança
    
    # Busca preços atuais
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Erro ao obter preço para {symbol}")
        return

    print(f"--- TESTE DE EXECUÇÃO REAL ---")
    print(f"Preço Atual Bid: {tick.bid}")

    # Tenta enviar uma ordem a mercado (SELL)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": tick.bid,
        "magic": 999999,
        "comment": "TESTE DE PERMISSAO",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN, # Vamos testar se esse é o problema
    }

    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ FALHA NA EXECUÇÃO!")
        print(f"Código de Retorno: {result.retcode}")
        print(f"Mensagem do MT5: {result.comment}")
        
        # Se falhou por preenchimento, tentamos outro modo
        if "filling" in result.comment.lower() or result.retcode == 10030:
            print("\nTentando com outro modo de preenchimento (IOC)...")
            request["type_filling"] = mt5.ORDER_FILLING_IOC
            result2 = mt5.order_send(request)
            print(f"Resultado IOC: {result2.comment} ({result2.retcode})")
    else:
        print(f"✅ SUCESSO! Ordem executada. Ticket: {result.order}")
        # Fecha a ordem de teste imediatamente
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "position": result.order,
            "price": mt5.symbol_info_tick(symbol).ask,
            "magic": 999999,
            "comment": "FECHANDO TESTE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": request["type_filling"],
        }
        mt5.order_send(close_request)
        print("Ordem de teste fechada.")

    mt5.shutdown()

if __name__ == "__main__":
    test_order_execution()
