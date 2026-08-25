"""
Gate trace: runs the XAU Lunch strategy on actual Lunch candles
and prints which gate kills the signal.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data.data_loader import DataLoader
from strategies.session_configs import make_sb_xau_lunch

loader = DataLoader()
data = {
    "5m": loader.load_data("C:XAUUSD", "5m", "2026-04-19", "2026-05-19"),
    "15m": loader.load_data("C:XAUUSD", "15m", "2026-04-19", "2026-05-19"),
    "1h": loader.load_data("C:XAUUSD", "1h", "2026-04-19", "2026-05-19"),
    "1d": loader.load_data("C:XAUUSD", "1d", "2026-04-19", "2026-05-19"),
}

df_5m = data["5m"]
if df_5m.index.tz is None:
    df_5m.index = df_5m.index.tz_localize("UTC").tz_convert("America/New_York")
else:
    df_5m.index = df_5m.index.tz_convert("America/New_York")

strat = make_sb_xau_lunch()
strat.diagnostic_enabled = True

lunch_indices = [i for i in range(50, len(df_5m)) if df_5m.index[i].hour == 13]
print(f"Total lunch candles: {len(lunch_indices)}")

# Test several candles and print their gate traces
test_indices = lunch_indices[::30][:5]  # every 30th candle, max 5
for i in test_indices:
    hist = df_5m.iloc[: i + 1]
    t = hist.index[-1]
    strat._reset_gates()
    sig = strat.evaluate(
        candles_5m=hist,
        candles_15m=data["15m"],
        candles_1h=data["1h"],
        candles_1d=data["1d"],
    )
    print(f"\n=== Candle: {t} ===")
    print(f"Signal: {sig}")
    gate_log = getattr(strat, "last_gates", [])
    for g in gate_log:
        status = "PASS" if g.get("passed") else "FAIL"
        name = g.get("name", "?")
        value = g.get("value", "?")
        reason = g.get("reason", "?")
        print(f"  [{status}] {name} | val={value} | reason={reason}")

# Count which gate kills most often
from collections import Counter
first_fail_counter = Counter()
for i in lunch_indices:
    hist = df_5m.iloc[: i + 1]
    strat._reset_gates()
    strat.evaluate(
        candles_5m=hist,
        candles_15m=data["15m"],
        candles_1h=data["1h"],
        candles_1d=data["1d"],
    )
    gate_log = getattr(strat, "last_gates", [])
    for g in gate_log:
        if not g.get("passed"):
            first_fail_counter[g.get("name", "?")] += 1
            break

print("\n\n=== Distribution of first killer gate (across all lunch candles) ===")
for gate, count in first_fail_counter.most_common():
    print(f"  {gate}: {count}")
