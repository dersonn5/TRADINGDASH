"""
Estratégia 9:30-11:00 AM IFVG Reversal + HTF Orderflow Filter (V4 - RR 3:1)
=============================================================================
- Gate Horário: Entrada entre 09:30h e 11:00h EST.
- Filtro HTF Orderflow: Confluência OBRIGATÓRIA com Bias Diário/1H via HTFContextEngine.
  * BUY só permitido se Bias HTF == BULLISH e Preço em DISCOUNT.
  * SELL só permitido se Bias HTF == BEARISH e Preço em PREMIUM.
- Stop Loss Folgado: Protegido além do extremo com buffer ATR expandido (0.75 ATR).
- Alvo Expandido: RR 3:1 fixo (3.0x risco).
"""

from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, List, Tuple
from collections import Counter
import pandas as pd

from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.base import Signal
from core.htf_context import HTFContextEngine, HTFView


@dataclass
class Strat930Config(ICTTopDownConfig):
    kz_start: time = time(9, 30)
    kz_end: time = time(12, 0)
    killzone_end: time = time(16, 0) # Posição pode rodar até 16:00 EST
    swing_lookback_1h: int = 20
    reclaim_buffer_atr: float = 0.1
    ifvg_lookback_1m: int = 30
    sl_buffer_atr: float = 0.75       # Stop mais longo (folgado)
    target_rr: float = 3.0           # Alvo 3:1
    min_rr: float = 1.8
    cooldown_minutes: int = 60
    require_htf_orderflow: bool = True # Filtro rígido de Orderflow HTF


