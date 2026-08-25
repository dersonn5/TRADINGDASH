# Relatório Funil — Silver Bullet NQ — NY Lunch

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 244 | 1344 | 15.4% |
| 3 | `bias_not_neutral` | 244 | 156 | 88 | 63.9% |
| 4 | `today_has_data` | 156 | 156 | 0 | 100.0% |
| 5 | `london_bias_active` | 156 | 0 | 156 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1344 | 84.6% |
| 2 | `london_bias_active` | 156 | 9.8% |
| 3 | `bias_not_neutral` | 88 | 5.5% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1344 falhas)
- 1344x: horário fora de 13:00:00-14:00:00

### `bias_not_neutral` (88 falhas)
- 88x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (156 falhas)
- 156x: London did not sweep Asian Range

## Near-misses (passaram >=80% dos gates) — 156 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-22 13:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 13:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 13:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 13:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1344 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
