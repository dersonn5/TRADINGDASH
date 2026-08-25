"""
Teste de Backtest para a Estratégia 9:30-11:00 AM IFVG Reversal
================================================================
IS 2022-2023 | VAL 2024 | Holdout 2025-2026 (opcional via --holdout)

Uso:
  python -m research.test_930
  python -m research.test_930 --rr 3.0
  python -m research.test_930 --holdout
"""

import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.strat_930_ifvg import Strat930IFVG, Strat930Config

WINDOWS = {
    "IS 22-23": ("2022-01-01", "2023-12-31"),
    "VAL 2024": ("2024-01-01", "2024-12-31")
}


def run(market, start, end, target_rr=2.0):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (
        _slice(c5, start, end),
        _slice(c1h, start, end),
        _slice(c1d, start, end),
        _slice(c1m, start, end)
    )
    cfg = Strat930Config(target_rr=target_rr)
    strat = Strat930IFVG(cfg)
    strat.symbol = m["symbol"]
    
    bc = BacktestConfig(
        initial_balance=10000.0,
        tick_size=m["tick"],
        point_value=1.0,
        commission_usd=0.0,
        commission_pct=0.0002,
        enable_partials=True,
        partial_rr=target_rr,
        partial_pct=0.5,
        enable_break_even=True,
        break_even_trigger_rr=1.5,
        enable_trailing=False
    )
    
    res = BacktestEngine(bc).run(
        strategy=strat,
        candles_5m=s5,
        candles_15m=s5,
        candles_1h=s1h,
        candles_1d=s1d,
        candles_1m=s1m,
        use_filters=False
    )
    metrics = PerformanceMetrics.calculate(res["positions"], 10000.0)
    metrics["funnel"] = dict(strat.funnel)
    return metrics


def _job(args_):
    mk, wname, s, e, rr = args_
    try:
        m = run(mk, s, e, target_rr=rr)
        return (f"  {mk:<5}{wname:<14}RR={rr:<4.1f}trades={m['total_trades']:<5}"
                f"PF={m['profit_factor']:<7.2f}win={m['win_rate']:<6.1f}DD={m['max_drawdown_percent']:.1f}%")
    except Exception as ex:
        return f"  {mk:<5}{wname:<14}ERRO {str(ex)[:60]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rr", type=float, default=2.0, help="Target RR (default: 2.0)")
    ap.add_argument("--holdout", action="store_true", help="Rodar período Holdout (2025-2026)")
    args = ap.parse_args()

    wins = {"HOLDOUT 25-26": ("2025-01-01", "2026-06-29")} if args.holdout else WINDOWS
    print("=" * 75, flush=True)
    print(f"  TESTE ESTRATÉGIA 9:30-11:00 AM IFVG REVERSAL (RR {args.rr}:1) | Engine Honesto", flush=True)
    print("=" * 75, flush=True)

    jobs = [(mk, wname, s, e, args.rr) for mk in ("NQ", "ES", "XAU") for wname, (s, e) in wins.items()]
    
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=6) as ex:
        for line in ex.map(_job, jobs):
            print(line, flush=True)

    print("\n  Régua de corte: IS e VAL >= 1.05 para prosseguir ao Holdout. (Holdout: PF>=1.3, DD<=15%)", flush=True)


if __name__ == "__main__":
    main()
