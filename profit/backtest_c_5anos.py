"""Cenarios do Setup C nos 5 anos de 15 min (o 1 min so tem 5 meses no Profit).

Sem o gatilho de 1 min, a entrada mais cedo que o 15 min permite e o fechamento da primeira
barra que volta para dentro depois do sweep. Mede a direcao (reversao contra o sweep), nao
o trade de 1 min com stop curto.

C1: entre 10:15 e 11:14 o preco passa da maxima (minima) da barra das 10 (B).
    Entrada: fechamento da primeira barra, a partir da do sweep, que fecha de volta dentro
    de B (abaixo da maxima de B, na venda). Stop: extremo do sweep ate ali + 1 tick.
    Extra: chega ao outro lado de B ate 12:00?
C2: B passa do topo (fundo) de uma barra de 15 min anterior intacto ate 10:00 (o ultimo
    topo/fundo, o mais proximo). Entrada: fechamento da primeira barra, a partir de B, que
    fecha de volta abaixo (acima) do nivel varrido. Stop: extremo do sweep + 1 tick.
Entrada so ate 11:30 (barra que comeca antes de 11:15). kR medido ate 12:00.

Contexto da 1a hora (backtest_c2b.tendencia: 3 de 4 barras ou >= 475 pts):
  reversao    = operacao CONTRA a tendencia da 1a hora
  continuacao = operacao A FAVOR (sweep contra a tendencia, papa os stops e segue)
  lateral     = sem tendencia
"""

from collections import defaultdict

import backtest_c2b as c2b
import padrao_15m as p

TICK = 5


def m(b):
    return p.minutos(b[0])


def kr(b15, i_ent, ext, lado):
    ent = b15[i_ent][4]
    stop = ext + TICK if lado < 0 else ext - TICK
    R = abs(ent - stop)
    if R <= 0:
        return None
    melhor = 0.0
    for y in b15[i_ent + 1:]:
        if m(y) >= 720:
            break
        if (y[2] >= stop) if lado < 0 else (y[3] <= stop):
            return melhor
        melhor = max(melhor, ((ent - y[3]) if lado < 0 else (y[2] - ent)) / R)
    return melhor


def entrada(b15, i_ini, nivel, lado):
    """Primeira barra a partir de i_ini que fecha de volta alem do nivel, comecando antes de 11:15."""
    for k in range(i_ini, len(b15)):
        if m(b15[k]) >= 675:
            return None
        if (b15[k][4] < nivel) if lado < 0 else (b15[k][4] > nivel):
            return k
    return None


def casos(b15):
    idx = {m(b): i for i, b in enumerate(b15)}
    if 600 not in idx:
        return []
    iB = idx[600]
    B = b15[iB]
    tend = c2b.tendencia(b15)
    out = []
    antes = [i for i in range(iB) if m(b15[i]) >= 540]
    topos = [b15[i][2] for i in antes if all(b15[k][2] < b15[i][2] for k in range(i + 1, iB))]
    fundos = [b15[i][3] for i in antes if all(b15[k][3] > b15[i][3] for k in range(i + 1, iB))]
    for lado in (-1, 1):
        ctx = "lateral" if tend == 0 else "continuacao" if tend == lado else "reversao"
        # C2
        niveis = topos if lado < 0 else fundos
        if niveis:
            nivel = min(niveis) if lado < 0 else max(niveis)
            if (B[2] > nivel) if lado < 0 else (B[3] < nivel):
                k = entrada(b15, iB, nivel, lado)
                r = None
                if k is not None:
                    seg = b15[iB:k + 1]
                    ext = max(b[2] for b in seg) if lado < 0 else min(b[3] for b in seg)
                    r = kr(b15, k, ext, lado)
                out.append(("C2", ctx, r, None))
        # C1
        nivel = B[2] if lado < 0 else B[3]
        ks = next((k for k in range(iB + 1, len(b15)) if m(b15[k]) < 675
                   and ((b15[k][2] > nivel) if lado < 0 else (b15[k][3] < nivel))), None)
        if ks is None:
            continue
        k = entrada(b15, ks, nivel, lado)
        r = None
        oposto = False
        if k is not None:
            seg = b15[ks:k + 1]
            ext = max(b[2] for b in seg) if lado < 0 else min(b[3] for b in seg)
            r = kr(b15, k, ext, lado)
            alvo = B[3] if lado < 0 else B[2]
            oposto = any(((y[3] <= alvo) if lado < 0 else (y[2] >= alvo))
                         for y in b15[k + 1:] if m(y) < 720)
        out.append(("C1", ctx, r, oposto))
    return out


def main():
    dias = p.carregar15()
    res = defaultdict(list)
    for d, b15 in sorted(dias.items()):
        for modo, ctx, r, op in casos(b15):
            res[(modo, ctx)].append((d.year, r, op))
            res[(modo, "todos")].append((d.year, r, op))
    print("5 anos de 15 min. Sweep -> entrada no fechamento da 1a barra que volta, stop no extremo.\n")
    for modo in ("C1", "C2"):
        print(f"{modo}:")
        for ctx in ("reversao", "continuacao", "lateral", "todos"):
            x = res[(modo, ctx)]
            e = [r for _, r, _ in x if r is not None]
            n = len(e)
            if not n:
                continue
            f = lambda k: sum(r >= k for r in e) / n
            extra = ""
            if modo == "C1":
                extra = f"  chega ao outro lado de B {sum(op for _, r, op in x if r is not None) / n:4.0%}"
            print(f"  {ctx:<12} sweeps {len(x):4d}  voltou {n / len(x):4.0%}  |  1R {f(1):4.0%}  2R {f(2):4.0%}"
                  f"  3R {f(3):4.0%}  5R {f(5):4.0%}{extra}")
        print("  por ano, chance de 2R:   reversao  x  continuacao  x  lateral")
        for a in range(2021, 2027):
            cel = []
            for ctx in ("reversao", "continuacao", "lateral"):
                e = [r for y, r, _ in res[(modo, ctx)] if y == a and r is not None]
                cel.append(f"{sum(r >= 2 for r in e) / len(e):4.0%} (n={len(e):3d})" if e else "   -       ")
            print(f"   {a}:  " + "  x  ".join(cel))
        print()


if __name__ == "__main__":
    main()
