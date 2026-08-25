"""
ICT PO3 v2 — "Judas open-anchored" (100% leak-free por construção)
===================================================================
Redesenho após a descoberta do look-ahead: NADA de bias por vela HTF em formação.
Todas as referências são conhecidas em TEMPO REAL no momento da decisão:

  - Midnight open (00:00 NY de HOJE)      → lado premium/discount do dia (PO3 real)
  - PDH/PDL (máx/mín de ONTEM, dia fechado)→ liquidez externa
  - Range da Ásia (sessão fechada 20-24 ET)→ acumulação
  - SMT vs mercado correlacionado          → confirmação do reversal (opcional)

Modelo (Power of Three / Judas Swing):
  ACUMULAÇÃO  = range da Ásia perto do open.
  MANIPULAÇÃO = expansão FALSA: preço varre PDH/asia-high ACIMA do midnight open
                (ou PDL/asia-low ABAIXO), e FALHA (fecha de volta).
  DISTRIBUIÇÃO= MSS 5m com displacement na direção oposta → entrada FVG 1m →
                alvo na liquidez oposta (PDL p/ SELL, PDH p/ BUY) ou RR fixo.

Direção nasce do EVENTO (sweep+reclaim+MSS), não de tendência de vela atrasada.
"""
from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional
import pandas as pd

from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.base import Signal


@dataclass
class ICTPo3V2Config(ICTTopDownConfig):
    judas_ref: str = "both"        # nível varrido: "asia" | "pd" (PDH/PDL) | "both" (qualquer)
    require_open_side: bool = True # SELL só acima do midnight open; BUY só abaixo (premium/discount do dia)
    smt_gate: bool = True          # SMT confirma o reversal (desliga p/ mercados sem par)
    reclaim_buffer_atr: float = 0.1  # preço deve fechar de volta além do nível por essa fração do ATR
    target_mode: str = "liquidity"   # "liquidity" = PDL/PDH oposto | "rr" = target_rr fixo
    asia_start_hour: int = 20
    asia_end_hour: int = 24
    # DISTRIBUIÇÃO/confirmação: "mss" = quebra de swing (mais tarde, mais confirmado) |
    # "cisd" = corpo fecha além do corpo da vela oposta anterior (mais cedo, menos confirmado) |
    # "either" = qualquer um dos dois já confirma
    confirm_type: str = "mss"
    # ENTRADA (backlog #13/#11):
    # entry_precision: "edge" = mercado no sinal (atual) | "ce" = ordem LIMITE no 50% do FVG 1m
    #   (Consequent Encroachment — entra mais fundo, stop relativo menor, payoff maior)
    entry_precision: str = "edge"
    # entry_fvg: "first" = 1º FVG 1m na direção (atual) | "next" = pula o 1º, usa o 2º
    #   (Turtle Soup: não entrar no 1º desbalanço — o 1º tende a ser induzido)
    entry_fvg: str = "first"
    # GESTÃO (backlog #17): "rr" = BE/parcial por múltiplo de R (engine padrão) |
    # "stdev" = BE quando preço percorre 2x a perna de manipulação, parcial em 3x
    #   (projeção de desvio-padrão do judas — gatilho por estrutura, não por R arbitrário)
    mgmt_mode: str = "rr"
    # Novas Melhorias:
    require_two_phases: bool = True     # Duas fases de acumulação/manipulação
    index_930_mode: bool = True         # Janela 9h30 NY específica para índices
    ob_largo_mode: bool = True          # Order block largo (range de consolidação)
    ob_largo_lookback: int = 24         # Lookback para detecção do OB Largo



