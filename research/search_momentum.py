"""
Busca Momentum Diário — staged, engine limpo, régua travada ANTES de ver resultado
====================================================================================
BARRA DE ACEITAÇÃO (combinada com o usuário, fixa, não muda depois de ver o número):
  PF >= 1.3 no holdout (2025-26)  |  DD <= 15%  |  trades suficientes p/ ser prático.
Sem isso: família morre, sem "quase deu".

IS 2022-23 (busca) / VAL 2024 (seleção) / HOLDOUT 2025-26 (travado, só no final).

Uso:  python -m research.search_momentum --market NQ --samples 150
"""
import os, sys, json, random, argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

from research.lab_market import MARKETS, _load_full, _slice
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.momentum_daily import MomentumDaily, MomentumDailyConfig

IS_WIN = ("2022-01-01", "2023-12-31")
VAL_WIN = ("2024-01-01", "2024-12-31")

SPACE = {
    "lookback_days":  (10, 120),
    "min_roc_atr":    (0.3, 2.0),
    "atr_period":     (10, 20),
    "stop_atr_mult":  (1.0, 3.5),
    "target_rr":      (2.0, 8.0),
    "cooldown_days":  (0, 7),
    # GESTÃO (bug corrigido: era hardcoded estilo ICT — parcial@2R + BE@2R cortava o
    # ganho real pra ~1:1 mesmo com alvo de 8R. Trend-following NÃO realiza parcial cedo;
    # só protege com trailing largo, deixando o vencedor correr até reverter de verdade.
    "trail_trigger_rr":  (1.0, 3.0),
    "trail_distance_rr": (1.5, 4.0),
    "be_trigger_rr":      (1.0, 3.0),
}


def sample_cfg(rng):
    ov = {}
    for k, (lo, hi) in SPACE.items():
        v = rng.uniform(lo, hi)
        if isinstance(lo, int):
            v = int(round(v))
        ov[k] = round(v, 3) if isinstance(v, float) else v
    return ov


def run_window(ov, market, start, end):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (_slice(c5, start, end), _slice(c1h, start, end),
                         _slice(c1d, start, end), _slice(c1m, start, end))
    mom_kw = {k: v for k, v in ov.items() if k in MomentumDailyConfig.__dataclass_fields__}
    strat = MomentumDaily(MomentumDailyConfig(**mom_kw))
    strat.symbol = m["symbol"]
    # GESTÃO trend-following corrigida: SEM parcial cedo (deixa o vencedor correr por
    # completo), BE só depois de movimento real, trailing largo (não fixo em 2R como ICT).
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=False,
                        enable_break_even=True, break_even_trigger_rr=ov.get("be_trigger_rr", 1.5),
                        enable_trailing=True, trail_trigger_rr=ov.get("trail_trigger_rr", 1.5),
                        trail_distance_rr=ov.get("trail_distance_rr", 2.0))
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def score(m):
    if m["total_trades"] < 15:
        return -9.0
    return m["profit_factor"] - m["max_drawdown_percent"] / 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=list(MARKETS.keys()))
    ap.add_argument("--samples", type=int, default=150)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    mk = args.market
    log = Path(__file__).resolve().parent / f"momentum_search_{mk.lower()}.jsonl"
    best_f = Path(__file__).resolve().parent / f"momentum_best_{mk.lower()}.json"

    print("=" * 68, flush=True)
    print(f"  BUSCA MOMENTUM {mk} — {args.samples} staged | IS 22-23 / VAL 24 | s/ leak", flush=True)
    print(f"  BARRA FIXA (holdout): PF>=1.3 DD<=15% | régua travada antes do resultado", flush=True)
    print("=" * 68, flush=True)

    screened = []
    f = open(log, "w", encoding="utf-8")
    for i in range(1, args.samples + 1):
        ov = sample_cfg(rng)
        try:
            val_m = run_window(ov, mk, *VAL_WIN)
        except Exception as e:
            print(f"  [s1 {i:03d}] ERRO {str(e)[:70]}", flush=True); continue
        rec = {"i": i, "stage": 1, "ov": ov,
               "val": {k: round(val_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
        f.write(json.dumps(rec) + "\n"); f.flush()
        if val_m["profit_factor"] >= 1.10 and val_m["total_trades"] >= 15:
            screened.append((score(val_m), ov, rec["val"]))
            print(f"  [s1 {i:03d}] VAL PF={val_m['profit_factor']:.2f}({val_m['total_trades']}) "
                  f"DD={val_m['max_drawdown_percent']:.0f}% lb={ov['lookback_days']} → candidata", flush=True)
        elif i % 15 == 0:
            print(f"  [s1 {i:03d}] ... ({len(screened)} candidatas)", flush=True)

    screened.sort(key=lambda x: -x[0])
    finalists = screened[:args.top]
    print(f"\n  ESTÁGIO 2: {len(finalists)} finalistas → IS 2022-23", flush=True)
    best = None
    for j, (sc1, ov, valr) in enumerate(finalists, 1):
        try:
            is_m = run_window(ov, mk, *IS_WIN)
        except Exception as e:
            print(f"  [s2 {j:02d}] ERRO {str(e)[:70]}", flush=True); continue
        rec = {"stage": 2, "ov": ov, "val": valr,
               "is": {k: round(is_m[k], 3) for k in ("total_trades", "profit_factor", "win_rate", "max_drawdown_percent")}}
        f.write(json.dumps(rec) + "\n"); f.flush()
        ok = is_m["profit_factor"] >= 1.05
        sc = min(score(is_m), sc1) if ok else -9.0
        tag = ""
        if ok and (best is None or sc > best["sc"]):
            best = {"sc": sc, "rec": rec}; tag = " ★"
        print(f"  [s2 {j:02d}] IS PF={is_m['profit_factor']:.2f}({is_m['total_trades']}) "
              f"DD={is_m['max_drawdown_percent']:.0f}% VAL PF={valr['profit_factor']:.2f}{tag}", flush=True)
    f.close()

    if best:
        best_f.write_text(json.dumps(best["rec"], indent=2), encoding="utf-8")
        print(f"\n  MELHOR {mk}: {best['rec']['ov']}", flush=True)
        print(f"  IS {best['rec']['is']} | VAL {best['rec']['val']}", flush=True)
        print(f"  salvo -> {best_f.name} (holdout 25-26 SÓ no final, 1x, régua PF>=1.3 DD<=15%)", flush=True)
    else:
        print(f"\n  NENHUMA config Momentum passou. Família também sem edge neste espaço.", flush=True)


if __name__ == "__main__":
    main()
