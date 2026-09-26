"""Setup V: o V da abertura das 09:00 + sweep de liquidez + gatilhos do operador (26/09/2026).

Ideia do operador: "esse padrao, somado a sweep de minima do dia anterior, BSL ou SSL, e
usando todos nossos gatilhos de entrada". Definicoes confirmadas antes de rodar:

  Movimento  = o preco se afasta 800 pts da abertura das 09:00 (padrao_v_0900.py). O lado
               que chega primeiro e a direcao; o trade e CONTRA ela (a reversao do V).
  Liquidez   = maxima/minima do dia anterior (PDH/PDL) + topos/fundos de swing de 15 min do
               dia anterior que ficaram intactos ate o fechamento dele (BSL/SSL).
               Movimento de baixa -> niveis abaixo (SSL); de alta -> acima (BSL).
  Sweep      = primeiro minuto em que o preco passa do nivel, no lado do movimento.
  Gatilho    = reversao no 1 min em ate 30 min depois de um sweep, com o movimento de 800
               pts ja feito. Os quatro do operador, cada um medido separado:
     MSS+FVG  : MSS (candle fecha alem do ultimo swing contrario) com pernada forte (candle
                >= 1,5x a media); entrada na borda do ultimo FVG da pernada. (backtest_ob)
     MSS+OB   : mesmo MSS; entrada na abertura do ultimo candle contrario antes da pernada.
     BPR      : mesmo MSS; o FVG da pernada de reversao sobrepoe um FVG contrario da pernada
                do movimento (ate 30 candles antes do extremo); entrada na borda da
                sobreposicao.
     Risk     : sem MSS. Depois do sweep, o preco toca um FVG ainda aberto do outro lado do
                nivel (de hoje ou do dia anterior) no sentido da reversao; entra no toque,
                stop alem da borda oposta do FVG (definicao da Fase 4, setup_vista.risk_entry).
  Stop       = extremo da pernada + 1 tick (MSS) / borda oposta do FVG + 1 tick (Risk).
  Gestao     = alvo no proximo swing nao varrido do outro lado; zero a zero em 1R, depois
               trailing atras dos swings de 1 min (setup_vista.gerir). Saida ate 12:00
               (fim da tela do operador). Custo 10 pts. Stop e alvo no mesmo candle = stop.
  Janelas    = entrada 09:00-11:29 e so 10:00-11:29 (a regra atual do operador). MSS ate 11:14.
  1 trade por dia por gatilho: o primeiro que executa. "Qualquer" = o primeiro dos quatro.

Comparacoes: o mesmo gatilho contra o movimento SEM exigir o sweep, e todo gatilho da
janela sem condicao nenhuma (base).
Amostra: so existe 1 min de abr-set/2026 (5 meses). Nao ha como confirmar em 5 anos: os
gatilhos precisam do 1 min.
"""

import statistics as st
from collections import defaultdict

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

sv = hl.sv
H = bq.hm
MOVIMENTO = 800
JANELA_SWEEP = 30
FIM_TELA = H("12:00")


def gerir_ate_12(bs, i_fill, lado, entrada, stop, alvo):
    """setup_vista.gerir com saida as 12:00 em vez de 17:50."""
    risco = abs(entrada - stop)
    be = False
    fim = sv.idx(bs, FIM_TELA)
    for i in range(i_fill, min(fim, len(bs))):
        b = bs[i]
        if (b[3] <= stop) if lado == 1 else (b[2] >= stop):
            return (stop - entrada) * lado - sv.CUSTO, "stop", i
        if alvo is not None and ((b[2] >= alvo) if lado == 1 else (b[3] <= alvo)):
            return (alvo - entrada) * lado - sv.CUSTO, "alvo", i
        if not be and ((b[2] >= entrada + risco) if lado == 1 else (b[3] <= entrada - risco)):
            be, stop = True, entrada
        if be and i - sv.K_TRAIL > i_fill:
            j = i - sv.K_TRAIL
            viz = bs[j - sv.K_TRAIL:j] + bs[j + 1:j + 1 + sv.K_TRAIL]
            if lado == 1 and all(bs[j][3] < v[3] for v in viz):
                stop = max(stop, bs[j][3] - sv.TICK)
            if lado == -1 and all(bs[j][2] > v[2] for v in viz):
                stop = min(stop, bs[j][2] + sv.TICK)
    ult = bs[min(fim, len(bs)) - 1]
    return (ult[4] - entrada) * lado - sv.CUSTO, "12:00", min(fim, len(bs)) - 1


