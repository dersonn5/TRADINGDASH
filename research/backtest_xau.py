"""
Backtest XAU (Ouro) — top-down v2 no mercado NATIVO do ICT
===========================================================
Roda a estratégia ICT top-down em XAU/USD (Dukascopy), IS 2022-23 / OOS 2024.
Tese: ICT é nativo de ouro/índices (sessões reais, fluxo institucional) →
pode render MELHOR que cripto. SMT off (ouro não tem par tipo BTC/ETH).

Uso:
    python -m research.backtest_xau
"""
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig

SYMBOL = "XAU/USD"
# config otimizada (min_score menor: sem SMT o teto de score cai de 100->90)
CFG = dict(min_score=52, displacement_atr=0.95, pd_tolerance=0.08,
           require_smt=False, target_rr=3.0, min_rr=1.8,
           min_sl_distance_percent=0.0025, max_sl_distance_percent=0.012)


def _load(start, end):
    ld = DataLoader()
    c5 = ld.load_data(SYMBOL, "5m", start, end)
    c1d = ld.load_data(SYMBOL, "1d", start, end)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(SYMBOL, "1m", start, end)
    return c5, c1h, c1d, c1m


def run(start, end):
    c5, c1h, c1d, c1m = _load(start, end)
    s = ICTTopDownCrypto(ICTTopDownConfig(**CFG))
    s.symbol = SYMBOL
    s.correlated_symbol = ""
    eng = BacktestEngine(BacktestConfig(initial_balance=10000.0, tick_size=0.01, point_value=1.0,
                                        commission_usd=0.5, enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                                        enable_break_even=True, break_even_trigger_rr=2.0,
                                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5,
                                        funding_rate_8h=0.0))  # ouro: sem funding de perp
    res = eng.run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h, candles_1d=c1d,
                  candles_1m=c1m, use_filters=False, candles_5m_corr=None)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def main():
    print("=" * 60)
    print("  BACKTEST XAU (Ouro) — top-down v2 | mercado nativo ICT")
    print("=" * 60)
    for name, (s, e) in [("IS  2022-23", ("2022-01-01", "2023-12-31")),
                         ("OOS 2024   ", ("2024-01-01", "2024-12-31"))]:
        m = run(s, e)
        print(f"  {name}: trades={m['total_trades']:<4} win={m['win_rate']:.1f}% "
              f"PF={m['profit_factor']:.2f} PnL={m['total_pnl_usd']:+.0f} DD={m['max_drawdown_percent']:.1f}%")


if __name__ == "__main__":
    main()
