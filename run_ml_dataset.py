"""
Gera dataset ML para treinamento XGBoost.
1. Baixa dados Binance históricos (2023-2024) — pula se já em cache
2. Roda SilverBulletNQ candle-por-candle (5 ativos × até 3 sessões)
3. Simula fill da ordem limite + outcome TP/SL
4. Extrai 20 features por sinal
5. Salva ml/data/all_signals_log.json

Uso:
    python run_ml_dataset.py
    python run_ml_dataset.py --start 2022-01-01T00:00:00Z --end 2024-12-31T23:59:59Z
    python run_ml_dataset.py --skip-download   # dados já em cache
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time as time_mod
import argparse
import numpy as np
import pandas as pd
import pytz
from pathlib import Path
from datetime import time

sys.path.insert(0, str(Path(__file__).parent))

from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
from ml.feature_extractor import extract_features

EST = pytz.timezone('America/New_York')
CACHE_DIR  = Path(__file__).parent / "data" / "cached"
OUTPUT_PATH = Path(__file__).parent / "ml" / "data" / "all_signals_log.json"

SYMBOLS    = ["ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT", "XRP/USDT:USDT", "DOGE/USDT:USDT"]
TIMEFRAMES = ["5m", "15m", "1h", "1d"]

NY_AM    = (time(10, 0), time(11, 0))
NY_LUNCH = (time(13, 0), time(14, 0))
NY_CLOSE = (time(15, 0), time(16, 0))
ASIAN    = (time(20, 0), time(23, 59))  # 8pm-midnight EST — acumulação institucional crypto

SYMBOL_SESSIONS = {
    "ETH/USDT:USDT":  [("NY_AM", *NY_AM), ("NY_LUNCH", *NY_LUNCH), ("NY_CLOSE", *NY_CLOSE), ("ASIAN", *ASIAN)],
    "SOL/USDT:USDT":  [("NY_AM", *NY_AM), ("NY_LUNCH", *NY_LUNCH), ("NY_CLOSE", *NY_CLOSE), ("ASIAN", *ASIAN)],
    "BNB/USDT:USDT":  [("NY_AM", *NY_AM), ("NY_LUNCH", *NY_LUNCH), ("ASIAN", *ASIAN)],
    "XRP/USDT:USDT":  [("NY_AM", *NY_AM), ("NY_LUNCH", *NY_LUNCH), ("NY_CLOSE", *NY_CLOSE), ("ASIAN", *ASIAN)],
    "DOGE/USDT:USDT": [("NY_AM", *NY_AM), ("ASIAN", *ASIAN)],
}

MIN_SL = {
    "ETH/USDT:USDT":  20.0,
    "SOL/USDT:USDT":  2.0,
    "BNB/USDT:USDT":  5.0,
    "XRP/USDT:USDT":  0.005,   # era 0.03 — FVGs 5m XRP tipicamente $0.002-0.010
    "DOGE/USDT:USDT": 0.001,   # era 0.004 — FVGs 5m DOGE tipicamente $0.0002-0.001
}


# ─── DATA ────────────────────────────────────────────────────────────────────

def download_symbol(symbol: str, tf: str, start: str, end: str):
    import ccxt
    safe = symbol.replace(":", "_")
    path = CACHE_DIR / f"{safe}_{tf}.parquet"
    if path.exists():
        print(f"    [cache] {safe}_{tf} já existe — pulando")
        return

    exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
    since  = exchange.parse8601(start)
    end_ts = exchange.parse8601(end)
    rows   = []
    limit  = 1000
    print(f"    [download] {symbol} {tf}", end="")

    while since < end_ts:
        try:
            batch = exchange.fetch_ohlcv(symbol, tf, since=since, limit=limit)
        except Exception as e:
            print(f"\n    [retry] {e}")
            time_mod.sleep(5)
            continue
        if not batch:
            break
        rows.extend(batch)
        since = batch[-1][0] + 1
        print(f"\r    [download] {symbol} {tf} — {len(rows)} candles", end="")
        if len(batch) < limit:
            break
        time_mod.sleep(exchange.rateLimit / 1000)

    print(f"\r    [download OK] {symbol} {tf}: {len(rows)} candles")
    if not rows:
        return

    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df[df["ts"] <= end_ts]
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["ts"])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def load_parquet(symbol: str, tf: str) -> pd.DataFrame:
    safe = symbol.replace(":", "_")
    path = CACHE_DIR / f"{safe}_{tf}.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


# ─── SIMULATION ──────────────────────────────────────────────────────────────

def simulate_outcome(df_5m: pd.DataFrame, signal_idx: int, signal) -> dict:
    """
    Retorna dict com label (1=WIN, 0=LOSS, -1=skip).
    Fill: limite toca entry dentro de 4h (48 candles × 5m).
    Exit: TP ou SL dentro de 16h (192 candles × 5m).
    """
    entry  = signal.entry_price
    sl     = signal.stop_loss
    tp     = signal.take_profit
    is_buy = signal.action == "BUY"
    n      = len(df_5m)

    fill_idx = None
    for i in range(signal_idx + 1, min(n, signal_idx + 49)):  # 4h fill window
        c = df_5m.iloc[i]
        if is_buy and c["low"] <= entry:
            fill_idx = i
            break
        elif not is_buy and c["high"] >= entry:
            fill_idx = i
            break

    if fill_idx is None:
        return {"label": -1}

    for i in range(fill_idx + 1, min(n, fill_idx + 193)):  # 16h exit window
        c = df_5m.iloc[i]
        hit_sl = c["low"] <= sl  if is_buy else c["high"] >= sl
        hit_tp = c["high"] >= tp if is_buy else c["low"]  <= tp

        if hit_sl and hit_tp:
            label = 0  # ambos no mesmo candle → assume SL (conservador)
        elif hit_sl:
            label = 0
        elif hit_tp:
            label = 1
        else:
            continue

        return {
            "label":        label,
            "bars_to_fill": fill_idx - signal_idx,
            "bars_to_exit": i - fill_idx,
            "exit_price":   sl if label == 0 else tp,
        }

    return {"label": -1}  # timeout


# ─── BACKTEST LOOP ───────────────────────────────────────────────────────────

def run_symbol_session(
    symbol: str,
    session_name: str,
    kz_start: time,
    kz_end: time,
    df_5m: pd.DataFrame,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_1d: pd.DataFrame,
) -> list:
    strategy = SilverBulletNQ(SilverBulletConfig(
        killzone_start=kz_start,
        killzone_end=kz_end,
        min_sl_distance_pts=MIN_SL[symbol],
        min_rr=2.0,
        require_daily_bias=False,       # ML vai aprender isso
        require_premium_discount=False, # ML vai aprender isso
        require_london_sweep=False,     # ML vai aprender isso
        session_name=f"{symbol.split('/')[0].lower()}_{session_name.lower()}",
    ))

    # Índice EST para filtrar killzone
    df_est = df_5m.copy()
    df_est.index = df_est.index.tz_convert(EST)

    s_min = kz_start.hour * 60 + kz_start.minute
    e_min = kz_end.hour   * 60 + kz_end.minute

    kz_indices = [
        i for i in range(50, len(df_5m))
        if s_min <= df_est.index[i].hour * 60 + df_est.index[i].minute < e_min
    ]

    asset_tag = symbol.split("/")[0]
    print(f"  [{asset_tag} {session_name}] {len(kz_indices)} candles na killzone...", flush=True)

    # Ponteiros monotônicos — O(n+m) em vez de O(n×m)
    ix15 = df_15m.index if not df_15m.empty else None
    ix1h = df_1h.index  if not df_1h.empty  else None
    ix1d = df_1d.index  if not df_1d.empty  else None
    p15 = p1h = p1d = 0

    logs = []
    for idx in kz_indices:
        current_time = df_5m.index[idx]

        h5m = df_5m.iloc[max(0, idx - 499): idx + 1]

        if ix15 is not None:
            while p15 < len(df_15m) and ix15[p15] <= current_time:
                p15 += 1
            h15m = df_15m.iloc[max(0, p15 - 200): p15]
        else:
            h15m = df_15m

        if ix1h is not None:
            while p1h < len(df_1h) and ix1h[p1h] <= current_time:
                p1h += 1
            h1h = df_1h.iloc[max(0, p1h - 200): p1h]
        else:
            h1h = df_1h

        if ix1d is not None:
            while p1d < len(df_1d) and ix1d[p1d] <= current_time:
                p1d += 1
            h1d = df_1d.iloc[max(0, p1d - 60): p1d]
        else:
            h1d = df_1d

        if len(h15m) < 5 or len(h1h) < 5 or len(h1d) < 2:
            continue

        try:
            signal = strategy.evaluate(h5m, h15m, h1h, h1d)
        except Exception:
            continue

        if signal is None or signal.action not in ("BUY", "SELL"):
            continue

        outcome = simulate_outcome(df_5m, idx, signal)
        if outcome["label"] == -1:
            continue

        feats = extract_features(
            df_5m=h5m,
            signal_idx=len(h5m) - 1,
            entry_price=signal.entry_price,
            sl_price=signal.stop_loss,
        )
        if not feats:
            continue

        logs.append({
            "symbol":       symbol,
            "session":      session_name,
            "timestamp":    str(current_time),
            "action":       signal.action,
            "entry":        signal.entry_price,
            "sl":           signal.stop_loss,
            "tp":           signal.take_profit,
            "label":        outcome["label"],
            "bars_to_fill": outcome.get("bars_to_fill"),
            "bars_to_exit": outcome.get("bars_to_exit"),
            "exit_price":   outcome.get("exit_price"),
            "features":     feats,
        })

    wins   = sum(1 for s in logs if s["label"] == 1)
    losses = sum(1 for s in logs if s["label"] == 0)
    wr     = wins / max(1, wins + losses) * 100
    print(f"    → {len(logs)} sinais | WIN {wins} LOSS {losses} WR {wr:.1f}%", flush=True)
    return logs


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start",         default="2023-01-01T00:00:00Z")
    parser.add_argument("--end",           default="2024-12-31T23:59:59Z")
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    t0 = time_mod.time()

    # ── 1. Download ───────────────────────────────────────────────────────────
    if not args.skip_download:
        print(f"\n[FASE 1] Download dados Binance | {args.start[:10]} → {args.end[:10]}")
        for sym in SYMBOLS:
            print(f"  {sym}")
            for tf in TIMEFRAMES:
                download_symbol(sym, tf, args.start, args.end)
    else:
        print("[FASE 1] Pulado (--skip-download)")

    # ── 2. Backtest ───────────────────────────────────────────────────────────
    print("\n[FASE 2] Backtest ICT candle-por-candle")
    all_signals = []
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    for symbol in SYMBOLS:
        print(f"\n  Carregando {symbol}...")
        try:
            df_5m  = load_parquet(symbol, "5m")
            df_15m = load_parquet(symbol, "15m")
            df_1h  = load_parquet(symbol, "1h")
            df_1d  = load_parquet(symbol, "1d")

            if df_5m.empty:
                print(f"  [SKIP] sem dados 5m para {symbol}")
                continue

            print(f"  {symbol}: {len(df_5m):,} candles 5m | {len(df_15m):,} 15m | "
                  f"{len(df_1h):,} 1h | {len(df_1d):,} 1d")

            for sess in SYMBOL_SESSIONS[symbol]:
                sess_name, kz_start, kz_end = sess
                logs = run_symbol_session(
                    symbol, sess_name, kz_start, kz_end,
                    df_5m, df_15m, df_1h, df_1d,
                )
                all_signals.extend(logs)

        except Exception as e:
            print(f"  [ERRO] {symbol}: {e} — pulando")
            import traceback; traceback.print_exc()

        # Salva incrementalmente após cada ativo (preserva dados se crash)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_signals, f, ensure_ascii=False, indent=2)
        print(f"  [checkpoint] {len(all_signals)} sinais salvos até agora")

    # ── 4. Relatório ──────────────────────────────────────────────────────────
    elapsed = time_mod.time() - t0
    wins   = sum(1 for s in all_signals if s["label"] == 1)
    losses = sum(1 for s in all_signals if s["label"] == 0)
    wr     = wins / max(1, wins + losses) * 100

    print(f"\n{'='*60}")
    print(f"[RESULTADO] {len(all_signals)} sinais | WIN {wins} LOSS {losses} | WR {wr:.1f}% | {elapsed:.0f}s")
    print(f"  Salvo em: {OUTPUT_PATH}")

    # Por ativo
    from collections import Counter
    by_sym = Counter(s["symbol"].split("/")[0] for s in all_signals)
    print("\n  Por ativo:")
    for sym_tag, cnt in sorted(by_sym.items(), key=lambda x: -x[1]):
        ss = [s for s in all_signals if s["symbol"].split("/")[0] == sym_tag]
        w  = sum(1 for s in ss if s["label"] == 1)
        l  = sum(1 for s in ss if s["label"] == 0)
        print(f"    {sym_tag:<6}: {cnt:>4} | WIN {w:>3} LOSS {l:>3} | WR {w/max(1,w+l)*100:.1f}%")

    print()
    if len(all_signals) >= 100:
        print("[OK] Dataset suficiente. Treinar modelo:")
        print("     python ml/train.py")
    elif len(all_signals) >= 30:
        print("[AVISO] Dataset marginal (30-99). Modelo treinável mas WC pode ser ruidoso.")
        print("     python ml/train.py")
    else:
        print("[CRITICO] Poucos sinais (<30). Verificar calibragem da estratégia ou expandir período.")


if __name__ == "__main__":
    main()
