# Análise de Backtest Anual — Sniper v5.7.2
**Data da análise:** 19 de Abril de 2026  
**Período coberto:** ~1 ano  
**Base documental:** `brownfield-architecture.md`, `prd.md`, `README_SQUAD.md`, `strategy.md`, `relatorio_anual_sniper.md`

---

## 1. Resumo Executivo

O sistema Sniper v5.7.2 encerrou o período com um PNL total de **$9.852,15** distribuídos em **366 operações** em 10 pares simultâneos, com média de **$26,92 por trade** e uma média diária estimada de **~$39/dia** — representando **39% da meta declarada de $100/dia**.

A estratégia demonstra funcionamento sólido em pares com USD como denominador principal (win rates acima de 90%), mas apresenta degradação significativa em cruzamentos com EUR e pares JPY cruzados (win rates entre 72% e 77%). Foram identificados um bug crítico de gerenciamento de tempo, padrões de perda sistêmicos e oportunidades claras de otimização que podem elevar substancialmente o desempenho na próxima rodada.

---

## 2. Performance por Ativo

| Ativo   | PNL USD   | Win Rate | Trades | PNL/Trade | Cluster      |
|:--------|----------:|:--------:|-------:|----------:|:-------------|
| GBPUSD  | $1.940,49 | 92,1%    | 38     | $51,07    | Alta eficiência |
| AUDUSD  | $1.346,88 | 95,7%    | 46     | $29,28    | Alta eficiência |
| EURJPY  | $1.217,63 | 75,8%    | 62     | $19,64    | Alto volume, baixa margem |
| USDCHF  | $1.050,81 | 93,1%    | 29     | $36,24    | Alta eficiência |
| USDJPY  | $1.030,74 | 96,4%    | 28     | $36,81    | Alta eficiência |
| GBPJPY  | $963,23   | 76,5%    | 51     | $18,89    | Alta volatilidade |
| EURUSD  | $687,25   | 77,1%    | 35     | $19,64    | Baixa eficiência |
| EURGBP  | $713,58   | 72,5%    | 40     | $17,84    | Baixa eficiência |
| USDCAD  | $502,20   | 95,0%    | 20     | $25,11    | Subaproveitado |
| NZDUSD  | $399,34   | 94,1%    | 17     | $23,49    | Subaproveitado |

**Dois clusters claros emergem:**

**Cluster A — Alta eficiência** (GBPUSD, AUDUSD, USDCHF, USDJPY, USDCAD, NZDUSD): win rates entre 92% e 96%, PNL/trade elevado, perdas isoladas e controladas. Estes pares devem ser priorizados e com frequência de sinal aumentada.

**Cluster B — Alta fricção** (EURUSD, EURGBP, EURJPY, GBPJPY): win rates entre 72% e 77%, perdas mais frequentes e, no caso de EURJPY e GBPJPY, perdas catastróficas pontuais. A presença do EUR como componente e o comportamento mais volátil do JPY cruzado degradam a consistência da estratégia de reversão à média.

---

## 3. Achados Críticos

### 3.1 Bug: `exit_candles_max` não está sendo ativado

**Evidência no backtest:**

| Data       | Par    | Entrada | Saída | Duração   | PNL     |
|:-----------|:-------|:--------|:------|----------:|--------:|
| 30/05      | EURUSD | 23:40   | 00:00 | **2900m** | -$59,41 |
| 29/08      | EURJPY | 23:55   | 00:00 | **2885m** | -$9,38  |
| 03/10      | GBPJPY | 23:55   | 00:00 | **2885m** | -$9,35  |

Os três trades duraram aproximadamente **48 horas**, enquanto a regra `exit_candles_max = 8` deveria encerrar toda posição em no máximo **40 minutos**. Os três ocorrem próximos à virada da meia-noite (23:40–23:55), sugerindo que o comparador de tempo do `bot_liquidez.py` calcula a duração com subtração direta de timestamps sem tratar a virada de dia corretamente.

**Causa provável:** O código calcula `elapsed = current_time - entry_time` usando apenas horas:minutos locais, sem converter para segundos absolutos ou usar o `SESSION_START` timestamp (implementado na v5.6.1 para P&L, mas possivelmente não estendido ao controle de duração de trade).

**Impacto:** Exposição não controlada em posições abertas por ~48h, quebrando toda a lógica de gestão de risco.

---

### 3.2 Perda catastrófica isolada (EURJPY, 06/06)

O maior prejuízo único do backtest foi de **-$248,02** no EURJPY em 06/06 às 00:00, uma operação de apenas 5 minutos com RSI:35.6 — um sinal de qualidade mediana. O valor da perda é desproporcional a qualquer outro trade do portfólio (o segundo maior prejuízo foi -$167,54 no GBPJPY).

