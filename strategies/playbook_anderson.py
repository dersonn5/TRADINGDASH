"""
Playbook Anderson #1 — "ICT abrasileirado" (hipótese FIXA, pré-registrada)
===========================================================================
Codificação da leitura do usuário (5-6 anos B3), narrada em 2026-07-03 a partir
de trade real no mini-índice. NÃO é busca de parâmetros — é UMA hipótese testada
do jeito mais justo (engine honesto, IS/VAL/holdout).

Máquina de estados (exemplo vendedor; comprador é espelho):
 1. BIAS HTF: estrutura diária quebrou último fundo válido (velas FECHADAS) → bearish
 2. LIQUIDEZ ALVO: EQH multi-dia acima (topos iguais = liquidez institucional boa)
 3. EVENTO: sessão ANTERIOR varreu o EQH e falhou (fechou de volta abaixo)
 4. ABERTURA: dia atual abre ABAIXO da zona varrida → estado vendedor do dia
 5. SETUP: range intradiário → rompe pra baixo com displacement → deixa IFVG
    (FVG bullish da perna que foi INVERTIDO por fechamento)
 6. INDUÇÃO OBRIGATÓRIA: antes da entrada, o pullback precisa ter varrido um
    micro-topo (induzir comprador) — "nunca entrar sem indução, senão VOCÊ é a liquidez"
 7. ENTRADA: reteste do IFVG (troca de polaridade), stop além do IFVG,
    alvo = próxima liquidez (mínima recente) ou RR
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from strategies.base import Signal


@dataclass
class PlaybookAndersonConfig(ICTTopDownConfig):
    eqh_days: int = 10               # janela de dias p/ achar EQH/EQL multi-dia
    eqh_tol_pct: float = 0.004       # tolerância p/ topos/fundos "iguais" (v2: 0.15%→0.4%)
    # v2 (pré-registrado): liquidez-alvo obrigatória = PDH/PDL (leitura real do usuário nos
    # prints: "previous day high - eqh" — PDH é o nível, EQH multi-dia é BÔNUS de confluência,
    # não gate). require_eq=True volta ao comportamento v1 (raro demais: ~1 trade/ano).
    require_eq: bool = False
    range_bars_5m: int = 24          # 1ªs 2h do dia definem o range intradiário
    displacement_atr: float = 0.6    # corpo mínimo do rompimento vs ATR5m
    ifvg_lookback: int = 24          # janela p/ achar o FVG invertido na perna
    induction_lookback: int = 12     # micro-swing varrido no pullback (indução)
    sl_buffer_atr: float = 0.25
    target_rr: float = 3.0
    min_rr: float = 1.5
    cooldown_minutes: int = 120


class PlaybookAnderson(ICTTopDownCrypto):
    name = "playbook_anderson"

    def __init__(self, config: PlaybookAndersonConfig = None):
        super().__init__(config or PlaybookAndersonConfig())
        self._day_state = {}   # cache por dia: (date) -> dict(bias, zone, open_ok)
        # FUNIL de diagnóstico: conta em qual etapa cada DIA morre (1 contagem por dia/etapa)
        from collections import Counter
        self.funnel = Counter()
        self._funnel_seen = {}

    def _fn(self, stage, day):
        if self._funnel_seen.get(stage) != day:
            self._funnel_seen[stage] = day
            self.funnel[stage] += 1

    # ── camada DIÁRIA (velas fechadas — engine já corta honesto) ──
    def _daily_context(self, d1: pd.DataFrame):
        """bias por estrutura + EQH/EQL multi-dia + sweep na última sessão fechada.
        Retorna dict ou None."""
        cfg = self.config
        if d1 is None or len(d1) < cfg.eqh_days + 6:
            return None
        h, l, c = d1["high"].values, d1["low"].values, d1["close"].values
        n = len(d1)

        # v6: a DIREÇÃO NASCE DO EVENTO (narrativa do usuário: "o mercado captura a liquidez
        # e hoje abre abaixo da zona" — a falha da varredura É a mudança de caráter).
        # Fractais 2/2 EXCLUINDO ontem (ontem é quem varre):
        lows = [(i, l[i]) for i in range(n - 4, max(n - 25, 2), -1)
                if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]]
        highs = [(i, h[i]) for i in range(n - 4, max(n - 25, 2), -1)
                 if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]]
        # v7: MACRO bias (peça da narrativa que faltava no v6: "mudança de caráter no
        # semanal/diário") — fractais MAIORES (3/3, 60 dias): estrutura macro decide o lado.
        macro = None
        big_lo = [(i, l[i]) for i in range(n - 5, max(n - 60, 3), -1)
                  if all(l[i] < l[i+k] for k in (-3, -2, -1, 1, 2, 3) if 0 <= i+k < n)]
        big_hi = [(i, h[i]) for i in range(n - 5, max(n - 60, 3), -1)
                  if all(h[i] > h[i+k] for k in (-3, -2, -1, 1, 2, 3) if 0 <= i+k < n)]
        if big_lo and c[-1] < big_lo[0][1]:
            macro = "SELL"
        elif big_hi and c[-1] > big_hi[0][1]:
            macro = "BUY"
        if macro is None:
            return None

        bias = None; zone = None
        # sweep-falha SÓ na direção do macro (SELL: ontem varreu swing high e fechou abaixo)
        if macro == "SELL":
            for _, lv in highs[:3]:
                if h[-1] > lv and c[-1] < lv:
                    bias = "SELL"; zone = float(lv); break
        else:
            for _, lv in lows[:3]:
                if l[-1] < lv and c[-1] > lv:
                    bias = "BUY"; zone = float(lv); break
        if bias is None:
            return None
        return {"bias": bias, "zone": zone}

    def evaluate(self, candles_5m, candles_15m, candles_1h, candles_1d, candles_1m=None) -> Optional[Signal]:
        self._reset_gates()
        cfg = self.config
        if candles_5m is None or candles_5m.empty or candles_1d is None or candles_1d.empty:
            return None

        df5 = self._convert_to_est(candles_5m)
        d1 = self._convert_to_est(candles_1d)
        ct = df5.index[-1]
        day = ct.date()
        price = float(df5.iloc[-1]["close"])

        if self._last_signal_ts is not None:
            el = (ct - self._last_signal_ts).total_seconds() / 60.0
            if el < cfg.cooldown_minutes:
                return None

        # contexto diário: 1x por dia
        if day not in self._day_state:
            dc = self._daily_context(d1)
            today = df5[df5.index.date == day]
            open_ok = False
            if dc is not None and not today.empty:
                o = float(today.iloc[0]["open"])
                open_ok = (o < dc["zone"]) if dc["bias"] == "SELL" else (o > dc["zone"])
            self._day_state = {day: {"dc": dc, "open_ok": open_ok}}
        self._fn("00_dias", day)
        st = self._day_state[day]
        if st["dc"] is None:
            return None
        self._fn("01_ctx_diario", day)
        if not st["open_ok"]:
            return None
        self._fn("02_abertura_ok", day)
        direction = st["dc"]["bias"]

        # range intradiário (primeiras N velas do dia) + rompimento com displacement
        today = df5[df5.index.date == day]
        if len(today) < cfg.range_bars_5m + 3:
            return None
        rng = today.iloc[:cfg.range_bars_5m]
        rng_hi, rng_lo = float(rng["high"].max()), float(rng["low"].min())
        atr = self._atr5(df5, 14)
        if atr <= 0:
            return None
        after = today.iloc[cfg.range_bars_5m:]

        # procura rompimento na direção + IFVG deixado na perna
        broke_i = None
        for i in range(len(after)):
            row = after.iloc[i]
            body = abs(float(row["close"]) - float(row["open"]))
            if direction == "SELL" and float(row["close"]) < rng_lo and body >= atr * cfg.displacement_atr:
                broke_i = i; break
            if direction == "BUY" and float(row["close"]) > rng_hi and body >= atr * cfg.displacement_atr:
                broke_i = i; break
        if broke_i is None:
            return None
        self._fn("03_rompimento", day)

        # IFVG: FVG contrário na perna do rompimento que foi INVERTIDO por fechamento
        leg = today.iloc[max(0, cfg.range_bars_5m + broke_i - cfg.ifvg_lookback):cfg.range_bars_5m + broke_i + 1]
        ifvg = None
        want_orig = "bullish" if direction == "SELL" else "bearish"
        for k in range(len(leg) - 1, 1, -1):
            cndl, p2 = leg.iloc[k], leg.iloc[k - 2]
            if want_orig == "bullish" and cndl["low"] > p2["high"]:
                top, bot = float(cndl["low"]), float(p2["high"])
                if float(today.iloc[cfg.range_bars_5m + broke_i]["close"]) < bot:  # invertido
                    ifvg = (top, bot); break
            elif want_orig == "bearish" and cndl["high"] < p2["low"]:
                top, bot = float(p2["low"]), float(cndl["high"])
                if float(today.iloc[cfg.range_bars_5m + broke_i]["close"]) > top:
                    ifvg = (top, bot); break
        if ifvg is None:
            return None
        self._fn("04_ifvg", day)
        ftop, fbot = ifvg

        post = after.iloc[broke_i + 1:]
        if post.empty:
            return None

        # INDUÇÃO: pullback precisa varrer um micro-swing antes/no toque do IFVG
        induced = False
        pw = post.iloc[-cfg.induction_lookback:] if len(post) > cfg.induction_lookback else post
        hs, ls_ = pw["high"].values, pw["low"].values
        for j in range(1, len(pw) - 1):
            if direction == "SELL" and hs[j] > hs[j-1] and hs[j] > hs[j+1]:
                if float(pw["high"].iloc[-1]) > hs[j] or float(df5.iloc[-1]["high"]) > hs[j]:
                    induced = True; break
            if direction == "BUY" and ls_[j] < ls_[j-1] and ls_[j] < ls_[j+1]:
                if float(pw["low"].iloc[-1]) < ls_[j] or float(df5.iloc[-1]["low"]) < ls_[j]:
                    induced = True; break
        if not induced:
            return None
        self._fn("05_inducao", day)

        # GATILHO: preço tocando o IFVG agora (reteste da troca de polaridade)
        touching = (fbot <= float(df5.iloc[-1]["high"]) and float(df5.iloc[-1]["low"]) <= ftop)
        if not touching:
            return None
        self._fn("06_toque_ifvg", day)

        # alvo = PRÓXIMA liquidez EXTERNA (PDH/PDL de ontem), não a máx/mín já feita do
        # próprio dia (bug v2: alvo colava na entrada quando ela vinha após o extremo do dia)
        buf = atr * cfg.sl_buffer_atr
        d1h, d1l = float(d1.iloc[-1]["high"]), float(d1.iloc[-1]["low"])
        if direction == "SELL":
            entry = price
            sl = ftop + buf
            sl_dist = sl - entry
            ext_liq = d1l                      # PDL = liquidez externa abaixo
            tp = entry - sl_dist * cfg.target_rr
            if ext_liq < entry - sl_dist:      # se PDL dá alvo válido mais perto, respeita
                tp = max(tp, ext_liq - buf)
        else:
            entry = price
            sl = fbot - buf
            sl_dist = entry - sl
            ext_liq = d1h                      # PDH = liquidez externa acima
            tp = entry + sl_dist * cfg.target_rr
            if ext_liq > entry + sl_dist:
                tp = min(tp, ext_liq + buf)
        if sl_dist <= 0:
            return None
        rr = abs(tp - entry) / sl_dist
        if rr < cfg.min_rr:
            return None

        self._last_signal_ts = ct
        return Signal(symbol=getattr(self, "symbol", ""), action=direction,
                      entry_price=round(entry, 2), stop_loss=round(sl, 2), take_profit=round(tp, 2),
                      confidence_score=0.85,
                      reasoning=f"PlaybookAnderson {direction} | zona={st['dc']['zone']:.1f} | IFVG reteste + indução | RR={rr:.2f}",
                      meta={"zone": st["dc"]["zone"], "ifvg": {"top": ftop, "bottom": fbot}},
                      timestamp=ct.to_pydatetime() if hasattr(ct, "to_pydatetime") else ct)
