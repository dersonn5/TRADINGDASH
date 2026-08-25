"""
CryptoICTBase — Base compartilhada das estratégias ICT de cripto
================================================================
Centraliza os detectores comuns (FVG, swing/MSS, OTE fib, daily bias,
killzone, sweep, construção de Signal) para que cada modelo ICT novo
fique enxuto e consistente. Padroniza o que antes estava duplicado em
cada arquivo de estratégia.

Convenção de fuso: todos os timeframes trabalham em America/New_York (EST/EDT),
pois as Killzones e Macros do ICT são definidas no horário de Nova York.
"""

from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple, List

import pandas as pd

from strategies.base import Strategy, Signal


class CryptoICTBase(Strategy):
    """Base com helpers ICT reutilizáveis para cripto (BTC/ETH perpétuos)."""

    # ─── Tempo / fuso ────────────────────────────────────────────────────
    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None and \
           str(df.index.tz) in ["America/New_York", "EST5EDT"]:
            return df
        d = df.copy()
        if not isinstance(d.index, pd.DatetimeIndex):
            d.index = pd.to_datetime(d.index)
        if d.index.tz is None:
            d.index = d.index.tz_localize("UTC").tz_convert("America/New_York")
        else:
            d.index = d.index.tz_convert("America/New_York")
        return d

    @staticmethod
    def _in_window(t: time, start: time, end: time) -> bool:
        return start <= t < end

    # ─── Viés diário ─────────────────────────────────────────────────────
    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        """Bias pela vela diária ANTERIOR (sem look-ahead): close forte na direção."""
        if len(candles_1d) < 2:
            return "NEUTRAL"
        last = candles_1d.iloc[-2]
        close, open_v, high, low = last["close"], last["open"], last["high"], last["low"]
        rng = high - low if high > low else 1.0
        if close > open_v and (high - close) / rng < 0.3:
            return "BULLISH"
        if close < open_v and (close - low) / rng < 0.3:
            return "BEARISH"
        return "NEUTRAL"

    def _ema(self, closes: pd.Series, span: int = 200) -> float:
        if len(closes) >= span * 3:
            return float(closes.iloc[-span * 3:].ewm(span=span, adjust=False).mean().iloc[-1])
        if len(closes) >= span:
            return float(closes.ewm(span=span, adjust=False).mean().iloc[-1])
        return float(closes.mean())

    # ─── Swing / MSS ─────────────────────────────────────────────────────
    def _detect_mss_and_swing(self, df_5m: pd.DataFrame, lookback: int = 20
                              ) -> Tuple[Optional[float], Optional[float]]:
        """Swing high/low fractais (3 velas) mais recentes em M5."""
        if len(df_5m) < 4:
            return None, None
        highs = df_5m["high"].values
        lows = df_5m["low"].values
        n = len(df_5m)
        start_idx = max(2, n - lookback - 1)
        sh = sl = None
        for i in range(n - 2, start_idx, -1):
            if sh is None and highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                sh = float(highs[i])
            if sl is None and lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                sl = float(lows[i])
            if sh is not None and sl is not None:
                break
        return sh, sl

    # ─── FVG ─────────────────────────────────────────────────────────────
    def _detect_active_fvg(self, df_5m: pd.DataFrame, lookback: int = 6
                           ) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        """FVG ativo (não mitigado) mais recente. Retorna (dir, (top, bottom))."""
        fvgs = self._detect_fvg_list(df_5m, lookback)
        if not fvgs:
            return None, None
        d, bounds, _ = fvgs[0]
        return d, bounds

    def _detect_fvg_list(self, df_5m: pd.DataFrame, lookback: int = 15
                         ) -> List[Tuple[str, Tuple[float, float], int]]:
        """Lista de FVGs ativos (não mitigados) nos últimos `lookback` candles.
        Item: (dir, (top, bottom), idx_da_vela_central)."""
        if len(df_5m) < 4:
            return []
        n = len(df_5m)
        start = max(2, n - lookback)
        out = []
        for i in range(n - 1, start, -1):
            c, p2 = df_5m.iloc[i], df_5m.iloc[i - 2]
            if c["low"] > p2["high"]:  # bullish FVG
                top, bot = float(c["low"]), float(p2["high"])
                if not any(df_5m.iloc[j]["close"] < bot for j in range(i + 1, n)):
                    out.append(("bullish", (top, bot), i))
            elif c["high"] < p2["low"]:  # bearish FVG
                top, bot = float(p2["low"]), float(c["high"])
                if not any(df_5m.iloc[j]["close"] > top for j in range(i + 1, n)):
                    out.append(("bearish", (top, bot), i))
        return out

    # ─── OTE (fib retracement zone) ──────────────────────────────────────
    @staticmethod
    def _ote_zone(swing_low: float, swing_high: float, direction: str,
                  lo: float = 0.62, hi: float = 0.79) -> Tuple[float, float]:
        """Zona OTE entre 62% e 79% do impulso.
        BUY: retração para baixo num impulso de alta (low->high).
        SELL: retração para cima num impulso de baixa (high->low)."""
        rng = swing_high - swing_low
        if direction == "BUY":
            return swing_high - rng * hi, swing_high - rng * lo   # (zona_baixo, zona_topo)
        return swing_low + rng * lo, swing_low + rng * hi          # (zona_baixo, zona_topo)

    # ─── 24h range / sweep ───────────────────────────────────────────────
    def _get_range(self, df_5m: pd.DataFrame, lookback: int = 288
                   ) -> Tuple[Optional[float], Optional[float]]:
        if len(df_5m) < lookback + 1:
            return None, None
        recent = df_5m.iloc[-(lookback + 1):-1]
        return float(recent["high"].max()), float(recent["low"].min())

    @staticmethod
    def _swept(df_5m: pd.DataFrame, level: float, side: str, window: int = 3) -> bool:
        """side='high': varreu acima e fechou abaixo (bearish sweep).
        side='low': varreu abaixo e fechou acima (bullish sweep)."""
        w = df_5m.iloc[-window:]
        last_close = float(df_5m.iloc[-1]["close"])
        if side == "high":
            return float(w["high"].max()) > level and last_close < level
        return float(w["low"].min()) < level and last_close > level

    # ─── SMT Divergence (Smart Money Technique) ──────────────────────────
    def _smt_divergence(self, df_5m: pd.DataFrame, df_corr: pd.DataFrame, direction: str,
                        window: int = 5) -> bool:
        """Divergência SMT entre o ativo e o correlacionado (BTC/ETH).
        BUY:  um faz lower low, o outro NÃO (não confirma) → força de alta.
        SELL: um faz higher high, o outro NÃO → fraqueza de alta.
        df_corr vem de self.correlated_data (injetado pelo engine)."""
        if df_corr is None or len(df_corr) < 2 * window or len(df_5m) < 2 * window:
            return False
        us_now, us_prev = df_5m.iloc[-window:], df_5m.iloc[-2 * window:-window]
        co_now, co_prev = df_corr.iloc[-window:], df_corr.iloc[-2 * window:-window]
        if direction == "BUY":
            us_ll = us_now["low"].min() < us_prev["low"].min()
            co_ll = co_now["low"].min() < co_prev["low"].min()
            return us_ll != co_ll        # um fez nova mínima, o outro não
        else:
            us_hh = us_now["high"].max() > us_prev["high"].max()
            co_hh = co_now["high"].max() > co_prev["high"].max()
            return us_hh != co_hh

    # ─── Construção de Signal com SL/TP padronizados ─────────────────────
    def _build_signal(self, action: str, entry: float, sl_anchor: float,
                      current_time: datetime, reason: str,
                      min_rr: float, min_sl_pct: float, sl_buffer_pct: float = 0.0,
                      dol_target: Optional[float] = None, confidence: float = 0.85
                      ) -> Optional[Signal]:
        """Monta Signal aplicando buffer, SL mínimo e R:R. Retorna None se R:R falhar."""
        if action == "BUY":
            sl = sl_anchor * (1.0 - sl_buffer_pct)
            sl_dist = entry - sl
            min_sl = entry * min_sl_pct
            if sl_dist < min_sl:
                sl = entry - min_sl
                sl_dist = min_sl
            tp = dol_target if (dol_target and dol_target > entry) else entry + sl_dist * min_rr
        else:
            sl = sl_anchor * (1.0 + sl_buffer_pct)
            sl_dist = sl - entry
            min_sl = entry * min_sl_pct
            if sl_dist < min_sl:
                sl = entry + min_sl
                sl_dist = min_sl
            tp = dol_target if (dol_target and dol_target < entry) else entry - sl_dist * min_rr

        if sl_dist <= 0:
            return None
        rr = abs(tp - entry) / sl_dist
        if not self._gate("min_rr_passed", rr >= min_rr, f"RR={rr:.2f}", f"R:R < {min_rr}"):
            return None

        return Signal(
            symbol=self.symbol, action=action,
            entry_price=round(entry, 2), stop_loss=round(sl, 2), take_profit=round(tp, 2),
            confidence_score=confidence, reasoning=f"{reason} | RR={rr:.2f}",
            timestamp=current_time.to_pydatetime() if hasattr(current_time, "to_pydatetime") else current_time,
        )
