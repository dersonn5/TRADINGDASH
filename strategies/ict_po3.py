"""
ICT PO3 + Market Maker Model + SMT — estratégia SEPARADA (candidata)
====================================================================
NÃO altera a validada (ict_topdown_crypto). Subclasse isolada.

Tese testada aqui = PO3/MMM explícito:
  ACUMULAÇÃO (sessão Ásia forma a range) -> MANIPULAÇÃO (Londres/NY varrem essa
  range = judas real) -> DISTRIBUIÇÃO (MSS + entrega pelo FVG até o DOL).

Diferença vs validada: PO3 e SMT entram como GATE DURO (não +score que afrouxa
o gate — foi o que estragou o momentum). Só opera o setup quando:
  - a manipulação varreu a range de acumulação da Ásia (po3_manip), E
  - SMT confirma (smt_gate), se ligado.
Seleção mais ESTRITA -> menos trades, hipótese = maior qualidade. Head-to-head
vs validada no holdout cego decide. Scoring idêntico ao validado (9 confluências,
score_entry read-only) — PO3/SMT são filtros ADICIONAIS, não mexem no score.
"""
from dataclasses import dataclass
from datetime import time
from typing import Optional
import pandas as pd

from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.base import Signal


@dataclass
class ICTPo3Config(ICTTopDownConfig):
    require_po3: bool = True      # manipulação tem que varrer a range de acumulação (Ásia)
    smt_gate: bool = True         # SMT vira gate duro (não só pontua)
    asia_start_hour: int = 20     # início da acumulação Ásia (ET)
    asia_end_hour: int = 24       # fim (exclusivo) — 20,21,22,23


class ICTPo3(ICTTopDownCrypto):
    name = "ict_po3"

    def __init__(self, config: ICTPo3Config = None):
        super().__init__(config or ICTPo3Config())

    def _asia_range(self, df5):
        """Range de acumulação da sessão asiática nas últimas ~24h.
        Retorna (high, low) — a liquidez que a manipulação de Londres/NY varre."""
        try:
            cfg = self.config
            recent = df5.iloc[-288:]                       # 24h de velas 5m
            hrs = recent.index.hour
            sub = recent[(hrs >= cfg.asia_start_hour) & (hrs < cfg.asia_end_hour)]
            if len(sub) < 3:
                return None, None
            return float(sub["high"].max()), float(sub["low"].min())
        except Exception:
            return None, None

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

        if cfg.require_killzone and not self._gate(
                "killzone", self._in_window(t, cfg.killzone_start, cfg.killzone_end),
                t.strftime("%H:%M"), "fora da killzone"):
            return None

        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        # ── Camada 1: contexto HTF ──
        view = self._htf_view_cached(ct, h1, d1)
        if not self._gate("htf_bias", view.bias != "NEUTRAL", view.bias, "bias HTF neutro"):
            return None

        direction = "BUY" if view.bias == "BULLISH" else "SELL"

        dol = view.dol_target
        dol_ok = dol is not None and ((direction == "BUY" and dol > price) or (direction == "SELL" and dol < price))
        if not self._gate("dol_valid", dol_ok, str(dol), "DOL inválido/sem alvo"):
            return None

        # ── Confluências (pontuam — scoring idêntico ao validado) ──
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

        atr = self._atr5(df5, 14)
        body = abs(float(df5.iloc[-1]["close"]) - float(df5.iloc[-1]["open"]))
        mss_clear = mss and atr > 0 and body >= atr * cfg.displacement_atr

        corr = getattr(self, "correlated_data", None)
        smt = self._smt_divergence(df5, self._convert_to_est(corr) if corr is not None else None, direction)

        fdir, _ = self._detect_active_fvg(df5, lookback=8)
        imbalance = fdir == ("bullish" if direction == "BUY" else "bearish")
        bpr_top, bpr_bot = self._detect_bpr_m1(m1, lookback=20) if m1 is not None else (None, None)
        bpr = bpr_top is not None

        prime = self._in_window(t, time(2, 0), time(5, 0)) or self._in_window(t, time(10, 0), time(11, 0))

        confluences = {
            "htf_aligned":      True,
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

        if not self._gate("quality_score", quality.score >= cfg.min_score,
                          quality.summary(), f"score {quality.score:.0f} < {cfg.min_score}"):
            return None

        # ── GATES PO3/MMM + SMT (o delta desta estratégia) ──
        # PO3: manipulação = sweep da range de acumulação (Ásia) = judas real
        asia_hi, asia_lo = self._asia_range(df5)
        if direction == "BUY":
            po3 = asia_lo is not None and float(df5.iloc[-w:]["low"].min()) < asia_lo
        else:
            po3 = asia_hi is not None and float(df5.iloc[-w:]["high"].max()) > asia_hi
        if cfg.require_po3 and not self._gate("po3_manip", po3, f"asia_hi={asia_hi} asia_lo={asia_lo}",
                                              "sem manipulação da range de acumulação (Ásia)"):
            return None
        if cfg.smt_gate and not self._gate("smt_gate", bool(smt), None, "SMT não confirma o reversal"):
            return None

        # ── Camada 3: confirmation entry 1m ──
        conf = self._confirm_1m(m1, direction)
        if not self._gate("confirm_1m", conf is not None, None, "sem confirmation entry no 1m"):
            return None
        ftop, fbot, anchor = conf

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

        # DISTRIBUIÇÃO: entrega pelo FVG até o DOL (intermediário ou DOL cheio)
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
        self._gate("signal_generated", True, direction, "PO3+SMT ok")
        reason = (f"ICT PO3 {direction} | bias={view.bias} | quality={quality.summary()} "
                  f"| manip Ásia+SMT | DOL={tp:.2f} RR={rr:.2f}")
        meta = {
            "direction": direction,
            "quality_score": quality.score,
            "quality_grade": quality.grade,
            "confluences": quality.breakdown,
            "equilibrium": eq,
            "range_high": rng_high, "range_low": rng_low,
            "swept_level": (rng_low if direction == "BUY" else rng_high),
            "asia_high": asia_hi, "asia_low": asia_lo,
            "swept_local": (sl if direction == "BUY" else sh),
            "mss_level":   (sh if direction == "BUY" else sl),
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
