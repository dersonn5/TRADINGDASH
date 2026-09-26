"""Que condicao separa o V da abertura do a vista da continuacao? (26/09/2026)

Pergunta do operador: "na abertura ele faz um movimento forte para um lado, e falso,
reverte e entrega em V. Qual condicao ele imprime que mais impacta em reverter?"

Definicoes — as mesmas ja combinadas no Estudo_Reversao_Abertura_Vista (Fase 3):
  o10       = abertura do candle de 1 min das 10:00.
  Impulso   = direcao de 10:00-10:04 (fechamento 10:04 - o10).
  Range15   = maxima/minima de 10:00-10:14.
  REVERTEU  = entre 10:15 e 10:59 rompe o lado OPOSTO do Range15.
  V         = reverteu E, ate 11:29, anda alem de o10 pelo menos o tamanho do impulso
              (o10 ate o extremo de 10:00-10:14), do outro lado. E o "entrega em V".

Condicoes: so o que se sabe ATE 10:15 (nada olha o futuro). Parte ja existe antes das
10:00 (dia anterior, gap, 1a hora); parte e o proprio impulso de 10:00-10:14.

Confirmacao em 5 anos: o 15 min nao tem o impulso de 5 min, entao usa um espelho:
impulso = corpo da barra de 15 min das 10:00; reverteu = 10:15-10:59 rompe o lado oposto
dela. A concordancia do espelho com a definicao de 1 min e medida no 1 min.

Saida: tabelas no terminal e profit/condicoes_reversao_por_dia.csv (1 min, um pregao
por linha) para conferir no Profit.
"""

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

from scipy.stats import fisher_exact

import backtest_quarters as bq
from padrao_15m import carregar15

AQUI = Path(__file__).parent
ROLAGEM = 0.012  # gap acima de 1,2% = troca de vencimento no cache sem ajuste


def t(s):
    return bq.hm(s)


def entre(bs, a, b):
    return [x for x in bs if t(a) <= x[0] < t(b)]


def condicoes(bs, prev, hist, extremo15, i_ext15, close15, up, hi15, lo15, o10, h1):
    """Condicoes conhecidas ate 10:15. bs = barras do dia; prev = barras do dia anterior."""
    o09, c09 = h1[0][1], h1[-1][4]
    hi1, lo1 = max(b[2] for b in h1), min(b[3] for b in h1)
    r1 = hi1 - lo1
    s = 1 if up else -1
    c = {}
    # antes das 10:00
    if prev:
        pc = prev[-1][4]
        pho, plo = max(b[2] for b in prev), min(b[3] for b in prev)
        gap = o09 - pc
        c["gap_pct"] = None if abs(gap) / pc > ROLAGEM else gap / pc * 100
        c["gap_lado"] = None if c["gap_pct"] is None or gap == 0 else ("mesmo lado do impulso" if (gap > 0) == up else "contra o impulso")
        c["dia_ant"] = "mesmo lado do impulso" if ((prev[-1][4] - prev[0][1]) > 0) == up else "contra o impulso"
        # a 1a hora ja tomou a maxima/minima do dia anterior no lado do impulso?
        c["h1_tomou_pd"] = (hi1 > pho) if up else (lo1 < plo)
        c["imp_tomou_pd"] = (extremo15 > pho) if up else (extremo15 < plo)
    if hist:
        atr = sum(hist) / len(hist)
        c["h1_rel_atr"] = r1 / atr
        c["imp_rel_atr"] = (hi15 - lo15) / atr
    c["h1_lado"] = "neutro" if c09 == o09 else ("mesmo lado do impulso" if (c09 > o09) == up else "contra o impulso")
    c["h1_range"] = r1
    # onde o a vista abre dentro da 1a hora, medido no sentido do impulso (1 = no extremo para onde o impulso vai)
    pos = (o10 - lo1) / r1 if r1 else 0.5
    c["pos_o10"] = pos if up else 1 - pos
    c["o10_vs_o09"] = "o10 ja do lado do impulso" if ((o10 > o09) == up) else "o10 do outro lado da abertura 09:00"
    # ate 10:15: o proprio impulso
    c["imp_range"] = hi15 - lo15
    c["imp_rel_h1"] = (hi15 - lo15) / r1 if r1 else None
    c["varreu_h1"] = (extremo15 > hi1) if up else (extremo15 < lo1)
    # fechamento de 10:14 dentro do range15, no sentido do impulso (1 = fechou no extremo)
    p = (close15 - lo15) / (hi15 - lo15) if hi15 > lo15 else 0.5
    c["fech15_pos"] = p if up else 1 - p
    c["min_extremo"] = i_ext15
    c["fech15_vs_o10"] = "fechou 10:14 de volta alem de o10" if (close15 - o10) * s < 0 else "fechou 10:14 do lado do impulso"
    return c