class ICTPo3V2(ICTTopDownCrypto):
    name = "ict_po3_v2"

    def __init__(self, config: ICTPo3V2Config = None):
        super().__init__(config or ICTPo3V2Config())

    def get_operational_hours(self):
        cfg = self.config
        is_index = any(x in self.symbol.upper() for x in ["NAS", "NQ", "SPX", "ES", "YM", "US30", "GER30"])
        if is_index and getattr(cfg, "index_930_mode", True):
            return time(9, 30), time(11, 30)
        return getattr(cfg, "killzone_start", time(2, 0)), getattr(cfg, "killzone_end", time(16, 0))

    # ── referências em tempo real (sem look-ahead por construção) ──
    def _asia_range(self, df5):
        try:
            cfg = self.config
            recent = df5.iloc[-288:]
            hrs = recent.index.hour
            sub = recent[(hrs >= cfg.asia_start_hour) & (hrs < cfg.asia_end_hour)]
            if len(sub) < 3:
                return None, None
            return float(sub["high"].max()), float(sub["low"].min())
        except Exception:
            return None, None

    def _midnight_open(self, df5, ct):
        """Open de 00:00 NY de HOJE — primeiro candle do dia corrente."""
        try:
            today = df5[df5.index.date == ct.date()]
            if today.empty:
                return None
            return float(today.iloc[0]["open"])
        except Exception:
            return None

    def _get_consolidation_range(self, df5):
        """Identifica o range de consolidação recente (Order Block Largo)."""
        try:
            recent = df5.iloc[-40:-4]
            highs = recent["high"].values
            lows = recent["low"].values
            n = len(highs)
            if n < 12:
                return None, None
            best_hi, best_lo = None, None
            min_spread = float('inf')
            for width in [12, 18, 24]:
                if n < width:
                    continue
                for i in range(n - width + 1):
                    hi = float(highs[i : i + width].max())
                    lo = float(lows[i : i + width].min())
                    spread = hi - lo
                    if spread < min_spread:
                        min_spread = spread
                        best_hi = hi
                        best_lo = lo
            return best_hi, best_lo
        except Exception:
            return None, None

    def _check_two_phases(self, win_df, level, direction, min_gap=3) -> bool:
        """Verifica se houve duas varreduras distintas (duas fases de acumulação/manipulação)."""
        try:
            if direction == "SELL":
                cross_indices = [i for i, val in enumerate(win_df["high"]) if val > level]
            else:
                cross_indices = [i for i, val in enumerate(win_df["low"]) if val < level]
            if len(cross_indices) < 2:
                return False
            for idx in range(len(cross_indices) - 1):
                gap = cross_indices[idx + 1] - cross_indices[idx]
                if gap >= min_gap:
                    gap_slice = win_df.iloc[cross_indices[idx] + 1 : cross_indices[idx + 1]]
                    if direction == "SELL":
                        if (gap_slice["high"] <= level).all():
                            return True
                    else:
                        if (gap_slice["low"] >= level).all():
                            return True
            return False
        except Exception:
            return False

    def _prev_day_levels(self, d1):
        """PDH/PDL do ÚLTIMO dia FECHADO (engine já corta por vela fechada)."""
        try:
            if d1 is None or d1.empty:
                return None, None
            return float(d1.iloc[-1]["high"]), float(d1.iloc[-1]["low"])
        except Exception:
            return None, None

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        self._reset_gates()
        cfg = self.config

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty), None, "dados vazios"):
            return None
        if not self._gate("has_1m", candles_1m is not None and not candles_1m.empty, None, "sem 1m"):
            return None

        df5 = self._convert_to_est(candles_5m)
        d1 = self._convert_to_est(candles_1d)
        m1 = self._convert_to_est(candles_1m)
        ct = df5.index[-1]
        t = ct.time()
        price = float(df5.iloc[-1]["close"])

        # Check index 9:30 NY Killzone override
        is_index = any(x in self.symbol.upper() for x in ["NAS", "NQ", "SPX", "ES", "YM", "US30", "GER30"])
        if is_index and cfg.index_930_mode:
            kz_start = time(9, 30)
            kz_end = time(11, 30)
        else:
            kz_start = cfg.killzone_start
            kz_end = cfg.killzone_end

        if cfg.require_killzone and not self._gate(
                "killzone", self._in_window(t, kz_start, kz_end),
                t.strftime("%H:%M"), f"fora da killzone index={is_index}"):
            return None
        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown", el >= cfg.cooldown_minutes, f"{el:.0f}min", "cooldown"):
                return None

        # ── Referências do dia (todas conhecidas em tempo real) ──
        mo = self._midnight_open(df5, ct)
        pdh, pdl = self._prev_day_levels(d1)
        asia_hi, asia_lo = self._asia_range(df5)

        ob_hi, ob_lo = None, None
        if cfg.ob_largo_mode:
            ob_hi, ob_lo = self._get_consolidation_range(df5)

        if not self._gate("refs", mo is not None and pdh is not None, f"mo={mo} pdh={pdh}", "sem referências"):
            return None

        atr = self._atr5(df5, 14)
        if not self._gate("atr", atr > 0, None, "ATR zero"):
            return None
        buf = atr * cfg.reclaim_buffer_atr
        w = cfg.sweep_window_5m
        win = df5.iloc[-w:]
        hi_w, lo_w = float(win["high"].max()), float(win["low"].min())

        # níveis de referência p/ o judas
        up_levels, dn_levels = [], []
        if cfg.judas_ref in ("asia", "both") and asia_hi is not None:
            up_levels.append(asia_hi); dn_levels.append(asia_lo)
        if cfg.judas_ref in ("pd", "both"):
            up_levels.append(pdh); dn_levels.append(pdl)
        if cfg.ob_largo_mode and ob_hi is not None:
            up_levels.append(ob_hi); dn_levels.append(ob_lo)

        # MANIPULAÇÃO: varreu nível de cima e voltou (SELL) / de baixo e voltou (BUY)
        if cfg.require_two_phases:
            sell_sweep = any(hi_w > lv and price < lv - buf and self._check_two_phases(win, lv, "SELL") for lv in up_levels)
            buy_sweep = any(lo_w < lv and price > lv + buf and self._check_two_phases(win, lv, "BUY") for lv in dn_levels)
        else:
            sell_sweep = any(hi_w > lv and price < lv - buf for lv in up_levels)
            buy_sweep = any(lo_w < lv and price > lv + buf for lv in dn_levels)

        # lado do dia vs midnight open (PO3: judas ACIMA do open → dia de venda)
        if cfg.require_open_side:
            sell_sweep = sell_sweep and price >= mo * 0.999
            buy_sweep = buy_sweep and price <= mo * 1.001

        if not self._gate("judas", sell_sweep or buy_sweep,
                          f"hi_w={hi_w:.1f} lo_w={lo_w:.1f} mo={mo:.1f}", "sem manipulação"):
            return None
        direction = "SELL" if sell_sweep else "BUY"

        # DISTRIBUIÇÃO: confirmação da mudança de entrega de preço (CISD)
        # MSS = quebra de swing 5m (estrutural, mais tarde/confirmado)
        sh, sl = self._detect_mss_and_swing(df5, lookback=cfg.swing_lookback_5m)
        mw = cfg.mss_window_5m
        recent_closes = df5.iloc[-mw:]["close"]
        if direction == "BUY":
            mss = sh is not None and float(recent_closes.max()) > sh
        else:
            mss = sl is not None and float(recent_closes.min()) < sl
        last = df5.iloc[-1]
        body = abs(float(last["close"]) - float(last["open"]))
        mss_clear = mss and body >= atr * cfg.displacement_atr

        # CISD = corpo da vela atual fecha além do CORPO da última vela de cor oposta
        # (ignora pavio; não exige quebra de swing — gatilho mais cedo que MSS)
        prev = df5.iloc[-2]
        prev_bearish = prev["close"] < prev["open"]
        prev_bullish = prev["close"] > prev["open"]
        prev_body_top = max(prev["open"], prev["close"])
        prev_body_bot = min(prev["open"], prev["close"])
        if direction == "BUY":
            cisd = prev_bearish and float(last["close"]) > prev_body_top
        else:
            cisd = prev_bullish and float(last["close"]) < prev_body_bot
        cisd_clear = cisd and body >= atr * cfg.displacement_atr

        if cfg.confirm_type == "cisd":
            ok, why = cisd_clear, "sem CISD (corpo não fechou além da vela oposta)"
        elif cfg.confirm_type == "either":
            ok, why = (mss_clear or cisd_clear), "sem MSS nem CISD"
        else:
            ok, why = mss_clear, "sem MSS com displacement"
        if not self._gate("confirm", ok, f"mss={mss_clear} cisd={cisd_clear} body={body:.2f}", why):
            return None

        # SMT (opcional, gate)
        if cfg.smt_gate:
            corr = getattr(self, "correlated_data", None)
            smt = self._smt_divergence(df5, self._convert_to_est(corr) if corr is not None else None, direction)
            if not self._gate("smt", bool(smt), None, "SMT não confirma"):
                return None

        # ── entrada 1m (FVG) ──
        # entry_fvg="next": pula o 1º FVG (tende a ser o induzido — Turtle Soup) e usa o 2º
        if cfg.entry_fvg == "next":
            want = "bullish" if direction == "BUY" else "bearish"
            matches = [(fd, z, idx) for fd, z, idx in
                       self._detect_fvg_list(m1, lookback=cfg.confirm_lookback_1m) if fd == want]
            if len(matches) >= 2:
                fd, (ftop, fbot), idx = matches[1]
                if direction == "BUY":
                    anchor = float(m1.iloc[max(0, idx - 3):idx + 1]["low"].min())
                else:
                    anchor = float(m1.iloc[max(0, idx - 3):idx + 1]["high"].max())
                conf = (ftop, fbot, anchor)
            else:
                conf = None
        else:
            conf = self._confirm_1m(m1, direction)
        if not self._gate("confirm_1m", conf is not None, None, "sem confirmation 1m"):
            return None
        ftop, fbot, anchor = conf

        # entry_precision="ce": ordem LIMITE no 50% do FVG (Consequent Encroachment)
        # — entra mais fundo, stop relativo menor, payoff maior (backlog #13)
        if cfg.entry_precision == "ce":
            entry_px = (ftop + fbot) / 2.0
        else:
            entry_px = price

        if direction == "BUY":
            sl_price = anchor * (1.0 - cfg.sl_buffer_percent)
            sl_dist = entry_px - sl_price
        else:
            sl_price = anchor * (1.0 + cfg.sl_buffer_percent)
            sl_dist = sl_price - entry_px
        if sl_dist <= 0:
            self._gate("entry_px", False, f"entry={entry_px:.2f} sl={sl_price:.2f}", "CE além do stop")
            return None
        floor_sl = price * cfg.min_sl_distance_percent
        ceil_sl = price * cfg.max_sl_distance_percent
        if sl_dist < floor_sl:
            sl_dist = floor_sl
            sl_price = entry_px - floor_sl if direction == "BUY" else entry_px + floor_sl
        if not self._gate("sl_band", sl_dist <= ceil_sl, f"{sl_dist:.2f}>{ceil_sl:.2f}", "stop largo"):
            return None

        # alvo: liquidez oposta (PDL/PDH) ou RR fixo — sem ultrapassar a liquidez
        if direction == "BUY":
            liq = pdh
            tp = min(entry_px + sl_dist * cfg.target_rr, liq) if cfg.target_mode == "rr" else liq
        else:
            liq = pdl
            tp = max(entry_px - sl_dist * cfg.target_rr, liq) if cfg.target_mode == "rr" else liq
        rr = abs(tp - entry_px) / sl_dist if sl_dist > 0 else 0.0
        if not self._gate("min_rr", rr >= cfg.min_rr, f"RR={rr:.2f}", f"RR<{cfg.min_rr}"):
            return None

        self._last_signal_ts = ct
        self._gate("signal_generated", True, direction, "po3 v2 judas ok")
        meta = {
            "direction": direction, "midnight_open": mo,
            "pdh": pdh, "pdl": pdl, "asia_high": asia_hi, "asia_low": asia_lo,
            "swept_level": (max(up_levels) if direction == "SELL" else min(dn_levels)),
            "mss_level": (sh if direction == "BUY" else sl),
            "fvg_1m": {"top": ftop, "bottom": fbot}, "dol": tp,
        }
        # GESTÃO stdev (backlog #17): BE quando percorre 2x a perna de manipulação,
        # parcial em 3x — projeção da perna do judas (origem=midnight open, extremo=sweep).
        # Convertido p/ R e passado como override por-trade (engine lê do meta).
        if cfg.mgmt_mode == "stdev":
            extreme = hi_w if direction == "SELL" else lo_w
            leg = abs(extreme - mo)
            if leg > 0 and sl_dist > 0:
                if direction == "SELL":
                    be_px = extreme - 2 * leg
                    pt_px = extreme - 3 * leg
                    be_rr = (entry_px - be_px) / sl_dist
                    pt_rr = (entry_px - pt_px) / sl_dist
                else:
                    be_px = extreme + 2 * leg
                    pt_px = extreme + 3 * leg
                    be_rr = (be_px - entry_px) / sl_dist
                    pt_rr = (pt_px - entry_px) / sl_dist
                meta["be_trigger_rr_override"] = max(0.5, round(be_rr, 2))
                meta["partial_rr_override"] = max(0.8, round(pt_rr, 2))
        return Signal(symbol=self.symbol, action=direction,
                      entry_price=round(entry_px, 2), stop_loss=round(sl_price, 2), take_profit=round(tp, 2),
                      confidence_score=0.9,
                      reasoning=f"PO3v2 {direction} judas | mo={mo:.1f} | RR={rr:.2f} | {cfg.entry_precision}",
                      meta=meta,
                      timestamp=ct.to_pydatetime() if hasattr(ct, "to_pydatetime") else ct)
