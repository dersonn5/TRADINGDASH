# Auditoria Estatística do Backtester

Data: 2026-05-18
Escopo: `core/backtester.py`, `run_backtest.py`, `core/agent.py`, `core/risk_manager.py`, `core/rag.py`, `backtest_scenarios/*`

---

## Sumário Executivo

**Veredito:** Backtest **NÃO valida edge do sistema**. Mede capacidade da IA de ler comentários em português, não capacidade de prever movimento de preço.

**Severidade dos achados:**
- 🔴 Críticos: 4 (invalidam qualquer conclusão de lucratividade)
- 🟡 Médios: 6 (distorcem métricas)
- 🔵 Info: 3 (qualidade de código)

**Recomendação:** Antes de rodar backtest novamente, corrigir os 4 críticos. Caso contrário resultados são teatro estatístico.

---

## 🔴 Críticos

### C1 — Look-ahead bias massivo nos cenários
**Arquivo:** `backtest_scenarios/scenarios_xauusd.json` e `scenarios_nq.json`, gerados por `generate_large_scenarios.py`.

**Problema:** Campo `commentary` contém literalmente a resposta do teste. Exemplos:
- SCENARIO-003: *"ATENÇAO CRITICA: O corpo de vela fechou ABAIXO do Consequent Encroachment, violando o suporte"* → IA tem que ser idiota pra aprovar
- SCENARIO-004: *"O preco de H4 esta preso em um range lateral ha 3 dias"* → "rejeite isso" gritado no ouvido
- SCENARIO-005 (vencedor): *"Preco mitigou perfeitamente o CE da FVG após varrer o SSL... com forte rejeicao... formacao de MSS com deslocamento agressivo"* → "compre isso" telegrafado

**Impacto:** Win rate alto = IA leu português, não que tem edge. Em mercado real, o `commentary` virá de você ou de Pine Script no momento do alerta, sem saber o futuro.

**Fix:** Reescrever `commentary` em tempo presente neutro, sem adjetivos de qualidade (`perfeitamente`, `crítica`, `apertado`, `decisiva`). Apenas dados observáveis no momento. Idealmente: dataset real de candles + indicadores brutos, sem narrativa.

---

### C2 — PnL deterministicamente acoplado ao `historical_outcome.result`
**Arquivo:** `core/backtester.py:96-115` (ideal) e `:243-257` (estressado).

**Problema:** Backtest não simula price action. Lógica é:
```python
if ai_action approved AND outcome["result"] == "WIN":
    pnl = +risk × R:R
else:
    pnl = -risk
```
Sem simulação de candles, sem SL/TP sendo atingido em ordem cronológica, sem partial fills, sem trailing. PnL é binário e fixo.

**Impacto:** Qualquer R:R que a IA propor não importa pra direção do trade — só se a IA concorda com o gabarito. Profit Factor inflado artificialmente quando IA acerta.

**Fix:** Cenários precisam de timeseries de candles pós-entrada. PnL deve vir de `OnBarUpdate` simulando o tempo até SL ou TP ser tocado.

---

### C3 — Stressed loop NÃO re-avalia com info degradada
**Arquivo:** `core/backtester.py:177-180`

```python
ideal_res = self.results_ideal[idx]
ai_action = ideal_res["ai_decision"]
ai_reasoning = ideal_res["reasoning"]
```

**Problema:** Loop estressado reutiliza decisão do loop ideal. Slippage só afeta PnL, não a decisão. "Estresse" portanto não testa robustez cognitiva — só re-precifica o mesmo trade.

**Impacto:** Métrica "ambiente estressado" é matematicamente dependente do ideal. Não há experimento independente. Comparativo ideal vs estressado é tautológico.

**Fix:** Loop estressado deve re-chamar `evaluate_trade_setup()` com snapshot perturbado (preço deslocado, candle ruidoso, latência simulada antes da decisão).

---

### C4 — `RiskManager` valida contra DB de produção durante backtest
**Arquivo:** `core/agent.py:59-94` + `core/risk_manager.py:51-118`

