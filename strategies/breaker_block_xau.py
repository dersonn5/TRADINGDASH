"""
Breaker Block XAU — Estratégia ICT para XAUUSD

Opera nas killzones NY Lunch (13:00-14:00) e NY PM/Close (15:00-16:00) EST,
onde o move da sessão AM é frequentemente revertido em Breaker Blocks.

Setup:
  1. Daily Bias (PO3 D1) definido
  2. Sweep do move da sessão AM (Asian High/Low ou PDH/PDL)
  3. MSS M5 com displacement >= 1.2x ATR
  4. Preço retorna ao OB violado (Breaker Block)
  5. Entrada no CE do Breaker (midpoint da vela do OB)
  6. SL além do extremo do Breaker + buffer
  7. TP = próximo liquidity pool (swing oposto ou PDH/PDL)
"""
from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from strategies.base import Strategy, Signal


@dataclass
class BreakerBlockXAUConfig:
    killzone_start: time = time(13, 0)   # EST — NY Lunch default
    killzone_end: time = time(14, 0)     # EST
    min_rr: float = 2.0
    sl_buffer_usd: float = 0.5
    tick_size: float = 0.1
    require_daily_bias: bool = True
    require_sweep: bool = True           # Sweep prévio obrigatório (ICT canônico)
    cooldown_minutes: int = 45
    min_sl_distance_usd: float = 6.0    # Lunch: ATR menor → SL menor OK
    atr_multiplier: float = 1.2         # Displacement mínimo para OB ser válido
    breaker_lookback: int = 40          # Candles M5 para buscar o OB violado
    session_name: str = "ny_lunch"


