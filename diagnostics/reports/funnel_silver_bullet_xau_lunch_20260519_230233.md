# Relatório Funil — Silver Bullet XAU — NY Lunch

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 252 | 132 | 120 | 52.4% |
| 4 | `today_has_data` | 132 | 132 | 0 | 100.0% |
| 5 | `london_bias_active` | 132 | 120 | 12 | 90.9% |
| 6 | `enough_candles_for_fvg` | 120 | 120 | 0 | 100.0% |
| 7 | `fvg_present_any` | 120 | 25 | 95 | 20.8% |
| 8 | `fvg_aligned_with_bias` | 25 | 18 | 7 | 72.0% |
| 9 | `london_bias_direction` | 18 | 0 | 18 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `bias_not_neutral` | 120 | 2.1% |
| 3 | `fvg_present_any` | 95 | 1.7% |
| 4 | `london_bias_direction` | 18 | 0.3% |
| 5 | `london_bias_active` | 12 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 13:00:00-14:00:00

### `bias_not_neutral` (120 falhas)
- 120x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (12 falhas)
- 12x: London did not sweep Asian Range

### `fvg_present_any` (95 falhas)
- 95x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (7 falhas)
- 7x: direção do FVG contraria daily bias

### `london_bias_direction` (18 falhas)
- 18x: London bias is BULLISH, but setup is BEARISH

## Near-misses (passaram >=80% dos gates) — 132 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 13:00:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 13:05:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 13:10:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 13:15:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 13:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 13:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:05:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:10:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:15:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:20:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:25:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:30:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 13:45:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:50:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 13:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 13:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