def trade(bs, i_ent, lado, entrada, stop, **extra):
    alvo = sv.alvo_liquidez(bs, i_ent, lado, entrada)
    pts, motivo, _ = gerir_ate_12(bs, i_ent, lado, entrada, stop, alvo)
    risco = abs(entrada - stop)
    return dict(lado=lado, pts=pts, r=pts / risco, risco=risco, motivo=motivo, t_ent=bs[i_ent][0], **extra)


def movimento(bs):
    """(direcao, indice em que chegou aos 800) ou None."""
    o09 = bs[0][1]
    for i, b in enumerate(bs):
        if b[0] >= FIM_TELA:
            return None
        sobe, cai = b[2] - o09 >= MOVIMENTO, o09 - b[3] >= MOVIMENTO
        if sobe and cai:
            return None
        if sobe or cai:
            return (1 if sobe else -1), i
    return None


def niveis_liquidez(ant, direcao):
    """PDH/PDL + swings de 15 min do dia anterior intactos ate o fechamento, no lado do movimento."""
    b15 = p.agrega15(ant)
    topos, fundos = sv.fractais(b15, 2)
    if direcao == 1:
        sw = [b15[i][2] for i in topos if all(x[2] < b15[i][2] for x in b15[i + 1:])]
        return sorted(set(sw + [max(b[2] for b in ant)]))
    sw = [b15[i][3] for i in fundos if all(x[3] > b15[i][3] for x in b15[i + 1:])]
    return sorted(set(sw + [min(b[3] for b in ant)]))


def sweeps(bs, niveis, direcao):
    """Indices dos minutos em que cada nivel foi passado pela primeira vez."""
    out = []
    for n in niveis:
        i = next((k for k, b in enumerate(bs) if b[0] < FIM_TELA and ((b[2] > n) if direcao == 1 else (b[3] < n))), None)
        if i is not None:
            out.append((i, n))
    return sorted(out)


def gatilhos_mss(bs):
    """Todo MSS com pernada forte, com as entradas FVG, OB e BPR (mesma logica de backtest_ob)."""
    out = []
    vistos = set()
    i_ini, i_fim = sv.idx(bs, H("09:05")), sv.idx(bs, H("11:15"))
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
            media = st.mean(hl.corpo(b) for b in base) or 1
            if max(hl.corpo(b) for b in bs[i_org:m + 1]) < 1.5 * media:
                continue
            vistos.add((i_org, alta))
            lado = 1 if alta else -1
            stop = extremo - sv.TICK if alta else extremo + sv.TICK
            gaps = sv.fvgs(bs, i_org + 1, m + 1, alta=alta)
            entradas = {}
            if gaps:
                g_i, g_lo, g_hi = gaps[-1]
                entradas["MSS+FVG"] = ((g_hi if alta else g_lo), g_i + 1)
                # BPR: FVG contrario na pernada do movimento que sobrepoe o FVG da reversao
                contra = sv.fvgs(bs, max(2, i_org - 30), i_org + 1, alta=not alta)
                for c_i, c_lo, c_hi in reversed(contra):
                    lo, hi = max(g_lo, c_lo), min(g_hi, c_hi)
                    if lo < hi:
                        entradas["BPR"] = ((hi if alta else lo), g_i + 1)
                        break
            ob = None
            for k in range(i_org, i_ref - 1, -1):
                b = bs[k]
                if (b[4] < b[1]) if alta else (b[4] > b[1]):
                    ob = b[1]
                    break
            if ob is not None:
                entradas["MSS+OB"] = (ob, m + 1)
            lim = sv.idx(bs, hl.mais(bs[m][0], 30))
            for nome, (borda, desde) in entradas.items():
                if (borda <= stop) if alta else (borda >= stop):
                    continue
                for f in range(desde, min(lim, len(bs))):
                    x = bs[f]
                    if (x[3] <= stop) if alta else (x[2] >= stop):
                        break
                    if (x[3] <= borda) if alta else (x[2] >= borda):
                        out.append(trade(bs, f, lado, borda, stop, gatilho=nome, i_mss=m, t_mss=bs[m][0]))
                        break
    return out


def risk_entries(bs, ant, sws, direcao, i800):
    """Depois de um sweep, toque num FVG aberto do outro lado do nivel, no sentido da reversao."""
    lado = -direcao
    junto = ant + bs
    off = len(ant)
    alta = lado == 1
    todos = sv.fvgs(junto, 2, len(junto) - 1, alta)
    out = []
    for i_sw, nivel in sws:
        fim = sv.idx(bs, H("11:30"))
        for s in range(max(i_sw, i800), fim):
            b = bs[s]
            gs = [g for g in todos if g[0] < off + i_sw
                  and ((g[2] < nivel) if alta else (g[1] > nivel))
                  and ((min(x[3] for x in junto[g[0] + 1:off + s]) > g[2]) if alta
                       else (max(x[2] for x in junto[g[0] + 1:off + s]) < g[1]))]
            for g_i, g_lo, g_hi in gs:
                borda, stop = (g_hi, g_lo - sv.TICK) if alta else (g_lo, g_hi + sv.TICK)
                if (b[3] <= borda) if alta else (b[2] >= borda):
                    if (b[3] <= stop) if alta else (b[2] >= stop):
                        continue
                    out.append(trade(bs, s, lado, borda, stop, gatilho="Risk", i_mss=s, t_mss=b[0], i_sw=i_sw))
                    return out
    return out


