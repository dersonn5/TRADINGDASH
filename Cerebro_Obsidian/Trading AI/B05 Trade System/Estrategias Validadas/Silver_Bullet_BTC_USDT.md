---
tags: [estrategia, silver-bullet, btc, camada-3, modelo, validado]
camada: 3
categoria: TRADE_SYSTEM
ativo: BTC/USDT
timeframe_entrada: 5m
janela_tempo: "10:00–11:00 ET | 14:00–15:00 ET"
win_rate: 41.2%
profit_factor_ideal: 1.91
profit_factor_estressado: 1.84
total_trades_backtest: 17
periodo_backtest: 2022-2024
status: validado
ultima_revisao: 2026-06-27
---

# ⚡ Silver Bullet — BTC/USDT

> **Camada 3 — Modelo Validado**
> Estratégia algorítmica baseada no Silver Bullet Model do ICT, adaptada para o mercado de cripto 24/7.
> **PF 1.84 estressado | WR 41.2% | 3 anos de backtest**

---

## 1. Identificação

| Campo | Valor |
|---|---|
| Nome | Silver Bullet BTC/USDT |
| Tipo | Setup de continuação / reversão em killzone |
| Ativo | BTC/USDT (Binance Spot/Futures) |
| Timeframe análise | H1, H4 (bias) + M5 (entrada) |
| Timeframe entrada | M5 |
| Sessão | NY AM (principal) + NY PM (secundária) |

---

## 2. Contexto de Mercado Exigido

Antes de qualquer análise de setup, verificar **TODOS** os itens:

- [ ] **Daily Bias mapeado**: identificar se H4/D1 está em estrutura de alta ou baixa
- [ ] **DOL identificado**: onde o preço está sendo atraído (mínima/máxima de ontem, FVG de H1)
- [ ] **Posição no AMD**: estamos na fase de Manipulação (Judas Swing) ou início de Distribuição?
- [ ] **EMA 200 no M5**: o preço está do lado correto da EMA 200 na direção do trade?

> [!IMPORTANT]
> **Filtro obrigatório**: Se Daily Bias for NEUTRO (sem direção clara em H4), o Silver Bullet **não é executado**.

---

## 3. Janela de Tempo (Killzone)

| Sessão | Horário ET | Horário BRT | Prioridade |
|---|---|---|---|
| NY AM Silver Bullet | 10:00 – 11:00 | 12:00 – 13:00 | ⭐⭐⭐ Principal |
| NY PM Silver Bullet | 14:00 – 15:00 | 16:00 – 17:00 | ⭐⭐ Secundária |

> **Regra**: Nenhuma entrada **fora** dessas janelas é válida como Silver Bullet.
> Setup fora da janela = outro padrão = outro protocolo.

---

## 4. Condições de Entrada (Obrigatórias — todas devem estar presentes)

### Para LONG (Bullish Silver Bullet)
1. **Daily Bias BULLISH** confirmado em H4
2. **Varredura de liquidez**: o preço varremos um nível de venda (SSL, Equal Lows, Asian Low)
3. **FVG bullish formado** no M5 durante a janela 10:00–11:00 ET
4. **MSS bullish no M5**: quebra de estrutura de alta após a varredura
5. **FVG dentro da janela temporal**: o FVG deve ser formado **dentro** da hora de Silver Bullet
6. **EMA 200 abaixo do preço**: o trade é na direção da EMA

### Para SHORT (Bearish Silver Bullet)
1. **Daily Bias BEARISH** confirmado em H4
2. **Varredura de liquidez**: preço varremos BSL (Equal Highs, Asian High)
3. **FVG bearish formado** no M5 durante a janela 10:00–11:00 ET
4. **MSS bearish no M5**: quebra de estrutura de baixa após a varredura
5. **FVG dentro da janela temporal**
6. **EMA 200 acima do preço**

---

## 5. Execução

```
ENTRADA:  Limit order no CE (50%) da FVG formada no M5
STOP:     1 tick abaixo da mínima do FVG (LONG) ou acima da máxima (SHORT)
ALVO 1:  2R (recompensa de 2x o risco)
ALVO 2:  Próximo nível de liquidez (mínima/máxima de ontem, FVG de H1)
```

> [!CAUTION]
> **Não usar ordens a mercado**. A entrada sempre é com limit order no CE do FVG.
> Slippage em BTC pode ser significativo em momento de alta volatilidade.

---

## 6. Gerenciamento — Regras Específicas do BTC

> [!WARNING]
> **Break-Even é PROIBIDO no NY AM** para este ativo.
> Backtests provaram que BE precoce derruba o WR de 44.4% para 16.7%.
> Ver: [[../02_Licoes_Aprendidas/Erros_Evitar#perigo-de-mover-para-break-even]]

| Regra | NY AM Session | NY PM Session |
|---|---|---|
| Break-Even | ❌ Proibido | ✅ Permitido após 1.5R |
| Parcial 50% | Em 1.5R | Em 1R |
| Stop ajuste | Somente com 2R+ atingido | Permitido em 1R |
| Trailing Stop | ❌ Não usar | ✅ Após 2R |

---

## 7. Performance Histórica (Backtest 2022–2024)

| Métrica | Ideal | Estressado |
|---|---|---|
| PnL Total | +$916.15 | +$863.24 |
| Win Rate | 41.2% | 41.2% |
| Profit Factor | 1.91 | **1.84** |
| Total Trades | 17 | 17 |
| Período | 3 anos | 3 anos |

> Simulação estressada inclui: slippage de 0.05%, delay de 1 candle, spread de corretora.

---

## 8. Cenários Possíveis

### ✅ Cenário A — Setup Limpo (mais comum)
Preço varre SSL → forma FVG bullish no M5 → MSS → retorna ao CE → expansão ao alvo.
**Ação**: Executar normalmente conforme protocolo.

### ⚠️ Cenário B — FVG Parcialmente Preenchido
O preço toca o CE mas não retorna imediatamente; fica lateralizando.
**Ação**: Manter a ordem. Se o preço fechar **abaixo** do CE com corpo de vela → cancelar e aguardar próxima janela.

### ⚠️ Cenário C — Dupla Varredura (Stop Hunt no Stop Hunt)
O preço varre o SSL, forma FVG, depois varre mais fundo antes de subir.
**Ação**: Se o stop for atingido e a estrutura se mantiver, o setup pode ser reconsiderado na próxima janela PM.

### ❌ Cenário D — Invalidação por Corpo de Vela
Corpo de vela M5 fecha decisivamente abaixo do CE (para LONG).
**Ação**: Cancelar ordem imediatamente. O suporte institucional falhou.

---

## 🔗 Conexões Neurais
- [[MOC_Estrategias_Validadas|📈 MOC Estratégias]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[Silver_Bullet_ETH_USDT|⚡ Silver Bullet ETH]]
- [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais e Break-Even]]
- [[CONDUCAO_DE_TRADE/Execucao_de_Entrada|🟢 Execução de Entrada]]
- [[DURANTE_O_TRADE/Cenarios_Possiveis|🔀 Cenários Possíveis]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 FVG — Conceito]]
- [[../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|⏰ Killzones]]
- [[../01_Regras_ICT/ICT_MarketStructure_YouTube_Distilled|📊 Market Structure]]
- [[../01_Regras_ICT/ICT_Liquidity_YouTube_Distilled|💧 Liquidity]]
- [[../04_Backtests/Relatorio_Otimizacao_Risco_Cripto_2022_2024|📋 Backtest Report]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/Power_of_3_e_AMD]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]