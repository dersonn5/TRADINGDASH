"""Backtest rápido das estratégias Breaker Block XAU (Lunch + Close)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.session_configs import make_bb_xau_lunch, make_bb_xau_close

loader = DataLoader()
xau = {k: loader.load_data("C:XAUUSD", k, "2026-04-19", "2026-05-19") for k in ["5m","15m","1h","1d","1m"]}

# Config correta para XAU: tick=0.01, point_value=1.0 (preço em USD/oz, size=1oz)
# O DataLoader usa preco em USD/oz. 1 unidade = 1 oz (micro-lote).
# PnL = (price_diff) * size_units * point_value
# Para XAU: tick=0.1, point_value=1.0 → size_units = capital_risk / sl_distance
xau_config = BacktestConfig(
    initial_balance=10000.0,
    slippage_ticks=2,
    spread_ticks=2,
    commission_usd=2.5,
    tick_size=0.1,
    point_value=1.0,  # 1 oz XAU, PnL = price_diff * oz
)
engine = BacktestEngine(xau_config)

print("=== Backtest: Breaker Block XAU — Lunch + Close ===\n")

all_positions = []
for label, strat in [("BB XAU Lunch", make_bb_xau_lunch()), ("BB XAU Close", make_bb_xau_close())]:
    result = engine.run(
        strategy=strat,
        candles_5m=xau["5m"],
        candles_15m=xau["15m"],
        candles_1h=xau["1h"],
        candles_1d=xau["1d"],
        candles_1m=xau["1m"],
        use_filters=False,
    )
    positions = result["positions"]
    metrics = result["metrics"]
    all_positions.extend(positions)
    pnl = metrics.get("total_pnl", 0)
    wr = metrics.get("win_rate", 0) * 100
    pf = metrics.get("profit_factor", 0)
    dd = metrics.get("max_drawdown_percent", 0)
    n = len(positions)
    print(f"  {label}:")
    print(f"    Trades: {n}")
    print(f"    PnL: {pnl:.2f} USD")
    print(f"    Win Rate: {wr:.1f}%")
    print(f"    Profit Factor: {pf:.2f}")
    print(f"    Max Drawdown: {dd:.2f}%")
    print()

wins = sum(1 for p in all_positions if getattr(p, "pnl_usd", 0) > 0)
total_pnl = sum(getattr(p, "pnl_usd", 0) for p in all_positions)
n_total = len(all_positions)
wr_total = (wins / n_total * 100) if n_total else 0.0
print("PORTFOLIO BREAKER BLOCK XAU TOTAL:")
print(f"  Trades: {n_total}")
print(f"  Win Rate: {wr_total:.1f}%")
print(f"  PnL Total: {total_pnl:.2f} USD")
