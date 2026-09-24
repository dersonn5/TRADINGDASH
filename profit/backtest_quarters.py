"""Backtest das regras da Quarterly Theory no WIN, com o CSV de 1 min do cache do Profit.

Regras fixadas ANTES de olhar os resultados (conversa de 22/09/2026):

R1  Direcao do Q3 contra a manipulacao do Q2.
    Q2 observado = 09:00-09:59. Movimento liquido = close 09:59 - open 09:00.
    Entrada 10:00 (open) CONTRA o movimento do Q2.
    Alvo  = open das 09:00 (a origem do Q2).
    Stop  = extremo do Q2 do lado do movimento (minima se caiu, maxima se subiu).
    Saida por tempo = close 11:29.

R2  Sequencia (10:45-11:07) + captura.
    Pool = o extremo (maxima/minima) do quarto de 90 min ate ali, desde que o
    preco tenha recuado RECUO_MIN pontos ou mais depois dele. Um candle dentro da
    janela que passa desse extremo e o sweep.
    Gatilho = depois do sweep, primeiro candle que FECHA abaixo da minima do
    candle do sweep (topo) / acima da maxima (fundo), ate SAIDA_TEMPO.
    Entrada = close do candle do gatilho.
    Stop    = extremo desde o sweep + 1 tick.
    Alvo    = 2R.
    Saida por tempo = SAIDA_TEMPO.

R2b Mesmo gatilho, mas o extremo varrido NAO teve recuo de RECUO_MIN depois dele
    (extremo novo no meio de uma pernada, sem liquidez parada).

Controle: a regra R2 aplicada a outras janelas de 22 min do dia, cada uma com
saida por tempo 23 min depois do fim da janela. Se a sequencia nao se destacar
das outras janelas, o horario nao acrescenta nada.

Conflito no mesmo candle (alvo e stop): conta como stop. Conservador.
Resultados em pontos de indice. 1 ponto de WIN = R$ 0,20 por contrato.
"""

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

CSV = Path(__file__).parent / "WINFUT_1min.csv"
TICK = 5
RECUO_MIN = 150


def carregar():
    dias = defaultdict(list)
    with CSV.open() as f:
        for r in csv.DictReader(f):
            t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
            dias[t.date()].append((t.time(), float(r["open"]), float(r["high"]),
                                   float(r["low"]), float(r["close"])))
    return dias


def hm(s):
    h, m = s.split(":")
    return dt.time(int(h), int(m))


def entre(barras, ini, fim):
    """Barras com ini <= hora < fim."""
    return [b for b in barras if ini <= b[0] < fim]


def simular(barras_depois, lado, entrada, stop, alvo):
    """lado +1 compra, -1 venda. Retorna resultado em pontos."""
    for _, o, h, l, c in barras_depois:
        if lado == 1:
            bateu_stop, bateu_alvo = l <= stop, h >= alvo
        else:
            bateu_stop, bateu_alvo = h >= stop, l <= alvo
        if bateu_stop:
            return (stop - entrada) * lado, "stop"
        if bateu_alvo:
            return (alvo - entrada) * lado, "alvo"
    if not barras_depois:
        return 0.0, "tempo"
    return (barras_depois[-1][4] - entrada) * lado, "tempo"


# ---------------------------------------------------------------- R1
def r1(dias):
    res = []
    for d, bs in sorted(dias.items()):
        q2 = entre(bs, hm("09:00"), hm("10:00"))
        q3 = entre(bs, hm("10:00"), hm("11:30"))
        if len(q2) < 50 or len(q3) < 80:
            continue
        o2, c2 = q2[0][1], q2[-1][4]
        mov = c2 - o2
        if mov == 0:
            continue
        lado = -1 if mov > 0 else 1
        entrada = q3[0][1]
        alvo = o2
        stop = max(b[2] for b in q2) + TICK if mov > 0 else min(b[3] for b in q2) - TICK
        # Alvo ja ultrapassado na abertura do Q3, ou stop do lado errado: sem trade.
        if (lado == 1 and not (stop < entrada < alvo)) or (lado == -1 and not (alvo < entrada < stop)):
            continue
        pts, como = simular(q3, lado, entrada, stop, alvo)
        risco = abs(entrada - stop)
        res.append((d, lado, pts, como, risco, abs(mov)))
    return res


# ---------------------------------------------------------------- R2
def pools(barras_ate, lado_topo):
    """Topos (ou fundos) seguidos de recuo >= RECUO_MIN, nas barras dadas."""
    out = []
    for i, b in enumerate(barras_ate):
        if lado_topo:
            nivel = b[2]
            recuo = nivel - min((x[3] for x in barras_ate[i + 1:]), default=nivel)
        else:
            nivel = b[3]
            recuo = max((x[2] for x in barras_ate[i + 1:]), default=nivel) - nivel
        if recuo >= RECUO_MIN:
            out.append(nivel)
    return out