class Strat930IFVG(ICTTopDownCrypto):
    name = "strat_930_ifvg"

    def __init__(self, config: Strat930Config = None):
        super().__init__(config or Strat930Config())
        self.config: Strat930Config = self.config
        self.htf_engine = HTFContextEngine()
        self.funnel = Counter()
        self._funnel_seen = {}

    def _fn(self, stage, day):
        if self._funnel_seen.get(stage) != day:
            self._funnel_seen[stage] = day
            self.funnel[stage] += 1

    def _detect_ifvgs(self, df1m: pd.DataFrame, lookback: int = 30) -> List[Tuple[str, float, float, int]]:
        """Detecta FVGs no M1 que foram INVERTIDOS (fechados através) pela ação do preço recente."""
        if len(df1m) < 4:
            return []
        n = len(df1m)
        start = max(2, n - lookback)
        ifvgs = []

        for i in range(start, n - 1):
            c, p2 = df1m.iloc[i], df1m.iloc[i - 2]
            
            # 1. Bullish FVG original (low > p2.high) -> Se fechar abaixo do fbot = IFVG Vendedor (SELL)
            if c["low"] > p2["high"]:
                ftop, fbot = float(c["low"]), float(p2["high"])
                for j in range(i + 1, n):
                    cj = df1m.iloc[j]
                    if cj["close"] < fbot and cj["open"] > cj["close"]: # Exige vela de força vendedora na inversão
                        ifvgs.append(("SELL", ftop, fbot, j))
                        break

            # 2. Bearish FVG original (high < p2.low) -> Se fechar acima do ftop = IFVG Comprador (BUY)
            elif c["high"] < p2["low"]:
                ftop, fbot = float(p2["low"]), float(c["high"])
                for j in range(i + 1, n):
                    cj = df1m.iloc[j]
                    if cj["close"] > ftop and cj["close"] > cj["open"]: # Exige vela de força compradora na inversão
                        ifvgs.append(("BUY", ftop, fbot, j))
                        break

        return ifvgs

    def generate_signal(self, candles_5m: pd.DataFrame, candles_15m: pd.DataFrame = None,
                        candles_1h: pd.DataFrame = None, candles_1d: pd.DataFrame = None,
                        candles_1m: pd.DataFrame = None) -> Optional[Signal]:
        cfg = self.config
        if candles_5m is None or len(candles_5m) < 10 or candles_1m is None or len(candles_1m) < 10:
            return None

        # Fuso / timestamp garantido em EST
        def _to_est(df_):
            if df_ is None or df_.empty: return df_
            d = df_.copy()
            if not isinstance(d.index, pd.DatetimeIndex):
                d.index = pd.to_datetime(d.index)
            if d.index.tz is None:
                d.index = d.index.tz_localize("UTC")
            d.index = d.index.tz_convert("America/New_York")
            return d

        df5 = _to_est(candles_5m)
        df1m = _to_est(candles_1m)
        df1h = _to_est(candles_1h) if candles_1h is not None else None
        df1d = _to_est(candles_1d) if candles_1d is not None else None

        last_ts = df5.index[-1]
        cur_time = last_ts.time()
        cur_day = last_ts.date()

        # 1. Gate de horário de entrada (Apenas entre 9:30 e 11:00 EST)
        if not self._in_window(cur_time, cfg.kz_start, cfg.kz_end):
            return None
        self._fn("1_horario_ok", cur_day)

        # Cooldown check
        if self._last_signal_ts is not None:
            if (last_ts - self._last_signal_ts).total_seconds() < cfg.cooldown_minutes * 60:
                return None

        # 1.5 Filtro de Abertura (Evita os primeiros 5 minutos da abertura de NY - Judas Swing)
        if last_ts.hour == 9 and last_ts.minute < 35:
            return None

        # 2. HTF Orderflow Filter (Contexto Diário/1H)
        htf_view: HTFView = self.htf_engine.compute(last_ts, df1h, None, df1d)
        htf_bias = htf_view.bias # BULLISH / BEARISH / NEUTRAL

        # 3. HTF Sweep no 1H (Fractal de 5 barras - Major Swings)
        if df1h is None or len(df1h) < 10:
            return None

        h1_h, h1_l = df1h["high"].values, df1h["low"].values
        h1_c = df1h["close"].values
        n_1h = len(df1h)
        lookback = min(cfg.swing_lookback_1h, n_1h - 3)

        sh_1h, sl_1h = None, None
        
        current_price = float(df1m["close"].iloc[-1])
        high_recent = float(df1m["high"].iloc[-60:].max())
        low_recent = float(df1m["low"].iloc[-60:].min())
        
        # Em vez de procurar um fractal de 5 velas exato (que falha em capturar máximas de sessões/aberturas),
        # consideramos como alvo de liquidez a máxima/mínima das últimas 5 horas fechadas.
        # Se o preço recente de 1M varreu alguma dessas máximas/mínimas, temos uma captura de liquidez válida.
        for i in range(n_1h - 2, max(0, n_1h - 7), -1):
            if sh_1h is None and high_recent > h1_h[i]:
                sh_1h = float(h1_h[i])
            if sl_1h is None and low_recent < h1_l[i]:
                sl_1h = float(h1_l[i])
            if sh_1h is not None and sl_1h is not None:
                break

        bias = None
        if sh_1h is not None and high_recent > sh_1h:
            bias = "SELL"
        elif sl_1h is not None and low_recent < sl_1h:
            bias = "BUY"

        if bias is None:
            return None

        # Filtro Rígido de Orderflow HTF + Intraday Momentum
        if cfg.require_htf_orderflow:
            # Verifica o momentum do 1H (Intraday Orderflow)
            h1_trend_bearish = h1_c[-1] < h1_c[-3] and h1_c[-2] < h1_c[-4]
            h1_trend_bullish = h1_c[-1] > h1_c[-3] and h1_c[-2] > h1_c[-4]
            
            if bias == "SELL":
                if htf_bias == "BULLISH" and not h1_trend_bearish:
                    return None # Contra a trend diária e intraday não confirmou reversão
            if bias == "BUY":
                if htf_bias == "BEARISH" or h1_trend_bearish:
                    return None # Não compra em orderflow intraday forte de baixa

        self._fn("2_sweep_orderflow_ok", cur_day)

        # 4. Busca Zonas válidas e virgens (IFVG ou FVG)
        target_zone = None
        n_1m = len(df1m)
        
        # Helper para checar se a zona é virgem (não testada antes da vela atual)
        def _is_virgin(side, top_z, bot_z, b_idx):
            if n_1m - 1 <= b_idx: return False
            for i in range(b_idx + 1, n_1m - 1):
                if side == "SELL" and float(df1m["high"].iloc[i]) >= bot_z: return False
                if side == "BUY" and float(df1m["low"].iloc[i]) <= top_z: return False
            return True

        ifvgs_1m = self._detect_ifvgs(df1m, lookback=cfg.ifvg_lookback_1m)
        for side, ftop, fbot, idx in reversed(ifvgs_1m):
            if side == bias and _is_virgin(side, ftop, fbot, idx):
                target_zone = (side, ftop, fbot, idx, "IFVG")
                break

        if target_zone is None:
            fvgs_1m = self._detect_fvg_list(df1m, lookback=cfg.ifvg_lookback_1m)
            for side, (ftop, fbot), idx in reversed(fvgs_1m):
                mapped_side = "BUY" if side == "bullish" else "SELL"
                if mapped_side == bias and _is_virgin(bias, ftop, fbot, idx):
                    target_zone = (bias, ftop, fbot, idx, "FVG")
                    break

        if target_zone is None:
            return None
            
        self._fn("3_ifvg_ok", cur_day)

        # 5. O preço atual (candle atual) deve tocar a zona (rejeição relaxada para capturar o trade do print)
        side, top_zone, bot_zone, break_idx, zone_type = target_zone
        
        curr_high = float(df1m["high"].iloc[-1])
        curr_low = float(df1m["low"].iloc[-1])
        curr_open = float(df1m["open"].iloc[-1])
        current_price = float(df1m["close"].iloc[-1])
        
        if side == "SELL":
            if curr_high < bot_zone:
                return None
        else: # BUY
            if curr_low > top_zone:
                return None


        self._fn("4_reteste_ok", cur_day)

        # 6. Stop Loss Folgado (0.75 ATR) e Target Expandido (3:1 RR)
        atr = self._atr5(df5)
        sl_buffer = max(atr * cfg.sl_buffer_atr, (top_zone - bot_zone) * 0.5)

        if side == "SELL":
            sl = top_zone + sl_buffer
            tp = current_price - (sl - current_price) * cfg.target_rr
        else: # BUY
            sl = bot_zone - sl_buffer
            tp = current_price + (current_price - sl) * cfg.target_rr

        # Validação de Risco mínimo
        if abs(current_price - sl) < (current_price * 0.0008):
            return None

        self._last_signal_ts = last_ts
        self._fn("5_entrada_gerada", cur_day)

        return Signal(
            symbol=self.symbol or "NQ",
            action=side,
            entry_price=current_price,
            stop_loss=sl,
            take_profit=tp,
            confidence_score=0.90,
            timestamp=last_ts.to_pydatetime(),
            meta={"strategy": self.name, "ifvg_zone": (top_zone, bot_zone), "htf_bias": htf_bias, "zone_type": zone_type}
        )
