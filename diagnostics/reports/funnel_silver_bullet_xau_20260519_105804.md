# Relatório Funil — Silver Bullet XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 9

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 215 | 215 | 0 | 100.0% |
| 4 | `today_has_data` | 215 | 215 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 215 | 215 | 0 | 100.0% |
| 6 | `fvg_present_any` | 215 | 13 | 202 | 6.0% |
| 7 | `fvg_aligned_with_bias` | 13 | 13 | 0 | 100.0% |
| 8 | `sweep_present_bearish` | 6 | 6 | 0 | 100.0% |
| 9 | `mss_confirmed_bearish` | 6 | 5 | 1 | 83.3% |
| 10 | `fvg_in_premium` | 5 | 5 | 0 | 100.0% |
| 11 | `signal_generated` | 9 | 9 | 0 | 100.0% |
| 12 | `cooldown_passed` | 230 | 193 | 37 | 83.9% |
| 13 | `sweep_present_bullish` | 7 | 7 | 0 | 100.0% |
| 14 | `mss_confirmed_bullish` | 7 | 4 | 3 | 57.1% |
| 15 | `fvg_in_discount` | 4 | 4 | 0 | 100.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `fvg_present_any` | 202 | 3.5% |
| 3 | `cooldown_passed` | 37 | 0.6% |
| 4 | `data_present` | 6 | 0.1% |
| 5 | `mss_confirmed_bullish` | 3 | 0.1% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 10:00:00-11:00:00

### `fvg_present_any` (202 falhas)
- 202x: nenhum FVG ativo nos últimos 6 candles M5

### `mss_confirmed_bearish` (1 falhas)
- 1x: fechamento atual não rompeu swing low recente

### `cooldown_passed` (37 falhas)
- 8x: último sinal há 5min (cooldown 30min)
- 8x: último sinal há 10min (cooldown 30min)
- 7x: último sinal há 15min (cooldown 30min)

### `mss_confirmed_bullish` (3 falhas)
- 3x: fechamento atual não rompeu swing high recente

## Near-misses (passaram >=80% dos gates) — 206 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-20 10:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:30:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:45:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-20 10:55:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:00:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:10:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:15:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:20:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:30:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |

## Sinais Gerados (9)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-04-21 10:45:00-04:00 | SELL | 4770.65 | 4777.90 | 4756.15 |
| 2026-04-23 10:00:00-04:00 | SELL | 4747.30 | 4752.30 | 4705.70 |
| 2026-04-24 10:10:00-04:00 | BUY | 4737.15 | 4731.50 | 4748.45 |
| 2026-04-27 10:55:00-04:00 | SELL | 4700.95 | 4706.20 | 4690.45 |
| 2026-05-01 10:00:00-04:00 | BUY | 4624.20 | 4620.10 | 4640.30 |
| 2026-05-04 10:20:00-04:00 | BUY | 4578.85 | 4573.70 | 4626.50 |
| 2026-05-05 10:15:00-04:00 | SELL | 4586.35 | 4588.70 | 4537.00 |
| 2026-05-08 10:10:00-04:00 | SELL | 4745.25 | 4749.00 | 4716.60 |
| 2026-05-15 10:20:00-04:00 | BUY | 4557.25 | 4554.00 | 4625.90 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
