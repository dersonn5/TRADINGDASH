"""Fase 4 do Estudo_Reversao_Abertura_Vista: a regra do operador, WIN 1 min.

Regra (escrita pelo operador em 22/09/2026, com as definicoes confirmadas):

MODELO PRINCIPAL - manipulacao do a vista + MSS + FVG
  Referencia  = topos e fundos de SWING da 1a hora (09:00-09:59), fractal de
                K_REF candles de cada lado, ainda nao varridos ate 10:00.
  Manipulacao = entre 10:00 e 10:29, o preco passa de um desses swings.
                Varreu topo -> setup de VENDA. Varreu fundo -> setup de COMPRA.
  Extremo     = ponto mais longe da manipulacao ate o MSS.
  MSS         = um candle FECHA alem do ultimo swing contrario (fractal K_MSS)
                formado antes do extremo. Ate 11:00.
  FVG         = gap de 3 candles na pernada do extremo ate o MSS (inclusive o
                candle seguinte ao MSS). Vale o ultimo formado.
  Entrada     = ordem limitada na borda do FVG; executa quando o preco volta a
                ela. Cancelada se o preco passar do stop antes, ou apos 11:30.
  Stop        = extremo da manipulacao + 1 tick.

RISK ENTRY - FVG da perna anterior
  A 1a hora deixou um FVG ainda nao tocado. Entre 10:00 e 10:29 o a vista varre
  um swing da 1a hora e, depois disso, toca esse FVG do lado de la:
    varreu FUNDO e desceu ate um FVG de ALTA abaixo dele -> COMPRA no toque.
    varreu TOPO  e subiu  ate um FVG de BAIXA acima dele -> VENDA no toque.
  Sem MSS. Stop alem da borda oposta do FVG + 1 tick (o "fundo varrido" fica
  do lado errado da entrada, por isso o stop e o do proprio FVG).

AMBOS
  Alvo     = proximo swing (fractal K_REF) do lado oposto, ainda nao varrido,
             formado antes da entrada. Sem nenhum, so trailing.
  Trailing = ao andar 1R a favor, stop no preco de entrada; depois o stop segue
             cada novo swing de 1 min (fractal K_TRAIL) a favor.
  Saida    = stop, alvo, ou 17:50 ("ate o mercado me tirar", mas day trade).
  1 trade por dia: o primeiro que executar.
  Custo    = CUSTO pts por trade. Conflito no mesmo candle = stop (conservador).

Amostra: os ultimos N_VALIDACAO pregoes ficam FORA; so sao rodados quando o
operador aprovar a regra olhando os trades.
"""

import csv
import datetime as dt
import sys
from pathlib import Path

import backtest_quarters as bq
from ny_1030 import mais

TICK = 5
CUSTO = 10
K_REF = 3
K_MSS = 2
K_TRAIL = 2
N_VALIDACAO = 30
H = bq.hm


def fractais(bs, k):
    """(indice, preco) de topos e fundos de swing, confirmados com k candles de cada lado."""
    topos, fundos = [], []
    for i in range(k, len(bs) - k):
        viz = bs[i - k:i] + bs[i + 1:i + 1 + k]
        if all(bs[i][2] > v[2] for v in viz):
            topos.append(i)
        if all(bs[i][3] < v[3] for v in viz):
            fundos.append(i)
    return topos, fundos


def idx(bs, t):
    for i, b in enumerate(bs):
        if b[0] >= t:
            return i
    return len(bs)


def fvgs(bs, i0, i1, alta):
    """FVGs completados entre i0 e i1 (candle do meio = i-1). Retorna (i, fundo, topo)."""
    out = []
    for i in range(max(i0, 2), min(i1, len(bs) - 1) + 1):
        if alta and bs[i - 2][2] < bs[i][3]:
            out.append((i, bs[i - 2][2], bs[i][3]))
        if not alta and bs[i - 2][3] > bs[i][2]:
            out.append((i, bs[i][2], bs[i - 2][3]))
    return out


def gerir(bs, i_fill, lado, entrada, stop, alvo):
    """Gestao a partir do candle da execucao. Retorna (pts, motivo, i_saida)."""
    risco = abs(entrada - stop)
    be = False
    fim = idx(bs, H("17:50"))
    for i in range(i_fill, min(fim, len(bs))):
        b = bs[i]
        # stop primeiro (conservador)
        if (b[3] <= stop) if lado == 1 else (b[2] >= stop):
            return (stop - entrada) * lado - CUSTO, ("zero" if be and stop == entrada else
                                                     "trailing" if be else "stop"), i
        if alvo is not None and ((b[2] >= alvo) if lado == 1 else (b[3] <= alvo)):
            return (alvo - entrada) * lado - CUSTO, "alvo", i
        # atualiza o stop para o proximo candle
        if not be and ((b[2] >= entrada + risco) if lado == 1 else (b[3] <= entrada - risco)):
            be, stop = True, entrada
        if be and i - K_TRAIL > i_fill:
            j = i - K_TRAIL  # candidato a swing confirmado agora
            viz = bs[j - K_TRAIL:j] + bs[j + 1:j + 1 + K_TRAIL]
            if lado == 1 and all(bs[j][3] < v[3] for v in viz):
                stop = max(stop, bs[j][3] - TICK)
            if lado == -1 and all(bs[j][2] > v[2] for v in viz):
                stop = min(stop, bs[j][2] + TICK)
    ult = bs[min(fim, len(bs)) - 1]
    return (ult[4] - entrada) * lado - CUSTO, "17:50", min(fim, len(bs)) - 1


