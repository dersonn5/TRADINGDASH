---
tags: [moc, durante-trade, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 👁️ MOC — Durante o Trade

> **O que fazer (e o que NÃO fazer) enquanto o trade está aberto.**

---

## Notas Desta Camada

| Nota | Propósito |
|---|---|
| [[Regras_Nao_Intervir\|🚦 Regras de Não Intervir]] | Por que e como não interferir |
| [[Cenarios_Possiveis\|🔀 Cenários Possíveis]] | 12 cenários mapeados com resposta |
| [[Quando_Fechar_Antecipado\|⛔ Fechar Antecipado]] | Condições estritas para saída manual |
| [[Alertas_de_Invalidacao\|🚨 Alertas de Invalidação]] | Sinais técnicos de que o setup falhou |

---

## Princípio da Fase Durante

```
Trade aberto → Plano já foi feito
                    ↓
              Confiar no plano
                    ↓
         Monitorar APENAS: Stop | Alvo | Alertas
                    ↓
         NÃO monitorar: P&L flutuante | Notícias | Outros setups
```

---

## 🔗 Conexões Neurais
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Stop Loss]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos|🏁 Alvos]]
- [[../MENTALIDADE_PRE_TRADE/Estado_Mental_Ideal|🧘 Estado Mental]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]