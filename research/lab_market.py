"""
Lab Market — banco de testes por MERCADO (NQ / ES / ouro), 1 config ótima cada
==============================================================================
Generaliza o lab_nq p/ qualquer mercado. Carrega dados COMPLETOS 1x (cache) e
fatia por janela. Cada mercado tem:
  - symbol / correlacionado (SMT) / se usa SMT
  - BASE_CFG (sl% adequado à volatilidade do ativo)
  - MKT_CTX: texto das peculiaridades p/ o LLM adaptar a condução

run_experiment(overrides, market, is_window, oos_window) -> IS + OOS + veredito.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from research.lab import STRAT_KEYS, ENGINE_KEYS, clamp

FULL = ("2022-01-01", "2024-12-31")

# Registry por mercado — personalidade + base cfg + contexto p/ o pesquisador
MARKETS = {
    "NQ": {
        "symbol": "NAS/USD", "corr": "SPX/USD", "use_smt": True, "tick": 0.25,
        "base": dict(require_smt=True, target_rr=3.0, min_rr=1.8,
                     min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010),
        "ctx": ("Nasdaq-100 futures (NQ). HIGH volatility, strong trends, tech-driven. "
                "Momentum expansions are large -> let runners run (favor higher target_rr, later "
                "trail_trigger). Choppy US-morning fakeouts happen -> a momentum filter helps. "
                "SMT divergence vs S&P (ES) is reliable."),
    },
    "ES": {
        "symbol": "SPX/USD", "corr": "NAS/USD", "use_smt": True, "tick": 0.25,
        "base": dict(require_smt=True, target_rr=2.5, min_rr=1.6,
                     min_sl_distance_percent=0.0010, max_sl_distance_percent=0.007),
        "ctx": ("S&P 500 futures (ES). SMOOTHER, lower volatility than NQ, mean-reverts cleaner "
                "around PD arrays. Displacement is smaller -> lower displacement_atr; targets are "
                "tighter (lower target_rr); stops tighter. SMT divergence vs NQ is reliable."),
    },
    "XAU": {
        "symbol": "XAU/USD", "corr": None, "use_smt": False, "tick": 0.01,
        "base": dict(require_smt=False, target_rr=3.0, min_rr=1.8,
                     min_sl_distance_percent=0.0015, max_sl_distance_percent=0.010),
        "ctx": ("Gold spot (XAU). Safe-haven, SESSION-driven (London/NY killzones). Trends hard on "
                "macro then dead-ranges in Asia. No reliable index SMT pair -> SMT is OFF, so lean on "
                "momentum + PD arrays. A momentum filter (min_momentum_atr up) avoids the dead range."),
    },
}

_DATA = {}  # cache por mercado dos dados completos


def market_ctx(market: str) -> str:
    return MARKETS[market]["ctx"]


def _load_full(market: str):
    if market in _DATA:
        return _DATA[market]
    m = MARKETS[market]
    ld = DataLoader()
    c5 = ld.load_data(m["symbol"], "5m", *FULL)
    c1d = ld.load_data(m["symbol"], "1d", *FULL)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"}).dropna()
    c1m = ld.load_data(m["symbol"], "1m", *FULL)
    c5c = ld.load_data(m["corr"], "5m", *FULL) if m["corr"] else None
    _DATA[market] = (c5, c1h, c1d, c1m, c5c)
    return _DATA[market]


def _slice(df, start, end):
    if df is None:
        return None
    s = pd.to_datetime(start).tz_localize("America/New_York")
    e = pd.to_datetime(end).tz_localize("America/New_York")
    idx = df.index
    if idx.tz is None:
        idx = df.index.tz_localize("UTC").tz_convert("America/New_York")
        df = df.copy(); df.index = idx
    return df[(df.index >= s) & (df.index <= e)]


def _run_window(overrides, market, start, end):
    m = MARKETS[market]
    c5, c1h, c1d, c1m, c5c = _load_full(market)
    s5, s1h, s1d, s1m = (_slice(c5, start, end), _slice(c1h, start, end),
                         _slice(c1d, start, end), _slice(c1m, start, end))
    s5c = _slice(c5c, start, end)
    cfg_kw = dict(m["base"])
    cfg_kw.update({k: v for k, v in overrides.items() if k in STRAT_KEYS})
    strat = ICTTopDownCrypto(ICTTopDownConfig(**cfg_kw))
    strat.symbol = m["symbol"]
    strat.correlated_symbol = m["corr"]
    eng_kw = {k: v for k, v in overrides.items() if k in ENGINE_KEYS}
    bc = BacktestConfig(initial_balance=10000.0, tick_size=m["tick"], point_value=1.0,
                        commission_usd=0.0, commission_pct=0.0002, funding_rate_8h=0.0,
                        enable_partials=True, partial_pct=eng_kw.get("partial_pct", 0.5),
                        partial_rr=eng_kw.get("partial_rr", 2.0),
                        enable_break_even=True, break_even_trigger_rr=eng_kw.get("break_even_trigger_rr", 2.0),
                        enable_trailing=True, trail_trigger_rr=eng_kw.get("trail_trigger_rr", 4.0),
                        trail_distance_rr=eng_kw.get("trail_distance_rr", 1.5))
    res = BacktestEngine(bc).run(strategy=strat, candles_5m=s5, candles_15m=s5, candles_1h=s1h,
                                 candles_1d=s1d, candles_1m=s1m, use_filters=False, candles_5m_corr=s5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def run_experiment(overrides: dict, market: str,
                   is_window=("2022-01-01", "2023-12-31"),
                   oos_window=("2024-01-01", "2024-12-31")) -> dict:
    ov = clamp(overrides)
    is_m = _run_window(ov, market, *is_window)
    oos_m = _run_window(ov, market, *oos_window)

    def score(mm):
        if mm["total_trades"] < 30:
            return -1.0
        return mm["profit_factor"] - mm["max_drawdown_percent"] / 100.0

    holds = oos_m["profit_factor"] >= 1.05 and oos_m["total_pnl_usd"] > 0 and oos_m["total_trades"] >= 30
    keys = ("total_trades", "win_rate", "profit_factor", "total_pnl_usd", "max_drawdown_percent")
    return {
        "market": market, "overrides": ov,
        "is": {k: round(is_m[k], 3) for k in keys},
        "oos": {k: round(oos_m[k], 3) for k in keys},
        "is_score": round(score(is_m), 3), "oos_score": round(score(oos_m), 3),
        "oos_holds": bool(holds),
    }


if __name__ == "__main__":
    import json
    for mk in ("NQ", "ES", "XAU"):
        r = run_experiment({}, mk, is_window=("2022-01-01", "2022-12-31"),
                           oos_window=("2023-01-01", "2023-12-31"))
        print(mk, "VAL PF", r["oos"]["profit_factor"], "trades", r["oos"]["total_trades"],
              "holds", r["oos_holds"])
