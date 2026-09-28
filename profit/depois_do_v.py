"""Depois que o V das 09:00 se completa, o que acontece ate 12:00? (28/09/2026)

Pergunta do operador (grafico de 28/09: abriu em gap de baixa, caiu, reverteu em V forte
para cima e fez um candle grande de baixa no topo): "a probabilidade e de dar seguimento
a essa reversao?"

Mesmo V do padrao_v_0900.py (movimento de 800 pts da abertura das 09:00, volta de 75%).
A partir do minuto em que o V se completa, ate 12:00, mede:
  SEGUE     = o preco passa da abertura das 09:00, do outro lado, pelo menos o tamanho do
              movimento (o V vira um espelho inteiro).
  DEVOLVE   = o preco volta ao extremo do movimento (o V falha por completo).
  PASSA_AB  = o preco passa da abertura das 09:00 (so isso).
E, nos dias em que o movimento abriu em gap contra o dia anterior, se o gap fecha ate 12:00.
Base: 1 min (abr-set/2026) e 15 min (2021-2026, com o movimento em % = 0,43% da abertura).
"""

import datetime as dt
from collections import defaultdict

import backtest_quarters as bq
from padrao_15m import carregar15

FIM = dt.time(12, 0)


def medir(bs, prev, mov):
    manha = [b for b in bs if b[0] < FIM]
    if not manha or manha[0][0] > dt.time(9, 5):
        return None
    o09 = manha[0][1]
    lado = i0 = None
    for i, b in enumerate(manha):
        sobe, cai = b[2] - o09 >= mov, o09 - b[3] >= mov
        if sobe and cai:
            return None
        if sobe or cai:
            lado, i0 = (1 if sobe else -1), i
            break
    if lado is None:
        return None
    ext = manha[i0][2] if lado == 1 else manha[i0][3]
    i_v = None
    for k in range(i0 + 1, len(manha)):
        b = manha[k]
        alvo = ext - 0.75 * (ext - o09) if lado == 1 else ext + 0.75 * (o09 - ext)
        if (b[3] <= alvo) if lado == 1 else (b[2] >= alvo):
            i_v = k
            break
        novo = b[2] if lado == 1 else b[3]
        if (novo > ext) if lado == 1 else (novo < ext):
            ext = novo
    if i_v is None:
        return None
    tam = abs(ext - o09)
    depois = manha[i_v + 1:]
    if not depois:
        return None
    # lado da reversao = -lado
    if lado == 1:
        segue = any(b[3] <= o09 - tam for b in depois)
        devolve = any(b[2] >= ext for b in depois)
        passa = any(b[3] < o09 for b in manha[i_v:])
    else:
        segue = any(b[2] >= o09 + tam for b in depois)
        devolve = any(b[3] <= ext for b in depois)
        passa = any(b[2] > o09 for b in manha[i_v:])
    r = dict(lado=lado, segue=segue, devolve=devolve, passa=passa, t_v=manha[i_v][0])
    if prev:
        pc = prev[-1][4]
        gap = o09 - pc
        # gap no mesmo sentido do movimento (abriu em baixa e caiu mais): o V vai na direcao de fechar o gap
        if abs(gap) / pc < 0.012 and gap != 0 and (gap > 0) == (lado == 1):
            r["gap_fecha"] = any((b[3] <= pc) if lado == 1 else (b[2] >= pc) for b in manha[i_v:])
    return r


def resumo(nome, rs):
    n = len(rs)
    if not n:
        return
    f = lambda k, g=rs: f"{sum(r[k] for r in g) / len(g):4.0%}"
    gs = [r for r in rs if "gap_fecha" in r]
    print(f"  {nome:<34} V completos n={n:4d} | passa da abertura {f('passa')} | SEGUE (espelho inteiro) {f('segue')} "
          f"| DEVOLVE ate o extremo {f('devolve')}" + (f" | gap fecha ate 12:00 {f('gap_fecha', gs)} (n={len(gs)})" if gs else ""))


def main():
    d1 = bq.carregar()
    ks = sorted(d1)
    rs = [r for i, d in enumerate(ks) for r in [medir(d1[d], d1[ks[i - 1]] if i else None, 800)] if r]
    print("Depois que o V das 09:00 se completa (volta de 75%), ate 12:00\n")
    resumo("1 min, abr-set/2026", rs)
    resumo("  comecou em baixa (V para cima)", [r for r in rs if r["lado"] == -1])
    resumo("  V completo antes das 10:00", [r for r in rs if r["t_v"] < dt.time(10, 0)])
    resumo("  V completo 10:00 ou depois", [r for r in rs if r["t_v"] >= dt.time(10, 0)])

    d15 = carregar15()
    ks = sorted(d15)
    anos = defaultdict(list)
    for i, d in enumerate(ks):
        r = medir(d15[d], d15[ks[i - 1]] if i else None, d15[d][0][1] * 0.0043)
        if r:
            anos[d.year].append(r)
    print()
    resumo("15 min, 2021-2026 (todos)", [r for g in anos.values() for r in g])
    for a, g in sorted(anos.items()):
        resumo(f"  {a}", g)


if __name__ == "__main__":
    main()
