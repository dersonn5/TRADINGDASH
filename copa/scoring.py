"""
Motor de Scoring e Avaliação de Ambiente da Sessão.
"""
import json
from typing import Dict, Any, List
from core.entry_quality import grade_for


def score_checklist(strategy: Dict[str, Any], marcado: Dict[str, bool]) -> Dict[str, Any]:
    """
    Calcula o score a partir dos itens PONTO marcados e verifica se faltam itens KILL.
    Retorna: {
        "score": float,
        "grade": str,
        "kills_faltando": list[str],
        "pontos_marcados": list[str]
    }
    """
    checklist = strategy.get("checklist", [])
    kills_faltando: List[str] = []
    pontos_marcados: List[str] = []
    score_total = 0.0

    for item in checklist:
        item_id = item.get("id")
        tipo = item.get("tipo")
        peso = item.get("peso", 0)
        is_marcado = bool(marcado.get(item_id, False))

        if tipo == "KILL":
            if not is_marcado:
                kills_faltando.append(item_id)
        elif tipo == "PONTO":
            if is_marcado:
                score_total += float(peso)
                pontos_marcados.append(item_id)

    grade = grade_for(score_total)

    return {
        "score": score_total,
        "grade": grade,
        "kills_faltando": kills_faltando,
        "pontos_marcados": pontos_marcados,
    }


def _extrair_campos_sessao(sessao: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza e calcula campos derivados da sessão (como agenda e níveis)."""
    dados = dict(sessao)

    agenda = dados.get("agenda", [])
    if isinstance(agenda, str):
        try:
            agenda = json.loads(agenda)
        except Exception:
            agenda = []

    niveis = dados.get("niveis", [])
    if isinstance(niveis, str):
        try:
            niveis = json.loads(niveis)
        except Exception:
            niveis = []

    tem_noticia_alta = any(
        isinstance(ev, dict) and str(ev.get("impacto", "")).upper() == "ALTO"
        for ev in agenda
    )
    niveis_marcados = len(niveis) if isinstance(niveis, list) else 0

    dados["tem_noticia_alta"] = tem_noticia_alta
    dados["niveis_marcados"] = niveis_marcados
    dados["agenda_parsed"] = agenda
    dados["niveis_parsed"] = niveis

    return dados


def _eval_op(val_atual: Any, op: str, val_alvo: Any) -> bool:
    """Avalia o operador lógico entre o valor atual e o valor alvo."""
    if op in ("=", "=="):
        return val_atual == val_alvo
    elif op == "!=":
        return val_atual != val_alvo
    elif op == ">=":
        return val_atual >= val_alvo
    elif op == "<=":
        return val_atual <= val_alvo
    elif op == ">":
        return val_atual > val_alvo
    elif op == "<":
        return val_atual < val_alvo
    return False


def sugerir_modo(sessao: Dict[str, Any]) -> str:
    """
    Sugere modo DEFENSIVO se:
      tilt >= 3 ou sono <= 2 ou pressao >= 4 ou tem_noticia_alta.
    Senão NORMAL.
    """
    dados = _extrair_campos_sessao(sessao)
    tilt = int(dados.get("tilt", 0))
    sono = int(dados.get("sono", 3))
    pressao = int(dados.get("pressao", 0))
    tem_noticia_alta = bool(dados.get("tem_noticia_alta", False))

    if tilt >= 3 or sono <= 2 or pressao >= 4 or tem_noticia_alta:
        return "DEFENSIVO"
    return "NORMAL"


def avaliar_ambiente(strategy: Dict[str, Any], sessao: Dict[str, Any]) -> Dict[str, Any]:
    """
    Avalia o ambiente do dia contra as regras da estratégia.
    Retorna: {
        "ambiente": "FAVORAVEL" | "NEUTRA" | "DESFAVORAVEL",
        "motivos": list[str]
    }
    """
    dados = _extrair_campos_sessao(sessao)
    regras = strategy.get("regras_ambiente", [])

    efeitos_casados: List[str] = []
    motivos: List[str] = []

    for regra in regras:
        campo = regra.get("campo")
        op = regra.get("op", "=")
        valor_alvo = regra.get("valor")
        efeito = regra.get("efeito", "NEUTRA")
        motivo = regra.get("motivo", "")

        if campo in dados:
            val_atual = dados[campo]
            # Normalizar tipos para comparação se necessário
            if isinstance(val_atual, (int, float)) and isinstance(valor_alvo, (int, float)):
                val_atual = float(val_atual)
                valor_alvo = float(valor_alvo)
            elif isinstance(val_atual, str) and isinstance(valor_alvo, str):
                val_atual = val_atual.upper()
                valor_alvo = valor_alvo.upper()

            if _eval_op(val_atual, op, valor_alvo):
                efeitos_casados.append(efeito)
                if motivo:
                    motivos.append(motivo)

    if "DESFAVORAVEL" in efeitos_casados:
        resultado = "DESFAVORAVEL"
    elif "FAVORAVEL" in efeitos_casados:
        resultado = "FAVORAVEL"
    else:
        resultado = "NEUTRA"

    return {
        "ambiente": resultado,
        "motivos": motivos,
    }
