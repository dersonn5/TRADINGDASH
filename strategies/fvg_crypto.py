"""
FVG Model (puro) — Cripto
==========================
Modelo de alta frequência do ICT: displacement (vela de deslocamento forte)
cria uma Fair Value Gap; o preço retorna para reequilibrar e entra na FVG na
direção do bias. Stop além da FVG, alvo no draw on liquidity.

Gates de qualidade:
  - Killzone ampla (volume cripto)
  - Daily bias alinhado
  - Displacement (corpo da vela > ATR * mult)
  - FVG ativa (não mitigada) na direção do bias
  - Preço retornando à FVG (dentro ou tocando)
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional
import pandas as pd

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class FVGCryptoConfig:
    killzone_start: time = time(2, 0)
    killzone_end: time = time(16, 0)
    min_rr: float = 2.0
    require_daily_bias: bool = True
    require_displacement: bool = True
    atr_period: int = 14
    atr_multiplier: float = 1.2          # corpo da vela criadora vs ATR
    fvg_lookback: int = 12
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 45


class FVGCrypto(CryptoICTBase):
    name = "fvg_crypto"

    def __init__(self, config: FVGCryptoConfig = None):
        self.config = config or FVGCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

    def _atr(self, df: pd.DataFrame, period: int) -> float:
        if len(df) < period + 1:
            return 0.0
        h = df["high"].iloc[-period:]
        l = df["low"].iloc[-period:]
        c = df["close"].shift(1).iloc[-period:]
        tr = pd.concat([(h - l).abs(), (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
        return float(tr.mean())

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
                          t.strftime("%H:%M"), "fora da janela de volume"):
            return None

        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        bias = self._get_daily_bias(d1)
        if not self._gate("bias_not_neutral", (not cfg.require_daily_bias) or bias != "NEUTRAL", bias, "bias neutro"):
            return None

        # FVG ativa na direção do bias
        want = "bullish" if bias == "BULLISH" else ("bearish" if bias == "BEARISH" else None)
        fdir, fb = self._detect_active_fvg(df, lookback=cfg.fvg_lookback)
        dir_ok = fb is not None and (want is None or fdir == want)
        if not self._gate("fvg_active", dir_ok, f"{fdir} {fb}", "sem FVG ativa alinhada"):
            return None

        fvg_top, fvg_bottom = fb
        action = "BUY" if fdir == "bullish" else "SELL"

        # Displacement: vela criadora forte vs ATR
        if cfg.require_displacement:
            atr = self._atr(df, cfg.atr_period)
            body = abs(float(df.iloc[-1]["close"]) - float(df.iloc[-1]["open"]))
            disp_ok = atr > 0 and (fvg_top - fvg_bottom) >= atr * 0.5
            if not self._gate("displacement", disp_ok, f"gap={fvg_top - fvg_bottom:.2f} atr={atr:.2f}", "sem displacement"):
                return None

        # Preço reequilibrando para dentro/borda da FVG
        if action == "BUY":
            touching = price <= fvg_top * 1.001
            sl_anchor = fvg_bottom
            dol = self._detect_dynamic_dol(candles_15m, "BUY", price, lookback=50) if hasattr(self, "_detect_dynamic_dol") else None
        else:
            touching = price >= fvg_bottom * 0.999
            sl_anchor = fvg_top
            dol = self._detect_dynamic_dol(candles_15m, "SELL", price, lookback=50) if hasattr(self, "_detect_dynamic_dol") else None

        if not self._gate("price_rebalancing", touching, f"price={price:.2f} fvg=({fvg_bottom:.2f},{fvg_top:.2f})", "preço longe da FVG"):
            return None

        self._last_signal_ts = ct
        self._gate("signal_generated", True, action, "FVG ok")
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"FVG model {action} bias={bias} fvg=({fvg_bottom:.2f},{fvg_top:.2f})",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.82)
