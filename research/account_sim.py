"""
Simulação de conta micro ($150 / $500) — o edge sobrevive às taxas reais?
=========================================================================
Roda o top-down v2 (config otimizada) com saldo pequeno e TAXA % REAL da OKX
(taker 0.05%/lado) + funding. Mostra se o atrito come o edge fino.

Sizing por risco (RiskManager, 1% do saldo) → compõe ao longo do tempo.

Uso:
    python -m research.account_sim
"""
import os
import sys
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

CFG = dict(min_score=58, displacement_atr=0.95, pd_tolerance=0.08)
START, END = "2022-01-01", "2024-12-31"
SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT"]
# cenários de taxa (por LADO): sem taxa / maker OKX / taker OKX
SCENARIOS = {"ideal": 0.0, "maker 0.02%": 0.0002, "taker 0.05%": 0.0005}
_C = {}


def _load(sym):
    if sym in _C:
        return _C[sym]
    ld = DataLoader()
    c5 = ld.load_data(sym, "5m", START, END)
    c1d = ld.load_data(sym, "1d", START, END)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(sym, "1m", START, END)
    corr = "ETH/USDT:USDT" if sym == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    c5c = ld.load_data(corr, "5m", START, END)
    _C[sym] = (c5, c1h, c1d, c1m, c5c)
    return _C[sym]


def run(sym, balance, scenario):
    c5, c1h, c1d, c1m, c5c = _load(sym)
    s = ICTTopDownCrypto(ICTTopDownConfig(**CFG))
    s.symbol = sym
    s.correlated_symbol = "ETH/USDT:USDT" if sym == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    tick = 0.1 if sym == "BTC/USDT:USDT" else 0.01
    comm_pct = SCENARIOS[scenario]
    comm_usd = 0.0
    fund = 0.0 if scenario == "ideal" else 0.0001
    bc = BacktestConfig(initial_balance=balance, tick_size=tick, point_value=1.0,
                        commission_usd=comm_usd, commission_pct=comm_pct, funding_rate_8h=fund,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    m = PerformanceMetrics.calculate(res["positions"], balance)
    return m


def main():
    print("=" * 68)
    print("  SIMULAÇÃO CONTA MICRO — edge sobrevive às taxas reais? (2022-2024)")
    print("=" * 68)
    for bal in (500.0,):
        print(f"\n  ### Saldo inicial ${bal:.0f} (3 anos) ###")
        print(f"  {'SYM':<5}{'cenário':<14}{'trades':>7}{'win%':>7}{'PF':>7}{'ret3a%':>9}{'ret/ano%':>10}{'final$':>10}")
        for sym in SYMBOLS:
            for sc in SCENARIOS:
                m = run(sym, bal, sc)
                ret = (m["final_balance"] / bal - 1) * 100
                ret_yr = ((m["final_balance"] / bal) ** (1 / 3.0) - 1) * 100  # anualizado
                print(f"  {sym[:3]:<5}{sc:<14}{m['total_trades']:>7}{m['win_rate']:>7.1f}"
                      f"{m['profit_factor']:>7.2f}{ret:>+9.1f}{ret_yr:>+10.1f}{m['final_balance']:>10.0f}")
    print("\n  (ret% e PF são ~independentes do saldo com taxa %; o que muda é ordem mínima e psicológico.)")


if __name__ == "__main__":
    main()
