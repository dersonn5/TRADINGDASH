"""A pernada do dia: o movimento grande que o indice entrega entre 09:00 e 12:00.
WIN, 1 min. Descritivo.

Observacao do operador (22/09/2026): "todo dia tem um movimento bom que estica no
indice, e em sua maioria tem uma manipulacao antes da entrega". Exemplo: entrada
depois de AMD, MSS + OB, stop de 185 pts, preco andou 1.226 pts (~6,6R).

Definicoes:
  Pernada do dia = a maior distancia entre um extremo e o extremo oposto POSTERIOR,
                   dentro de 09:00-11:59 (fundo -> topo para alta, topo -> fundo para
                   baixa). Origem = o candle do extremo onde ela comeca.
  Manipulacao antes da origem = o candle de origem furou, pela primeira vez, um nivel
                   que estava intacto ate 30 min antes: swing de 1 min (fractal 3) do
                   dia, maxima/minima da 1a hora, ou do pregao anterior.
                   Tambem conta "origem = novo extremo do dia" (varreu todos os
                   extremos anteriores do lado dela).
  Gatilho da pernada = um MSS + FVG do hierarquia_liquidez cujo MSS acontece ate 30 min
                   depois da origem, no sentido da pernada, com stop no extremo que
                   fica ate 2 candles da origem.
  Gatilhos anteriores = gatilhos do mesmo dia com MSS antes do gatilho da pernada, e
                   quantos deles pararam antes de 1R (o "erro 2-3x antes de acertar").
"""

import statistics as st
from collections import Counter

import backtest_quarters as bq
import hierarquia_liquidez as hl
import setup_vista as sv
from ny_1030 import mais

H = bq.hm


def pernada(bs):
    """(lado, i_origem, i_fim, tamanho) da maior pernada em bs."""
    melhor = (None, 0, 0, 0.0)
    i_min = i_max = 0
    for j, b in enumerate(bs):
        if b[3] < bs[i_min][3]:
            i_min = j
        if b[2] > bs[i_max][2]:
            i_max = j
        alta = b[2] - bs[i_min][3]
        baixa = bs[i_max][2] - b[3]
        if alta > melhor[3]:
            melhor = (1, i_min, j, alta)
        if baixa > melhor[3]:
            melhor = (-1, i_max, j, baixa)
    return melhor


def manipulou(bs, i_org, lado, anterior):
    ws = max(0, i_org - 30)
    org = bs[i_org]
    alta = lado == 1
    fura = (lambda n: org[3] < n) if alta else (lambda n: org[2] > n)
    furou_antes = (lambda n, seg: min((b[3] for b in seg), default=1e12) < n) if alta else \
                  (lambda n, seg: max((b[2] for b in seg), default=-1) > n)
    motivos = []
    if i_org > 0:
        ext_antes = min(b[3] for b in bs[:i_org]) if alta else max(b[2] for b in bs[:i_org])
        if fura(ext_antes):
            motivos.append("novo extremo do dia")
    if anterior:
        n = min(b[3] for b in anterior) if alta else max(b[2] for b in anterior)
        if fura(n) and not furou_antes(n, bs[:ws]):
            motivos.append("dia anterior")
    i10 = sv.idx(bs, H("10:00"))
    if i_org >= i10 and i10 > 0:
        n = min(b[3] for b in bs[:i10]) if alta else max(b[2] for b in bs[:i10])
        if fura(n) and not furou_antes(n, bs[i10:max(ws, i10)]):
            motivos.append("1a hora")
    t1, f1 = sv.fractais(bs[:ws], 3)
    for i in (f1 if alta else t1):
        n = bs[i][3] if alta else bs[i][2]
        if fura(n) and not furou_antes(n, bs[i + 1:ws]):
            motivos.append("swing 1 min")
            break
    return motivos


