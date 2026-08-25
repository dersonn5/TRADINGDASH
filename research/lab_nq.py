"""
Lab NQ — banco de testes do Agente Pesquisador para Nasdaq (SMT vs S&P)
=======================================================================
Fix de performance: carrega os dados COMPLETOS (2022-2024) UMA vez e fatia
por janela em memória. Antes recarregava 1M velas por bloco (lento).

run_experiment(overrides) -> IS + OOS no NQ, com SMT vs SPX e taxa maker.
Guarda anti-overfit no veredito.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from research.lab import SEARCH_SPACE, STRAT_KEYS, ENGINE_KEYS, clamp

SYMBOL, CORR = "NAS/USD", "SPX/USD"
FULL = ("2022-01-01", "2024-12-31")
# Base NQ (SMT ligado; sl % adequado ao índice)
BASE_CFG = dict(require_smt=True, target_rr=3.0, min_rr=1.8,
                min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010)

_DATA = None  # cache dos dados completos, carregado 1x


def _load_full():
    global _DATA
    if _DATA is not None:
        return _DATA
    ld = DataLoader()
    c5 = ld.load_data(SYMBOL, "5m", *FULL)
    c1d = ld.load_data(SYMBOL, "1d", *FULL)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(SYMBOL, "1m", *FULL)
    c5c = ld.load_data(CORR, "5m", *FULL)
    _DATA = (c5, c1h, c1d, c1m, c5c)
    return _DATA


def _slice(df, start, end):
    import pandas as pd
    s = pd.to_datetime(start).tz_localize("America/New_York")
    e = pd.to_datetime(end).tz_localize("America/New_York")
    idx = df.index
    if idx.tz is None:
        idx = df.index.tz_localize("UTC").tz_convert("America/New_York")
        df = df.copy(); df.index = idx
    return df[(df.index >= s) & (df.index <= e)]


def _run_window(overrides, start, end):
    c5, c1h, c1d, c1m, c5c = _load_full()
    s5, s1h, s1d, s1m, s5c = (_slice(c5, start, end), _slice(c1h, start, end),
                              _slice(c1d, start, end), _slice(c1m, start, end), _slice(c5c, start, end))
    cfg_kw = dict(BASE_CFG)
    cfg_kw.update({k: v for k, v in overrides.items() if k in STRAT_KEYS})
    strat = ICTTopDownCrypto(ICTTopDownConfig(**cfg_kw))
    strat.symbol = SYMBOL
    strat.correlated_symbol = CORR
    eng_kw = {k: v for k, v in overrides.items() if k in ENGINE_KEYS}
    bc = BacktestConfig(initial_balance=10000.0, tick_size=0.25, point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_pct=eng_kw.get("partial_pct", 0.5),
                        partial_rr=eng_kw.get("partial_rr", 2.0),
                        enable_break_even=True, break_even_trigger_rr=eng_kw.get("break_even_trigger_rr", 2.0),
                        enable_trailing=True, trail_trigger_rr=eng_kw.get("trail_trigger_rr", 4.0),
                        trail_distance_rr=eng_kw.get("trail_distance_rr", 1.5))
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False, candles_5m_corr=s5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def run_experiment(overrides: dict,
                   is_window=("2022-01-01", "2023-12-31"),
                   oos_window=("2024-01-01", "2024-12-31")) -> dict:
    ov = clamp(overrides)
    is_m = _run_window(ov, *is_window)
    oos_m = _run_window(ov, *oos_window)

    def score(m):
        if m["total_trades"] < 30:
            return -1.0
        return m["profit_factor"] - m["max_drawdown_percent"] / 100.0

    holds = oos_m["profit_factor"] >= 1.05 and oos_m["total_pnl_usd"] > 0 and oos_m["total_trades"] >= 30
    return {
        "overrides": ov,
        "is": {k: round(is_m[k], 3) for k in ("total_trades", "win_rate", "profit_factor", "total_pnl_usd", "max_drawdown_percent")},
        "oos": {k: round(oos_m[k], 3) for k in ("total_trades", "win_rate", "profit_factor", "total_pnl_usd", "max_drawdown_percent")},
        "is_score": round(score(is_m), 3), "oos_score": round(score(oos_m), 3),
        "oos_holds": bool(holds),
    }
