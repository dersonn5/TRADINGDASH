"""Fase 1 do Estudo_Reversao_Abertura_Vista: a 2a hora reverte a 1a hora?
WIN, grafico de 1 min, cache do Profit.

Definicoes (plano aprovado em 22/09/2026):
  Hora A        = 60 min a partir de um horario (09:00 e controles).
  Hora B        = os 60 min seguintes (10:00-10:59 no caso principal).
  Direcao de A  = fechamento do ultimo candle de A - abertura do primeiro.
  B reverte A:
    RETRACAO 50%   = B devolve pelo menos metade do movimento de A.
    CRUZA ABERTURA = B passa da abertura de A (devolve o movimento todo).
    ROMPE OPOSTO   = B rompe o extremo oposto de A (maxima se A caiu, minima se subiu).
    FECHA CONTRA   = B fecha no sentido contrario ao de A.
  Controle: pares 11->12, 13->14, 14->15, 15->16. A pergunta e se 09->10 reverte
  MAIS do que o resto do dia.
"""

from collections import defaultdict

import backtest_quarters as bq
from ny_1030 import mais


def par(bs, ini):
    a = bq.entre(bs, ini, mais(ini, 60))
    b = bq.entre(bs, mais(ini, 60), mais(ini, 120))
    if len(a) < 55 or len(b) < 55:
        return None
    oa, ca = a[0][1], a[-1][4]
    mov = ca - oa
    if mov == 0:
        return None
    up = mov > 0
    hi_a, lo_a = max(x[2] for x in a), min(x[3] for x in a)
    hi_b, lo_b = max(x[2] for x in b), min(x[3] for x in b)
    cb = b[-1][4]
    if up:
        ret50 = lo_b <= ca - abs(mov) / 2
        cruza = lo_b < oa
        rompe = lo_b < lo_a
        contra = cb < b[0][1]
    else:
        ret50 = hi_b >= ca + abs(mov) / 2
        cruza = hi_b > oa
        rompe = hi_b > hi_a
        contra = cb > b[0][1]
    return dict(up=up, mov=abs(mov), ret50=ret50, cruza=cruza, rompe=rompe, contra=contra)


def main():
    dias = bq.carregar()
    print(f"WIN 1 min: {len(dias)} pregoes, {min(dias)} a {max(dias)}\n")
    print(f"{'par':<13} {'dias':>4}  {'retr.50%':>8} {'cruza abert.':>12} {'rompe oposto':>12} {'fecha contra':>12}")
    for ini in ("09:00", "11:00", "13:00", "14:00", "15:00"):
        rs = [r for r in (par(bs, bq.hm(ini)) for bs in dias.values()) if r]
        n = len(rs)
        f = lambda k: sum(r[k] for r in rs) / n
        rot = f"{ini[:2]}h -> {int(ini[:2]) + 1:02d}h"
        print(f"{rot:<13} {n:4d}  {f('ret50'):8.0%} {f('cruza'):12.0%} {f('rompe'):12.0%} {f('contra'):12.0%}")

    # Por tamanho do movimento da 1a hora (tercis), so 09->10.
    rs = {d: r for d, bs in sorted(dias.items()) for r in [par(bs, bq.hm("09:00"))] if r}
    tam = sorted(r["mov"] for r in rs.values())
    c1, c2 = tam[len(tam) // 3], tam[2 * len(tam) // 3]
    print(f"\n09h -> 10h por tamanho da 1a hora (tercis: <{c1:.0f} | {c1:.0f}-{c2:.0f} | >{c2:.0f} pts)")
    for nome, filtro in (("pequena", lambda m: m < c1), ("media", lambda m: c1 <= m <= c2), ("grande", lambda m: m > c2)):
        g = [r for r in rs.values() if filtro(r["mov"])]
        f = lambda k: sum(r[k] for r in g) / len(g)
        print(f"  {nome:<8} n={len(g):3d}  retr.50% {f('ret50'):4.0%}  cruza {f('cruza'):4.0%}  "
              f"rompe {f('rompe'):4.0%}  fecha contra {f('contra'):4.0%}")

    print("\nDatas 09h->10h (para conferir no Profit):")
    por = defaultdict(list)
    for d, r in rs.items():
        chave = "rompe oposto" if r["rompe"] else ("cruza abertura" if r["cruza"] else
                ("retrai 50%" if r["ret50"] else "continua"))
        por[chave].append(d)
    for k in ("rompe oposto", "cruza abertura", "retrai 50%", "continua"):
        print(f"  {k:<15} {len(por[k]):3d}  ultimas: {', '.join(str(x) for x in por[k][-6:])}")


if __name__ == "__main__":
    main()
