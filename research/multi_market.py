"""
Multi-mercado — top-down v2 em NQ + ES + Ouro
==============================================
Mesma estratégia (config NQ-tunada) em mercados descorrelacionados.
Se o edge segura nos 3, é robusto de verdade (não específico do NQ) e o
portfólio dá curva mais suave.

SMT: NQ↔ES (correlacionados). Ouro sem par → SMT off (pontua menos).

Uso:  python -m research.multi_market
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig

# Config tunada pelo agente no NQ (candidata do sistema)
BASE = dict(target_rr=3.2, min_score=63, min_rr=1.8,
            min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)

MARKETS = [
    # (nome, symbol, correlacionado p/ SMT, smt_on, min_score_ajustado)
    ("NQ  (Nasdaq)", "NAS/USD", "SPX/USD", True, 63),
    ("ES  (S&P500)", "SPX/USD", "NAS/USD", True, 63),
    ("XAU (Ouro)",   "XAU/USD", None,      False, 55),  # sem SMT: teto de score menor
]
_C = {}


def _load(sym, start, end):
    key = (sym, start, end)
    if key in _C:
        return _C[key]
    ld = DataLoader()
    c5 = ld.load_data(sym, "5m", start, end)
    c1d = ld.load_data(sym, "1d", start, end)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(sym, "1m", start, end)
    _C[key] = (c5, c1h, c1d, c1m)
    return _C[key]


def run(symbol, corr, smt, min_score, start, end):
    c5, c1h, c1d, c1m = _load(symbol, start, end)
    c5c = _load(corr, start, end)[0] if corr else None
    cfg = dict(BASE); cfg["min_score"] = min_score; cfg["require_smt"] = smt
    s = ICTTopDownCrypto(ICTTopDownConfig(**cfg))
    s.symbol = symbol
    s.correlated_symbol = corr or ""
    tick = 0.01 if symbol == "XAU/USD" else 0.25
    bc = BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                        enable_break_even=True, break_even_trigger_rr=2.0,
                        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5)
    res = BacktestEngine(bc).run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h,
                                 candles_1d=c1d, candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def main():
    print("=" * 66)
    print("  MULTI-MERCADO — top-down v2 (config NQ) | maker fee | OOS 2024")
    print("=" * 66)
    print(f"  {'MERCADO':<16}{'janela':<12}{'trades':>7}{'win%':>7}{'PF':>7}{'PnL':>9}{'DD%':>7}")
    print("  " + "-" * 62)
    agg = {"pf": [], "pos": 0, "n": 0}
    for name, sym, corr, smt, ms in MARKETS:
        for lbl, (s, e) in [("IS 22-23", ("2022-01-01", "2023-12-31")),
                            ("OOS 2024", ("2024-01-01", "2024-12-31"))]:
            try:
                m = run(sym, corr, smt, ms, s, e)
                print(f"  {name:<16}{lbl:<12}{m['total_trades']:>7}{m['win_rate']:>7.1f}"
                      f"{m['profit_factor']:>7.2f}{m['total_pnl_usd']:>+9.0f}{m['max_drawdown_percent']:>7.1f}")
                if lbl == "OOS 2024":
                    agg["n"] += 1
                    agg["pf"].append(m["profit_factor"])
                    if m["profit_factor"] > 1.05 and m["total_pnl_usd"] > 0:
                        agg["pos"] += 1
            except Exception as ex:
                print(f"  {name:<16}{lbl:<12} ERRO: {str(ex)[:36]}")
        print()
    print("  " + "-" * 62)
    print(f"  OOS 2024: {agg['pos']}/{agg['n']} mercados positivos | PF médio {sum(agg['pf'])/max(1,len(agg['pf'])):.2f}")


if __name__ == "__main__":
    main()
