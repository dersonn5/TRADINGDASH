"""
Momentum Diário — Time-Series Momentum clássico (Moskowitz/Ooi/Pedersen 2012)
================================================================================
SEM ICT, SEM narrativa retrospectiva. Sinal = 1 número: retorno acumulado dos
últimos N dias. Positivo => long, negativo => short. É o edge quant mais
documentado da história (décadas, cross-asset, fundos bilionários vivem disso).

Sem look-ahead: usa só velas DIÁRIAS FECHADAS (engine corta por vela fechada).
Avalia 1x/dia (gate interno). Gestão via engine padrão (partial/BE/trailing —
mesma máquina genérica usada em todo o projeto, não específica de ICT).
"""
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional
import pandas as pd

from strategies.base import Strategy, Signal


@dataclass
class MomentumDailyConfig:
    lookback_days: int = 40       # janela de retorno (ROC) em dias
    min_roc_atr: float = 1.0      # ROC mínimo (múltiplos do ATR diário) p/ sinal válido
    atr_period: int = 14
    stop_atr_mult: float = 2.0    # stop = N x ATR diário
    target_rr: float = 4.0        # alvo = stop_dist x RR (deixa tendência correr)
    cooldown_days: int = 3        # não re-sinaliza mesma direção logo em seguida
    allow_overnight_hold: bool = True   # trend-following PRECISA segurar dias/semanas (não é day-trade)


class MomentumDaily(Strategy):
    name = "momentum_daily"

    def __init__(self, config: MomentumDailyConfig = None):
        self.config = config or MomentumDailyConfig()
        self._last_day = None
        self._last_direction = None
        self._cooldown_until = None

    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engine exige esse método em toda estratégia (independente de ICT)."""
        if df is None or df.empty:
            return df
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None and \
           str(df.index.tz) in ["America/New_York", "EST5EDT"]:
            return df
        d = df.copy()
        if not isinstance(d.index, pd.DatetimeIndex):
            d.index = pd.to_datetime(d.index)
        if d.index.tz is None:
            d.index = d.index.tz_localize("UTC").tz_convert("America/New_York")
        else:
            d.index = d.index.tz_convert("America/New_York")
        return d

    def _atr(self, d1: pd.DataFrame, period: int) -> float:
        if d1 is None or len(d1) < period + 1:
            return 0.0
        h, l, c = d1["high"], d1["low"], d1["close"].shift(1)
        tr = pd.concat([(h - l).abs(), (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
        return float(tr.tail(period).mean())

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        cfg = self.config
        if candles_5m is None or candles_5m.empty or candles_1d is None or candles_1d.empty:
            return None

        ct = candles_5m.index[-1]
        day = ct.date()
        if self._last_day == day:      # só avalia 1x/dia
            return None
        self._last_day = day

        d1 = candles_1d
        if len(d1) < cfg.lookback_days + cfg.atr_period + 2:
            return None

        price = float(candles_5m.iloc[-1]["close"])
        atr = self._atr(d1, cfg.atr_period)
        if atr <= 0:
            return None

        past = float(d1.iloc[-cfg.lookback_days]["close"])
        last_close = float(d1.iloc[-1]["close"])
        roc_atr = (last_close - past) / atr

        if abs(roc_atr) < cfg.min_roc_atr:
            return None
        direction = "BUY" if roc_atr > 0 else "SELL"

        if self._cooldown_until is not None and day <= self._cooldown_until \
                and direction == self._last_direction:
            return None

        sl_dist = atr * cfg.stop_atr_mult
        if direction == "BUY":
            sl = price - sl_dist
            tp = price + sl_dist * cfg.target_rr
        else:
            sl = price + sl_dist
            tp = price - sl_dist * cfg.target_rr

        self._last_direction = direction
        self._cooldown_until = day + timedelta(days=cfg.cooldown_days)

        return Signal(
            symbol=getattr(self, "symbol", ""), action=direction,
            entry_price=round(price, 2), stop_loss=round(sl, 2), take_profit=round(tp, 2),
            confidence_score=0.7, reasoning=f"Momentum {direction} ROC/ATR={roc_atr:.2f}",
            meta={"roc_atr": round(roc_atr, 3)},
            timestamp=ct.to_pydatetime() if hasattr(ct, "to_pydatetime") else ct,
        )
