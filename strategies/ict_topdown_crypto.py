"""
ICT Top-Down Sniper — Cripto (v2)
==================================
O modelo ICT COMPLETO, em 3 camadas:

  1. CONTEXTO HTF (1h/4h/Diário) — bias, premium/discount, PD array, DOL (alvo).
     O institucional atua aqui. Só operamos NA direção do bias, no lado certo
     (discount p/ compra, premium p/ venda), DENTRO de um PD array HTF, mirando o DOL.

  2. SETUP 5m — varredura de liquidez (sweep) + quebra de estrutura (MSS) no 5m,
     acontecendo dentro do array HTF.

  3. CONFIRMATION ENTRY 1m — desce pro 1m: MSS de 1m + FVG de 1m = gatilho.
     Entrada no FVG do 1m, STOP curto mas FOLGADO (estrutura do 1m + buffer),
     ALVO = DOL do HTF (longe) → R:R alto, exposição baixa. Sniper.

Anti-look-ahead: tudo cortado por timestamp. Engine chama por vela 5m, passando
o histórico de 1m até o momento.
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional
import pandas as pd

from strategies.ict_crypto_base import CryptoICTBase
from strategies.base import Signal
from core.htf_context import HTFContextEngine


@dataclass
class ICTTopDownConfig:
    killzone_start: time = time(2, 0)
    killzone_end: time = time(16, 0)
    require_killzone: bool = True
    require_smt: bool = True             # (mantido p/ compat; SMT agora pontua no score)
    min_score: float = 60.0             # threshold de qualidade (confluências) — sniper
    displacement_atr: float = 0.8       # corpo da vela de MSS vs ATR p/ "MSS claro"
    # Alvo: "dol" = extremo HTF distante (RR alto, WR baixo) | "intermediate" = mais curto (WR alto)
    target_mode: str = "intermediate"
    target_rr: float = 3.0              # RR do alvo no modo intermediário (mais curto que o DOL)
    min_rr: float = 1.8                 # piso de RR aceitável
    # stop 1m: curto mas folgado
    sl_buffer_percent: float = 0.0015    # buffer além da estrutura do 1m
    min_sl_distance_percent: float = 0.003   # piso de stop (0.3%) — nunca raspando
    max_sl_distance_percent: float = 0.015   # teto de stop (1.5%) — senão não é 1m
    sweep_window_5m: int = 8         # janela p/ o sweep ter ocorrido
    mss_window_5m: int = 5           # janela p/ o MSS ter ocorrido (após o sweep)
    swing_lookback_5m: int = 30
    pd_tolerance: float = 0.15       # banda de tolerância no equilíbrio (15% do range)
    confirm_lookback_1m: int = 15
    cooldown_minutes: int = 60


class ICTTopDownCrypto(CryptoICTBase):
    name = "ict_topdown_crypto"

    def __init__(self, config: ICTTopDownConfig = None):
        self.config = config or ICTTopDownConfig()
        self._last_signal_ts: Optional[datetime] = None
        self._htf = HTFContextEngine()
        self._htf_cache_key = None       # (hora) — HTF só muda quando fecha vela de 1h
        self._htf_cache_view = None
        self._last_quality = None

    def _atr5(self, df, period: int = 14) -> float:
        if df is None or len(df) < period + 1:
            return 0.0
        h, l = df["high"].iloc[-period:], df["low"].iloc[-period:]
        c = df["close"].shift(1).iloc[-period:]
        import pandas as _pd
        tr = _pd.concat([(h - l).abs(), (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
        return float(tr.mean())

    def _htf_view_cached(self, ct, h1, d1):
        """Recomputa o contexto HTF só quando muda a hora (não a cada vela 5m)."""
        key = (ct.year, ct.month, ct.day, ct.hour)
        if key != self._htf_cache_key:
            h4 = (h1.resample("4h").agg({"open": "first", "high": "max", "low": "min",
                                         "close": "last", "volume": "sum"}).dropna()
                  if h1 is not None and not h1.empty else None)
            self._htf_cache_view = self._htf.compute(ct, h1, h4, d1)
            self._htf_cache_key = key
        return self._htf_cache_view

    def _confirm_1m(self, df1m: pd.DataFrame, direction: str):
        """Procura confirmation entry no 1m: FVG de 1m na direção, não-mitigado.
        Retorna (entry_zone_top, entry_zone_bottom, swing_anchor) ou None."""
        if df1m is None or len(df1m) < 5:
            return None
        want = "bullish" if direction == "BUY" else "bearish"
        fvgs = self._detect_fvg_list(df1m, lookback=self.config.confirm_lookback_1m)
        for fdir, (ftop, fbot), idx in fvgs:
            if fdir != want:
                continue
            # MSS de 1m: para BUY, a vela do FVG rompeu o high anterior; aproximação:
            # exige que o FVG seja recente e que o preço atual ainda esteja perto dele
            if direction == "BUY":
                anchor = float(df1m.iloc[max(0, idx - 3):idx + 1]["low"].min())
                return ftop, fbot, anchor
            else:
                anchor = float(df1m.iloc[max(0, idx - 3):idx + 1]["high"].max())
                return ftop, fbot, anchor
        return None

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        self._reset_gates()
        cfg = self.config

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty), None, "dados vazios"):
            return None
        if not self._gate("has_1m", candles_1m is not None and not candles_1m.empty, None, "sem candles 1m"):
            return None

        df5 = self._convert_to_est(candles_5m)
        d1 = self._convert_to_est(candles_1d)
        h1 = self._convert_to_est(candles_1h)
        m1 = self._convert_to_est(candles_1m)
        ct = df5.index[-1]
        t = ct.time()
        price = float(df5.iloc[-1]["close"])

        # GATE killzone
        if cfg.require_killzone and not self._gate(
                "killzone", self._in_window(t, cfg.killzone_start, cfg.killzone_end),
                t.strftime("%H:%M"), "fora da killzone"):
            return None

        # GATE cooldown
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        # ── Camada 1: contexto HTF (cacheado por hora) ──
        view = self._htf_view_cached(ct, h1, d1)
        if not self._gate("htf_bias", view.bias != "NEUTRAL", view.bias, "bias HTF neutro"):
            return None

        direction = "BUY" if view.bias == "BULLISH" else "SELL"
        pd_state = self._htf.pd_state(price, view)

        # DOL (alvo) — MÍNIMO DURO: sem alvo HTF não há trade
        dol = view.dol_target
        dol_ok = dol is not None and ((direction == "BUY" and dol > price) or (direction == "SELL" and dol < price))
        if not self._gate("dol_valid", dol_ok, str(dol), "DOL inválido/sem alvo"):
            return None

        # ── Calcular TODAS as confluências (não corta — pontua) ──
        eq = view.equilibrium
        band = (view.range_high - view.range_low) * cfg.pd_tolerance if view.range_high > view.range_low else 0
        side_ok = (price <= eq + band) if direction == "BUY" else (price >= eq - band)

        arr = view.discount_array_at(price, "bullish" if direction == "BUY" else "bearish")

        rng_high, rng_low = self._get_range(df5, 288)
        sh, sl = self._detect_mss_and_swing(df5, lookback=cfg.swing_lookback_5m)
        w, mw = cfg.sweep_window_5m, cfg.mss_window_5m
        recent_closes = df5.iloc[-mw:]["close"]
        if direction == "BUY":
            swept = rng_low is not None and float(df5.iloc[-w:]["low"].min()) < rng_low
            mss = sh is not None and float(recent_closes.max()) > sh
        else:
            swept = rng_high is not None and float(df5.iloc[-w:]["high"].max()) > rng_high
            mss = sl is not None and float(recent_closes.min()) < sl

        # MSS claro = quebra COM displacement (corpo forte vs ATR)
        atr = self._atr5(df5, 14)
        body = abs(float(df5.iloc[-1]["close"]) - float(df5.iloc[-1]["open"]))
        mss_clear = mss and atr > 0 and body >= atr * cfg.displacement_atr

        # SMT
        corr = getattr(self, "correlated_data", None)
        smt = self._smt_divergence(df5, self._convert_to_est(corr) if corr is not None else None, direction)

        # imbalance (FVG 5m na direção) + BPR (1m)
        fdir, _ = self._detect_active_fvg(df5, lookback=8)
        imbalance = fdir == ("bullish" if direction == "BUY" else "bearish")
        bpr_top, bpr_bot = self._detect_bpr_m1(m1, lookback=20) if m1 is not None else (None, None)
        bpr = bpr_top is not None

        # killzone prime (London open / NY silver bullet)
        prime = self._in_window(t, time(2, 0), time(5, 0)) or self._in_window(t, time(10, 0), time(11, 0))

        confluences = {
            "htf_aligned":      True,                 # direção = bias HTF (já garantido)
            "premium_discount": side_ok,
            "in_htf_array":     arr is not None,
            "liquidity_quality": swept,
            "killzone_prime":   prime,
            "mss_clear":        mss_clear,
            "smt_divergence":   smt,
            "imbalance_fvg":    imbalance,
            "bpr":              bpr,
        }
        from core.entry_quality import score_entry
        quality = score_entry(confluences)
        self._last_quality = quality

        # GATE de QUALIDADE — só A+ (score >= threshold) = sniper
        if not self._gate("quality_score", quality.score >= cfg.min_score,
                          quality.summary(), f"score {quality.score:.0f} < {cfg.min_score}"):
            return None

        # ── Camada 3: confirmation entry 1m (MÍNIMO DURO — é o gatilho) ──
        conf = self._confirm_1m(m1, direction)
        if not self._gate("confirm_1m", conf is not None, None, "sem confirmation entry no 1m"):
            return None
        ftop, fbot, anchor = conf

        # SL curto mas folgado: estrutura do 1m + buffer, dentro de piso/teto
        if direction == "BUY":
            sl_price = anchor * (1.0 - cfg.sl_buffer_percent)
            sl_dist = price - sl_price
        else:
            sl_price = anchor * (1.0 + cfg.sl_buffer_percent)
            sl_dist = sl_price - price

        floor_sl = price * cfg.min_sl_distance_percent
        ceil_sl = price * cfg.max_sl_distance_percent
        if sl_dist < floor_sl:
            sl_dist = floor_sl
            sl_price = price - floor_sl if direction == "BUY" else price + floor_sl
        if not self._gate("sl_in_band", sl_dist <= ceil_sl, f"sl_dist={sl_dist:.2f} ceil={ceil_sl:.2f}",
                          "stop largo demais p/ entrada de 1m"):
            return None

        # alvo: DOL distante OU intermediário (mais curto = winrate maior), sem ultrapassar o DOL
        if cfg.target_mode == "intermediate":
            if direction == "BUY":
                tp = min(price + sl_dist * cfg.target_rr, dol)
            else:
                tp = max(price - sl_dist * cfg.target_rr, dol)
        else:
            tp = dol
        rr = abs(tp - price) / sl_dist if sl_dist > 0 else 0.0
        if not self._gate("min_rr", rr >= cfg.min_rr, f"RR={rr:.2f}", f"R:R < {cfg.min_rr}"):
            return None

        self._last_signal_ts = ct
        self._gate("signal_generated", True, direction, "top-down sniper ok")
        reason = (f"ICT TopDown {direction} | bias={view.bias} | quality={quality.summary()} "
                  f"| 1m entry | DOL={tp:.2f} RR={rr:.2f}")
        meta = {
            "direction": direction,
            "quality_score": quality.score,
            "quality_grade": quality.grade,
            "confluences": quality.breakdown,
            "equilibrium": eq,
            "range_high": rng_high, "range_low": rng_low,
            "swept_level": (rng_low if direction == "BUY" else rng_high),
            # pontos LOCAIS que originam a entrada (visualmente perto da ação):
            "swept_local": (sl if direction == "BUY" else sh),   # liquidez local varrida
            "mss_level":   (sh if direction == "BUY" else sl),   # swing rompido (MSS)
            "swing_high": sh, "swing_low": sl,
            "dol": tp,
            "htf_array": ({"top": arr.top, "bottom": arr.bottom, "tf": arr.tf, "kind": arr.kind}
                          if arr is not None else None),
            "fvg_1m": {"top": ftop, "bottom": fbot},
            "bias": view.bias,
        }
        return Signal(
            symbol=self.symbol, action=direction,
            entry_price=round(price, 2), stop_loss=round(sl_price, 2), take_profit=round(tp, 2),
            confidence_score=0.92, reasoning=reason, meta=meta,
            timestamp=ct.to_pydatetime() if hasattr(ct, "to_pydatetime") else ct,
        )
