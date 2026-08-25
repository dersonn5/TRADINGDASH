"""
Head-to-head: VALIDADA (ict_topdown) vs PO3+SMT (ict_po3) — mesma config, mesmo dado
====================================================================================
NÃO toca em nada validado. Roda as DUAS estratégias com a config EXATA do portfólio
(BASE target_rr=3.2, min_score por mercado, SMT por mercado) nos 3 mercados.
Compara PF / win / trades / sumR na janela CHEIA (2022-24) e no OOS 2024 sozinho.

PO3 não tem busca de params (regra fixa: gate manip-Ásia + SMT) -> sem risco de
overfit-por-seleção. Se PO3 bate a validada em PF mantendo trades suficientes -> candidata.

Uso:  python -m research.compare_po3
"""
import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.ict_po3 import ICTPo3, ICTPo3Config

BASE = dict(target_rr=3.2, min_rr=1.8, min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)
MARKETS = [
    ("NQ",  "NAS/USD", "SPX/USD", True, 63, 0.25),
    ("ES",  "SPX/USD", "NAS/USD", True, 63, 0.25),
    ("XAU", "XAU/USD", None,      False, 55, 0.01),
]
FULL = ("2022-01-01", "2024-12-31")
_C = {}


def _load(sym):
    if sym in _C:
        return _C[sym]
    ld = DataLoader()
    c5 = ld.load_data(sym, "5m", *FULL)
    c1d = ld.load_data(sym, "1d", *FULL)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(sym, "1m", *FULL)
    _C[sym] = (c5, c1h, c1d, c1m)
    return _C[sym]


def _engine():
    return BacktestConfig(initial_balance=10000.0, tick_size=0.25, point_value=1.0,
                          commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                          enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                          enable_break_even=True, break_even_trigger_rr=2.0,
                          enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)


def trades_for(strat, sym, corr, tick):
    c5, c1h, c1d, c1m = _load(sym)
    c5c = _load(corr)[0] if corr else None
    strat.symbol = sym
    strat.correlated_symbol = corr or ""
    bc = _engine(); bc.tick_size = tick
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    out = []
    for p in res["positions"]:
        et = p.exit_time or p.entry_time
        risk = getattr(p, "risk_usd", 0.0) or 0.0
        r = (p.pnl_usd / risk) if risk > 0 else (p.pnl_usd / 100.0)   # R correto = pnl/risco real
        out.append({"exit": et, "r": r})
    return out


def stats(trades, year=None):
    rs = [t["r"] for t in trades
          if year is None or (hasattr(t["exit"], "year") and t["exit"].year == year)]
    if not rs:
        return (0, 0.0, 0.0, 0.0)
    gp = sum(x for x in rs if x > 0); gl = -sum(x for x in rs if x < 0)
    pf = gp / gl if gl > 0 else 999.0
    wr = sum(1 for x in rs if x > 0) / len(rs) * 100
    return (len(rs), round(pf, 3), round(wr, 1), round(sum(rs), 1))


def dd_equity(trades, year=None, balance=2000.0, risk_frac=0.01):
    """Equity com risco FIXO por trade (realista prop). Retorna (maxDD%, retorno%)."""
    tr = sorted([t for t in trades
                 if year is None or (hasattr(t["exit"], "year") and t["exit"].year == year)],
                key=lambda x: x["exit"])
    if not tr:
        return (0.0, 0.0)
    bal = balance; peak = balance; maxdd = 0.0
    fixed = balance * risk_frac
    for t in tr:
        r = max(-1.2, min(15.0, t["r"]))         # cap outliers (igual portfolio.py)
        bal += r * fixed
        peak = max(peak, bal)
        maxdd = max(maxdd, (peak - bal) / peak * 100)
    return (round(maxdd, 1), round((bal / balance - 1) * 100, 1))


def main():
    print("=" * 74)
    print("  HEAD-TO-HEAD — VALIDADA (top-down) vs PO3+SMT (gate manip-Ásia + SMT)")
    print("  mesma config do portfólio (target_rr=3.2, min_score/SMT por mercado)")
    print("=" * 74)
    header = f"  {'mercado':<7}{'estratégia':<12}{'janela':<9}{'trades':>7}{'PF':>7}{'win%':>7}{'sumR':>8}"
    print(header); print("  " + "-" * 66)
    agg = {"VALID": [], "PO3": []}
    agg_clean = {"VALID": [], "PO3": []}   # só NQ+ES (r confiável; XAU tem bug de escala)
    for name, sym, corr, smt, ms, tick in MARKETS:
        vcfg = dict(BASE); vcfg["min_score"] = ms; vcfg["require_smt"] = smt
        vtr = trades_for(ICTTopDownCrypto(ICTTopDownConfig(**vcfg)), sym, corr, tick)

        pcfg = dict(BASE); pcfg["min_score"] = ms; pcfg["require_smt"] = smt
        pcfg["require_po3"] = True; pcfg["smt_gate"] = bool(smt)   # XAU sem par -> SMT off
        ptr = trades_for(ICTPo3(ICTPo3Config(**pcfg)), sym, corr, tick)
        agg["VALID"] += vtr; agg["PO3"] += ptr
        if name in ("NQ", "ES"):
            agg_clean["VALID"] += vtr; agg_clean["PO3"] += ptr

        for label, tr in (("VALIDADA", vtr), ("PO3+SMT", ptr)):
            n, pf, wr, sr = stats(tr)
            n24, pf24, wr24, sr24 = stats(tr, 2024)
            print(f"  {name:<7}{label:<12}{'2022-24':<9}{n:>7}{pf:>7}{wr:>7}{sr:>8}")
            print(f"  {'':<7}{'':<12}{'2024 OOS':<9}{n24:>7}{pf24:>7}{wr24:>7}{sr24:>8}")
        print("  " + "-" * 66)

    def show(title, a):
        print(f"\n  === {title} — R=pnl/100 + DD (equity risco fixo 1%) ===")
        for label, key in (("VALIDADA", "VALID"), ("PO3+SMT", "PO3")):
            n, pf, wr, sr = stats(a[key]); dd, ret = dd_equity(a[key])
            n24, pf24, wr24, sr24 = stats(a[key], 2024); dd24, ret24 = dd_equity(a[key], 2024)
            print(f"  {label:<10} 2022-24 : n={n:<5} PF={pf:<6} win={wr}% sumR={sr:<7} maxDD={dd}% ret={ret}%")
            print(f"  {'':<10} 2024 OOS: n={n24:<5} PF={pf24:<6} win={wr24}% sumR={sr24:<7} maxDD={dd24}% ret={ret24}%")

    show("PORTFÓLIO NQ+ES (r CONFIÁVEL — decisão)", agg_clean)
    show("PORTFÓLIO NQ+ES+XAU (XAU tem bug de escala r — só referência)", agg)
    print("\n  Leitura: PO3 vale se PF↑ E DD↓ (risco-ajustado). Decisão pelo NQ+ES limpo.")


if __name__ == "__main__":
    main()