**Problema:** `evaluate_trade_setup(is_backtest=True)` chama `RiskManager.validate_pre_trade_filters()` que lê `trades_database.json` filtrando por `datetime.now()`. Se você rodou 3 trades reais HOJE, **todos** os 100 cenários do backtest vão ser rejeitados pelo overtrading filter (`MAX_TRADES_PER_DAY=3`).

Pior: backtest também pode ser bloqueado pelo daily drawdown se sua conta real tomou perdas hoje.

**Impacto:** Resultado do backtest depende do estado real da sua conta naquele dia. Não-reprodutível. Cenários sendo silenciosamente vetados.

**Fix:** Adicionar `bypass_daily_limits=True` quando `is_backtest=True`. Ou usar DB separado para backtest.

---

## 🟡 Médios

### M1 — Sample size insuficiente
50 cenários por ativo, 10 WINs cada. Sharpe/PF calculados em n=10 vencedores = ruído. Mínimo aceitável: 200 trades.

### M2 — Sem comissão, spread, swap, financiamento overnight
`risk_per_trade_usd = 100`, `pnl = ±risk × RR`. Custos de execução zerados. Em CFD XAUUSD um spread típico já come 5-10% do alvo curto.

### M3 — R:R hardcoded no stressed, desconectado da IA
Linhas 232-237: `original_sl_dist = 1.5`, `original_tp_dist = 4.0` para XAU. Não usa `ai_decision["stop_loss"]` / `take_profit`. IA pode propor 1:10, sistema simula 1:2.67 mesmo assim.

### M4 — Embargo de 2h nunca dispara
Cenários espaçados ~3.5 dias entre si (`current_date + timedelta(days=i*3.5)`). Embargo só faria sentido em dataset intradiário denso. Filtro inerte no dataset atual.

### M5 — Sem Sharpe, Sortino, Max DD, Expectancy, equity curve
Backtester só reporta win_rate + profit_factor + PnL total. Falta:
- Sharpe (PnL/std)
- Max Drawdown absoluto + duração
- Expectancy = (WR × avg_win) - ((1-WR) × avg_loss)
- Equity curve / running balance
- Consecutive losses streak

### M6 — Cenários sintéticos com distribuição fixa
`scenario_type = i % 5` → exatamente 20% wins, 80% losses. Distribuição artificial não reflete mercado real. Edge testado é "aprovar 20%, rejeitar 80%" — IA pode ser premiada por viés simples.

---

## 🔵 Info

### I1 — `time.sleep(2.0)` entre scenarios
Linha 87 backtester. 100 trades × 2s = 3.3min só dormindo. Aceitável só pra anti-rate-limit; remover quando usar tier pago.

### I2 — `profit_factor` fallback retorna 1.0 sem trades
Linhas 137, 278. Se `gross_profits == 0 == gross_losses` retorna 1.0 (parece neutro mas é "sem dados"). Deveria retornar `None` ou `NaN`.

### I3 — Loop estressado preserva `slippage_val` da iteração anterior em `PASS`
Linha 271: `slippage_applied: slippage_val` referencia variável da iteração anterior se branch `PASS` foi tomado sem `slippage_val=0.0` definido nessa volta. Já corrigido na linha 221, mas escopo de variável em loop Python é frágil.

---

## Correções recomendadas — ordem de prioridade

1. **C4** (15 min) — adicionar flag `bypass_daily_limits` no RiskManager. **Faz backtest atual ser sequer executável de forma reprodutível.**
2. **C1** (algumas horas) — neutralizar `commentary` nos JSONs ou regerar
3. **M5** (1-2h) — adicionar Sharpe / Max DD / Expectancy ao stats
4. **C3** (médio) — re-chamar Gemini no stressed loop com input perturbado
5. **C2** (grande) — refatorar pra usar timeseries reais de candles

---

## Notas adicionais sobre confiabilidade

- **Dataset não é histórico real** — é gerado proceduralmente. Ainda que tudo acima fosse corrigido, edge medido seria sobre regras sintéticas do gerador, não sobre mercado real.
- **Para validar edge real**: baixar dados M1/M5 reais de XAUUSD/NQ (ex: Dukascopy, TwelveData free, ou TradingView export), gerar cenários a partir de price action observada com bias/sweep/FVG detectados por código (não anotados manualmente).