def medir1(bs, prev, hist):
    h1 = entre(bs, "09:00", "10:00")
    x = entre(bs, "10:00", "11:30")
    if len(h1) < 50 or len(x) < 85 or x[0][0] != t("10:00"):
        return None
    o10 = x[0][1]
    imp = x[4][4] - o10
    if imp == 0:
        return None
    up = imp > 0
    p15 = x[:15]
    hi15, lo15 = max(b[2] for b in p15), min(b[3] for b in p15)
    if up:
        i_ext = max(range(15), key=lambda i: p15[i][2])
        ext = p15[i_ext][2]
    else:
        i_ext = min(range(15), key=lambda i: p15[i][3])
        ext = p15[i_ext][3]
    rev = any((b[3] < lo15) if up else (b[2] > hi15) for b in x[15:60])
    tam = abs(ext - o10)
    alvo_v = o10 - tam if up else o10 + tam
    v = rev and any((b[3] <= alvo_v) if up else (b[2] >= alvo_v) for b in x[15:90])
    # espelho de 15 min: corpo da barra 10:00 e rompimento do lado oposto em 10:15-10:59
    up15 = p15[-1][4] > o10
    esp = None if p15[-1][4] == o10 else any((b[3] < lo15) if up15 else (b[2] > hi15) for b in x[15:60])
    c = condicoes(bs, prev, hist, ext, i_ext, p15[-1][4], up, hi15, lo15, o10, h1)
    return dict(rev=rev, v=v, up=up, esp=esp, esp_up=up15, **c)


def medir15(bs, prev, hist):
    """Espelho em 15 min: impulso = corpo da barra das 10:00."""
    h1 = [b for b in bs if t("09:00") <= b[0] < t("10:00")]
    b10 = [b for b in bs if b[0] == t("10:00")]
    depois = [b for b in bs if t("10:15") <= b[0] < t("11:00")]
    if len(h1) < 4 or not b10 or len(depois) < 3:
        return None
    _, o10, hi15, lo15, c15 = b10[0]
    if c15 == o10:
        return None
    up = c15 > o10
    rev = any((b[3] < lo15) if up else (b[2] > hi15) for b in depois)
    ext = hi15 if up else lo15
    c = condicoes(bs, prev, hist, ext, None, c15, up, hi15, lo15, o10, h1)
    return dict(rev=rev, up=up, **c)


def percorrer(dias, medir):
    out = {}
    ks = sorted(dias)
    for i, d in enumerate(ks):
        prev = dias[ks[i - 1]] if i else None
        hist = [max(b[2] for b in dias[k]) - min(b[3] for b in dias[k]) for k in ks[max(0, i - 10):i]]
        r = medir(dias[d], prev, hist if len(hist) >= 5 else None)
        if r:
            r["data"] = d
            r["dia_semana"] = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][d.weekday()]
            out[d] = r
    return out


