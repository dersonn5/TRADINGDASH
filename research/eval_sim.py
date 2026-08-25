"""
Simulador de Eval de Prop Firm + Escala (Monte Carlo)
======================================================
Usa a sequência REAL de trades do portfólio (cache, R-multiples) e simula a
avaliação de uma conta 25k (alvo +$1.500, trailing drawdown), variando o risco
por trade. Descobre:
  - Probabilidade de PASSAR (por nível de risco)
  - Quantas evals comprar p/ ter 10 contas aprovadas
  - Renda mensal esperada com 10 contas funded (NQ+ES+ouro)

Preserva os STREAKS (janelas contíguas aleatórias) — o drawdown é o que mata.

Uso:  python -m research.eval_sim
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

# Parâmetros da eval (estilo Apex 25k) — ajustáveis
ACCOUNT = 25000
PROFIT_TARGET = 1500.0      # +6%
TRAILING_DD = 1500.0        # perda máx (trailing a partir do pico)
TRIALS = 4000
MAX_TRADES = 400            # ~14 meses de trades
TRADES_PER_MONTH = 1024 / 36.0
PAYOUT_SPLIT = 0.90


def load_R():
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    # ordena cronologicamente pra preservar streaks reais
    raw.sort(key=lambda x: str(x["exit"]))
    return [t["r"] for t in raw]


def simulate_eval(R, risk_usd):
    """Retorna (pass_rate, mediana_trades_p/_passar)."""
    n = len(R)
    passes = 0
    days = []
    for _ in range(TRIALS):
        start = random.randint(0, n - 1)
        bal = 0.0            # lucro acumulado
        peak = 0.0
        for k in range(MAX_TRADES):
            r = R[(start + k) % n]
            bal += r * risk_usd
            peak = max(peak, bal)
            # trailing DD: falha se cair TRAILING_DD abaixo do pico
            if bal <= peak - TRAILING_DD:
                break
            if bal >= PROFIT_TARGET:
                passes += 1
                days.append(k + 1)
                break
    pr = passes / TRIALS
    md = sorted(days)[len(days) // 2] if days else None
    return pr, md


def main():
    if not CACHE.exists():
        print("[erro] rode 'python -m research.portfolio --rebuild' antes (gera o cache).")
        return
    R = load_R()
    print("=" * 62)
    print(f"  SIMULADOR EVAL 25k — alvo +${PROFIT_TARGET:.0f} | trailing DD ${TRAILING_DD:.0f}")
    print(f"  Sistema: {len(R)} trades reais (NQ+ES+ouro), {TRIALS} simulações Monte Carlo")
    print("=" * 62)
    print(f"  {'risco/trade':<14}{'PASS %':>9}{'mediana trades':>16}{'~meses p/ passar':>18}")
    print("  " + "-" * 56)
    best = None
    for risk in (50, 75, 100, 125, 150, 200):
        pr, md = simulate_eval(R, risk)
        meses = md / TRADES_PER_MONTH if md else None
        print(f"  ${risk:<13}{pr*100:>8.1f}%{(md if md else '-'):>16}{(f'{meses:.1f}' if meses else '-'):>18}")
        if best is None or pr > best[1]:
            best = (risk, pr, md)
    print("  " + "-" * 56)

    risk, pr, md = best
    print(f"\n  MELHOR: risco ${risk}/trade → {pr*100:.1f}% de aprovação")

    # Escala p/ 10 contas
    if pr > 0:
        evals_needed = round(10 / pr)
        print(f"\n  === ESCALA PARA 10 CONTAS 25k ===")
        print(f"  A {pr*100:.0f}% de aprovação, pra ter ~10 aprovadas: comprar ~{evals_needed} evals")
        print(f"  Custo estimado evals (~$50 c/ desconto): ~${evals_needed*50}")
        # renda mensal com 10 funded
        exp_R = sum(R) / len(R)
        month_per_acc = TRADES_PER_MONTH * exp_R * risk * PAYOUT_SPLIT
        print(f"\n  === RENDA COM 10 CONTAS FUNDED (risco ${risk}/trade) ===")
        print(f"  Expectância: {exp_R:.3f}R/trade | ~{TRADES_PER_MONTH:.0f} trades/mês")
        print(f"  Por conta: ~${month_per_acc:.0f}/mês (após split {PAYOUT_SPLIT*100:.0f}%)")
        print(f"  10 contas: ~${month_per_acc*10:.0f}/mês  (~${month_per_acc*10*12:.0f}/ano)")
    print("\n  (Estimativa. Real depende de execução maker, regras da firma e forward-test.)")


if __name__ == "__main__":
    main()
