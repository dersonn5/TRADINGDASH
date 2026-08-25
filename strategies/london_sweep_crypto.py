"""
London Sweep — Cripto
======================
Adaptação cripto do modelo London Sweep. A sessão de Londres (02:00-09:30 EST)
varre (manipula) um lado do Asian Range; o preço reverte na direção real para
buscar a liquidez oposta na sessão de NY.

Gates de qualidade:
  - Janela de Londres / início de NY
  - Asian Range definido
  - Manipulação de Londres detectada (sweep de um lado)
  - Entrada na direção da reversão, stop além do extremo varrido
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class LondonSweepCryptoConfig:
    session_start: time = time(2, 0)
    session_end: time = time(11, 0)
    min_rr: float = 2.0
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 240


class LondonSweepCrypto(CryptoICTBase):
    name = "london_sweep_crypto"

    def __init__(self, config: LondonSweepCryptoConfig = None):
        self.config = config or LondonSweepCryptoConfig()
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

        if not self._gate("session_active", self._in_window(t, cfg.session_start, cfg.session_end),
                          t.strftime("%H:%M"), "fora da sessão"):
            return None
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        a_high, a_low = self._get_asian_range(df, ct)
        if not self._gate("asian_range", a_high is not None, None, "sem Asian Range"):
            return None

        manip = self._detect_london_manipulation(df, a_high, a_low, ct)  # BULLISH/BEARISH/NONE
        if not self._gate("london_manipulation", manip != "NONE", manip, "sem manipulação de Londres"):
            return None

        if manip == "BULLISH":
            action, sl_anchor, dol = "BUY", a_low, a_high
        else:
            action, sl_anchor, dol = "SELL", a_high, a_low

        self._gate("signal_generated", True, action, "London sweep ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"London Sweep {action} (asian {manip})",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.84)
