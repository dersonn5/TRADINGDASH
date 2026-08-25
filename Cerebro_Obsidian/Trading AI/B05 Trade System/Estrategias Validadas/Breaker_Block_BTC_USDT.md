---
tags: [estrategia, breaker-block, btc, camada-3, modelo, monitorando]
camada: 3
categoria: TRADE_SYSTEM
ativo: BTC/USDT
win_rate: 26.9%
profit_factor_ideal: 1.01
profit_factor_estressado: 0.99
total_trades_backtest: 257
periodo_backtest: 2022-2024
status: monitorando
ultima_revisao: 2026-06-27
---

# 🧱 Breaker Block — BTC/USDT

> **Camada 3 — Modelo em Monitoramento**
> Alta frequência (257 trades/3 anos) mas PF estressado abaixo de 1.00.
> **Requer refinamento adicional antes de operar com capital real.**

> [!WARNING]
> **Status: MONITORANDO** — PF estressado de 0.99 indica breakeven em condições reais.
> Operar somente em modo paper trading ou com tamanho mínimo até refinamento.

---

## O Que é o Breaker Block

Um **Breaker Block** é um Order Block que foi **mitigado e depois quebrou a estrutura** — tornando-se um nível de suporte/resistência institucional invertido.

**Formação**:
1. OB formado (última vela de baixa antes de subida, ou última de alta antes de queda)
2. Preço mitiga o OB (retorna e o testa)
3. Estrutura quebra na direção oposta → o OB vira Breaker

---

## Condições de Entrada

### Para LONG (Bullish Breaker)
1. Identificar OB de alta que foi quebrado para baixo (se tornou Breaker)
2. EMA 200 no M5 acima do Breaker (viés de alta maior)
3. Preço retorna para o Breaker em zona de desconto
4. MSS de M5 na direção de alta confirmado

### Para SHORT (Bearish Breaker)
1. OB de baixa quebrado para cima → Breaker bearish
2. EMA 200 abaixo do preço de entrada
3. Preço retorna ao Breaker em zona de prêmio
4. MSS bearish no M5

---

## Por Que Está em Monitoramento

| Problema Identificado | Impacto |
|---|---|
| Alta frequência (257 trades) gera overtrading | Viola limite de 3 trades/dia |
| PF cai para 0.99 com slippage | Não sustentável em condições reais |
| Sem filtro de tempo forte | Muitos falsos setups fora de killzone |

**Refinamentos em desenvolvimento:**
- [ ] Aplicar filtro de Killzone obrigatório (igual ao Silver Bullet)
- [ ] Exigir SMT divergência como confirmação
- [ ] Aumentar exigência de contexto HTF

---

## 🔗 Conexões Neurais
- [[MOC_Estrategias_Validadas|📈 MOC Estratégias]]
- [[Breaker_Block_ETH_USDT|🧱 Breaker Block ETH]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../01_Regras_ICT/ICT_OrderBlocks_YouTube_Distilled|📐 Order Blocks]]
- [[../01_Regras_ICT/ICT_MarketStructure_YouTube_Distilled|📊 Market Structure]]
- [[../04_Backtests/Relatorio_Otimizacao_Risco_Cripto_2022_2024|📋 Backtest Report]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]