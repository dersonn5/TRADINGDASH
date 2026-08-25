---
tags: [invalidacao, alertas, durante-trade, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🚨 Alertas de Invalidação

> **Sinais técnicos de que o setup original falhou.**
> Quando estes alertas se ativam, a saída manual é autorizada (excepcionalmente).

---

## Invalidação por Ação de Preço

### AI-1 — Corpo de Vela Fecha Além do CE
```
Para LONG: Corpo de vela M5 fecha ABAIXO do CE (50%) da FVG de entrada
Para SHORT: Corpo de vela M5 fecha ACIMA do CE da FVG

Ação: Saída manual imediata (limit order abaixo do CE)
      Não esperar o stop — o suporte institucional falhou
```

### AI-2 — Eliminação do OB / Breaker
```
O Order Block ou Breaker Block usado na entrada foi completamente
preenchido por corpo de vela (não pavio) — sem reteste

Ação: Saída manual imediata
```

### AI-3 — Estrutura de HTF Quebrada na Direção Oposta
```
O H1 ou H4 quebra estrutura contra o trade em andamento
com displacement (vela de impulso forte de corpo cheio)

Ação: Reduzir posição em 50%, manter o restante até o stop
```

---

## Invalidação por Contexto

### AI-4 — Daily Bias Invertido
```
H4 confirma nova direção oposta ao trade em andamento
(novo swing high/low de H4 na direção contrária)

Ação: Saída manual na próxima vela de M5
```

### AI-5 — DOL Atingido na Direção Oposta
```
O preço atingiu o DOL do lado oposto ao trade (absorveu toda a liquidez disponível)

Ação: Saída manual imediata — o movimento está esgotado
```

---

## O Que NÃO É Invalidação

❌ Preço chegando perto do stop sem atingi-lo → **aguardar**
❌ Pavio tocando o CE sem fechar corpo abaixo → **aguardar**
❌ Consolidação lateral após entrada → **aguardar**
❌ Notícia menor (não-crítica) surgindo → **aguardar**

---

## 🔗 Conexões Neurais
- [[MOC_DuranteTrade|👁️ MOC Durante]]
- [[Quando_Fechar_Antecipado|⛔ Fechar Antecipado]]
- [[Cenarios_Possiveis|🔀 Cenários]]
- [[Regras_Nao_Intervir|🚦 Não Intervir]]
- [[../01_Regras_ICT/Consequent_Encroachment_FVG|📐 Consequent Encroachment]]
- [[../01_Regras_ICT/ICT_MarketStructure_YouTube_Distilled|📊 Estrutura de Mercado]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]