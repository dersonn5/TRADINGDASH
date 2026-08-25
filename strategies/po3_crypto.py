"""
Power of Three (PO3 / AMD) — Cripto
====================================
Ciclo diário do algoritmo: Accumulation (range no open) → Manipulation (sweep
falso de um lado do range do open) → Distribution (expansão na direção real).

Usa o Midnight Open Range (00:00-02:00 EST) como acumulação. Quando a sessão
varre um extremo dessa acumulação e reverte, entra na direção da distribuição.

Gates de qualidade:
  - Janela de distribuição (após o open, London/NY)
  - Range de acumulação (midnight open) definido
  - Manipulação: sweep de um lado + close de volta
  - Alinhamento com daily bias (opcional)
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple
import pandas as pd

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class PowerOfThreeCryptoConfig:
    accumulation_start: time = time(0, 0)   # midnight open ET
    accumulation_end: time = time(2, 0)
    distribution_start: time = time(2, 0)
    distribution_end: time = time(12, 0)
    min_rr: float = 2.0
    sweep_window: int = 4
    require_daily_bias: bool = True
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 180


class PowerOfThreeCrypto(CryptoICTBase):
    name = "po3_crypto"

    def __init__(self, config: PowerOfThreeCryptoConfig = None):
        self.config = config or PowerOfThreeCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

    def _accumulation_range(self, df, ct) -> Tuple[Optional[float], Optional[float]]:
        cfg = self.config
        date = ct.date()
        start = pd.to_datetime(f"{date} {cfg.accumulation_start}").tz_localize("America/New_York", nonexistent="shift_forward")
        end = pd.to_datetime(f"{date} {cfg.accumulation_end}").tz_localize("America/New_York", nonexistent="shift_forward")
        if df.index.tz is not None:
            start, end = start.tz_convert(df.index.tz), end.tz_convert(df.index.tz)
        win = df.iloc[-600:]
        acc = win[(win.index >= start) & (win.index <= end)]
        if acc.empty:
            return None, None
        return float(acc["high"].max()), float(acc["low"].min())

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

        if not self._gate("distribution_window", self._in_window(t, cfg.distribution_start, cfg.distribution_end),
                          t.strftime("%H:%M"), "fora da distribuição"):
            return None
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        acc_high, acc_low = self._accumulation_range(df, ct)
        if not self._gate("accumulation_found", acc_high is not None, None, "sem range de acumulação"):
            return None

        bias = self._get_daily_bias(d1)
        bull = self._swept(df, acc_low, "low", cfg.sweep_window)    # manipula para baixo -> distribui BUY
        bear = self._swept(df, acc_high, "high", cfg.sweep_window)  # manipula para cima -> distribui SELL
        if cfg.require_daily_bias:
            bull = bull and bias == "BULLISH"
            bear = bear and bias == "BEARISH"

        if bull and not bear:
            action, sl_anchor, dol = "BUY", float(df.iloc[-cfg.sweep_window:]["low"].min()), acc_high + (acc_high - acc_low)
        elif bear and not bull:
            action, sl_anchor, dol = "SELL", float(df.iloc[-cfg.sweep_window:]["high"].max()), acc_low - (acc_high - acc_low)
        else:
            self._gate("po3_manipulation", False, f"bull={bull} bear={bear}", "sem AMD claro")
            return None

        self._gate("po3_manipulation", True, action, "AMD ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"PO3/AMD {action} bias={bias}",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.85)
