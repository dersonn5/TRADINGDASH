"""
Módulo Torneio da Copa BTG — Apuração de Fases e Estado do Mulligan.
=====================================================================
Calcula o placar da fase com descarte automático do pior dia, consumo do mulligan,
dias restantes e eficiência de contratos (R$/contrato).
"""
from typing import Dict, Any, List, Optional
from copa.db import get_conn


def fase_atual(data: str) -> Optional[Dict[str, Any]]:
    """Retorna a fase oficial que contém a data YYYY-MM-DD, ou None."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM fase WHERE data_inicio <= ? AND data_fim >= ? ORDER BY ordem ASC LIMIT 1",
        (data, data),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "data_inicio": row["data_inicio"],
            "data_fim": row["data_fim"],
            "dias": int(row["dias"]),
            "tem_descarte": bool(row["tem_descarte"]),
            "ordem": int(row["ordem"]),
        }
    return None


def placar_fase(fase_id: str) -> Dict[str, Any]:
    """
    Calcula o placar consolidado da fase especificada.
    Retorna o placar bruto, efetivo (com descarte), mulligan e eficiência de contratos.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fase WHERE id = ?", (fase_id,))
    fase_row = cursor.fetchone()

    if not fase_row:
        conn.close()
        return {"fase": None}

    fase_dict = {
        "id": fase_row["id"],
        "nome": fase_row["nome"],
        "data_inicio": fase_row["data_inicio"],
        "data_fim": fase_row["data_fim"],
        "dias": int(fase_row["dias"]),
        "tem_descarte": bool(fase_row["tem_descarte"]),
    }

    # Buscar todas as sessões dentro do período da fase
    cursor.execute(
        """
        SELECT s.data, s.fase_id
        FROM session_day s
        WHERE (s.fase_id = ? OR (s.data >= ? AND s.data <= ?))
        ORDER BY s.data ASC
        """,
        (fase_id, fase_dict["data_inicio"], fase_dict["data_fim"]),
    )
    sessoes = cursor.fetchall()
    datas_fase = [s["data"] for s in sessoes]

    dias_list: List[Dict[str, Any]] = []
    contratos_total = 0

    for dt in datas_fase:
        cursor.execute(
            "SELECT * FROM trade WHERE data = ? AND status = 'FECHADO'",
            (dt,),
        )
        trades = cursor.fetchall()
        pnl_dia = round(sum(float(t["pnl_real"] or 0.0) for t in trades), 2)
        contratos_dia = sum(int(t["contratos"] or 0) for t in trades)
        num_trades = len(trades)
        contratos_total += contratos_dia

        dias_list.append({
            "data": dt,
            "pnl": pnl_dia,
            "trades": num_trades,
            "contratos": contratos_dia,
            "descartado": False,
        })

    conn.close()

    dias_operados = len(dias_list)
    dias_restantes = max(0, fase_dict["dias"] - dias_operados)
    placar_bruto = round(sum(d["pnl"] for d in dias_list), 2)

    # Identificar o pior dia
    pior_dia_info: Optional[Dict[str, Any]] = None
    if dias_list:
        pior = min(dias_list, key=lambda d: d["pnl"])
        pior_dia_info = {"data": pior["data"], "pnl": pior["pnl"]}

    # Mulligan e Descarte
    tem_descarte = fase_dict["tem_descarte"]
    placar_efetivo = placar_bruto

    dias_negativos = [d for d in dias_list if d["pnl"] < 0]
    mulligan_disponivel = True
    consumido_por = None
    motivo_mulligan = "nenhum dia negativo ainda"

    if len(dias_negativos) == 1:
        mulligan_disponivel = False
        consumido_por = dias_negativos[0]["data"]
        motivo_mulligan = f"consumido pelo dia {consumido_por}"
    elif len(dias_negativos) > 1:
        mulligan_disponivel = False
        pior_negativo = min(dias_negativos, key=lambda d: d["pnl"])
        consumido_por = pior_negativo["data"]
        motivo_mulligan = "2+ dias negativos: os excedentes ja pesam no placar"

    if tem_descarte and dias_operados >= 2 and pior_dia_info is not None:
        # Marcar o pior dia como descartado
        for d in dias_list:
            if d["data"] == pior_dia_info["data"]:
                d["descartado"] = True
                break
        placar_efetivo = round(placar_bruto - pior_dia_info["pnl"], 2)

    reais_por_contrato = (
        round(placar_bruto / contratos_total, 2) if contratos_total > 0 else 0.0
    )

    return {
        "fase": fase_dict,
        "dias": dias_list,
        "dias_operados": dias_operados,
        "dias_restantes": dias_restantes,
        "placar_bruto": placar_bruto,
        "placar_efetivo": placar_efetivo,
        "pior_dia": pior_dia_info,
        "mulligan": {
            "disponivel": mulligan_disponivel,
            "consumido_por": consumido_por,
            "motivo": motivo_mulligan,
        },
        "contratos_total": contratos_total,
        "reais_por_contrato": reais_por_contrato,
    }
