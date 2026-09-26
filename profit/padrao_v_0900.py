"""O V da abertura do futuro (09:00) — definicao do operador em 26/09/2026.

"Vi diversos pregoes que o indice comeca indo pra baixo e reverte em V, e vice-versa."

Definicao (respostas do operador, antes de rodar):
  Abertura   = abertura do primeiro candle das 09:00 (o09).
  Movimento  = o preco se afasta 800 pts ou mais de o09. O lado que chega aos 800 primeiro
               define a direcao. Se nenhum lado chega ate 12:00, o dia nao entra.
  Extremo    = o ponto mais longe de o09 nessa direcao, ate a volta.
  V          = depois do extremo, o preco volta pelo menos 75% de (extremo - o09),
               ate 12:00.
Conservador: a volta so e checada contra o extremo dos candles ANTERIORES; um candle
que faz extremo novo e volta no mesmo candle nao conta como V nele.

Condicoes medidas no instante em que o movimento chega aos 800 pts (o que da para saber
na hora, sem olhar o futuro): horario, gap das 09:00, direcao do dia anterior, se ja tomou
a maxima/minima do dia anterior, dia da semana.

Base: 1 min (abr-set/2026) e 15 min (2021-2026). No 15 min o caminho dentro do candle nao
e visto, entao a medida e mais grosseira (e mais conservadora).
Saida: tabelas e profit/padrao_v_0900_dias.csv (1 min) com as datas para conferir no Profit.
"""

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

import backtest_quarters as bq
from padrao_15m import carregar15

AQUI = Path(__file__).parent
MOVIMENTO = 800
VOLTA = 0.75
ROLAGEM = 0.012
FIM = dt.time(12, 0)


def medir(bs, prev):
    manha = [b for b in bs if b[0] < FIM]
    if not manha or manha[0][0] > dt.time(9, 5):
        return None
    o09 = manha[0][1]
    lado = None
    i0 = None
    for i, b in enumerate(manha):
        sobe, cai = b[2] - o09 >= MOVIMENTO, o09 - b[3] >= MOVIMENTO
        if sobe and cai:
            return None  # os dois lados no mesmo candle: ambiguo
        if sobe or cai:
            lado, i0 = (1 if sobe else -1), i
            break
    if lado is None:
        return dict(sem_movimento=True)
    ext = manha[i0][2] if lado == 1 else manha[i0][3]
    t_ext = manha[i0][0]
    v_em = None
    for b in manha[i0 + 1:]:
        alvo = ext - VOLTA * (ext - o09) if lado == 1 else ext + VOLTA * (o09 - ext)
        if (b[3] <= alvo) if lado == 1 else (b[2] >= alvo):
            v_em = b[0]
            break
        novo = b[2] if lado == 1 else b[3]
        if (novo > ext) if lado == 1 else (novo < ext):
            ext, t_ext = novo, b[0]
    r = dict(sem_movimento=False, lado="alta" if lado == 1 else "baixa", t800=manha[i0][0], t_ext=t_ext,
             tamanho=abs(ext - o09), v=v_em is not None, t_v=v_em)
    # condicoes no instante dos 800 pts
    r["hora_800"] = ("09:00-09:29" if r["t800"] < dt.time(9, 30) else "09:30-09:59" if r["t800"] < dt.time(10, 0)
                     else "10:00-10:29" if r["t800"] < dt.time(10, 30) else "10:30-11:59")
    if prev:
        pc = prev[-1][4]
        gap = o09 - pc
        r["gap"] = None if abs(gap) / pc > ROLAGEM or gap == 0 else ("mesmo lado do movimento" if (gap > 0) == (lado == 1) else "contra o movimento")
        r["dia_ant"] = "mesmo lado do movimento" if ((prev[-1][4] - prev[0][1]) > 0) == (lado == 1) else "contra o movimento"
        ate = manha[:i0 + 1]
        r["tomou_pd"] = (max(b[2] for b in ate) > max(b[2] for b in prev)) if lado == 1 else (min(b[3] for b in ate) < min(b[3] for b in prev))
    return r


def percorrer(dias):
    ks = sorted(dias)
    out = {}
    for i, d in enumerate(ks):
        r = medir(dias[d], dias[ks[i - 1]] if i else None)
        if r:
            r["data"] = d
            r["semana"] = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"][d.weekday()]
            out[d] = r
    return out


def pct(g):
    return f"{sum(r['v'] for r in g) / len(g):4.0%}" if g else "  - "


