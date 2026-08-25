---
tags: [estrategia, silver-bullet, eth, camada-3, modelo, validado]
camada: 3
categoria: TRADE_SYSTEM
ativo: ETH/USDT
timeframe_entrada: 5m
janela_tempo: "10:00–11:00 ET | 14:00–15:00 ET"
win_rate: 30.4%
profit_factor_ideal: 1.15
profit_factor_estressado: 1.08
total_trades_backtest: 23
periodo_backtest: 2022-2024
status: validado
ultima_revisao: 2026-06-27
---

# ⚡ Silver Bullet — ETH/USDT

> **Camada 3 — Modelo Validado**
> Mesmo modelo do Silver Bullet BTC, mas ETH apresenta comportamento distinto.
> **PF 1.08 estressado | WR 30.4% | Requer confirmação de SMT com BTC**

---

## Diferenças Críticas em Relação ao BTC

> [!WARNING]
> ETH é **mais volátil** e menos previsível que BTC no intraday.
> Exige **confirmação adicional** via SMT Divergência com BTC antes de qualquer entrada.

| Parâmetro | BTC/USDT | ETH/USDT |
|---|---|---|
| Win Rate | 41.2% | 30.4% |
| PF Estressado | 1.84 | 1.08 |
| Trades/3 anos | 17 | 23 |
| Filtro extra | Não | SMT obrigatório |
| BE proibido NY AM | Sim | Sim |

---

## Condições de Entrada ETH (Adicional ao BTC)

Todas as condições do [[Silver_Bullet_BTC_USDT]] se aplicam, **mais**:

### Filtro Extra Obrigatório — SMT Divergência
- **Para LONG ETH**: BTC **não deve** estar fazendo nova mínima enquanto ETH tem oportunidade de long. Se BTC está afundando, ETH long = alto risco.
- **Para SHORT ETH**: BTC **não deve** estar em alta firme enquanto ETH tem setup de short.
- **SMT favorável**: BTC e ETH confirmando a mesma direção = sinal mais forte.

### Filtro de Sessão ETH
ETH responde melhor à sessão **NY AM** que ao NY PM.
Trades no NY PM para ETH têm performance histórica inferior — considerar reduzir tamanho de posição.

---

## Execução
```
ENTRADA:  Limit order no CE (50%) da FVG de M5
STOP:     1 tick abaixo da mínima da FVG (LONG) ou acima da máxima (SHORT)
ALVO 1:  2R
ALVO 2:  FVG de H1 mais próximo na direção do trade
```

---

## Performance Histórica (Backtest 2022–2024)

| Métrica | Ideal | Estressado |
|---|---|---|
| PnL Total | +$247.52 | +$134.97 |
| Win Rate | 30.4% | 30.4% |
| Profit Factor | 1.15 | **1.08** |
| Total Trades | 23 | 23 |

> ETH tem PF mais baixo que BTC — opera com tamanho de posição reduzido em cenário de dúvida.

---

## 🔗 Conexões Neurais
- [[MOC_Estrategias_Validadas|📈 MOC Estratégias]]
- [[Silver_Bullet_BTC_USDT|⚡ Silver Bullet BTC — Protocolo Base]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 FVG]]
- [[../01_Regras_ICT/ICT_Liquidity_YouTube_Distilled|💧 Liquidity & SMT]]
- [[../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|⏰ Killzones]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]