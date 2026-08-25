"""
Probe de TODOS os modelos ICT no NQ (home turf) — mecânico
===========================================================
Roda cada modelo ICT (Turtle, Judas, PO3, OTE, Unicorn, MMXM, FVG, London,
Silver Bullet, Breaker) no NQ 2022-2024 com SMT vs S&P, taxa maker.
Mostra quais têm edge no home turf (no cripto 6/10 eram perdedores).

Uso:  python -m research.probe_nq_strategies
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

from strategies.silver_bullet_crypto import SilverBulletCrypto, SilverBulletCryptoConfig
from strategies.breaker_block_crypto import BreakerBlockCrypto, BreakerBlockCryptoConfig
from strategies.fvg_crypto import FVGCrypto, FVGCryptoConfig
from strategies.turtle_soup_crypto import TurtleSoupCrypto, TurtleSoupCryptoConfig
from strategies.judas_swing_crypto import JudasSwingCrypto, JudasSwingCryptoConfig
from strategies.po3_crypto import PowerOfThreeCrypto, PowerOfThreeCryptoConfig
from strategies.unicorn_crypto import UnicornCrypto, UnicornCryptoConfig
from strategies.mmxm_crypto import MMXMCrypto, MMXMCryptoConfig
from strategies.london_sweep_crypto import LondonSweepCrypto, LondonSweepCryptoConfig
from strategies.ote_crypto import OTECrypto, OTECryptoConfig

SYMBOL, CORR = "NAS/USD", "SPX/USD"
START, END = "2024-01-01", "2024-12-31"  # screen rápido (1 ano) — full valida depois

MODELS = {
    "silver_bullet": lambda: SilverBulletCrypto(SilverBulletCryptoConfig(require_smt=True)),
    "breaker_block": lambda: BreakerBlockCrypto(BreakerBlockCryptoConfig()),
    "fvg":           lambda: FVGCrypto(FVGCryptoConfig()),
    "turtle_soup":   lambda: TurtleSoupCrypto(TurtleSoupCryptoConfig()),
    "judas_swing":   lambda: JudasSwingCrypto(JudasSwingCryptoConfig()),
    "po3":           lambda: PowerOfThreeCrypto(PowerOfThreeCryptoConfig()),
    "unicorn":       lambda: UnicornCrypto(UnicornCryptoConfig()),
    "mmxm":          lambda: MMXMCrypto(MMXMCryptoConfig()),
    "london_sweep":  lambda: LondonSweepCrypto(LondonSweepCryptoConfig()),
    "ote":           lambda: OTECrypto(OTECryptoConfig()),
}

_D = None


def _load():
    global _D
    if _D:
        return _D
    ld = DataLoader()
    c5 = ld.load_data(SYMBOL, "5m", START, END)
    c1d = ld.load_data(SYMBOL, "1d", START, END)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c5c = ld.load_data(CORR, "5m", START, END)
    _D = (c5, c1h, c1d, c5c)
    return _D


def main():
    c5, c1h, c1d, c5c = _load()
    print("=" * 60)
    print("  MODELOS ICT no NQ (home turf) — mecânico, taxa maker, 2022-2024")
    print("=" * 60)
    print(f"  {'MODELO':<16}{'trades':>7}{'t/mês':>7}{'win%':>7}{'PF':>7}{'PnL':>9}{'DD%':>7}")
    print("  " + "-" * 54)
    rows = []
    for name, mk in MODELS.items():
        try:
            s = mk()
            s.symbol = SYMBOL
            s.correlated_symbol = CORR
            eng = BacktestEngine(BacktestConfig(initial_balance=10000.0, tick_size=0.25, point_value=1.0,
                                                commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                                                enable_partials=True, partial_rr=2.0, partial_pct=0.5,
                                                enable_break_even=True, break_even_trigger_rr=2.0,
                                                enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5))
            r = eng.run(strategy=s, candles_5m=c5, candles_15m=c5, candles_1h=c1h, candles_1d=c1d,
                        candles_1m=None, use_filters=False, candles_5m_corr=c5c)
            m = PerformanceMetrics.calculate(r["positions"], 10000.0)
            print(f"  {name:<16}{m['total_trades']:>7}{m['total_trades']/36:>7.1f}{m['win_rate']:>7.1f}"
                  f"{m['profit_factor']:>7.2f}{m['total_pnl_usd']:>+9.0f}{m['max_drawdown_percent']:>7.1f}")
            rows.append((name, m["profit_factor"], m["total_pnl_usd"]))
        except Exception as e:
            print(f"  {name:<16} ERRO: {str(e)[:40]}")
    print("  " + "-" * 54)
    winners = [n for n, pf, pnl in rows if pf > 1.05 and pnl > 0]
    print(f"\n  Vencedores (PF>1.05): {', '.join(winners) if winners else 'nenhum'}")
    print("  (candidatos a portfólio no NQ)")


if __name__ == "__main__":
    main()