class BreakerBlockXAU(Strategy):
    name = "breaker_block_xau"
    symbol = "XAUUSD"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: BreakerBlockXAUConfig = None):
        self.config = config or BreakerBlockXAUConfig()
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

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        if len(df) < period + 1:
            return 0.0
        df_sliced = df.iloc[-(period + 5):] if len(df) > (period + 5) else df
        high = df_sliced["high"]
        low = df_sliced["low"]
        close = df_sliced["close"]
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1])

    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        if len(candles_1d) < 2:
            return "NEUTRAL"
        last = candles_1d.iloc[-2]
        close = last["close"]
        open_val = last["open"]
        high = last["high"]
        low = last["low"]
        total_range = high - low if high > low else 1.0
        if close > open_val and (high - close) / total_range < 0.3:
            return "BULLISH"
        elif close < open_val and (close - low) / total_range < 0.3:
            return "BEARISH"
        return "NEUTRAL"

    def _get_am_session_levels(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """Retorna high/low da sessão AM (09:30-11:00 EST) do dia atual."""
        day_str = current_time.strftime("%Y-%m-%d")
        am_start = pd.to_datetime(f"{day_str} 09:30:00").tz_localize("America/New_York")
        am_end = pd.to_datetime(f"{day_str} 11:00:00").tz_localize("America/New_York")
        am_candles = df_5m[(df_5m.index >= am_start) & (df_5m.index <= am_end)]
        if am_candles.empty:
            return None, None
        return float(am_candles["high"].max()), float(am_candles["low"].min())

    def _check_am_sweep(self, df_5m: pd.DataFrame, am_high: float, am_low: float, current_time: datetime) -> Tuple[bool, bool]:
        """Verifica se houve sweep do AM High ou AM Low após as 11:00 EST."""
        if am_high is None or am_low is None:
            return False, False
        day_str = current_time.strftime("%Y-%m-%d")
        after_am = pd.to_datetime(f"{day_str} 11:00:00").tz_localize("America/New_York")
        post_am_candles = df_5m[(df_5m.index >= after_am) & (df_5m.index <= current_time)]
        if post_am_candles.empty:
            return False, False
        # Bullish sweep: preço varreu o AM Low (trapper bears) e fechou acima
        low_swept = post_am_candles["low"].min() < am_low
        close_above_low = post_am_candles.iloc[-1]["close"] > am_low
        bullish_sweep = low_swept and close_above_low
        # Bearish sweep: preço varreu AM High e fechou abaixo
        high_swept = post_am_candles["high"].max() > am_high
        close_below_high = post_am_candles.iloc[-1]["close"] < am_high
        bearish_sweep = high_swept and close_below_high
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

        # GATE 1 — Killzone
        in_killzone = self.config.killzone_start <= current_time_only < self.config.killzone_end
        if not self._gate("killzone_active", in_killzone,
                          current_time_only.strftime("%H:%M"),
                          f"horário fora de {self.config.killzone_start}-{self.config.killzone_end}"):
            return None

        # GATE 1.5 — Cooldown
        if self._last_signal_ts is not None:
            elapsed = (current_time - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", elapsed >= self.config.cooldown_minutes,
                              f"{elapsed:.0f}min",
                              f"cooldown {self.config.cooldown_minutes}min não atingido"):
                return None

        # GATE 2 — Daily Bias
        bias = self._get_daily_bias(df_1d)
        bias_ok = (not self.config.require_daily_bias) or (bias != "NEUTRAL")
        if not self._gate("bias_not_neutral", bias_ok, bias,
                          "PO3 retornou NEUTRAL"):
            return None

        # GATE 3 — AM Session levels disponíveis
        am_high, am_low = self._get_am_session_levels(df_5m, current_time)
        am_ok = am_high is not None and am_low is not None
        if not self._gate("am_levels_available", am_ok,
                          f"am_high={am_high} am_low={am_low}",
                          "sem dados da sessão AM (09:30-11:00)"):
            return None

        # GATE 4 — Sweep da AM Session
        bullish_sweep, bearish_sweep = self._check_am_sweep(df_5m, am_high, am_low, current_time)
        sweep_ok = bullish_sweep or bearish_sweep
        if not self._gate("am_sweep_present",
                          (not self.config.require_sweep) or sweep_ok,
                          f"bull_sweep={bullish_sweep} bear_sweep={bearish_sweep}",
                          "sem sweep do AM High/Low após 11:00"):
            return None

        # GATE 5 — Detectar Breaker Block na direção correta (alinhada com bias)
        # Bearish sweep do AM High + BEARISH bias = Bearish Breaker
        # Bullish sweep do AM Low + BULLISH bias = Bullish Breaker
        if bearish_sweep and bias == "BEARISH":
            bb = self._detect_breaker_block(df_5m, "bearish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier)
        elif bullish_sweep and bias == "BULLISH":
            bb = self._detect_breaker_block(df_5m, "bullish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier)
        else:
            # Sweep e bias não alinhados — sem setup
            bb = None

        if not self._gate("breaker_detected", bb is not None,
                          bb["breaker_type"] if bb else "none",
                          "nenhum Breaker Block detectado no M5"):
            return None

        # GATE 6 — Entrada a mercado no close atual; SL além do extremo do Breaker
        # O Breaker Block já tem o preço dentro da zona — entramos a mercado
        entry_price = current_close
        zone_ref = bb["zone_high"] if bb["breaker_type"] == "bearish" else bb["zone_low"]

        if bb["breaker_type"] == "bearish":
            sl_price = bb["zone_high"] + self.config.sl_buffer_usd
            sl_dist = abs(entry_price - sl_price)
            if sl_dist < self.config.min_sl_distance_usd:
                sl_price = entry_price + self.config.min_sl_distance_usd
                sl_dist = self.config.min_sl_distance_usd
            tp_target = am_low if am_low < entry_price else (entry_price - sl_dist * self.config.min_rr)
            take_profit = min(entry_price - sl_dist * self.config.min_rr, tp_target)
            action = "SELL"
        else:
            sl_price = bb["zone_low"] - self.config.sl_buffer_usd
            sl_dist = abs(entry_price - sl_price)
            if sl_dist < self.config.min_sl_distance_usd:
                sl_price = entry_price - self.config.min_sl_distance_usd
                sl_dist = self.config.min_sl_distance_usd
            tp_target = am_high if am_high > entry_price else (entry_price + sl_dist * self.config.min_rr)
            take_profit = max(entry_price + sl_dist * self.config.min_rr, tp_target)
            action = "BUY"

        self._gate("sl_min_ok", True, f"{sl_dist:.2f}", "SL OK")

        self._gate("signal_generated", True, action, "todos os gates passaram")
        self._last_signal_ts = current_time

        reason = (
            f"Breaker Block {bb['breaker_type'].upper()} — {self.config.session_name.upper()}. "
            f"{bb['reason']} "
            f"Entry={entry_price:.2f} SL={sl_price:.2f} TP={take_profit:.2f} RR={self.config.min_rr}"
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
