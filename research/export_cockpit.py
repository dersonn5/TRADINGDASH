"""
Exporter — gera cockpit/data/portfolio.json com dados REAIS do backtest
=======================================================================
Roda a config validada, coleta trades + curva de capital + métricas e salva
no formato que o cockpit_api serve.

Uso:
    python -m research.export_cockpit --symbol BTC/USDT:USDT --start 2024-01-01 --end 2024-12-31
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab import _load, clamp
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics

OUT = Path(__file__).resolve().parents[1] / "cockpit" / "data" / "portfolio.json"
BEST = {"min_score": 58, "displacement_atr": 0.95, "pd_tolerance": 0.08}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTC/USDT:USDT")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--balance", type=float, default=500.0)
    args = ap.parse_args()

    c5, c1h, c1d, c1m, c5c = _load(args.symbol, args.start, args.end)
    ov = clamp(BEST)
    strat_kw = {k: v for k, v in ov.items() if k in ("min_score", "displacement_atr", "pd_tolerance")}
    s = ICTTopDownCrypto(ICTTopDownConfig(**strat_kw))
    s.symbol = args.symbol
    s.correlated_symbol = "ETH/USDT:USDT" if args.symbol == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    tick = 0.1 if args.symbol == "BTC/USDT:USDT" else 0.01
    bc = BacktestConfig(initial_balance=args.balance, tick_size=tick, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0001,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    positions = res["positions"]
    m = PerformanceMetrics.calculate(positions, args.balance)

    # curva de capital + trades
    bal = args.balance
    equity = [{"t": args.start, "balance": round(bal, 2)}]
    trades = []
    for i, p in enumerate(positions, 1):
        bal += p.pnl_usd
        et = p.exit_time or p.entry_time
        equity.append({"t": (et.strftime("%Y-%m-%d %H:%M") if hasattr(et, "strftime") else str(et)),
                       "balance": round(bal, 2)})
        meta = getattr(p, "meta", {}) or {}
        trades.append({
            "id": i,
            "date": p.entry_time.strftime("%Y-%m-%d %H:%M") if hasattr(p.entry_time, "strftime") else str(p.entry_time),
            "symbol": args.symbol.split(":")[0],
            "side": p.action,
            "entry": round(p.entry_price, 2), "sl": round(p.stop_loss, 2), "tp": round(p.take_profit, 2),
            "rr": round(abs(p.take_profit - p.entry_price) / abs(p.entry_price - p.stop_loss), 1)
                  if abs(p.entry_price - p.stop_loss) > 0 else 0,
            "result": "WIN" if p.pnl_usd > 0 else "LOSS",
            "pnl": round(p.pnl_usd, 2),
            "grade": meta.get("quality_grade", "?"),
            "reason": (p.reason or "")[:60],
        })

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "symbol": args.symbol, "period": f"{args.start} → {args.end}", "balance0": args.balance,
        "metrics": {
            "profit_factor": round(m["profit_factor"], 2), "win_rate": round(m["win_rate"], 1),
            "total_pnl": round(m["total_pnl_usd"], 2), "max_drawdown": round(m["max_drawdown_percent"], 1),
            "trades": m["total_trades"], "expectancy": round(m["expectancy_usd"], 1),
            "final_balance": round(m["final_balance"], 2),
        },
        "equity": equity, "trades": trades, "positions": [], "sample": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"[export] {len(trades)} trades, PF={out['metrics']['profit_factor']}, "
          f"final=${out['metrics']['final_balance']} -> {OUT}")


if __name__ == "__main__":
    main()
