"""Backtest do Setup C (C1 e C2) com todo o historico salvo do cache do Profit.

Definicoes fixadas antes de rodar (25/09/2026, a partir do Trade System):
  B = barra de 15 min das 10:00.
  C1 (B e manipulada): entre 10:15 e 11:14 uma barra passa da max/min de B e FECHA
     de volta dentro. Topo varrido -> venda; fundo -> compra.
  C2 (B manipula): B passa do topo (fundo) de uma barra de 15 min anterior que
     estava intacto ate 10:00; depois, entre 10:15 e 11:14, uma barra FECHA abaixo
     da minima (acima da maxima) de B. Topo varrido -> venda; fundo -> compra.
  CONTROLE do C2: o mesmo rompimento de B, sem B ter varrido nada antes.

Parte 1 - 5 anos, 15 min (so estrutura; sem gatilho de 1 min):
  C2/controle: entrada no fechamento da barra que rompeu; stop na max (min) dessa
  barra + 1 tick; mede ate quantos R chega antes do stop, ate B + 2h.
Parte 2 - 5 meses, 1 min: o gatilho do operador (MSS + FVG, gestao BSL/SSL +
  trailing) no sentido do C1/C2, com MSS a partir da barra de 15 min do sinal e
  ate 11:14.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

TICK = 5
H = bq.hm


def sinais(b15):
    """Devolve lista de sinais do dia: (modo, lado, i_barra_sinal)."""
    idx = {p.minutos(b[0]): i for i, b in enumerate(b15)}
    if 600 not in idx:
        return []
    iB = idx[600]
    B = b15[iB]
    antes = [i for i in range(iB) if p.minutos(b15[i][0]) >= 540]
    if not antes:
        return []
    # liquidez intacta ate 10:00 nas barras anteriores
    topos = [b15[i][2] for i in antes if all(b15[k][2] < b15[i][2] for k in range(i + 1, iB))]
    fundos = [b15[i][3] for i in antes if all(b15[k][3] > b15[i][3] for k in range(i + 1, iB))]
    varreu_topo = any(B[2] > t for t in topos)
    varreu_fundo = any(B[3] < f for f in fundos)
    out = []
    # C1
    r = p.analisar(b15, 10)
    if r and not r.get("sem"):
        ib = next(i for i, b in enumerate(b15) if b[0] == r["barra"])
        out.append(("C1", r["lado"], ib))
    # C2 e controle: primeiro rompimento de B por fechamento, 10:15-11:14
    for k in range(iB + 1, min(iB + 5, len(b15))):
        x = b15[k]
        if x[4] < B[3]:
            modo = "C2" if varreu_topo else "controle"
            out.append((modo, -1, k))
            break
        if x[4] > B[2]:
            modo = "C2" if varreu_fundo else "controle"
            out.append((modo, 1, k))
            break
    return out


def mfe15(b15, k, lado, fim_min):
    x = b15[k]
    ent = x[4]
    stop = x[2] + TICK if lado < 0 else x[3] - TICK
    R = abs(ent - stop)
    if R <= 0:
        return None
    melhor = 0.0
    for y in b15[k + 1:]:
        if p.minutos(y[0]) >= fim_min:
            break
        if (y[2] >= stop) if lado < 0 else (y[3] <= stop):
            return melhor, R
        melhor = max(melhor, ((ent - y[3]) if lado < 0 else (y[2] - ent)) / R)
    return melhor, R


def parte1():
    dias = p.carregar15()
    res = defaultdict(list)
    por_ano = defaultdict(lambda: defaultdict(list))
    for d, b15 in sorted(dias.items()):
        for modo, lado, k in sinais(b15):
            if modo == "C1":
                continue
            m = mfe15(b15, k, lado, 720)
            if m:
                res[modo].append(m[0])
                por_ano[d.year][modo].append(m[0])
    print("PARTE 1 - 5 anos de 15 min: rompimento da barra das 10, entrada no fechamento,")
    print("stop na barra que rompeu. Chance de chegar a kR antes do stop, ate 12:00.\n")
    for modo in ("C2", "controle"):
        v = res[modo]
        n = len(v)
        f = lambda k: sum(x >= k for x in v) / n
        rot = "C2 (barra das 10 varreu antes)" if modo == "C2" else "CONTROLE (rompimento sem varrida)"
        print(f"  {rot:<36} n={n:4d}  1R {f(1):4.0%}  2R {f(2):4.0%}  3R {f(3):4.0%}  5R {f(5):4.0%}")
    print("\n  por ano, chance de 2R:   C2  x  controle")
    for a in sorted(por_ano):
        c, k2 = por_ano[a]["C2"], por_ano[a]["controle"]
        f = lambda v: f"{sum(x >= 2 for x in v) / len(v):4.0%} (n={len(v):3d})" if v else "   -      "
        print(f"   {a}: {f(c)}  x  {f(k2)}")


def parte2():
    dias1 = bq.carregar()
    o = sorted(dias1)
    grupos = defaultdict(list)
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias1[d], H("09:00"), H("17:51"))
        ant = bq.entre(dias1[o[kd - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        b15 = p.agrega15(bs)
        gs = None
        for modo, lado, k in sinais(b15):
            ini = p.minutos(b15[k][0])
            gs = gs if gs is not None else hl.gatilhos_do_dia(bs, ant)
            c = [g for g in gs if g["lado"] == lado and ini <= p.minutos(g["t_mss"]) < 675]
            if c:
                g = dict(c[0])
                g["data"] = d
                grupos[modo].append(g)
    print("\nPARTE 2 - 5 meses de 1 min: gatilho do operador (MSS + FVG), gestao BSL/SSL + trailing.\n")
    meio = o[len(o) // 2]
    for modo in ("C1", "C2", "controle"):
        v = grupos[modo]
        n = len(v)
        if not n:
            print(f"  {modo}: sem trades")
            continue
        rs = [g["r"] for g in v]
        m = st.mean(rs)
        se = st.pstdev(rs) / n ** 0.5 if n > 1 else 0
        f = lambda k: sum(g["mfe"] >= k for g in v) / n
        a = [g["r"] for g in v if g["data"] <= meio]
        b = [g["r"] for g in v if g["data"] > meio]
        rot = {"C1": "C1 (barra das 10 varrida)", "C2": "C2 (barra das 10 varre, depois rompe)",
               "controle": "CONTROLE (rompe sem varrer)"}[modo]
        print(f"  {rot:<38} n={n:3d}  3R {f(3):4.0%}  5R {f(5):4.0%}  media {m:+.2f}R (t={m / se if se else 0:+.1f})"
              f"  metades {st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}"
              f"  R$ {sum(g['pts'] for g in v) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))


if __name__ == "__main__":
    parte1()
    parte2()
