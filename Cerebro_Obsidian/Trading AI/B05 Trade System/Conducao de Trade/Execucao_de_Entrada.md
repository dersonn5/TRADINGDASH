---
tags: [entrada, execucao, ordem, camada-4, conducao]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🟢 Execução de Entrada

> **Como posicionar a ordem com precisão cirúrgica.**
> A entrada define o R:R de todo o trade. Uma entrada ruim não pode ser corrigida.

---

## Tipo de Ordem: SEMPRE Limit Order

```
❌ NUNCA: Ordem a mercado na entrada de swing
✅ SEMPRE: Limit Order no CE (50%) da FVG
```

**Por quê limit?**
- Garante o preço planejado — sem slippage de entrada
- O CE da FVG é o ponto de máxima eficiência de risco/retorno
- Entrada a mercado após movimento = risco maior, reward menor

---

## Localização Exata da Entrada

```
FVG Bullish:
  ┌─────┐ ← Topo do FVG (vela 3)
  │     │
  │ CE  │ ← 50% do FVG = ponto de entrada (Consequent Encroachment)
  │     │
  └─────┘ ← Base do FVG (vela 1)

Entrada: Limit Buy no CE
Stop: 1 tick abaixo da base do FVG
Alvo: 2× distância do stop acima da entrada
```

---

## Protocolo de Entrada Passo a Passo

```
1. Aguardar a killzone ativa
2. Identificar varredura de liquidez
3. Aguardar MSS no M5 na direção do trade
4. Localizar FVG formado pelo MSS
5. Calcular CE: (topo + base) / 2
6. Posicionar Limit Order no CE
7. Posicionar Stop Loss: 1 tick além da base/topo do FVG
8. Calcular Alvo: CE + (CE - Stop) × 2
9. Calcular Sizing: ver [[../GERENCIAMENTO_VALIDADO/Sizing_e_Alavancagem]]
10. Confirmar R:R ≥ 2:1 antes de enviar a ordem
```

---

## Validade da Ordem

- A ordem limit é válida **apenas durante a killzone ativa**
- Se a killzone encerrar sem que a ordem seja preenchida → **cancelar**
- Não manter ordens abertas fora da janela de tempo

---

## 🔗 Conexões Neurais
- [[MOC_Conducao|🎮 MOC Condução]]
- [[Gestao_de_Stop_Loss|🔴 Stop Loss]]
- [[Gestao_de_Alvos|🏁 Alvos]]
- [[../GERENCIAMENTO_VALIDADO/Sizing_e_Alavancagem|📐 Sizing]]
- [[../01_Regras_ICT/Consequent_Encroachment_FVG|📐 Consequent Encroachment]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 FVG]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]