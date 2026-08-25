"""
OTE (Optimal Trade Entry) — Cripto
===================================
Modelo core do ICT. Após um impulso com quebra de estrutura (MSS), o preço
retrai para a zona fib 62%-79% (OTE). Entrada na zona, alvo no extremo oposto
(draw on liquidity), stop além do swing que originou o impulso.

Gates de qualidade:
  - Killzone (London/NY)
  - Daily bias alinhado
  - Impulso recente válido (swing low->high ou high->low)
  - Preço dentro da zona OTE 62-79%
  - Confluência opcional: FVG dentro da zona OTE
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional
import pandas as pd

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class OTECryptoConfig:
    min_rr: float = 2.5
    require_daily_bias: bool = True
    require_fvg_confluence: bool = False   # confluência FVG-na-zona é rara no fechamento M5
    swing_lookback: int = 60
    min_impulse_percent: float = 0.006     # impulso mínimo (0.6%) para ser válido
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.001
    cooldown_minutes: int = 90
    ote_lo: float = 0.62
    ote_hi: float = 0.79


class OTECrypto(CryptoICTBase):
    name = "ote_crypto"

    def __init__(self, config: OTECryptoConfig = None):
        self.config = config or OTECryptoConfig()
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

        # GATE killzone
        in_kz = self._in_window(t, time(2, 0), time(5, 0)) or self._in_window(t, time(10, 0), time(12, 0))
        if not self._gate("killzone_active", in_kz, t.strftime("%H:%M"), "fora da killzone"):
            return None

        # GATE cooldown
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        # GATE bias
        bias = self._get_daily_bias(d1)
        if not self._gate("bias_not_neutral", (not cfg.require_daily_bias) or bias != "NEUTRAL", bias, "bias neutro"):
            return None

        # Impulso recente
        sh, sl = self._detect_mss_and_swing(df, lookback=cfg.swing_lookback)
        if not self._gate("swings_found", sh is not None and sl is not None, f"sh={sh},sl={sl}", "sem swings"):
            return None

        impulse = (sh - sl) / sl if sl > 0 else 0.0
        if not self._gate("impulse_valid", impulse >= cfg.min_impulse_percent, f"{impulse:.3f}", "impulso fraco"):
            return None

        # Direção pelo bias; default usa o impulso
        if bias == "BULLISH" or (bias == "NEUTRAL" and price < (sh + sl) / 2):
            action = "BUY"
            zb, zt = self._ote_zone(sl, sh, "BUY", cfg.ote_lo, cfg.ote_hi)
            sl_anchor = sl
            dol = sh
        else:
            action = "SELL"
            zb, zt = self._ote_zone(sl, sh, "SELL", cfg.ote_lo, cfg.ote_hi)
            sl_anchor = sh
            dol = sl

        # GATE preço dentro da zona OTE
        in_zone = zb <= price <= zt
        if not self._gate("price_in_ote", in_zone, f"{price:.2f} in [{zb:.2f},{zt:.2f}]", "fora da zona OTE"):
            return None

        # GATE confluência FVG na zona
        if cfg.require_fvg_confluence:
            fdir, fb = self._detect_active_fvg(df, lookback=12)
            want = "bullish" if action == "BUY" else "bearish"
            fvg_ok = fdir == want and fb is not None and (zb <= fb[0] <= zt or zb <= fb[1] <= zt)
            if not self._gate("fvg_confluence", fvg_ok, str(fb), "sem FVG na zona OTE"):
                return None

        self._last_signal_ts = ct
        self._gate("signal_generated", True, action, "OTE ok")
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"OTE {action} bias={bias} imp={impulse:.2%}",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.88)
