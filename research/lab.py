"""
Research Lab — banco de testes do Agente Pesquisador
=====================================================
run_experiment(overrides) constrói a estratégia top-down com os parâmetros
propostos, roda IS (treino) e OOS (teste cego), e retorna métricas + veredito.

Guarda anti-overfit: uma hipótese só "vence" se melhora o IN-SAMPLE E SEGURA no
OUT-SAMPLE (PnL+ e PF não desaba). Sem isso, é descartada.

Backtest mecânico (sem LLM). Default BTC-only p/ velocidade no loop de pesquisa.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig

# Espaço de busca permitido (limites) — restringe a IA, evita overfit selvagem
SEARCH_SPACE = {
    # estratégia
    "min_score":        (45.0, 80.0),
    "target_rr":        (2.0, 5.0),
    "min_rr":           (1.5, 2.5),
    "displacement_atr": (0.4, 1.4),
    "pd_tolerance":     (0.0, 0.30),
    "sweep_window_5m":  (4, 12),
    "mss_window_5m":    (3, 8),
    "sl_buffer_percent":(0.0008, 0.003),
    # gestão (engine)
    "partial_rr":       (1.5, 3.0),
    "partial_pct":      (0.3, 0.7),
    "break_even_trigger_rr": (1.5, 3.0),
    "trail_trigger_rr": (3.0, 6.0),
    "trail_distance_rr":(1.0, 2.5),
}
STRAT_KEYS = {"min_score", "target_rr", "min_rr", "displacement_atr", "pd_tolerance",
              "sweep_window_5m", "mss_window_5m", "sl_buffer_percent"}
ENGINE_KEYS = {"partial_rr", "partial_pct", "break_even_trigger_rr", "trail_trigger_rr", "trail_distance_rr"}

_CACHE = {}


def _load(symbol, start, end):
    key = (symbol, start, end)
    if key in _CACHE:
        return _CACHE[key]
    loader = DataLoader()
    c5 = loader.load_data(symbol, "5m", start, end)
    c1d = loader.load_data(symbol, "1d", start, end)
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    c1m = loader.load_data(symbol, "1m", start, end)
    corr = "ETH/USDT:USDT" if symbol == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    c5c = loader.load_data(corr, "5m", start, end)
    _CACHE[key] = (c5, c1h, c1d, c1m, c5c)
    return _CACHE[key]


def clamp(overrides: dict) -> dict:
    """Força os parâmetros dentro do espaço de busca permitido."""
    out = {}
    for k, v in overrides.items():
        if k in SEARCH_SPACE:
            lo, hi = SEARCH_SPACE[k]
            v = max(lo, min(hi, type(lo)(v)))
            if isinstance(lo, int):
                v = int(round(v))
            out[k] = v
    return out


def _run_window(overrides, symbol, start, end):
    c5, c1h, c1d, c1m, c5c = _load(symbol, start, end)
    strat_kw = {k: v for k, v in overrides.items() if k in STRAT_KEYS}
    cfg = ICTTopDownConfig(**strat_kw)
    strat = ICTTopDownCrypto(cfg)
    strat.symbol = symbol
    strat.correlated_symbol = "ETH/USDT:USDT" if symbol == "BTC/USDT:USDT" else "BTC/USDT:USDT"
    eng_kw = {k: v for k, v in overrides.items() if k in ENGINE_KEYS}
    tick = 0.1 if symbol == "BTC/USDT:USDT" else 0.01
    bc = BacktestConfig(initial_balance=10000.0, tick_size=tick, point_value=1.0, commission_usd=1.0,
                        enable_partials=True, partial_pct=eng_kw.get("partial_pct", 0.5),
                        partial_rr=eng_kw.get("partial_rr", 2.0),
                        enable_break_even=True, break_even_trigger_rr=eng_kw.get("break_even_trigger_rr", 2.0),
                        enable_trailing=True, trail_trigger_rr=eng_kw.get("trail_trigger_rr", 4.0),
                        trail_distance_rr=eng_kw.get("trail_distance_rr", 1.5),
                        funding_rate_8h=0.0001)
    eng = BacktestEngine(bc)
    res = eng.run(strategy=strat, candles_5m=c5, candles_15m=c5, candles_1h=c1h, candles_1d=c1d,
                  candles_1m=c1m, use_filters=False, candles_5m_corr=c5c)
    return PerformanceMetrics.calculate(res["positions"], 10000.0)


def run_experiment(overrides: dict, symbol="BTC/USDT:USDT",
                   is_window=("2022-01-01", "2023-12-31"),
                   oos_window=("2024-01-01", "2024-12-31")) -> dict:
    ov = clamp(overrides)
    is_m = _run_window(ov, symbol, *is_window)
    oos_m = _run_window(ov, symbol, *oos_window)

    def score(m):  # função-objetivo: PF penalizado por DD, exige amostra mínima
        if m["total_trades"] < 30:
            return -1.0
        return m["profit_factor"] - m["max_drawdown_percent"] / 100.0

    is_s, oos_s = score(is_m), score(oos_m)
    holds = (oos_m["profit_factor"] >= 1.05 and oos_m["total_pnl_usd"] > 0
             and oos_m["total_trades"] >= 30)
    return {
        "overrides": ov,
        "is": {k: round(is_m[k], 3) for k in ("total_trades", "win_rate", "profit_factor",
                                              "total_pnl_usd", "max_drawdown_percent")},
        "oos": {k: round(oos_m[k], 3) for k in ("total_trades", "win_rate", "profit_factor",
                                                "total_pnl_usd", "max_drawdown_percent")},
        "is_score": round(is_s, 3), "oos_score": round(oos_s, 3),
        "oos_holds": bool(holds),
    }


if __name__ == "__main__":
    import json
    r = run_experiment({})
    print(json.dumps(r, indent=2))
