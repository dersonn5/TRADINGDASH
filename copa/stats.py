"""
Motor de Estatísticas e Análise de Probabilidades da Copa BTG.
=============================================================
Calcula métricas agregadas, curvas de capital, performance por item de checklist,
por grade, por estratégia, por hora, por dia da semana e custo da indisciplina.
"""
import json
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from copa.db import get_conn
from copa.strategies_config import load_all


DIAS_SEMANA_MAP = {
    0: "seg",
    1: "ter",
    2: "qua",
    3: "qui",
    4: "sex",
    5: "sab",
    6: "dom",
}


def calcular() -> Dict[str, Any]:
    """Calcula todas as estatísticas consolidadas sobre os trades fechados."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trade WHERE status = 'FECHADO' ORDER BY id ASC")
    rows = cursor.fetchall()

    cursor.execute("SELECT chave, valor FROM copa_config")
    cfg_rows = cursor.fetchall()
    conn.close()

    config = {}
    for r in cfg_rows:
        try:
            config[r["chave"]] = json.loads(r["valor"])
        except Exception:
            config[r["chave"]] = r["valor"]

    banca_inicial = float(config.get("banca_inicial", 0.0))
    meta_copa = float(config.get("meta_dia_padrao", 0.0))

    # Estrutura padrão com zero trades
    default_structure: Dict[str, Any] = {
        "geral": {
            "trades": 0,
            "winrate": 0.0,
            "profit_factor": 0.0,
            "expectancia": 0.0,
            "pnl_total": 0.0,
            "max_drawdown": 0.0,
            "banca_atual": banca_inicial,
            "meta_copa": meta_copa,
            "falta_para_meta": meta_copa,
        },
        "equity": [{"t": datetime.now().strftime("%Y-%m-%d"), "balance": banca_inicial}],
        "por_estrategia": [],
        "por_grade": [],
        "por_item": [],
        "por_hora": [],
        "por_dia_semana": [],
        "disciplina": {
            "trades_com_desvio": 0,
            "custo_total": 0.0,
            "por_flag": [
                {"flag": "antecipou_stop", "n": 0, "custo": 0.0},
                {"flag": "parcial_emocional", "n": 0, "custo": 0.0},
                {"flag": "mudou_alvo", "n": 0, "custo": 0.0},
                {"flag": "nao_respeitou_plano", "n": 0, "custo": 0.0},
            ],
        },
    }

    if not rows:
        return default_structure

    # Transformar em DataFrame
    trades_data = [dict(r) for r in rows]
    df = pd.DataFrame(trades_data)

    df["pnl_real"] = df["pnl_real"].astype(float).fillna(0.0)
    df["pnl_plano"] = df["pnl_plano"].astype(float).fillna(df["pnl_real"])
    df["is_win"] = df["pnl_real"] > 0
    df["is_loss"] = df["pnl_real"] < 0

    total_trades = len(df)
    total_wins = int(df["is_win"].sum())
    total_pnl = round(float(df["pnl_real"].sum()), 2)
    winrate = round((total_wins / total_trades) * 100.0, 1) if total_trades > 0 else 0.0
    expectancia = round(total_pnl / total_trades, 2) if total_trades > 0 else 0.0

    soma_ganhos = float(df[df["pnl_real"] > 0]["pnl_real"].sum())
    soma_perdas = abs(float(df[df["pnl_real"] < 0]["pnl_real"].sum()))
    profit_factor = round(soma_ganhos / soma_perdas, 2) if soma_perdas > 0 else 0.0

    # Curva de capital e Drawdown
    equity_points = []
    bal = banca_inicial
    peak = bal
    max_dd = 0.0

    for _, row in df.iterrows():
        pnl = row["pnl_real"]
        bal = round(bal + pnl, 2)
        if bal > peak:
            peak = bal
        dd = round(((peak - bal) / peak) * 100.0, 1) if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
        t_label = row.get("fechado_em") or row.get("data") or datetime.now().strftime("%Y-%m-%d")
        equity_points.append({"t": str(t_label), "balance": bal})

    banca_atual = bal
    falta_para_meta = round(max(0.0, meta_copa - total_pnl), 2)

    # 1. Por Estratégia
    por_estrategia = []
    strats = load_all()
    strat_nome_map = {s["id"]: s.get("nome", s["id"]) for s in strats}

    for strat_id, group in df.groupby("strategy_id"):
        n = len(group)
        wins = int(group["is_win"].sum())
        pnl_strat = round(float(group["pnl_real"].sum()), 2)
        wr = round((wins / n) * 100.0, 1) if n > 0 else 0.0
        exp = round(pnl_strat / n, 2) if n > 0 else 0.0
        por_estrategia.append({
            "strategy_id": str(strat_id),
            "nome": strat_nome_map.get(str(strat_id), str(strat_id)),
            "n": n,
            "winrate": wr,
            "expectancia": exp,
            "pnl": pnl_strat,
        })

    # 2. Por Grade
    por_grade = []
    for grade_name in ["A+", "A", "B", "C", "D"]:
        group = df[df["grade"] == grade_name]
        n = len(group)
        if n > 0:
            wins = int(group["is_win"].sum())
            pnl_grade = round(float(group["pnl_real"].sum()), 2)
            wr = round((wins / n) * 100.0, 1)
            exp = round(pnl_grade / n, 2)
            por_grade.append({
                "grade": grade_name,
                "n": n,
                "winrate": wr,
                "expectancia": exp,
                "pnl": pnl_grade,
            })

    # 3. Por Item de Checklist (o core do edge analítico)
    por_item = []
    for s in strats:
        strat_id = s["id"]
        strat_trades = df[df["strategy_id"] == strat_id]
        if strat_trades.empty:
            continue

        for item in s.get("checklist", []):
            item_id = item["id"]
            label = item.get("label", item_id)
            tipo = item.get("tipo", "PONTO")

            marcados_pnls: List[float] = []
            nao_marcados_pnls: List[float] = []

            for _, t_row in strat_trades.iterrows():
                try:
                    chk = json.loads(t_row["checklist"]) if isinstance(t_row["checklist"], str) else t_row["checklist"]
                except Exception:
                    chk = {}
                is_checked = bool(chk.get(item_id, False))
                pnl_val = float(t_row["pnl_real"])
                if is_checked:
                    marcados_pnls.append(pnl_val)
                else:
                    nao_marcados_pnls.append(pnl_val)

            n_m = len(marcados_pnls)
            n_n = len(nao_marcados_pnls)

            wins_m = sum(1 for p in marcados_pnls if p > 0)
            wins_n = sum(1 for p in nao_marcados_pnls if p > 0)

            wr_m = round((wins_m / n_m) * 100.0, 1) if n_m > 0 else 0.0
            wr_n = round((wins_n / n_n) * 100.0, 1) if n_n > 0 else 0.0

            exp_m = round(sum(marcados_pnls) / n_m, 2) if n_m > 0 else 0.0
            exp_n = round(sum(nao_marcados_pnls) / n_n, 2) if n_n > 0 else 0.0

            delta_wr = round(wr_m - wr_n, 1)
            amostra_baixa = n_m < 20 or n_n < 20

            por_item.append({
                "strategy_id": strat_id,
                "item_id": item_id,
                "label": label,
                "tipo": tipo,
                "n_marcado": n_m,
                "winrate_marcado": wr_m,
                "exp_marcado": exp_m,
                "n_nao": n_n,
                "winrate_nao": wr_n,
                "exp_nao": exp_n,
                "delta_winrate": delta_wr,
                "amostra_baixa": amostra_baixa,
            })

    por_item.sort(key=lambda x: x["delta_winrate"], reverse=True)

    # 4. Por Hora
    por_hora = []
    df["hora"] = df["criado_em"].apply(
        lambda x: str(x)[11:13] if len(str(x)) >= 13 else "09"
    )
    for hora_str, group in df.groupby("hora"):
        n = len(group)
        wins = int(group["is_win"].sum())
        pnl_h = round(float(group["pnl_real"].sum()), 2)
        wr = round((wins / n) * 100.0, 1) if n > 0 else 0.0
        por_hora.append({
            "hora": str(hora_str),
            "n": n,
            "winrate": wr,
            "pnl": pnl_h,
        })
    por_hora.sort(key=lambda x: x["hora"])

    # 5. Por Dia da Semana
    por_dia_semana = []
    def _dia_sem(val):
        try:
            dt = datetime.fromisoformat(str(val)[:10])
            return DIAS_SEMANA_MAP.get(dt.weekday(), "seg")
        except Exception:
            return "seg"

    df["dia_sem"] = df["data"].apply(_dia_sem)
    for dia_str, group in df.groupby("dia_sem"):
        n = len(group)
        wins = int(group["is_win"].sum())
        pnl_d = round(float(group["pnl_real"].sum()), 2)
        wr = round((wins / n) * 100.0, 1) if n > 0 else 0.0
        por_dia_semana.append({
            "dia": str(dia_str),
            "n": n,
            "winrate": wr,
            "pnl": pnl_d,
        })

    # 6. Disciplina e Custo de Indisciplina
    # Trades com desvio: antecipou_stop == 1 ou parcial_emocional == 1 ou mudou_alvo == 1 ou respeitou_plano == 0
    desvio_mask = (
        (df["antecipou_stop"] == 1)
        | (df["parcial_emocional"] == 1)
        | (df["mudou_alvo"] == 1)
        | (df["respeitou_plano"] == 0)
    )
    trades_desvio = df[desvio_mask]
    trades_com_desvio = len(trades_desvio)

    # custo: pnl_plano - pnl_real
    df["custo_desvio"] = df["pnl_plano"] - df["pnl_real"]
    custo_total = round(float(df[desvio_mask]["custo_desvio"].sum()), 2)

    por_flag = [
        {
            "flag": "antecipou_stop",
            "n": int((df["antecipou_stop"] == 1).sum()),
            "custo": round(float(df[df["antecipou_stop"] == 1]["custo_desvio"].sum()), 2),
        },
        {
            "flag": "parcial_emocional",
            "n": int((df["parcial_emocional"] == 1).sum()),
            "custo": round(float(df[df["parcial_emocional"] == 1]["custo_desvio"].sum()), 2),
        },
        {
            "flag": "mudou_alvo",
            "n": int((df["mudou_alvo"] == 1).sum()),
            "custo": round(float(df[df["mudou_alvo"] == 1]["custo_desvio"].sum()), 2),
        },
        {
            "flag": "nao_respeitou_plano",
            "n": int((df["respeitou_plano"] == 0).sum()),
            "custo": round(float(df[df["respeitou_plano"] == 0]["custo_desvio"].sum()), 2),
        },
    ]

    return {
        "geral": {
            "trades": total_trades,
            "winrate": winrate,
            "profit_factor": profit_factor,
            "expectancia": expectancia,
            "pnl_total": total_pnl,
            "max_drawdown": max_dd,
            "banca_atual": banca_atual,
            "meta_copa": meta_copa,
            "falta_para_meta": falta_para_meta,
        },
        "equity": equity_points,
        "por_estrategia": por_estrategia,
        "por_grade": por_grade,
        "por_item": por_item,
        "por_hora": por_hora,
        "por_dia_semana": por_dia_semana,
        "disciplina": {
            "trades_com_desvio": trades_com_desvio,
            "custo_total": custo_total,
            "por_flag": por_flag,
        },
    }
