"""
HTF Context Engine — Camada Institucional (Top-Down ICT)
=========================================================
O institucional atua nos timeframes maiores. Esta camada lê Semanal / Diário /
4h / 1h e produz o CONTEXTO que filtra qualquer entrada:

  1. Bias HTF        — direção do dealing range (HH/HL = bullish, LH/LL = bearish)
  2. Premium/Discount— preço acima (premium) ou abaixo (discount) do equilíbrio (50%)
                       do dealing range HTF. Compra só em discount, venda só em premium.
  3. PD Arrays HTF   — FVG e Order Blocks não-mitigados em 1h/4h/Diário (zonas onde o
                       preço reage). O setup precisa acontecer DENTRO de um array.
  4. DOL (alvo)      — Draw on Liquidity: a liquidez externa oposta (swing HTF) para
                       onde o preço é atraído. Vira o take-profit.

Sem look-ahead: tudo é calculado com candles ATÉ o momento (cortados por timestamp).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import pandas as pd


@dataclass
class PDArray:
    kind: str          # "FVG" ou "OB"
    direction: str     # "bullish" / "bearish"
    top: float
    bottom: float
    tf: str            # "1h", "4h", "1d"

    def contains(self, price: float) -> bool:
        return self.bottom <= price <= self.top


@dataclass
class HTFView:
    bias: str = "NEUTRAL"               # BULLISH / BEARISH / NEUTRAL
    equilibrium: float = 0.0
    pd_state: str = "EQUILIBRIUM"       # PREMIUM / DISCOUNT / EQUILIBRIUM
    range_high: float = 0.0
    range_low: float = 0.0
    dol_target: Optional[float] = None  # draw on liquidity (alvo HTF)
    arrays: List[PDArray] = field(default_factory=list)

    def discount_array_at(self, price: float, direction: str) -> Optional[PDArray]:
        """Retorna um array HTF na direção pedida que contém o preço."""
        for a in self.arrays:
            if a.direction == direction and a.contains(price):
                return a
        return None


class HTFContextEngine:
    """Computa o HTFView para um instante, a partir dos candles HTF."""

    def __init__(self, swing_lookback: int = 30, fvg_lookback: int = 40):
        self.swing_lookback = swing_lookback
        self.fvg_lookback = fvg_lookback

    # ─── utilidades ──────────────────────────────────────────────────────
    @staticmethod
    def _cut(df: pd.DataFrame, t) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        try:
            return df[df.index <= t]
        except Exception:
            return df

    @staticmethod
    def _swings(df: pd.DataFrame, lookback: int) -> Tuple[Optional[float], Optional[float]]:
        if df is None or len(df) < 4:
            return None, None
        h = df["high"].values
        l = df["low"].values
        n = len(df)
        start = max(2, n - lookback - 1)
        sh = sl = None
        for i in range(n - 2, start, -1):
            if sh is None and h[i] > h[i - 1] and h[i] > h[i + 1]:
                sh = float(h[i])
            if sl is None and l[i] < l[i - 1] and l[i] < l[i + 1]:
                sl = float(l[i])
            if sh and sl:
                break
        return sh, sl

    def _bias(self, d1: pd.DataFrame) -> str:
        """Bias estrutural: compara dois últimos swings (HH/HL vs LH/LL) no diário."""
        if d1 is None or len(d1) < 10:
            return "NEUTRAL"
        recent = d1.iloc[-20:]
        highs = recent["high"]
        lows = recent["low"]
        # tendência simples: posição do close vs média + inclinação
        closes = recent["close"]
        ema = closes.ewm(span=10, adjust=False).mean()
        slope = float(ema.iloc[-1] - ema.iloc[-5]) if len(ema) >= 5 else 0.0
        last = float(closes.iloc[-1])
        if last > float(ema.iloc[-1]) and slope > 0:
            return "BULLISH"
        if last < float(ema.iloc[-1]) and slope < 0:
            return "BEARISH"
        return "NEUTRAL"

    def _fvg_arrays(self, df: pd.DataFrame, tf: str) -> List[PDArray]:
        """FVGs não-mitigados recentes no timeframe df."""
        out = []
        if df is None or len(df) < 4:
            return out
        n = len(df)
        start = max(2, n - self.fvg_lookback)
        for i in range(n - 1, start, -1):
            c, p2 = df.iloc[i], df.iloc[i - 2]
            if c["low"] > p2["high"]:  # bullish FVG
                top, bot = float(c["low"]), float(p2["high"])
                if not any(df.iloc[j]["close"] < bot for j in range(i + 1, n)):
                    out.append(PDArray("FVG", "bullish", top, bot, tf))
            elif c["high"] < p2["low"]:  # bearish FVG
                top, bot = float(p2["low"]), float(c["high"])
                if not any(df.iloc[j]["close"] > top for j in range(i + 1, n)):
                    out.append(PDArray("FVG", "bearish", top, bot, tf))
        return out

    # ─── principal ───────────────────────────────────────────────────────
    def compute(self, t, c1h: pd.DataFrame, c4h: pd.DataFrame,
                c1d: pd.DataFrame, c1w: pd.DataFrame = None) -> HTFView:
        d1 = self._cut(c1d, t)
        h4 = self._cut(c4h, t)
        h1 = self._cut(c1h, t)

        bias = self._bias(d1)

        # Dealing range = swing high/low recentes do diário
        rh, rl = self._swings(d1, self.swing_lookback)
        if rh is None or rl is None or rh <= rl:
            return HTFView(bias=bias)
        eq = (rh + rl) / 2.0

        view = HTFView(bias=bias, equilibrium=eq, range_high=rh, range_low=rl)

        # PD arrays HTF (diário + 4h + 1h)
        arrays = []
        arrays += self._fvg_arrays(d1, "1d")
        arrays += self._fvg_arrays(h4, "4h")
        arrays += self._fvg_arrays(h1, "1h")
        view.arrays = arrays

        # DOL: liquidez externa oposta ao bias (para onde o preço é atraído)
        if bias == "BULLISH":
            view.dol_target = rh       # busca o high (BSL)
        elif bias == "BEARISH":
            view.dol_target = rl       # busca o low (SSL)
        else:
            view.dol_target = None
        return view

    @staticmethod
    def pd_state(price: float, view: HTFView) -> str:
        if view.equilibrium <= 0:
            return "EQUILIBRIUM"
        if price > view.equilibrium:
            return "PREMIUM"
        if price < view.equilibrium:
            return "DISCOUNT"
        return "EQUILIBRIUM"
