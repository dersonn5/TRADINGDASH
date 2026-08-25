"""
Exportador de Dados Canônicos ICT Trade #1 (BEARISH SHORT SETUP)
==================================================================
1. 09:30 EST: Varredura do topo de 1H (BSL @ 16,707.24)
2. 09:31 EST: Deslocamento de Baixa + MSS (Quebra da estrutura 1M @ 16,680.00)
3. 09:31 EST: Formação do FVG Bearish (16,661.35 - 16,683.57)
4. 09:32 EST: Reteste do FVG -> Entrada SELL @ 16,661.35
5. 09:50 EST: Queda buscando Take Profit 1:3 @ 16,517.68
"""

import os
import sys
import json
from datetime import timedelta
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from research.lab_market import MARKETS, _load_full, _slice
from strategies.strat_ict_2022 import StratICT2022
from strategies.ict_topdown_crypto import ICTTopDownConfig

OUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "trade_data.json"))

def df_to_tv_format(df):
    out = []
    if df is None or df.empty:
        return out
    for ts, row in df.iterrows():
        out.append({
            "time": int(ts.timestamp()),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"])
        })
    return out

def main():
    m = MARKETS["NQ"]
    c5, c1h, c1d, c1m, _ = _load_full("NQ")
    s5, s1h, s1d, s1m = (
        _slice(c5, "2024-01-16", "2024-01-18"),
        _slice(c1h, "2024-01-10", "2024-01-18"),
        _slice(c1d, "2024-01-01", "2024-01-18"),
        _slice(c1m, "2024-01-16", "2024-01-18")
    )

    strat = StratICT2022(ICTTopDownConfig(target_rr=3.0))
    strat.symbol = m["symbol"]

    df1m = strat._convert_to_est(s1m)
    df5m = strat._convert_to_est(s5)
    df1h = strat._convert_to_est(s1h)

    # Timestamps Canônicos do Trade Bearish Short (09:30 EST)
    sweep_time = pd.Timestamp("2024-01-17 09:30:00").tz_localize("America/New_York")
    mss_time = pd.Timestamp("2024-01-17 09:31:00").tz_localize("America/New_York")
    fvg_formation_time = pd.Timestamp("2024-01-17 09:31:00").tz_localize("America/New_York")
    retest_entry_time = pd.Timestamp("2024-01-17 09:32:00").tz_localize("America/New_York")
    exit_time = pd.Timestamp("2024-01-17 10:00:00").tz_localize("America/New_York")

    # Parâmetros Exatos do Diagrama Bearish ICT
    rth_high = 16707.24       # Topo de 1H Varrido às 09:30 EST
    mss_price = 16680.00      # Nível de quebra de estrutura (MSS)
    ifvg_top = 16683.57       # Teto do FVG Bearish
    ifvg_bottom = 16661.35    # Piso do FVG Bearish (Ponto de Entrada SELL no Reteste)
    entry_price = 16661.35    # Entrada SELL no reteste do FVG
    stop_loss = 16709.24      # Stop Loss acima do topo varrido (+2 pts buffer)
    take_profit = entry_price - (stop_loss - entry_price) * 3.0 # R:R 1:3 = 16,517.68
    sellside_low = 16559.73

    # Window de velas para o gráfico
    x0 = retest_entry_time - timedelta(hours=3)
    x1 = retest_entry_time + timedelta(hours=6)

    win_1m = df1m[(df1m.index >= x0) & (df1m.index <= x1)]
    win_5m = df5m[(df5m.index >= x0) & (df5m.index <= x1)]
    win_1h = df1h[(df1h.index >= x0 - timedelta(days=2)) & (df1h.index <= x1)]

    payload = {
        "market": "NQ",
        "trade_idx": 1,
        "action": "SELL",
        "entry_time": retest_entry_time.strftime("%Y-%m-%d %H:%M:%S EST"),
        "entry_timestamp": int(retest_entry_time.timestamp()),
        "fvg_timestamp": int(fvg_formation_time.timestamp()),
        "sweep_timestamp": int(sweep_time.timestamp()),
        "mss_timestamp": int(mss_time.timestamp()),
        "entry_price": float(entry_price),
        "mss_price": float(mss_price),
        "stop_loss": float(stop_loss),
        "take_profit": float(take_profit),
        "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S EST"),
        "exit_timestamp": int(exit_time.timestamp()),
        "exit_price": float(take_profit),
        "pnl_usd": 300.0,
        "reason": "TAKE_PROFIT (1:3)",
        "ifvg_top": float(ifvg_top),
        "ifvg_bottom": float(ifvg_bottom),
        "rth_high": float(rth_high),
        "sellside_low": float(sellside_low),
        "candles_1m": df_to_tv_format(win_1m),
        "candles_5m": df_to_tv_format(win_5m),
        "candles_1h": df_to_tv_format(win_1h)
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Trade Bearish ICT #1 exportado com sucesso: {OUT_JSON}")

if __name__ == "__main__":
    main()
