---
tags: [stop-loss, gestao, sagrado, camada-4, conducao]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🔴 Gestão do Stop Loss

> **O stop loss é o limite máximo de dano. É sagrado.**
> Uma vez posicionado, só pode ser movido para PROTEGER — nunca para AMPLIAR.

---

## Posicionamento Inicial

```
Para FVG Bullish:
  Stop = 1 tick abaixo da BASE do FVG
  (O FVG é invalidado se o preço fechar abaixo da base)

Para FVG Bearish:
  Stop = 1 tick acima do TOPO do FVG

Para Breaker Block:
  Stop = 1 tick além do extremo do Breaker
```

---

## Regra Absoluta — Stop Não Pode Ser Ampliado

> [!CAUTION]
> **NUNCA mover o stop para dar mais "espaço" ao trade.**
> O stop foi calculado com base na invalidação técnica do setup.
> Se o preço está chegando ao stop, o setup está falhando — o stop está correto.

---

## Quando o Stop Pode Ser Movido (Para Proteger)

| Condição | Movimento Permitido | Onde Mover |
|---|---|---|
| Posição atingiu 1.5R | Mover para BE (NY PM) | Preço de entrada exato |
| Posição atingiu 2R | Mover para +1R | 1R acima da entrada |
| Trailing ativado | Seguir HH do M5 | CE de cada vela de impulso |

> **Regra de sessão**: No NY AM para BTC/ETH, o BE só é permitido após 2R.
> Ver: [[../GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven]]

---

## Psicologia do Stop

O momento em que o stop se aproxima é o momento de maior pressão emocional.
O impulso natural é mover o stop "um pouco mais".
**Este impulso deve ser ignorado completamente.**

A razão: o stop foi calculado em estado frio, com dados históricos.
A decisão de mover em tempo real é feita em estado emocional — e portanto, errada.

---

## 🔗 Conexões Neurais
- [[MOC_Conducao|🎮 MOC Condução]]
- [[Execucao_de_Entrada|🟢 Entrada]]
- [[Gestao_de_Alvos|🏁 Alvos]]
- [[../GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[../GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais]]
- [[../DURANTE_O_TRADE/Regras_Nao_Intervir|🚦 Não Intervir]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]