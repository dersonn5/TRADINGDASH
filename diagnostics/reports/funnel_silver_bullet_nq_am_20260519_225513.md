# Relatório Funil — Silver Bullet NQ — NY AM

**Período analisado:** 2026-04-20 09:30:00-04:00 → 2026-05-18 15:55:00-04:00
**Candles M5 totais:** 1638
**Candles avaliados (após warmup 50):** 1588
**Sinais gerados:** 0

## Funil de Gates (ordem de avaliação)

| # | Gate | Avaliados | Passaram | Falharam | % Pass |
|---|---|---:|---:|---:|---:|
| 1 | `data_present` | 1588 | 1588 | 0 | 100.0% |
| 2 | `killzone_active` | 1588 | 240 | 1348 | 15.1% |
| 3 | `bias_not_neutral` | 240 | 156 | 84 | 65.0% |
| 4 | `today_has_data` | 156 | 156 | 0 | 100.0% |
| 5 | `london_bias_active` | 156 | 0 | 156 | 0.0% |

## Top 5 Gates que mais mataram sinais

| Rank | Gate | Falhas | % do total |
|---|---|---:|---:|
| 1 | `killzone_active` | 1348 | 84.9% |
| 2 | `london_bias_active` | 156 | 9.8% |
| 3 | `bias_not_neutral` | 84 | 5.3% |

## Motivos de Falha (top 3 por gate)

### `killzone_active` (1348 falhas)
- 1348x: horário fora de 10:00:00-11:00:00

### `bias_not_neutral` (84 falhas)
- 84x: PO3 retornou NEUTRAL (close não em top/bottom 30% do range)

### `london_bias_active` (156 falhas)
- 156x: London did not sweep Asian Range

## Near-misses (passaram >=80% dos gates) — 156 candles

| Timestamp | Gates passados | Gate que matou | Motivo |
|---|---:|---|---|
| 2026-04-22 10:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-22 10:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:30:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:35:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:40:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:45:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:50:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-23 10:55:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:00:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:05:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:10:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:15:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:20:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |
| 2026-04-27 10:25:00-04:00 | 4/5 | `london_bias_active` | London did not sweep Asian Range |

## Sinais Gerados (0)

_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._

## Recomendação de Calibração

**Gate mais letal:** `killzone_active` (1348 falhas)

Próximo passo sugerido:
1. Relaxar/remover gate `killzone_active` temporariamente
2. Re-rodar este diagnóstico
3. Se sample chegar a >=30 sinais, rodar backtest e medir PF
4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente
