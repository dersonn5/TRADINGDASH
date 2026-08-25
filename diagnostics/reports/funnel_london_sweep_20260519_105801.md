# Relatório Funil — London Sweep XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 6

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 719 | 4998 | 12.6% |
| 3 | `bias_not_neutral` | 691 | 691 | 0 | 100.0% |
| 4 | `asian_range_valid` | 691 | 691 | 0 | 100.0% |
| 5 | `killzone_has_candles` | 691 | 691 | 0 | 100.0% |
| 6 | `enough_candles_for_fvg` | 691 | 691 | 0 | 100.0% |
| 7 | `fvg_present_any` | 691 | 209 | 482 | 30.2% |
| 8 | `setup_combo_valid` | 209 | 24 | 185 | 11.5% |
| 9 | `mss_confirmed_bearish` | 18 | 4 | 14 | 22.2% |
| 10 | `mss_confirmed_bullish` | 6 | 2 | 4 | 33.3% |
| 11 | `signal_generated` | 6 | 6 | 0 | 100.0% |
| 12 | `cooldown_passed` | 687 | 659 | 28 | 95.9% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 4998 | 87.3% |
| 2 | `fvg_present_any` | 482 | 8.4% |
| 3 | `setup_combo_valid` | 185 | 3.2% |
| 4 | `cooldown_passed` | 28 | 0.5% |
| 5 | `mss_confirmed_bearish` | 14 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (4998 falhas)
- 4998x: horário fora de 02:00:00-05:00:00

### `fvg_present_any` (482 falhas)
- 482x: nenhum FVG ativo nos últimos 12 candles M5

### `setup_combo_valid` (185 falhas)
- 185x: sweep + FVG + bias não alinharam na mesma direção

### `mss_confirmed_bearish` (14 falhas)
- 14x: fechamento atual não rompeu swing low recente

### `mss_confirmed_bullish` (4 falhas)
- 4x: fechamento atual não rompeu swing high recente

### `cooldown_passed` (28 falhas)
- 6x: último sinal há 5min (cooldown 30min)
- 6x: último sinal há 10min (cooldown 30min)
- 6x: último sinal há 15min (cooldown 30min)

## Near-misses (passaram >=80% dos gates) — 685 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 02:00:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:05:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:10:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:15:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:20:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:25:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:35:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-21 02:40:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-21 02:45:00-04:00 | 8/9 | `mss_confirmed_bearish` | fechamento atual não rompeu swing low recente |
| 2026-04-21 02:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 02:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 03:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 04:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 04:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 04:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 04:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 12 candles M5 |
| 2026-04-21 04:20:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-21 04:25:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-21 04:30:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |

## Sinais Gerados (6)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-21 04:40:00-04:00 | BUY | 4800.95 | 4790.30 | 4822.25 |
| 2026-04-22 03:45:00-04:00 | SELL | 4784.85 | 4791.30 | 4769.90 |
| 2026-04-28 03:05:00-04:00 | BUY | 4645.70 | 4636.00 | 4685.10 |
| 2026-05-05 03:50:00-04:00 | SELL | 4559.30 | 4568.60 | 4537.00 |
| 2026-05-06 03:15:00-04:00 | SELL | 4674.15 | 4681.90 | 4653.30 |
| 2026-05-08 03:25:00-04:00 | SELL | 4719.40 | 4744.00 | 4670.20 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (4998 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
