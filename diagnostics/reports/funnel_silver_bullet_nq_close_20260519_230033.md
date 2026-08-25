# Relatório Funil — Silver Bullet NQ — NY Close

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5722
**Candles avaliados (após warmup 50):** 5672
**Sinais gerados:** 1

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5672 | 5652 | 20 | 99.6% |
| 2 | `killzone_active` | 5652 | 252 | 5400 | 4.5% |
| 3 | `bias_not_neutral` | 247 | 163 | 84 | 66.0% |
| 4 | `today_has_data` | 163 | 163 | 0 | 100.0% |
| 5 | `london_bias_active` | 163 | 127 | 36 | 77.9% |
| 6 | `enough_candles_for_fvg` | 127 | 127 | 0 | 100.0% |
| 7 | `fvg_present_any` | 127 | 23 | 104 | 18.1% |
| 8 | `fvg_aligned_with_bias` | 23 | 7 | 16 | 30.4% |
| 9 | `london_bias_direction` | 7 | 4 | 3 | 57.1% |
| 10 | `sweep_present_bullish` | 4 | 4 | 0 | 100.0% |
| 11 | `mss_confirmed_bullish` | 4 | 3 | 1 | 75.0% |
| 12 | `fvg_in_discount` | 3 | 1 | 2 | 33.3% |
| 13 | `m1_confirmation` | 1 | 1 | 0 | 100.0% |
| 14 | `signal_generated` | 1 | 1 | 0 | 100.0% |
| 15 | `cooldown_passed` | 56 | 51 | 5 | 91.1% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5400 | 95.2% |
| 2 | `fvg_present_any` | 104 | 1.8% |
| 3 | `bias_not_neutral` | 84 | 1.5% |
| 4 | `london_bias_active` | 36 | 0.6% |
| 5 | `data_present` | 20 | 0.4% |

## Motivos de Falha (top 3 por gate)

### `data_present` (20 falhas)
- 20x: dados M5 ou D1 vazios

### `killzone_active` (5400 falhas)
- 5400x: horário fora de 15:00:00-16:00:00

### `bias_not_neutral` (84 falhas)
- 84x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (36 falhas)
- 36x: London did not sweep Asian Range

### `fvg_present_any` (104 falhas)
- 104x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (16 falhas)
- 16x: direção do FVG contraria daily bias

### `london_bias_direction` (3 falhas)
- 3x: London bias is BEARISH, but setup is BULLISH

### `mss_confirmed_bullish` (1 falhas)
- 1x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (2 falhas)
- 2x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

### `cooldown_passed` (5 falhas)
- 1x: último sinal há 5min (cooldown 30min)
- 1x: último sinal há 10min (cooldown 30min)
- 1x: último sinal há 15min (cooldown 30min)

## Near-misses (passaram >=80% dos gates) — 162 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 15:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 15:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 15:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:10:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 15:15:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 15:20:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 15:25:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 15:30:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 15:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 15:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 15:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 15:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 15:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 15:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 15:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |

## Sinais Gerados (1)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-05-12 15:15:00-04:00 | BUY | 29022.00 | 28997.00 | 29480.00 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5400 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
