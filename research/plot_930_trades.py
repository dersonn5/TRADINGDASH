"""
Plotter de Trades da Estratégia 9:30 AM IFVG (Estilo TradingView / ICT)
========================================================================
Plota o gráfico M1 com as marcações ICT do trade:
- Sweep 1H (linha azul)
- Caixa IFVG (retângulo verde/amarelo)
- Entrada (triângulo preto), Stop Loss (linha vermelha), Take Profit (linha verde)
- Rótulo de Resultado (PNL, Win/Loss, motivo da saída)

Uso: python -m research.plot_930_trades --market NQ --max 5
"""

import os
import sys
import argparse
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.strat_930_ifvg import Strat930IFVG, Strat930Config

OUT_DIR = os.path.join(os.path.dirname(__file__), "trade_plots_930")


def draw_candlesticks(ax, df):
    """Desenha velas japonesas limpas estilo TradingView."""
    for i, (_, r) in enumerate(df.iterrows()):
        color = "#26a69a" if r["close"] >= r["open"] else "#ef5350"
        ax.plot([i, i], [r["low"], r["high"]], color=color, lw=0.8)
        height = abs(r["close"] - r["open"]) or 0.05
        bottom = min(r["open"], r["close"])
        ax.add_patch(plt.Rectangle((i - 0.35, bottom), 0.7, height, color=color))


def plot_single_trade(market, p, df1m, index_no):
    et = p.entry_time
    day = et.date()
    
    # Filtra 60 velas M1 antes da entrada e 60 velas depois
    trade_idx = df1m.index.get_indexer([et], method="nearest")[0]
    start_idx = max(0, trade_idx - 50)
    end_idx = min(len(df1m), trade_idx + 80)
    
    window = df1m.iloc[start_idx:end_idx]
    if window.empty:
        return None

    fig, ax = plt.subplots(figsize=(14, 7))
    draw_candlesticks(ax, window)

    # Re-mapeia o índice relativo para plotagem (0 a N)
    rel_entry_idx = trade_idx - start_idx
    meta = getattr(p, "meta", {}) or {}
    ifvg_zone = meta.get("ifvg_zone")

    # 1. Desenhar Zona IFVG
    if ifvg_zone:
        top_z, bot_z = ifvg_zone
        ax.axhspan(bot_z, top_z, color="#ffe082", alpha=0.45, label=f"IFVG 1M [{bot_z:.1f} - {top_z:.1f}]")

    # 2. Desenhar Nível de Entrada, Stop Loss e Take Profit
    ax.axhline(p.stop_loss, color="#d32f2f", lw=1.5, ls="--", label=f"Stop Loss ({p.stop_loss:.1f})")
    ax.axhline(p.take_profit, color="#388e3c", lw=1.5, ls="--", label=f"Take Profit ({p.take_profit:.1f})")
    
    # Ponto de entrada
    ax.scatter([rel_entry_idx], [p.entry_price], marker="^" if p.action == "BUY" else "v",
               color="black", s=120, zorder=6, label=f"Entrada {p.action} @ {p.entry_price:.1f}")

    # Estética do gráfico
    status_str = "WIN ✅" if p.pnl_usd > 0 else "LOSS ❌"
    ax.set_title(f"{market} | Data: {day} {et.strftime('%H:%M')} | {status_str} (PnL: ${p.pnl_usd:+.2f}) | Exit: {p.reason}",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Velas M1 (Relativo)", fontsize=10)
    ax.set_ylabel("Preço", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)

    out_file = os.path.join(OUT_DIR, f"{market}_{day}_{index_no:02d}_{status_str[:4]}.png")
    fig.savefig(out_file, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return out_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="NQ", choices=list(MARKETS.keys()))
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--max", type=int, default=10)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    m = MARKETS[args.market]
    c5, c1h, c1d, c1m, _ = _load_full(args.market)
    s5, s1h, s1d, s1m = (
        _slice(c5, args.start, args.end),
        _slice(c1h, args.start, args.end),
        _slice(c1d, args.start, args.end),
        _slice(c1m, args.start, args.end)
    )

    strat = Strat930IFVG(Strat930Config(target_rr=3.0))
    strat.symbol = m["symbol"]
    
    bc = BacktestConfig(
        initial_balance=10000.0,
        tick_size=m["tick"],
        point_value=1.0,
        commission_pct=0.0002
    )

    print(f"[PLOT] Rodando simulação para gerar trades em {args.market}...", flush=True)
    res = BacktestEngine(bc).run(
        strategy=strat,
        candles_5m=s5,
        candles_15m=s5,
        candles_1h=s1h,
        candles_1d=s1d,
        candles_1m=s1m,
        use_filters=False
    )
    
    positions = res["positions"]
    print(f"[PLOT] Total de {len(positions)} trades gerados. Salvando {min(len(positions), args.max)} gráficos PNG...", flush=True)

    df1m = strat._convert_to_est(s1m)
    saved_count = 0
    for idx, p in enumerate(positions[:args.max], 1):
        out_fn = plot_single_trade(args.market, p, df1m, idx)
        if out_fn:
            saved_count += 1
            print(f"  -> Gráfico salvo: [trade_{idx:02d}] {out_fn}", flush=True)

    print(f"\n✅ {saved_count} gráficos salvos na pasta: {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
