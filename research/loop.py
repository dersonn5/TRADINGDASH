"""
Research Loop — o Agente Pesquisador autônomo
==============================================
Ciclo: LLM propõe config -> lab testa IS+OOS -> registra -> mantém o melhor
que SOBREVIVE no OOS. Guarda anti-overfit: só conta como melhoria se oos_holds
E o oos_score sobe vs baseline.

Uso:
    python -m research.loop --cycles 6
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab import run_experiment
from research.researcher import propose

LOG = Path(__file__).resolve().parent / "experiments.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--model", type=str, default=None)
    args = ap.parse_args()

    history = []
    print("=" * 60)
    print("  AGENTE PESQUISADOR — busca de edge com guarda OOS")
    print("=" * 60)

    # Baseline (config atual)
    print("\n[baseline] testando config atual...")
    base = run_experiment({})
    base["cycle"] = 0
    base["rationale"] = "baseline (config atual)"
    history.append(base)
    print(f"  baseline IS: PF={base['is']['profit_factor']} | OOS: PF={base['oos']['profit_factor']} "
          f"win={base['oos']['win_rate']}% holds={base['oos_holds']} oos_score={base['oos_score']}")

    best = base
    for c in range(1, args.cycles + 1):
        print(f"\n[ciclo {c}/{args.cycles}] researcher propondo...")
        p = propose(history, model=args.model)
        ov = p["overrides"]
        if not ov:
            print(f"  proposta vazia ({p['rationale']}), pulando.")
            continue
        print(f"  proposta: {ov}")
        print(f"  razao: {p['rationale']}")
        exp = run_experiment(ov)
        exp["cycle"] = c
        exp["rationale"] = p["rationale"]
        history.append(exp)
        print(f"  -> IS: PF={exp['is']['profit_factor']} trades={exp['is']['total_trades']} | "
              f"OOS: PF={exp['oos']['profit_factor']} win={exp['oos']['win_rate']}% "
              f"DD={exp['oos']['max_drawdown_percent']}% holds={exp['oos_holds']} oos_score={exp['oos_score']}")
        if exp["oos_holds"] and exp["oos_score"] > best["oos_score"]:
            best = exp
            print(f"  ★ NOVO MELHOR (oos_score {exp['oos_score']} > anterior)")

    with open(LOG, "w", encoding="utf-8") as f:
        for h in history:
            f.write(json.dumps(h) + "\n")

    print("\n" + "=" * 60)
    print("  MELHOR CONFIG (validada OOS)")
    print("=" * 60)
    print(f"  overrides: {best['overrides']}")
    print(f"  IS : PF={best['is']['profit_factor']} win={best['is']['win_rate']}% PnL={best['is']['total_pnl_usd']}")
    print(f"  OOS: PF={best['oos']['profit_factor']} win={best['oos']['win_rate']}% PnL={best['oos']['total_pnl_usd']} DD={best['oos']['max_drawdown_percent']}%")
    print(f"  log: {LOG}")


if __name__ == "__main__":
    main()
