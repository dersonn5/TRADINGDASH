"""
Validação Out-of-Sample (IS vs OOS)
====================================
Compara o desempenho das estratégias (mecânico e/ou com cérebro) em duas janelas:

  IN-SAMPLE  (treino)  : período onde a calibração/decisões são tomadas
  OUT-SAMPLE (teste)   : período NUNCA usado para tunar — o juiz da verdade

Regra de ouro: NÃO ajuste nada olhando o OOS. Decida tudo no IS, valide 1x no OOS.
Se PF/winrate desabam do IS para o OOS → overfit. Se seguram → edge plausível.

Uso:
    python run_oos_validation.py                          # mecânico, todos
    python run_oos_validation.py --brain                  # com segundo cérebro
    python run_oos_validation.py --strategies breaker_block,fvg,turtle_soup
    python run_oos_validation.py --is 2022-01-01:2023-12-31 --oos 2024-01-01:2024-12-31
"""
import os
import sys
import argparse
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from data.data_loader import DataLoader
from core.brain_filter import BrainFilter
from run_crypto_backtest_brain import run_setup, ALL_STRATEGIES


def agg(results):
    """Agrega métricas de uma lista de resultados (soma trades/PnL, recalcula winrate ponderada)."""
    raw_t = sum(r["raw"]["total_trades"] for r in results if r)
    raw_pnl = sum(r["raw"]["total_pnl_usd"] for r in results if r)
    brn_t = sum(r["brain"]["total_trades"] for r in results if r)
    brn_pnl = sum(r["brain"]["total_pnl_usd"] for r in results if r)
    raw_wins = sum(r["raw"]["win_rate"] / 100 * r["raw"]["total_trades"] for r in results if r)
    brn_wins = sum(r["brain"]["win_rate"] / 100 * r["brain"]["total_trades"] for r in results if r)
    return {
        "raw_trades": raw_t, "raw_pnl": raw_pnl,
        "raw_wr": (100 * raw_wins / raw_t) if raw_t else 0.0,
        "brn_trades": brn_t, "brn_pnl": brn_pnl,
        "brn_wr": (100 * brn_wins / brn_t) if brn_t else 0.0,
    }


def run_window(loader, brain, symbols, strategies, start, end, mechanical_only):
    res = []
    for sym in symbols:
        for strat in strategies:
            try:
                res.append(run_setup(loader, brain, sym, strat, start, end,
                                     mechanical_only=mechanical_only))
            except Exception as e:
                import traceback
                print(f"[ERRO] {sym}/{strat}: {e}")
                traceback.print_exc()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTC/USDT:USDT,ETH/USDT:USDT")
    ap.add_argument("--strategies", default=",".join(ALL_STRATEGIES))
    ap.add_argument("--is", dest="is_win", default="2022-01-01:2023-12-31")
    ap.add_argument("--oos", dest="oos_win", default="2024-01-01:2024-12-31")
    ap.add_argument("--brain", action="store_true", help="Aplica o segundo cérebro (LLM).")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]
    is_s, is_e = args.is_win.split(":")
    oos_s, oos_e = args.oos_win.split(":")
    mech = not args.brain

    print("=" * 70)
    print("  VALIDAÇÃO OUT-OF-SAMPLE" + ("  (mecânico)" if mech else "  (com SEGUNDO CÉREBRO)"))
    print(f"  IN-SAMPLE : {is_s} -> {is_e}   (treino)")
    print(f"  OUT-SAMPLE: {oos_s} -> {oos_e}   (teste cego)")
    print(f"  Estratégias: {strategies}")
    print("=" * 70)

    brain = None
    if args.brain:
        brain = BrainFilter()
        if not brain.available():
            print("[ERRO] Ollama offline."); sys.exit(1)

    loader = DataLoader()
    print("\n>>> Rodando IN-SAMPLE...")
    is_res = run_window(loader, brain, symbols, strategies, is_s, is_e, mech)
    print("\n>>> Rodando OUT-OF-SAMPLE...")
    oos_res = run_window(loader, brain, symbols, strategies, oos_s, oos_e, mech)

    a_is, a_oos = agg(is_res), agg(oos_res)
    col = "brn" if args.brain else "raw"
    is_months = 24
    oos_months = 12

    print("\n" + "=" * 70)
    print(f"  RESULTADO {'(BRAIN)' if args.brain else '(MECÂNICO)'} — IS vs OOS (agregado)")
    print("=" * 70)
    print(f"  {'MÉTRICA':<22}{'IN-SAMPLE':>20}{'OUT-SAMPLE':>20}")
    print(f"  {'-'*62}")
    print(f"  {'Trades':<22}{a_is[col+'_trades']:>20}{a_oos[col+'_trades']:>20}")
    print(f"  {'Trades/mês':<22}{a_is[col+'_trades']/is_months:>20.1f}{a_oos[col+'_trades']/oos_months:>20.1f}")
    print(f"  {'Win rate %':<22}{a_is[col+'_wr']:>20.1f}{a_oos[col+'_wr']:>20.1f}")
    print(f"  {'PnL líquido USD':<22}{a_is[col+'_pnl']:>+20.0f}{a_oos[col+'_pnl']:>+20.0f}")
    print("=" * 70)

    # Veredito automático simples
    is_wr, oos_wr = a_is[col + "_wr"], a_oos[col + "_wr"]
    is_pnl, oos_pnl = a_is[col + "_pnl"], a_oos[col + "_pnl"]
    print("\n  VEREDITO:")
    if oos_pnl > 0 and oos_wr >= is_wr * 0.8:
        print("  ✅ Edge SEGUROU fora da amostra (PnL+ e winrate manteve). Plausível — vale forward-test.")
    elif oos_pnl > 0:
        print("  ⚠️  OOS lucrativo mas winrate caiu. Frágil — investigar antes de confiar.")
    else:
        print("  ❌ OOS NEGATIVO. Edge não generaliza = overfit. NÃO operar real.")
    print()


if __name__ == "__main__":
    main()
