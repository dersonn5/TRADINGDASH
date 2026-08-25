---
tags: [mapeamento, liquidez, dol, pre-trade, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🗺️ Mapeamento de Liquidez

> **Antes de qualquer sessão, o mercado precisa ser mapeado.**
> Identificar onde está a liquidez = identificar para onde o preço vai.

---

## Protocolo de Mapeamento (Por Sessão)

### 1. Identificar o DOL (Draw on Liquidity)
```
Hierarquia (do mais importante ao menos):
Monthly High/Low → Weekly High/Low → PDH/PDL → Asian High/Low → Intraday Highs/Lows
```
- O DOL é o "ímã" do dia — para onde o algoritmo está sendo "puxado"
- Identificar 1 DOL principal e 1–2 DOLs secundários

### 2. Marcar os Níveis de BSL e SSL
```
BSL (Buy Side Liquidity) — onde estão os stops dos vendedores:
  → Equal Highs (EQH)
  → Asian Range High
  → PDH (Previous Day High)

SSL (Sell Side Liquidity) — onde estão os stops dos compradores:
  → Equal Lows (EQL)
  → Asian Range Low
  → PDL (Previous Day Low)
```

### 3. Identificar FVGs de HTF Abertos
```
H4: FVGs não preenchidos → zonas de forte atração institucional
H1: FVGs não preenchidos → alvos intraday de alta probabilidade
```

### 4. Marcar o Midnight Open (00:00 ET)
```
Este nível divide o dia em:
  → Acima: zona de prêmio (buscar shorts)
  → Abaixo: zona de desconto (buscar longs)
```

### 5. Marcar Asian Range
```
High e Low da sessão asiática (18:00–00:00 ET)
Serve como referência para o Judas Swing do London/NY
```

---

## Checklist de Mapeamento

- [ ] DOL principal identificado e marcado
- [ ] BSL e SSL relevantes marcados
- [ ] FVGs de H4 e H1 marcados
- [ ] Midnight Open marcado
- [ ] Asian Range High e Low marcados
- [ ] Daily Bias definido (bullish/bearish/neutro)
- [ ] POI (Point of Interest) de entrada mapeado

---

## 🔗 Conexões Neurais
- [[MOC_PreTrade|📋 MOC Pré-Trade]]
- [[Checklist_Pre_Sessao|✅ Checklist]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../01_Regras_ICT/ICT_Liquidity_YouTube_Distilled|💧 Liquidez]]
- [[../01_Regras_ICT/Daily_Bias_e_Order_Flow|📊 Daily Bias]]
- [[../01_Regras_ICT/Power_of_3_e_AMD|📐 PO3 & AMD]]
- [[../01_Regras_ICT/Draw_on_Liquidity|🎯 Draw on Liquidity]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 FVG]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]