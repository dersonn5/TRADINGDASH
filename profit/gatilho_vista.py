"""Gatilho limpo na janela do a vista (10:00-10:30). WIN, 1 min.

Ideia do operador (22/09/2026): a janela nao e o gatilho, e o contexto. Durante
10:00-10:30 o a vista pode entregar um gatilho limpo de continuacao OU de
reversao - ou nao entregar nada. Quando entrega, a entrada e a de sempre.

Versao 1 - somente MSS + FVG (os outros gatilhos entram depois, um a um):

  Estrutura   = swings de 1 min, fractal de K_SW candles de cada lado.
  MSS         = candle que FECHA alem do ultimo swing contrario confirmado.
                Compra: fecha acima do ultimo topo. Venda: fecha abaixo do ultimo fundo.
                O fechamento do MSS tem que ocorrer entre 10:00 e 10:30.
  Deslocamento= na pernada (do swing de origem ate o candle do MSS), pelo menos um
                candle com CORPO >= MULT x a media dos corpos dos 15 candles anteriores
                a pernada. E o "limpo".
  FVG         = gap de 3 candles dentro da pernada, incluindo o candle seguinte ao
                MSS. Qualquer tamanho. Vale o ultimo formado.
  Entrada     = ordem limitada na BORDA do FVG (a primeira que o preco toca ao voltar),
                valida ate LIMITE_ENTRADA. Cancela se o preco tocar o stop antes.
  Stop        = extremo da pernada (o swing de origem) + 1 tick.
  Alvo        = proximo swing (fractal K_ALVO) do lado oposto ainda nao varrido.
  Trailing    = zero a zero em 1R; depois o stop segue os swings de 1 min.
  Saida       = stop, alvo ou 17:50. 1 trade por dia: o primeiro que executar.
  Custo       = 10 pts por trade. Conflito no mesmo candle = stop.
"""

import csv
import datetime as dt
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import backtest_quarters as bq
import setup_vista as sv

K_SW = 2
K_ALVO = 3
MULT = 1.5
JANELA = ("10:00", "10:30")
LIMITE_ENTRADA = "11:00"
H = bq.hm


def corpo(b):
    return abs(b[4] - b[1])


def achar(bs):
    i_ini, i_fim = sv.idx(bs, H(JANELA[0])), sv.idx(bs, H(JANELA[1]))
    i_lim = sv.idx(bs, H(LIMITE_ENTRADA))
    for m in range(i_ini, i_fim):
        topos, fundos = sv.fractais(bs[:m], K_SW)
        for alta in (True, False):
            ref_list = topos if alta else fundos
            if not ref_list:
                continue
            i_ref = ref_list[-1]
            nivel = bs[i_ref][2] if alta else bs[i_ref][3]
            if not ((bs[m][4] > nivel) if alta else (bs[m][4] < nivel)):
                continue
            # pernada: do swing de origem (extremo oposto entre i_ref e m) ate o MSS
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
                continue  # deslocamento fraco
            gaps = sv.fvgs(bs, i_org + 1, m + 1, alta=alta)
            if not gaps:
                continue
            g_i, g_lo, g_hi = gaps[-1]
            borda = g_hi if alta else g_lo
            stop = extremo - sv.TICK if alta else extremo + sv.TICK
            lado = 1 if alta else -1
            for f in range(g_i + 1, min(i_lim, len(bs))):
                x = bs[f]
                if (x[3] <= stop) if alta else (x[2] >= stop):
                    break
                if (x[3] <= borda) if alta else (x[2] >= borda):
                    alvo = sv.alvo_liquidez(bs, f, lado, borda)
                    pts, mot, i_out = sv.gerir(bs, f, lado, borda, stop, alvo)
                    return dict(lado=lado, t_mss=bs[m][0], nivel=nivel, t_org=bs[i_org][0],
                                extremo=extremo, fvg=(g_lo, g_hi), t_fvg=bs[g_i][0],
                                t_ent=x[0], entrada=borda, stop=stop, alvo=alvo, pts=pts,
                                motivo=mot, t_out=bs[i_out][0], risco=abs(borda - stop),
                                desloc=round(max(corpo(b) for b in bs[i_org:m + 1]) / media, 2))
            break
    return None


def resumo(nome, ts):
    if not ts:
        print(f"{nome}: sem trades")
        return
    pts = [t["pts"] for t in ts]
    n = len(pts)
    print(f"{nome}: n={n:3d}  acerto {sum(1 for p in pts if p > 0) / n:4.0%}  "
          f"media {sum(pts) / n:+6.0f} pts  total {sum(pts) * 0.2:+7.0f} R$/contrato  "
          f"erro padrao {st.pstdev(pts) / n ** 0.5:5.0f}")


def main():
    dias = bq.carregar()
    ordem = sorted(dias)
    ts = []
    for d in ordem:
        bs = bq.entre(dias[d], H("09:00"), H("17:51"))
        if len(bs) < 300:
            continue
        t = achar(bs)
        if t:
            t["data"] = d
            ts.append(t)
    corte = ordem[len(ordem) // 2]
    print(f"{len(ordem)} pregoes, {ordem[0]} a {ordem[-1]}\n")
    resumo("TODOS               ", ts)
    resumo(f"1a metade (ate {corte})", [t for t in ts if t["data"] <= corte])
    resumo(f"2a metade (apos {corte})", [t for t in ts if t["data"] > corte])
    print("\nsaidas:", dict(Counter(t["motivo"] for t in ts)))
    r = sorted(t["risco"] for t in ts)
    print(f"risco por trade: mediana {r[len(r) // 2]:.0f} | p90 {r[int(.9 * len(r))]:.0f} | max {r[-1]:.0f}")

    destino = Path(__file__).parent / "gatilho_vista_trades.csv"
    with destino.open("w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "lado", "mss", "nivel", "origem", "extremo", "fvg", "entrada_hora",
                    "entrada", "stop", "risco", "alvo", "desloc_x_media", "saida", "motivo", "pts"])
        for t in ts:
            w.writerow([t["data"], "compra" if t["lado"] == 1 else "venda", t["t_mss"].strftime("%H:%M"),
                        int(t["nivel"]), t["t_org"].strftime("%H:%M"), int(t["extremo"]),
                        f"{int(t['fvg'][0])}-{int(t['fvg'][1])}", t["t_ent"].strftime("%H:%M"),
                        int(t["entrada"]), int(t["stop"]), int(t["risco"]),
                        "" if t["alvo"] is None else int(t["alvo"]), t["desloc"],
                        t["t_out"].strftime("%H:%M"), t["motivo"], int(t["pts"])])
    print(f"\ntrade a trade: {destino.name}")


if __name__ == "__main__":
    main()
