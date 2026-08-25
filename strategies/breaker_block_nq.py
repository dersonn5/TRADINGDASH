"""
Breaker Block NQ — Estratégia ICT para Nasdaq (NQ/NDX)

Opera nas killzones NY Lunch (13:00-14:00) e NY PM/Close (15:00-16:00) EST.
Lógica idêntica à BreakerBlockXAU, ajustada para NQ:
  - SL em pontos NQ (não USD)
  - Referência de sweep = AM Session do NQ (09:30-11:00)
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple
import pandas as pd
from strategies.base import Strategy, Signal


@dataclass
class BreakerBlockNQConfig:
    killzone_start: time = time(13, 0)
    killzone_end: time = time(14, 0)
    min_rr: float = 2.0
    sl_buffer_ticks: int = 3
    tick_size: float = 0.25            # NQ tick = $0.25
    require_daily_bias: bool = True
    require_sweep: bool = True
    cooldown_minutes: int = 45
    min_sl_distance_pts: float = 20.0  # Lunch: 80 ticks NQ
    atr_multiplier: float = 1.2
    breaker_lookback: int = 40
    session_name: str = "ny_lunch"


class BreakerBlockNQ(Strategy):
    name = "breaker_block_nq"
    symbol = "NQ"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: BreakerBlockNQConfig = None):
        self.config = config or BreakerBlockNQConfig()
        self._last_signal_ts: Optional[datetime] = None

    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        if df_copy.index.tz is None:
            df_copy.index = df_copy.index.tz_localize("UTC").tz_convert("America/New_York")
        else:
            df_copy.index = df_copy.index.tz_convert("America/New_York")
        return df_copy

    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        if len(candles_1d) < 2:
            return "NEUTRAL"
        last = candles_1d.iloc[-2]
        close, open_val = last["close"], last["open"]
        high, low = last["high"], last["low"]
        total_range = high - low if high > low else 1.0
        if close > open_val and (high - close) / total_range < 0.3:
            return "BULLISH"
        elif close < open_val and (close - low) / total_range < 0.3:
            return "BEARISH"
        return "NEUTRAL"

    def _get_am_session_levels(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        day_str = current_time.strftime("%Y-%m-%d")
        am_start = pd.to_datetime(f"{day_str} 09:30:00").tz_localize("America/New_York")
        am_end = pd.to_datetime(f"{day_str} 11:00:00").tz_localize("America/New_York")
        am_candles = df_5m[(df_5m.index >= am_start) & (df_5m.index <= am_end)]
        if am_candles.empty:
            return None, None
        return float(am_candles["high"].max()), float(am_candles["low"].min())

    def _check_am_sweep(self, df_5m: pd.DataFrame, am_high: float, am_low: float, current_time: datetime) -> Tuple[bool, bool]:
        if am_high is None or am_low is None:
            return False, False
        day_str = current_time.strftime("%Y-%m-%d")
        after_am = pd.to_datetime(f"{day_str} 11:00:00").tz_localize("America/New_York")
        post_am = df_5m[(df_5m.index >= after_am) & (df_5m.index <= current_time)]
        if post_am.empty:
            return False, False
        bullish_sweep = (post_am["low"].min() < am_low) and (post_am.iloc[-1]["close"] > am_low)
        bearish_sweep = (post_am["high"].max() > am_high) and (post_am.iloc[-1]["close"] < am_high)
        return bullish_sweep, bearish_sweep

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
    ) -> Optional[Signal]:
        self._reset_gates()

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty),
                          None, "dados M5 ou D1 vazios"):
            return None

        df_5m = self._convert_to_est(candles_5m)
        df_1d = self._convert_to_est(candles_1d)
        current_time = df_5m.index[-1]
        current_time_only = current_time.time()
        current_close = float(df_5m.iloc[-1]["close"])  # Entrada a mercado

        in_killzone = self.config.killzone_start <= current_time_only < self.config.killzone_end
        if not self._gate("killzone_active", in_killzone,
                          current_time_only.strftime("%H:%M"),
                          f"horário fora de {self.config.killzone_start}-{self.config.killzone_end}"):
            return None

        if self._last_signal_ts is not None:
            elapsed = (current_time - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", elapsed >= self.config.cooldown_minutes,
                              f"{elapsed:.0f}min", f"cooldown de {self.config.cooldown_minutes}min"):
                return None

        bias = self._get_daily_bias(df_1d)
        if not self._gate("bias_not_neutral", (not self.config.require_daily_bias) or (bias != "NEUTRAL"),
                          bias, "PO3 retornou NEUTRAL"):
            return None

        am_high, am_low = self._get_am_session_levels(df_5m, current_time)
        if not self._gate("am_levels_available", am_high is not None,
                          f"am_high={am_high}", "sem dados da sessão AM"):
            return None

        bullish_sweep, bearish_sweep = self._check_am_sweep(df_5m, am_high, am_low, current_time)
        sweep_ok = bullish_sweep or bearish_sweep
        if not self._gate("am_sweep_present", (not self.config.require_sweep) or sweep_ok,
                          f"bull={bullish_sweep} bear={bearish_sweep}",
                          "sem sweep do AM High/Low após 11:00"):
            return None

        if bearish_sweep and bias == "BEARISH":
            bb = self._detect_breaker_block(df_5m, "bearish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier)
        elif bullish_sweep and bias == "BULLISH":
            bb = self._detect_breaker_block(df_5m, "bullish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier)
        else:
            bb = None

        if not self._gate("breaker_detected", bb is not None,
                          bb["breaker_type"] if bb else "none",
                          "nenhum Breaker Block detectado no M5"):
            return None

        # Entrada a mercado no close; SL além do extremo do Breaker
        entry_price = current_close
        sl_buffer = self.config.sl_buffer_ticks * self.config.tick_size

        if bb["breaker_type"] == "bearish":
            sl_price = bb["zone_high"] + sl_buffer
            sl_dist = abs(entry_price - sl_price)
            if sl_dist < self.config.min_sl_distance_pts:
                sl_price = entry_price + self.config.min_sl_distance_pts
                sl_dist = self.config.min_sl_distance_pts
            take_profit = entry_price - sl_dist * self.config.min_rr
            action = "SELL"
        else:
            sl_price = bb["zone_low"] - sl_buffer
            sl_dist = abs(entry_price - sl_price)
            if sl_dist < self.config.min_sl_distance_pts:
                sl_price = entry_price - self.config.min_sl_distance_pts
                sl_dist = self.config.min_sl_distance_pts
            take_profit = entry_price + sl_dist * self.config.min_rr
            action = "BUY"

        self._gate("sl_min_ok", True, f"{sl_dist:.2f}pts", "SL OK")

        self._gate("signal_generated", True, action, "todos os gates passaram")
        self._last_signal_ts = current_time

        reason = (
            f"Breaker Block {bb['breaker_type'].upper()} — NQ {self.config.session_name.upper()}. "
            f"{bb['reason']} "
            f"Entry={entry_price:.2f} SL={sl_price:.2f} TP={take_profit:.2f}"
        )

        return Signal(
            symbol=self.symbol,
            action=action,
            entry_price=round(entry_price, 2),
            stop_loss=round(sl_price, 2),
            take_profit=round(take_profit, 2),
            confidence_score=0.88,
            reasoning=reason,
            timestamp=current_time.to_pydatetime(),
        )
