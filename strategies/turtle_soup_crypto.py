"""
Turtle Soup — Cripto
=====================
Raid de liquidez + reversão. O preço varre (sweep) um extremo prévio importante
(high/low das últimas 24h ou do range recente), induz breakout traders, e
fecha de volta para dentro do range. Entrada na reversão, stop além do sweep,
alvo no lado oposto do range (draw on liquidity).

Gates de qualidade:
  - Killzone ampla
  - Sweep de extremo de 24h (varreu e fechou de volta)
  - Vela de rejeição (close de volta no range)
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class TurtleSoupCryptoConfig:
    killzone_start: time = time(2, 0)
    killzone_end: time = time(16, 0)
    min_rr: float = 2.0
    range_lookback_5m: int = 288          # 24h
    sweep_window: int = 3
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 60
    require_daily_bias: bool = False


class TurtleSoupCrypto(CryptoICTBase):
    name = "turtle_soup_crypto"

    def __init__(self, config: TurtleSoupCryptoConfig = None):
        self.config = config or TurtleSoupCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        self._reset_gates()
        cfg = self.config
        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty), None, "dados vazios"):
            return None

        df = self._convert_to_est(candles_5m)
        d1 = self._convert_to_est(candles_1d)
        ct = df.index[-1]
        t = ct.time()
        price = float(df.iloc[-1]["close"])

        if not self._gate("killzone_active", self._in_window(t, cfg.killzone_start, cfg.killzone_end),
                          t.strftime("%H:%M"), "fora da janela"):
            return None
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        rng_high, rng_low = self._get_range(df, cfg.range_lookback_5m)
        if not self._gate("range_found", rng_high is not None, None, "sem range 24h"):
            return None

        bias = self._get_daily_bias(d1)
        bull_sweep = self._swept(df, rng_low, "low", cfg.sweep_window)    # varreu o low -> reversão BUY
        bear_sweep = self._swept(df, rng_high, "high", cfg.sweep_window)  # varreu o high -> reversão SELL

        if cfg.require_daily_bias:
            bull_sweep = bull_sweep and bias == "BULLISH"
            bear_sweep = bear_sweep and bias == "BEARISH"

        if bull_sweep:
            action, sl_anchor, dol = "BUY", float(df.iloc[-cfg.sweep_window:]["low"].min()), rng_high
        elif bear_sweep:
            action, sl_anchor, dol = "SELL", float(df.iloc[-cfg.sweep_window:]["high"].max()), rng_low
        else:
            self._gate("turtle_sweep", False, f"bull={bull_sweep} bear={bear_sweep}", "sem sweep+reversão")
            return None

        self._gate("turtle_sweep", True, action, "sweep+reversão ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"Turtle Soup {action} bias={bias}",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.83)
