"""Fase 3 do Estudo_Reversao_Abertura_Vista: anatomia do impulso das 10:00.
WIN, 1 min, cache do Profit. Descritivo: nenhuma regra de entrada aqui.

Definicoes (mesmas da Fase 1):
  o10      = abertura do candle das 10:00.
  Impulso  = direcao de 10:00-10:04 (fechamento 10:04 - o10).
  Range15  = maxima/minima de 10:00-10:14.
  REVERTEU = entre 10:15 e 10:59 rompe o lado OPOSTO do Range15.
  Extremo do impulso = ponto mais longe na direcao do impulso, de 10:00 ate o
             rompimento (se reverteu) ou ate 10:59 (se nao reverteu).
  Contexto = o impulso das 10:00 vai A FAVOR ou CONTRA a direcao da 1a hora
             (fechamento 09:59 - abertura 09:00).

Medidas:
  tamanho do impulso        = extremo - o10                (base do stop)
  horario do extremo        = minutos depois das 10:00     (janela de entrada)
  avanco apos 10:05         = extremo - fechamento 10:04   (quanto anda contra quem
                                                            fade aos 10:05)
  alcance da reversao       = do extremo ate o ponto mais longe do outro lado,
                              ate 11:29                    (base do alvo)
  alvos atingidos apos o extremo, ate 11:29: abertura 09:00, 50% da 1a hora,
                              extremo oposto da 1a hora.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
from ny_1030 import mais


def medir(bs):
    h1 = bq.entre(bs, bq.hm("09:00"), bq.hm("10:00"))
    x = bq.entre(bs, bq.hm("10:00"), bq.hm("11:30"))
    if len(h1) < 55 or len(x) < 85:
        return None
    o10 = x[0][1]
    imp = x[4][4] - o10
    if imp == 0:
        return None
    up = imp > 0
    hi15, lo15 = max(b[2] for b in x[:15]), min(b[3] for b in x[:15])
    i_rev = None
    for i in range(15, 60):
        if (x[i][3] < lo15) if up else (x[i][2] > hi15):
            i_rev = i
            break
    fim = i_rev if i_rev is not None else 60
    seg = x[:fim + 1]
    if up:
        i_ext = max(range(len(seg)), key=lambda i: seg[i][2])
        ext = seg[i_ext][2]
    else:
        i_ext = min(range(len(seg)), key=lambda i: seg[i][3])
        ext = seg[i_ext][3]
    tam = abs(ext - o10)
    avanco = abs(ext - x[4][4])
    depois = x[i_ext:]
    if up:
        alcance = ext - min(b[3] for b in depois)
    else:
        alcance = max(b[2] for b in depois) - ext

    o09, c09 = h1[0][1], h1[-1][4]
    hi1, lo1 = max(b[2] for b in h1), min(b[3] for b in h1)
    mov1 = c09 - o09
    meio1 = (hi1 + lo1) / 2
    if up:
        ating = dict(ab09=any(b[3] <= o09 for b in depois) if o09 < ext else False,
                     meio=any(b[3] <= meio1 for b in depois) if meio1 < ext else False,
                     oposto=any(b[3] <= lo1 for b in depois))
    else:
        ating = dict(ab09=any(b[2] >= o09 for b in depois) if o09 > ext else False,
                     meio=any(b[2] >= meio1 for b in depois) if meio1 > ext else False,
                     oposto=any(b[2] >= hi1 for b in depois))
    ctx = "neutro" if mov1 == 0 else ("a favor" if (mov1 > 0) == up else "contra")
    varreu = (ext > hi1) if up else (ext < lo1)
    return dict(rev=i_rev is not None, t_ext=i_ext, t_rev=i_rev, tam=tam, avanco=avanco,
                alcance=alcance, ctx=ctx, varreu=varreu, imp5=abs(imp), **ating)


def pcts(v):
    if not v:
        return "-"
    v = sorted(v)
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    return f"p25 {q(.25):5.0f} | mediana {q(.5):5.0f} | p75 {q(.75):5.0f} | p90 {q(.9):5.0f}"


def main():
    dias = bq.carregar()
    rs = {d: r for d, bs in sorted(dias.items()) for r in [medir(bs)] if r}
    n = len(rs)
    rev = [r for r in rs.values() if r["rev"]]
    cont = [r for r in rs.values() if not r["rev"]]
    print(f"WIN 1 min, {n} pregoes. Impulso das 10:00 revertido: {len(rev)} ({len(rev) / n:.0%})\n")

    print("== Contexto: impulso das 10:00 em relacao a 1a hora ==")
    for ctx in ("a favor", "contra"):
        g = [r for r in rs.values() if r["ctx"] == ctx]
        if g:
            print(f"  impulso {ctx:<8} da 1a hora: n={len(g):3d}  reverte {sum(r['rev'] for r in g) / len(g):4.0%}")

    print("\n== Tamanho do impulso nos 5 primeiros minutos (tercis) ==")
    t = sorted(r["imp5"] for r in rs.values())
    c1, c2 = t[n // 3], t[2 * n // 3]
    for nome, f in (("pequeno", lambda v: v < c1), ("medio", lambda v: c1 <= v <= c2), ("grande", lambda v: v > c2)):
        g = [r for r in rs.values() if f(r["imp5"])]
        print(f"  {nome:<8} ({'<' if nome == 'pequeno' else ''}{c1 if nome != 'grande' else c2:.0f} pts) "
              f"n={len(g):3d}  reverte {sum(r['rev'] for r in g) / len(g):4.0%}")

    print("\n== Dias que REVERTERAM ==")
    print(f"  tamanho do impulso (o10 ate o extremo)  pts : {pcts([r['tam'] for r in rev])}")
    print(f"  avanco depois de 10:05 (contra quem fade) pts: {pcts([r['avanco'] for r in rev])}")
    print(f"  horario do extremo (min apos 10:00)         : {pcts([r['t_ext'] for r in rev])}")
    print(f"  horario do rompimento do oposto (min)       : {pcts([r['t_rev'] for r in rev])}")
    print(f"  alcance da reversao ate 11:29           pts : {pcts([r['alcance'] for r in rev])}")
    razao = [r["alcance"] / r["avanco"] for r in rev if r["avanco"] > 0]
    print(f"  alcance / avanco (R bruto do fade em 10:05) : mediana {st.median(razao):.1f}")
    for k, nome in (("ab09", "abertura 09:00"), ("meio", "50% da 1a hora"), ("oposto", "extremo oposto da 1a hora")):
        print(f"  alvo {nome:<28}: {sum(r[k] for r in rev) / len(rev):4.0%}")

    print("\n== Dias que NAO reverteram (continuacao) ==")
    print(f"  tamanho do impulso                      pts : {pcts([r['tam'] for r in cont])}")
    print(f"  avanco depois de 10:05                  pts : {pcts([r['avanco'] for r in cont])}")

    print("\n== Sweep do extremo da 1a hora pelo impulso ==")
    for v, nome in ((True, "varreu"), (False, "nao varreu")):
        g = [r for r in rs.values() if r["varreu"] == v]
        print(f"  {nome:<11} n={len(g):3d}  reverte {sum(r['rev'] for r in g) / len(g):4.0%}")

    print("\nDatas para conferir (reverteu | nao reverteu), ultimas:")
    print("  reverteu    :", ", ".join(str(d) for d, r in rs.items() if r["rev"])[-120:])
    print("  nao reverteu:", ", ".join(str(d) for d, r in rs.items() if not r["rev"])[-120:])


if __name__ == "__main__":
    main()
