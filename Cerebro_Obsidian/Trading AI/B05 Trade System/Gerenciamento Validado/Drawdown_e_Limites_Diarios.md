---
tags: [drawdown, limites, circuit-breaker, camada-4, gerenciamento]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🛡️ Drawdown e Limites Diários

> **Os circuit breakers que salvam a conta nos dias ruins.**
> O objetivo não é ganhar todo dia — é sobreviver para ganhar no longo prazo.

---

## Circuit Breakers (Automáticos)

### CB-1 — Drawdown Diário: 3%
```
Trigger:  Perda acumulada no dia ≥ 3% do capital
Ação:     Sistema para completamente
Reset:    00:00 ET do dia seguinte
```
**Por que 3%?** Com risco de 1% por trade, significa 3 perdas consecutivas.
Estatisticamente, continuar após 3 perdas aumenta o DD total sem recuperar o edge.

### CB-2 — Meta Diária de Proteção: 5%
```
Trigger:  Lucro acumulado no dia ≥ 5% do capital
Ação:     Sistema encerra. Proteger o lucro.
Reset:    00:00 ET do dia seguinte
```
**Por que 5%?** Após 5% de lucro em um dia, o risco/retorno de continuar inverte.
A probabilidade de devolver o lucro supera a de aumentá-lo.

### CB-3 — Máximo de Trades: 3/dia
```
Trigger:  3 trades fechados (win ou loss)
Ação:     Sistema para
Reset:    00:00 ET do dia seguinte
```

---

## Limites Semanais e Mensais

| Período | Limite de Drawdown | Ação |
|---|---|---|
| Diário | -3% | Para até amanhã |
| Semanal | -8% | Reduzir tamanho de posição pela metade |
| Mensal | -15% | Parar operação e revisar estratégias |

---

## Curva de Equity Esperada

Com as regras acima e PF 1.84 (Silver Bullet BTC):
```
Expectativa por trade: +0.84R em média
Com 1% por trade: +0.84% por trade em média
Com ~6 trades/mês: +~5% de expectativa mensal
```
> Drawdowns fazem parte da curva. Um mês negativo não invalida a estratégia.

---

## Tabela de Controle Diário

```markdown
| Data | Capital Início | P&L | % Dia | Trades | Status |
|---|---|---|---|---|---|
| ____-__-__ | $_____ | +/- $_____ | ___% | _/3 | ativo/parado |
```

---

## 🔗 Conexões Neurais
- [[MOC_Gerenciamento|💰 MOC Gerenciamento]]
- [[Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[Sizing_e_Alavancagem|📐 Sizing]]
- [[../MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar|🚫 Filtros]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../POS_TRADE/Protocolo_de_Review|🔍 Review]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]