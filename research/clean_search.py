"""
BUSCA NO ENGINE LIMPO — reconstruir o edge sem look-ahead
=========================================================
Random search (espaço controlado) nos 2 motores (topdown / PO3-gates), por mercado.
Janelas anti-leak:
  IS   2022-01 → 2023-12  (busca)
  VAL  2024-01 → 2024-12  (seleção)
  HOLDOUT 2025-26         (NUNCA tocado aqui — só o vencedor final, 1 vez, via holdout_2025.py)

Ranqueia por score VAL (PF - DD/100, min 30 trades) exigindo PF>=1.05 nos DOIS lados.
Salva tudo em clean_search_<mkt>.jsonl + top em clean_best_<mkt>.json.

Uso:  python -m research.clean_search --market NQ --samples 20
"""
import os, sys, json, random, argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.ict_po3 import ICTPo3, ICTPo3Config

IS_WIN = ("2022-01-01", "2023-12-31")
VAL_WIN = ("2024-01-01", "2024-12-31")

# Espaço de busca (dimensões que importam; contexto HTF agora é honesto/atrasado)
SPACE = {
    "min_score":        (45.0, 75.0),
    "target_rr":        (2.0, 4.5),
    "min_rr":           (1.5, 2.2),
    "displacement_atr": (0.4, 1.2),
    "pd_tolerance":     (0.05, 0.30),
    "sweep_window_5m":  (4, 12),
    "mss_window_5m":    (3, 8),
    "partial_rr":       (1.5, 2.5),
    "break_even_trigger_rr": (1.5, 3.0),
    "trail_trigger_rr": (3.0, 5.5),
}
STRAT_KEYS = {"min_score", "target_rr", "min_rr", "displacement_atr", "pd_tolerance",
              "sweep_window_5m", "mss_window_5m"}


def sample_cfg(rng):
    ov = {}
    for k, (lo, hi) in SPACE.items():
        v = rng.uniform(lo, hi)
        if isinstance(lo, int):
            v = int(round(v))
        ov[k] = round(v, 3) if isinstance(v, float) else v
    ov["engine"] = rng.choice(["topdown", "po3"])
    return ov


