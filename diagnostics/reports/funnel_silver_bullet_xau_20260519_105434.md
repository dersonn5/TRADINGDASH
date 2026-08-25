# Relatório Funil — Silver Bullet XAU

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5773
**Candles avaliados (após warmup 50):** 5723
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5723 | 5717 | 6 | 99.9% |
| 2 | `killzone_active` | 5717 | 252 | 5465 | 4.4% |
| 3 | `bias_not_neutral` | 252 | 120 | 132 | 47.6% |
| 4 | `today_has_data` | 120 | 120 | 0 | 100.0% |
| 5 | `enough_candles_for_fvg` | 120 | 120 | 0 | 100.0% |
| 6 | `fvg_present_any` | 120 | 17 | 103 | 14.2% |
| 7 | `fvg_aligned_with_bias` | 17 | 12 | 5 | 70.6% |
| 8 | `sweep_present_bearish` | 6 | 0 | 6 | 0.0% |
| 9 | `sweep_present_bullish` | 6 | 0 | 6 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5465 | 95.5% |
| 2 | `bias_not_neutral` | 132 | 2.3% |
| 3 | `fvg_present_any` | 103 | 1.8% |
| 4 | `data_present` | 6 | 0.1% |
| 5 | `sweep_present_bearish` | 6 | 0.1% |

## Motivos de Falha (top 3 por gate)

### `data_present` (6 falhas)
- 6x: dados M5 ou D1 vazios

### `killzone_active` (5465 falhas)
- 5465x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (132 falhas)
- 132x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `fvg_present_any` (103 falhas)
- 103x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (5 falhas)
- 5x: direção do FVG contraria daily bias

### `sweep_present_bearish` (6 falhas)
- 6x: sem sweep do Asian High desde 04:00 EST

### `sweep_present_bullish` (6 falhas)
- 6x: sem sweep do Asian Low desde 04:00 EST

## Near-misses (passaram >=80% dos gates) — 120 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
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
| 2026-04-23 10:00:00-04:00 | 7/8 | `sweep_present_bearish` | sem sweep do Asian High desde 04:00 EST |
| 2026-04-23 10:05:00-04:00 | 7/8 | `sweep_present_bearish` | sem sweep do Asian High desde 04:00 EST |
| 2026-04-23 10:10:00-04:00 | 7/8 | `sweep_present_bearish` | sem sweep do Asian High desde 04:00 EST |
| 2026-04-23 10:15:00-04:00 | 7/8 | `sweep_present_bearish` | sem sweep do Asian High desde 04:00 EST |
| 2026-04-23 10:20:00-04:00 | 7/8 | `sweep_present_bearish` | sem sweep do Asian High desde 04:00 EST |
| 2026-04-23 10:25:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:30:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:35:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:40:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:45:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:50:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:55:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:00:00-04:00 | 7/8 | `sweep_present_bullish` | sem sweep do Asian Low desde 04:00 EST |
| 2026-04-24 10:05:00-04:00 | 5/6 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-24 10:10:00-04:00 | 7/8 | `sweep_present_bullish` | sem sweep do Asian Low desde 04:00 EST |
| 2026-04-24 10:15:00-04:00 | 7/8 | `sweep_present_bullish` | sem sweep do Asian Low desde 04:00 EST |
| 2026-04-24 10:20:00-04:00 | 7/8 | `sweep_present_bullish` | sem sweep do Asian Low desde 04:00 EST |
| 2026-04-24 10:25:00-04:00 | 7/8 | `sweep_present_bullish` | sem sweep do Asian Low desde 04:00 EST |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5465 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
