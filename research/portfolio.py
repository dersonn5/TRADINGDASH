"""
Portfólio combinado — NQ + ES + Ouro numa conta única
======================================================
Roda o top-down v2 nos 3 mercados, normaliza cada trade em R (múltiplo de risco
— conserta o artefato de sizing e torna os mercados comparáveis), junta tudo
por ordem cronológica e simula UMA conta com risco fixo por trade.

Saída: métricas do portfólio + curva de capital → cockpit (dashboard mostra o
sistema TODO junto). Base pro teste em demo.

Uso:  python -m research.portfolio --balance 2000 --risk 0.01
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig

OUT = Path(__file__).resolve().parents[1] / "cockpit" / "data" / "portfolio.json"
BASE = dict(target_rr=3.2, min_rr=1.8, min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)
MARKETS = [
    ("NQ",  "NAS/USD", "SPX/USD", True, 63, 0.25),
    ("ES",  "SPX/USD", "NAS/USD", True, 63, 0.25),
    ("XAU", "XAU/USD", None,      False, 55, 0.01),
]
START, END = "2022-01-01", "2024-12-31"
_C = {}


def _load(sym):
    if sym in _C:
        return _C[sym]
    ld = DataLoader()
    c5 = ld.load_data(sym, "5m", START, END)
    c1d = ld.load_data(sym, "1d", START, END)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(sym, "1m", START, END)
    _C[sym] = (c5, c1h, c1d, c1m)
    return _C[sym]


def trades_for(name, sym, corr, smt, min_score, tick):
    c5, c1h, c1d, c1m = _load(sym)
    c5c = _load(corr)[0] if corr else None
    cfg = dict(BASE); cfg["min_score"] = min_score; cfg["require_smt"] = smt
    s = ICTTopDownCrypto(ICTTopDownConfig(**cfg))
    s.symbol = sym; s.correlated_symbol = corr or ""
    bc = BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    out = []
    for p in res["positions"]:
        # Engine dimensiona cada trade p/ arriscar ~$100 (1% de $10k, cap). Logo R = pnl/100.
        r = p.pnl_usd / 100.0
        out.append({"market": name, "exit": p.exit_time or p.entry_time,
                    "entry": p.entry_time, "side": p.action, "r": r})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--balance", type=float, default=2000.0)
    ap.add_argument("--risk", type=float, default=0.01)   # 1% por trade
    ap.add_argument("--rebuild", action="store_true", help="Re-roda os backtests (ignora cache)")
    args = ap.parse_args()

    print("=" * 60)
    print(f"  PORTFÓLIO COMBINADO — NQ+ES+Ouro | ${args.balance:.0f} | risco {args.risk*100:.0f}%/trade")
    print("=" * 60)

    # Cache dos trades brutos: roda backtests 1x, ajustes de math depois viram segundos.
    cache = Path(__file__).resolve().parent / "portfolio_trades_cache.json"
    if cache.exists() and not args.rebuild:
        raw = json.loads(cache.read_text(encoding="utf-8"))
        all_trades = [{"market": t["market"], "entry": t["entry"], "exit": t["exit"],
                       "side": t["side"], "r": t["r"]} for t in raw]
        print(f"  [cache] {len(all_trades)} trades carregados (use --rebuild p/ re-rodar backtests)")
    else:
        all_trades = []
        for name, sym, corr, smt, ms, tick in MARKETS:
            t = trades_for(name, sym, corr, smt, ms, tick)
            print(f"  {name}: {len(t)} trades")
            all_trades += t
        cache.write_text(json.dumps([{**t, "entry": str(t["entry"]), "exit": str(t["exit"])}
                                     for t in all_trades], default=str), encoding="utf-8")
    # ordena por saída (quando o resultado é realizado)
    all_trades.sort(key=lambda x: x["exit"])

    bal = args.balance
    fixed_risk = args.risk * args.balance   # risco FIXO por trade (não composto — realista p/ prop)
    equity = [{"t": START, "balance": round(bal, 2)}]
    wins = losses = 0
    gp = gl = 0.0
    trades_out = []
    peak = bal; maxdd = 0.0
    for i, tr in enumerate(all_trades, 1):
        r = max(-1.2, min(15.0, tr["r"]))   # sanidade: cap R por trade (outliers)
        pnl = r * fixed_risk
        bal += pnl
        peak = max(peak, bal); maxdd = max(maxdd, (peak - bal) / peak * 100)
        if pnl > 0: wins += 1; gp += pnl
        else: losses += 1; gl += -pnl
        et = tr["exit"]
        equity.append({"t": et.strftime("%Y-%m-%d %H:%M") if hasattr(et, "strftime") else str(et), "balance": round(bal, 2)})
        trades_out.append({"id": i, "date": (tr["entry"].strftime("%Y-%m-%d %H:%M") if hasattr(tr["entry"], "strftime") else str(tr["entry"])),
                           "symbol": tr["market"], "side": tr["side"], "rr": round(r, 2),
                           "result": "WIN" if pnl > 0 else "LOSS", "pnl": round(pnl, 2), "grade": tr["market"]})
    n = wins + losses
    pf = gp / gl if gl > 0 else 0.0
    ret = (bal / args.balance - 1) * 100
    ret_yr = ret / 3.0   # linear (risco fixo, não composto)
    print("\n  " + "-" * 54)
    print(f"  Trades: {n} | Win: {100*wins/n:.1f}% | PF: {pf:.2f}")
    print(f"  Saldo: ${args.balance:.0f} -> ${bal:.0f} ({ret:+.1f}% em 3 anos | {ret_yr:+.1f}%/ano, risco fixo)")
    print(f"  Max Drawdown: {maxdd:.1f}%")

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "symbol": "PORTFÓLIO NQ+ES+XAU", "period": f"{START} → {END}", "balance0": args.balance,
        "metrics": {"profit_factor": round(pf, 2), "win_rate": round(100*wins/n, 1),
                    "total_pnl": round(bal - args.balance, 2), "max_drawdown": round(maxdd, 1),
                    "trades": n, "expectancy": round((bal-args.balance)/n, 2), "final_balance": round(bal, 2)},
        "equity": equity, "trades": trades_out[-200:], "positions": [], "sample": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"  cockpit atualizado: {OUT}")


if __name__ == "__main__":
    main()
