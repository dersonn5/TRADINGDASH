# Sistema Validado — ICT Top-Down v2 (Cripto)

> Produto atual do projeto. Estratégia mecânica sistemática, validada out-of-sample.
> O filtro LLM ("segundo cérebro") foi **removido do fluxo** — piorou os resultados (ver abaixo).

## Estratégia: `ict_topdown_crypto` (ICTTopDownCrypto)

Modelo ICT top-down em 3 camadas:
1. **Contexto HTF** (`core/htf_context.py`): bias, premium/discount, PD arrays (1h/4h/D), DOL (alvo)
2. **Setup 5m**: sweep de liquidez + MSS (estrutura quebrada)
3. **Confirmation entry 1m**: FVG de 1m, stop curto folgado

Seleção por **EntryQualityScorer** (`core/entry_quality.py`): confluências ponderadas
(HTF, premium/discount, array HTF, liquidez, killzone, MSS claro, SMT, FVG, BPR) → score ≥ 60.

## Gestão de trade (engine `BacktestConfig`)
- Parcial: **50% a 2R** (`enable_partials, partial_rr=2.0, partial_pct=0.5`)
- Break-even: **2R** (`break_even_trigger_rr=2.0`) — não 1R (ruído do 1m tira no zero)
- Trailing: após **4R**, trava 1.5R atrás do pico (`trail_trigger_rr=4.0, trail_distance_rr=1.5`)
- Alvo: intermediário/curto (`target_mode="intermediate", target_rr=3.0, min_rr=1.8`)

## Resultados (2 ativos, BTC + ETH)

### Full 3 anos (2022-2024) — mecânico
| Ativo | Trades | Win% | PF | PnL ($10k) | DD |
|---|---|---|---|---|---|
| BTC | 777 | 40.9% | 1.39 | +$18.011 | 16.8% |
| ETH | 815 | 38.3% | 1.33 | +$16.936 | 13.6% |

### OUT-OF-SAMPLE (treino 2022-23 / teste cego 2024) — ✅ EDGE SEGUROU
| Janela | Trades | Win% | PnL |
|---|---|---|---|
| IN-SAMPLE (2022-23) | 1070 | 40.0% | +$24.706 |
| OUT-SAMPLE (2024) | 500 | 38.4% | +$9.241 |

OOS por ativo: BTC PF 1.35 (DD 9.5%) · ETH PF 1.26 (DD 8.4%).

## Filtro LLM (segundo cérebro) — REMOVIDO do fluxo
Teste RAW vs BRAIN no OOS 2024: o cérebro 7b aprovou ~20% dos trades e **selecionou os piores**
(win 6.8% / 0.0%, PF 0.14 / 0.00). **Anti-preditivo.** Removido da execução.
Código preservado (`core/brain_filter.py`) para revisão futura (modelo forte / regime / feature ML).

## Pendências antes de capital real
- [ ] Walk-forward multi-janela (robustez além de 1 ano OOS)
- [ ] Custo real OKX: incluir funding de perp (hoje só comissão + 1 tick slippage)
- [ ] Forward/paper trade (testnet) 2-3 meses
- [ ] Risco 0.5%/trade + regras de drawdown
- [ ] Portar para NQ/ES/XAU (ICT é nativo lá) — bloqueio: dados 1m de 3 anos (Dukascopy)

---

## Atualização — Agente Pesquisador (research/loop.py)

Agente autônomo: LLM (gpt-5.4-nano) propõe configs → lab testa IS+OOS → guarda anti-overfit.
Achou config mais robusta, **validada cross-asset** (ETH, fora da otimização):

**Config otimizada:** `min_score=58, displacement_atr=0.95, pd_tolerance=0.08`

| | BTC OOS 2024 | ETH OOS 2024 (cross-check) |
|---|---|---|
| Profit Factor | 1.73 | 1.32 |
| Win rate | 44.3% | 38.7% |
| Drawdown | 5.47% | 6.89% |

Honesto: o PF 1.73 do BTC era parte sorte de período (ETH = 1.32 = não replicou).
Ganho real = **drawdown ~metade** do baseline, generaliza. Expectativa: PF ~1.3-1.4, DD 5-7%.
O ativo de verdade aqui é o **motor de pesquisa autônomo** que produz candidatos auto-validados.

### Pendência de rigor
- Agente viu mesmo OOS (BTC 2024) em 6 ciclos → risco de leak ao OOS. Cross-asset (ETH) mitigou mas não elimina.
- Próximo: walk-forward multi-janela antes de confiar 100%.
