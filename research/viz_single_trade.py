"""
Visualizador de Trade Único Estilo ICT (Foco em Perfeição Visual)
==================================================================
Gera um HTML interativo de um ÚNICO trade com todas as marcações ICT detalhadas:
- Nível de liquidez HTF varrido (linha horizontal pontilhada + rótulo)
- Caixa do IFVG 1M (retângulo colorido com borda e nome)
- Níveis de Entrada, Stop Loss e Take Profit
- Painel de detalhes do trade (HUD)

Uso: python -m research.viz_single_trade --market NQ --trade-idx 1
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="NQ", choices=list(MARKETS.keys()))
    ap.add_argument("--trade-idx", type=int, default=1, help="Número do trade (1-based)")
    ap.add_argument("--theme", default="dark", choices=["dark", "light"])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
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

    bc = BacktestConfig(
        initial_balance=10000.0,
        tick_size=m["tick"],
        point_value=1.0,
        commission_pct=0.0002
    )

    print(f"[SINGLE] Rodando simulação para capturar Trade #{args.trade_idx} em {args.market}...", flush=True)
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
    if not positions or len(positions) < args.trade_idx:
        print(f"[ERRO] Trade #{args.trade_idx} não encontrado. Total de trades: {len(positions)}")
        return

    p = positions[args.trade_idx - 1]
    df1m = strat._convert_to_est(s1m)

    et = pd.Timestamp(p.entry_time)
    if et.tzinfo is None:
        et = et.tz_localize("America/New_York")
    
    xt = pd.Timestamp(p.exit_time) if p.exit_time is not None else et + timedelta(minutes=30)
    if xt.tzinfo is None:
        xt = xt.tz_localize("America/New_York")

    # Janela de zoom ajustada: 40 velas antes e 30 velas depois
    x0 = et - timedelta(minutes=40)
    x1 = xt + timedelta(minutes=30)
    win = df1m[(df1m.index >= x0) & (df1m.index <= x1)]

    is_dark = args.theme == "dark"
    bg_color = "#131722" if is_dark else "#ffffff"
    grid_color = "#2a2e39" if is_dark else "#f0f3fa"
    text_color = "#d1d4dc" if is_dark else "#131722"
    bull_color = "#089981"
    bear_color = "#f23645"

    fig = go.Figure()

    # 1. Candlesticks M1 estilo TradingView
    fig.add_trace(go.Candlestick(
        x=win.index,
        open=win["open"],
        high=win["high"],
        low=win["low"],
        close=win["close"],
        showlegend=False,
        increasing_line_color=bull_color,
        decreasing_line_color=bear_color,
        increasing_fillcolor=bull_color,
        decreasing_fillcolor=bear_color,
        name="Preço 1M"
    ))

    # 2. Ponto de Entrada
    fig.add_trace(go.Scatter(
        x=[et],
        y=[p.entry_price],
        mode="markers+text",
        text=[f"  <b>ENTRADA {p.action}</b><br>  @{p.entry_price:.2f}"],
        textposition="middle right",
        textfont=dict(color="#2962ff", size=12),
        marker=dict(
            symbol="triangle-up" if p.action == "BUY" else "triangle-down",
            size=16,
            color="#2962ff",
            line=dict(width=1.5, color="#ffffff")
        ),
        showlegend=False
    ))

    # 3. Ponto de Saída
    fig.add_trace(go.Scatter(
        x=[xt],
        y=[p.exit_price if p.exit_price else p.entry_price],
        mode="markers+text",
        text=[f"  <b>SAÍDA ({p.reason})</b><br>  @{p.exit_price if p.exit_price else p.entry_price:.2f}"],
        textposition="middle right",
        textfont=dict(color=bull_color if p.pnl_usd > 0 else bear_color, size=12),
        marker=dict(
            symbol="x",
            size=14,
            color=bull_color if p.pnl_usd > 0 else bear_color
        ),
        showlegend=False
    ))

    shapes = []
    anns = []

    # 4. Caixas de Risco / Retorno (Projeção R:R)
    # Zone de Lucro (Verde)
    shapes.append(dict(
        type="rect", xref="x", yref="y",
        x0=et, x1=x1, y0=p.entry_price, y1=p.take_profit,
        fillcolor="rgba(8,153,129,0.18)", line=dict(width=0), layer="below"
    ))
    # Zone de Risco (Vermelha)
    shapes.append(dict(
        type="rect", xref="x", yref="y",
        x0=et, x1=x1, y0=p.entry_price, y1=p.stop_loss,
        fillcolor="rgba(242,54,69,0.18)", line=dict(width=0), layer="below"
    ))

    # 5. Caixa de Retângulo IFVG 1M (Estilo ICT com Nome e Preços)
    meta = getattr(p, "meta", {}) or {}
    ifvg_zone = meta.get("ifvg_zone")
    if ifvg_zone:
        top_z, bot_z = ifvg_zone
        shapes.append(dict(
            type="rect", xref="x", yref="y",
            x0=x0, x1=x1, y0=bot_z, y1=top_z,
            fillcolor="rgba(255, 152, 0, 0.35)", line=dict(color="#ff9800", width=1.5, dash="solid"), layer="below"
        ))
        anns.append(dict(
            x=x0 + timedelta(minutes=3), y=(top_z + bot_z) / 2,
            text=f"<b>1M IFVG (Inversion Gap)</b> [{bot_z:.2f} - {top_z:.2f}]",
            showarrow=False, font=dict(size=12, color="#ffffff"),
            xanchor="left", bgcolor="#ff9800", bordercolor="#ffffff", borderwidth=1
        ))

    # 6. Linha de Stop Loss e Take Profit
    shapes.append(dict(
        type="line", xref="x", yref="y",
        x0=x0, x1=x1, y0=p.stop_loss, y1=p.stop_loss,
        line=dict(color=bear_color, width=2, dash="dash")
    ))
    anns.append(dict(
        x=x1, y=p.stop_loss, text=f"  <b>STOP LOSS: {p.stop_loss:.2f}</b>",
        showarrow=False, font=dict(size=12, color=bear_color), xanchor="right"
    ))

    shapes.append(dict(
        type="line", xref="x", yref="y",
        x0=x0, x1=x1, y0=p.take_profit, y1=p.take_profit,
        line=dict(color=bull_color, width=2, dash="dash")
    ))
    anns.append(dict(
        x=x1, y=p.take_profit, text=f"  <b>TAKE PROFIT (3:1): {p.take_profit:.2f}</b>",
        showarrow=False, font=dict(size=12, color=bull_color), xanchor="right"
    ))

    ys = list(win["low"]) + list(win["high"]) + [p.stop_loss, p.take_profit, p.entry_price]
    ylo, yhi = min(ys), max(ys)
    pad_y = (yhi - ylo) * 0.06

    status_str = "WIN ✅" if p.pnl_usd > 0 else "LOSS ❌"
    title_text = (
        f"<b>Trade #{args.trade_idx}: {p.action} {args.market}</b> | Data: <b>{et.strftime('%Y-%m-%d %H:%M EST')}</b> | "
        f"Resultado: <b>{status_str} ({p.pnl_usd:+.2f} USD)</b>"
    )

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        shapes=shapes,
        annotations=anns,
        xaxis=dict(
            range=[x0, x1],
            rangeslider=dict(visible=False),
            gridcolor=grid_color,
            color=text_color,
            title="Horário (EST)"
        ),
        yaxis=dict(
            range=[ylo - pad_y, yhi + pad_y],
            gridcolor=grid_color,
            color=text_color,
            title="Preço"
        ),
        title=dict(text=title_text, font=dict(color=text_color, size=15)),
        height=750,
        margin=dict(t=80, b=40, l=50, r=50)
    )

    out_file = OUT_DIR / f"single_trade_{args.trade_idx}_{args.market}.html"
    fig.write_html(str(out_file))
    print(f"\n✅ Gráfico do Trade #{args.trade_idx} gerado com sucesso!")
    print(f"📄 Arquivo: {out_file}")


if __name__ == "__main__":
    main()
