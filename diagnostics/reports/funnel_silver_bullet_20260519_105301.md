# Relatório Funil — Silver Bullet NQ

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 240 | 1348 | 15.1% |
| 3 | `bias_not_neutral` | 240 | 156 | 84 | 65.0% |
| 4 | `today_has_data` | 156 | 156 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 156 | 156 | 0 | 100.0% |
| 6 | `fvg_present_any` | 156 | 28 | 128 | 17.9% |
| 7 | `fvg_aligned_with_bias` | 28 | 11 | 17 | 39.3% |
| 8 | `sweep_present_bullish` | 11 | 0 | 11 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1348 | 84.9% |
| 2 | `fvg_present_any` | 128 | 8.1% |
| 3 | `bias_not_neutral` | 84 | 5.3% |
| 4 | `fvg_aligned_with_bias` | 17 | 1.1% |
| 5 | `sweep_present_bullish` | 11 | 0.7% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1348 falhas)
- 1348x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (84 falhas)
- 84x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (128 falhas)
- 128x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (17 falhas)
- 17x: direção do FVG contraria daily bias

### `sweep_present_bullish` (11 falhas)
- 11x: sem sweep do PDL desde 04:00 EST

## Near-misses (passaram >=80% dos gates) — 156 candles

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
| 2026-04-21 10:45:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:55:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
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
| 2026-04-24 10:00:00-04:00 | 6/7 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1348 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
