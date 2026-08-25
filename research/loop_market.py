"""
Agente Pesquisador POR MERCADO — tuning market-aware, anti-leak 3 janelas
=========================================================================
O agente recebe o CONTEXTO do mercado (personalidade) e adapta a config
(condução, momentum, alvos) especificamente pra ele. Cada mercado -> 1 config.

SEARCH: IS=2022 / VAL=2023 (agente seleciona aqui) | HOLDOUT=2024 (intocado).
Pesquisador local (Ollama, grátis). Dados cacheados.

Uso:  python -m research.loop_market --market NQ --cycles 8
      python -m research.loop_market --market ES --cycles 8
      python -m research.loop_market --market XAU --cycles 8
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

from research.lab_market import run_experiment, market_ctx, MARKETS
from research.researcher import propose

IS_WIN = ("2022-01-01", "2022-12-31")
VAL_WIN = ("2023-01-01", "2023-12-31")
HOLDOUT = ("2024-01-01", "2024-12-31")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=list(MARKETS.keys()))
    ap.add_argument("--cycles", type=int, default=8)
    args = ap.parse_args()
    mk = args.market
    ctx = market_ctx(mk)
    log = Path(__file__).resolve().parent / f"experiments_{mk.lower()}.jsonl"
    best_file = Path(__file__).resolve().parent / f"best_{mk.lower()}.json"

    print("=" * 66)
    print(f"  AGENTE PESQUISADOR {mk} — market-aware (adapta à personalidade)")
    print(f"  SEARCH IS=2022 VAL=2023 | HOLDOUT=2024 (intocado)")
    print("=" * 66)
    print(f"  contexto: {ctx[:110]}...")

    history = []
    base = run_experiment({}, mk, is_window=IS_WIN, oos_window=VAL_WIN)
    base["cycle"] = 0; base["rationale"] = f"baseline {mk}"
    history.append(base)
    print(f"\n[baseline] VAL PF={base['oos']['profit_factor']} win={base['oos']['win_rate']}% "
          f"trades={base['oos']['total_trades']} holds={base['oos_holds']} score={base['oos_score']}")
    best = base

    for c in range(1, args.cycles + 1):
        print(f"\n[ciclo {c}/{args.cycles}] propondo...")
        p = propose(history, market_ctx=ctx)
        ov = p["overrides"]
        if not ov:
            print(f"  vazio ({p['rationale']})"); continue
        print(f"  {ov} | {p['rationale'][:80]}")
        exp = run_experiment(ov, mk, is_window=IS_WIN, oos_window=VAL_WIN)
        exp["cycle"] = c; exp["rationale"] = p["rationale"]
        history.append(exp)
        print(f"  -> VAL PF={exp['oos']['profit_factor']} win={exp['oos']['win_rate']}% "
              f"trades={exp['oos']['total_trades']} DD={exp['oos']['max_drawdown_percent']}% "
              f"holds={exp['oos_holds']} score={exp['oos_score']}")
        if exp["oos_holds"] and exp["oos_score"] > best["oos_score"]:
            best = exp
            print(f"  ★ novo melhor na VAL (score {exp['oos_score']})")

    with open(log, "w", encoding="utf-8") as f:
        for h in history:
            f.write(json.dumps(h) + "\n")

    print("\n" + "=" * 66)
    print(f"  TESTE FINAL {mk} — HOLDOUT 2024 (intocado na busca)")
    print("=" * 66)
    print(f"  config vencedora (selecionada na VAL 2023): {best['overrides']}")
    final = run_experiment(best["overrides"], mk, is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    base_hold = run_experiment({}, mk, is_window=("2022-01-01", "2023-12-31"), oos_window=HOLDOUT)
    print(f"  HOLDOUT 2024 · AGENTE: PF={final['oos']['profit_factor']} win={final['oos']['win_rate']}% "
          f"PnL={final['oos']['total_pnl_usd']} DD={final['oos']['max_drawdown_percent']}%")
    print(f"  HOLDOUT 2024 · BASE  : PF={base_hold['oos']['profit_factor']} win={base_hold['oos']['win_rate']}% "
          f"PnL={base_hold['oos']['total_pnl_usd']} DD={base_hold['oos']['max_drawdown_percent']}%")
    win = final['oos']['profit_factor'] > base_hold['oos']['profit_factor']
    # salva a config vencedora + resultado holdout p/ o portfólio usar
    best_file.write_text(json.dumps({
        "market": mk, "overrides": best["overrides"],
        "holdout": final["oos"], "base_holdout": base_hold["oos"],
        "beat_base": bool(win),
    }, indent=2), encoding="utf-8")
    print(f"\n  VEREDITO: {'✅ agente MELHOROU '+mk+' no holdout cego' if win else '➖ agente nao superou base no holdout'}")
    print(f"  salvo -> {best_file.name}")


if __name__ == "__main__":
    main()