def main():
    dias = bq.carregar()
    ordem = sorted(dias)
    linhas = []
    for k, d in enumerate(ordem):
        if k == 0:
            continue
        cheio = bq.entre(dias[d], H("09:00"), H("17:51"))
        if len(cheio) < 300:
            continue
        janela = bq.entre(cheio, H("09:00"), H("12:00"))
        ant = bq.entre(dias[ordem[k - 1]], H("09:00"), H("18:00"))
        lado, i_org, i_fim, tam = pernada(janela)
        if lado is None:
            continue
        mot = manipulou(cheio, i_org, lado, ant)
        gats = hl.gatilhos_do_dia(cheio, ant)
        t_org = janela[i_org][0]
        alvo_g = None
        for g in gats:
            if g["lado"] == lado and t_org <= g["t_mss"] <= mais(t_org, 30):
                alvo_g = g
                break
        anteriores = [g for g in gats if alvo_g and g["t_mss"] < alvo_g["t_mss"]]
        linhas.append(dict(data=d, lado=lado, tam=tam, t_org=t_org, t_fim=janela[i_fim][0],
                           manip=mot, gat=alvo_g, n_ant=len(anteriores),
                           falhos=sum(1 for g in anteriores if g["mfe"] < 1)))

    n = len(linhas)
    tams = sorted(l["tam"] for l in linhas)
    print(f"WIN 1 min, {n} pregoes, janela 09:00-12:00\n")
    print("1) TAMANHO da pernada do dia (pts):")
    print(f"   mediana {tams[n // 2]:.0f} | p25 {tams[n // 4]:.0f} | p75 {tams[3 * n // 4]:.0f}"
          f" | >= 800 em {sum(t >= 800 for t in tams) / n:.0%} | >= 1000 em {sum(t >= 1000 for t in tams) / n:.0%}")

    print("\n2) QUANDO a pernada comeca (horario da origem):")
    faixas = Counter()
    for l in linhas:
        m = l["t_org"].hour * 60 + l["t_org"].minute
        faixas[(m - 540) // 15] += 1
    for f in range(12):
        a = 540 + 15 * f
        barra = "#" * faixas[f]
        print(f"   {a // 60:02d}:{a % 60:02d}-{(a + 15) // 60:02d}:{(a + 15) % 60:02d}  {faixas[f] / n:4.0%} {barra}")

    print("\n3) MANIPULACAO antes da origem:")
    com = sum(1 for l in linhas if l["manip"])
    print(f"   com manipulacao: {com / n:.0%}")
    c = Counter(m for l in linhas for m in l["manip"])
    for k2, v in c.most_common():
        print(f"     {k2:<20} {v / n:4.0%}")

    print("\n4) GATILHO (MSS + FVG) no comeco da pernada, ate 30 min da origem:")
    com_g = [l for l in linhas if l["gat"]]
    print(f"   existia em {len(com_g) / n:.0%} dos dias")
    if com_g:
        rs = sorted(l["gat"]["risco"] for l in com_g)
        mf = sorted(l["gat"]["mfe"] for l in com_g)
        m2 = len(com_g)
        print(f"   stop mediano {rs[m2 // 2]:.0f} pts | MFE mediano {mf[m2 // 2]:.1f}R | "
              f"chegou a 5R {sum(x >= 5 for x in mf) / m2:.0%} | 8R {sum(x >= 8 for x in mf) / m2:.0%}")

        print("\n5) GATILHOS ANTES do gatilho da pernada, no mesmo dia:")
        na = sorted(l["n_ant"] for l in com_g)
        print(f"   mediana {na[m2 // 2]} | 0 antes em {sum(x == 0 for x in na) / m2:.0%} | "
              f"1-2 em {sum(1 <= x <= 2 for x in na) / m2:.0%} | 3+ em {sum(x >= 3 for x in na) / m2:.0%}")
        fa = sorted(l["falhos"] for l in com_g)
        print(f"   desses, pararam antes de 1R: mediana {fa[m2 // 2]}")

    print("\n   ultimos 8 dias:")
    for l in linhas[-8:]:
        g = l["gat"]
        gs = f"gatilho {g['t_mss'].strftime('%H:%M')} stop {g['risco']:.0f} MFE {g['mfe']:.1f}R" if g else "sem gatilho"
        print(f"   {l['data']} {'alta ' if l['lado'] > 0 else 'baixa'} {l['tam']:5.0f} pts  "
              f"{l['t_org'].strftime('%H:%M')}->{l['t_fim'].strftime('%H:%M')}  "
              f"manip: {', '.join(l['manip']) or '-':<32} {gs}  (antes: {l['n_ant']})")


if __name__ == "__main__":
    main()
