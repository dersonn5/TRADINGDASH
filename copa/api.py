"""
Router FastAPI da Copa BTG.
===========================
Implementa todos os endpoints da API da Copa com validações rigorosas no servidor.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import FileResponse

from copa.db import get_conn, DB_PATH
from copa.strategies_config import load_all, load_one
from copa.scoring import score_checklist, avaliar_ambiente
from copa.risk import avaliar_gate, calcular_pnl
from copa import stats
from copa.torneio import fase_atual, placar_fase

router = APIRouter(prefix="/api/copa", tags=["copa"])


@router.get("/config")
def get_config() -> Dict[str, Any]:
    """Retorna as configurações da Copa com valores já desserializados."""
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


@router.put("/config")
def update_config(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Atualiza configurações parcialmente e retorna o estado completo."""
    conn = get_conn()
    cursor = conn.cursor()
    for k, v in payload.items():
        val_str = json.dumps(v)
        cursor.execute(
            """
            INSERT INTO copa_config (chave, valor)
            VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (k, val_str),
        )
    conn.commit()
    conn.close()
    return get_config()


@router.get("/strategies")
def get_strategies() -> List[Dict[str, Any]]:
    """Retorna a lista de estratégias configuradas."""
    return load_all()


@router.get("/session/{data}")
def get_session(data: str) -> Optional[Dict[str, Any]]:
    """Retorna a SessionDay do dia ou null (200 OK)."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_day WHERE data = ?", (data,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    sessao = dict(row)
    try:
        sessao["niveis"] = json.loads(sessao["niveis"])
    except Exception:
        sessao["niveis"] = []
    try:
        sessao["agenda"] = json.loads(sessao["agenda"])
    except Exception:
        sessao["agenda"] = []

    return sessao


@router.put("/session/{data}")
def upsert_session(data: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Salva ou atualiza a sessão do dia (upsert)."""
    bias_d1 = str(payload.get("bias_d1", "INDEFINIDO")).upper()
    bias_h1 = str(payload.get("bias_h1", "INDEFINIDO")).upper()
    contexto = str(payload.get("contexto", "INDEFINIDO")).upper()

    niveis = payload.get("niveis", [])
    niveis_str = json.dumps(niveis) if not isinstance(niveis, str) else niveis

    agenda = payload.get("agenda", [])
    agenda_str = json.dumps(agenda) if not isinstance(agenda, str) else agenda

    sono = int(payload.get("sono", 3))
    tilt = int(payload.get("tilt", 0))
    pressao = int(payload.get("pressao", 0))
    meta_dia = float(payload.get("meta_dia", 0.0))
    limite_perda_dia = float(payload.get("limite_perda_dia", 300.0))
    max_trades_dia = int(payload.get("max_trades_dia", 3))
    modo = str(payload.get("modo", "NORMAL")).upper()
    notas = str(payload.get("notas", ""))

    # Auto preencher fase_id
    fase = fase_atual(data)
    fase_id = fase["id"] if fase else None

    agora_iso = datetime.now().isoformat()

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO session_day (
          data, bias_d1, bias_h1, contexto, niveis, agenda, sono, tilt, pressao,
          meta_dia, limite_perda_dia, max_trades_dia, modo, notas, criado_em, fase_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(data) DO UPDATE SET
          bias_d1 = excluded.bias_d1,
          bias_h1 = excluded.bias_h1,
          contexto = excluded.contexto,
          niveis = excluded.niveis,
          agenda = excluded.agenda,
          sono = excluded.sono,
          tilt = excluded.tilt,
          pressao = excluded.pressao,
          meta_dia = excluded.meta_dia,
          limite_perda_dia = excluded.limite_perda_dia,
          max_trades_dia = excluded.max_trades_dia,
          modo = excluded.modo,
          notas = excluded.notas,
          fase_id = excluded.fase_id
        """,
        (
            data,
            bias_d1,
            bias_h1,
            contexto,
            niveis_str,
            agenda_str,
            sono,
            tilt,
            pressao,
            meta_dia,
            limite_perda_dia,
            max_trades_dia,
            modo,
            notas,
            agora_iso,
            fase_id,
        ),
    )
    conn.commit()
    conn.close()

    res = get_session(data)
    if res is None:
        raise HTTPException(status_code=500, detail="Erro ao recuperar sessão salva")
    return res


@router.get("/gate")
def get_gate(data: str = Query(...), agora: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Avalia e retorna o gate de liberação/bloqueio do dia."""
    return avaliar_gate(data, agora=agora)


@router.get("/ranking")
def get_ranking(data: str = Query(...)) -> List[Dict[str, Any]]:
    """Gera ranking de estratégias para o dia especificado com base na pré-sessão."""
    sessao = get_session(data) or {}
    strategies = load_all()
    ranking = []
    for s in strategies:
        res = avaliar_ambiente(s, sessao)
        ranking.append({
            "strategy_id": s["id"],
            "nome": s.get("nome", s["id"]),
            "ambiente": res["ambiente"],
            "motivos": res["motivos"],
        })
    return ranking


@router.post("/trades")
def create_trade(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Cria e registra a entrada de um trade com gate estrito no servidor."""
    data = payload.get("data")
    strategy_id = payload.get("strategy_id")
    mercado = str(payload.get("mercado", "")).upper()
    direcao = str(payload.get("direcao", "")).upper()
    checklist = payload.get("checklist", {})
    notas = str(payload.get("notas", ""))

    try:
        entrada = float(payload.get("entrada", 0.0))
        stop = float(payload.get("stop", 0.0))
        alvo = float(payload.get("alvo", 0.0))
        contratos = int(payload.get("contratos", 1))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Valores de preço ou contratos inválidos",
        )

    if not data or not strategy_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data e estratégia são obrigatórias",
        )

    if entrada == stop:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entrada não pode ser igual ao stop",
        )

    # Validar coerência de direção
    if direcao == "COMPRA":
        if not (stop < entrada < alvo):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Compra exige: Stop < Entrada < Alvo",
            )
    elif direcao == "VENDA":
        if not (alvo < entrada < stop):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Venda exige: Alvo < Entrada < Stop",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Direção deve ser COMPRA ou VENDA",
        )

    # Cálculo do RR planejado
    rr_planejado = round(abs(alvo - entrada) / abs(entrada - stop), 2)
    if rr_planejado < 2.0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"RR planejado ({rr_planejado:.2f}) é inferior ao mínimo obrigatório de 2.0",
        )

    # Avaliar Gate de Risco
    agora = payload.get("agora")
    gate = avaliar_gate(data, agora=agora)
    if not gate["liberado"]:
        motivos_str = "; ".join(gate["motivos"])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gate bloqueado: {motivos_str}",
        )

    # Carregar estratégia e auditar checklist
    strategy = load_one(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Estratégia '{strategy_id}' não encontrada",
        )

    score_res = score_checklist(strategy, checklist)
    if score_res["kills_faltando"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Itens KILL obrigatórios faltando: {', '.join(score_res['kills_faltando'])}",
        )

    # Score mínimo (+15 se modo DEFENSIVO)
    modo = gate["breakers"].get("modo", "NORMAL")
    score_minimo = float(strategy.get("score_minimo", 65))
    if modo == "DEFENSIVO":
        score_minimo += 15

    if score_res["score"] < score_minimo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Score atingido ({score_res['score']:.0f}) é inferior ao mínimo exigido ({score_minimo:.0f})",
        )

    criado_em = datetime.now().isoformat()
    checklist_str = json.dumps(checklist)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trade (
          data, strategy_id, mercado, direcao, checklist, score, grade,
          entrada, stop, alvo, contratos, rr_planejado, status, notas, criado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ABERTO', ?, ?)
        """,
        (
            data,
            strategy_id,
            mercado,
            direcao,
            checklist_str,
            score_res["score"],
            score_res["grade"],
            entrada,
            stop,
            alvo,
            contratos,
            rr_planejado,
            notas,
            criado_em,
        ),
    )
    trade_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM trade WHERE id = ?", (trade_id,))
    new_trade = dict(cursor.fetchone())
    conn.close()

    try:
        new_trade["checklist"] = json.loads(new_trade["checklist"])
    except Exception:
        pass

    return new_trade


@router.get("/trades")
def list_trades(
    status: Optional[str] = Query(None),
    data: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Lista trades ordenados do mais recente para o mais antigo."""
    conn = get_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM trade WHERE 1=1"
    params: List[Any] = []

    if status:
        query += " AND status = ?"
        params.append(status.upper())
    if data:
        query += " AND data = ?"
        params.append(data)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    trades: List[Dict[str, Any]] = []
    for r in rows:
        t = dict(r)
        try:
            t["checklist"] = json.loads(t["checklist"])
        except Exception:
            pass
        trades.append(t)
    return trades


@router.patch("/trades/{id}/fechar")
def close_trade(id: int, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Fecha o trade e registra a auditoria de disciplina obrigatória."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trade WHERE id = ?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Trade não encontrado")

    trade = dict(row)
    if trade["status"] == "FECHADO":
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trade já está FECHADO",
        )

    try:
        saida = float(payload.get("saida", 0.0))
    except (ValueError, TypeError):
        conn.close()
        raise HTTPException(status_code=422, detail="Preço de saída inválido")

    motivo_saida = str(payload.get("motivo_saida", "")).upper()
    if motivo_saida not in ("ALVO", "STOP", "MANUAL"):
        conn.close()
        raise HTTPException(status_code=422, detail="Motivo de saída deve ser ALVO, STOP ou MANUAL")

    desfecho_plano = payload.get("desfecho_plano")
    if motivo_saida == "MANUAL" and not desfecho_plano:
        conn.close()
        raise HTTPException(
            status_code=422,
            detail="desfecho_plano é obrigatório para saídas manuais (BATEU_ALVO, BATEU_STOP, NAO_SEI)",
        )

    respeitou_plano = int(bool(payload.get("respeitou_plano", 0)))
    antecipou_stop = int(bool(payload.get("antecipou_stop", 0)))
    parcial_emocional = int(bool(payload.get("parcial_emocional", 0)))
    mudou_alvo = int(bool(payload.get("mudou_alvo", 0)))
    notas_adicionais = payload.get("notas", "")

    # Calcular resultado real
    pontos_real, pnl_real = calcular_pnl(
        trade["mercado"], trade["direcao"], trade["entrada"], saida, trade["contratos"]
    )

    # Calcular PnL do plano
    if motivo_saida == "ALVO":
        _, pnl_plano = calcular_pnl(
            trade["mercado"], trade["direcao"], trade["entrada"], trade["alvo"], trade["contratos"]
        )
    elif motivo_saida == "STOP":
        _, pnl_plano = calcular_pnl(
            trade["mercado"], trade["direcao"], trade["entrada"], trade["stop"], trade["contratos"]
        )
    else:  # MANUAL
        desfecho_upper = str(desfecho_plano).upper()
        if desfecho_upper == "BATEU_ALVO":
            _, pnl_plano = calcular_pnl(
                trade["mercado"], trade["direcao"], trade["entrada"], trade["alvo"], trade["contratos"]
            )
        elif desfecho_upper == "BATEU_STOP":
            _, pnl_plano = calcular_pnl(
                trade["mercado"], trade["direcao"], trade["entrada"], trade["stop"], trade["contratos"]
            )
        else:
            pnl_plano = pnl_real

    fechado_em = datetime.now().isoformat()
    notas_finais = (trade["notas"] + "\n" + notas_adicionais).strip() if notas_adicionais else trade["notas"]

    cursor.execute(
        """
        UPDATE trade SET
          status = 'FECHADO',
          saida = ?,
          motivo_saida = ?,
          desfecho_plano = ?,
          pnl_real = ?,
          pnl_plano = ?,
          pontos_real = ?,
          respeitou_plano = ?,
          antecipou_stop = ?,
          parcial_emocional = ?,
          mudou_alvo = ?,
          notas = ?,
          fechado_em = ?
        WHERE id = ?
        """,
        (
            saida,
            motivo_saida,
            desfecho_plano,
            pnl_real,
            pnl_plano,
            pontos_real,
            respeitou_plano,
            antecipou_stop,
            parcial_emocional,
            mudou_alvo,
            notas_finais,
            fechado_em,
            id,
        ),
    )
    conn.commit()

    cursor.execute("SELECT * FROM trade WHERE id = ?", (id,))
    updated = dict(cursor.fetchone())
    conn.close()

    try:
        updated["checklist"] = json.loads(updated["checklist"])
    except Exception:
        pass

    return updated


@router.delete("/trades/{id}")
def delete_trade(id: int) -> Dict[str, bool]:
    """Deleta trade apenas se status == ABERTO."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM trade WHERE id = ?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Trade não encontrado")

    if row["status"] != "ABERTO":
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas trades com status ABERTO podem ser deletados",
        )

    cursor.execute("DELETE FROM trade WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/stats")
def get_stats() -> Dict[str, Any]:
    """Retorna relatório de estatísticas consolidadas e custo da indisciplina."""
    return stats.calcular()


@router.get("/export")
def export_db() -> FileResponse:
    """Exporta e envia o arquivo do banco de dados SQLite."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Banco de dados não encontrado")
    return FileResponse(
        path=DB_PATH,
        filename="copa.db",
        media_type="application/x-sqlite3",
    )


@router.get("/fase")
def get_fase_info(data: str = Query(...)) -> Dict[str, Any]:
    """Retorna informações e placar da fase que contém a data especificada."""
    fase = fase_atual(data)
    if not fase:
        return {"fase": None}
    return placar_fase(fase["id"])
