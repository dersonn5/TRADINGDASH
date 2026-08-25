"""
Unicorn Model — Cripto
=======================
Setup de alta probabilidade do ICT: um Breaker Block que se SOBREPÕE a uma
Fair Value Gap na mesma direção. A sobreposição Breaker+FVG é a zona "unicórnio".
Entrada quando o preço retorna à zona de sobreposição.

Gates de qualidade:
  - Killzone
  - Daily bias
  - Breaker Block detectado (M5)
  - FVG ativa sobreposta à zona do Breaker
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class UnicornCryptoConfig:
    killzone_start: time = time(2, 0)
    killzone_end: time = time(16, 0)
    min_rr: float = 2.5
    require_daily_bias: bool = True
    breaker_lookback: int = 50
    atr_multiplier: float = 1.0
    fvg_lookback: int = 15
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 90


class UnicornCrypto(CryptoICTBase):
    name = "unicorn_crypto"

    def __init__(self, config: UnicornCryptoConfig = None):
        self.config = config or UnicornCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

    @staticmethod
    def _overlap(a_lo, a_hi, b_lo, b_hi) -> bool:
        return max(a_lo, b_lo) <= min(a_hi, b_hi)

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

        bias = self._get_daily_bias(d1)
        if not self._gate("bias_not_neutral", (not cfg.require_daily_bias) or bias != "NEUTRAL", bias, "bias neutro"):
            return None

        direction = "bullish" if bias == "BULLISH" else ("bearish" if bias == "BEARISH" else None)
        if direction is None:
            return None

        asian = self._get_asian_range(df, ct)
        rng24 = self._get_range(df, 288)
        bb = self._detect_breaker_block(df, direction, lookback=cfg.breaker_lookback,
                                        atr_multiplier=cfg.atr_multiplier, asian_range=asian, range_24h=rng24)
        if not self._gate("breaker_detected", bb is not None, None, "sem breaker"):
            return None

        # FVG na mesma direção, sobreposta à zona do breaker
        want = "bullish" if direction == "bullish" else "bearish"
        overlap_fvg = None
        for fdir, (ftop, fbot), _ in self._detect_fvg_list(df, cfg.fvg_lookback):
            if fdir == want and self._overlap(bb["zone_low"], bb["zone_high"], fbot, ftop):
                overlap_fvg = (ftop, fbot)
                break
        if not self._gate("unicorn_overlap", overlap_fvg is not None, str(overlap_fvg), "sem FVG sobreposta ao breaker"):
            return None

        action = "BUY" if direction == "bullish" else "SELL"
        sl_anchor = bb["zone_low"] if action == "BUY" else bb["zone_high"]
        dol = self._detect_dynamic_dol(candles_15m, action, price, lookback=50)

        self._gate("signal_generated", True, action, "Unicorn ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"Unicorn {action} (breaker+FVG) bias={bias}",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.90)
