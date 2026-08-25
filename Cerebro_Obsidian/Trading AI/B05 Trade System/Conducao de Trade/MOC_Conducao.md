---
tags: [moc, conducao, execucao, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🎮 MOC — Condução de Trade

> **Da entrada ao fechamento — gestão técnica de cada fase da operação.**

---

## Notas Desta Camada

| Nota | Propósito |
|---|---|
| [[Execucao_de_Entrada\|🟢 Execução de Entrada]] | Como posicionar a ordem com precisão |
| [[Gestao_de_Stop_Loss\|🔴 Gestão do Stop Loss]] | O stop é sagrado — quando e como mover |
| [[Gestao_de_Alvos\|🏁 Gestão de Alvos]] | 2R, extensões e trailing |
| [[Cenarios_Durante_Trade\|🔀 Cenários Durante o Trade]] | O que pode acontecer na condução |

---

## Sequência de Condução

```
ENTRADA → Ordem limit no CE da FVG (ver Execucao_de_Entrada)
    ↓
POSIÇÃO ABERTA → Stop e Alvo definidos (imutáveis até condição especial)
    ↓
EM 1.5R → Parcial de 50% + BE (ver Parciais_e_Breakeven)
    ↓
EM 2R → Fechar posição restante OU ativar trailing
    ↓
FECHAMENTO → Protocolo de Review
```

---

## 🔗 Conexões Neurais
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais]]
- [[DURANTE_O_TRADE/Regras_Nao_Intervir|🚦 Não Intervir]]
- [[Cerebro_ICT|🧠 Hub Central]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]