"""Padrao observado pelo operador no grafico de 15 min (22/09/2026):
"se o a vista abre e as proximas 4 barras varrem a maxima ou a minima dela,
reverte a favor de um movimento".

Definicoes (confirmadas pelo operador antes de rodar):
  Barra B     = candle de 15 min que abre as HH:00 (10:00 no caso principal).
  Varrida     = uma das 4 barras seguintes passa da maxima (minima) de B e FECHA de
                volta abaixo (acima) dela. Vale a primeira.
                Varreu a maxima -> reversao para BAIXO; varreu a minima -> para CIMA.
  Contexto    = direcao da hora anterior a B (fechamento - abertura).
                "a favor" = a reversao vai no sentido dessa hora (continuidade).
  Entrada de referencia = fechamento da barra da varrida.
  Stop de referencia    = extremo da varrida + 1 tick.
  Resultado 1 = chega ao lado OPOSTO de B antes de passar do extremo da varrida,
                ate B + 2h. Mede tambem em R: (entrada - lado oposto) / risco.
  Resultado 2 = quanto andou a favor ate B + 2h (fechamento) e o maximo a favor.
Controle: barras das 11, 13 e 14.

Fonte principal: 15 min do cache (275 pregoes). Conferencia: 1 min (108 pregoes),
agregado em 15 min, com o caminho resolvido minuto a minuto (sem ambiguidade de
qual extremo veio primeiro dentro do candle).
"""

import csv
import datetime as dt
import statistics as st
from collections import defaultdict
from pathlib import Path

import backtest_quarters as bq

TICK = 5
AQUI = Path(__file__).parent


def carregar15():
    dias = defaultdict(list)
    with (AQUI / "WINFUT_15min.csv").open() as f:
        for r in csv.DictReader(f):
            t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
            dias[t.date()].append((t.time(), float(r["open"]), float(r["high"]),
                                   float(r["low"]), float(r["close"])))
    return dias


def agrega15(bs1):
    g = defaultdict(list)
    for b in bs1:
        m = b[0].hour * 60 + b[0].minute
        g[m // 15].append(b)
    out = []
    for k in sorted(g):
        x = g[k]
        out.append((dt.time(k * 15 // 60, k * 15 % 60), x[0][1], max(b[2] for b in x),
                    min(b[3] for b in x), x[-1][4]))
    return out


def minutos(t):
    return t.hour * 60 + t.minute


def analisar(b15, hora, bs1=None):
    """b15: barras de 15 min do dia. bs1: barras de 1 min (opcional, para o caminho)."""
    idx = {minutos(b[0]): i for i, b in enumerate(b15)}
    m0 = hora * 60
    if m0 not in idx or (m0 - 60) not in idx:
        return None
    iB = idx[m0]
    B = b15[iB]
    antes = [b for b in b15 if m0 - 60 <= minutos(b[0]) < m0]
    ctx = antes[-1][4] - antes[0][1]
    for k in range(iB + 1, min(iB + 5, len(b15))):
        x = b15[k]
        topo = x[2] > B[2] and x[4] < B[2]
        fundo = x[3] < B[3] and x[4] > B[3]
        if topo == fundo:
            continue  # nenhum, ou os dois (ambiguo)
        lado = -1 if topo else 1
        entrada = x[4]
        extremo = x[2] if topo else x[3]
        stop = extremo + TICK if topo else extremo - TICK
        alvo = B[3] if topo else B[2]
        risco = abs(entrada - stop)
        fim = m0 + 120
        t_ent = minutos(x[0]) + 15  # a entrada e no fechamento da barra da varrida
        if bs1 is not None:
            cam = [(b[2], b[3], b[4]) for b in bs1 if t_ent <= minutos(b[0]) < fim]
        else:
            cam = [(b[2], b[3], b[4]) for b in b15 if t_ent <= minutos(b[0]) < fim]
        if not cam:
            return None
        chegou = None
        for h, l, c in cam:
            bate_stop = h >= stop if topo else l <= stop
            bate_alvo = l <= alvo if topo else h >= alvo
            if bate_stop:  # conservador: stop primeiro
                chegou = False
                break
            if bate_alvo:
                chegou = True
                break
        if chegou is None:
            chegou = False
        mfe = max(((entrada - l) if topo else (h - entrada)) for h, l, c in cam)
        final = (cam[-1][2] - entrada) * lado
        return dict(lado=lado, favor=(ctx != 0 and (ctx > 0) == (lado > 0)), chegou=chegou,
                    r_alvo=abs(entrada - alvo) / risco if risco else 0, risco=risco,
                    mfe=mfe, final=final, barra=x[0])
    return {"sem": True}


def resumo(rot, rs):
    ts = [r for r in rs if not r.get("sem")]
    n = len(ts)
    if not n:
        print(f"  {rot:<34} sem casos")
        return
    ch = sum(r["chegou"] for r in ts) / n
    rr = st.median(r["r_alvo"] for r in ts)
    exp = sum((r["r_alvo"] if r["chegou"] else -1) for r in ts) / n
    print(f"  {rot:<34} n={n:3d}  chega ao oposto {ch:4.0%}  (alvo mediano {rr:.1f}R, resultado {exp:+.2f}R/trade)"
          f"  | ate +2h: fecha a favor {sum(r['final'] > 0 for r in ts) / n:4.0%}, media {st.mean(r['final'] for r in ts):+5.0f} pts")


def rodar(nome, dias_dados, agregar):
    print(f"\n=== {nome} ===")
    ordem = sorted(dias_dados)
    meio = ordem[len(ordem) // 2]
    for hora in (10, 11, 13, 14):
        rs = []
        for d in ordem:
            bs = dias_dados[d]
            b15 = agrega15(bs) if agregar else bs
            r = analisar(b15, hora, bs if agregar else None)
            if r:
                r["data"] = d
                rs.append(r)
        casos = [r for r in rs if not r.get("sem")]
        marca = "   <- barra das 10 (a vista)" if hora == 10 else ""
        print(f" Barra das {hora}: {len(rs)} dias, varrida em {len(casos)} ({len(casos) / max(len(rs), 1):.0%}){marca}")
        resumo("todas as varridas", casos)
        resumo("a favor da hora anterior", [r for r in casos if r["favor"]])
        resumo("contra a hora anterior", [r for r in casos if not r["favor"]])
        if hora == 10:
            resumo("  1a metade", [r for r in casos if r["data"] <= meio])
            resumo("  2a metade", [r for r in casos if r["data"] > meio])


def main():
    rodar("15 min, 275 pregoes (ordem dentro do candle: stop primeiro)", carregar15(), False)
    rodar("1 min agregado em 15 min, 108 pregoes (caminho minuto a minuto)", bq.carregar(), True)


if __name__ == "__main__":
    main()
