"""Setup C ao vivo com BLOCO DE ORDEM alem do FVG (pedido do operador, 25/09/2026).

Mesmo gatilho de hierarquia_liquidez.gatilhos_do_dia (MSS + pernada com candle >= 1,5x a
media, stop no extremo da pernada + 1 tick, entrada ate 30 min depois do MSS, gestao
BSL/SSL + trailing), mudando so ONDE se entra:
  FVG        : borda do FVG da pernada (o atual).
  OB         : bloco de ordem = ultimo candle contrario antes da pernada (na venda, o
               ultimo candle de alta entre o swing rompido e o topo da pernada); entrada
               na abertura dele (inicio do corpo). Nao exige FVG.
  FVG ou OB  : FVG quando existe; sem FVG, o OB. (Mais gatilhos: MSS sem FVG passa a valer.)
Setup C como em backtest_c_ao_vivo: sweep -> primeiro gatilho de reversao em ate 30 min.
"""

import statistics as st
from collections import defaultdict

import backtest_c_ao_vivo as av
import backtest_c2b as c2b
import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

sv = hl.sv
H = bq.hm


def bloco(bs, i_ref, i_org, alta):
    """Ultimo candle contrario a pernada, do extremo para tras ate o swing rompido."""
    for k in range(i_org, i_ref - 1, -1):
        b = bs[k]
        if (b[4] < b[1]) if alta else (b[4] > b[1]):
            return b[1]
    return None


def gatilhos(bs, modo):
    out = []
    vistos = set()
    i_ini, i_fim = sv.idx(bs, H("09:05")), sv.idx(bs, H("12:00"))
    for m in range(i_ini, i_fim):
        topos, fundos = sv.fractais(bs[:m], 2)
        for alta in (True, False):
            refs = topos if alta else fundos
            if not refs:
                continue
            i_ref = refs[-1]
            nivel = bs[i_ref][2] if alta else bs[i_ref][3]
            if not ((bs[m][4] > nivel) if alta else (bs[m][4] < nivel)):
                continue
            trecho = bs[i_ref:m + 1]
            if alta:
                i_org = i_ref + min(range(len(trecho)), key=lambda k: trecho[k][3])
                extremo = bs[i_org][3]
            else:
                i_org = i_ref + max(range(len(trecho)), key=lambda k: trecho[k][2])
                extremo = bs[i_org][2]
            if (i_org, alta) in vistos:
                continue
            base = bs[max(0, i_org - 15):i_org]
            if len(base) < 5:
                continue
            media = st.mean(hl.corpo(b) for b in base) or 1
            if max(hl.corpo(b) for b in bs[i_org:m + 1]) < 1.5 * media:
                continue
            gaps = sv.fvgs(bs, i_org + 1, m + 1, alta=alta)
            ob = bloco(bs, i_ref, i_org, alta)
            stop = extremo - sv.TICK if alta else extremo + sv.TICK
            if modo == "FVG" or (modo == "FVG ou OB" and gaps):
                if not gaps:
                    continue
                g_i, g_lo, g_hi = gaps[-1]
                borda, desde = (g_hi if alta else g_lo), g_i + 1
            else:
                if ob is None:
                    continue
                borda, desde = ob, m + 1
            if (borda <= stop) if alta else (borda >= stop):
                continue
            vistos.add((i_org, alta))
            lado = 1 if alta else -1
            lim = sv.idx(bs, hl.mais(bs[m][0], 30))
            for f in range(desde, min(lim, len(bs))):
                x = bs[f]
                if (x[3] <= stop) if alta else (x[2] >= stop):
                    break
                if (x[3] <= borda) if alta else (x[2] >= borda):
                    alvo = sv.alvo_liquidez(bs, f, lado, borda)
                    pts, _, _ = sv.gerir(bs, f, lado, borda, stop, alvo)
                    out.append(dict(lado=lado, mfe=hl.mfe_em_r(bs, f, lado, borda, stop), pts=pts,
                                    r=pts / abs(borda - stop), risco=abs(borda - stop),
                                    t_mss=bs[m][0], t_ent=x[0]))
                    break
    return out


def main():
    dias1 = bq.carregar()
    o = sorted(dias1)
    meio = o[len(o) // 2]
    g = defaultdict(list)
    m = av.m
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias1[d], H("09:00"), H("17:51"))
        if len(bs) < 300:
            continue
        b15 = p.agrega15(bs)
        sw = av.sweeps(bs, b15)
        tend = c2b.tendencia(b15)
        for modo in ("FVG", "OB", "FVG ou OB"):
            gs = gatilhos(bs, modo)
            for x in gs:
                if 600 <= m((x["t_mss"],)) < 675 and m((x["t_ent"],)) < 690:
                    g[(modo, "base")].append(dict(x, data=d))
            for setup, lado, t_sw, _ in sw:
                c = [x for x in gs if x["lado"] == lado and t_sw < m((x["t_mss"],)) <= t_sw + 30
                     and m((x["t_mss"],)) < 675 and m((x["t_ent"],)) < 690]
                if c:
                    ctx = "lateral" if tend == 0 else "continuacao" if tend == lado else "reversao"
                    g[(modo, setup)].append(dict(c[0], data=d))
                    g[(modo, setup, ctx)].append(dict(c[0], data=d))
    print("Setup C ao vivo, 5 meses de 1 min: FVG x bloco de ordem x os dois.\n")
    for modo in ("FVG", "OB", "FVG ou OB"):
        print(f"{modo}:")
        av.linha("base: todo gatilho 10:00-11:14", g[(modo, "base")], meio)
        for setup in ("C1", "C2"):
            av.linha(setup, g[(modo, setup)], meio)
            x = g[(modo, setup)]
            if x:
                print(f"      stop mediano {st.median(t['risco'] for t in x):.0f} pts")
        print()


if __name__ == "__main__":
    main()
