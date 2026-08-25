"""
Researcher — o cérebro de pesquisa (LLM propõe a próxima hipótese)
==================================================================
Dado o histórico de experimentos (config → IS/OOS), o LLM propõe o PRÓXIMO
conjunto de parâmetros a testar, dentro do espaço de busca permitido, com
raciocínio. Aqui o LLM atua onde funciona: IDEAÇÃO/pesquisa — não como gatilho.

Anti-overfit: o LLM é instruído a perseguir robustez OOS, não PnL in-sample.
"""
import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
from research.lab import SEARCH_SPACE, clamp


import random


def _heuristic(history: list) -> dict:
    """Fallback grátis: perturba a melhor config dentro do espaço (random-walk dirigido)."""
    best = None
    for h in history:
        if h.get("oos_holds") and (best is None or h.get("oos_score", -9) > best.get("oos_score", -9)):
            best = h
    base = dict(best["overrides"]) if best else {}
    keys = random.sample(list(SEARCH_SPACE.keys()), k=random.choice([1, 2]))
    ov = dict(base)
    for k in keys:
        lo, hi = SEARCH_SPACE[k]
        cur = base.get(k, (lo + hi) / 2)
        step = (hi - lo) * random.uniform(-0.2, 0.2)
        ov[k] = cur + step
    return {"overrides": clamp(ov), "rationale": "heuristic random-walk (LLM indisponivel)"}


def _call_llm(prompt: str, model: str) -> str:
    """Tenta OpenAI; se falhar (cota/erro), cai para Ollama local (grátis)."""
    prov = getattr(cfg, "BRAIN_PROVIDER", "ollama").lower()
    # OpenAI primeiro só se provider=openai E há chave
    if prov == "openai" and getattr(cfg, "OPENAI_API_KEY", ""):
        try:
            from openai import OpenAI
            c = OpenAI(api_key=cfg.OPENAI_API_KEY)
            kw = dict(model=model, messages=[{"role": "user", "content": prompt}],
                      response_format={"type": "json_object"})
            if model.lower().startswith(("gpt-5", "o1", "o3", "o4")):
                kw["max_completion_tokens"] = 500
            else:
                kw["max_tokens"] = 300; kw["temperature"] = 0.5
            return c.chat.completions.create(**kw).choices[0].message.content
        except Exception as e:
            print(f"[researcher] OpenAI falhou ({str(e)[:60]}), caindo p/ Ollama local...")
    # Ollama local (grátis)
    import requests
    r = requests.post(f"{cfg.OLLAMA_HOST}/api/generate",
                      json={"model": getattr(cfg, "OLLAMA_MODEL", "qwen2.5:7b-instruct"),
                            "prompt": prompt, "stream": False, "format": "json",
                            "options": {"temperature": 0.5, "num_ctx": 8192}},
                      timeout=getattr(cfg, "OLLAMA_TIMEOUT", 900))
    r.raise_for_status()
    return r.json().get("response") or ""


def propose(history: list, model: str = None, market_ctx: str = "") -> dict:
    """Retorna {'overrides': {...}, 'rationale': str}. Robusto: OpenAI->Ollama->heurística.
    market_ctx: descrição das peculiaridades do mercado (NQ/ES/ouro) p/ o LLM adaptar."""
    model = model or getattr(cfg, "OPENAI_BRAIN_MODEL", "gpt-5.4-nano")
    space_txt = "\n".join(f"  - {k}: {lo}..{hi}" for k, (lo, hi) in SEARCH_SPACE.items())
    hist_txt = json.dumps(history[-8:], indent=1) if history else "none yet"
    mkt_block = f"\nMARKET CONTEXT (adapt the strategy to THIS market's personality):\n{market_ctx}\n" if market_ctx else ""

    prompt = f"""You are a quantitative trading researcher optimizing an ICT top-down strategy for ONE specific market.
Goal: find parameters that are ROBUST OUT-OF-SAMPLE — high profit factor with low drawdown that HOLDS on
unseen data. Chasing in-sample PnL that fails OOS is FAILURE. Prefer changes that generalize.
{mkt_block}
PARAMETERS you may set (stay within these ranges):
{space_txt}

Meaning (brief): min_score=quality threshold (higher=fewer/better trades); target_rr=target distance in R;
displacement_atr=how strong the breakout must be; pd_tolerance=premium/discount tolerance; partial_rr=where to
take partial; trail_trigger_rr/trail_distance_rr=runner management; break_even_trigger_rr=BE move;
min_momentum_atr=required directional move (close vs close[N])/ATR to enter — RAISE it to skip dead/choppy
markets (no-momentum filter), LOWER it (toward 0) to trade more; momentum_lookback=candles for that momentum.

EXPERIMENT HISTORY (config -> in-sample & out-of-sample metrics; oos_holds=survived blind test):
{hist_txt}

Propose the NEXT single experiment. Change only 1-3 parameters at a time (controlled search). Reason from the
history AND the market context: what improved OOS, what hurt it. Avoid repeating tried configs.

Respond ONLY JSON: {{"overrides": {{"param": value, ...}}, "rationale": "one sentence why"}}"""

    try:
        raw = _call_llm(prompt, model)
        data = json.loads(raw)
        ov = clamp(data.get("overrides", {}))
        if not ov:
            return _heuristic(history)
        return {"overrides": ov, "rationale": str(data.get("rationale", ""))[:200]}
    except Exception as e:
        print(f"[researcher] LLM indisponivel ({str(e)[:60]}) -> heurística")
        return _heuristic(history)
