"""Hierarquia de liquidez: o gatilho paga mais quando vem depois de liquidez de peso?
WIN, 1 min, janela 09:00-12:00.

Operacional (operador, 22/09/2026): janela 09:00-12:00; captura de liquidez
importante, depois MSS + FVG (ou BPR); na continuidade, topo/fundo de inducao,
captura dessa liquidez e FVG ou MSS + FVG a favor. Os trades grandes (~1.000 pts)
nao sao presos a um horario.

Pergunta: dentro da janela, o que separa o gatilho que chega a 8-10R do que para
no stop? Hipotese testada: a IMPORTANCIA da liquidez capturada antes do MSS.

Gatilho (mesmas definicoes do barra10/gatilho_vista):
  MSS = candle fecha alem do ultimo swing contrario (fractal 2 de 1 min),
        com fechamento entre 09:05 e 11:59.
  Pernada com candle de corpo >= 1,5x a media dos 15 anteriores.
  FVG da pernada, entrada na borda ate 30 min depois do MSS.
  Stop no extremo da pernada (o candle de ORIGEM) + 1 tick.
  Todos os gatilhos do dia sao medidos, cada um de forma independente.

Classe de liquidez = o nivel mais importante VARRIDO nos 30 min antes do MSS
(furado pela primeira vez nessa janela, intacto antes dela):
  1 DIA ANTERIOR  maxima/minima do pregao anterior (09:00-18:00)
  2 1a HORA       maxima/minima de 09:00-09:59 (so para origem a partir de 10:00)
  3 SWING 15 MIN  fractal 2 de candles de 15 min do proprio dia
  4 SWING 1 MIN   fractal 3 de 1 min do proprio dia
  5 NENHUMA
Compra precisa ter varrido um FUNDO; venda, um TOPO.

Resultado: chance de chegar a kR antes de -1R (MFE) e resultado com a gestao do
operador (alvo no proximo BSL/SSL + trailing). Custo 10 pts.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import setup_vista as sv
from barra10 import NIVEIS_R, mfe_em_r
from gatilho_vista import corpo
from ny_1030 import mais

H = bq.hm
CLASSES = ("1 dia anterior", "2 1a hora", "3 swing 15 min", "4 swing 1 min", "5 nenhuma")


def barras15(bs):
    grupos = defaultdict(list)
    for b in bs:
        m = b[0].hour * 60 + b[0].minute
        grupos[(m - 540) // 15].append(b)
    out = []
    for k in sorted(grupos):
        g = grupos[k]
        out.append((g[0][0], g[0][1], max(x[2] for x in g), min(x[3] for x in g), g[-1][4], g[-1][0]))
    return out  # (inicio, o, h, l, c, fim)


JANELA_VARRIDA = 30  # minutos antes do MSS


def classe(bs, i_mss, alta, anterior):
    """Nivel mais importante VARRIDO nos JANELA_VARRIDA minutos antes do MSS.

    Varrido = o preco furou o nivel pela primeira vez dentro dessa janela (entre
    ws e o MSS), e o nivel estava intacto antes dela. A varrida pode levar varios
    candles e varias pernadas - em 22/09 a queda de 10:00 a 10:15 furou a minima
    da 1a hora as ~10:10 e fez o extremo as 10:15: e UMA varrida.
    """
    ws = max(0, i_mss - JANELA_VARRIDA)
    jan = bs[ws:i_mss + 1]
    if alta:
        furou = lambda nivel, seg: min((b[3] for b in seg), default=1e12) < nivel
    else:
        furou = lambda nivel, seg: max((b[2] for b in seg), default=-1) > nivel

    def varrido(nivel, intacto_desde):
        return furou(nivel, jan) and not furou(nivel, bs[intacto_desde:ws])

    if anterior:
        nivel = min(b[3] for b in anterior) if alta else max(b[2] for b in anterior)
        if varrido(nivel, 0):
            return CLASSES[0]
    i10 = sv.idx(bs, H("10:00"))
    if bs[i_mss][0] >= H("10:00") and i10 < len(bs):
        h1 = bs[:i10]
        nivel = min(b[3] for b in h1) if alta else max(b[2] for b in h1)
        seg = bs[max(ws, i10):i_mss + 1]
        if furou(nivel, seg) and not furou(nivel, bs[i10:max(ws, i10)]):
            return CLASSES[1]
    antes = bs[:ws]
    b15 = [x for x in barras15(antes) if x[5] < bs[ws][0]]
    t15, f15 = sv.fractais([(x[0], x[1], x[2], x[3], x[4]) for x in b15], 2)
    for i in (f15 if alta else t15):
        nivel = b15[i][3] if alta else b15[i][2]
        i_depois = next((k for k, b in enumerate(bs) if b[0] > b15[i][5]), ws)
        if varrido(nivel, i_depois):
            return CLASSES[2]
    t1, f1 = sv.fractais(antes, 3)
    for i in (f1 if alta else t1):
        nivel = bs[i][3] if alta else bs[i][2]
        if varrido(nivel, i + 1):
            return CLASSES[3]
    return CLASSES[4]


def gatilhos_do_dia(bs, anterior):
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
            media = st.mean(corpo(b) for b in base) or 1
            if max(corpo(b) for b in bs[i_org:m + 1]) < 1.5 * media:
                continue
            gaps = sv.fvgs(bs, i_org + 1, m + 1, alta=alta)
            if not gaps:
                continue
            vistos.add((i_org, alta))
            g_i, g_lo, g_hi = gaps[-1]
            borda = g_hi if alta else g_lo
            stop = extremo - sv.TICK if alta else extremo + sv.TICK
            lado = 1 if alta else -1
            lim = sv.idx(bs, mais(bs[m][0], 30))
            for f in range(g_i + 1, min(lim, len(bs))):
                x = bs[f]
                if (x[3] <= stop) if alta else (x[2] >= stop):
                    break
                if (x[3] <= borda) if alta else (x[2] >= borda):
                    alvo = sv.alvo_liquidez(bs, f, lado, borda)
                    pts, mot, _ = sv.gerir(bs, f, lado, borda, stop, alvo)
                    out.append(dict(classe=classe(bs, m, alta, anterior), lado=lado,
                                    mfe=mfe_em_r(bs, f, lado, borda, stop), pts=pts,
                                    r=pts / abs(borda - stop), risco=abs(borda - stop),
                                    t_mss=bs[m][0], t_ent=x[0]))
                    break
    return out


def linha(nome, ts):
    if not ts:
        print(f"  {nome:<18} sem gatilhos")
        return
    n = len(ts)
    probs = "  ".join(f"{k}R {sum(t['mfe'] >= k for t in ts) / n:4.0%}" for k in NIVEIS_R)
    print(f"  {nome:<18} n={n:4d} | antes de -1R: {probs} | gestao {sum(t['r'] for t in ts) / n:+.2f}R  "
          f"risco med {sorted(t['risco'] for t in ts)[n // 2]:.0f} pts")


def main():
    dias = bq.carregar()
    ordem = sorted(dias)
    todos = []
    for k, d in enumerate(ordem):
        if k == 0:
            continue
        bs = bq.entre(dias[d], H("09:00"), H("17:51"))
        ant = bq.entre(dias[ordem[k - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        for g in gatilhos_do_dia(bs, ant):
            g["data"] = d
            todos.append(g)
    n_dias = len({t['data'] for t in todos})
    print(f"WIN 1 min, janela 09:00-12:00: {len(todos)} gatilhos em {n_dias} pregoes "
          f"({len(todos) / max(n_dias, 1):.1f} por dia)")
    print("limiar de empate: 3R 25% | 5R 17% | 8R 11% | 10R 9%\n")
    linha("TODOS", todos)
    for c in CLASSES:
        linha(c, [t for t in todos if t["classe"] == c])
    meio = ordem[len(ordem) // 2]
    print("\nestabilidade (1a metade | 2a metade):")
    for c in CLASSES:
        a = [t for t in todos if t["classe"] == c and t["data"] <= meio]
        b = [t for t in todos if t["classe"] == c and t["data"] > meio]
        f = lambda ts, k: f"{sum(t['mfe'] >= k for t in ts) / len(ts):4.0%}" if ts else "  - "
        g = lambda ts: f"{sum(t['r'] for t in ts) / len(ts):+.2f}R" if ts else "  -  "
        print(f"  {c:<18} 8R {f(a, 8)} (n={len(a):3d}) {g(a)} | 8R {f(b, 8)} (n={len(b):3d}) {g(b)}")


if __name__ == "__main__":
    main()
