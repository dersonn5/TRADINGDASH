"""Setup C como o operador opera ao vivo (25/09/2026):
  "a entrada no 1m nao depende da barra dos 15 fechar; se ela sweepar uma regiao, ja e
   valido olhar o 1m e esperar o setup de reversao".

Sem usar o fechamento de 15 min (que ainda nao se sabe no momento da entrada):
  C1: entre 10:15 e 11:14, o preco passa da maxima (minima) da barra das 10 -> sweep.
  C2: dentro da barra das 10 (10:00-10:14), o preco passa do topo (fundo) de uma barra de
      15 min anterior, intacto ate 10:00 -> sweep.
  Depois do minuto do sweep: primeiro MSS + FVG de reversao (contra o lado varrido), MSS em
  ate 30 min depois do sweep e antes de 11:15, entrada antes de 11:30. Gestao BSL/SSL +
  trailing (hierarquia_liquidez.gatilhos_do_dia).
Base de comparacao: todos os gatilhos MSS + FVG da mesma janela, sem condicao nenhuma.
Informativo: separa depois os casos em que a barra de 15 min fechou de volta ou nao.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import backtest_c2b as c2b
import hierarquia_liquidez as hl
import padrao_15m as p

H = bq.hm


def m(b):
    return p.minutos(b[0])


def sweeps(bs, b15):
    """[(modo, lado, minuto_do_sweep, fechou_de_volta)]"""
    idx = {m(b): i for i, b in enumerate(b15)}
    if 600 not in idx:
        return []
    iB = idx[600]
    B = b15[iB]
    out = []
    antes = [i for i in range(iB) if m(b15[i]) >= 540]
    topos = [b15[i][2] for i in antes if all(b15[k][2] < b15[i][2] for k in range(i + 1, iB))]
    fundos = [b15[i][3] for i in antes if all(b15[k][3] > b15[i][3] for k in range(i + 1, iB))]
    barraB = [b for b in bs if 600 <= m(b) < 615]
    # C2: sweep dentro da barra das 10
    if topos:
        t = next((m(b) for b in barraB if b[2] > min(topos)), None)
        if t is not None:
            out.append(("C2", -1, t, B[4] < min(topos)))
    if fundos:
        t = next((m(b) for b in barraB if b[3] < max(fundos)), None)
        if t is not None:
            out.append(("C2", 1, t, B[4] > max(fundos)))
    # C1: sweep da barra das 10 entre 10:15 e 11:14
    depois = [b for b in bs if 615 <= m(b) < 675]
    for lado in (-1, 1):
        i = next((k for k, b in enumerate(depois)
                  if (b[2] > B[2] if lado < 0 else b[3] < B[3])), None)
        if i is None:
            continue
        t = m(depois[i])
        barra15 = next(x for x in b15 if m(x) <= t < m(x) + 15)
        volta = (barra15[4] < B[2]) if lado < 0 else (barra15[4] > B[3])
        out.append(("C1", lado, t, volta))
    return out


def linha(rot, x, meio):
    n = len(x)
    if n < 2:
        print(f"  {rot:<40} n={n:3d}")
        return
    rs = [t["r"] for t in x]
    mu = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5
    a = [t["r"] for t in x if t["data"] <= meio]
    b = [t["r"] for t in x if t["data"] > meio]
    f5 = sum(t["mfe"] >= 5 for t in x) / n
    print(f"  {rot:<40} n={n:3d}  media {mu:+.2f}R (t={mu / se if se else 0:+.1f})  metades "
          f"{st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}  5R {f5:4.0%}  "
          f"R$ {sum(t['pts'] for t in x) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))


def main():
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
        gs = hl.gatilhos_do_dia(bs, ant)
        for x in gs:
            if 600 <= m((x["t_mss"],)) < 675 and m((x["t_ent"],)) < 690:
                g["base"].append(dict(x, data=d))
        tend = c2b.tendencia(b15)
        for modo, lado, t_sw, volta in sweeps(bs, b15):
            c = [x for x in gs if x["lado"] == lado and t_sw < m((x["t_mss"],)) <= t_sw + 30
                 and m((x["t_mss"],)) < 675 and m((x["t_ent"],)) < 690]
            if not c:
                g[(modo, "sem gatilho")].append(None)
                continue
            x = dict(c[0], data=d)
            ctx = "lateral" if tend == 0 else "continuacao" if tend == lado else "contra"
            for chave in (modo, (modo, "volta" if volta else "nao volta"), (modo, ctx)):
                g[chave].append(x)
    print("Setup C ao vivo: sweep -> gatilho de reversao no 1 min, sem esperar o 15 min fechar.\n")
    linha("BASE: todos os gatilhos 10:00-11:14", g["base"], meio)
    for modo in ("C1", "C2"):
        print()
        linha(f"{modo} (sweep + gatilho de reversao)", g[modo], meio)
        print(f"    sweeps sem gatilho em 30 min: {len(g[(modo, 'sem gatilho')])}")
        linha(f"  {modo} - 15 min fechou de volta", g[(modo, "volta")], meio)
        linha(f"  {modo} - 15 min NAO fechou de volta", g[(modo, "nao volta")], meio)
        for ctx in ("continuacao", "contra", "lateral"):
            linha(f"  {modo} - {ctx}", g[(modo, ctx)], meio)


if __name__ == "__main__":
    main()
