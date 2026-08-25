---
tags: [gerenciamento, moc, risco, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 💰 MOC — Gerenciamento Validado

> **A matemática que protege o capital e garante a sobrevivência no longo prazo.**
> Sem gerenciamento correto, a melhor estratégia do mundo quebra a conta.

---

## Notas Desta Camada

| Nota | Propósito | Criticidade |
|---|---|---|
| [[Regras_Risco_Obrigatorias\|⚖️ Regras de Risco]] | 5 regras absolutas não-negociáveis | 🔴 CRÍTICO |
| [[Sizing_e_Alavancagem\|📐 Sizing e Alavancagem]] | Cálculo exato de tamanho de posição | 🔴 CRÍTICO |
| [[Drawdown_e_Limites_Diarios\|🛡️ Drawdown e Limites]] | Circuit breakers e proteção de capital | 🔴 CRÍTICO |
| [[Parciais_e_Breakeven\|🎯 Parciais e Break-Even]] | Quando e como realizar parcialmente | 🟡 IMPORTANTE |

---

## Hierarquia de Proteção

```
Capital Total
      │
      ▼
Risco Máximo por Trade: 1% ──────────── [[Regras_Risco_Obrigatorias]]
      │
      ▼
Drawdown Máximo Diário: 3% ──────────── [[Drawdown_e_Limites_Diarios]]
      │
      ▼
Máximo de 3 Trades/Dia ──────────────── [[Regras_Risco_Obrigatorias]]
      │
      ▼
Meta de Proteção Diária: 5% ─────────── [[Drawdown_e_Limites_Diarios]]
      │
      ▼
Sizing Calculado por Stop ───────────── [[Sizing_e_Alavancagem]]
      │
      ▼
Parciais e Trailing ─────────────────── [[Parciais_e_Breakeven]]
```

---

## 🔗 Conexões Neurais
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[Cerebro_ICT|🧠 Hub Central]]
- [[../MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar|🚫 Filtros]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[../04_Backtests/Relatorio_Otimizacao_Risco_Cripto_2022_2024|📊 Backtest]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]