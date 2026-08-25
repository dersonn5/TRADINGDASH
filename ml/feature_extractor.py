"""
20 features de contexto de mercado para classificação XGBoost.
Agnóstico de ativo — funciona para BTC, ETH, SOL, etc.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Optional
import pytz

EST = pytz.timezone('America/New_York')

FEATURE_NAMES = [
    "hour", "day_of_week",
    "atr_14", "atr_pct", "volatility_20",
    "fvg_size_pts", "fvg_size_atr", "fvg_age_candles", "displacement_ratio",
    "sl_distance_pts", "sl_distance_atr",
    "rsi_14", "trend_1h", "trend_4h",
    "body_to_range_ratio", "volume_ratio",
    "price_vs_asian_pct", "distance_pdh_pct", "distance_pdl_pct",
    "london_swept",
]


def extract_features(
    df_5m: pd.DataFrame,
    signal_idx: int,
    entry_price: float,
    sl_price: float,
    fvg_size: float = 0.0,
    fvg_age_candles: int = 1,
    displacement_ratio: float = 0.5,
    asian_high: Optional[float] = None,
    asian_low: Optional[float] = None,
    pdh: Optional[float] = None,
    pdl: Optional[float] = None,
    london_swept: bool = False,
) -> dict:
    window = df_5m.iloc[max(0, signal_idx - 49): signal_idx + 1]
    if len(window) < 10:
        return {}

    closes = window["close"].values
    highs  = window["high"].values
    lows   = window["low"].values
    vols   = window["volume"].values
    current = window.iloc[-1]
    price = float(current["close"])

    # ATR(14)
    n = len(window)
    trs = []
    for i in range(1, n):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    atr_14 = float(np.mean(trs[-14:])) if len(trs) >= 14 else float(np.mean(trs)) if trs else 1.0

    # RSI(14)
    c_slice = closes[-16:] if len(closes) >= 16 else closes
    deltas = np.diff(c_slice)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_g  = np.mean(gains)  if gains.size  > 0 else 1e-10
    avg_l  = np.mean(losses) if losses.size > 0 else 1e-10
    rsi = 100.0 - (100.0 / (1.0 + avg_g / max(avg_l, 1e-10)))

    # Timestamp in EST
    ts = window.index[-1]
    if hasattr(ts, 'tz') and ts.tz is not None:
        ts_est = ts.astimezone(EST)
    else:
        ts_est = ts
    hour       = ts_est.hour       if hasattr(ts_est, 'hour')       else 10
    day_of_week = ts_est.dayofweek if hasattr(ts_est, 'dayofweek') else 0

    # Trends
    trend_1h = float((closes[-1] - closes[-12]) / closes[-12]) if len(closes) >= 12 and closes[-12] != 0 else 0.0
    trend_4h = float((closes[-1] - closes[-48]) / closes[-48]) if len(closes) >= 48 and closes[-48] != 0 else 0.0

    # Body/range
    body = abs(float(current["close"]) - float(current["open"]))
    rng  = float(current["high"]) - float(current["low"])
    btr  = body / rng if rng > 0 else 0.0

    # Volume
    avg_vol   = float(np.mean(vols[-20:])) if len(vols) >= 20 else 1.0
    vol_ratio = float(vols[-1]) / avg_vol if avg_vol > 0 else 1.0

    # Asian range position
    if asian_high is not None and asian_low is not None and asian_high != asian_low:
        price_vs_asian = (price - asian_low) / (asian_high - asian_low)
    else:
        price_vs_asian = 0.5

    # PDH/PDL
    dist_pdh = (pdh - price) / price if pdh and price > 0 else 0.0
    dist_pdl = (price - pdl) / price if pdl and price > 0 else 0.0

    sl_dist = abs(entry_price - sl_price)
    if fvg_size <= 0:
        fvg_size = sl_dist  # fallback proxy

    return {
        "hour":                 hour,
        "day_of_week":          day_of_week,
        "atr_14":               round(atr_14, 6),
        "atr_pct":              round(atr_14 / price if price > 0 else 0.0, 6),
        "volatility_20":        round(float(np.std(closes[-20:]) / price) if len(closes) >= 20 and price > 0 else 0.0, 6),
        "fvg_size_pts":         round(fvg_size, 6),
        "fvg_size_atr":         round(fvg_size / atr_14 if atr_14 > 0 else 0.0, 6),
        "fvg_age_candles":      fvg_age_candles,
        "displacement_ratio":   round(displacement_ratio, 4),
        "sl_distance_pts":      round(sl_dist, 6),
        "sl_distance_atr":      round(sl_dist / atr_14 if atr_14 > 0 else 0.0, 4),
        "rsi_14":               round(float(rsi), 2),
        "trend_1h":             round(trend_1h, 6),
        "trend_4h":             round(trend_4h, 6),
        "body_to_range_ratio":  round(btr, 4),
        "volume_ratio":         round(vol_ratio, 4),
        "price_vs_asian_pct":   round(price_vs_asian, 4),
        "distance_pdh_pct":     round(dist_pdh, 6),
        "distance_pdl_pct":     round(dist_pdl, 6),
        "london_swept":         int(london_swept),
    }


def features_to_array(features: dict) -> "np.ndarray":
    import numpy as np
    return np.array([features[k] for k in FEATURE_NAMES], dtype=np.float32)
