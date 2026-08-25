---
tags: [estrategia, breaker-block, eth, camada-3, modelo, monitorando]
camada: 3
categoria: TRADE_SYSTEM
ativo: ETH/USDT
win_rate: 26.2%
profit_factor_ideal: 0.98
profit_factor_estressado: 0.93
total_trades_backtest: 301
periodo_backtest: 2022-2024
status: monitorando
ultima_revisao: 2026-06-27
---

# 🧱 Breaker Block — ETH/USDT

> **Camada 3 — Modelo em Monitoramento**
> Alta frequência (301 trades em 3 anos) mas performance estressada abaixo de breakeven (PF 0.93).
> **Filtros adicionais são estritamente necessários antes de qualquer execução.**

> [!WARNING]
> **Status: MONITORANDO** — Não operar com capital real.
> O setup sofre com wicks de liquidação do ETH que violam os limites técnicos frequentemente.

---

## Particularidades no ETH/USDT

Diferente do BTC, o Breaker Block em ETH sofre com "Fakeouts" (falsos rompimentos) devido à menor liquidez relativa nas exchanges no intraday:
1. **Double Sweeps (Varreduras Duplas)**: O preço rompe o Breaker, stopa o trade, e logo depois inicia a expansão real.
2. **Spread e Slippage**: O spread flutuante no ETH Futures aumenta nas reversões, deteriorando a execução da Limit Order.

---

## Plano de Reabilitação da Estratégia

Para reabilitar a estratégia para o status `validado`, novos backtests estão avaliando:
- Exigir que a quebra de estrutura (MSS) ocorra com **Volume ≥ 1.5x a média** das últimas 20 velas de 5m.
- Execução somente na zona de **Discount profundo (≥ 70.5% Fibonacci)** para longs, e **Premium profundo (≤ 29.5%)** para shorts.
- Uso obrigatório de **SMT Divergência** com o BTC no momento do toque do Breaker.

---

## 🔗 Conexões Neurais
- [[MOC_Estrategias_Validadas|📈 MOC Estratégias]]
- [[Breaker_Block_BTC_USDT|🧱 Breaker Block BTC]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../01_Regras_ICT/ICT_OrderBlocks_YouTube_Distilled|📐 Order Blocks]]
- [[../01_Regras_ICT/ICT_MarketStructure_YouTube_Distilled|📊 Market Structure]]
- [[../04_Backtests/Relatorio_Otimizacao_Risco_Cripto_2022_2024|📋 Backtest Report]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]