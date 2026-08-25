"""
EntryQualityScorer — Qualidade da Entrada (o edge do ICT)
==========================================================
Traduz o "feeling" de um trader ICT experiente em NÚMERO: o que separa um
trade A+ de um mediano não é UMA condição obrigatória, é a SOMA de confluências.

Cada confluência vale pontos. Soma → score 0-100. Opera só ≥ threshold = sniper.
O breakdown (quais confluências bateram) também alimenta o segundo cérebro e
aparece no gráfico, pra criar feeling de alongar/encurtar alvo.

Confluências (pesos somam 100):
  htf_aligned        15  — direção alinhada ao bias HTF (institucional)
  premium_discount   15  — preço no lado certo (discount p/ compra)
  in_htf_array       15  — entrada dentro de um PD array HTF (FVG/OB de 1h/4h/D)
  liquidity_quality  15  — varreu liquidez de QUALIDADE (EQH/EQL, PDH/PDL, 24h)
  killzone_prime     10  — horário nobre (London/NY open, Silver Bullet)
  mss_clear          10  — quebra de estrutura com displacement forte (corpo vs ATR)
  smt_divergence     10  — divergência SMT BTC/ETH no sweep
  imbalance_fvg       5  — deixou desbalanceamento (FVG) na perna
  bpr                 5  — deixou Balanced Price Range
"""
from dataclasses import dataclass, field
from typing import Dict


WEIGHTS = {
    "htf_aligned":      15,
    "premium_discount": 15,
    "in_htf_array":     15,
    "liquidity_quality":15,
    "killzone_prime":   10,
    "mss_clear":        10,
    "smt_divergence":   10,
    "imbalance_fvg":     5,
    "bpr":               5,
}


@dataclass
class QualityResult:
    score: float
    grade: str
    breakdown: Dict[str, bool] = field(default_factory=dict)

    def summary(self) -> str:
        hit = [k for k, v in self.breakdown.items() if v]
        return f"{self.grade} ({self.score:.0f}) [{','.join(hit)}]"


def grade_for(score: float) -> str:
    if score >= 80:
        return "A+"
    if score >= 65:
        return "A"
    if score >= 50:
        return "B"
    if score >= 35:
        return "C"
    return "D"


def score_entry(confluences: Dict[str, bool]) -> QualityResult:
    """confluences: dict {nome: bool}. Retorna QualityResult com score 0-100."""
    total = sum(WEIGHTS[k] for k, v in confluences.items() if v and k in WEIGHTS)
    return QualityResult(score=float(total), grade=grade_for(total),
                         breakdown={k: bool(confluences.get(k, False)) for k in WEIGHTS})
