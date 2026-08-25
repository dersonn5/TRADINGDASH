---
tags: [sizing, alavancagem, calculo, camada-4, gerenciamento]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 📐 Sizing e Alavancagem

> Cada trade tem tamanho calculado matematicamente — nunca por intuição.
> **Fórmula**: `Tamanho = (Capital × 1%) ÷ Distância do Stop em USD`

---

## Fórmula de Sizing

```python
# Cálculo exato usado pelo sistema
risco_usd    = capital_total * 0.01          # 1% fixo
stop_dist_usd = abs(entrada - stop) * preco  # distância em USD
tamanho      = risco_usd / stop_dist_usd     # em unidades do ativo
```

### Exemplo Prático — BTC
```
Capital: $10.000
Risco: $100 (1%)
Entrada BTC: $65.000
Stop: $64.500 (500 pts abaixo)
Stop em USD: 500 pts × (1 BTC / 1 pt) = $500 por BTC

Tamanho = $100 / $500 = 0.2 BTC
```

---

## Regras de Alavancagem

| Situação | Alavancagem Máxima |
|---|---|
| Operação normal (Silver Bullet) | 3x |
| Operação de alta confiança (A+) | 5x |
| Operação em teste / Breaker Block | 1x (sem alavancagem) |
| Nunca usar | >10x |

> [!CAUTION]
> Alavancagem amplifica **perdas e ganhos** proporcionalmente.
> Com 1% de risco por trade e 3x de alavancagem, uma perda de 0.33% no ativo = 1% da conta.
> O sizing já contempla a alavancagem no cálculo.

---

## Tabela Rápida de Referência

| Capital | Stop 200 pts BTC | Stop 500 pts BTC | Stop 1000 pts BTC |
|---|---|---|---|
| $5.000 | 0.25 BTC | 0.1 BTC | 0.05 BTC |
| $10.000 | 0.5 BTC | 0.2 BTC | 0.1 BTC |
| $25.000 | 1.25 BTC | 0.5 BTC | 0.25 BTC |
| $50.000 | 2.5 BTC | 1.0 BTC | 0.5 BTC |

---

## 🔗 Conexões Neurais
- [[MOC_Gerenciamento|💰 MOC Gerenciamento]]
- [[Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[Drawdown_e_Limites_Diarios|🛡️ Drawdown]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../CONDUCAO_DE_TRADE/Execucao_de_Entrada|🟢 Execução]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]