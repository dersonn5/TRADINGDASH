---
tags: [moc, estrategias, camada-3, modelo]
camada: 3
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 📈 MOC — Estratégias Validadas

> Todas as estratégias aqui listadas foram **validadas por backtest** (2022–2024, 3 anos de dados).
> A IA consulta este MOC para identificar qual protocolo aplicar ao sinal detectado.

---

## Critérios de Validação

Para uma estratégia entrar aqui, ela precisa ter:
- ✅ Backtest mínimo de **12 meses** de dados reais
- ✅ **Profit Factor ≥ 1.05** em condições estressadas (com slippage + delay)
- ✅ **Mínimo de 15 trades** (amostra estatisticamente relevante)
- ✅ **Drawdown máximo < 15%** do capital no período

---

## Estratégias Ativas

| Estratégia | Asset | WR | PF Estressado | Trades | Status |
|---|---|---|---|---|---|
| [[Silver_Bullet_BTC_USDT\|Silver Bullet]] | BTC/USDT | 41.2% | **1.84** | 17 | ✅ Ativa |
| [[Silver_Bullet_ETH_USDT\|Silver Bullet]] | ETH/USDT | 30.4% | **1.08** | 23 | ✅ Ativa |
| [[Breaker_Block_BTC_USDT\|Breaker Block]] | BTC/USDT | 26.9% | **0.99** | 257 | ⚠️ Monitorando |
| [[Breaker_Block_ETH_USDT\|Breaker Block]] | ETH/USDT | 26.2% | **0.93** | 301 | ⚠️ Monitorando |
| [[Prop_Firm_2024_BTC\|Prop Firm 2024]] | BTC/USDT | 30.7% | **1.03** | 231 | ✅ Ativa |

---

## Como a IA Seleciona a Estratégia

```
Sinal detectado
      │
      ├─ É NY AM (10:00–11:00 ET) ou NY PM (14:00–15:00 ET)?
      │    └─ SIM → [[Silver_Bullet_BTC_USDT]] ou [[Silver_Bullet_ETH_USDT]]
      │
      ├─ Tem Breaker Block identificado em zona de desconto/prêmio?
      │    └─ SIM → [[Breaker_Block_BTC_USDT]] ou [[Breaker_Block_ETH_USDT]]
      │
      └─ É setup Unicorn / IFVG em contexto de Prop Firm?
           └─ SIM → [[Prop_Firm_2024_BTC]]
```

---

## 🔗 Conexões Neurais
- [[MOC_TradeSystem|🧠 Hub TRADE SYSTEM]]
- [[Cerebro_ICT|🧠 Hub Central]]
- [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|⏰ Killzones]]
- [[../01_Regras_ICT/ICT_ModelosTrade_YouTube_Distilled|📐 Modelos de Trade]]
- [[../04_Backtests/Relatorio_Otimizacao_Risco_Cripto_2022_2024|📊 Relatório Backtest]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]