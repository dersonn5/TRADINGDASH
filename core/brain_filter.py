"""
Brain Filter — Segundo Cérebro aplicado ao Backtest
====================================================
Pega cada sinal MECÂNICO gerado pelas estratégias ICT e o submete ao
"segundo cérebro" (regras destiladas do ICT no Obsidian + RAG) usando o
LLM LOCAL via Ollama. Decide APROVAR ou REJEITAR o trade.

Vantagem do local: sem rate-limit (429), sem custo → dá pra filtrar
milhares de trades num backtest longo, em loop, sem travar.

Anti-look-ahead: o filtro só recebe dados conhecidos NA ENTRADA
(ação, preço, SL, TP, R:R, horário, viés). NUNCA recebe o resultado (pnl).
"""

import json
import re
from datetime import datetime

import config
from core.rag import ObsidianRAG


class BrainFilter:
    """Filtra sinais mecânicos consultando o segundo cérebro via Ollama local."""

    def __init__(self, brain_char_cap: int = 2500, model: str = None):
        self.provider = getattr(config, "BRAIN_PROVIDER", "ollama").lower()
        if self.provider == "openai":
            self.model = model or getattr(config, "OPENAI_BRAIN_MODEL", "gpt-4o-mini")
        else:
            self.model = model or getattr(config, "OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.brain_char_cap = brain_char_cap
        self._brain_cache: dict = {}   # (symbol, strategy) -> texto do cérebro compilado 1x
        self._ok = None
        self._openai_client = None

    # ─── Disponibilidade ─────────────────────────────────────────────────
    def available(self) -> bool:
        if self._ok is not None:
            return self._ok
        if self.provider == "openai":
            key = getattr(config, "OPENAI_API_KEY", "")
            if not key:
                print("[BrainFilter] OPENAI_API_KEY ausente no .env")
                self._ok = False
            else:
                try:
                    from openai import OpenAI
                    self._openai_client = OpenAI(api_key=key)
                    self._ok = True
                    print(f"[BrainFilter] provider=openai model={self.model}")
                except Exception as e:
                    print(f"[BrainFilter] OpenAI indisponivel: {str(e)[:100]}")
                    self._ok = False
            return self._ok
        # Ollama
        try:
            import requests
            r = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
            self._ok = r.status_code == 200
        except Exception as e:
            print(f"[BrainFilter] Ollama indisponivel: {str(e)[:100]}")
            self._ok = False
        return self._ok

    def _call(self, prompt: str) -> str:
        if self.provider == "openai":
            kwargs = dict(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            # Modelos novos (gpt-5*, o*) usam max_completion_tokens e não aceitam temperature!=1
            m = self.model.lower()
            if m.startswith(("gpt-5", "o1", "o3", "o4")):
                kwargs["max_completion_tokens"] = 400
            else:
                kwargs["max_tokens"] = 200
                kwargs["temperature"] = 0.2
            resp = self._openai_client.chat.completions.create(**kwargs)
            return (resp.choices[0].message.content or "").strip()
        # Ollama
        import requests
        resp = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model":   self.model,
                "prompt":  prompt,
                "stream":  False,
                "format":  "json",
                "options": {"temperature": 0.2, "num_ctx": 8192},
            },
            timeout=getattr(config, "OLLAMA_TIMEOUT", 900),
        )
        resp.raise_for_status()
        return (resp.json().get("response") or "").strip()

    # ─── Cérebro (compilado 1x por setup) ────────────────────────────────
    def _brain_for(self, symbol: str, strategy: str) -> str:
        key = (symbol, strategy)
        if key not in self._brain_cache:
            seed = {"symbol": symbol, "ict_signal": strategy.replace("_", " ")}
            try:
                ctx = ObsidianRAG.compile_brain_context(seed)
            except Exception as e:
                print(f"[BrainFilter] Falha ao compilar cerebro: {str(e)[:120]}")
                ctx = "ICT brain unavailable."
            self._brain_cache[key] = ctx[: self.brain_char_cap]
        return self._brain_cache[key]

    # ─── Contexto discriminante (features de mercado na entrada) ─────────
    @staticmethod
    def _killzone_label(hour: int, minute: int) -> str:
        m = hour * 60 + minute
        if 2 * 60 <= m < 5 * 60:    return "London Open KZ (prime)"
        if 10 * 60 <= m < 11 * 60:  return "NY AM Silver Bullet (prime)"
        if 7 * 60 <= m < 10 * 60:   return "NY Open KZ"
        if 11 * 60 <= m < 12 * 60:  return "London Close KZ"
        if 14 * 60 <= m < 15 * 60:  return "NY PM Silver Bullet"
        return "outside primary killzones"

    def compute_context(self, pos, frames) -> dict:
        """frames = (c5, c15, c1h, c1d) em qualquer tz. Calcula features na entrada
        SEM look-ahead (corta até entry_time)."""
        import pandas as pd
        c5, c15, c1h, c1d = frames
        t = pos.entry_time
        action = pos.action
        ctx = {}

        def _cut(df):
            if df is None or df.empty:
                return df
            idx = df.index
            try:
                return df[idx <= t]
            except Exception:
                return df

        h1 = _cut(c1h)
        # HTF trend: close 1h vs EMA200
        if h1 is not None and len(h1) >= 50:
            closes = h1["close"]
            ema = closes.ewm(span=min(200, len(closes)), adjust=False).mean().iloc[-1]
            last = float(closes.iloc[-1])
            up = last > ema
            ctx["htf_trend"] = "UP" if up else "DOWN"
            ctx["htf_aligned"] = (action == "BUY" and up) or (action == "SELL" and not up)
        else:
            ctx["htf_trend"] = "n/a"; ctx["htf_aligned"] = None

        # Volatilidade: ATR(14) 5m vs mediana das últimas ~300 velas
        f5 = _cut(c5)
        if f5 is not None and len(f5) >= 50:
            hi, lo, cl = f5["high"], f5["low"], f5["close"].shift(1)
            tr = pd.concat([(hi - lo).abs(), (hi - cl).abs(), (lo - cl).abs()], axis=1).max(axis=1)
            atr = float(tr.iloc[-14:].mean())
            med = float(tr.iloc[-300:].median()) if len(tr) >= 50 else atr
            ctx["atr"] = atr
            ctx["vol_regime"] = "HIGH" if atr > med * 1.3 else ("LOW" if atr < med * 0.7 else "NORMAL")
            dist = abs(pos.take_profit - pos.entry_price)
            ctx["target_atr"] = round(dist / atr, 1) if atr > 0 else None
        else:
            ctx["vol_regime"] = "n/a"; ctx["target_atr"] = None

        hh = t.hour if hasattr(t, "hour") else int(str(t)[11:13])
        mm = t.minute if hasattr(t, "minute") else int(str(t)[14:16])
        ctx["killzone"] = self._killzone_label(hh, mm)
        ctx["weekday"] = t.strftime("%a") if hasattr(t, "strftime") else "?"

        # Qualidade da entrada emitida pela estratégia (score + confluências) — o sinal discriminante
        meta = getattr(pos, "meta", None) or {}
        ctx["quality_score"] = meta.get("quality_score")
        ctx["quality_grade"] = meta.get("quality_grade")
        conf = meta.get("confluences") or {}
        ctx["confluences_hit"] = [k for k, v in conf.items() if v]
        ctx["confluences_missing"] = [k for k, v in conf.items() if not v]
        return ctx

    def _scenario_narrative(self, pos, ctx, action, entry, sl, tp, rr) -> str:
        """Conta a SITUAÇÃO do trade como um trader veria — números que importam."""
        m = getattr(pos, "meta", None) or {}
        risk_pct = abs(entry - sl) / entry * 100 if entry else 0
        tgt_pct = abs(tp - entry) / entry * 100 if entry else 0
        rh, rl = m.get("range_high"), m.get("range_low")
        pos_in_range = None
        if rh and rl and rh > rl:
            pos_in_range = (entry - rl) / (rh - rl) * 100  # 0=low(discount) 100=high(premium)
        fvg = m.get("fvg_1m") or {}
        fvg_w = (abs(fvg.get("top", 0) - fvg.get("bottom", 0)) / entry * 100) if fvg else 0
        conf = m.get("confluences", {}) or {}
        dirn = "long" if action == "BUY" else "short"
        swept = m.get("swept_local")
        mssl = m.get("mss_level")
        lines = [
            f"- Asset {pos.symbol}, {dirn.upper()} setup ({m.get('bias','?')} HTF bias). Model: {ctx.get('quality_grade','?')}-grade, score {ctx.get('quality_score','?')}/100.",
            f"- Liquidity grab: price swept the local {'low' if action=='BUY' else 'high'} at {swept:.2f} (took {'sell-side' if action=='BUY' else 'buy-side'} liquidity)." if swept else "- Liquidity: no clear local sweep recorded.",
            f"- Structure: {'broke above' if action=='BUY' else 'broke below'} the swing at {mssl:.2f} (MSS). Displacement strong? {'YES' if conf.get('mss_clear') else 'NO/weak'}." if mssl else "- Structure: MSS level not recorded.",
            f"- Entry trigger: 1m FVG (fresh imbalance), width {fvg_w:.2f}% of price." if fvg else "- Entry: no 1m FVG recorded.",
            f"- SMT divergence (BTC/ETH): {'PRESENT (institutional confirmation)' if conf.get('smt_divergence') else 'ABSENT'}.",
            f"- Location: price is at {pos_in_range:.0f}% of the daily range ({'discount' if (pos_in_range or 50)<50 else 'premium'} side); inside HTF PD array: {'YES' if conf.get('in_htf_array') else 'NO'}." if pos_in_range is not None else "- Location: daily range position unknown.",
            f"- Session: {ctx.get('killzone','?')} | Volatility: {ctx.get('vol_regime','?')} | 1H trend: {ctx.get('htf_trend','?')} (trade is {'WITH' if ctx.get('htf_aligned') else 'AGAINST'} it).",
            f"- Trade math: risk {risk_pct:.2f}% to stop, target {tgt_pct:.2f}% away = R:R {rr:.1f}. Target is {ctx.get('target_atr','?')} ATR away (reachability).",
        ]
        return "\n".join(lines)

    # ─── Decisão por trade ───────────────────────────────────────────────
    def evaluate(self, pos, symbol: str, strategy: str, context: dict = None) -> dict:
        """Retorna {'approved': bool, 'confidence': int, 'reason': str}.
        context: features de mercado na entrada (compute_context)."""
        brain = self._brain_for(symbol, strategy)
        ctx = context or {}

        action = pos.action
        entry = pos.entry_price
        sl = pos.stop_loss
        tp = pos.take_profit
        rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0.0
        bias = "BULLISH" if action == "BUY" else "BEARISH"
        t = pos.entry_time
        hhmm = t.strftime("%H:%M") if isinstance(t, datetime) else str(t)[11:16]
        date = t.strftime("%Y-%m-%d") if isinstance(t, datetime) else str(t)[:10]
        aligned = ctx.get("htf_aligned")
        aligned_s = "ALIGNED with HTF trend" if aligned else ("AGAINST HTF trend" if aligned is False else "unknown")

        narrative = self._scenario_narrative(pos, ctx, action, entry, sl, tp, rr)

        prompt = f"""You are a professional ICT trader reading a chart to decide if THIS specific trade is worth taking.
You are shown the live situation in detail. Judge it like a trader: is this an A+ setup, or a trap/mediocre one?

ICT principles to apply (your trading knowledge):
{brain}

=== THE SITUATION RIGHT NOW (entry moment — outcome unknown) ===
{narrative}

HOW TO DECIDE (think like a discretionary trader):
- Rank this setup's odds. APPROVE the better-than-average ones; SKIP only those with a concrete weakness.
- Positives: clean liquidity grab, strong displacement, fresh FVG, correct discount/premium, SMT, realistic target.
- Negatives: weak/no displacement, target too far to reach, late entry, counter-trend without confirmation.
- Do NOT demand perfection — a solid B-grade setup with the move in its favor is tradeable. Approve ~half.
- confidence = your odds estimate (0-100). Approve when confidence >= 50.

Respond ONLY with JSON: {{"approved": true|false, "confidence": 0-100, "reason": "one short sentence citing the deciding factor"}}"""

        try:
            raw = self._call(prompt)
            data = json.loads(raw)
            return {
                "approved":   bool(data.get("approved", False)),
                "confidence": int(data.get("confidence", 0) or 0),
                "reason":     str(data.get("reason", ""))[:300],
            }
        except Exception as e:
            # Fallback de parse: tenta achar true/false
            txt = locals().get("raw", "") or ""
            approved = bool(re.search(r'"approved"\s*:\s*true', txt, re.I))
            return {"approved": approved, "confidence": 0,
                    "reason": f"parse-fallback ({str(e)[:60]})"}