A combinação de horário (meia-noite, abertura de sessão asiática), par cruzado JPY (maior amplitude de pip-value) e RSI sem confirmação forte aponta para um evento de gap ou slippage extremo não contido pelo SL calculado. O sistema não possui nenhum mecanismo de **max-loss por trade** independente da posição do SL matemático.

---

### 3.3 Clustering de perdas em sessões de alta volatilidade

**18/02 — GBPJPY (4 trades consecutivos):**

| Hora  | PNL      |
|:------|--------:|
| 00:00 | -$81,37 |
| 02:45 | -$58,83 |
| 08:15 | -$0,26  |
| 08:25 | +$38,47 |

O sistema continuou operando após 3 perdas consecutivas na mesma sessão sem nenhum mecanismo de circuit breaker. O parâmetro `cooldown_candles = 12` aparentemente funciona por zona individual, não por sessão global do par.

**07/04 — GBPJPY (dia de alta volatilidade macro):**  
O mesmo dia gerou perdas também em EURUSD (-$70,82), EURJPY e AUDUSD. Sinais de evento macro (possivelmente notícia de alto impacto) afetando múltiplos pares simultaneamente, sem filtro de correlação ou suspensão automática por volatilidade elevada.

---

### 3.4 Viés direcional acentuado (BUY dominante)

Dos 366 trades no backtest, a vasta maioria são operações de compra. Os poucos SELLs aparecem concentrados em USDCHF (quase 100% SELL) e USDCAD (balanceado). Os pares com EUR são operados quase que exclusivamente como BUY.

Isso pode indicar que, no período testado, o mercado estava em tendência de alta nos pares EUR/USD e GBP/USD, mas o filtro `use_trend_filter` (SMA20 H1) estava filtrando os SELLs corretamente. O risco é que o robô fique sem operações válidas em períodos de tendência de baixa, prejudicando a consistência da meta diária.

---

### 3.5 Frequência de sinal insuficiente para a meta

A média de **1,45 trades/dia** em todo o portfólio, com **$26,92 por trade**, gera matematicamente ~$39/dia — menos da metade da meta de $100. Para atingir $100/dia mantendo a qualidade atual, seria necessário ou **~3,7 trades/dia** com o ticket médio atual, ou **aumentar o ticket médio para ~$69** mantendo a frequência.

Os pares subaproveitados (NZDUSD: 17 trades no ano, USDCAD: 20 trades) com win rates acima de 94% representam a oportunidade de maior retorno sem degradação de qualidade.

---

### 3.6 Trades de micro-lucro diluindo o portfólio

Há um número significativo de operações com ganho abaixo de $10 (várias entre $0,10 e $7,36). Esses trades consomem slots de cooldown, afetam contadores internos e, em operação real, seriam absorvidos parcialmente pelo spread mesmo com a correção de 1.5–2.5 pips já aplicada. Exemplos: GBPUSD $5.95, GBPJPY $5.73, USDJPY $5.07, EURJPY $1.81.

---

## 4. Sugestões de Melhoria para a Próxima Rodada

As melhorias estão ordenadas por prioridade — corrigir primeiro o que quebra a lógica de risco, depois o que expande a receita.

---

### Melhoria 1 — [CRÍTICO] Corrigir o cálculo de duração de trade na virada de meia-noite

**Problema:** `exit_candles_max` falha para trades abertos após ~23:30.

**Solução no `bot_liquidez.py`:**  
Substituir qualquer cálculo de duração baseado em `datetime.now().hour` ou subtração de `time` por subtração de `datetime` completo (com data), ou usar o `SESSION_START` timestamp Unix já existente na v5.6.1 como referência absoluta:

```python
# Errado — falha na virada de meia-noite
elapsed_candles = (datetime.now().minute - entry_time.minute) // candle_size

# Correto — usar timestamp absoluto
elapsed_seconds = (datetime.now() - entry_datetime).total_seconds()
elapsed_candles = int(elapsed_seconds / (candle_size * 60))
if elapsed_candles >= exit_candles_max:
    close_position()
```

---

### Melhoria 2 — [CRÍTICO] Implementar max-loss absoluto por trade

**Problema:** Sem teto de perda independente do SL matemático, eventos de gap ou slippage extremo geram perdas catastróficas ($248 em um único trade de 5 minutos).

**Solução:** Adicionar em `config.yaml` um parâmetro `max_loss_per_trade_usd` (sugestão: $80) que encerra qualquer posição imediatamente ao ser atingido, independente do SL calculado pelo Risk/Reward de 1.5x. Este valor deve ser verificado em loop pelo monitoramento de posições, não apenas no momento da abertura.

