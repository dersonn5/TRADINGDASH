"""
Gerador Canônico de Gráficos ICT (Estilo idêntico aos vídeos do ICT)
====================================================================
Recria com precisão cirúrgica o layout visual dos vídeos do ICT:
- Fundo Claro / Clean Backdrop (#f5f5f5)
- Velas estilo TradingView (Preto/Branco ou Verde/Vermelho)
- Nível RTH High / Low (Linha preta sólida com rótulo na direita: "RTH ORG High")
- Sellside / Buyside Liquidity (Linha vermelha/verde sólida com rótulo na direita)
- Linha de Equilíbrio 0.5 (Linha rosa no centro do range)
- Caixas Retangulares de FVGs e IFVGs (Preenchimento Rosa/Azul com bordas pontilhadas)
  * As caixas nascem na vela EXATA onde o gap foi gerado e se estendem até o reteste!

Uso: python -m research.plot_ict_canonical --market NQ --trade-idx 1
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

OUT_DIR = os.path.join(os.path.dirname(__file__), "trade_plots_ict_canonical")


def draw_ict_candlesticks(ax, df):
    """Desenha velas japonesas exatamente no estilo TradingView Light do ICT."""
    for i, (_, r) in enumerate(df.iterrows()):
        is_bull = r["close"] >= r["open"]
        border_color = "#26a69a" if is_bull else "#434651"
        fill_color = "#26a69a" if is_bull else "#434651"
        
        # Pavio
        ax.plot([i, i], [r["low"], r["high"]], color=border_color, lw=1.1, zorder=2)
        # Corpo da vela
        height = abs(r["close"] - r["open"]) or 0.15
        bottom = min(r["open"], r["close"])
        rect = patches.Rectangle((i - 0.38, bottom), 0.76, height, facecolor=fill_color, edgecolor=border_color, zorder=3)
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
    
    # Zoom ideal estilo ICT: 25 velas antes e 25 velas depois
    start_idx = max(0, trade_idx_pos - 25)
    end_idx = min(len(df1m), trade_idx_pos + 30)
    window = df1m.iloc[start_idx:end_idx]

    # Setup da figura no estilo visual do ICT (Fundo claro/cinza suave)
    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    draw_ict_candlesticks(ax, window)

    rel_entry = trade_idx_pos - start_idx
    meta = getattr(p, "meta", {}) or {}
    ifvg_zone = meta.get("ifvg_zone")

    # 1. Marcação do Nível RTH High Swept (Linha Preta Sólida no topo com rótulo na direita)
    high_max = window["high"].max()
    ax.axhline(high_max, color="#000000", linestyle="-", linewidth=1.5, zorder=4)
    ax.text(len(window) - 0.5, high_max, f"  RTH ORG High  {high_max:.2f}",
            color="#ffffff", fontsize=10, fontweight="bold", verticalalignment="center",
            bbox=dict(boxstyle="square,pad=0.3", facecolor="#000000", edgecolor="none"))

    # 2. Marcação da Liquidez de Venda (Sellside Liquidity - Linha Vermelha no fundo)
    low_min = window["low"].min()
    ax.axhline(low_min, color="#a93226", linestyle="-", linewidth=1.2, zorder=4)
    ax.text(len(window) - 0.5, low_min, f"  Sellside Liquidity  {low_min:.2f}",
            color="#ffffff", fontsize=10, fontweight="bold", verticalalignment="center",
            bbox=dict(boxstyle="square,pad=0.3", facecolor="#a93226", edgecolor="none"))

    # 3. Linha de Equilíbrio (0.5 Range - Linha Rosa)
    eq_level = (high_max + low_min) / 2.0
    ax.axhline(eq_level, color="#e8a0bf", linestyle="-", linewidth=1.0, zorder=4)
    ax.text(len(window) - 0.5, eq_level, f"  0.5 ({eq_level:.2f})",
            color="#e8a0bf", fontsize=9, verticalalignment="center")

    # 4. Caixas Retangulares dos FVGs e IFVGs (Exatamente como nas fotos do ICT)
    if ifvg_zone:
        top_z, bot_z = ifvg_zone
        
        # A caixa retangular nasce cerca de 10 velas antes da entrada e se estende até o final do gráfico
        fvg_x_start = max(0, rel_entry - 12)
        fvg_x_width = len(window) - fvg_x_start - 2
        
        # Cor estilo ICT (Rosa/Laranja Suave com bordas pontilhadas)
        rect = patches.Rectangle(
            (fvg_x_start, bot_z), fvg_x_width, top_z - bot_z,
            facecolor="#f88789" if p.action == "SELL" else "#56c5e4",
            alpha=0.55, edgecolor="#d9534f" if p.action == "SELL" else "#0288d1",
            linestyle=":", linewidth=1.5, zorder=1
        )
        ax.add_patch(rect)
        
        # Rótulo de texto DENTRO da caixa retangular (igual nas fotos do ICT)
        ax.text(
            fvg_x_start + (fvg_x_width * 0.4), (top_z + bot_z) / 2,
            f"1M IFVG [{bot_z:.2f} - {top_z:.2f}]",
            color="#ffffff" if p.action == "SELL" else "#000000",
            fontsize=10, fontweight="bold", verticalalignment="center", horizontalalignment="center", zorder=5
        )

    # 5. Marcador de Entrada no Reteste
    ax.scatter([rel_entry], [p.entry_price], marker="v" if p.action == "SELL" else "^",
               color="#000000", s=180, zorder=6)
    ax.text(rel_entry, p.entry_price + (2.0 if p.action == "SELL" else -2.0),
            f"  ENTRADA {p.action} @ {p.entry_price:.2f}",
            color="#000000", fontsize=11, fontweight="bold", verticalalignment="bottom" if p.action == "SELL" else "top")

    # 6. Linhas de Stop Loss e Take Profit
    ax.axhline(p.stop_loss, color="#d9534f", linestyle="--", linewidth=1.5, zorder=4)
    ax.text(0.5, p.stop_loss, f"SL: {p.stop_loss:.2f}", color="#d9534f", fontsize=10, fontweight="bold", verticalalignment="bottom")

    ax.axhline(p.take_profit, color="#26a69a", linestyle="--", linewidth=1.5, zorder=4)
    ax.text(0.5, p.take_profit, f"TP (3:1): {p.take_profit:.2f}", color="#26a69a", fontsize=10, fontweight="bold", verticalalignment="top")

    # Limites e Formatação Estética de Eixos
    ax.set_xlim(-1, len(window) + 6)
    ax.tick_params(colors="#333333", labelsize=10)
    ax.grid(True, color="#e0e0e0", linestyle=":", alpha=0.6)
    
    # Esconde a moldura superior e direita para visual clean
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    status_str = "WIN ✅" if p.pnl_usd > 0 else "LOSS ❌"
    ax.set_title(f"ICT Trade Review — {args.market} | Data: {et.strftime('%d/%m/%Y %H:%M EST')} | Resultado: {status_str} ({p.pnl_usd:+.2f} USD)",
                 color="#000000", fontsize=13, fontweight="bold", pad=15)

    out_png = os.path.join(OUT_DIR, f"trade_{args.trade_idx}_canonical_ict.png")
    fig.savefig(out_png, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"✅ Gráfico canônico ICT gerado com sucesso: {out_png}")


if __name__ == "__main__":
    main()
