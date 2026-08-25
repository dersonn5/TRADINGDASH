# Relatório Funil — Silver Bullet XAU — NY AM

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 2

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 242 | 122 | 120 | 50.4% |
| 4 | `today_has_data` | 122 | 122 | 0 | 100.0% |
| 5 | `london_bias_active` | 122 | 110 | 12 | 90.2% |
| 6 | `enough_candles_for_fvg` | 110 | 110 | 0 | 100.0% |
| 7 | `fvg_present_any` | 110 | 24 | 86 | 21.8% |
| 8 | `fvg_aligned_with_bias` | 24 | 14 | 10 | 58.3% |
| 9 | `london_bias_direction` | 14 | 9 | 5 | 64.3% |
| 10 | `sweep_present_bullish` | 7 | 7 | 0 | 100.0% |
| 11 | `mss_confirmed_bullish` | 7 | 2 | 5 | 28.6% |
| 12 | `fvg_in_discount` | 2 | 0 | 2 | 0.0% |
| 13 | `sweep_present_bearish` | 2 | 2 | 0 | 100.0% |
| 14 | `mss_confirmed_bearish` | 2 | 2 | 0 | 100.0% |
| 15 | `fvg_in_premium` | 2 | 2 | 0 | 100.0% |
| 16 | `m1_confirmation` | 2 | 2 | 0 | 100.0% |
| 17 | `signal_generated` | 2 | 2 | 0 | 100.0% |
| 18 | `cooldown_passed` | 116 | 106 | 10 | 91.4% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `bias_not_neutral` | 120 | 2.1% |
| 3 | `fvg_present_any` | 86 | 1.5% |
| 4 | `london_bias_active` | 12 | 0.2% |
| 5 | `fvg_aligned_with_bias` | 10 | 0.2% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (120 falhas)
- 120x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (12 falhas)
- 12x: London did not sweep Asian Range

### `fvg_present_any` (86 falhas)
- 86x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (10 falhas)
- 10x: direção do FVG contraria daily bias

### `london_bias_direction` (5 falhas)
- 5x: London bias is BULLISH, but setup is BEARISH

### `mss_confirmed_bullish` (5 falhas)
- 5x: fechamento atual não rompeu swing high recente

### `fvg_in_discount` (2 falhas)
- 2x: FVG está acima do equilibrium (zona premium, não serve pra BUY)

### `cooldown_passed` (10 falhas)
- 2x: último sinal há 5min (cooldown 30min)
- 2x: último sinal há 10min (cooldown 30min)
- 2x: último sinal há 15min (cooldown 30min)

## Near-misses (passaram >=80% dos gates) — 120 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 10:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-21 10:45:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 10:50:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-21 10:55:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-23 10:00:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 10:05:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 10:10:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 10:15:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 10:20:00-04:00 | 8/9 | `london_bias_direction` | London bias is BULLISH, but setup is BEARISH |
| 2026-04-23 10:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:00:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:10:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:15:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:20:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |
| 2026-04-24 10:25:00-04:00 | 7/8 | `fvg_aligned_with_bias` | direção do FVG contraria daily bias |

## Sinais Gerados (2)

| Timestamp | Ação | Entry | SL | TP |
|---|---|---:|---:|---:|
| 2026-05-05 10:15:00-04:00 | SELL | 4586.35 | 4594.35 | 4522.70 |
| 2026-05-08 10:10:00-04:00 | SELL | 4745.25 | 4753.25 | 4702.70 |

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
