"""
Simulação Apex 25k COM TODOS OS CUSTOS — passa? rende? (10 contas)
==================================================================
Params reais Apex 25k: alvo +$1500, trailing DD $1500 (EOD), consistência 50%,
split 100% nos primeiros $25k depois 90%, eval $19.90/mês (cupom), min payout $500.

Monte Carlo com trades reais (cache). Mostra, líquido de custos:
  - Pass rate + custo de eval até passar
  - Renda anual por conta funded (após split + consistência)
  - Plano 10 contas: custo total + renda total

Uso:  python -m research.apex_sim
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
TARGET = 1500.0
DD = 1500.0
EVAL_FEE_MONTH = 19.90       # cupom 90%
CONSISTENCY = 0.50           # nenhum "dia" > 50% do lucro
TRADES_MONTH = 1024 / 36.0
TRADES_YEAR = int(TRADES_MONTH * 12)
TRIALS = 5000
FIRST_100PCT = 25000.0       # 100% split nos primeiros $25k de saque


def load_R():
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    raw.sort(key=lambda x: str(x["exit"]))
    # agrupa em "dias" ~ a cada 1.3 trades (aprox) — simplificação p/ consistência
    return [t["r"] for t in raw]


def sim_eval(R, risk):
    """Passou? em quantos trades? respeitando consistência 50% (nenhum trade > 50% do alvo)."""
    n = len(R)
    start = random.randint(0, n - 1)
    profit = 0.0; peak = 0.0; maxday = 0.0
    for k in range(400):
        pnl = R[(start + k) % n] * risk
        profit += pnl; peak = max(peak, profit)
        if pnl > 0:
            maxday = max(maxday, pnl)
        if profit <= peak - DD:
            return False, k
        if profit >= TARGET:
            # consistência: maior ganho isolado não pode ser > 50% do lucro
            if maxday <= CONSISTENCY * profit:
                return True, k + 1
            return False, k  # passou o alvo mas viola consistência → precisa mais dias (falha simplificada)
    return False, 400


def sim_funded_year(R, risk):
    n = len(R); start = random.randint(0, n - 1)
    profit = 0.0; peak = 0.0
    for k in range(TRADES_YEAR):
        profit += R[(start + k) % n] * risk; peak = max(peak, profit)
        if profit <= min(peak - DD, 100.0):
            return None  # quebrou
    return profit


def main():
    if not CACHE.exists():
        print("[erro] rode 'python -m research.portfolio --rebuild' primeiro."); return
    R = load_R()
    print("=" * 66)
    print("  APEX 25k COM CUSTOS REAIS — passa? rende? (trades reais NQ+ES+ouro)")
    print("=" * 66)
    print(f"  {'risco':<8}{'PASS%':>8}{'~meses':>9}{'evalCusto':>11}{'renda/ano líq':>16}{'quebra%':>9}")
    print("  " + "-" * 60)
    results = {}
    for risk in (40, 50, 75, 100):
        # eval
        passes = 0; months = []
        for _ in range(TRIALS):
            ok, k = sim_eval(R, risk)
            if ok:
                passes += 1; months.append(k / TRADES_MONTH)
        pr = passes / TRIALS
        med_m = sorted(months)[len(months)//2] if months else 99
        eval_cost = (int(med_m) + 1) * EVAL_FEE_MONTH   # meses até passar × fee
        # funded 1 ano
        yr = [sim_funded_year(R, risk) for _ in range(TRIALS)]
        blows = sum(1 for x in yr if x is None)
        profits = [x for x in yr if x is not None]
        gross = sum(profits)/len(profits) if profits else 0
        # split: 100% ate 25k (nunca chega), então ~100% no 1º ano
        net = gross * 1.0
        results[risk] = (pr, med_m, eval_cost, net, blows/TRIALS)
        print(f"  ${risk:<7}{pr*100:>7.0f}%{med_m:>9.1f}{eval_cost:>11.0f}{net:>+16.0f}{blows/TRIALS*100:>8.1f}%")
    print("  " + "-" * 60)

    # Plano 10 contas no risco mais seguro com renda boa
    pick = 50
    pr, med_m, eval_cost, net, blow = results[pick]
    n_evals = max(10, round(10 / max(pr, 0.01)))
    print(f"\n  === PLANO 10 CONTAS (risco ${pick}/trade — quebra {blow*100:.0f}%) ===")
    print(f"  Comprar ~{n_evals} evals a ${EVAL_FEE_MONTH:.0f} = ~${n_evals*EVAL_FEE_MONTH:.0f} (até ~10 aprovarem)")
    print(f"  Custo eval por conta aprovada: ~${eval_cost:.0f}")
    print(f"  Renda/ano: ~${net:.0f} x 10 = ~${net*10:.0f}/ano (~${net*10/12:.0f}/mês)")
    print(f"  Payout: 100% dos primeiros $25k/conta → 1º ano você fica com ~tudo")
    print("\n  (Semi-auto na PA: robô alerta, você clica na master, Apex copia p/ as 20.)")
    print("  (Estimativa in-sample; real depende de forward-test + execução maker.)")


if __name__ == "__main__":
    main()
