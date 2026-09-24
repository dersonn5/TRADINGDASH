"""A estrutura da barra das 10 no WIN, medida em R. Grafico de 1 min.

Hipotese do operador (22/09/2026):
  Da abertura ate as 10:00 o indice forma uma micro tendencia. As 10:00 ele faz
  algo: reverte a barra das 10, ou cria uma maxima/minima que, se rompida, da um
  trade - de continuacao ou de reversao.

Definicoes (confirmadas pelo operador antes de rodar):
  Micro tendencia = direcao de [H-60, H): fechamento do ultimo candle - abertura do primeiro.
  Barra de decisao = o candle de 1 min das H:00 (maxima Hb, minima Lb).
  Rompimento  = o primeiro lado da barra que o preco passar, de H:01 ate H+30.
                A favor da micro tendencia = CONTINUIDADE; contra = REVERSAO.
  Gatilho     = MSS no sentido do rompimento, com fechamento a partir do rompimento
                e ate H+60: candle fecha alem do ultimo swing contrario (fractal 2).
                Pernada com candle de corpo >= 1,5x a media dos 15 anteriores.
  Entrada     = borda do FVG da pernada (qualquer tamanho), ate H+90.
  Stop        = extremo da pernada (swing de origem) + 1 tick.

Resultado, em R (R = distancia entrada-stop):
  MFE         = o quanto o preco andou a favor, em R, ate tocar o stop ou 17:50.
                "Chegou a kR antes de -1R" = MFE >= k.
  Gestao      = alvo no proximo BSL/SSL nao varrido + trailing (zero em 1R, depois
                swings), a mesma do setup_vista. Custo 10 pts.

Controle: a mesma estrutura com a barra das 11, 13 e 14.
"""

import statistics as st
import sys
from collections import Counter

import backtest_quarters as bq
import setup_vista as sv
from gatilho_vista import corpo
from ny_1030 import mais

H = bq.hm
K_SW = 2
MULT = 1.5
NIVEIS_R = (2, 3, 5, 8, 10)


def mfe_em_r(bs, i_fill, lado, entrada, stop):
    """Maximo a favor, em R, antes do stop (stop checado primeiro em cada candle)."""
    r = abs(entrada - stop)
    melhor = 0.0
    fim = sv.idx(bs, H("17:50"))
    for i in range(i_fill, min(fim, len(bs))):
        b = bs[i]
        if (b[3] <= stop) if lado == 1 else (b[2] >= stop):
            return melhor
        fav = (b[2] - entrada) if lado == 1 else (entrada - b[3])
        melhor = max(melhor, fav / r)
    return melhor


def gatilho_apos(bs, i_ini, i_fim_mss, i_fim_ent, alta):
    """Primeiro MSS+FVG no sentido pedido, com MSS entre i_ini e i_fim_mss."""
    for m in range(i_ini, min(i_fim_mss, len(bs))):
        topos, fundos = sv.fractais(bs[:m], K_SW)
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
        base = bs[max(0, i_org - 15):i_org]
        if len(base) < 5:
            continue
        media = st.mean(corpo(b) for b in base) or 1
        if max(corpo(b) for b in bs[i_org:m + 1]) < MULT * media:
            continue
        gaps = sv.fvgs(bs, i_org + 1, m + 1, alta=alta)
        if not gaps:
            continue
        g_i, g_lo, g_hi = gaps[-1]
        borda = g_hi if alta else g_lo
        stop = extremo - sv.TICK if alta else extremo + sv.TICK
        for f in range(g_i + 1, min(i_fim_ent, len(bs))):
            x = bs[f]
            if (x[3] <= stop) if alta else (x[2] >= stop):
                return None
            if (x[3] <= borda) if alta else (x[2] >= borda):
                return f, borda, stop, bs[m][0]
        return None
    return None


