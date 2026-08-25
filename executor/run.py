"""
Executor — replay/forward test (paper) do pipeline completo
===========================================================
Prova o executor end-to-end SEM dinheiro: puxa dados reais, replay vela 5m a vela,
roda o motor numa conta com compliance + broker paper. Mostra eventos (fill/partial/
exit), status do compliance (equity/pico/floor) e o veredito (PASS/BLOWN).

É o MOLDE do live: trocar o feed (replay->tempo real) e o broker (paper->NinjaTrader)
e é a mesma máquina. Roda local agora; VPS depois.

Uso:
  python -m executor.run --engine validado --symbol NAS/USD --days 45 --risk 200 --phase eval
  python -m executor.run --engine po3 --symbol SPX/USD --days 90 --risk 150 --phase funded
"""
import os, sys, argparse
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import pandas as pd
from data.data_loader import DataLoader
from executor.account import AccountRunner, AccountConfig
from executor.broker import MgmtParams
from executor.compliance import FirmRules

BASE = dict(target_rr=3.2, min_rr=1.8, min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)
CORR = {"NAS/USD": "SPX/USD", "SPX/USD": "NAS/USD", "XAU/USD": None}

# Contrato REAL Bulenox/CME (MICROS — risco $150-300/trade pede granularidade fina;
# emini exigiria $20-50/ponto = poucos contratos inteiros, sizing grosseiro demais).
#   MNQ (Micro Nasdaq): $2.00/ponto, tick 0.25 = $0.50/tick
#   MES (Micro S&P):    $5.00/ponto, tick 0.25 = $1.25/tick
#   MGC (Micro Gold):   $10.00/ponto, tick 0.10 = $1.00/tick
CONTRACT = {
    "NAS/USD": {"name": "MNQ", "point_value": 2.0, "tick_size": 0.25},
    "SPX/USD": {"name": "MES", "point_value": 5.0, "tick_size": 0.25},
    "XAU/USD": {"name": "MGC", "point_value": 10.0, "tick_size": 0.10},
}
PV = {k: v["point_value"] for k, v in CONTRACT.items()}


def build_strategy(engine, symbol):
    smt = CORR.get(symbol) is not None
    ms = 55 if symbol == "XAU/USD" else 63
    cfg = dict(BASE); cfg["min_score"] = ms; cfg["require_smt"] = smt
    if engine == "po3":
        from strategies.ict_po3 import ICTPo3, ICTPo3Config
        cfg["require_po3"] = True; cfg["smt_gate"] = smt
        s = ICTPo3(ICTPo3Config(**cfg))
    else:
        from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
        s = ICTTopDownCrypto(ICTTopDownConfig(**cfg))
    s.symbol = symbol
    s.correlated_symbol = CORR.get(symbol) or ""
    return s


