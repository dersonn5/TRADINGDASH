"""
Motor de Risco e Circuit Breakers do Cockpit Copa BTG.
======================================================
Avalia as condições de gate para liberação ou bloqueio de novas operações.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from copa.db import get_conn, VALOR_PONTO


def calcular_pnl(
    mercado: str, direcao: str, entrada: float, saida: float, contratos: int
) -> Tuple[float, float]:
    """
    Calcula pontos e PnL em R$.
    Retorna (pontos, reais).
    """
    mercado_upper = str(mercado).upper()
    direcao_upper = str(direcao).upper()
    fator = VALOR_PONTO.get(mercado_upper, 0.20)

    if direcao_upper == "COMPRA":
        pontos = float(saida) - float(entrada)
    else:  # VENDA
        pontos = float(entrada) - float(saida)

    reais = round(pontos * int(contratos) * fator, 2)
    return (round(pontos, 2), reais)


def _load_copa_config() -> Dict[str, Any]:
    """Carrega as configurações salvas em copa_config."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT chave, valor FROM copa_config")
    rows = cursor.fetchall()
    conn.close()

    cfg: Dict[str, Any] = {}
    for r in rows:
        try:
            cfg[r["chave"]] = json.loads(r["valor"])
        except Exception:
            cfg[r["chave"]] = r["valor"]
    return cfg


