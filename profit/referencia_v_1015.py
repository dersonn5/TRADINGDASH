"""Referencia bruta: o sinal das 10:15 (condicoes_reversao.py) vira trade? (26/09/2026)

NAO e regra de entrada do operador — e a medida mais simples possivel, para saber se o
"92% reverte" deixa espaco para ganhar depois de stop e custo.

Trade de referencia, contra o impulso das 10:00:
  Entrada = fechamento do candle de 10:14 (o que se sabe as 10:15).
  Stop    = extremo do impulso (10:00-10:14) + 1 tick.
  Alvo 1  = lado oposto do range 10:00-10:14 + 1 tick (a definicao de "reverteu").
  Alvo V  = abertura das 10:00 - tamanho do impulso (a definicao de "V completo").
  Prazo   = 11:29, sai no fechamento se nada bateu. Custo 10 pts por trade.
No 1 min o caminho e resolvido candle a candle; se stop e alvo caem no mesmo candle,
conta stop (conservador).

Espelho de 5 anos (15 min): entrada no fechamento da barra das 10:00, stop alem do
extremo dela, alvo 1 = lado oposto dela; mesmo candle com stop e alvo = stop.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import condicoes_reversao as cr
from padrao_15m import carregar15

TICK = 5
CUSTO = 10


def andar(barras, venda, entrada, stop, alvo):
    for b in barras:
        bateu_stop = (b[2] >= stop) if venda else (b[3] <= stop)
        bateu_alvo = (b[3] <= alvo) if venda else (b[2] >= alvo)
        if bateu_stop:
            return stop, "stop"
        if bateu_alvo:
            return alvo, "alvo"
    return barras[-1][4], "prazo"


def trade1(bs, alvo_tipo):
    x = cr.entre(bs, "10:00", "11:30")
    if len(x) < 85 or x[0][0] != bq.hm("10:00"):
        return None
    o10 = x[0][1]
    imp = x[4][4] - o10
    if imp == 0:
        return None
    up = imp > 0
    p15 = x[:15]
    hi15, lo15 = max(b[2] for b in p15), min(b[3] for b in p15)
    ext = hi15 if up else lo15
    entrada = p15[-1][4]
    venda = up  # contra o impulso
    stop = ext + TICK if up else ext - TICK
    tam = abs(ext - o10)
    alvo = (lo15 - TICK if up else hi15 + TICK) if alvo_tipo == "1" else (o10 - tam if up else o10 + tam)
    if (venda and alvo >= entrada) or (not venda and alvo <= entrada):
        return None
    saida, como = andar(x[15:90], venda, entrada, stop, alvo)
    risco = abs(entrada - stop)
    pts = (entrada - saida if venda else saida - entrada) - CUSTO
    return dict(pts=pts, r=pts / risco, risco=risco, premio=abs(alvo - entrada), como=como)


def trade15(bs):
    b10 = [b for b in bs if b[0] == bq.hm("10:00")]
    dep = [b for b in bs if bq.hm("10:15") <= b[0] < bq.hm("11:30")]
    if not b10 or len(dep) < 4:
        return None
    _, o, hi, lo, c = b10[0]
    if c == o or hi == lo:
        return None
    up = c > o
    venda = up
    stop = hi + TICK if up else lo - TICK
    alvo = lo - TICK if up else hi + TICK
    saida, como = andar(dep, venda, c, stop, alvo)
    risco = abs(c - stop)
    pts = (c - saida if venda else saida - c) - CUSTO
    return dict(pts=pts, r=pts / risco, risco=risco, premio=abs(alvo - c), como=como)


def resumo(nome, ts):
    if not ts:
        print(f"  {nome}: sem trades")
        return
    n = len(ts)
    ac = sum(t["pts"] > 0 for t in ts) / n
    r = [t["r"] for t in ts]
    ep = st.stdev(r) / n ** 0.5 if n > 1 else 0
    print(f"  {nome:<58} n={n:4d}  acerto {ac:4.0%}  media {st.mean(r):+.2f}R (erro {ep:.2f})  "
          f"{st.mean(t['pts'] for t in ts):+5.0f} pts  risco med {st.median(t['risco'] for t in ts):4.0f}  "
          f"alvo med {st.median(t['premio'] for t in ts):4.0f}  stops {sum(t['como'] == 'stop' for t in ts) / n:.0%}")


def main():
    dias1 = bq.carregar()
    conds = cr.percorrer(dias1, cr.medir1)
    print("1 MIN (abr-set/2026), entrada 10:15 contra o impulso, custo 10 pts\n")
    for alvo_tipo, nome_alvo in (("1", "alvo = lado oposto do 10:00-10:14"), ("V", "alvo = V completo")):
        print(f" {nome_alvo}")
        grupos = defaultdict(list)
        for d, c in conds.items():
            t = trade1(dias1[d], alvo_tipo)
            if not t:
                continue
            grupos["todos os dias"].append(t)
            cedo, volta = c["min_extremo"] <= 7, c["fech15_pos"] < 0.5
            if cedo and volta:
                grupos["SINAL: extremo ate 10:07 e 10:14 voltou metade"].append(t)
            if not cedo and not volta:
                grupos["contrario: extremo tarde e 10:14 no lado do impulso"].append(t)
        for k in ("todos os dias", "SINAL: extremo ate 10:07 e 10:14 voltou metade", "contrario: extremo tarde e 10:14 no lado do impulso"):
            resumo(k, grupos[k])
        print()

    dias15 = carregar15()
    c15 = cr.percorrer(dias15, cr.medir15)
    print("15 MIN, 5 ANOS (espelho), entrada no fechamento da barra das 10:00, alvo = lado oposto dela\n")
    por_ano = defaultdict(list)
    todos, sinal = [], []
    for d, c in c15.items():
        t = trade15(dias15[d])
        if not t:
            continue
        todos.append(t)
        if c["fech15_pos"] < 0.5:
            sinal.append(t)
            por_ano[d.year].append(t)
    resumo("todos os dias", todos)
    resumo("SINAL: barra das 10 fechou com pavio contra (pos < 0,5)", sinal)
    for a, ts in sorted(por_ano.items()):
        resumo(f"   {a}", ts)


if __name__ == "__main__":
    main()
