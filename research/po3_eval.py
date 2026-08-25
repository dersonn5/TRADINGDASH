"""
Eval prop 25k com o motor PO3+SMT (NQ+ES) — Monte Carlo
========================================================
Gera trades do PO3 (NQ+ES, r=pnl/100 confiável), salva cache, e simula:
  - Eval 25k (alvo +$1500, trailing DD $1500): pass rate por risco
  - Funded 1 ano: P(quebra) + renda
Compara com o motor validado (portfolio_trades_cache NQ+ES only).

Uso:  python -m research.po3_eval [--rebuild]
"""
import os, sys, json, random, argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

CACHE = Path(__file__).resolve().parent / "po3_trades_cache.json"
VALID_CACHE = Path(__file__).resolve().parent / "portfolio_trades_cache.json"
TARGET, DD, LOCK = 1500.0, 1500.0, 100.0
TRIALS = 5000


def build():
    from research.compare_po3 import trades_for, MARKETS, BASE
    from strategies.ict_po3 import ICTPo3, ICTPo3Config
    out = []
    for name, sym, corr, smt, ms, tick in MARKETS:
        if name not in ("NQ", "ES"):
            continue
        cfg = dict(BASE); cfg["min_score"] = ms; cfg["require_smt"] = smt
        cfg["require_po3"] = True; cfg["smt_gate"] = bool(smt)
        tr = trades_for(ICTPo3(ICTPo3Config(**cfg)), sym, corr, tick)
        for t in tr:
            out.append({"market": name, "exit": str(t["exit"]), "r": t["r"]})
        print(f"  {name}: {len(tr)} trades PO3")
    CACHE.write_text(json.dumps(out), encoding="utf-8")
    return out


def load_R(path, nq_es_only=False):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if nq_es_only:
        raw = [t for t in raw if t.get("market") in ("NQ", "ES")]
    raw.sort(key=lambda x: str(x["exit"]))
    return [max(-1.2, min(15.0, t["r"])) for t in raw]


def sim_eval(R, risk, tpm):
    n = len(R); s = random.randint(0, n - 1); p = pk = 0.0
    for k in range(400):
        p += R[(s + k) % n] * risk; pk = max(pk, p)
        if p <= pk - DD: return False, k
        if p >= TARGET: return True, k + 1
    return False, 400


def sim_funded_year(R, risk, tpy):
    n = len(R); s = random.randint(0, n - 1); p = pk = 0.0
    for k in range(tpy):
        p += R[(s + k) % n] * risk; pk = max(pk, p)
        if p <= min(pk - DD, LOCK): return None
    return p


def block(label, R, months=36):
    tpm = len(R) / months
    tpy = int(tpm * 12)
    print(f"\n  === {label} — {len(R)} trades | ~{tpm:.1f} trades/mês ===")
    print(f"  {'risco':<8}{'PASS%':>8}{'~meses':>9}{'~dias':>7}{'P(quebra/ano)':>15}{'renda/ano':>12}")
    for risk in (150, 200, 250, 300, 350):
        wins = 0; ms = []
        for _ in range(TRIALS):
            ok, k = sim_eval(R, risk, tpm)
            if ok: wins += 1; ms.append(k / tpm)
        pr = wins / TRIALS
        med = sorted(ms)[len(ms)//2] if ms else 99
        yr = [sim_funded_year(R, risk, tpy) for _ in range(TRIALS)]
        blow = sum(1 for x in yr if x is None) / TRIALS
        prof = [x for x in yr if x is not None]
        g = sum(prof) / len(prof) if prof else 0
        dias = med * 30.4
        print(f"  ${risk:<7}{pr*100:>7.0f}%{med:>9.1f}{dias:>7.0f}{blow*100:>14.1f}%{g:>+12.0f}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    print("=" * 64)
    print("  EVAL 25k — motor PO3+SMT vs VALIDADO (NQ+ES, Monte Carlo)")
    print("=" * 64)
    if CACHE.exists() and not args.rebuild:
        print(f"  [cache] {CACHE.name}")
    else:
        print("  gerando trades PO3 (2 backtests)...")
        build()
    R_po3 = load_R(CACHE)
    R_val = load_R(VALID_CACHE, nq_es_only=True)
    block("VALIDADO NQ+ES", R_val)
    block("PO3+SMT NQ+ES", R_po3)
    print("\n  (In-sample 2022-24; forward-test decide. XAU fora até fix de escala.)")


if __name__ == "__main__":
    main()
