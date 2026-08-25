"""
Teste do Playbook Anderson #1 — hipótese FIXA, sem busca de parâmetros
=======================================================================
IS 2022-23 + VAL 2024, 4 mercados. Holdout 2025-26 SÓ se IS+VAL passarem (rodar
com --holdout depois, 1x). Régua travada: PF>=1.3 e DD<=15% no holdout.

Uso:  python -m research.test_playbook           (IS+VAL)
      python -m research.test_playbook --holdout (só o vencedor, 1x)
"""
import os, sys, argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.playbook_anderson import PlaybookAnderson, PlaybookAndersonConfig

WINDOWS = {"IS 22-23": ("2022-01-01", "2023-12-31"), "VAL 2024": ("2024-01-01", "2024-12-31")}


def run(market, start, end):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (_slice(c5, start, end), _slice(c1h, start, end),
                         _slice(c1d, start, end), _slice(c1m, start, end))
    strat = PlaybookAnderson(PlaybookAndersonConfig())
    strat.symbol = m["symbol"]
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=3.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def _job(args_):
    mk, wname, s, e = args_
    try:
        m = run(mk, s, e)
        return (f"  {mk:<5}{wname:<14}trades={m['total_trades']:<5}PF={m['profit_factor']:<7.2f}"
                f"win={m['win_rate']:<6.1f}DD={m['max_drawdown_percent']:.1f}%")
    except Exception as ex:
        return f"  {mk:<5}{wname:<14}ERRO {str(ex)[:60]}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--holdout", action="store_true")
    args = ap.parse_args()
    wins = {"HOLDOUT 25-26": ("2025-01-01", "2026-06-29")} if args.holdout else WINDOWS
    print("=" * 70, flush=True)
    print("  PLAYBOOK ANDERSON #1 — hipótese fixa (sem busca) | engine honesto", flush=True)
    print("=" * 70, flush=True)
    jobs = [(mk, wname, s, e) for mk in ("NQ", "ES", "XAU") for wname, (s, e) in wins.items()]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=6) as ex:
        for line in ex.map(_job, jobs):
            print(line, flush=True)
    print("\n  Régua: só vai pro holdout se IS E VAL >= 1.05. Holdout: PF>=1.3 DD<=15%.", flush=True)


if __name__ == "__main__":
    main()
