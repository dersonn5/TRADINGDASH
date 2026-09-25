"""C2 corrigido pelo operador (25/09/2026):
  a barra das 10 (B) VARRE o topo/fundo de uma barra de 15 min anterior (intacto ate 10:00);
  a barra SEGUINTE (10:15) FECHA DE VOLTA PARA DENTRO de B - nao precisa romper B.
  Varreu topo -> venda; varreu fundo -> compra.

"Fechar para dentro" em tres versoes (todas mostradas, para escolher pela logica):
  V1: 10:15 fecha contra B (de baixa apos varrer topo) e dentro do range de B.
  V2: 10:15 fecha alem do MEIO de B (abaixo do meio, apos varrer topo).
  V3: 10:15 fecha alem da ABERTURA de B (devolve o corpo inteiro).
Controle de cada versao: a mesma barra das 10:15, sem B ter varrido nada antes.

Parte 1 - 5 anos, 15 min: entrada no fechamento das 10:15; stop na maxima (minima) da
  barra que varreu (B) ou da 10:15, o que for mais longe, + 1 tick; mede kR ate 12:00.
Parte 2 - 5 meses, 1 min: gatilho MSS + FVG no sentido, MSS entre 10:15 e 11:14,
  gestao BSL/SSL + trailing.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

TICK = 5
H = bq.hm


def casos(b15):
    idx = {p.minutos(b[0]): i for i, b in enumerate(b15)}
    if 600 not in idx or 615 not in idx:
        return []
    iB = idx[600]
    B, N = b15[iB], b15[idx[615]]
    antes = [i for i in range(iB) if p.minutos(b15[i][0]) >= 540]
    topos = [b15[i][2] for i in antes if all(b15[k][2] < b15[i][2] for k in range(i + 1, iB))]
    fundos = [b15[i][3] for i in antes if all(b15[k][3] > b15[i][3] for k in range(i + 1, iB))]
    vt = any(B[2] > t for t in topos)
    vf = any(B[3] < f for f in fundos)
    meio = (B[2] + B[3]) / 2
    out = []
    for lado, varreu in ((-1, vt), (1, vf)):
        if lado < 0:
            v1 = N[4] < N[1] and N[4] < B[2]
            v2 = N[4] < meio
            v3 = N[4] < B[1]
        else:
            v1 = N[4] > N[1] and N[4] > B[3]
            v2 = N[4] > meio
            v3 = N[4] > B[1]
        if vt and vf:
            varreu = False  # varreu os dois lados: ambiguo, conta como controle
        for nome, ok in (("V1", v1), ("V2", v2), ("V3", v3)):
            if ok:
                out.append((nome, "C2" if varreu else "controle", lado, idx[615]))
    return out


def mfe15(b15, iN, lado):
    iB = iN - 1
    ent = b15[iN][4]
    ext = max(b15[iB][2], b15[iN][2]) if lado < 0 else min(b15[iB][3], b15[iN][3])
    stop = ext + TICK if lado < 0 else ext - TICK
    R = abs(ent - stop)
    if R <= 0:
        return None
    melhor = 0.0
    for y in b15[iN + 1:]:
        if p.minutos(y[0]) >= 720:
            break
        if (y[2] >= stop) if lado < 0 else (y[3] <= stop):
            return melhor
        melhor = max(melhor, ((ent - y[3]) if lado < 0 else (y[2] - ent)) / R)
    return melhor


def main():
    dias = p.carregar15()
    r = defaultdict(list)
    anos = defaultdict(list)
    for d, b15 in sorted(dias.items()):
        for v, grupo, lado, iN in casos(b15):
            m = mfe15(b15, iN, lado)
            if m is not None:
                r[(v, grupo)].append(m)
                anos[(v, grupo, d.year)].append(m)
    print("PARTE 1 - 5 anos de 15 min. Entrada no fechamento das 10:15, stop no extremo da varrida.")
    print("Chance de chegar a kR antes do stop, ate 12:00.\n")
    for v in ("V1", "V2", "V3"):
        for g in ("C2", "controle"):
            x = r[(v, g)]
            n = len(x)
            f = lambda k: sum(m >= k for m in x) / n
            print(f"  {v} {g:<9} n={n:4d}  1R {f(1):4.0%}  2R {f(2):4.0%}  3R {f(3):4.0%}")
        melhor_anos = sum(
            1 for a in range(2021, 2027)
            if anos[(v, "C2", a)] and anos[(v, "controle", a)]
            and sum(m >= 2 for m in anos[(v, "C2", a)]) / len(anos[(v, "C2", a)])
            > sum(m >= 2 for m in anos[(v, "controle", a)]) / len(anos[(v, "controle", a)]))
        print(f"     -> C2 melhor que o controle (2R) em {melhor_anos} de 6 anos\n")

    dias1 = bq.carregar()
    o = sorted(dias1)
    meio = o[len(o) // 2]
    g2 = defaultdict(list)
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias1[d], H("09:00"), H("17:51"))
        ant = bq.entre(dias1[o[kd - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        cs = casos(p.agrega15(bs))
        if not cs:
            continue
        gs = hl.gatilhos_do_dia(bs, ant)
        for v, grupo, lado, iN in cs:
            c = [g for g in gs if g["lado"] == lado and 615 <= p.minutos(g["t_mss"]) < 675]
            if c:
                x = dict(c[0])
                x["data"] = d
                g2[(v, grupo)].append(x)
    print("PARTE 2 - 5 meses de 1 min, gatilho do operador + gestao:\n")
    for v in ("V1", "V2", "V3"):
        for g in ("C2", "controle"):
            x = g2[(v, g)]
            n = len(x)
            if n < 2:
                print(f"  {v} {g:<9} n={n}")
                continue
            rs = [t["r"] for t in x]
            m = st.mean(rs)
            se = st.pstdev(rs) / n ** 0.5
            a = [t["r"] for t in x if t["data"] <= meio]
            b = [t["r"] for t in x if t["data"] > meio]
            print(f"  {v} {g:<9} n={n:3d}  media {m:+.2f}R (t={m / se:+.1f})  metades "
                  f"{st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}  "
                  f"R$ {sum(t['pts'] for t in x) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))
        print()


if __name__ == "__main__":
    main()
