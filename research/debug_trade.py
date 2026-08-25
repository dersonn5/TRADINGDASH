import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.strat_930_ifvg import Strat930IFVG, Strat930Config

def main():
    m = MARKETS["NQ"]
    c5, c1h, c1d, c1m, _ = _load_full("NQ")
    s5, s1h, s1d, s1m = (
        _slice(c5, "2024-01-16", "2024-01-20"),
        _slice(c1h, "2024-01-16", "2024-01-20"),
        _slice(c1d, "2024-01-16", "2024-01-20"),
        _slice(c1m, "2024-01-16", "2024-01-20")
    )
    strat = Strat930IFVG(Strat930Config(target_rr=3.0))
    strat.symbol = "NQ"
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0)
    res = BacktestEngine(bc).run(
        strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h, candles_1d=s1d, candles_1m=s1m, use_filters=False
    )
    positions = res["positions"]
    if not positions:
        print("Nenhum trade encontrado.")
        return
    p = positions[0]
    print("Action:", p.action)
    print("Entry Time Raw:", p.entry_time)
    
    et = pd.Timestamp(p.entry_time)
    print("ET TZ:", et.tzinfo)
    if et.tzinfo is not None:
        print("ET UTC:", et.tz_convert("UTC"))
        print("ET EST:", et.tz_convert("America/New_York"))
    else:
        print("ET is naive")

if __name__ == "__main__":
    main()