def alvo_liquidez(bs, i_ent, lado, entrada):
    topos, fundos = fractais(bs[:i_ent], K_REF)
    cand = []
    if lado == -1:
        for i in fundos:
            nivel = bs[i][3]
            if nivel < entrada and min(b[3] for b in bs[i + 1:i_ent]) > nivel:
                cand.append(nivel)
        return max(cand) if cand else None
    for i in topos:
        nivel = bs[i][2]
        if nivel > entrada and max(b[2] for b in bs[i + 1:i_ent]) < nivel:
            cand.append(nivel)
    return min(cand) if cand else None


def referencias(bs):
    """Swings da 1a hora ainda nao varridos ate 10:00."""
    i10 = idx(bs, H("10:00"))
    h1 = bs[:i10]
    topos, fundos = fractais(bs[:i10 + K_REF], K_REF)
    topos = [i for i in topos if i < i10 and max((b[2] for b in bs[i + 1:i10]), default=-1) < bs[i][2]]
    fundos = [i for i in fundos if i < i10 and min((b[3] for b in bs[i + 1:i10]), default=1e12) > bs[i][3]]
    return i10, h1, topos, fundos


def modelo_principal(bs):
    i10, h1, topos, fundos = referencias(bs)
    i1030, i11, i1130 = idx(bs, H("10:30")), idx(bs, H("11:00")), idx(bs, H("11:30"))
    for s in range(i10, i1030):
        b = bs[s]
        venda = any(b[2] > bs[i][2] for i in topos)
        compra = any(b[3] < bs[i][3] for i in fundos)
        if venda == compra:  # nenhum, ou os dois no mesmo candle
            continue
        lado = -1 if venda else 1
        nivel = (max(bs[i][2] for i in topos if b[2] > bs[i][2]) if venda
                 else min(bs[i][3] for i in fundos if b[3] < bs[i][3]))
        # acompanha o extremo ate o MSS
        i_ext = s
        for m in range(s, min(i11, len(bs))):
            if (bs[m][2] > bs[i_ext][2]) if venda else (bs[m][3] < bs[i_ext][3]):
                i_ext = m
            t_, f_ = fractais(bs[:i_ext], K_MSS)
            orig = f_ if venda else t_
            if not orig:
                continue
            ref = bs[orig[-1]][3] if venda else bs[orig[-1]][2]
            if m > i_ext and ((bs[m][4] < ref) if venda else (bs[m][4] > ref)):
                # o candle que varre costuma ser o do MEIO do FVG, entao a busca comeca em i_ext+1
                gaps = fvgs(bs, i_ext + 1, m + 1, alta=not venda)
                if not gaps:
                    return None
                g_i, g_lo, g_hi = gaps[-1]
                borda = g_lo if venda else g_hi
                extremo = bs[i_ext][2] if venda else bs[i_ext][3]
                stop = extremo + TICK if venda else extremo - TICK
                for f in range(g_i + 1, min(i1130, len(bs))):
                    x = bs[f]
                    if (x[2] >= stop) if venda else (x[3] <= stop):
                        return None
                    if (x[2] >= borda) if venda else (x[3] <= borda):
                        alvo = alvo_liquidez(bs, f, lado, borda)
                        pts, mot, i_out = gerir(bs, f, lado, borda, stop, alvo)
                        return dict(modelo="principal", lado=lado, sweep=bs[s][0], nivel=nivel,
                                    t_ext=bs[i_ext][0], extremo=extremo, t_mss=bs[m][0], mss=ref,
                                    fvg=(g_lo, g_hi), t_fvg=bs[g_i][0], t_ent=x[0], entrada=borda,
                                    stop=stop, alvo=alvo, pts=pts, motivo=mot, t_out=bs[i_out][0],
                                    risco=abs(borda - stop))
                return None
        return None
    return None


