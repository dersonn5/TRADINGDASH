---
tags: [alvos, gestao, take-profit, camada-4, conducao]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🏁 Gestão de Alvos

> Os alvos são definidos antes da entrada e honrados após ela.
> Mover o alvo para baixo por medo ou para cima por ganância = destruir o PF.

---

## Alvos Padrão

```
Alvo 1 (obrigatório): 2R acima da entrada
  = entrada + (entrada - stop) × 2

Alvo 2 (opcional, após parcial):
  = próximo nível de liquidez em HTF
  = FVG de H1 não preenchido
  = PDH / PDL (máxima/mínima do dia anterior)
  = Equal Highs / Equal Lows varridos
```

---

## Hierarquia de Alvos por Contexto

| Contexto | Alvo 1 | Alvo 2 |
|---|---|---|
| Setup normal (A/B) | 2R | Fechar tudo em 2R |
| Setup forte (A+) | 2R (50%) | 3R–5R (50% restante) |
| Contexto de alta volatilidade | 1.5R | Fechar tudo |
| Approaching major level | Fechar antes do nível | — |

---

## Quando Ajustar o Alvo (Antes da Entrada)

Ajustar o alvo **antes** de enviar a ordem é permitido se:
- Um nível de liquidez forte está entre a entrada e o alvo de 2R
  → Ajustar o alvo para **logo antes** do nível (não depois)
- O alvo de 2R coincide exatamente com um nível de resistência estrutural forte
  → Manter — confirmação institucional do alvo

---

## 🔗 Conexões Neurais
- [[MOC_Conducao|🎮 MOC Condução]]
- [[Execucao_de_Entrada|🟢 Entrada]]
- [[Gestao_de_Stop_Loss|🔴 Stop]]
- [[../GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais]]
- [[../DURANTE_O_TRADE/Cenarios_Possiveis|🔀 Cenários]]
- [[../01_Regras_ICT/ICT_Liquidity_YouTube_Distilled|💧 Liquidez]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]