```yaml
risk:
  max_loss_per_trade_usd: 80
  rr_ratio: 1.5
  stop_buffer_points: 10
```

---

### Melhoria 3 — [ALTO] Implementar circuit breaker por par/sessão

**Problema:** O sistema continua operando após múltiplas perdas consecutivas na mesma sessão (ex: 3 perdas seguidas no GBPJPY em 18/02).

**Solução:** Adicionar um contador de perdas consecutivas por par. Após 2 perdas consecutivas em um único par, suspender aquele par por `session_pause_candles` (sugestão: 48 candles = ~4 horas no M15):

```yaml
risk:
  max_consecutive_losses_per_pair: 2
  session_pause_candles: 48
```

Este mecanismo é diferente do `cooldown_candles` existente (que opera por zona individual) — este age no par inteiro quando o mercado está claramente adverso.

---

### Melhoria 4 — [ALTO] Tighten RSI boundaries para os pares do Cluster B

**Problema:** Cruzamentos EUR e JPY cruzados mostram muitas perdas em RSI próximo ao limite de 40/60 (RSI:37–39 para BUY, RSI:60–64 para SELL). A lógica de reversão à média funciona melhor com RSI genuinamente extremo.

**Solução:** Criar configurações de RSI distintas por grupo de par em `config.yaml`:

```yaml
rsi_filters:
  majors_usd:       # GBPUSD, AUDUSD, USDCHF, USDJPY, USDCAD, NZDUSD
    oversold: 40
    overbought: 60
  eur_crosses:      # EURUSD, EURGBP, EURJPY
    oversold: 35
    overbought: 65
  jpy_crosses:      # GBPJPY
    oversold: 33
    overbought: 67
```

Isso filtra os setups de qualidade marginal nos pares de Cluster B sem afetar a frequência dos pares de alta performance.

---

### Melhoria 5 — [ALTO] Reduzir `lookback_zones` e `min_displacement_candles` para NZDUSD e USDCAD

**Problema:** NZDUSD gerou apenas 17 trades no ano (win rate: 94,1%) e USDCAD apenas 20 (win rate: 95,0%). Esses pares têm a melhor relação qualidade/frequência do portfólio e estão claramente subaproveitados.

**Solução:** Para esses dois pares especificamente, reduzir os parâmetros de zona para capturar mais sinais:

```yaml
zone_config:
  NZDUSD:
    min_displacement_candles: 5    # era 7
    lookback_zones: 120            # era 100
  USDCAD:
    min_displacement_candles: 5
    lookback_zones: 120
```

O objetivo é dobrar a frequência desses pares (de ~17 para ~34 e de ~20 para ~40) sem degradar o win rate abaixo de 90%.

---

### Melhoria 6 — [MÉDIO] Adicionar filtro de sessão para pares JPY cruzados

**Problema:** EURJPY e GBPJPY acumulam várias perdas em horário de transição asiático/europeu (00:00–02:00) e no início de sessão (abertura do mercado). O evento -$248 do EURJPY ocorreu exatamente à meia-noite.

**Solução:** Bloquear novas entradas para pares com JPY cruzado no horário de maior risco de gap:

```yaml
session_filter:
  EURJPY:
    blocked_hours_utc: ["23:45-00:30", "07:45-08:15"]  # transição asiático-europeu
  GBPJPY:
    blocked_hours_utc: ["23:45-00:30", "07:45-08:15"]
```

---

### Melhoria 7 — [MÉDIO] Implementar threshold mínimo de lucro esperado por trade

**Problema:** Trades com PNL abaixo de $12 (ex: $0.10, $1.81, $5.07, $5.73, $5.95) consomem cooldown de zona, crédito de trade diário e monitoramento de loop sem contribuir significativamente para a meta.

**Solução:** Calcular o PNL esperado antes de abrir a posição (com base no SL, TP calculado pelo RR 1.5x e `lot_size`) e recusar entradas onde o TP não supere um mínimo absoluto:

```yaml
risk:
  min_expected_profit_usd: 12
```

Esse filtro eliminaria as operações de micro-ganho sem alterar os critérios de RSI/zona/tendência.

---

### Melhoria 8 — [MÉDIO] Adicionar suspensão por correlação em evento macro

**Problema:** Em 07/04, múltiplos pares sofreram perdas simultâneas, indicando um evento macro que o sistema não detectou. Entrar em 6 trades no GBPJPY em um único dia de alta volatilidade macro nega o propósito de diversificação por multi-par.