def analisar(bs, hora):
    t0 = H(hora)
    antes = bq.entre(bs, mais(t0, -60), t0)
    i0 = sv.idx(bs, t0)
    if len(antes) < 50 or i0 >= len(bs) or bs[i0][0] != t0:
        return None
    tend = antes[-1][4] - antes[0][1]
    if tend == 0:
        return None
    hb, lb = bs[i0][2], bs[i0][3]
    i_brk_fim = sv.idx(bs, mais(t0, 31))
    lado_brk = None
    for i in range(i0 + 1, min(i_brk_fim, len(bs))):
        cima, baixo = bs[i][2] > hb, bs[i][3] < lb
        if cima and baixo:
            break  # candle rompe os dois lados: ambiguo, descarta o dia
        if cima or baixo:
            lado_brk, i_brk = (1 if cima else -1), i
            break
    if lado_brk is None:
        return {"tipo": "sem rompimento"}
    tipo = "continuidade" if (lado_brk > 0) == (tend > 0) else "reversao"
    g = gatilho_apos(bs, i_brk, sv.idx(bs, mais(t0, 61)), sv.idx(bs, mais(t0, 91)), lado_brk > 0)
    if not g:
        return {"tipo": tipo, "trade": False, "tend": abs(tend)}
    f, entrada, stop, t_mss = g
    mfe = mfe_em_r(bs, f, lado_brk, entrada, stop)
    alvo = sv.alvo_liquidez(bs, f, lado_brk, entrada)
    pts, mot, _ = sv.gerir(bs, f, lado_brk, entrada, stop, alvo)
    return {"tipo": tipo, "trade": True, "tend": abs(tend), "mfe": mfe, "pts": pts,
            "r": pts / abs(entrada - stop), "risco": abs(entrada - stop), "motivo": mot,
            "t_ent": bs[f][0], "lado": lado_brk}


def linha_r(nome, ts):
    if not ts:
        print(f"  {nome:<24} sem trades")
        return
    n = len(ts)
    probs = "  ".join(f"{k}R {sum(t['mfe'] >= k for t in ts) / n:4.0%}" for k in NIVEIS_R)
    pts = [t["pts"] for t in ts]
    print(f"  {nome:<24} n={n:3d} | chega antes de -1R: {probs} | gestao: media {sum(pts) / n:+5.0f} pts, "
          f"{sum(t['r'] for t in ts) / n:+.2f}R, total R$ {sum(pts) * 0.2:+.0f}/ct")


def main():
    dias = bq.carregar()
    ordem = sorted(dias)
    print(f"WIN 1 min, {len(ordem)} pregoes ({ordem[0]} a {ordem[-1]})\n")
    for hora in ("10:00", "11:00", "13:00", "14:00"):
        rs = {}
        for d in ordem:
            bs = bq.entre(dias[d], H("09:00"), H("17:51"))
            if len(bs) < 300:
                continue
            r = analisar(bs, hora)
            if r:
                rs[d] = r
        tipos = Counter(r["tipo"] for r in rs.values())
        marca = "   <- barra das 10" if hora == "10:00" else ""
        print(f"== Barra das {hora[:2]}{marca} | {len(rs)} dias | rompimento: "
              f"continuidade {tipos['continuidade']}, reversao {tipos['reversao']}, "
              f"sem rompimento {tipos['sem rompimento']}")
        trades = [r for r in rs.values() if r.get("trade")]
        linha_r("todos", trades)
        linha_r("continuidade", [t for t in trades if t["tipo"] == "continuidade"])
        linha_r("reversao", [t for t in trades if t["tipo"] == "reversao"])
        if hora == "10:00":
            meio = ordem[len(ordem) // 2]
            linha_r("1a metade", [r for d, r in rs.items() if r.get("trade") and d <= meio])
            linha_r("2a metade", [r for d, r in rs.items() if r.get("trade") and d > meio])
            tt = sorted(t["tend"] for t in trades)
            if tt:
                c1, c2 = tt[len(tt) // 3], tt[2 * len(tt) // 3]
                linha_r(f"micro tend. < {c1:.0f}", [t for t in trades if t["tend"] < c1])
                linha_r(f"micro tend. {c1:.0f}-{c2:.0f}", [t for t in trades if c1 <= t["tend"] <= c2])
                linha_r(f"micro tend. > {c2:.0f}", [t for t in trades if t["tend"] > c2])
        print()


if __name__ == "__main__":
    main()
