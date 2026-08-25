"""
Estratégia 2 fases: eval AGRESSIVO -> funded CONSERVADOR (Apex 25k)
==================================================================
Eval: risco alto = passa rápido; se quebrar, reset ~$20 (barato).
Funded: risco baixo = ~0% quebra, renda estável.
Quantifica custo total (com resets) + renda p/ 10 contas.
"""
import os, sys, json, random
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

CACHE = Path(__file__).resolve().parent / "portfolio_trades_cache.json"
TARGET, DD, FEE = 1500.0, 1500.0, 19.90
TPM = 1024/36.0; TRIALS = 5000

def R():
    raw = json.loads(CACHE.read_text(encoding="utf-8")); raw.sort(key=lambda x:str(x["exit"]))
    return [t["r"] for t in raw]

def eval_once(r, risk):
    n=len(r); s=random.randint(0,n-1); p=pk=0.0
    for k in range(400):
        p+=r[(s+k)%n]*risk; pk=max(pk,p)
        if p<=pk-DD: return False,k
        if p>=TARGET: return True,k+1
    return False,400

def funded_year(r, risk):
    n=len(r); s=random.randint(0,n-1); p=pk=0.0
    for k in range(int(TPM*12)):
        p+=r[(s+k)%n]*risk; pk=max(pk,p)
        if p<=min(pk-DD,100.0): return None
    return p

def main():
    r=R()
    print("="*64); print("  2 FASES: eval AGRESSIVO -> funded CONSERVADOR (Apex 25k)"); print("="*64)
    # eval agressivo: testa risco alto
    print("\n  FASE 1 — EVAL (achar risco que passa rápido, reset barato se quebrar):")
    print(f"  {'risco':<8}{'pass%':>8}{'~meses':>9}{'evals/conta':>13}{'custo/conta':>13}")
    for risk in (100,125,150,200,250):
        wins=0; ms=[]
        for _ in range(TRIALS):
            ok,k=eval_once(r,risk)
            if ok: wins+=1; ms.append(k/TPM)
        pr=wins/TRIALS; med=sorted(ms)[len(ms)//2] if ms else 99
        evals_per = 1/max(pr,0.01)              # tentativas até passar
        cost = evals_per * (int(med)+1) * FEE   # ~meses de fee por tentativa
        print(f"  ${risk:<7}{pr*100:>7.0f}%{med:>9.1f}{evals_per:>13.1f}{cost:>13.0f}")
    # funded conservador
    print("\n  FASE 2 — FUNDED CONSERVADOR (renda + quebra):")
    print(f"  {'risco':<8}{'quebra%':>9}{'renda/ano':>12}")
    fund={}
    for risk in (40,50,60):
        yr=[funded_year(r,risk) for _ in range(TRIALS)]
        blow=sum(1 for x in yr if x is None)/TRIALS
        prof=[x for x in yr if x is not None]; g=sum(prof)/len(prof) if prof else 0
        fund[risk]=(blow,g)
        print(f"  ${risk:<7}{blow*100:>8.1f}%{g:>+12.0f}")

    # plano combinado
    print("\n  === PLANO COMBINADO (eval $200 agressivo -> funded $50) ===")
    # eval $200
    wins=0; ms=[]
    for _ in range(TRIALS):
        ok,k=eval_once(r,200)
        if ok: wins+=1; ms.append(k/TPM)
    pr=wins/TRIALS; med=sorted(ms)[len(ms)//2] if ms else 99
    evals_10 = round(10/pr) if pr>0 else 99
    cost_eval = evals_10*(int(med)+1)*FEE
    blow,g = fund[50]
    print(f"  Eval $200: {pr*100:.0f}% pass em ~{med:.1f} mês → ~{evals_10} evals p/ 10 aprovar = ~${cost_eval:.0f}")
    print(f"  Funded $50: quebra {blow*100:.0f}% | renda ~${g:.0f}/conta/ano")
    print(f"  10 contas: ~${g*10:.0f}/ano (~${g*10/12:.0f}/mês) | custo inicial ~${cost_eval:.0f}")
    print("\n  (In-sample; forward-test decide. Semi-auto na PA.)")

if __name__=="__main__": main()
