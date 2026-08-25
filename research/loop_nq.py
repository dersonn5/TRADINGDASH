"""
Agente Pesquisador NQ — tuning do Nasdaq (home turf ICT), anti-leak 3 janelas
=============================================================================
SEARCH: IS=2022 / VAL=2023 (o agente seleciona aqui) | HOLDOUT=2024 (intocado).
Pesquisador local (Ollama, grátis). Dados cacheados (fix de performance).

Uso:  python -m research.loop_nq --cycles 8
"""
import os
import sys
import json
import argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab_nq import run_experiment
from research.researcher import propose

LOG = Path(__file__).resolve().parent / "experiments_nq.jsonl"
IS_WIN = ("2022-01-01", "2022-12-31")
VAL_WIN = ("2023-01-01", "2023-12-31")
HOLDOUT = ("2024-01-01", "2024-12-31")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=8)
    args = ap.parse_args()

    print("=" * 64)
    print("  AGENTE PESQUISADOR NQ — tuning do home turf (anti-leak)")
    print(f"  SEARCH IS=2022 VAL=2023 | HOLDOUT=2024 (intocado)")
    print("=" * 64)

    history = []
    base = run_experiment({}, is_window=IS_WIN, oos_window=VAL_WIN)
    base["cycle"] = 0; base["rationale"] = "baseline NQ"
    history.append(base)
    print(f"[baseline] VAL PF={base['oos']['profit_factor']} win={base['oos']['win_rate']}% "
          f"holds={base['oos_holds']} score={base['oos_score']}")
    best = base

    for c in range(1, args.cycles + 1):
        print(f"\n[ciclo {c}/{args.cycles}] propondo...")
        p = propose(history)
        ov = p["overrides"]
        if not ov:
            print(f"  vazio ({p['rationale']})"); continue
        print(f"  {ov} | {p['rationale'][:80]}")
        exp = run_experiment(ov, is_window=IS_WIN, oos_window=VAL_WIN)
        exp["cycle"] = c; exp["rationale"] = p["rationale"]
        history.append(exp)
        print(f"  -> VAL PF={exp['oos']['profit_factor']} win={exp['oos']['win_rate']}% "
              f"DD={exp['oos']['max_drawdown_percent']}% holds={exp['oos_holds']} score={exp['oos_score']}")
        if exp["oos_holds"] and exp["oos_score"] > best["oos_score"]:
            best = exp
            print(f"  ★ novo melhor na VAL (score {exp['oos_score']})")

    with open(LOG, "w", encoding="utf-8") as f:
        for h in history:
            f.write(json.dumps(h) + "\n")

    print("\n" + "=" * 64)
    print("  TESTE FINAL — HOLDOUT 2024 (intocado na busca)")
    print("=" * 64)
    print(f"  config vencedora (selecionada na VAL 2023): {best['overrides']}")
    final = run_experiment(best["overrides"], is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    base_hold = run_experiment({}, is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    print(f"  HOLDOUT 2024 · AGENTE: PF={final['oos']['profit_factor']} win={final['oos']['win_rate']}% "
          f"PnL={final['oos']['total_pnl_usd']} DD={final['oos']['max_drawdown_percent']}%")
    print(f"  HOLDOUT 2024 · BASE  : PF={base_hold['oos']['profit_factor']} win={base_hold['oos']['win_rate']}% "
          f"PnL={base_hold['oos']['total_pnl_usd']} DD={base_hold['oos']['max_drawdown_percent']}%")
    win = final['oos']['profit_factor'] > base_hold['oos']['profit_factor']
    print(f"\n  VEREDITO: {'✅ agente MELHOROU o NQ no holdout cego' if win else '➖ agente nao superou base no holdout'}")


if __name__ == "__main__":
    main()