def quantis(v):
    v = sorted(v)
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    return f"p25 {q(.25)} | mediana {q(.5)} | p75 {q(.75)}"


def relatorio(nome, rs_todos):
    total = len(rs_todos)
    rs = [r for r in rs_todos if not r["sem_movimento"]]
    print(f"\n=== {nome} ===")
    print(f"Pregoes: {total}. Com movimento de {MOVIMENTO}+ pts a partir das 09:00 ate 12:00: {len(rs)} ({len(rs) / total:.0%})")
    print(f"Desses, V (volta 75% ate 12:00): {sum(r['v'] for r in rs)} ({pct(rs).strip()})")
    for lado in ("baixa", "alta"):
        g = [r for r in rs if r["lado"] == lado]
        print(f"  comecou em {lado:<5}: n={len(g):4d}  V {pct(g)}")
    for chave, titulo in (("hora_800", "Horario em que chegou aos 800 pts"), ("gap", "Gap das 09:00 (sem rolagem)"),
                          ("dia_ant", "Dia anterior"), ("tomou_pd", "Ja tinha tomado max/min do dia anterior"),
                          ("semana", "Dia da semana")):
        print(f"  {titulo}:")
        cats = sorted({r.get(chave) for r in rs if r.get(chave) is not None}, key=str)
        for c in cats:
            g = [r for r in rs if r.get(chave) == c]
            print(f"      {str(c):<26} n={len(g):4d}  V {pct(g)}")
    return rs


def main():
    r1 = percorrer(bq.carregar())
    rs1 = relatorio("WIN 1 min (abr-set/2026)", list(r1.values()))
    vs = [r for r in rs1 if r["v"]]
    if vs:
        mins = lambda t: t.hour * 60 + t.minute - 540
        print("  Dias com V:")
        print(f"      tamanho do movimento ate o extremo (pts): {quantis([int(r['tamanho']) for r in vs])}")
        print(f"      horario do extremo (min depois das 09:00): {quantis([mins(r['t_ext']) for r in vs])}")
        print(f"      horario em que completou o V (min depois das 09:00): {quantis([mins(r['t_v']) for r in vs])}")
    print("  Datas com V:   ", ", ".join(f"{r['data']:%d/%m}({r['lado'][0]})" for r in vs))
    print("  Datas sem V:   ", ", ".join(f"{r['data']:%d/%m}({r['lado'][0]})" for r in rs1 if not r["v"]))

    r15 = percorrer(carregar15())
    rs15 = relatorio("WIN 15 min (2021-2026)", list(r15.values()))
    anos = defaultdict(list)
    for r in rs15:
        anos[r["data"].year].append(r)
    print("  Por ano:", " | ".join(f"{a}: V {pct(g).strip()} (n={len(g)})" for a, g in sorted(anos.items())))

    # 800 pts em 2021 (indice ~117 mil) e um movimento maior que em 2026 (~181 mil):
    # repete por ano com o mesmo tamanho em % (800 pts sobre o indice de 2026 = 0,43%)
    global MOVIMENTO
    print("\n  Por ano com o movimento em % (0,43% da abertura, = 800 pts no indice de 2026):")
    ks = sorted(r15_dias := carregar15())
    anos_pct = defaultdict(list)
    for i, d in enumerate(ks):
        MOVIMENTO = r15_dias[d][0][1] * 0.0043
        r = medir(r15_dias[d], r15_dias[ks[i - 1]] if i else None)
        if r and not r["sem_movimento"]:
            anos_pct[d.year].append(r)
    MOVIMENTO = 800
    for a, g in sorted(anos_pct.items()):
        cedo = [r for r in g if r["hora_800"] == "09:00-09:29"]
        tarde = [r for r in g if r["hora_800"] != "09:00-09:29"]
        print(f"    {a}: V {pct(g).strip()} (n={len(g)}) | chegou ate 09:29: V {pct(cedo).strip()} (n={len(cedo)}) "
              f"| depois: V {pct(tarde).strip()} (n={len(tarde)})")

    with (AQUI / "padrao_v_0900_dias.csv").open("w", newline="", encoding="utf-8") as f:
        campos = ["data", "lado", "t800", "t_ext", "tamanho", "v", "t_v", "hora_800", "gap", "dia_ant", "tomou_pd", "semana"]
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rs1:
            w.writerow(r)


if __name__ == "__main__":
    main()
