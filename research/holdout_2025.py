"""
HOLDOUT CEGO 2025-2026 — o teste final antes de pagar a conta
==============================================================
Baixa dado que o sistema NUNCA viu (jan/2025 → jun/2026) num cache SEPARADO
(data/cached_holdout/ — NÃO toca no validado 2022-24). Roda os 2 motores
(VALIDADO + PO3+SMT) nesse período virgem, com a config do portfólio.

Se o edge segurar aqui = confiança real p/ comprar. Se afundar = economizou a conta.
Zero tuning, zero seleção — dado 100% out-of-sample no tempo.

Uso:
  python -m research.holdout_2025 --fetch     # baixa (lento, 1x)
  python -m research.holdout_2025             # valida (usa cache holdout)
"""
import os, sys, argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import pandas as pd
import dukascopy_python as dk
from dukascopy_python.instruments import (
    INSTRUMENT_IDX_AMERICA_E_SANDP_500, INSTRUMENT_IDX_AMERICA_E_NQ_100)

HCACHE = Path(__file__).resolve().parents[1] / "data" / "cached_holdout"
HCACHE.mkdir(parents=True, exist_ok=True)
START, END = "2025-01-01", "2026-06-29"
INSTR = {"NAS/USD": INSTRUMENT_IDX_AMERICA_E_NQ_100, "SPX/USD": INSTRUMENT_IDX_AMERICA_E_SANDP_500}
IV = {"1m": dk.INTERVAL_MIN_1, "5m": dk.INTERVAL_MIN_5, "1d": dk.INTERVAL_DAY_1}
BASE = dict(target_rr=3.2, min_rr=1.8, min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)
MARKETS = [("NQ", "NAS/USD", "SPX/USD", True, 63, 0.25), ("ES", "SPX/USD", "NAS/USD", True, 63, 0.25)]


def _path(sym, tf):
    return HCACHE / f"{sym.replace('/','_')}_{tf}.parquet"


def fetch():
    for sym, instr in INSTR.items():
        for tf, iv in IV.items():
            p = _path(sym, tf)
            if p.exists():
                print(f"  [skip] {sym} {tf} já existe"); continue
            print(f"  baixando {sym} {tf}...", flush=True)
            df = dk.fetch(instr, iv, dk.OFFER_SIDE_BID, pd.to_datetime(START), pd.to_datetime(END))
            df = df[["open", "high", "low", "close", "volume"]].copy()
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            df.to_parquet(p)
            print(f"    {len(df)} velas ({df.index.min()} .. {df.index.max()})", flush=True)


def _load(sym):
    c5 = pd.read_parquet(_path(sym, "5m"))
    c1d = pd.read_parquet(_path(sym, "1d"))
    c1m = pd.read_parquet(_path(sym, "1m"))
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"}).dropna()
    return c5, c1h, c1d, c1m


def trades_for(strat, sym, corr, tick):
    from backtesting.engine import BacktestEngine, BacktestConfig
    c5, c1h, c1d, c1m = _load(sym)
    c5c = _load(corr)[0] if corr else None
    strat.symbol = sym; strat.correlated_symbol = corr or ""
    bc = BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    return [{"exit": p.exit_time or p.entry_time, "r": p.pnl_usd / 100.0} for p in res["positions"]]


def stats(rs):
    rs = [max(-1.2, min(15.0, r)) for r in rs]
    if not rs: return (0, 0.0, 0.0, 0.0, 0.0)
    gp = sum(x for x in rs if x > 0); gl = -sum(x for x in rs if x < 0)
    pf = gp / gl if gl > 0 else 999.0
    wr = sum(1 for x in rs if x > 0) / len(rs) * 100
    bal = 2000.0; peak = 2000.0; dd = 0.0
    for r in rs:
        bal += r * 20.0; peak = max(peak, bal); dd = max(dd, (peak - bal) / peak * 100)
    return (len(rs), round(pf, 3), round(wr, 1), round(sum(rs), 1), round(dd, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()
    print("=" * 68)
    print("  HOLDOUT CEGO 2025-2026 (jan/25 → jun/26) — dado NUNCA visto")
    print("=" * 68)
    if args.fetch:
        fetch(); print("\n  fetch OK. Rode sem --fetch p/ validar.\n"); return
    if not _path("NAS/USD", "5m").exists():
        print("  [erro] rode --fetch primeiro."); return

    from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
    from strategies.ict_po3 import ICTPo3, ICTPo3Config
    print(f"  {'mercado':<7}{'motor':<12}{'trades':>7}{'PF':>7}{'win%':>7}{'sumR':>8}{'DD%':>7}")
    print("  " + "-" * 58)
    agg = {"VALID": [], "PO3": []}
    for name, sym, corr, smt, ms, tick in MARKETS:
        vcfg = dict(BASE); vcfg["min_score"] = ms; vcfg["require_smt"] = smt
        vtr = trades_for(ICTTopDownCrypto(ICTTopDownConfig(**vcfg)), sym, corr, tick)
        pcfg = dict(vcfg); pcfg["require_po3"] = True; pcfg["smt_gate"] = bool(smt)
        ptr = trades_for(ICTPo3(ICTPo3Config(**pcfg)), sym, corr, tick)
        agg["VALID"] += vtr; agg["PO3"] += ptr
        for lbl, tr in (("VALIDADO", vtr), ("PO3+SMT", ptr)):
            n, pf, wr, sr, dd = stats([t["r"] for t in tr])
            print(f"  {name:<7}{lbl:<12}{n:>7}{pf:>7}{wr:>7}{sr:>8}{dd:>7}")
    print("  " + "-" * 58)
    for lbl, key in (("VALIDADO", "VALID"), ("PO3+SMT", "PO3")):
        n, pf, wr, sr, dd = stats([t["r"] for t in agg[key]])
        print(f"  {'PORT':<7}{lbl:<12}{n:>7}{pf:>7}{wr:>7}{sr:>8}{dd:>7}")
    print("\n  Se PF>1.3 e DD baixo aqui = edge segurou em 18 meses cegos. Verdade, não fé.")


if __name__ == "__main__":
    main()
