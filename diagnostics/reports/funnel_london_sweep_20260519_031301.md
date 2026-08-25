# Relatório Funil — London Sweep XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:00:00-04:00
**Candles M5 totais:** 5762
**Candles avaliados (após warmup 50):** 5712
**Sinais gerados:** 3

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5712 | 5706 | 6 | 99.9% |
| 2 | `killzone_active` | 5706 | 719 | 4987 | 12.6% |
| 3 | `bias_not_neutral` | 705 | 418 | 287 | 59.3% |
| 4 | `asian_range_valid` | 418 | 418 | 0 | 100.0% |
| 5 | `killzone_has_candles` | 418 | 418 | 0 | 100.0% |
| 6 | `enough_candles_for_fvg` | 418 | 418 | 0 | 100.0% |
| 7 | `fvg_present_any` | 418 | 293 | 125 | 70.1% |
| 8 | `setup_combo_valid` | 293 | 13 | 280 | 4.4% |
| 9 | `mss_confirmed_bearish` | 13 | 3 | 10 | 23.1% |
| 10 | `signal_generated` | 3 | 3 | 0 | 100.0% |
| 11 | `cooldown_passed` | 662 | 648 | 14 | 97.9% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 4987 | 87.3% |
| 2 | `bias_not_neutral` | 287 | 5.0% |
| 3 | `setup_combo_valid` | 280 | 4.9% |
| 4 | `fvg_present_any` | 125 | 2.2% |
| 5 | `cooldown_passed` | 14 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (4987 falhas)
- 4987x: horário fora de 02:00:00-05:00:00

### `bias_not_neutral` (287 falhas)
- 287x: PO3 retornou NEUTRAL (close não em top/bottom 35% do range)

### `fvg_present_any` (125 falhas)
- 125x: nenhum FVG ativo nos últimos 12 candles M5

### `setup_combo_valid` (280 falhas)
- 280x: sweep + FVG + bias não alinharam na mesma direção

### `mss_confirmed_bearish` (10 falhas)
- 10x: fechamento atual não rompeu swing low recente

### `cooldown_passed` (14 falhas)
- 3x: último sinal há 5min (cooldown 30min)
- 3x: último sinal há 10min (cooldown 30min)
- 3x: último sinal há 15min (cooldown 30min)

## Near-misses (passaram >=80% dos gates) — 415 candles

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
| 2026-04-22 03:15:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 03:20:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 03:25:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 03:30:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 03:35:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 03:40:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-22 04:15:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:20:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:25:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:30:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:35:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:40:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:45:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:50:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-22 04:55:00-04:00 | 7/8 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |

## Sinais Gerados (3)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-22 03:45:00-04:00 | SELL | 4780.00 | 4791.30 | 4757.40 |
| 2026-04-23 03:00:00-04:00 | SELL | 4729.50 | 4739.50 | 4705.70 |
| 2026-04-23 04:35:00-04:00 | SELL | 4724.30 | 4742.60 | 4687.70 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (4987 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
