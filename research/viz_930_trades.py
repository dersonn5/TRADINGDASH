"""
Visualizador Interativo de Trades ICT (Estratégia 9:30 AM IFVG) — Estilo TradingView
===================================================================================
Gera um relatório HTML interativo (Plotly) com marcações idênticas ao TradingView:
- Caixas retangulares coloridas para FVGs / IFVGs / Breaker Blocks com nomes customizados
- Linhas horizontais pontilhadas para Sweeps de 1H e liquidez (RTH High/Low)
- Caixas de Risco/Retorno (Risk/Reward 3:1)
- Menu dropdown para navegar por cada trade com navegação fluida de zoom

Uso:
  python -m research.viz_930_trades --market NQ --start 2024-01-01 --end 2024-12-31 --max 20
"""

import os
import sys
import argparse
from datetime import timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.strat_930_ifvg import Strat930IFVG, Strat930Config

OUT_DIR = Path(__file__).resolve().parent / "plots_html"


def to_est(df):
    if df is None or df.empty:
        return df
    d = df.copy()
    if not isinstance(d.index, pd.DatetimeIndex):
        d.index = pd.to_datetime(d.index)
    return d.index.tz_localize("UTC").tz_convert("America/New_York") if d.index.tz is None else d.index.tz_convert("America/New_York")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="NQ", choices=list(MARKETS.keys()))
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--max", type=int, default=25)
    ap.add_argument("--theme", default="dark", choices=["dark", "light"])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
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

    print(f"[VIZ] Executando backtest em {args.market} para extração visual de trades...", flush=True)
    res = BacktestEngine(bc).run(
        strategy=strat,
        candles_5m=s5,
        candles_15m=s5,
        candles_1h=s1h,
        candles_1d=s1d,
        candles_1m=s1m,
        use_filters=False
    )

    positions = res["positions"][:args.max]
    if not positions:
        print("[VIZ] Nenhum trade encontrado no período.")
        return

    df1m = strat._convert_to_est(s1m)
    fig = go.Figure()
    per_trade = []

    is_dark = args.theme == "dark"
    bg_color = "#131722" if is_dark else "#ffffff"
    grid_color = "#2a2e39" if is_dark else "#f0f3fa"
    text_color = "#d1d4dc" if is_dark else "#131722"
    bull_color = "#089981"
    bear_color = "#f23645"

    for i, p in enumerate(positions):
        et = pd.Timestamp(p.entry_time)
        if et.tzinfo is None:
            et = et.tz_localize("America/New_York")
        
        xt = pd.Timestamp(p.exit_time) if p.exit_time is not None else et + timedelta(minutes=30)
        if xt.tzinfo is None:
            xt = xt.tz_localize("America/New_York")

        x0 = et - timedelta(minutes=45)
        x1 = xt + timedelta(minutes=25)
        win = df1m[(df1m.index >= x0) & (df1m.index <= x1)]
        if win.empty:
            per_trade.append(None)
            continue

        base_idx = len(fig.data)
        # Add Candlesticks trace
        fig.add_trace(go.Candlestick(
            x=win.index,
            open=win["open"],
            high=win["high"],
            low=win["low"],
            close=win["close"],
            showlegend=False,
            visible=(i == 0),
            increasing_line_color=bull_color,
            decreasing_line_color=bear_color,
            increasing_fillcolor=bull_color,
            decreasing_fillcolor=bear_color,
            name="Preço 1M"
        ))

        # Add Entry Marker
        fig.add_trace(go.Scatter(
            x=[et],
            y=[p.entry_price],
            mode="markers+text",
            text=[f"  ENTRADA {p.action}"],
            textposition="middle right",
            textfont=dict(color="#2962ff" if is_dark else "#1e88e5", size=11),
            visible=(i == 0),
            marker=dict(
                symbol="triangle-up" if p.action == "BUY" else "triangle-down",
                size=14,
                color="#2962ff",
                line=dict(width=1, color="#ffffff")
            ),
            showlegend=False
        ))

        # Add Exit Marker
        fig.add_trace(go.Scatter(
            x=[xt],
            y=[p.exit_price if p.exit_price else p.entry_price],
            mode="markers+text",
            text=[f"  SAÍDA ({p.reason})"],
            textposition="middle right",
            textfont=dict(color=bull_color if p.pnl_usd > 0 else bear_color, size=11),
            visible=(i == 0),
            marker=dict(
                symbol="x",
                size=12,
                color=bull_color if p.pnl_usd > 0 else bear_color
            ),
            showlegend=False
        ))

        shapes = []
        anns = []

        # 1. Caixa de Risk/Reward (Shading verde/vermelho)
        # Profit Zone (Verde)
        shapes.append(dict(
            type="rect", xref="x", yref="y",
            x0=et, x1=x1, y0=p.entry_price, y1=p.take_profit,
            fillcolor="rgba(8,153,129,0.15)", line=dict(width=0), layer="below"
        ))
        # Risk Zone (Vermelha)
        shapes.append(dict(
            type="rect", xref="x", yref="y",
            x0=et, x1=x1, y0=p.entry_price, y1=p.stop_loss,
            fillcolor="rgba(242,54,69,0.15)", line=dict(width=0), layer="below"
        ))

        # 2. Marcação da Zona IFVG 1M (Estilo Retângulo TradingView)
        meta = getattr(p, "meta", {}) or {}
        ifvg_zone = meta.get("ifvg_zone")
        if ifvg_zone:
            top_z, bot_z = ifvg_zone
            ifvg_color = "rgba(255,152,0,0.35)"
            shapes.append(dict(
                type="rect", xref="x", yref="y",
                x0=x0, x1=x1, y0=bot_z, y1=top_z,
                fillcolor=ifvg_color, line=dict(color="#ff9800", width=1, dash="dot"), layer="below"
            ))
            anns.append(dict(
                x=x0 + timedelta(minutes=5), y=(top_z + bot_z) / 2,
                text="<b>1M IFVG (Inversion Gap)</b>",
                showarrow=False, font=dict(size=11, color="#ff9800"),
                xanchor="left", bgcolor=bg_color, bordercolor="#ff9800", borderwidth=1
            ))

        # 3. Linhas horizontais de Stop Loss e Take Profit com rótulos estilo TradingView
        shapes.append(dict(
            type="line", xref="x", yref="y",
            x0=x0, x1=x1, y0=p.stop_loss, y1=p.stop_loss,
            line=dict(color=bear_color, width=1.5, dash="dash")
        ))
        anns.append(dict(
            x=x1, y=p.stop_loss, text=f"  SL: {p.stop_loss:.2f}",
            showarrow=False, font=dict(size=11, color=bear_color), xanchor="right"
        ))

        shapes.append(dict(
            type="line", xref="x", yref="y",
            x0=x0, x1=x1, y0=p.take_profit, y1=p.take_profit,
            line=dict(color=bull_color, width=1.5, dash="dash")
        ))
        anns.append(dict(
            x=x1, y=p.take_profit, text=f"  TP (3:1): {p.take_profit:.2f}",
            showarrow=False, font=dict(size=11, color=bull_color), xanchor="right"
        ))

        # Y limits
        ys = list(win["low"]) + list(win["high"]) + [p.stop_loss, p.take_profit, p.entry_price]
        ylo, yhi = min(ys), max(ys)
        pad_y = (yhi - ylo) * 0.05

        status_str = "WIN ✅" if p.pnl_usd > 0 else "LOSS ❌"
        title = (
            f"<b>Trade #{i+1}: {p.action} {args.market}</b> | Data: {et.strftime('%Y-%m-%d %H:%M EST')} | "
            f"Resultado: <b>{status_str} ({p.pnl_usd:+.2f} USD)</b> | Motivo Saída: {p.reason}"
        )

        per_trade.append(([base_idx, base_idx + 1, base_idx + 2], shapes, anns, [x0, x1], [ylo - pad_y, yhi + pad_y], title))

    # Construir Botões Dropdown
    total_traces = len(fig.data)
    buttons = []
    valid_trades = [(idx, item) for idx, item in enumerate(per_trade) if item]

    for idx, item in valid_trades:
        vis_idxs, shapes, anns, xr, yr, title = item
        vis = [False] * total_traces
        for vi in vis_idxs:
            vis[vi] = True

        buttons.append(dict(
            label=f"Trade #{idx+1} ({positions[idx].action} - {'WIN' if positions[idx].pnl_usd > 0 else 'LOSS'})",
            method="update",
            args=[
                {"visible": vis},
                {
                    "shapes": shapes,
                    "annotations": anns,
                    "xaxis.range": xr,
                    "yaxis.range": yr,
                    "title.text": title
                }
            ]
        ))

    first_item = valid_trades[0][1]
    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        updatemenus=[dict(
            buttons=buttons,
            direction="down",
            x=0.01, xanchor="left",
            y=1.12, yanchor="top",
            showactive=True,
            bgcolor="#2a2e39" if is_dark else "#ffffff",
            bordercolor="#434651" if is_dark else "#cccccc",
            font=dict(color=text_color, size=12)
        )],
        shapes=first_item[1],
        annotations=first_item[2],
        xaxis=dict(
            range=first_item[3],
            rangeslider=dict(visible=False),
            gridcolor=grid_color,
            color=text_color
        ),
        yaxis=dict(
            range=first_item[4],
            gridcolor=grid_color,
            color=text_color
        ),
        title=dict(text=first_item[5], font=dict(color=text_color, size=14)),
        height=750,
        margin=dict(t=100, b=40, l=40, r=40)
    )

    out_file = OUT_DIR / f"ict_trade_review_{args.market}_2024.html"
    fig.write_html(str(out_file))
    print(f"\n✅ Relatório Visual Interativo gerado com sucesso!")
    print(f"📄 Arquivo: {out_file}")


if __name__ == "__main__":
    main()
