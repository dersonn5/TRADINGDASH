# ⛔ INVALIDADO — vazamento de look-ahead descoberto (2026-07-02)

## O que aconteceu

Todos os resultados anteriores deste projeto (PF 1.51/1.97 em 2022-24, holdout 1.71/1.85
em 2025-26, sims de eval e de 10 contas) estavam INFLADOS por um vazamento de dado futuro:

- Velas HTF (1h e 1d) rotuladas pela ABERTURA e resampladas sobre a série inteira.
- O corte `searchsorted(current_time, side='right')` incluía a vela EM FORMAÇÃO
  com OHLC completo → o bias diário enxergava o fechamento do dia de manhã.
- Corrigido em `backtesting/engine.py` (corte por vela FECHADA: rótulo + duração <= agora)
  e `executor/run.py`.

## Resultado HONESTO (holdout 2025-01 → 2026-06, engine limpo)

| Mercado | Motor    | trades | PF    | win%  | sumR  | DD%  |
|---------|----------|--------|-------|-------|-------|------|
| NQ      | VALIDADO | 132    | 0.938 | 37.9  | -5.8  | 18.3 |
| NQ      | PO3+SMT  | 57     | 0.980 | 42.1  | -0.7  | 10.2 |
| ES      | VALIDADO | 102    | 0.794 | 36.3  | -14.0 | 21.5 |
| ES      | PO3+SMT  | 52     | 0.966 | 38.5  | -1.1  | 11.1 |
| PORT    | VALIDADO | 234    | 0.878 | 37.2  | -19.8 | 35.3 |
| PORT    | PO3+SMT  | 109    | 0.974 | 40.4  | -1.8  | 11.2 |

VEREDITO: sem o futuro vazado, o sistema atual PERDE dinheiro (PF < 1).
NÃO COMPRAR conta prop com este sistema. Decisão de 2026-07-02.

Nota: PO3+SMT degradou muito menos (0.97 vs 0.88) — os gates (sweep da range
asiática + SMT) têm seletividade real própria, mas insuficiente sem contexto HTF honesto.

## O que sobrevive (ativos reais)

- Engine de backtest AGORA HONESTO (instrumento de medição confiável).
- Executor completo (compliance guard intrabar, broker paper realista, contratos micro).
- Pipeline de dados Dukascopy 2022-2026 (incl. cache holdout separado).
- Ferramentas de research (labs, loops com anti-overfit, sims Monte Carlo).
- Metodologia: 3 janelas + holdout cego + ceticismo do usuário = pegou o bug antes do dinheiro.

## Próximo passo

Re-tunar/redesenhar a estratégia SOBRE O ENGINE LIMPO:
- A mecânica 5m/1m (sweep, MSS, FVG) nunca vazou — o vazamento era só no contexto HTF.
- HTF bias agora precisa funcionar com velas FECHADAS (contexto atrasado ~1h/1d).
- Critério de aprovação: PF > 1.3 no holdout 2025-26 limpo. Sem isso, não há compra.
