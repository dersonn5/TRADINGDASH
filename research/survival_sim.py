"""
Simulador de Sobrevivência da Conta Funded (PA) — quão conservador p/ não quebrar
================================================================================
Modela a conta funded 25k com trailing DD que TRAVA após ganhar o colchão
(estilo Apex: trailing sobe até +$100 do start, depois trava). Simula 1 ano
de trading (Monte Carlo, trades reais) por nível de risco e mostra:
  - P(quebrar no ano)  ← queremos MUITO baixa
  - Renda líquida/ano (após split)

Verdade: nenhum risco > 0 garante "nunca quebrar". Mas dá p/ P(quebra) ~2-5%.

Uso:  python -m research.survival_sim
"""
import os
import sys
import json
import random
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CACHE = Path(__file__).resolve().parent / "portfolio_trades_cache.json"
DD = 1500.0            # trailing drawdown 25k (Apex)
LOCK = 100.0           # trava quando o trailing atinge start + $100
TRADES_YEAR = int(1024 / 36 * 12)   # ~341 trades/ano
TRIALS = 5000
PAYOUT = 0.90


def load_R():
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    raw.sort(key=lambda x: str(x["exit"]))
    return [t["r"] for t in raw]


def sim_year(R, risk, daily_stop_R=None):
    """1 ano. Retorna (quebrou?, lucro_liquido_R_total)."""
    n = len(R)
    start = random.randint(0, n - 1)
    profit = 0.0
    peak = 0.0
    for k in range(TRADES_YEAR):
        r = R[(start + k) % n]
        profit += r * risk
        peak = max(peak, profit)
        floor = min(peak - DD, LOCK)   # trailing que trava em +LOCK
        if profit <= floor:
            return True, profit
    return False, profit


def main():
    if not CACHE.exists():
        print("[erro] rode 'python -m research.portfolio --rebuild' primeiro.")
        return
    R = load_R()
    print("=" * 66)
    print(f"  SOBREVIVÊNCIA CONTA FUNDED 25k — trailing DD ${DD:.0f} (trava em +${LOCK:.0f})")
    print(f"  {len(R)} trades reais | {TRIALS} anos simulados | ~{TRADES_YEAR} trades/ano")
    print("=" * 66)
    print(f"  {'risco/trade':<14}{'P(quebrar/ano)':>16}{'lucro médio/ano':>18}{'por conta líq':>16}")
    print("  " + "-" * 62)
    for risk in (25, 40, 50, 75, 100):
        blows = 0
        profits = []
        for _ in range(TRIALS):
            b, p = sim_year(R, risk)
            if b:
                blows += 1
            else:
                profits.append(p)
        pblow = blows / TRIALS
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        liq = avg_profit * PAYOUT
        print(f"  ${risk:<13}{pblow*100:>15.1f}%{avg_profit:>+18.0f}{liq:>+16.0f}")
    print("  " + "-" * 62)
    print("\n  10 contas (copy, MESMO robô) = os resultados são CORRELACIONADOS:")
    print("  se quebrar, várias quebram JUNTAS. P(quebra) baixa protege TODAS.")
    print("  Renda 10 contas ~ 10x 'por conta líq' (menos taxas mensais/consistência).")


if __name__ == "__main__":
    main()
