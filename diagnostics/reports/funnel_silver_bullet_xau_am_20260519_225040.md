# Relatório Funil — Silver Bullet XAU — NY AM

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 3

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 237 | 117 | 120 | 49.4% |
| 4 | `today_has_data` | 117 | 117 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 117 | 117 | 0 | 100.0% |
| 6 | `fvg_present_any` | 117 | 21 | 96 | 17.9% |
| 7 | `fvg_aligned_with_bias` | 21 | 10 | 11 | 47.6% |
| 8 | `sweep_present_bearish` | 3 | 3 | 0 | 100.0% |
| 9 | `mss_confirmed_bearish` | 3 | 3 | 0 | 100.0% |
| 10 | `fvg_in_premium` | 3 | 3 | 0 | 100.0% |
| 11 | `m1_confirmation` | 3 | 3 | 0 | 100.0% |
| 12 | `signal_generated` | 3 | 3 | 0 | 100.0% |
| 13 | `cooldown_passed` | 215 | 200 | 15 | 93.0% |
| 14 | `sweep_present_bullish` | 7 | 7 | 0 | 100.0% |
| 15 | `mss_confirmed_bullish` | 7 | 2 | 5 | 28.6% |
| 16 | `fvg_in_discount` | 2 | 0 | 2 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `bias_not_neutral` | 120 | 2.1% |
| 3 | `fvg_present_any` | 96 | 1.7% |
| 4 | `cooldown_passed` | 15 | 0.3% |
| 5 | `fvg_aligned_with_bias` | 11 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (120 falhas)
- 120x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (96 falhas)
- 96x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (11 falhas)
- 11x: direção do FVG contraria daily bias

### `cooldown_passed` (15 falhas)
- 3x: último sinal há 5min (cooldown 30min)
- 3x: último sinal há 10min (cooldown 30min)
- 3x: último sinal há 15min (cooldown 30min)

### `mss_confirmed_bullish` (5 falhas)
- 5x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (2 falhas)
- 2x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

## Near-misses (passaram >=80% dos gates) — 114 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 10:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:30:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:45:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 10:50:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 10:55:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:00:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:10:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:15:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:20:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:25:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:30:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (3)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-23 10:00:00-04:00 | SELL | 4747.30 | 4755.30 | 4705.70 |
| 2026-05-05 10:15:00-04:00 | SELL | 4586.35 | 4594.35 | 4537.00 |
| 2026-05-08 10:10:00-04:00 | SELL | 4745.25 | 4753.25 | 4716.60 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