def grupos(rs, chave):
    """Divide pela condicao: categorias como estao; numeros em tercis."""
    vals = [r[chave] for r in rs if r.get(chave) is not None]
    if not vals:
        return []
    if isinstance(vals[0], bool) or isinstance(vals[0], str):
        cats = sorted(set(vals), key=str)
        return [(str(c), [r for r in rs if r.get(chave) == c]) for c in cats]
    v = sorted(vals)
    a, b = v[len(v) // 3], v[2 * len(v) // 3]
    fmt = (lambda z: f"{z:.2f}") if max(abs(z) for z in v) < 20 else (lambda z: f"{z:.0f}")
    return [
        (f"baixo (< {fmt(a)})", [r for r in rs if r.get(chave) is not None and r[chave] < a]),
        (f"meio", [r for r in rs if r.get(chave) is not None and a <= r[chave] <= b]),
        (f"alto (> {fmt(b)})", [r for r in rs if r.get(chave) is not None and r[chave] > b]),
    ]


NOMES = {
    "gap_lado": "Gap das 09:00 (sem dias de rolagem)",
    "gap_pct": "Tamanho do gap % (com sinal)",
    "dia_ant": "Direcao do dia anterior",
    "h1_tomou_pd": "1a hora ja tomou max/min do dia anterior (lado do impulso)",
    "imp_tomou_pd": "Impulso tomou max/min do dia anterior",
    "h1_rel_atr": "Range da 1a hora / range medio 10 dias",
    "imp_rel_atr": "Range 10:00-10:14 / range medio 10 dias",
    "h1_lado": "Direcao da 1a hora",
    "h1_range": "Range da 1a hora (pts)",
    "pos_o10": "Onde o a vista abre na 1a hora (1 = no extremo para onde vai o impulso)",
    "o10_vs_o09": "Abertura 10:00 x abertura 09:00",
    "imp_range": "Range 10:00-10:14 (pts)",
    "imp_rel_h1": "Range 10:00-10:14 / range da 1a hora",
    "varreu_h1": "Impulso varreu max/min da 1a hora ate 10:14",
    "fech15_pos": "Fechamento 10:14 no range15 (1 = fechou no extremo do impulso)",
    "min_extremo": "Minuto do extremo do impulso (0-14)",
    "fech15_vs_o10": "Fechamento 10:14 x abertura 10:00",
    "dia_semana": "Dia da semana",
}


def tabela(rs, chaves, alvo="rev", titulo=""):
    base = sum(r[alvo] for r in rs) / len(rs)
    print(f"\n=== {titulo} — n={len(rs)}, base {base:.0%} ===")
    ranking = []
    for k in chaves:
        gs = [(n, g) for n, g in grupos(rs, k) if len(g) >= 10]  # grupo pequeno (ex.: 1a hora neutra) fica fora
        if len(gs) < 2:
            continue
        print(f"\n  {NOMES[k]}")
        taxas = []
        for nome, g in gs:
            tx = sum(r[alvo] for r in g) / len(g)
            taxas.append((tx, g))
            print(f"    {nome:<42} n={len(g):4d}  {tx:4.0%}")
        # extremos: o grupo de maior e o de menor taxa, teste exato de Fisher
        hi, lo = max(taxas, key=lambda z: z[0]), min(taxas, key=lambda z: z[0])
        a, b = sum(r[alvo] for r in hi[1]), len(hi[1])
        cc, dd = sum(r[alvo] for r in lo[1]), len(lo[1])
        p = fisher_exact([[a, b - a], [cc, dd - cc]])[1]
        ranking.append((hi[0] - lo[0], p, k))
    print(f"\n  --- Ranking por diferenca entre o melhor e o pior grupo ({titulo}) ---")
    for dif, p, k in sorted(ranking, reverse=True):
        print(f"    {dif:5.0%}  p={p:.3f}  {NOMES[k]}")
    return {k: (dif, p) for dif, p, k in ranking}


def estabilidade(rs, chave, alvo="rev", partes=None):
    """Taxa por grupo em cada pedaco do periodo (metades no 1 min, anos no 15 min)."""
    for nome_p, sub in partes:
        linhas = []
        for nome, g in grupos(sub, chave):
            if g:
                linhas.append(f"{nome.split(' (')[0]} {sum(r[alvo] for r in g) / len(g):.0%} (n={len(g)})")
        print(f"      {nome_p:<14} " + " | ".join(linhas))


def main():
    CH = ["gap_lado", "dia_ant", "h1_tomou_pd", "imp_tomou_pd", "h1_rel_atr", "imp_rel_atr", "h1_lado",
          "h1_range", "pos_o10", "o10_vs_o09", "imp_range", "imp_rel_h1", "varreu_h1", "fech15_pos",
          "min_extremo", "fech15_vs_o10", "dia_semana"]

    dias1 = bq.carregar()
    r1 = percorrer(dias1, medir1)
    rs1 = list(r1.values())
    print(f"WIN 1 min: {len(rs1)} pregoes ({rs1[0]['data']} a {rs1[-1]['data']})")
    print(f"  Reverteu (rompe o lado oposto do 10:00-10:14 ate 10:59): {sum(r['rev'] for r in rs1) / len(rs1):.0%}")
    print(f"  V completo (e anda alem de o10 o tamanho do impulso ate 11:29): {sum(r['v'] for r in rs1) / len(rs1):.0%}")
    por_mes = defaultdict(list)
    for r in rs1:
        por_mes[r["data"].strftime("%Y-%m")].append(r)
    print("  Por mes (reverteu / V):", " | ".join(f"{m} {sum(r['rev'] for r in g) / len(g):.0%}/{sum(r['v'] for r in g) / len(g):.0%} (n={len(g)})" for m, g in sorted(por_mes.items())))
    ok = [r for r in rs1 if r["esp"] is not None]
    conc = sum((r["esp"] == r["rev"]) and (r["esp_up"] == r["up"]) for r in ok) / len(ok)
    print(f"  Espelho de 15 min concorda com a definicao de 1 min (mesma direcao e mesmo desfecho): {conc:.0%} dos dias")

    rk1 = tabela(rs1, CH, "rev", "1 MIN · REVERTEU")
    rkv = tabela(rs1, CH, "v", "1 MIN · V COMPLETO")

    dias15 = carregar15()
    r15 = percorrer(dias15, medir15)
    rs15 = list(r15.values())
    print(f"\n\nWIN 15 min (espelho): {len(rs15)} pregoes ({rs15[0]['data']} a {rs15[-1]['data']}), "
          f"reverteu {sum(r['rev'] for r in rs15) / len(rs15):.0%}")
    CH15 = [k for k in CH if k not in ("min_extremo", "fech15_vs_o10")] + ["fech15_vs_o10"]
    rk15 = tabela(rs15, CH15, "rev", "15 MIN · 5 ANOS · REVERTEU")

    # estabilidade das condicoes que mais separam no 1 min e no 5 anos
    top = sorted({k for k, (dif, p) in rk1.items() if p < 0.10} | {k for k, (dif, p) in rk15.items() if p < 0.01})
    anos = defaultdict(list)
    for r in rs15:
        anos[str(r["data"].year)].append(r)
    meio = len(rs1) // 2
    print("\n\n=== Estabilidade das condicoes que separaram (p<0,10 no 1 min ou p<0,01 nos 5 anos) ===")
    for k in top:
        print(f"\n  {NOMES[k]}")
        print("    1 min:")
        estabilidade(rs1, k, "rev", [("1a metade", rs1[:meio]), ("2a metade", rs1[meio:])])
        if k in CH15:
            print("    15 min, por ano:")
            estabilidade(rs15, k, "rev", sorted(anos.items()))

    with (AQUI / "condicoes_reversao_por_dia.csv").open("w", newline="", encoding="utf-8") as f:
        campos = ["data", "up", "rev", "v"] + CH
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rs1:
            w.writerow({k: (f"{r[k]:.2f}" if isinstance(r.get(k), float) else r.get(k)) for k in campos})


if __name__ == "__main__":
    main()