def avaliar_gate(data: str, agora: Optional[str] = None) -> Dict[str, Any]:
    """
    Avalia o gate de risco para o dia 'data' (YYYY-MM-DD).
    Retorna dict com status de liberação, motivos de bloqueio, avisos e detalhes dos breakers.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # 1. Carregar sessão do dia
    cursor.execute("SELECT * FROM session_day WHERE data = ?", (data,))
    sessao_row = cursor.fetchone()

    # 2. Carregar configurações gerais
    config = _load_copa_config()

    horarios_validos = config.get(
        "horarios_validos", [{"inicio": "09:00", "fim": "12:00"}]
    )
    max_perdas_seguidas_cfg = int(config.get("max_perdas_seguidas", 2))
    cooldown_min_cfg = int(config.get("cooldown_min", 60))
    bloquear_apos_meta = bool(config.get("bloquear_apos_meta", False))
    fator_perda_pos_descarte = float(config.get("fator_perda_pos_descarte", 0.5))

    # 3. Carregar trades do dia
    cursor.execute("SELECT * FROM trade WHERE data = ? ORDER BY id ASC", (data,))
    trades = cursor.fetchall()
    conn.close()

    motivos: List[str] = []
    avisos: List[str] = []

    # Se não há pré-sessão preenchida
    if not sessao_row:
        motivos.append("pre-sessao do dia nao preenchida")
        return {
            "liberado": False,
            "motivos": motivos,
            "avisos": avisos,
            "breakers": {
                "pre_sessao_ok": False,
                "dentro_horario": True,
                "pnl_dia": 0.0,
                "limite_perda_dia": float(config.get("limite_perda_dia", 300.0)),
                "trades_dia": 0,
                "max_trades_dia": int(config.get("max_trades_dia", 3)),
                "perdas_seguidas": 0,
                "max_perdas_seguidas": max_perdas_seguidas_cfg,
                "cooldown_ate": None,
                "trade_aberto_id": None,
                "modo": "NORMAL",
                "bonus_score_defensivo": 0,
            },
        }

    sessao = dict(sessao_row)
    modo = str(sessao.get("modo", "NORMAL")).upper()
    meta_dia = float(sessao.get("meta_dia", 0.0))
    limite_perda_dia = float(sessao.get("limite_perda_dia", config.get("limite_perda_dia", 300.0)))
    max_trades_dia = int(sessao.get("max_trades_dia", config.get("max_trades_dia", 3)))

    # Verificação de Módulo Torneio (Mulligan consumido) se aplicável
    modo_forcado_por_mulligan = False
    mulligan_disponivel = True
    limite_perda_dia_efetivo = limite_perda_dia

    fase_id = sessao.get("fase_id")
    if fase_id:
        try:
            from copa.torneio import placar_fase
            placar = placar_fase(fase_id)
            mulligan_info = placar.get("mulligan", {})
            mulligan_disponivel = bool(mulligan_info.get("disponivel", True))
            dias_restantes = placar.get("dias_restantes", 0)

            if not mulligan_disponivel and dias_restantes > 0:
                modo = "DEFENSIVO"
                modo_forcado_por_mulligan = True
                limite_perda_dia_efetivo = round(limite_perda_dia * fator_perda_pos_descarte, 2)
        except Exception:
            pass

    # Em modo DEFENSIVO, max_trades_dia é forçado a 1 e bônus score = 15
    if modo == "DEFENSIVO":
        max_trades_dia = 1
        bonus_score_defensivo = 15
    else:
        bonus_score_defensivo = 0

    # Analisar trades existentes no dia
    trades_fechados = [t for t in trades if t["status"] == "FECHADO"]
    trades_abertos = [t for t in trades if t["status"] == "ABERTO"]

    pnl_dia = round(sum(float(t["pnl_real"] or 0.0) for t in trades_fechados), 2)
    trades_dia = len(trades)  # total de trades do dia (abertos + fechados)
    trade_aberto_id = trades_abertos[0]["id"] if trades_abertos else None

    # Calcular perdas seguidas (do mais recente para trás)
    perdas_seguidas = 0
    ultimo_fechado_perdedor_time = None

    for t in reversed(trades_fechados):
        pnl_t = float(t["pnl_real"] or 0.0)
        if pnl_t < 0:
            perdas_seguidas += 1
            if ultimo_fechado_perdedor_time is None:
                ultimo_fechado_perdedor_time = t["fechado_em"]
        else:
            break

    # Cooldown
    cooldown_ate = None
    if perdas_seguidas >= max_perdas_seguidas_cfg and ultimo_fechado_perdedor_time:
        try:
            # Formatos suportados: ISO ou HH:MM
            if "T" in ultimo_fechado_perdedor_time or "-" in ultimo_fechado_perdedor_time:
                dt_fechado = datetime.fromisoformat(ultimo_fechado_perdedor_time)
                dt_cooldown = dt_fechado + timedelta(minutes=cooldown_min_cfg)
                cooldown_ate = dt_cooldown.strftime("%H:%M")
            else:
                h, m = map(int, ultimo_fechado_perdedor_time.split(":")[:2])
                dt_fechado = datetime.now().replace(hour=h, minute=m, second=0)
                dt_cooldown = dt_fechado + timedelta(minutes=cooldown_min_cfg)
                cooldown_ate = dt_cooldown.strftime("%H:%M")
        except Exception:
            cooldown_ate = None

    # Horário atual (HH:MM)
    if agora is None:
        hora_atual_str = datetime.now().strftime("%H:%M")
    else:
        if "T" in agora:
            hora_atual_str = datetime.fromisoformat(agora).strftime("%H:%M")
        elif len(agora) >= 5 and ":" in agora:
            hora_atual_str = agora[:5]
        else:
            hora_atual_str = agora

    # Checar horário válido
    dentro_horario = False
    for janela in horarios_validos:
        ini = janela.get("inicio", "00:00")
        fim = janela.get("fim", "23:59")
        if ini <= hora_atual_str <= fim:
            dentro_horario = True
            break

    # REGRAS QUE BLOQUEIAM:
    # 1. Limite de perda atingido
    if pnl_dia <= -limite_perda_dia_efetivo and limite_perda_dia_efetivo > 0:
        motivos.append(
            f"limite de perda do dia atingido (R$ {abs(pnl_dia):.2f} de R$ {limite_perda_dia_efetivo:.2f})"
        )

    # 2. Limite de trades atingido
    if trades_dia >= max_trades_dia:
        motivos.append(f"limite de trades do dia atingido ({trades_dia}/{max_trades_dia})")

    # 3. Cooldown ativo
    if perdas_seguidas >= max_perdas_seguidas_cfg and cooldown_ate:
        if hora_atual_str < cooldown_ate:
            motivos.append(
                f"cooldown apos {perdas_seguidas} perdas seguidas ate {cooldown_ate}"
            )

    # 4. Fora do horário permitido
    if not dentro_horario:
        motivos.append("fora do horario permitido")

    # 5. Já existe trade aberto
    if trade_aberto_id is not None:
        motivos.append(f"ja existe trade aberto (#{trade_aberto_id})")

    # REGRAS QUE AVISAM (OU BLOQUEIAM):
    if meta_dia > 0 and pnl_dia >= meta_dia:
        if bloquear_apos_meta:
            motivos.append("meta do dia batida (bloqueio ativo)")
        else:
            avisos.append("meta do dia batida")

    liberado = len(motivos) == 0

    breakers_dict: Dict[str, Any] = {
        "pre_sessao_ok": True,
        "dentro_horario": dentro_horario,
        "pnl_dia": pnl_dia,
        "limite_perda_dia": limite_perda_dia,
        "limite_perda_dia_efetivo": limite_perda_dia_efetivo,
        "trades_dia": trades_dia,
        "max_trades_dia": max_trades_dia,
        "perdas_seguidas": perdas_seguidas,
        "max_perdas_seguidas": max_perdas_seguidas_cfg,
        "cooldown_ate": cooldown_ate,
        "trade_aberto_id": trade_aberto_id,
        "modo": modo,
        "bonus_score_defensivo": bonus_score_defensivo,
        "mulligan_disponivel": mulligan_disponivel,
        "modo_forcado_por_mulligan": modo_forcado_por_mulligan,
    }

    return {
        "liberado": liberado,
        "motivos": motivos,
        "avisos": avisos,
        "breakers": breakers_dict,
    }