def load(symbol, start, end):
    ld = DataLoader()
    c5 = ld.load_data(symbol, "5m", start, end)
    c1d = ld.load_data(symbol, "1d", start, end)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(symbol, "1m", start, end)
    corr = CORR.get(symbol)
    c5c = ld.load_data(corr, "5m", start, end) if corr else None
    return c5, c1h, c1d, c1m, c5c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="validado", choices=["validado", "po3"])
    ap.add_argument("--symbol", default="NAS/USD")
    ap.add_argument("--days", type=int, default=45)
    ap.add_argument("--risk", type=float, default=200.0)
    ap.add_argument("--phase", default="eval", choices=["eval", "funded"])
    ap.add_argument("--start", default="2024-10-01")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    start = pd.to_datetime(args.start)
    end = (start + pd.Timedelta(days=args.days)).strftime("%Y-%m-%d")
    start_s = start.strftime("%Y-%m-%d")
    print("=" * 66)
    print(f"  EXECUTOR (paper) — {args.engine.upper()} {args.symbol} | {args.phase} | risco ${args.risk:.0f}")
    print(f"  replay {start_s} → {end} ({args.days}d)")
    print("=" * 66)

    c5, c1h, c1d, c1m, c5c = load(args.symbol, start_s, end)
    if c5 is None or c5.empty:
        print("  [erro] sem dados 5m."); return

    strat = build_strategy(args.engine, args.symbol)
    mgmt = MgmtParams(partial_rr=2.0, partial_pct=0.5, be_trigger_rr=2.0,
                      trail_trigger_rr=4.0, trail_distance_rr=1.5)
    rules = FirmRules()
    contract = CONTRACT.get(args.symbol, {"name": args.symbol, "point_value": 1.0, "tick_size": 0.25})
    acfg = AccountConfig(name=f"{args.engine}-{args.symbol}", symbol=args.symbol,
                         point_value=contract["point_value"], risk_usd=args.risk, phase=args.phase,
                         corr_symbol=CORR.get(args.symbol), tick_size=contract["tick_size"])
    print(f"  contrato: {contract['name']} (${contract['point_value']:.2f}/ponto, tick {contract['tick_size']})")

    counts = {"fill": 0, "partial": 0, "exit": 0, "error": 0, "skip": 0}

    def on_event(name, e):
        t = e.get("type")
        if t in counts:
            counts[t] += 1
        if args.verbose and t in ("fill", "exit", "error"):
            print(f"    [{name}] {t}: {({k: v for k, v in e.items() if k != 'type'})}")
        if t == "error":
            print(f"    [{name}] ERROR: {e.get('msg')}")

    runner = AccountRunner(acfg, strat, mgmt=mgmt, rules=rules, on_event=on_event)

    # replay: itera velas 5m; feeds = tudo até o ts atual
    idx5 = c5.index
    idx1m = c1m.index if c1m is not None else None
    idx1h = c1h.index; idx1d = c1d.index
    idx5c = c5c.index if c5c is not None else None
    last_pct = -1
    n = len(idx5)
    for i in range(300, n):    # começa com histórico p/ HTF
        ts = idx5[i]
        row = c5.iloc[i]
        feeds = {
            "5m": c5.iloc[:i + 1],
            # HTF só vela FECHADA (rótulo=abertura): senão a vela em formação vaza futuro
            "1h": c1h.loc[:ts - pd.Timedelta(hours=1)],
            "1d": c1d.loc[:ts - pd.Timedelta(days=1)],
            "1m": c1m.loc[:ts] if c1m is not None else None,
            "5m_corr": c5c.loc[:ts] if c5c is not None else None,
        }
        now = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
        runner.on_bar((row["open"], row["high"], row["low"], row["close"]), now, feeds)
        if runner.guard.blown:
            print(f"  💀 QUEBROU em {ts}"); break
        if runner.guard.passed and args.phase == "eval":
            print(f"  ✅ EVAL APROVADA em {ts}"); break
        pct = int((i - 300) / (n - 300) * 100)
        if pct >= last_pct + 20:
            last_pct = pct
            s = runner.summary(row["close"])
            print(f"  [{pct:>3}%] {ts.date()} equity=${s['equity']:.0f} floor=${s['floor']:.0f} "
                  f"pnl=${s['pnl']:+.0f} trades={s['trades']}")

    last_close = float(c5.iloc[-1]["close"])
    s = runner.summary(last_close)
    print("\n  " + "-" * 60)
    print(f"  RESULTADO: {s['name']} [{s['phase']}]")
    print(f"  equity ${s['equity']:.0f} | pnl ${s['pnl']:+.0f} | trades {s['trades']} "
          f"| pico ${s['peak']:.0f} floor ${s['floor']:.0f}")
    print(f"  fills={counts['fill']} exits={counts['exit']} partials={counts['partial']} "
          f"skips={counts['skip']} err={counts['error']}")
    print(f"  {'✅ PASSOU' if s['passed'] else ''}{'💀 QUEBROU' if s['blown'] else ''}"
          f"{'  (segue operando)' if not (s['passed'] or s['blown']) else ''}")
    print("\n  (Paper/replay. Live = trocar feed p/ tempo real + broker p/ NinjaTrader.)")


if __name__ == "__main__":
    main()
