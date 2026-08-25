# Relatório Funil — Silver Bullet NQ

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 7

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 240 | 1348 | 15.1% |
| 3 | `bias_not_neutral` | 209 | 209 | 0 | 100.0% |
| 4 | `today_has_data` | 209 | 209 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 209 | 209 | 0 | 100.0% |
| 6 | `fvg_present_any` | 209 | 21 | 188 | 10.0% |
| 7 | `fvg_aligned_with_bias` | 21 | 21 | 0 | 100.0% |
| 8 | `sweep_present_bullish` | 5 | 5 | 0 | 100.0% |
| 9 | `mss_confirmed_bullish` | 5 | 3 | 2 | 60.0% |
| 10 | `sweep_present_bearish` | 16 | 16 | 0 | 100.0% |
| 11 | `mss_confirmed_bearish` | 16 | 4 | 12 | 25.0% |
| 12 | `fvg_in_premium` | 4 | 4 | 0 | 100.0% |
| 13 | `signal_generated` | 7 | 7 | 0 | 100.0% |
| 14 | `cooldown_passed` | 171 | 140 | 31 | 81.9% |
| 15 | `fvg_in_discount` | 3 | 3 | 0 | 100.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1348 | 84.9% |
| 2 | `fvg_present_any` | 188 | 11.8% |
| 3 | `cooldown_passed` | 31 | 2.0% |
| 4 | `mss_confirmed_bearish` | 12 | 0.8% |
| 5 | `mss_confirmed_bullish` | 2 | 0.1% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1348 falhas)
- 1348x: horário fora de 10:00:00-11:00:00

### `fvg_present_any` (188 falhas)
- 188x: nenhum FVG ativo nos últimos 6 candles M5

### `mss_confirmed_bullish` (2 falhas)
- 2x: fechamento atual não rompeu swing high recente

### `mss_confirmed_bearish` (12 falhas)
- 12x: fechamento atual não rompeu swing low recente

### `cooldown_passed` (31 falhas)
- 7x: último sinal há 5min (cooldown 30min)
- 7x: último sinal há 10min (cooldown 30min)
- 7x: último sinal há 15min (cooldown 30min)

## Near-misses (passaram >=80% dos gates) — 202 candles

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
| 2026-04-23 10:00:00-04:00 | 8/9 | `mss_confirmed_bullish` | fechamento atual não rompeu swing high recente |
| 2026-04-23 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (7)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-28 10:40:00-04:00 | SELL | 26984.87 | 27006.51 | 26941.60 |
| 2026-05-01 10:00:00-04:00 | BUY | 27708.12 | 27680.77 | 27762.83 |
| 2026-05-01 10:35:00-04:00 | SELL | 27714.73 | 27742.66 | 27030.15 |
| 2026-05-05 10:25:00-04:00 | BUY | 27982.07 | 27962.97 | 28020.26 |
| 2026-05-07 10:00:00-04:00 | BUY | 28640.70 | 28625.93 | 28670.25 |
| 2026-05-12 10:00:00-04:00 | SELL | 29067.45 | 29083.18 | 29035.97 |
| 2026-05-18 10:35:00-04:00 | SELL | 29008.19 | 29041.35 | 28941.87 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1348 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
