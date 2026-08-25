"""
Simulação 10 CONTAS 25k — renda mensal (Monte Carlo, motor PO3 conservador)
============================================================================
Usa trades reais (po3_trades_cache.json, NQ+ES) e simula 10 contas funded
SIMULTÂNEAS por 1 ano. Dois cenários honestos:

  INDEPENDENTE: cada conta bootstrap com start aleatório próprio — otimista,
    assume streams genuinamente diferentes (mercados/motores distintos por
    conta, como planejado: Bulenox 1 conta/mercado + MFFU copy 5).
  CORRELACIONADO: todas as 10 usam o MESMO start (mesmo trade no mesmo dia)
    — pessimista, cenário "cópia" onde quebram juntas se DD bater.

A verdade real fica ENTRE os dois. Streams diferentes (mercado/motor) puxam
pro independente; contas copiadas puxam pro correlacionado.

Uso:  python -m research.ten_accounts_sim [--risk 100] [--n 10]
"""
import os, sys, json, random, argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

CACHE = Path(__file__).resolve().parent / "po3_trades_cache.json"
DD, LOCK = 1500.0, 100.0
TRIALS = 3000


def load_R():
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    raw.sort(key=lambda x: str(x["exit"]))
    return [max(-1.2, min(15.0, t["r"])) for t in raw]


def acc_year(R, risk, start, tpy):
    n = len(R); p = pk = 0.0
    for k in range(tpy):
        p += R[(start + k) % n] * risk; pk = max(pk, p)
        if p <= min(pk - DD, LOCK):
            return None
    return p


def sim_portfolio(R, risk, n_accounts, tpy, correlated):
    n = len(R)
    results = []
    shared_start = random.randint(0, n - 1) if correlated else None
    for a in range(n_accounts):
        s = shared_start if correlated else random.randint(0, n - 1)
        results.append(acc_year(R, risk, s, tpy))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--risk", type=float, default=100.0)
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()
    R = load_R()
    months = 18  # trades vieram do holdout-like cache? checar abaixo
    tpm = len(R) / 18.0     # po3_trades_cache é NQ+ES 2022-24 (36 meses) — ajusta
    tpm = len(R) / 36.0
    tpy = int(tpm * 12)
    print("=" * 68)
    print(f"  10 CONTAS 25k — motor PO3+SMT conservador | risco ${args.risk:.0f}/trade")
    print(f"  {len(R)} trades reais (NQ+ES) | ~{tpm:.1f} trades/mês/conta")
    print("=" * 68)

    for label, corr in (("INDEPENDENTE (streams distintos p/ conta)", False),
                        ("CORRELACIONADO (pior caso, tipo cópia)", True)):
        n_blown_dist = []
        monthly_income_dist = []
        for _ in range(TRIALS):
            res = sim_portfolio(R, args.risk, args.n, tpy, corr)
            blown = sum(1 for x in res if x is None)
            alive = [x for x in res if x is not None]
            total_year = sum(alive)
            n_blown_dist.append(blown)
            monthly_income_dist.append(total_year / 12.0)
        avg_blown = sum(n_blown_dist) / TRIALS
        p_any_blow = sum(1 for x in n_blown_dist if x > 0) / TRIALS
        avg_month = sum(monthly_income_dist) / TRIALS
        med_month = sorted(monthly_income_dist)[len(monthly_income_dist)//2]
        p10 = sorted(monthly_income_dist)[int(TRIALS*0.10)]
        p90 = sorted(monthly_income_dist)[int(TRIALS*0.90)]
        print(f"\n  === {label} ===")
        print(f"  contas quebradas/ano (média): {avg_blown:.2f} de {args.n}")
        print(f"  P(pelo menos 1 quebra no ano): {p_any_blow*100:.0f}%")
        print(f"  renda/mês (10 contas): média ${avg_month:+.0f} | mediana ${med_month:+.0f}")
        print(f"  faixa 10-90%: ${p10:+.0f} .. ${p90:+.0f}")

    print("\n  Realidade fica ENTRE os 2 cenários — depende de quão distintos são os streams.")
    print("  Plano (Bulenox 1 conta/mercado + MFFU copy 5) puxa mais pro INDEPENDENTE.")
    print("  (In-sample/holdout 2022-26; forward real decide o número de verdade.)")


if __name__ == "__main__":
    main()
