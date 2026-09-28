"""Gap para fechar depois do V: fecha o gap ou volta ao fundo primeiro? (28/09/2026)

Pergunta do operador: "mesmo tendo um gap do dia pra fechar, a maior probabilidade e voltar
tudo ate o fundo?"

Dias em que o gap das 09:00 e o movimento inicial de 800 pts (padrao_v_0900.py) vao para o
mesmo lado (abriu em baixa e caiu mais, ou o inverso). Rolagem de vencimento fora (gap > 1,2%).
Ponto de partida: o minuto em que o preco ja percorreu uma fracao (75% ou 85%) do caminho
entre o extremo do movimento e o fechamento do dia anterior, sem ter fechado o gap.
Dali em diante, o que acontece primeiro: o gap fecha ou o preco volta ao extremo.
Base: 1 min (abr-set/2026) e 15 min (2021-2026, movimento em % = 0,43% da abertura).
"""

import datetime as dt
from collections import Counter

import backtest_quarters as bq
from padrao_15m import carregar15


def medir(bs, prev, mov, frac, fim):
    manha = [b for b in bs if b[0] < dt.time(12, 0)]
    if not manha or manha[0][0] > dt.time(9, 5) or not prev:
        return None
    o09, pc = manha[0][1], prev[-1][4]
    gap = o09 - pc
    if gap == 0 or abs(gap) / pc > 0.012:
        return None
    lado = i0 = None
    for i, b in enumerate(manha):
        sobe, cai = b[2] - o09 >= mov, o09 - b[3] >= mov
        if sobe and cai:
            return None
        if sobe or cai:
            lado, i0 = (1 if sobe else -1), i
            break
    if lado is None or (gap > 0) != (lado == 1):
        return None
    ext = manha[i0][2] if lado == 1 else manha[i0][3]
    for k in range(i0 + 1, len(manha)):
        b = manha[k]
        if (b[3] <= pc) if lado == 1 else (b[2] >= pc):
            return None  # fechou o gap antes de passar pelo ponto de partida
        nivel = ext - frac * (ext - pc) if lado == 1 else ext + frac * (pc - ext)
        if (b[3] <= nivel) if lado == 1 else (b[2] >= nivel):
            for x in (x for x in bs if b[0] < x[0] < fim):
                if (x[3] <= pc) if lado == 1 else (x[2] >= pc):
                    return "gap fecha primeiro"
                if (x[2] >= ext) if lado == 1 else (x[3] <= ext):
                    return "volta ao fundo primeiro"
            return "nenhum"
        novo = b[2] if lado == 1 else b[3]
        if (novo > ext) if lado == 1 else (novo < ext):
            ext = novo
    return None


def main():
    for nome, dias, mov in (("1 min 2026", bq.carregar(), lambda o: 800), ("15 min 2021-26", carregar15(), lambda o: o * 0.0043)):
        ks = sorted(dias)
        for frac in (0.75, 0.85):
            for fim, rot in ((dt.time(12, 0), "ate 12:00"), (dt.time(18, 0), "ate o fechamento")):
                c = Counter(r for i, d in enumerate(ks)
                            for r in [medir(dias[d], dias[ks[i - 1]] if i else None, mov(dias[d][0][1]), frac, fim)] if r)
                n = sum(c.values())
                print(f"{nome:<15} ja percorreu {frac:.0%} do caminho fundo->gap, {rot:<17} n={n:3d}  "
                      + " | ".join(f"{k} {v / n:.0%}" for k, v in sorted(c.items(), key=lambda z: -z[1])))


if __name__ == "__main__":
    main()
