"""
Impacto da taxa no edge — analítico (rápido)
=============================================
Roda o engine 1x por ativo (sem comissão, com funding), pega os trades, e aplica
as 3 taxas (sem taxa / maker 0.02% / taker 0.05%) sobre os MESMOS trades.
Recalcula PF, win e expectância. Responde: a taxa real da OKX come o edge?

PF/win/expectância são ratios por-trade → o resultado vale p/ $150, $500 ou $10k.

Uso:
    python -m research.fee_impact
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from research.lab import _load, clamp
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from backtesting.engine import BacktestEngine, BacktestConfig

CFG = clamp({"min_score": 58, "displacement_atr": 0.95, "pd_tolerance": 0.08})
SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT"]
FEES = {"sem taxa": 0.0, "maker 0.02%": 0.0002, "taker 0.05%": 0.0005}
START, END = "2022-01-01", "2024-12-31"


def base_trades(sym):
    c5, c1h, c1d, c1m, c5c = _load(sym, START, END)
    kw = {k: v for k, v in CFG.items() if k in ("min_score", "displacement_atr", "pd_tolerance")}
    s = ICTTopDownCrypto(ICTTopDownConfig(**kw))
    s.symbol = sym
    s.correlated_symbol = "ETH/USDT:USDT" if sym == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    tick = 0.1 if sym == "BTC/USDT:USDT" else 0.01
    bc = BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0, funding_rate_8h=0.0001,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    out = []
    for p in res["positions"]:
        notional = p.entry_price * p.size_units  # point_value=1
        out.append((p.pnl_usd, notional))
    return out


def stats(trades, fee_pct):
    wins = losses = 0.0
    nw = nl = 0
    exp_sum = 0.0
    for pnl, notional in trades:
        fee = 2.0 * fee_pct * notional          # round-trip
        net = pnl - fee
        exp_sum += net
        if net > 0:
            wins += net; nw += 1
        else:
            losses += -net; nl += 1
    n = nw + nl
    pf = wins / losses if losses > 0 else (wins if wins > 0 else 0.0)
    return {"trades": n, "win": 100 * nw / n if n else 0, "pf": pf, "exp": exp_sum / n if n else 0}


def main():
    print("=" * 66)
    print("  IMPACTO DA TAXA NO EDGE (top-down v2, 2022-2024)")
    print("=" * 66)
    for sym in SYMBOLS:
        tr = base_trades(sym)
        print(f"\n  {sym}  ({len(tr)} trades)")
        print(f"  {'cenário':<14}{'PF':>7}{'win%':>8}{'exp/trade(R-norm)':>20}")
        for name, f in FEES.items():
            s = stats(tr, f)
            print(f"  {name:<14}{s['pf']:>7.2f}{s['win']:>8.1f}{s['exp']:>20.2f}")
    print("\n  Regra: PF>1 = sobrevive. exp/trade em $ (base risco ~$100 no eixo de 10k).")


if __name__ == "__main__":
    main()