def run_window(ov, market, start, end):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (_slice(c5, start, end), _slice(c1h, start, end),
                         _slice(c1d, start, end), _slice(c1m, start, end))
    s5c = _slice(c5c, start, end) if c5c is not None else None
    kw = dict(m["base"])
    kw.update({k: v for k, v in ov.items() if k in STRAT_KEYS})
    if ov["engine"] == "po3":
        kw["require_po3"] = True
        kw["smt_gate"] = bool(kw.get("require_smt", True))
        strat = ICTPo3(ICTPo3Config(**kw))
    else:
        strat = ICTTopDownCrypto(ICTTopDownConfig(**kw))
    strat.symbol = m["symbol"]; strat.correlated_symbol = m["corr"]
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=ov.get("partial_rr", 2.0), partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=ov.get("break_even_trigger_rr", 2.0),
                        enable_trailing=True, trail_trigger_rr=ov.get("trail_trigger_rr", 4.0),
                        trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False, candles_5m_corr=s5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def score(m):
    if m["total_trades"] < 30:
        return -9.0
    return m["profit_factor"] - m["max_drawdown_percent"] / 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=list(MARKETS.keys()))
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--staged", action="store_true",
                    help="2 estágios: triagem barata em VAL-2024, IS completo só nas top-N")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    mk = args.market
    suff = "_staged" if args.staged else ""
    log = Path(__file__).resolve().parent / f"clean_search_{mk.lower()}{suff}.jsonl"
    best_f = Path(__file__).resolve().parent / f"clean_best_{mk.lower()}.json"

    print("=" * 66, flush=True)
    print(f"  BUSCA LIMPA {mk} — {args.samples} amostras{' (staged)' if args.staged else ''} "
          f"| IS 22-23 / VAL 24 | s/ leak", flush=True)
    print("=" * 66, flush=True)

    best = None
    f = open(log, "w", encoding="utf-8")

    if args.staged:
        # ESTÁGIO 1: triagem barata — só VAL 2024 (1 backtest por amostra)
        screened = []
        for i in range(1, args.samples + 1):
            ov = sample_cfg(rng)
            try:
                val_m = run_window(ov, mk, *VAL_WIN)
            except Exception as e:
                print(f"  [s1 {i:03d}] ERRO {str(e)[:70]}", flush=True); continue
            sc = score(val_m)
            rec = {"i": i, "stage": 1, "ov": ov,
                   "val": {k: round(val_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
            f.write(json.dumps(rec) + "\n"); f.flush()
            if val_m["profit_factor"] >= 1.10 and val_m["total_trades"] >= 30:
                screened.append((sc, ov, rec["val"]))
                print(f"  [s1 {i:03d}] {ov['engine']:<8} VAL PF={val_m['profit_factor']:.2f}"
                      f"({val_m['total_trades']}) DD={val_m['max_drawdown_percent']:.0f}% → candidata", flush=True)
            elif i % 10 == 0:
                print(f"  [s1 {i:03d}] ... triando ({len(screened)} candidatas)", flush=True)
        screened.sort(key=lambda x: -x[0])
        finalists = screened[:args.top]
        print(f"\n  ESTÁGIO 2: {len(finalists)} finalistas → IS 2022-23 completo", flush=True)
        # ESTÁGIO 2: verificação completa nas top-N
        for j, (sc1, ov, valr) in enumerate(finalists, 1):
            try:
                is_m = run_window(ov, mk, *IS_WIN)
            except Exception as e:
                print(f"  [s2 {j:02d}] ERRO {str(e)[:70]}", flush=True); continue
            rec = {"stage": 2, "ov": ov, "val": valr,
                   "is": {k: round(is_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
            f.write(json.dumps(rec) + "\n"); f.flush()
            ok = is_m["profit_factor"] >= 1.05
            sc = min(score(is_m), sc1) if ok else -9.0
            tag = ""
            if ok and (best is None or sc > best["sc"]):
                best = {"sc": sc, "rec": rec}; tag = " ★"
            print(f"  [s2 {j:02d}] {ov['engine']:<8} IS PF={is_m['profit_factor']:.2f}({is_m['total_trades']}) "
                  f"VAL PF={valr['profit_factor']:.2f}{tag}", flush=True)
    else:
        for i in range(1, args.samples + 1):
            ov = sample_cfg(rng)
            try:
                is_m = run_window(ov, mk, *IS_WIN)
                val_m = run_window(ov, mk, *VAL_WIN)
            except Exception as e:
                print(f"  [{i:02d}] ERRO {str(e)[:80]}", flush=True); continue
            rec = {"i": i, "ov": ov,
                   "is": {k: round(is_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")},
                   "val": {k: round(val_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
            f.write(json.dumps(rec) + "\n"); f.flush()
            ok = is_m["profit_factor"] >= 1.05 and val_m["profit_factor"] >= 1.05
            sc = min(score(is_m), score(val_m)) if ok else -9.0
            tag = ""
            if ok and (best is None or sc > best["sc"]):
                best = {"sc": sc, "rec": rec}; tag = " ★"
            print(f"  [{i:02d}] {ov['engine']:<8} IS PF={is_m['profit_factor']:.2f}({is_m['total_trades']}) "
                  f"VAL PF={val_m['profit_factor']:.2f}({val_m['total_trades']}) DD={val_m['max_drawdown_percent']:.0f}%{tag}", flush=True)

    f.close()
    if best:
        best_f.write_text(json.dumps(best["rec"], indent=2), encoding="utf-8")
        print(f"\n  MELHOR {mk}: {best['rec']['ov']}", flush=True)
        print(f"  IS {best['rec'].get('is')} | VAL {best['rec']['val']}", flush=True)
        print(f"  salvo -> {best_f.name}  (holdout 2025-26 SÓ no final, 1x)", flush=True)
    else:
        print(f"\n  NENHUMA config passou (PF>=1.05 nos 2 lados). Edge não achado neste espaço.", flush=True)


if __name__ == "__main__":
    main()
