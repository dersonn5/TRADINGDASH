"""
Backtest NQ (Nasdaq 100) com SMT vs S&P 500 — o home turf do ICT
================================================================
NQ e ES(SPX) são super correlacionados → SMT divergence entre eles é o setup
CANÔNICO do ICT (muito mais limpo que BTC/ETH). Aqui o SMT fica LIGADO,
correlacionado = SPX.

Uso:
    python -m research.backtest_nq
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig

SYMBOL = "NAS/USD"
CORR = "SPX/USD"
# SMT LIGADO (é o ponto). Score sem SMT tem teto 90 → min_score ajustado.
CFG = dict(min_score=55, displacement_atr=0.9, pd_tolerance=0.10, require_smt=True,
           target_rr=3.0, min_rr=1.8,
           min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)


def _load(start, end):
    ld = DataLoader()
    c5 = ld.load_data(SYMBOL, "5m", start, end)
    c1d = ld.load_data(SYMBOL, "1d", start, end)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(SYMBOL, "1m", start, end)
    c5c = ld.load_data(CORR, "5m", start, end)   # S&P p/ SMT
    return c5, c1h, c1d, c1m, c5c


def run(start, end):
    c5, c1h, c1d, c1m, c5c = _load(start, end)
    s = ICTTopDownCrypto(ICTTopDownConfig(**CFG))
    s.symbol = SYMBOL
    s.correlated_symbol = CORR
    bc = BacktestConfig(initial_balance=10000.0, tick_size=0.25, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def main():
    print("=" * 62)
    print("  BACKTEST NQ (Nasdaq) + SMT vs S&P 500 — home turf do ICT")
    print("=" * 62)
    for name, (s, e) in [("IS  2022-23", ("2022-01-01", "2023-12-31")),
                         ("OOS 2024   ", ("2024-01-01", "2024-12-31"))]:
        m = run(s, e)
        print(f"  {name}: trades={m['total_trades']:<4} win={m['win_rate']:.1f}% "
              f"PF={m['profit_factor']:.2f} PnL={m['total_pnl_usd']:+.0f} DD={m['max_drawdown_percent']:.1f}%")


if __name__ == "__main__":
    main()
