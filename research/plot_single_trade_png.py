"""
Gerador de Imagem PNG de Trade Único Estilo ICT (TradingView Dark Theme)
========================================================================
Desenha um gráfico PNG de alta definição com estética idêntica ao TradingView:
- Fundo escuro (#131722) e grilação discreta (#2a2e39)
- Velas verdes (#089981) e vermelhas (#f23645)
- Caixa de Destaque Retangular do 1M IFVG com borda pontilhada e caixa de texto
- Nível de Liquidez Varrida (Sweep de 1H)
- Entrada, Stop Loss (linha vermelha) e Take Profit (linha verde)

Uso: python -m research.plot_single_trade_png --market NQ --trade-idx 1
"""

import os
import sys
import argparse
from datetime import timedelta
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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


def draw_tradingview_candlesticks(ax, df):
    """Desenha velas japonesas no estilo TradingView (Verde #089981, Vermelho #f23645)."""
    for i, (_, r) in enumerate(df.iterrows()):
        color = "#089981" if r["close"] >= r["open"] else "#f23645"
        # Pavio
        ax.plot([i, i], [r["low"], r["high"]], color=color, lw=1.0, zorder=2)
        # Corpo
        height = abs(r["close"] - r["open"]) or 0.1
        bottom = min(r["open"], r["close"])
        rect = patches.Rectangle((i - 0.35, bottom), 0.7, height, facecolor=color, edgecolor=color, zorder=3)
        ax.add_patch(rect)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="NQ")
    ap.add_argument("--trade-idx", type=int, default=1)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    m = MARKETS[args.market]
    c5, c1h, c1d, c1m, _ = _load_full(args.market)
    s5, s1h, s1d, s1m = (
        _slice(c5, "2024-01-01", "2024-12-31"),
        _slice(c1h, "2024-01-01", "2024-12-31"),
        _slice(c1d, "2024-01-01", "2024-12-31"),
        _slice(c1m, "2024-01-01", "2024-12-31")
    )

    strat = Strat930IFVG(Strat930Config(target_rr=3.0))
    strat.symbol = m["symbol"]
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0, commission_pct=0.0002)

    res = BacktestEngine(bc).run(
        strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h, candles_1d=s1d, candles_1m=s1m, use_filters=False
    )
    positions = res["positions"]
    if not positions or len(positions) < args.trade_idx:
        print(f"[ERRO] Trade #{args.trade_idx} não encontrado.")
        return

    p = positions[args.trade_idx - 1]
    df1m = strat._convert_to_est(s1m)

    et = pd.Timestamp(p.entry_time)
    if et.tzinfo is None:
        et = et.tz_localize("America/New_York")

    trade_idx_pos = df1m.index.get_indexer([et], method="nearest")[0]
    start_idx = max(0, trade_idx_pos - 40)
    end_idx = min(len(df1m), trade_idx_pos + 60)
    window = df1m.iloc[start_idx:end_idx]

    # Setup do gráfico com tema escuro TradingView
    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#131722")
    ax.set_facecolor("#131722")
    draw_tradingview_candlesticks(ax, window)

    rel_entry_idx = trade_idx_pos - start_idx
    meta = getattr(p, "meta", {}) or {}
    ifvg_zone = meta.get("ifvg_zone")

    # 1. Desenhar a Caixa Retangular do IFVG estilo TradingView
    if ifvg_zone:
        top_z, bot_z = ifvg_zone
        rect = patches.Rectangle(
            (0, bot_z), len(window), top_z - bot_z,
            facecolor="#ff9800", alpha=0.25, edgecolor="#ff9800", linestyle="--", linewidth=1.2, zorder=1
        )
        ax.add_patch(rect)
        # Rótulo de texto da caixa
        ax.text(
            2, (top_z + bot_z) / 2, f"  1M IFVG (Inversion Gap) [{bot_z:.2f} - {top_z:.2f}]  ",
            color="#ffffff", fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ff9800", edgecolor="#ffffff", lw=1),
            verticalalignment="center", zorder=5
        )

    # 2. Marcação da Linha do Stop Loss e Take Profit
    ax.axhline(p.stop_loss, color="#f23645", linestyle="--", linewidth=1.5, zorder=4)
    ax.text(len(window) - 1, p.stop_loss, f"  Stop Loss: {p.stop_loss:.2f}", color="#f23645", fontsize=11, fontweight="bold", verticalalignment="center")

    ax.axhline(p.take_profit, color="#089981", linestyle="--", linewidth=1.5, zorder=4)
    ax.text(len(window) - 1, p.take_profit, f"  Take Profit (3:1): {p.take_profit:.2f}", color="#089981", fontsize=11, fontweight="bold", verticalalignment="center")

    # 3. Marcador de Entrada
    ax.scatter([rel_entry_idx], [p.entry_price], marker="^" if p.action == "BUY" else "v",
               color="#2962ff", s=180, edgecolors="#ffffff", linewidths=1.5, zorder=6)
    ax.text(rel_entry_idx + 1, p.entry_price, f"ENTRADA {p.action} @ {p.entry_price:.2f}", color="#2962ff", fontsize=11, fontweight="bold", verticalalignment="center")

    # Estética do Grid e Eixos
    ax.tick_params(colors="#d1d4dc", labelsize=10)
    ax.grid(True, color="#2a2e39", linestyle=":", alpha=0.7)
    
    status_str = "WIN ✅" if p.pnl_usd > 0 else "LOSS ❌"
    ax.set_title(f"Trade #{args.trade_idx}: {p.action} {args.market} | Data: {et.strftime('%Y-%m-%d %H:%M EST')} | Resultado: {status_str} (PnL: ${p.pnl_usd:+.2f})",
                 color="#ffffff", fontsize=14, fontweight="bold", pad=15)

    out_png = os.path.join(OUT_DIR, f"single_trade_{args.trade_idx}_ict.png")
    fig.savefig(out_png, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"✅ PNG gerado com sucesso: {out_png}")


if __name__ == "__main__":
    main()