def risk_entry(bs):
    i10, h1, topos, fundos = referencias(bs)
    i1030 = idx(bs, H("10:30"))
    abertas_alta = [g for g in fvgs(bs, 2, i10 - 1, True)
                    if min((b[3] for b in bs[g[0] + 1:i10]), default=1e12) > g[2]]
    abertas_baixa = [g for g in fvgs(bs, 2, i10 - 1, False)
                     if max((b[2] for b in bs[g[0] + 1:i10]), default=-1) < g[1]]
    varreu_fundo = varreu_topo = None
    for s in range(i10, i1030):
        b = bs[s]
        if varreu_fundo is None:
            fs = [bs[i][3] for i in fundos if b[3] < bs[i][3]]
            if fs:
                varreu_fundo = min(fs)
        if varreu_topo is None:
            ts = [bs[i][2] for i in topos if b[2] > bs[i][2]]
            if ts:
                varreu_topo = max(ts)
        if varreu_fundo is not None:
            for g_i, g_lo, g_hi in abertas_alta:
                if g_hi < varreu_fundo and b[3] <= g_hi:
                    stop = g_lo - TICK
                    if b[3] <= stop:
                        return None
                    alvo = alvo_liquidez(bs, s, 1, g_hi)
                    pts, mot, i_out = gerir(bs, s, 1, g_hi, stop, alvo)
                    return dict(modelo="risk", lado=1, sweep=b[0], nivel=varreu_fundo, t_ext=b[0],
                                extremo=b[3], t_mss=None, mss=None, fvg=(g_lo, g_hi), t_fvg=bs[g_i][0],
                                t_ent=b[0], entrada=g_hi, stop=stop, alvo=alvo, pts=pts, motivo=mot,
                                t_out=bs[i_out][0], risco=abs(g_hi - stop))
        if varreu_topo is not None:
            for g_i, g_lo, g_hi in abertas_baixa:
                if g_lo > varreu_topo and b[2] >= g_lo:
                    stop = g_hi + TICK
                    if b[2] >= stop:
                        return None
                    alvo = alvo_liquidez(bs, s, -1, g_lo)
                    pts, mot, i_out = gerir(bs, s, -1, g_lo, stop, alvo)
                    return dict(modelo="risk", lado=-1, sweep=b[0], nivel=varreu_topo, t_ext=b[0],
                                extremo=b[2], t_mss=None, mss=None, fvg=(g_lo, g_hi), t_fvg=bs[g_i][0],
                                t_ent=b[0], entrada=g_lo, stop=stop, alvo=alvo, pts=pts, motivo=mot,
                                t_out=bs[i_out][0], risco=abs(g_lo - stop))
    return None


def dia(bs):
    bs = bq.entre(bs, H("09:00"), H("17:51"))
    if len(bs) < 300:
        return None
    a, r = modelo_principal(bs), risk_entry(bs)
    trades = [t for t in (a, r) if t]
    return min(trades, key=lambda t: t["t_ent"]) if trades else None


def resumo(nome, ts):
    if not ts:
        print(f"{nome}: sem trades")
        return
    n = len(ts)
    pts = [t["pts"] for t in ts]
    rs = [t["pts"] / t["risco"] for t in ts]
    g = sum(1 for p in pts if p > 0)
    print(f"{nome}: n={n}  acerto {g / n:.0%}  media {sum(pts) / n:+.0f} pts  "
          f"total {sum(pts):+.0f} pts (R$ {sum(pts) * 0.2:+.0f} por contrato)  R medio {sum(rs) / n:+.2f}")


def main():
    dias = bq.carregar()
    ordem = sorted(dias)
    validacao = set(ordem[-N_VALIDACAO:])
    rodar_validacao = "--validacao" in sys.argv
    ts = []
    for d in ordem:
        if d in validacao and not rodar_validacao:
            continue
        t = dia(dias[d])
        if t:
            t["data"] = d
            ts.append(t)
    amostra = [t for t in ts if t["data"] not in validacao]
    print(f"Ajuste: {len(ordem) - N_VALIDACAO} pregoes ({ordem[0]} a {ordem[-N_VALIDACAO - 1]}). "
          f"Validacao guardada: {N_VALIDACAO} pregoes.\n")
    resumo("TODOS (ajuste)", amostra)
    resumo("  modelo principal", [t for t in amostra if t["modelo"] == "principal"])
    resumo("  risk entry", [t for t in amostra if t["modelo"] == "risk"])
    if rodar_validacao:
        resumo("VALIDACAO", [t for t in ts if t["data"] in validacao])

    destino = Path(__file__).parent / "setup_vista_trades.csv"
    with destino.open("w", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "modelo", "lado", "sweep", "nivel_varrido", "extremo", "mss", "fvg",
                    "entrada_hora", "entrada", "stop", "alvo", "saida_hora", "motivo", "pts"])
        for t in ts:
            w.writerow([t["data"], t["modelo"], "compra" if t["lado"] == 1 else "venda",
                        t["sweep"].strftime("%H:%M"), int(t["nivel"]), int(t["extremo"]),
                        "" if t["mss"] is None else f"{t['t_mss'].strftime('%H:%M')} @ {int(t['mss'])}",
                        f"{int(t['fvg'][0])}-{int(t['fvg'][1])} ({t['t_fvg'].strftime('%H:%M')})",
                        t["t_ent"].strftime("%H:%M"), int(t["entrada"]), int(t["stop"]),
                        "" if t["alvo"] is None else int(t["alvo"]), t["t_out"].strftime("%H:%M"),
                        t["motivo"], int(t["pts"])])
    print(f"\ntrade a trade: {destino.name}")


if __name__ == "__main__":
    main()
