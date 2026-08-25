# Relatório Funil — Silver Bullet XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 1

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 247 | 115 | 132 | 46.6% |
| 4 | `today_has_data` | 115 | 115 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 115 | 115 | 0 | 100.0% |
| 6 | `fvg_present_any` | 115 | 13 | 102 | 11.3% |
| 7 | `fvg_aligned_with_bias` | 13 | 8 | 5 | 61.5% |
| 8 | `sweep_present_bearish` | 2 | 2 | 0 | 100.0% |
| 9 | `mss_confirmed_bearish` | 2 | 2 | 0 | 100.0% |
| 10 | `fvg_in_premium` | 2 | 1 | 1 | 50.0% |
| 11 | `signal_generated` | 1 | 1 | 0 | 100.0% |
| 12 | `cooldown_passed` | 215 | 210 | 5 | 97.7% |
| 13 | `sweep_present_bullish` | 6 | 6 | 0 | 100.0% |
| 14 | `mss_confirmed_bullish` | 6 | 1 | 5 | 16.7% |
| 15 | `fvg_in_discount` | 1 | 0 | 1 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `bias_not_neutral` | 132 | 2.3% |
| 3 | `fvg_present_any` | 102 | 1.8% |
| 4 | `data_present` | 6 | 0.1% |
| 5 | `cooldown_passed` | 5 | 0.1% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (132 falhas)
- 132x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (102 falhas)
- 102x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (5 falhas)
- 5x: direção do FVG contraria daily bias

### `fvg_in_premium` (1 falhas)
- 1x: FVG está abaixo do equilibrium (zona discount, não serve pra SELL)

### `cooldown_passed` (5 falhas)
- 1x: último sinal há 5min (cooldown 30min)
- 1x: último sinal há 10min (cooldown 30min)
- 1x: último sinal há 15min (cooldown 30min)

### `mss_confirmed_bullish` (5 falhas)
- 5x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (1 falhas)
- 1x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

## Near-misses (passaram >=80% dos gates) — 114 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-22 10:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:30:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:45:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:55:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:00:00-04:00 | 9/10 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:10:00-04:00 | 10/11 | `fvg_in_discount` | FVG está acima do equilibrium (zona premium, não serve pra BUY) |
| 2026-04-24 10:15:00-04:00 | 9/10 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 10:20:00-04:00 | 9/10 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 10:25:00-04:00 | 9/10 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 10:30:00-04:00 | 9/10 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (1)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-23 10:00:00-04:00 | SELL | 4747.30 | 4752.30 | 4705.70 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
