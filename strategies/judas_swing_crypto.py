"""
Judas Swing — Cripto
=====================
No início da sessão (London open 02:00 ou NY open ~09:30 EST), o algoritmo cria
um movimento FALSO (Judas) na direção contrária à real, varrendo o Asian Range,
e então reverte. Entrada na reversão pós-manipulação, stop além do extremo do
Judas, alvo no lado oposto.

Gates de qualidade:
  - Janela de abertura (London ou NY open)
  - Asian Range definido
  - Manipulação (sweep) de um lado do Asian Range
  - Reversão (close de volta para dentro do range)
  - R:R mínimo
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal


@dataclass
class JudasSwingCryptoConfig:
    london_start: time = time(2, 0)
    london_end: time = time(5, 0)
    ny_start: time = time(9, 30)
    ny_end: time = time(11, 30)
    min_rr: float = 2.0
    sweep_window: int = 4
    min_sl_distance_percent: float = 0.005
    sl_buffer_percent: float = 0.0015
    cooldown_minutes: int = 120


class JudasSwingCrypto(CryptoICTBase):
    name = "judas_swing_crypto"

    def __init__(self, config: JudasSwingCryptoConfig = None):
        self.config = config or JudasSwingCryptoConfig()
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

        in_open = self._in_window(t, cfg.london_start, cfg.london_end) or self._in_window(t, cfg.ny_start, cfg.ny_end)
        if not self._gate("open_window", in_open, t.strftime("%H:%M"), "fora da abertura"):
            return None
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        a_high, a_low = self._get_asian_range(df, ct)
        if not self._gate("asian_range", a_high is not None, None, "sem Asian Range"):
            return None

        # Judas: manipulação varre um lado e reverte
        bull = self._swept(df, a_low, "low", cfg.sweep_window)    # Judas para baixo -> real é BUY
        bear = self._swept(df, a_high, "high", cfg.sweep_window)  # Judas para cima -> real é SELL

        if bull and not bear:
            action, sl_anchor, dol = "BUY", float(df.iloc[-cfg.sweep_window:]["low"].min()), a_high
        elif bear and not bull:
            action, sl_anchor, dol = "SELL", float(df.iloc[-cfg.sweep_window:]["high"].max()), a_low
        else:
            self._gate("judas_manipulation", False, f"bull={bull} bear={bear}", "sem manipulação clara")
            return None

        self._gate("judas_manipulation", True, action, "Judas + reversão ok")
        self._last_signal_ts = ct
        return self._build_signal(action, price, sl_anchor, ct,
                                  f"Judas Swing {action} (asian sweep)",
                                  cfg.min_rr, cfg.min_sl_distance_percent, cfg.sl_buffer_percent,
                                  dol_target=dol, confidence=0.84)
