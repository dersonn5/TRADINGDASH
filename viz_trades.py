"""
Visualizador de Trades — estilo TradingView (Plotly HTML), formato SLIDE
========================================================================
Tema claro, zoom apertado por trade, e dropdown para escolher o trade na lista.
Desenha o CENÁRIO que originou a entrada (não só a entrada):
  - Array HTF (banda), nível de liquidez varrido (sweep), swings, equilíbrio
  - FVG de 1m da entrada, caixas Risk/Reward, entrada/saída, score de qualidade

Uso:
    python viz_trades.py --strategy ict_topdown --symbol BTC/USDT:USDT --start 2024-01-01 --end 2024-03-31 --max 30
"""
import os
import sys
import argparse
from datetime import timedelta
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import plotly.graph_objects as go

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from run_crypto_backtest_brain import build_strategy, load_candles

REPORTS = Path(__file__).resolve().parent / "backtesting" / "reports"


def to_est(df):
    if df is None or df.empty:
        return df
    d = df.copy()
    if not isinstance(d.index, pd.DatetimeIndex):
        d.index = pd.to_datetime(d.index)
    d.index = d.index.tz_localize("UTC").tz_convert("America/New_York") if d.index.tz is None \
        else d.index.tz_convert("America/New_York")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="ict_topdown")
    ap.add_argument("--symbol", default="BTC/USDT:USDT")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-03-31")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--pad", type=int, default=36, help="velas 5m antes da entrada (zoom)")
    ap.add_argument("--padr", type=int, default=12, help="velas 5m após a saída")
    args = ap.parse_args()

    loader = DataLoader()
    need_1m = args.strategy in ("ict_topdown",)
    data = load_candles(loader, args.symbol, args.start, args.end, need_1m=need_1m)
    if data is None:
        print("[ERRO] sem dados"); return
    c5, c15, c1h, c1d, c1m = data
    corr = "BTC/USDT:USDT" if args.symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    try:
        c5_corr = loader.load_data(corr, "5m", args.start, args.end)
    except Exception:
        c5_corr = None

    strat = build_strategy(args.symbol, args.strategy)
    tick = 0.1 if args.symbol == "BTC/USDT:USDT" else 0.01
    eng = BacktestEngine(BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0,
                                        commission_usd=1.0, enable_break_even=True, break_even_trigger_rr=2.0,
                                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5))
    res = eng.run(strategy=strat, candles_5m=c5, candles_15m=c15, candles_1h=c1h, candles_1d=c1d,
                  candles_1m=c1m, use_filters=False, candles_5m_corr=c5_corr)
    positions = res["positions"][:args.max]
    print(f"[VIZ] {len(positions)} trades.")
    if not positions:
        print("[VIZ] nenhum trade."); return

    df5 = to_est(c5)
    fig = go.Figure()
    per_trade = []  # (visible_idx_list, shapes, annotations, xrange, yrange, title)

    for i, p in enumerate(positions):
        et = pd.Timestamp(p.entry_time)
        if et.tzinfo is None:
            et = et.tz_localize("America/New_York")
        xt = pd.Timestamp(p.exit_time) if p.exit_time is not None else et + timedelta(hours=6)
        if xt.tzinfo is None:
            xt = xt.tz_localize("America/New_York")
        x0 = et - timedelta(minutes=5 * args.pad)
        x1 = xt + timedelta(minutes=5 * args.padr)
        win = df5[(df5.index >= x0) & (df5.index <= x1)]
        if win.empty:
            per_trade.append(None); continue

        base = len(fig.data)
        fig.add_trace(go.Candlestick(x=win.index, open=win["open"], high=win["high"], low=win["low"],
                                     close=win["close"], showlegend=False, visible=(i == 0),
                                     increasing_line_color="#089981", decreasing_line_color="#f23645",
                                     name="price"))
        fig.add_trace(go.Scatter(x=[et], y=[p.entry_price], mode="markers", visible=(i == 0),
                                 marker=dict(symbol="triangle-up" if p.action == "BUY" else "triangle-down",
                                             size=14, color="#2962ff", line=dict(width=1, color="#fff")),
                                 showlegend=False, name="entry"))
        fig.add_trace(go.Scatter(x=[xt], y=[p.exit_price if p.exit_price else p.entry_price], mode="markers",
                                 visible=(i == 0),
                                 marker=dict(symbol="x", size=12,
                                             color="#089981" if p.pnl_usd > 0 else "#f23645"),
                                 showlegend=False, name="exit"))
        vis_idx = [base, base + 1, base + 2]

        m = p.meta or {}
        rr = abs(p.take_profit - p.entry_price) / abs(p.entry_price - p.stop_loss) \
            if abs(p.entry_price - p.stop_loss) > 0 else 0.0
        shapes, anns = [], []

        def rect(y0, y1, color, x_start=x0, x_end=x1):
            shapes.append(dict(type="rect", xref="x", yref="y", x0=x_start, x1=x_end, y0=y0, y1=y1,
                               fillcolor=color, line=dict(width=0), layer="below"))

        def hline(y, color, dash="dot", w=1):
            shapes.append(dict(type="line", xref="x", yref="y", x0=x0, x1=x1, y0=y, y1=y,
                               line=dict(color=color, width=w, dash=dash)))

        # Reward / Risk (entrada -> alvo / -> stop) só da entrada em diante
        rect(p.entry_price, p.take_profit, "rgba(8,153,129,0.12)", x_start=et)
        rect(p.entry_price, p.stop_loss, "rgba(242,54,69,0.12)", x_start=et)
        # Array HTF (banda azul) — o contexto institucional
        arr = m.get("htf_array")
        if arr:
            rect(arr["bottom"], arr["top"], "rgba(41,98,255,0.10)")
            anns.append(dict(x=x0, y=arr["top"], text=f"HTF {arr['tf']} {arr['kind']}", showarrow=False,
                             font=dict(size=10, color="#2962ff"), xanchor="left"))
        # FVG de 1m da entrada (laranja)
        fvg = m.get("fvg_1m")
        if fvg:
            rect(fvg["bottom"], fvg["top"], "rgba(255,152,0,0.20)")
            anns.append(dict(x=et, y=fvg["top"], text="FVG 1m (entrada)", showarrow=False,
                             font=dict(size=10, color="#e65100"), xanchor="left",
                             bgcolor="rgba(255,243,224,0.9)"))
        # linhas: entrada, SL, TP
        hline(p.entry_price, "#2962ff", "solid")
        hline(p.stop_loss, "#f23645")
        hline(p.take_profit, "#089981")
        # LIQUIDEZ LOCAL VARRIDA (o que originou o setup) — linha + marcador + nome
        swl = m.get("swept_local")
        if swl:
            hline(swl, "#9c27b0", "dash")
            anns.append(dict(x=et, y=swl, text="◄ liquidez varrida (sweep)", showarrow=True, arrowhead=2,
                             ax=40, ay=0, font=dict(size=11, color="#9c27b0"), xanchor="left",
                             bgcolor="rgba(243,229,245,0.9)"))
        # MSS — swing rompido (quebra de estrutura)
        mss = m.get("mss_level")
        if mss:
            hline(mss, "#00897b", "dot")
            anns.append(dict(x=et, y=mss, text="◄ MSS (estrutura rompida)", showarrow=True, arrowhead=2,
                             ax=40, ay=0, font=dict(size=11, color="#00897b"), xanchor="left",
                             bgcolor="rgba(224,242,241,0.9)"))
        if m.get("equilibrium"):
            hline(m["equilibrium"], "#bbb", "dashdot")
            anns.append(dict(x=x0, y=m["equilibrium"], text="equilíbrio", showarrow=False,
                             font=dict(size=9, color="#999"), xanchor="left"))
        # rótulos R:R / qualidade
        anns.append(dict(x=x1, y=p.take_profit, text=f"TP {p.take_profit:.0f} · RR {rr:.1f}", showarrow=False,
                         font=dict(size=11, color="#089981"), xanchor="right"))
        anns.append(dict(x=x1, y=p.stop_loss, text=f"SL {p.stop_loss:.0f}", showarrow=False,
                         font=dict(size=11, color="#f23645"), xanchor="right"))
        ys = list(win["low"]) + list(win["high"]) + [p.stop_loss, p.take_profit, p.entry_price]
        ylo, yhi = min(ys), max(ys)
        pad_y = (yhi - ylo) * 0.05
        res_txt = "WIN" if p.pnl_usd > 0 else "LOSS"
        conf = m.get("confluences", {})
        hit = ",".join(k for k, v in conf.items() if v) if conf else ""
        title = (f"#{i+1} {p.action} {et.strftime('%Y-%m-%d %H:%M')} · {res_txt} {p.pnl_usd:+.0f} USD · "
                 f"qualidade {m.get('quality_grade','?')} ({m.get('quality_score','?')}) · RR {rr:.1f}<br>"
                 f"<span style='font-size:11px'>confluências: {hit}</span>")
        per_trade.append((vis_idx, shapes, anns, [x0, x1], [ylo - pad_y, yhi + pad_y], title))

    total_traces = len(fig.data)
    valid = [(i, t) for i, t in enumerate(per_trade) if t]
    buttons = []
    for i, t in valid:
        vis_idx, shapes, anns, xr, yr, title = t
        vis = [False] * total_traces
        for vi in vis_idx:
            vis[vi] = True
        buttons.append(dict(label=f"#{i+1}", method="update",
                            args=[{"visible": vis},
                                  {"shapes": shapes, "annotations": anns,
                                   "xaxis.range": xr, "yaxis.range": yr, "title.text": title}]))

    first = valid[0][1]
    fig.update_layout(
        template="plotly_white",
        updatemenus=[dict(buttons=buttons, direction="down", x=0, xanchor="left", y=1.18, yanchor="top",
                          showactive=True, bgcolor="#fff", bordercolor="#ccc")],
        shapes=first[1], annotations=first[2],
        xaxis=dict(range=first[3], rangeslider=dict(visible=False)),
        yaxis=dict(range=first[4]),
        title=dict(text=first[5]),
        height=720, margin=dict(t=120),
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    safe = args.symbol.split("/")[0]
    out = REPORTS / f"viz_{args.strategy}_{safe}_{args.start}_{args.end}.html"
    fig.write_html(str(out))
    print(f"[VIZ] salvo: {out}")


if __name__ == "__main__":
    main()
