"""
Robustez temporal (walk-forward por blocos)
============================================
Roda uma config FIXA em blocos consecutivos de tempo (ex: semestres) em BTC+ETH,
com funding de perp incluído. Mostra se o edge é CONSISTENTE no tempo ou
concentrado em poucos períodos de sorte.

Veredito: % de blocos com PF>1 e PnL+. Edge robusto = maioria dos blocos positivos.

Uso:
    python -m research.robustness
"""
import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab import _run_window, clamp

# Config otimizada pelo agente (validada cross-asset)
BEST = {"min_score": 58, "displacement_atr": 0.95, "pd_tolerance": 0.08}

# Blocos semestrais 2022-2024
BLOCKS = [
    ("2022-01-01", "2022-06-30"), ("2022-07-01", "2022-12-31"),
    ("2023-01-01", "2023-06-30"), ("2023-07-01", "2023-12-31"),
    ("2024-01-01", "2024-06-30"), ("2024-07-01", "2024-12-31"),
]
SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT"]


def main():
    ov = clamp(BEST)
    print("=" * 70)
    print("  ROBUSTEZ TEMPORAL (walk-forward por blocos, com funding)")
    print(f"  Config: {ov}")
    print("=" * 70)
    print(f"\n  {'BLOCO':<24}{'SYM':<5}{'trades':>7}{'win%':>7}{'PF':>7}{'PnL':>9}{'DD%':>7}")
    print("  " + "-" * 64)

    rows = []
    pos_blocks = 0
    total_blocks = 0
    for (s, e) in BLOCKS:
        for sym in SYMBOLS:
            try:
                m = _run_window(ov, sym, s, e)
            except Exception as ex:
                print(f"  [ERRO] {sym} {s}: {str(ex)[:60]}")
                continue
            pf = m["profit_factor"]
            pnl = m["total_pnl_usd"]
            lbl = f"{s[:7]}..{e[5:7]}"
            print(f"  {lbl:<24}{sym[:3]:<5}{m['total_trades']:>7}{m['win_rate']:>7.1f}"
                  f"{pf:>7.2f}{pnl:>+9.0f}{m['max_drawdown_percent']:>7.1f}")
            rows.append({"block": lbl, "sym": sym[:3], **{k: round(m[k], 2) for k in
                        ("total_trades", "win_rate", "profit_factor", "total_pnl_usd", "max_drawdown_percent")}})
            total_blocks += 1
            if pf > 1.0 and pnl > 0:
                pos_blocks += 1

    print("  " + "-" * 64)
    pct = 100 * pos_blocks / max(1, total_blocks)
    print(f"\n  Blocos positivos: {pos_blocks}/{total_blocks} ({pct:.0f}%)")
    if pct >= 70:
        print("  ✅ ROBUSTO — edge consistente ao longo do tempo e dos ativos.")
    elif pct >= 50:
        print("  ⚠️  PARCIAL — edge existe mas tem períodos fracos. Aceitável com risco baixo.")
    else:
        print("  ❌ FRÁGIL — edge concentrado em poucos períodos. Cuidado.")

    out = os.path.join(os.path.dirname(__file__), "robustness.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"config": ov, "rows": rows, "pos_blocks": pos_blocks, "total": total_blocks}, f, indent=1)
    print(f"  log: {out}")


if __name__ == "__main__":
    main()
