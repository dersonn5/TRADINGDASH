# Relatório Funil — Silver Bullet NQ — NY Lunch

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 244 | 1344 | 15.4% |
| 3 | `bias_not_neutral` | 244 | 156 | 88 | 63.9% |
| 4 | `today_has_data` | 156 | 156 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 156 | 156 | 0 | 100.0% |
| 6 | `fvg_present_any` | 156 | 45 | 111 | 28.8% |
| 7 | `fvg_aligned_with_bias` | 45 | 21 | 24 | 46.7% |
| 8 | `sweep_present_bullish` | 21 | 21 | 0 | 100.0% |
| 9 | `mss_confirmed_bullish` | 21 | 9 | 12 | 42.9% |
| 10 | `fvg_in_discount` | 9 | 0 | 9 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1344 | 84.6% |
| 2 | `fvg_present_any` | 111 | 7.0% |
| 3 | `bias_not_neutral` | 88 | 5.5% |
| 4 | `fvg_aligned_with_bias` | 24 | 1.5% |
| 5 | `mss_confirmed_bullish` | 12 | 0.8% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1344 falhas)
- 1344x: horário fora de 13:00:00-14:00:00

### `bias_not_neutral` (88 falhas)
- 88x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (111 falhas)
- 111x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (24 falhas)
- 24x: direção do FVG contraria daily bias

### `mss_confirmed_bullish` (12 falhas)
- 12x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (9 falhas)
- 9x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

## Near-misses (passaram >=80% dos gates) — 156 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-22 13:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:05:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:10:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:15:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:20:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:25:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:30:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:35:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:40:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:45:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-22 13:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 13:55:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:05:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:10:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:15:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:20:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:25:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:30:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:45:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:50:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 13:55:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-27 13:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-27 13:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-27 13:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-27 13:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-27 13:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-27 13:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1344 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
