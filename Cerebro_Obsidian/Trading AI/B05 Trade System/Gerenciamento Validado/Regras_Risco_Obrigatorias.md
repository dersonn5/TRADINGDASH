---
tags: [gerenciamento, risco, sizing, camada-4, validado]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# ⚖️ Regras de Risco Obrigatórias

> **Camada 4 — Não-Negociável**
> Estas regras foram validadas por backtest de 3 anos e são o escudo do capital.
> A IA não executa nenhum trade que viole qualquer uma destas regras.

---

## Regras Absolutas de Risco

### R1 — Risco por Operação: 1.0% Fixo
```
Risco por trade = 1.0% do capital total da conta
Exemplo: Conta $10.000 → Risco máximo = $100 por trade
```
- **Nunca aumentar** o risco para "recuperar" perdas
- **Nunca reduzir** o risco abaixo de 0.5% (ineficiência estatística)
- O sizing é calculado automaticamente com base no stop loss definido

### R2 — Drawdown Máximo Diário: 3%
```
Se perda acumulada no dia ≥ 3% → SISTEMA PARA
Próxima sessão: amanhã (reset às 00:00 ET)
```
- Três perdas de 1% em sequência = encerramento do dia
- O sistema não pode "buscar recuperação" no mesmo dia
- Ver: [[Drawdown_e_Limites_Diarios]]

### R3 — Meta Diária de Proteção: 5%
```
Se lucro acumulado no dia ≥ 5% → SISTEMA ENCERRA
Os ganhos são protegidos. Não há mais operações hoje.
```
- Após 5% de lucro, o risco de reverter o ganho é maior que o benefício de continuar
- Esta regra salva 70% dos dias lucrativos de serem revertidos em prejuízo

### R4 — Máximo de 3 Trades por Dia
```
Independente do resultado (wins ou losses), após 3 trades: SISTEMA PARA
```
- O 4º trade não existe. Não há exceção
- Esta regra existe pois o edge estatístico das estratégias não suporta mais de 3 trades/dia
- Backtests provam que trades acima de 3/dia destroem o Profit Factor

### R5 — Stop Loss é Sagrado
```
Após posicionar o stop, ele NUNCA é movido para AMPLIAR o risco
Mover para proteger (breakeven/trailing) = permitido com regras específicas
Mover para dar mais "espaço" = PROIBIDO ABSOLUTO
```
- Ver: [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss]]

---

## Tabela de Sizing por Capital

| Capital | Risco 1% | Stop 50 pts BTC | Stop 100 pts BTC | Stop 200 pts BTC |
|---|---|---|---|---|
| $1.000 | $10 | 0.0002 BTC | 0.0001 BTC | 0.00005 BTC |
| $5.000 | $50 | 0.001 BTC | 0.0005 BTC | 0.00025 BTC |
| $10.000 | $100 | 0.002 BTC | 0.001 BTC | 0.0005 BTC |
| $25.000 | $250 | 0.005 BTC | 0.0025 BTC | 0.00125 BTC |

> Ver cálculo detalhado: [[Sizing_e_Alavancagem]]

---

## Justificativa das Regras (Base Científica)

Todas as regras acima são derivadas de:
1. **Backtest de 3 anos** (2022–2024) com 500+ trades simulados
2. **Metodologia Lopez de Prado** — Purging e Embargo temporal para evitar overfitting
3. **Análise de drawdown** — curvas de equity estressadas com slippage + delay

> Ver: [[../02_Licoes_Aprendidas/Metodologia_Lopez_de_Prado]]

---

## 🔗 Conexões Neurais
- [[MOC_Gerenciamento|💰 MOC Gerenciamento]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[Sizing_e_Alavancagem|📐 Sizing e Alavancagem]]
- [[Drawdown_e_Limites_Diarios|🛡️ Drawdown e Limites]]
- [[Parciais_e_Breakeven|🎯 Parciais e Break-Even]]
- [[../MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar|🚫 Filtros]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Stop Loss]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]