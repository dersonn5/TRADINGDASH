# Relatório Funil — Silver Bullet NQ — NY AM

**Período analisado:** 2026-04-19 18:10:00-04:00 → 2026-05-18 23:55:00-04:00
**Candles M5 totais:** 5722
**Candles avaliados (após warmup 50):** 5672
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 5672 | 5652 | 20 | 99.6% |
| 2 | `killzone_active` | 5652 | 252 | 5400 | 4.5% |
| 3 | `bias_not_neutral` | 252 | 168 | 84 | 66.7% |
| 4 | `today_has_data` | 168 | 168 | 0 | 100.0% |
| 5 | `london_bias_active` | 168 | 132 | 36 | 78.6% |
| 6 | `enough_candles_for_fvg` | 132 | 132 | 0 | 100.0% |
| 7 | `fvg_present_any` | 132 | 20 | 112 | 15.2% |
| 8 | `fvg_aligned_with_bias` | 20 | 9 | 11 | 45.0% |
| 9 | `london_bias_direction` | 9 | 5 | 4 | 55.6% |
| 10 | `sweep_present_bearish` | 5 | 5 | 0 | 100.0% |
| 11 | `mss_confirmed_bearish` | 5 | 1 | 4 | 20.0% |
| 12 | `fvg_in_premium` | 1 | 0 | 1 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 5400 | 95.2% |
| 2 | `fvg_present_any` | 112 | 2.0% |
| 3 | `bias_not_neutral` | 84 | 1.5% |
| 4 | `london_bias_active` | 36 | 0.6% |
| 5 | `data_present` | 20 | 0.4% |

## Motivos de Falha (top 3 por gate)

### `data_present` (20 falhas)
- 20x: dados M5 ou D1 vazios

### `killzone_active` (5400 falhas)
- 5400x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (84 falhas)
- 84x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (36 falhas)
- 36x: London did not sweep Asian Range

### `fvg_present_any` (112 falhas)
- 112x: nenhum FVG ativo nos últimos 6 candles M5

### `fvg_aligned_with_bias` (11 falhas)
- 11x: direção do FVG contraria daily bias

### `london_bias_direction` (4 falhas)
- 4x: London bias is BEARISH, but setup is BULLISH

### `mss_confirmed_bearish` (4 falhas)
- 4x: fechamento atual não rompeu swing low recente

### `fvg_in_premium` (1 falhas)
- 1x: FVG está abaixo do equilibrium (zona discount, não serve pra SELL)

## Near-misses (passaram >=80% dos gates) — 168 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-21 10:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-21 10:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:00:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:05:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:10:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:15:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:20:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:25:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:30:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:35:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:40:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:45:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:50:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-22 10:55:00-04:00 | 6/7 | `fvg_present_any` | nenhum FVG ativo nos últimos 6 candles M5 |
| 2026-04-23 10:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (5400 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