def main():
    dias = bq.carregar()
    o = sorted(dias)
    meio = o[len(o) // 2]
    janelas = {"09:00-11:29": (H("09:00"), H("11:30")), "10:00-11:29": (H("10:00"), H("11:30"))}
    NOMES = ("MSS+FVG", "MSS+OB", "BPR", "Risk", "Qualquer")
    g = defaultdict(list)
    n_mov = n_sweep = 0
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias[d], H("09:00"), H("17:51"))
        ant = bq.entre(dias[o[kd - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300 or bs[0][0] > H("09:05") or not ant:
            continue
        gs = gatilhos_mss(bs)
        for x in gs:
            for jn, (a, b) in janelas.items():
                if a <= x["t_ent"] < b:
                    g[("base", jn, x["gatilho"])].append(dict(x, data=d))
        mv = movimento(bs)
        if not mv:
            continue
        n_mov += 1
        direcao, i800 = mv
        sws = sweeps(bs, niveis_liquidez(ant, direcao), direcao)
        if sws:
            n_sweep += 1
        contra = [x for x in gs if x["lado"] == -direcao and x["i_mss"] >= i800]
        com_sweep = [x for x in contra if any(i < x["i_mss"] <= i + JANELA_SWEEP for i, _ in sws)]
        risk = risk_entries(bs, ant, sws, direcao, i800)
        for jn, (a, b) in janelas.items():
            for rotulo, lista in (("V sem exigir sweep", contra), ("V + sweep", com_sweep + risk)):
                primeiros = {}
                for x in sorted(lista, key=lambda z: z["t_ent"]):
                    if a <= x["t_ent"] < b and x["gatilho"] not in primeiros:
                        primeiros[x["gatilho"]] = x
                for nome, x in primeiros.items():
                    g[(rotulo, jn, nome)].append(dict(x, data=d))
                if primeiros:
                    x = min(primeiros.values(), key=lambda z: z["t_ent"])
                    g[(rotulo, jn, "Qualquer")].append(dict(x, data=d))

    import csv
    with open("setup_v_sweep_trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["grupo", "janela", "gatilho", "data", "lado", "t_mss", "t_ent", "risco", "pts", "r", "motivo"])
        for (rot, jn, nome), xs in sorted(g.items()):
            if rot == "base":
                continue
            for x in xs:
                w.writerow([rot, jn, nome, x["data"], "compra" if x["lado"] == 1 else "venda", x["t_mss"], x["t_ent"],
                            round(x["risco"]), round(x["pts"]), f"{x['r']:.2f}", x["motivo"]])
    print(f"WIN 1 min, {len(o) - 1} pregoes (abr-set/2026). Movimento de {MOVIMENTO} pts: {n_mov} dias; "
          f"com sweep de PDH/PDL ou swing 15 min do dia anterior no lado do movimento: {n_sweep} dias.\n")
    for jn in janelas:
        print(f"==== Entrada {jn} ====")
        for rotulo in ("V + sweep", "V sem exigir sweep", "base"):
            print(f"  {rotulo}{'  (todo gatilho da janela, qualquer lado)' if rotulo == 'base' else ''}:")
            for nome in NOMES:
                x = g[(rotulo, jn, nome)]
                if rotulo == "base" and nome in ("Risk", "Qualquer"):
                    continue
                linha(f"    {nome}", x, meio)
        print()


def linha(rot, x, meio):
    n = len(x)
    if n < 2:
        print(f"{rot:<14} n={n:3d}")
        return
    rs = [t["r"] for t in x]
    mu = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5
    a = [t["r"] for t in x if t["data"] <= meio]
    b = [t["r"] for t in x if t["data"] > meio]
    ac = sum(t["pts"] > 0 for t in x) / n
    print(f"{rot:<14} n={n:3d}  acerto {ac:4.0%}  media {mu:+.2f}R (t={mu / se if se else 0:+.1f})  "
          f"metades {st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}  "
          f"stop med {st.median(t['risco'] for t in x):4.0f}  "
          f"R$ {sum(t['pts'] for t in x) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))


if __name__ == "__main__":
    main()
