"""
ICT Brain — Taxonomia de Keywords
===================================
Define o vocabulário técnico do método ICT em três tiers:
  Tier 1 (score +10): conceitos centrais de trading puro
  Tier 2 (score +5):  termos de mercado genéricos
  Tier 0 (score -8):  ruído — conteúdo não-técnico

Também define as CATEGORIAS temáticas usadas na destilação.
"""

# Threshold minimo de score para o Cerebro Lucrativo
MIN_SCORE_PROFITABLE = 40

# ─── TIER 1 — Alta Relevância Técnica (+10 cada) ────────────────────────────

TIER1_KEYWORDS = [
    # Fair Value Gap / Imbalance
    "fair value gap", "fvg", "imbalance", "inefficiency", "single candle", "void",

    # Order Blocks
    "order block", "ob ", " ob,", "breaker block", "breaker", "mitigation block",
    "rejection block", "institutional order flow", "institutional candle",

    # Market Structure
    "market structure shift", "mss", "break of structure", "bos", "change of character",
    "choch", "displacement", "leg lower", "leg higher", "swing high", "swing low",
    "internal range liquidity", "external range liquidity", "irl", "erl",

    # Liquidez
    "liquidity", "buy side liquidity", "sell side liquidity", "bsl", "ssl",
    "liquidity sweep", "stop hunt", "stop run", "raid", "inducement",
    "relative equal highs", "relative equal lows", "reh", "rel",
    "turtle soup", "judas swing",

    # Killzones e Sessões
    "killzone", "london open", "new york open", "new york am", "new york pm",
    "london close", "asian range", "asian session", "macro", "silver bullet",

    # Modelos de Trade
    "power of three", "po3", "accumulation", "manipulation", "distribution",
    "redelivery", "retracement", "premium", "discount", "equilibrium",
    "optimal trade entry", "ote", "pd array",

    # Conceitos Avançados
    "consequent encroachment", "ce ", "mean threshold", "volume imbalance",
    "propulsion block", "reclaimed", "rebalance", "delivery",
    "time and price", "smart money", "institutional",
    "draw on liquidity", "weekly profile", "daily profile",
    "opening range", "gap and go", "first presented fvg",

    # Instrumentos preferidos do ICT
    "nq", "nasdaq", "es futures", "sp500", "dxy", "dollar index",
    "xauusd", "gold futures", "6e futures", "eurusd",
]

# ─── TIER 2 — Relevância Média (+5 cada) ────────────────────────────────────

TIER2_KEYWORDS = [
    "entry", "stop loss", "take profit", "target", "objective",
    "long", "short", "buy", "sell", "trade",
    "resistance", "support", "high", "low", "open", "close",
    "candle", "wick", "body", "rejection",
    "trend", "bullish", "bearish", "consolidation",
    "risk", "reward", "risk reward", "r:r", "rr",
    "timeframe", "daily", "4 hour", "1 hour", "15 minute", "5 minute",
    "weekly", "monthly", "quarterly",
    "price action", "chart", "setup", "pattern",
    "session", "open", "model", "narrative",
    "bias", "direction", "higher timeframe",
    "futures", "contract", "tick", "point",
    "backtest", "journal", "review",
]

# ─── TIER 0 — Ruído / Conteúdo Não-Técnico (-8 cada) ───────────────────────

NOISE_KEYWORDS = [
    # Agradecimentos e interação social
    "thank you for watching", "subscribe", "like this video", "comment below",
    "hit the bell", "notification", "share this video",
    "patreon", "link in the description", "check out my",

    # Conteúdo pessoal / emocional
    "god bless", "i'm grateful", "my family", "my kids", "my wife",
    "i started trading", "back in the day", "my story",
    "years ago i", "i remember when", "growing up",

    # Críticas / drama / haters
    "haters", "critics", "gurus", "vendor", "charlatan", "fraud",
    "lawsuit", "legal action", "court", "attorney",
    "social media drama", "twitter", "exposed",

    # Autopromoção e comunidade
    "telegram group", "discord server", "mentorship program",
    "course", "paid course", "free course", "certificate",
    "i've been saying for years", "nobody teaches this",
    "inner circle", "community members",

    # Filosofia / motivação pura (sem contexto técnico)
    "life lesson", "mindset", "believe in yourself", "never give up",
    "success", "millionaire", "rich", "wealth", "money",
    "prayer", "meditate", "spirit",
]

# ─── CATEGORIAS TEMÁTICAS para Destilação ───────────────────────────────────
# Cada categoria tem: nome, keywords gatilho, nome do arquivo Obsidian

