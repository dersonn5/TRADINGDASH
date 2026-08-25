"""
Busca PO3 v2 (judas open-anchored) — staged, engine limpo
=========================================================
Família nova (referências em tempo real: midnight open, PDH/PDL, Ásia).
Triagem VAL 2024 → finalistas verificam IS 2022-23. Holdout 25-26 trancado.

Uso:  python -m research.search_po3v2 --market NQ --samples 100
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
from strategies.ict_po3_v2 import ICTPo3V2, ICTPo3V2Config

IS_WIN = ("2022-01-01", "2023-12-31")
VAL_WIN = ("2024-01-01", "2024-12-31")

SPACE = {
    "target_rr":        (2.0, 5.0),
    "min_rr":           (1.2, 2.2),
    "displacement_atr": (0.3, 1.2),
    "sweep_window_5m":  (4, 16),
    "mss_window_5m":    (3, 8),
    "reclaim_buffer_atr": (0.0, 0.5),
    "partial_rr":       (1.5, 2.5),
    "break_even_trigger_rr": (1.5, 3.0),
    "trail_trigger_rr": (3.0, 5.5),
}
STRAT_KEYS = {"target_rr", "min_rr", "displacement_atr", "sweep_window_5m",
              "mss_window_5m", "reclaim_buffer_atr"}


def sample_cfg(rng):
    ov = {}
    for k, (lo, hi) in SPACE.items():
        v = rng.uniform(lo, hi)
        if isinstance(lo, int):
            v = int(round(v))
        ov[k] = round(v, 3) if isinstance(v, float) else v
    ov["judas_ref"] = rng.choice(["asia", "pd", "both"])
    ov["require_open_side"] = rng.choice([True, False])
    ov["target_mode"] = rng.choice(["liquidity", "rr"])
    ov["smt_gate"] = rng.choice([True, False])
    # condução: trailing fixo em R vs ESTRUTURAL (segue swings 5m — deixa runner correr)
    ov["trail_mode"] = rng.choice(["rr", "structure"])
    if ov["trail_mode"] == "structure":
        ov["trail_trigger_rr"] = round(rng.uniform(1.5, 4.0), 2)  # estrutural pode começar cedo (pós-BE)
        ov["trail_swing_bars"] = rng.choice([3, 4, 5])
        ov["trail_struct_buffer_atr"] = round(rng.uniform(0.1, 0.5), 2)
    # backlog HSM: entrada de precisão (CE 50% do FVG), FVG seguinte (Turtle Soup),
    # gestão por projeção da perna de manipulação (stdev)
    ov["entry_precision"] = rng.choice(["edge", "ce"])
    ov["entry_fvg"] = rng.choice(["first", "next"])
    ov["mgmt_mode"] = rng.choice(["rr", "stdev"])
    # CISD já implementado (aula HSM): confirmação alternativa ao MSS
    ov["confirm_type"] = rng.choice(["mss", "cisd", "either"])
    # Novas melhorias adicionadas à busca:
    ov["require_two_phases"] = rng.choice([True, False])
    ov["index_930_mode"] = True
    ov["ob_largo_mode"] = rng.choice([True, False])
    return ov


def run_window(ov, market, start, end):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (_slice(c5, start, end), _slice(c1h, start, end),
                         _slice(c1d, start, end), _slice(c1m, start, end))
    s5c = _slice(c5c, start, end) if c5c is not None else None
    kw = dict(m["base"])
    kw.pop("require_smt", None)
    kw.update({k: v for k, v in ov.items() if k in STRAT_KEYS})
    kw["judas_ref"] = ov["judas_ref"]; kw["require_open_side"] = ov["require_open_side"]
    kw["target_mode"] = ov["target_mode"]; kw["smt_gate"] = ov["smt_gate"] and (m["corr"] is not None)
    kw["entry_precision"] = ov.get("entry_precision", "edge")
    kw["entry_fvg"] = ov.get("entry_fvg", "first")
    kw["mgmt_mode"] = ov.get("mgmt_mode", "rr")
    kw["confirm_type"] = ov.get("confirm_type", "mss")
    kw["require_two_phases"] = ov.get("require_two_phases", True)
    kw["index_930_mode"] = True
    kw["ob_largo_mode"] = ov.get("ob_largo_mode", True)
    strat = ICTPo3V2(ICTPo3V2Config(**kw))
    strat.symbol = m["symbol"]; strat.correlated_symbol = m["corr"]
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=ov.get("partial_rr", 2.0), partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=ov.get("break_even_trigger_rr", 2.0),
                        enable_trailing=True, trail_trigger_rr=ov.get("trail_trigger_rr", 4.0),
                        trail_distance_rr=1.5,
                        trail_mode=ov.get("trail_mode", "rr"),
                        trail_swing_bars=ov.get("trail_swing_bars", 3),
                        trail_struct_buffer_atr=ov.get("trail_struct_buffer_atr", 0.25))
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False, candles_5m_corr=s5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def score(m):
    if m["total_trades"] < 25:
        return -9.0
    return m["profit_factor"] - m["max_drawdown_percent"] / 100.0


def run_one_sample(args):
    idx, ov, mk = args
    try:
        val_m = run_window(ov, mk, *VAL_WIN)
        return idx, ov, val_m, None
    except Exception as e:
        import traceback
        return idx, ov, None, f"{str(e)[:70]} - {traceback.format_exc()[:100]}"


def run_one_finalist(args):
    idx, ov, valr, mk = args
    try:
        is_m = run_window(ov, mk, *IS_WIN)
        return idx, ov, valr, is_m, None
    except Exception as e:
        return idx, ov, valr, None, str(e)[:70]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=list(MARKETS.keys()))
    ap.add_argument("--samples", type=int, default=100)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--tag", default="", help="sufixo p/ não colidir com outra busca em paralelo")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    mk = args.market
    tag = f"_{args.tag}" if args.tag else ""
    log = Path(__file__).resolve().parent / f"po3v2_search_{mk.lower()}{tag}.jsonl"
    best_f = Path(__file__).resolve().parent / f"po3v2_best_{mk.lower()}{tag}.json"

    print("=" * 66, flush=True)
    print(f"  BUSCA PO3v2 {mk} — {args.samples} staged | IS 22-23 / VAL 24 | s/ leak", flush=True)
    print("=" * 66, flush=True)

    # Generate all overrides in advance
    tasks = []
    for idx in range(1, args.samples + 1):
        ov = sample_cfg(rng)
        tasks.append((idx, ov, mk))

    screened = []
    f = open(log, "w", encoding="utf-8")

    from concurrent.futures import ProcessPoolExecutor, as_completed
    print(f"  Iniciando Stage 1 com ProcessPoolExecutor (max_workers=10)...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(run_one_sample, t): t for t in tasks}
        completed_count = 0
        for fut in as_completed(futures):
            idx, ov, val_m, err = fut.result()
            completed_count += 1
            if err is not None:
                print(f"  [s1 {idx:03d}/{args.samples:03d}] ERRO {err}", flush=True)
                continue

            rec = {"i": idx, "stage": 1, "ov": ov,
                   "val": {k: round(val_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
            f.write(json.dumps(rec) + "\n")
            f.flush()

            if val_m["profit_factor"] >= 1.10 and val_m["total_trades"] >= 25:
                screened.append((score(val_m), ov, rec["val"]))
                print(f"  [s1 {idx:03d}/{args.samples:03d}] VAL PF={val_m['profit_factor']:.2f}({val_m['total_trades']}) "
                      f"DD={val_m['max_drawdown_percent']:.0f}% {ov['judas_ref']}/{ov['target_mode']}"
                      f"{'/smt' if ov['smt_gate'] else ''} → candidata", flush=True)
            elif completed_count % 10 == 0:
                print(f"  [s1 {completed_count:03d}/{args.samples:03d}] ... ({len(screened)} candidatas)", flush=True)

    screened.sort(key=lambda x: -x[0])
    finalists = screened[:args.top]
    print(f"\n  ESTÁGIO 2: {len(finalists)} finalistas → IS 2022-23 (em paralelo)", flush=True)

    best = None
    if finalists:
        finalist_tasks = [(j, ov, valr, mk) for j, (sc1, ov, valr) in enumerate(finalists, 1)]
        with ProcessPoolExecutor(max_workers=min(len(finalist_tasks), 10)) as executor:
            futures = {executor.submit(run_one_finalist, t): t for t in finalist_tasks}
            for fut in as_completed(futures):
                j, ov, valr, is_m, err = fut.result()
                if err is not None:
                    print(f"  [s2 {j:02d}] ERRO {err}", flush=True)
                    continue

                rec = {"stage": 2, "ov": ov, "val": valr,
                       "is": {k: round(is_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
                f.write(json.dumps(rec) + "\n")
                f.flush()

                ok = is_m["profit_factor"] >= 1.05
                sc1 = score({"total_trades": valr["total_trades"], "profit_factor": valr["profit_factor"], "max_drawdown_percent": valr["max_drawdown_percent"]})
                sc = min(score(is_m), sc1) if ok else -9.0
                tag = ""
                if ok and (best is None or sc > best["sc"]):
                    best = {"sc": sc, "rec": rec}
                    tag = " ★"

                print(f"  [s2 {j:02d}] IS PF={is_m['profit_factor']:.2f}({is_m['total_trades']}) "
                      f"VAL PF={valr['profit_factor']:.2f}{tag}", flush=True)

    f.close()

    if best:
        best_f.write_text(json.dumps(best["rec"], indent=2), encoding="utf-8")
        print(f"\n  MELHOR {mk}: {best['rec']['ov']}", flush=True)
        print(f"  IS {best['rec']['is']} | VAL {best['rec']['val']}", flush=True)
        print(f"  salvo -> {best_f.name} (holdout 25-26 SÓ no final)", flush=True)
    else:
        print(f"\n  NENHUMA config PO3v2 passou. Família também sem edge neste espaço.", flush=True)


if __name__ == "__main__":
    main()
