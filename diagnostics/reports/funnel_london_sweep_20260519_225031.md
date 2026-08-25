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
| 3 | `bias_not_neutral` | 719 | 467 | 252 | 65.0% |
| 4 | `asian_range_valid` | 467 | 467 | 0 | 100.0% |
| 5 | `killzone_has_candles` | 467 | 467 | 0 | 100.0% |
| 6 | `enough_candles_for_fvg` | 467 | 467 | 0 | 100.0% |
| 7 | `fvg_present_any` | 467 | 132 | 335 | 28.3% |
| 8 | `setup_combo_valid` | 132 | 23 | 109 | 17.4% |
| 9 | `mss_confirmed_bullish` | 8 | 1 | 7 | 12.5% |
| 10 | `m1_confirmation` | 4 | 0 | 4 | 0.0% |
| 11 | `mss_confirmed_bearish` | 15 | 3 | 12 | 20.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 4998 | 87.3% |
| 2 | `fvg_present_any` | 335 | 5.9% |
| 3 | `bias_not_neutral` | 252 | 4.4% |
| 4 | `setup_combo_valid` | 109 | 1.9% |
| 5 | `mss_confirmed_bearish` | 12 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (4998 falhas)
- 4998x: horário fora de 02:00:00-05:00:00

### `bias_not_neutral` (252 falhas)
- 252x: PO3 retornou NEUTRAL (close não em top/bottom 35% do range)

### `fvg_present_any` (335 falhas)
- 335x: nenhum FVG ativo nos últimos 12 candles M5

### `setup_combo_valid` (109 falhas)
- 109x: sweep + FVG + bias não alinharam na mesma direção

### `mss_confirmed_bullish` (7 falhas)
- 7x: fechamento atual não rompeu swing high recente

### `m1_confirmation` (4 falhas)
- 4x: M1 sem MSS+FVG/BPR confirmado na zona do FVG M5

### `mss_confirmed_bearish` (12 falhas)
- 12x: fechamento atual não rompeu swing low recente

## Near-misses (passaram >=80% dos gates) — 467 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 02:00:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:05:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:10:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:15:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:20:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:25:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:35:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:40:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
| 2026-04-21 02:45:00-04:00 | 7/8 | `setup_combo_valid` | sweep + FVG + bias não alinharam na mesma direção |
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

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (4998 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
