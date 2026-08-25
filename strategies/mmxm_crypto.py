"""
MMXM — Market Maker Buy/Sell Model — Cripto
============================================
Modelo institucional do ICT (mentoria 2023):
  Buy Model:  sweep da liquidez SSL (low) → MSS de alta (rompe swing high) →
              retração para desconto → continuação BUY até a BSL.
  Sell Model: sweep da liquidez BSL (high) → MSS de baixa → retração para prêmio
              → continuação SELL até a SSL.

Gates de qualidade:
  - Killzone ampla
  - Sweep de extremo de 24h (liquidez tomada)
  - MSS confirmado (close rompe swing oposto)
  - Retração para desconto/prêmio (preço entre o sweep e o swing)
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class MMXMCryptoConfig:
    killzone_start: time = time(2, 0)
    killzone_end: time = time(16, 0)
    min_rr: float = 2.0
    range_lookback_5m: int = 288
    swing_lookback: int = 30
    sweep_window: int = 6
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 120


class MMXMCrypto(CryptoICTBase):
    name = "mmxm_crypto"

    def __init__(self, config: MMXMCryptoConfig = None):
        self.config = config or MMXMCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        self._reset_gates()
        cfg = self.config
        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty), None, "dados vazios"):
            return None

        df = self._convert_to_est(candles_5m)
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
        sh, sl = self._detect_mss_and_swing(df, lookback=cfg.swing_lookback)
        if not self._gate("structure_found", rng_high is not None and sh is not None and sl is not None,
                          None, "sem range/swings"):
            return None

        # Buy model: varreu o low de 24h e rompeu o swing high (MSS up)
        swept_low = self._swept(df, rng_low, "low", cfg.sweep_window)
        mss_up = price > sh
        # Sell model: varreu o high de 24h e rompeu o swing low (MSS down)
        swept_high = self._swept(df, rng_high, "high", cfg.sweep_window)
        mss_down = price < sl

        if swept_low and mss_up:
            action, sl_anchor, dol = "BUY", float(df.iloc[-cfg.sweep_window:]["low"].min()), rng_high
        elif swept_high and mss_down:
            action, sl_anchor, dol = "SELL", float(df.iloc[-cfg.sweep_window:]["high"].max()), rng_low
        else:
            self._gate("mmxm_model", False, f"buy={swept_low and mss_up} sell={swept_high and mss_down}", "sem MMXM")
            return None

        self._gate("mmxm_model", True, action, "MMXM ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"MMXM {action} (sweep+MSS)",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.87)