**Solução:** Implementar um detector simples de correlação instantânea: se 3 ou mais pares gerarem sinal de perda dentro de uma janela de 30 minutos, suspender todos os pares por `macro_pause_candles` (sugestão: 24 candles = 2 horas):

```python
# Em bot_liquidez.py
if count_losses_last_30min(all_pairs) >= 3:
    suspend_all_pairs(candles=24)
    log_event("MACRO_PAUSE ativado — correlação de perdas detectada")
```

---

### Melhoria 9 — [BAIXO] Recalibrar `breakeven_candles` para pares de alta eficiência

**Problema:** O parâmetro `breakeven_candles = 4` move o SL para o preço de entrada após 4 velas em lucro, o que é adequado para pares mais lentos. Para GBPUSD e AUDUSD, que mostram movimentos rápidos e consistentes, o breakeven precoce pode estar encerrando trades que atingiriam o TP completo.

**Evidência:** GBPUSD registrou $341,39 e $183,15 em trades únicos de 35 e 40 minutos — o breakeven em 4 velas (20 minutos) pode ter cortado outros trades com potencial similar.

**Solução:** Testar `breakeven_candles = 6` para GBPUSD e AUDUSD na próxima rodada:

```yaml
trade_management:
  GBPUSD:
    breakeven_candles: 6
  AUDUSD:
    breakeven_candles: 6
  default:
    breakeven_candles: 4
```

---

### Melhoria 10 — [BAIXO] Registrar e auditar `require_color_reversal` por par

**Problema:** O parâmetro `require_color_reversal = true` exige uma vela de cor oposta como confirmação. Não há dados no backtest para avaliar quantos sinais foram rejeitados por este filtro e se ele está ajudando ou bloqueando oportunidades.

**Solução:** Adicionar ao CSV de exportação (FR1 do PRD) uma coluna `color_reversal_confirmed: true/false` para que a próxima rodada permita análise desse filtro isoladamente. Pode-se também testar com `require_color_reversal = false` em NZDUSD e USDCAD (os pares mais subaproveitados) para avaliar o impacto na frequência.

---

## 5. Priorização das Melhorias

| # | Melhoria | Prioridade | Impacto | Esforço |
|:--|:---------|:----------:|:-------:|:-------:|
| 1 | Correção do bug de duração (exit_candles_max) | CRÍTICO | Alto | Baixo |
| 2 | Max-loss absoluto por trade | CRÍTICO | Alto | Baixo |
| 3 | Circuit breaker por par/sessão | ALTO | Alto | Médio |
| 4 | RSI diferenciado por cluster de par | ALTO | Médio | Baixo |
| 5 | Reduzir limiar de zona (NZDUSD/USDCAD) | ALTO | Alto | Baixo |
| 6 | Filtro de sessão para JPY cruzados | MÉDIO | Médio | Baixo |
| 7 | Threshold mínimo de lucro esperado | MÉDIO | Médio | Baixo |
| 8 | Suspensão por correlação em evento macro | MÉDIO | Alto | Médio |
| 9 | Recalibrar breakeven_candles (GBPUSD/AUDUSD) | BAIXO | Médio | Baixo |
| 10 | Auditoria do filtro color_reversal | BAIXO | Baixo | Baixo |

---

## 6. Meta Projetada para a Próxima Rodada

Com as melhorias 1–5 implementadas e assumindo manutenção do win rate atual nos pares de Cluster A:

- Cluster A (pares de alta eficiência): estimativa de +60% de trades em NZDUSD e USDCAD = ~+40 trades adicionais no ano com PNL/trade de ~$24
- Filtragem de Cluster B com RSI mais restrito: estimativa de redução de 15% dos trades, mas eliminando os piores setups (perdas de $50–$248 evitadas)
- Bug fix do exit_candles_max: elimina exposição de 48h, sem impacto direto no PNL mas impacto crítico no risco real
- Max-loss por trade ($80): a perda catastrófica de $248 teria sido contida em $80, economizando $168 naquele único evento

**Estimativa conservadora:** $12.000–$14.000 de PNL para o mesmo período com as mesmas condições de mercado, elevando a média diária de $39 para ~$48–$56.

Para atingir a meta de $100/dia de forma consistente, será necessário também aumentar o `lot_size` ou aumentar a exposição por trade após validar a estabilidade das melhorias — o sistema possui a lógica, a diversificação e a robustez necessárias, mas opera atualmente abaixo da capacidade de posicionamento.

---

*Análise elaborada sobre os arquivos da v5.6/v5.7 do ecossistema Synkra AIOX — Sniper Edition.*