CATEGORIES = {
    "fair_value_gap": {
        "nome":        "Fair Value Gap (FVG) and Imbalance",
        "arquivo":     "ICT_FVG_YouTube_Distilled.md",
        "keywords":    ["fair value gap", "fvg", "imbalance", "inefficiency",
                        "void", "single candle", "rebalance", "first presented"],
        "descricao":   "Concepts, formation conditions, usage, and invalidation of FVGs",
    },
    "order_block": {
        "nome":        "Order Blocks and Breaker Blocks",
        "arquivo":     "ICT_OrderBlocks_YouTube_Distilled.md",
        "keywords":    ["order block", "breaker block", "mitigation", "ob ",
                        "institutional candle", "propulsion", "rejection block"],
        "descricao":   "How to identify, use, and invalidate Order Blocks and Breakers",
    },
    "market_structure": {
        "nome":        "Market Structure (MSS / BOS / CHoCH)",
        "arquivo":     "ICT_MarketStructure_YouTube_Distilled.md",
        "keywords":    ["market structure shift", "mss", "break of structure",
                        "choch", "displacement", "swing high", "swing low",
                        "irl", "erl", "internal range", "external range"],
        "descricao":   "Market Structure Shift, Break of Structure, and change of character",
    },
    "liquidity": {
        "nome":        "Liquidity — Sweep and Inducement",
        "arquivo":     "ICT_Liquidity_YouTube_Distilled.md",
        "keywords":    ["liquidity", "buy side", "sell side", "sweep", "stop hunt",
                        "inducement", "relative equal", "turtle soup", "judas"],
        "descricao":   "Liquidity sweep patterns, inducements, and market traps",
    },
    "killzone_session": {
        "nome":        "Killzones and Trading Sessions",
        "arquivo":     "ICT_Killzones_YouTube_Distilled.md",
        "keywords":    ["killzone", "london open", "new york open", "london close",
                        "asian range", "silver bullet", "macro", "session", "am session"],
        "descricao":   "High-probability time windows and the profile of each session",
    },
    "power_of_three": {
        "nome":        "Power of Three (PO3) and Manipulation",
        "arquivo":     "ICT_PowerOfThree_YouTube_Distilled.md",
        "keywords":    ["power of three", "po3", "accumulation", "manipulation",
                        "distribution", "judas swing", "open price", "range"],
        "descricao":   "ICT's Accumulation, Manipulation, and Distribution model",
    },
    "ote_premium_discount": {
        "nome":        "OTE, Premium & Discount (Optimal Trade Entry)",
        "arquivo":     "ICT_OTE_YouTube_Distilled.md",
        "keywords":    ["optimal trade entry", "ote", "premium", "discount",
                        "equilibrium", "pd array", "fibonacci", "62", "79"],
        "descricao":   "Optimal Trade Entry and premium/discount zones for entry",
    },
    "modelos_trade": {
        "nome":        "Complete Trading Models (Silver Bullet, etc.)",
        "arquivo":     "ICT_ModelosTrade_YouTube_Distilled.md",
        "keywords":    ["silver bullet", "model", "setup", "narrative",
                        "draw on liquidity", "daily profile", "weekly profile",
                        "opening range", "time and price"],
        "descricao":   "Complete trading models with entry conditions and execution rules",
    },
    "gestao_risco": {
        "nome":        "Risk Management and Trading Psychology",
        "arquivo":     "ICT_GestaoRisco_YouTube_Distilled.md",
        "keywords":    ["stop loss", "risk reward", "risk management", "position size",
                        "drawdown", "loss", "equity", "discipline", "patience",
                        "journal", "backtest", "review your trades"],
        "descricao":   "Rules for risk management, position sizing, discipline, and trade reviews",
    },
}

# ─── Funções Utilitárias ─────────────────────────────────────────────────────

def score_chunk(text: str) -> int:
    """
    Retorna score de relevância técnica de trading para um chunk.
    Score > 0: conteúdo técnico
    Score <= 0: ruído / conteúdo não-técnico
    """
    text_lower = text.lower()
    score = 0

    for kw in TIER1_KEYWORDS:
        if kw in text_lower:
            score += 10

    for kw in TIER2_KEYWORDS:
        if kw in text_lower:
            score += 5

    for kw in NOISE_KEYWORDS:
        if kw in text_lower:
            score -= 8

    return score


def classify_categories(text: str) -> list[str]:
    """
    Retorna lista de categorias às quais o chunk pertence.
    Um chunk pode pertencer a múltiplas categorias.
    """
    text_lower = text.lower()
    matched = []
    for cat_id, cat in CATEGORIES.items():
        for kw in cat["keywords"]:
            if kw in text_lower:
                matched.append(cat_id)
                break
    return matched


def get_category_info(cat_id: str) -> dict:
    """Retorna metadados de uma categoria."""
    return CATEGORIES.get(cat_id, {})