def inicio_quarto(t):
    """Inicio do quarto de 90 min que contem t (ancora 07:00), no minimo 09:00."""
    m = t.hour * 60 + t.minute
    ini = 7 * 60 + ((m - 7 * 60) // 90) * 90
    return max(hm("09:00"), dt.time(ini // 60, ini % 60))


def r2_janela(bs, ini, fim, saida, exigir_captura):
    """Um trade por dia por janela: o primeiro que disparar.

    Referencia = barras do quarto de 90 min atual, do inicio dele ate o candle.
    fez_extremo = o candle passa do extremo do quarto ate ali.
    capturou    = alem disso, depois daquele extremo o preco recuou RECUO_MIN
                  ou mais (havia liquidez parada ali, e ela foi varrida).
    """
    janela = entre(bs, ini, fim)
    for sw in janela:
        t = sw[0]
        ref = entre(bs, inicio_quarto(t), t)
        if len(ref) < 5:
            continue
        for topo in (True, False):
            if topo:
                i_ext = max(range(len(ref)), key=lambda i: ref[i][2])
                ext = ref[i_ext][2]
                fez_extremo = sw[2] > ext
                recuo = ext - min(b[3] for b in ref[i_ext:])
            else:
                i_ext = min(range(len(ref)), key=lambda i: ref[i][3])
                ext = ref[i_ext][3]
                fez_extremo = sw[3] < ext
                recuo = max(b[2] for b in ref[i_ext:]) - ext
            if not fez_extremo:
                continue
            capturou = recuo >= RECUO_MIN
            if capturou != exigir_captura:
                continue
            depois = entre(bs, t, saida)[1:]
            extremo = sw[2] if topo else sw[3]
            for j, g in enumerate(depois):
                extremo = max(extremo, g[2]) if topo else min(extremo, g[3])
                if (g[4] < sw[3]) if topo else (g[4] > sw[2]):
                    lado = -1 if topo else 1
                    entrada = g[4]
                    stop = extremo + TICK if topo else extremo - TICK
                    risco = abs(stop - entrada)
                    if risco <= 0:
                        break
                    alvo = entrada + lado * 2 * risco
                    pts, como = simular(depois[j + 1:], lado, entrada, stop, alvo)
                    return (lado, pts, como, risco, pts / risco, t)
                # Sem gatilho ate a saida: este sweep nao vira trade.
            break
    return None


def resumo(nome, trades):
    n = len(trades)
    if n == 0:
        print(f"{nome:<34} sem trades")
        return
    pts = [t[1] for t in trades]
    rs = [t[4] for t in trades]
    ganhos = sum(1 for p in pts if p > 0)
    print(f"{nome:<34} n={n:3d}  acerto={ganhos / n:5.0%}  "
          f"media={sum(pts) / n:+7.1f} pts  total={sum(pts):+8.0f}  R medio={sum(rs) / n:+.2f}")


def main():
    dias = carregar()
    print(f"{len(dias)} pregoes, {min(dias)} a {max(dias)}\n")

    # R1
    t1 = r1(dias)
    print("R1  entrada 10:00 contra o Q2, alvo = abertura 09:00, stop = extremo Q2")
    resumo("R1 todos", [(x[1], x[2], x[3], x[4], x[2] / x[4]) for x in t1])
    med = sorted(x[5] for x in t1)[len(t1) // 2] if t1 else 0
    resumo("R1 Q2 com movimento > mediana", [(x[1], x[2], x[3], x[4], x[2] / x[4]) for x in t1 if x[5] > med])
    como = defaultdict(int)
    for x in t1:
        como[x[3]] += 1
    print(f"    saidas: {dict(como)}   mediana do movimento do Q2: {med:.0f} pts\n")

    # R2 / R2b na sequencia
    seq_ini, seq_fim, seq_saida = hm("10:45"), hm("11:08"), hm("11:30")
    r2 = [x for x in (r2_janela(bs, seq_ini, seq_fim, seq_saida, True) for bs in dias.values()) if x]
    r2b = [x for x in (r2_janela(bs, seq_ini, seq_fim, seq_saida, False) for bs in dias.values()) if x]
    print("Sequencia 10:45-11:07, alvo 2R, saida 11:30")
    resumo("R2  sequencia + captura", r2)
    resumo("R2b sequencia sem captura", r2b)
    print()

    # Controle: mesma regra R2 em outras janelas de ~22 min
    print("Controle: R2 (com captura) em outras janelas, saida 23 min apos o fim")
    janelas = [("09:15", "09:38"), ("09:38", "10:00"), ("10:00", "10:23"), ("10:23", "10:45"),
               ("10:45", "11:08"), ("11:08", "11:30"), ("11:30", "11:53"), ("13:00", "13:23"),
               ("14:08", "14:30"), ("15:00", "15:23"), ("16:00", "16:23")]
    for a, b in janelas:
        fim = hm(b)
        saida = (dt.datetime.combine(dt.date.today(), fim) + dt.timedelta(minutes=23)).time()
        tr = [x for x in (r2_janela(bs, hm(a), fim, saida, True) for bs in dias.values()) if x]
        marca = "  <- sequencia" if a == "10:45" else ""
        resumo(f"  {a}-{b}{marca}", tr)


if __name__ == "__main__":
    main()
