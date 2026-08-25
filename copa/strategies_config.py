"""
Carregador e validador de estratégias em formato de configuração JSON.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

STRATEGIES_DIR = Path(__file__).resolve().parent / "strategies"


def _validate_strategy(strategy: Dict[str, Any]) -> None:
    """Valida a estratégia garantindo que a soma dos pesos dos itens PONTO seja exatamente 100."""
    strat_id = strategy.get("id", "desconhecida")
    checklist = strategy.get("checklist", [])
    soma_pontos = sum(item.get("peso", 0) for item in checklist if item.get("tipo") == "PONTO")
    if soma_pontos != 100:
        raise ValueError(
            f"Estratégia '{strat_id}' inválida: soma dos pesos PONTO é {soma_pontos}, esperado 100."
        )


def load_all() -> List[Dict[str, Any]]:
    """Carrega todas as estratégias de copa/strategies/*.json sem cache, ordenadas pelo campo 'ordem'."""
    strategies: List[Dict[str, Any]] = []
    if not STRATEGIES_DIR.exists():
        return strategies

    for json_file in STRATEGIES_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                _validate_strategy(data)
                strategies.append(data)
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Erro ao ler estratégia de {json_file.name}: {e}") from e

    strategies.sort(key=lambda s: s.get("ordem", 999))
    return strategies


def load_one(strategy_id: str) -> Optional[Dict[str, Any]]:
    """Carrega uma estratégia específica pelo ID."""
    for strategy in load_all():
        if strategy.get("id") == strategy_id:
            return strategy
    return None
