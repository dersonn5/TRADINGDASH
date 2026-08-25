# Relatório Funil — Silver Bullet NQ — NY Close

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 252 | 1336 | 15.9% |
| 3 | `bias_not_neutral` | 252 | 156 | 96 | 61.9% |
| 4 | `today_has_data` | 156 | 156 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 156 | 156 | 0 | 100.0% |
| 6 | `fvg_present_any` | 156 | 49 | 107 | 31.4% |
| 7 | `fvg_aligned_with_bias` | 49 | 30 | 19 | 61.2% |
| 8 | `sweep_present_bearish` | 3 | 3 | 0 | 100.0% |
| 9 | `mss_confirmed_bearish` | 3 | 0 | 3 | 0.0% |
| 10 | `sweep_present_bullish` | 27 | 27 | 0 | 100.0% |
| 11 | `mss_confirmed_bullish` | 27 | 13 | 14 | 48.1% |
| 12 | `fvg_in_discount` | 13 | 0 | 13 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1336 | 84.1% |
| 2 | `fvg_present_any` | 107 | 6.7% |
| 3 | `bias_not_neutral` | 96 | 6.0% |
| 4 | `fvg_aligned_with_bias` | 19 | 1.2% |
| 5 | `mss_confirmed_bullish` | 14 | 0.9% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1336 falhas)
- 1336x: horário fora de 15:00:00-16:00:00

### `bias_not_neutral` (96 falhas)
- 96x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (107 falhas)
- 107x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (19 falhas)
- 19x: direção do FVG contraria daily bias

### `mss_confirmed_bearish` (3 falhas)
- 3x: fechamento atual não rompeu swing low recente

### `mss_confirmed_bullish` (14 falhas)
- 14x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (13 falhas)
- 13x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

## Near-misses (passaram >=80% dos gates) — 156 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 15:00:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:05:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:10:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:15:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 15:25:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:30:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 15:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 15:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 15:45:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-21 15:50:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-21 15:55:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 15:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:10:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-22 15:15:00-04:00 | 9/10 | `fvg_in_discount` | FVG está acima do equilibrium (zona premium, não serve pra BUY) |
| 2026-04-22 15:20:00-04:00 | 9/10 | `fvg_in_discount` | FVG está acima do equilibrium (zona premium, não serve pra BUY) |
| 2026-04-22 15:25:00-04:00 | 9/10 | `fvg_in_discount` | FVG está acima do equilibrium (zona premium, não serve pra BUY) |
| 2026-04-22 15:30:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-22 15:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:45:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 15:55:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-24 15:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 15:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 15:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 15:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 15:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 15:25:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1336 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
