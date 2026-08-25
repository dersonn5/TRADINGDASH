"""
Agente Pesquisador v2 — disciplina de 3 janelas (anti-leak)
============================================================
Problema do v1: o agente via o mesmo OOS (2024) em todos os ciclos → podia
vazar/overfitar ao OOS.

v2 separa:
  - SEARCH: IS=2022 (treino) / VAL=2023 (o agente seleciona aqui)
  - HOLDOUT: 2024 — INTOCADO durante a busca. Só o VENCEDOR final testa nele, 1x.

Assim o número final é genuinamente fora de amostra.

Uso:
    python -m research.loop_v2 --cycles 6
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

from research.lab import run_experiment
from research.researcher import propose

LOG = Path(__file__).resolve().parent / "experiments_v2.jsonl"
IS_WIN = ("2022-01-01", "2022-12-31")
VAL_WIN = ("2023-01-01", "2023-12-31")
HOLDOUT = ("2024-01-01", "2024-12-31")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--symbol", default="BTC/USDT:USDT")
    args = ap.parse_args()

    print("=" * 64)
    print("  AGENTE PESQUISADOR v2 — 3 janelas (anti-leak)")
    print(f"  SEARCH: IS={IS_WIN[0][:4]} VAL={VAL_WIN[0][:4]} | HOLDOUT={HOLDOUT[0][:4]} (intocado)")
    print("=" * 64)

    history = []
    # baseline na fase de busca (IS=2022, VAL=2023)
    base = run_experiment({}, symbol=args.symbol, is_window=IS_WIN, oos_window=VAL_WIN)
    base["cycle"] = 0; base["rationale"] = "baseline"
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
        print(f"  proposta: {ov} | {p['rationale'][:90]}")
        exp = run_experiment(ov, symbol=args.symbol, is_window=IS_WIN, oos_window=VAL_WIN)
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

    # ── TESTE FINAL no HOLDOUT (2024) — 1 vez, só o vencedor ──
    print("\n" + "=" * 64)
    print("  TESTE FINAL — HOLDOUT 2024 (intocado durante a busca)")
    print("=" * 64)
    print(f"  config vencedora (selecionada na VAL 2023): {best['overrides']}")
    final = run_experiment(best["overrides"], symbol=args.symbol,
                           is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    print(f"  HOLDOUT 2024: PF={final['oos']['profit_factor']} win={final['oos']['win_rate']}% "
          f"PnL={final['oos']['total_pnl_usd']} DD={final['oos']['max_drawdown_percent']}% holds={final['oos_holds']}")
    # comparar com baseline no holdout
    base_hold = run_experiment({}, symbol=args.symbol,
                               is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    print(f"  baseline 2024: PF={base_hold['oos']['profit_factor']} win={base_hold['oos']['win_rate']}% "
          f"PnL={base_hold['oos']['total_pnl_usd']} DD={base_hold['oos']['max_drawdown_percent']}%")
    win = final['oos']['profit_factor'] > base_hold['oos']['profit_factor']
    print(f"\n  VEREDITO: {'✅ agente BATEU baseline no holdout cego' if win else '➖ agente NAO superou baseline no holdout'}")


if __name__ == "__main__":
    main()
