# Relatório Funil — London Sweep XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 719 | 4998 | 12.6% |
| 3 | `bias_not_neutral` | 719 | 432 | 287 | 60.1% |
| 4 | `asian_range_valid` | 432 | 432 | 0 | 100.0% |
| 5 | `killzone_has_candles` | 432 | 432 | 0 | 100.0% |
| 6 | `enough_candles_for_fvg` | 432 | 432 | 0 | 100.0% |
| 7 | `fvg_present_any` | 432 | 87 | 345 | 20.1% |
| 8 | `setup_combo_valid` | 87 | 0 | 87 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 4998 | 87.3% |
| 2 | `fvg_present_any` | 345 | 6.0% |
| 3 | `bias_not_neutral` | 287 | 5.0% |
| 4 | `setup_combo_valid` | 87 | 1.5% |
| 5 | `data_present` | 6 | 0.1% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (4998 falhas)
- 4998x: horário fora de 02:00:00-05:00:00

### `bias_not_neutral` (287 falhas)
- 287x: PO3 retornou NEUTRAL (close não em top/bottom 35% do range)

### `fvg_present_any` (345 falhas)
- 345x: nenhum FVG ativo nos últimos 12 candles M5

### `setup_combo_valid` (87 falhas)
- 87x: sweep + FVG + bias não alinharam na mesma direção

## Near-misses (passaram >=80% dos gates) — 432 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-22 02:00:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-22 02:05:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-22 02:10:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-22 02:15:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-22 02:20:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-22 02:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 02:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 03:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (4998 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
