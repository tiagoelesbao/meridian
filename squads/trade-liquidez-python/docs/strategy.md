# 📜 Documento de Estratégia: Sniper v5.7 (Multi-Pair)

Este documento detalha o racional técnico, os algoritmos e as configurações estratégicas que governam o robô de trading autônomo. A estratégia é baseada no conceito de **Liquidez Institucional com Reversão à Média**.

---

## 🎯 1. Filosofia da Estratégia
O robô não tenta prever o mercado. Ele atua como um **reator estatístico** que busca por "zonas de exaustão". A premissa é que grandes instituições "caçam" liquidez acima de topos e abaixo de fundos antes de mover o preço na direção oposta.

### Pilares Sniper:
1.  **Contexto Macro (Filtro H1):** Operar apenas a favor da tendência primária.
2.  **Estrutura Micro (Zonas M15):** Identificar suportes e resistências recentes com força institucional.
3.  **Gatilho de Confirmação (Wick + RSI):** Validar a rejeição de preço via anatomia de pavio e sobre-extensão do oscilador.

---

## 🛠️ 2. Parâmetros de Configuração (`config.yaml`)

### A. Filtros de Entrada
*   `min_wick_pct` (0.30): Exige que o pavio seja pelo menos 30% do tamanho total da vela. Pavios curtos indicam falta de força na reversão.
*   `rsi_overbought` (60) / `rsi_oversold` (40): O IFR (RSI) deve estar nesses extremos para autorizar a entrada. Evita compras em topos de RSI ou vendas em fundos de RSI.
*   `use_trend_filter` (true): Habilita o filtro de Média Móvel Simples (SMA 20) no gráfico de 1 hora.
    *   **BUY:** Preço H1 > SMA20.
    *   **SELL:** Preço H1 < SMA20.
*   `require_color_reversal` (true): Exige que a vela de entrada tenha cor oposta à anterior (ex: candle verde após candle vermelho em um suporte).

### B. Mapeamento de Zonas
*   `zone_timeframe` ("M15"): O robô analisa o gráfico de 15 minutos para traçar os retângulos de liquidez.
*   `min_displacement_candles` (7): Para um ponto ser considerado zona, o preço precisa ter se afastado dele por pelo menos 7 velas sem retornar. Isso confirma a "rejeição institucional".
*   `lookback_zones` (100): O robô olha para as últimas 100 velas do timeframe de zona para mapear o cenário.

---

## 📉 3. Gestão de Risco e Execução

### A. Alvos Dinâmicos (Matemática Sniper)
No modo **MARKET**, o robô não usa alvos fixos, ele os calcula no milisegundo da entrada:
1.  **Stop Loss (SL):** Posicionado na mínima/máxima do pavio que gerou o gatilho + `stop_buffer_points`.
2.  **Take Profit (TP):** Calculado automaticamente para buscar um **Risk/Reward de 1.5x**. Se o risco for de 10 pips, o alvo será de 15 pips.

### B. Proteções Ativas
*   `breakeven_candles` (4): Se o trade durar mais de 4 velas e estiver no lucro, o SL é movido para o preço de entrada (proteção de capital).
*   `exit_candles_max` (8): Se o trade não atingir o alvo em 8 velas, o robô encerra a posição "a mercado" para evitar exposição a eventos inesperados.
*   `cooldown_candles` (12): Após operar em uma zona, o robô a ignora por 1 hora para evitar "viciar" em um ponto que pode estar se enfraquecendo.

---

## 🌍 4. Operação Multi-Ativo
O robô itera sobre a lista `symbols`, processando cada par de moedas de forma independente. 
*   **Gerenciamento de P&L:** O lucro é consolidado em uma sessão global.
*   **Controle de Meta:** Ao atingir o `daily_profit_target` (ex: $100), o robô encerra todos os processos para garantir o lucro do dia.

---

## 🧪 5. Validação Institucional (Audit)
Para garantir que a estratégia não seja tendenciosa, o robô utiliza o `market_replay.py` v5.7 com:
*   **Slippage Real:** 0 a 0.2 pips de atraso.
*   **Spread Fixo:** 1.5 a 2.5 pips por ativo.
*   **Auditoria Visual:** Cada trade pode ser verificado no MT5 ligando a entrada à saída, validando o racional descrito no `relatorio_detalhado_backtest.md`.

---
*Documento Estratégico v5.7 - Synkra AIOX Ecosystem*
