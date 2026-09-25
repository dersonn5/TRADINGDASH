"""C2 com os dois cenarios descritos pelo operador (25/09/2026).

B = barra de 15 min das 10:00. B varre o topo (fundo) de uma barra de 15 min anterior,
intacto ate 10:00. Operacao sempre CONTRA o lado varrido.

Confirmacao (o que o operador descreveu):
  b2: a propria B reverte - varre e fecha contra (de baixa apos varrer topo).
      Sweep e inicio da reversao na mesma barra. Conhecido as 10:15.
  b1: B nao reverteu; a barra das 10:15 fecha contra B, dentro dela (V1 de backtest_c2.py).
      Conhecido as 10:30.

Contexto da 1a hora (4 barras de 15 min, 09:00-09:59):
  tendencia = 3 das 4 barras na mesma cor OU movimento liquido >= 475 pts.
  continuacao = operacao a favor da tendencia (ex.: tendencia de baixa, B varre um topo,
                venda) - cenario 1 do operador.
  contra      = operacao contra a tendencia (B varre o extremo da tendencia e reverte).
  lateral     = sem tendencia.
Contra + lateral = cenario 2 do operador (reversao no BSL/SSL).

Controle: a mesma confirmacao (mesma cor de barra) sem B ter varrido o lado.

Parte 1 - 5 anos de 15 min: entrada no fechamento da barra que confirma; stop no extremo
  de B ate essa barra + 1 tick; chance de kR antes do stop ate 12:00.
Parte 2 - 5 meses de 1 min: MSS + FVG no sentido, MSS depois do minuto do extremo de B e
  antes de 11:15, entrada so depois da confirmacao (sem olhar o futuro).
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

TICK = 5
ESTICADA = 475
H = bq.hm


def tendencia(b15):
    h1 = [b for b in b15 if 540 <= p.minutos(b[0]) < 600]
    if len(h1) < 4:
        return 0
    alta = sum(b[4] > b[1] for b in h1)
    baixa = sum(b[4] < b[1] for b in h1)
    net = h1[-1][4] - h1[0][1]
    s_barras = 1 if alta >= 3 else -1 if baixa >= 3 else 0
    s_net = 1 if net >= ESTICADA else -1 if net <= -ESTICADA else 0
    if s_barras and s_net and s_barras != s_net:
        return 0
    return s_barras or s_net


def sinais(b15):
    """(tipo, grupo, lado, i_entrada, contexto)"""
    idx = {p.minutos(b[0]): i for i, b in enumerate(b15)}
    if 600 not in idx or 615 not in idx:
        return []
    iB, iN = idx[600], idx[615]
    B, N = b15[iB], b15[iN]
    antes = [i for i in range(iB) if p.minutos(b15[i][0]) >= 540]
    topos = [b15[i][2] for i in antes if all(b15[k][2] < b15[i][2] for k in range(i + 1, iB))]
    fundos = [b15[i][3] for i in antes if all(b15[k][3] > b15[i][3] for k in range(i + 1, iB))]
    vt = any(B[2] > t for t in topos)
    vf = any(B[3] < f for f in fundos)
    tend = tendencia(b15)
    out = []
    for lado in (-1, 1):
        varreu = (vt if lado < 0 else vf) and not (vt and vf)
        grupo = "C2" if varreu else "controle"
        ctx = "lateral" if tend == 0 else "continuacao" if tend == lado else "contra"
        if (B[4] < B[1]) if lado < 0 else (B[4] > B[1]):
            out.append(("b2", grupo, lado, iB, ctx))
        elif (N[4] < N[1] and N[4] < B[2]) if lado < 0 else (N[4] > N[1] and N[4] > B[3]):
            out.append(("b1", grupo, lado, iN, ctx))
    return out


def mfe15(b15, iB, i_ent, lado):
    ent = b15[i_ent][4]
    ext = max(b[2] for b in b15[iB:i_ent + 1]) if lado < 0 else min(b[3] for b in b15[iB:i_ent + 1])
    stop = ext + TICK if lado < 0 else ext - TICK
    R = abs(ent - stop)
    if R <= 0:
        return None
    melhor = 0.0
    for y in b15[i_ent + 1:]:
        if p.minutos(y[0]) >= 720:
            break
        if (y[2] >= stop) if lado < 0 else (y[3] <= stop):
            return melhor
        melhor = max(melhor, ((ent - y[3]) if lado < 0 else (y[2] - ent)) / R)
    return melhor


def linha15(rot, x):
    n = len(x)
    if not n:
        print(f"  {rot:<34} n=   0")
        return
    f = lambda k: sum(m >= k for m in x) / n
    print(f"  {rot:<34} n={n:4d}  1R {f(1):4.0%}  2R {f(2):4.0%}  3R {f(3):4.0%}  5R {f(5):4.0%}")


def linha1(rot, x, meio):
    n = len(x)
    if n < 2:
        print(f"  {rot:<34} n={n:3d}")
        return
    rs = [t["r"] for t in x]
    m = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5
    a = [t["r"] for t in x if t["data"] <= meio]
    b = [t["r"] for t in x if t["data"] > meio]
    print(f"  {rot:<34} n={n:3d}  media {m:+.2f}R (t={m / se if se else 0:+.1f})  metades "
          f"{st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}  "
          f"R$ {sum(t['pts'] for t in x) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))


def parte1():
    r = defaultdict(list)
    anos = defaultdict(list)
    for d, b15 in sorted(p.carregar15().items()):
        for tipo, grupo, lado, i_ent, ctx in sinais(b15):
            iB = next(i for i, b in enumerate(b15) if p.minutos(b[0]) == 600)
            m = mfe15(b15, iB, i_ent, lado)
            if m is None:
                continue
            for chave in ((tipo, grupo), ("todos", grupo), ("ctx", grupo, ctx)):
                r[chave].append(m)
            anos[(grupo, d.year)].append(m)
    print("PARTE 1 - 5 anos de 15 min. Entrada no fechamento da confirmacao, stop no extremo de B.\n")
    for tipo, rot in (("b2", "b2 (B varre e ja reverte)"), ("b1", "b1 (10:15 fecha de volta)"),
                      ("todos", "b1 + b2")):
        for g in ("C2", "controle"):
            linha15(f"{rot} {g}", r[(tipo, g)])
        print()
    print("  C2 por contexto da 1a hora:")
    for ctx in ("continuacao", "contra", "lateral"):
        linha15(f"{ctx} C2", r[("ctx", "C2", ctx)])
        linha15(f"{ctx} controle", r[("ctx", "controle", ctx)])
    print("\n  por ano, chance de 2R (b1 + b2):  C2  x  controle")
    for a in range(2021, 2027):
        c, k = anos[("C2", a)], anos[("controle", a)]
        f = lambda v: f"{sum(m >= 2 for m in v) / len(v):4.0%} (n={len(v):3d})" if v else "  -  "
        print(f"   {a}: {f(c)}  x  {f(k)}")


def parte2():
    dias1 = bq.carregar()
    o = sorted(dias1)
    meio = o[len(o) // 2]
    g = defaultdict(list)
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias1[d], H("09:00"), H("17:51"))
        ant = bq.entre(dias1[o[kd - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        b15 = p.agrega15(bs)
        ss = sinais(b15)
        if not ss:
            continue
        gs = hl.gatilhos_do_dia(bs, ant)
        barraB = [b for b in bs if 600 <= p.minutos(b[0]) < 615]
        if not barraB:
            continue
        for tipo, grupo, lado, i_ent, ctx in ss:
            ext = max(barraB, key=lambda b: b[2]) if lado < 0 else min(barraB, key=lambda b: b[3])
            t_ext = p.minutos(ext[0])
            conf = 615 if tipo == "b2" else 630
            c = [x for x in gs if x["lado"] == lado and t_ext < p.minutos(x["t_mss"]) < 675
                 and p.minutos(x["t_ent"]) >= conf]
            if c:
                x = dict(c[0])
                x["data"] = d
                for chave in ((tipo, grupo), ("todos", grupo), ("ctx", grupo, ctx)):
                    g[chave].append(x)
    print("\nPARTE 2 - 5 meses de 1 min, gatilho do operador, entrada so apos a confirmacao:\n")
    for tipo, rot in (("b2", "b2 (B varre e ja reverte)"), ("b1", "b1 (10:15 fecha de volta)"),
                      ("todos", "b1 + b2")):
        for grp in ("C2", "controle"):
            linha1(f"{rot} {grp}", g[(tipo, grp)], meio)
        print()
    print("  C2 por contexto da 1a hora:")
    for ctx in ("continuacao", "contra", "lateral"):
        linha1(f"{ctx} C2", g[("ctx", "C2", ctx)], meio)
        linha1(f"{ctx} controle", g[("ctx", "controle", ctx)], meio)


if __name__ == "__main__":
    parte1()
    parte2()
