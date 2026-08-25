---
tags: [parciais, breakeven, trailing, camada-4, gerenciamento]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🎯 Parciais e Break-Even

> **Quando e como realizar parte da posição — com regras baseadas em backtest.**
> Parciais mal aplicadas destroem o PF. As regras aqui são científicas, não emocionais.

---

## A Regra de Ouro do Break-Even

> [!CAUTION]
> **Break-Even no NY AM para BTC/ETH é PROIBIDO.**
> Backtest provou: mover o stop para BE em 1R durante NY AM derrubou o WR de 44.4% para 16.7%.
> O mercado cripto tem wicks agressivos que param os traders antes do movimento real.

| Sessão | Break-Even Permitido? | Gatilho |
|---|---|---|
| NY AM (10:00–11:00 ET) | ❌ **Proibido** | — |
| NY PM (14:00–15:00 ET) | ✅ Permitido | Após 1.5R |
| London Open | ✅ Permitido | Após 1R |

---

## Protocolo de Parciais

### Regra Padrão (Maioria dos Setups)
```
Em 1.5R → Realizar 50% da posição
Em 1.5R → Mover stop para breakeven (entrada exata)
Posição restante (50%) → Alvo em 2R+ ou próximo nível de liquidez
```

### Regra Conservadora (Ambiente de Dúvida)
```
Em 1R → Realizar 50% da posição
Em 1R → Mover stop para +0.3R (pequeno lucro garantido)
Posição restante → Alvo em 2R
```

### Regra Agressiva (Setup A+ com Contexto Forte)
```
Sem parcial — manter 100% até o alvo de 2R
Após 2R → Trailing stop com alvo em 3R+
Aplicar somente em setups classificados como A+
```

---

## Trailing Stop — Quando e Como

O trailing stop só é ativado **após o alvo 1 ser atingido**:
```
Após 2R atingido:
  → Stop sobe para 1R acima da entrada
  → A cada novo HH de M5, stop sobe para o CE da última vela de impulso
  → Objetivo: capturar extensões de 3R, 4R sem risco de perder o lucro base
```

---

## 🔗 Conexões Neurais
- [[MOC_Gerenciamento|💰 MOC Gerenciamento]]
- [[Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Stop Loss]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos|🏁 Alvos]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros — Break-Even precoce]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]