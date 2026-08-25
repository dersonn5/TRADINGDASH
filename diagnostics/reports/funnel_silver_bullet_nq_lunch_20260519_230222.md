# Relatório Funil — Silver Bullet NQ — NY Lunch

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5722
**Candles avaliados (após warmup 50):** 5672
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5672 | 5652 | 20 | 99.6% |
| 2 | `killzone_active` | 5652 | 252 | 5400 | 4.5% |
| 3 | `bias_not_neutral` | 252 | 168 | 84 | 66.7% |
| 4 | `today_has_data` | 168 | 168 | 0 | 100.0% |
| 5 | `london_bias_active` | 168 | 132 | 36 | 78.6% |
| 6 | `enough_candles_for_fvg` | 132 | 132 | 0 | 100.0% |
| 7 | `fvg_present_any` | 132 | 24 | 108 | 18.2% |
| 8 | `fvg_aligned_with_bias` | 24 | 10 | 14 | 41.7% |
| 9 | `london_bias_direction` | 10 | 10 | 0 | 100.0% |
| 10 | `sweep_present_bullish` | 10 | 10 | 0 | 100.0% |
| 11 | `mss_confirmed_bullish` | 10 | 4 | 6 | 40.0% |
| 12 | `fvg_in_discount` | 4 | 0 | 4 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5400 | 95.2% |
| 2 | `fvg_present_any` | 108 | 1.9% |
| 3 | `bias_not_neutral` | 84 | 1.5% |
| 4 | `london_bias_active` | 36 | 0.6% |
| 5 | `data_present` | 20 | 0.4% |

## Motivos de Falha (top 3 por gate)

### `data_present` (20 falhas)
- 20x: dados M5 ou D1 vazios

### `killzone_active` (5400 falhas)
- 5400x: horário fora de 13:00:00-14:00:00

### `bias_not_neutral` (84 falhas)
- 84x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (36 falhas)
- 36x: London did not sweep Asian Range

### `fvg_present_any` (108 falhas)
- 108x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (14 falhas)
- 14x: direção do FVG contraria daily bias

### `mss_confirmed_bullish` (6 falhas)
- 6x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (4 falhas)
- 4x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

## Near-misses (passaram >=80% dos gates) — 168 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 13:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 13:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:05:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:10:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:15:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:20:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:25:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5400 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
