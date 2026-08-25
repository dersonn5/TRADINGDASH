"""
Plotter de trades — auditoria VISUAL dos setups detectados (estilo TradingView)
================================================================================
Roda o playbook num período, salva PNG de cada trade: candles 5m do dia + dia
anterior, com marcações (zona varrida, range, IFVG, entrada/stop/alvo).
Usuário confere com o olho se a detecção bate com a leitura dele.

Uso:  python -m research.plot_trades --market NQ --start 2024-01-01 --end 2024-12-31
Saída: research/trade_plots/<mercado>_<data>_<n>.png
"""
import os, sys, argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.playbook_anderson import PlaybookAnderson, PlaybookAndersonConfig

OUT = os.path.join(os.path.dirname(__file__), "trade_plots")


def candles(ax, df):
    for i, (_, r) in enumerate(df.iterrows()):
        c = "#26a69a" if r["close"] >= r["open"] else "#ef5350"
        ax.plot([i, i], [r["low"], r["high"]], color=c, lw=0.7)
        ax.add_patch(plt.Rectangle((i - 0.35, min(r["open"], r["close"])), 0.7,
                                   abs(r["close"] - r["open"]) or 0.01, color=c))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="NQ", choices=list(MARKETS.keys()))
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    m = MARKETS[args.market]
    c5, c1h, c1d, c1m, c5c = _load_full(args.market)
    s5, s1h, s1d, s1m = (_slice(c5, args.start, args.end), _slice(c1h, args.start, args.end),
                         _slice(c1d, args.start, args.end), _slice(c1m, args.start, args.end))
    strat = PlaybookAnderson(PlaybookAndersonConfig())
    strat.symbol = m["symbol"]
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=3.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False)
    poss = res["positions"][:args.max]
    print(f"{len(res['positions'])} trades no período; plotando {len(poss)}", flush=True)

    df5 = strat._convert_to_est(s5)
    for k, p in enumerate(poss, 1):
        et = p.entry_time
        day = et.date()
        prev = df5[df5.index.date < day]
        prev_day = prev[prev.index.date == prev.index.date[-1]] if not prev.empty else prev
        today = df5[df5.index.date == day]
        win = pd.concat([prev_day, today])
        if win.empty:
            continue
        fig, ax = plt.subplots(figsize=(16, 8))
        candles(ax, win)
        n0 = len(prev_day)
        meta = p.meta or {}
        if meta.get("zone"):
            ax.axhline(meta["zone"], color="#2962ff", lw=1.2, ls="-",
                       label=f"zona varrida {meta['zone']:.1f}")
        iv = meta.get("ifvg") or {}
        if iv:
            ax.axhspan(iv["bottom"], iv["top"], color="#a5d6a7", alpha=0.5, label="IFVG")
        # entrada/stop/alvo
        ei = win.index.get_indexer([et], method="nearest")[0]
        ax.scatter([ei], [p.entry_price], marker="^" if p.action == "BUY" else "v",
                   color="black", s=90, zorder=5, label=f"entrada {p.action}")
        ax.axhline(p.stop_loss, color="red", lw=1, ls="--", label="stop")
        ax.axhline(p.take_profit, color="green", lw=1, ls="--", label="alvo")
        ax.axvline(n0 - 0.5, color="gray", lw=0.8, ls=":")
        ax.set_title(f"{args.market} {day} | {p.action} | pnl={p.pnl_usd:+.0f} | {p.reason}")
        ax.legend(loc="best", fontsize=8)
        ax.set_xlim(-1, len(win))
        fn = os.path.join(OUT, f"{args.market}_{day}_{k:02d}.png")
        fig.savefig(fn, dpi=90, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {fn}", flush=True)


if __name__ == "__main__":
    main()
