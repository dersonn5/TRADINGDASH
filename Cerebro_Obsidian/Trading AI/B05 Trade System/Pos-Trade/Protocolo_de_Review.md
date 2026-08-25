---
tags: [pos-trade, review, protocolo, camada-5, sabedoria]
camada: 5
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🔍 Protocolo de Review — Pós-Trade

> **Camada 5 — Sabedoria Acumulada**
> O review não é opcional. É onde o sistema evolui.
> Um trade sem review é uma experiência desperdiçada.

---

## Quando Executar

- **Trade fechado (win ou loss)**: imediatamente após fechar
- **Fim de sessão**: revisão de todos os trades do dia
- **Fim de semana**: revisão semanal consolidada

---

## Protocolo de Review Individual (Por Trade)

### FASE 1 — Reconstituição (5 min)
```
1. Abrir o gráfico no momento exato da entrada
2. Identificar: qual era o Daily Bias naquele momento?
3. Identificar: qual era a killzone?
4. Identificar: qual FVG ou OB foi usado?
5. Tirar screenshot do setup
```

### FASE 2 — Avaliação do Processo (não do resultado)
```
Pergunta central: "O processo foi correto, independente do resultado?"

Checklist:
[ ] O Daily Bias estava claro antes da entrada?
[ ] A killzone estava ativa?
[ ] Todas as condições da estratégia estavam presentes?
[ ] O sizing foi calculado corretamente (1%)?
[ ] O stop foi posicionado corretamente?
[ ] Houve alguma intervenção não planejada?
```

> [!IMPORTANT]
> **Um trade perdedor com processo correto = trade bem executado.**
> **Um trade vencedor com processo errado = sorte, não skill.**
> O review avalia o PROCESSO, não o resultado.

### FASE 3 — Classificação do Trade

| Tipo | Descrição | Ação |
|---|---|---|
| **A+** | Setup perfeito, processo correto, resultado qualquer | Registrar como referência |
| **A** | Setup válido, processo correto | Registrar normalmente |
| **B** | Setup válido, pequeno desvio de processo | Registrar + nota de ajuste |
| **C** | Setup questionável mas dentro das regras | Registrar + análise crítica |
| **F** | Violação de regra — trade não deveria ter acontecido | Registrar + análise de causa |

### FASE 4 — Registro Sináptico

Registrar no diário seguindo o template:
```markdown
## Trade [número] — [data] [hora]
**Estratégia**: Silver Bullet / Breaker Block / Prop Firm
**Ativo**: BTC/USDT | ETH/USDT
**Direção**: LONG / SHORT
**Setup**: [descrever em 1 linha]
**Entrada**: $_____ | **Stop**: $_____ | **Alvo**: $_____
**Resultado**: +/- $_____ | +/- ___R
**Classificação**: A+ / A / B / C / F
**Lição**: [O que aprendi ou confirmei?]
**Nota atualizada**: [[link para a nota que deve ser revisada]]
```

Ver template completo: [[Gravacao_Sinapse_Obsidian]]

---

## Review Semanal (Todo Domingo)

```
1. Quantos trades A+ / A / B / C / F na semana?
2. Qual foi o PF real da semana?
3. Alguma regra foi violada? Por quê?
4. Qual padrão positivo se repetiu?
5. O que ajustar nas estratégias ou filtros?
```

Registrar no: [[../04_Backtests/Log_Desenvolvimento_Diario]]

---

## 🔗 Conexões Neurais
- [[MOC_PosTrade|📊 MOC Pós-Trade]]
- [[Gravacao_Sinapse_Obsidian|🧬 Gravação Sináptica]]
- [[Licoes_e_Ajustes|💡 Lições e Ajustes]]
- [[Cenarios_Finalizacao|🏁 Cenários de Finalização]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../03_Diario_Trades/Diario_2026_06|📅 Diário de Junho]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[../04_Backtests/Log_Desenvolvimento_Diario|📋 Log de Desenvolvimento]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]