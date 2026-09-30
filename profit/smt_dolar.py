"""SMT do WIN com o dolar (WDO): a divergencia melhora os gatilhos? (30/09/2026)

Pergunta do operador depois do pregao de 30/09 (SMT de baixa as 09:44-09:46). Palpite dele:
"nao vai ter relevancia, o dolar anda descolado dessa divergencia".

Definicoes (SMT classica com ativo de correlacao inversa):
  Gatilhos  = todo MSS de 1 min com entrada entre 10:00 e 11:29 (setup_v_sweep.gatilhos_mss:
              MSS+FVG, MSS+OB e BPR), gestao do sistema (alvo na liquidez + trailing, ate 12:00).
  Extremo   = o minuto do fundo (compra) ou topo (venda) que virou o stop do gatilho.
  Referencia = de 30 a 5 min antes do extremo.
  O WIN varreu = o extremo passou do fundo/topo da referencia (fundo mais baixo / topo mais alto).
  SMT       = o WIN varreu, mas o dolar NAO fez o espelho: na compra, o topo do WDO em
              extremo +-2 min nao passou do topo do WDO na referencia; na venda, o fundo do WDO
              nao passou do fundo da referencia.
  Confirmado = o WIN varreu e o dolar tambem fez o espelho (sem divergencia).
  Sem varrida = o extremo do WIN nao passou da referencia (fica fora da comparacao principal).
  Tambem mede: correlacao dos retornos de 1 min WIN x WDO, 10:00-11:29, por mes
  ("o dolar anda descolado?").
Dados: WIN 1 min (WINFUT, e WINV26 depois de 25/09); WDO 1 min so existe no cache para
jun/22-set/2026 (contratos Q26, U26, V26, X26). Por dia usa o contrato com mais candles.
"""

import csv
import datetime as dt
import statistics as st
from collections import defaultdict
from pathlib import Path

import backtest_quarters as bq
import setup_bpr_sweep as bpr
import setup_v_sweep as vs

AQUI = Path(__file__).parent
H = bq.hm
CONTRATOS = ("WDOQ26", "WDOU26", "WDOV26", "WDOX26")


def carregar_wdo():
    """{data: {hora: (o, h, l, c)}} usando, por dia, o contrato com mais candles 10:00-11:29."""
    por = {}
    for c in CONTRATOS:
        f = AQUI / f"{c}_1min.csv"
        if not f.exists():
            continue
        d = defaultdict(dict)
        with f.open() as fh:
            for r in csv.DictReader(fh):
                t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
                d[t.date()][t.time()] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
        por[c] = d
    out = {}
    for dia in {k for d in por.values() for k in d}:
        conta = lambda c: sum(1 for t in por[c].get(dia, {}) if H("10:00") <= t < H("11:30"))
        melhor = max(por, key=conta)
        if conta(melhor) >= 80:
            out[dia] = por[melhor][dia]
    return out


def minuto(t, delta):
    return (dt.datetime.combine(dt.date.today(), t) + dt.timedelta(minutes=delta)).time()


def classificar(bs, wdo, x):
    """SMT / confirmado / sem varrida para um gatilho."""
    lado = x["lado"]
    stop = x["entrada_stop"]
    ext = stop + bpr.sv.TICK if lado == 1 else stop - bpr.sv.TICK
    i_mss = x["i_mss"]
    i_ext = next((i for i in range(i_mss, -1, -1) if (bs[i][3] == ext if lado == 1 else bs[i][2] == ext)), None)
    if i_ext is None:
        return None
    t = bs[i_ext][0]
    ref = [b for b in bs if minuto(t, -30) <= b[0] < minuto(t, -5)]
    w_ref = [v for k, v in wdo.items() if minuto(t, -30) <= k < minuto(t, -5)]
    w_ext = [v for k, v in wdo.items() if minuto(t, -2) <= k <= minuto(t, 2)]
    if len(ref) < 15 or len(w_ref) < 15 or not w_ext:
        return None
    if lado == 1:
        varreu = ext < min(b[3] for b in ref)
        dolar = max(v[1] for v in w_ext) > max(v[1] for v in w_ref)
    else:
        varreu = ext > max(b[2] for b in ref)
        dolar = min(v[2] for v in w_ext) < min(v[2] for v in w_ref)
    if not varreu:
        return "sem varrida"
    return "confirmado" if dolar else "SMT"


def main():
    dias = bpr.carregar()
    wdo = carregar_wdo()
    comuns = sorted(d for d in dias if d in wdo)
    print(f"Dias com WIN e WDO de 1 min: {len(comuns)} ({comuns[0]:%d/%m} a {comuns[-1]:%d/%m/%Y})\n")

    # correlacao por mes
    print("Correlacao dos retornos de 1 min WIN x WDO, 10:00-11:29 (esperado: negativa):")
    por_mes = defaultdict(lambda: ([], []))
    for d in comuns:
        w = {b[0]: b[4] for b in dias[d] if H("10:00") <= b[0] < H("11:30")}
        ts = sorted(t for t in w if t in wdo[d])
        for a, b in zip(ts, ts[1:]):
            por_mes[d.strftime("%Y-%m")][0].append(w[b] - w[a])
            por_mes[d.strftime("%Y-%m")][1].append(wdo[d][b][3] - wdo[d][a][3])
    for m, (xs, ys) in sorted(por_mes.items()):
        print(f"  {m}: {st.correlation(xs, ys):+.2f}  ({len(xs)} minutos)")

    g = defaultdict(list)
    for d in comuns:
        bs = bq.entre(dias[d], H("09:00"), H("17:51"))
        if len(bs) < 150:
            continue
        for x in vs.gatilhos_mss(bs):
            if not (H("10:00") <= x["t_ent"] < H("11:30")):
                continue
            # gatilhos_mss nao devolve o stop: recalcula o extremo da pernada como ele faz
            i_mss = x["i_mss"]
            topos, fundos = bpr.sv.fractais(bs[:i_mss], 2)
            refs = topos if x["lado"] == 1 else fundos
            if not refs:
                continue
            trecho = bs[refs[-1]:i_mss + 1]
            ext = min(b[3] for b in trecho) if x["lado"] == 1 else max(b[2] for b in trecho)
            x = dict(x, entrada_stop=ext - bpr.sv.TICK if x["lado"] == 1 else ext + bpr.sv.TICK, data=d)
            c = classificar(bs, wdo[d], x)
            if c:
                g[c].append(x)
                g[(c, x["gatilho"])].append(x)

    print("\nGatilhos de 1 min (10:00-11:29), pelo que o dolar fez no extremo:")
    for c in ("SMT", "confirmado", "sem varrida"):
        linha(c, g[c])
    print("\n  Por gatilho:")
    for gat in ("MSS+FVG", "MSS+OB", "BPR"):
        for c in ("SMT", "confirmado"):
            linha(f"{gat} · {c}", g[(c, gat)])


def linha(rot, x):
    n = len(x)
    if n < 2:
        print(f"    {rot:<22} n={n:3d}")
        return
    rs = [t["r"] for t in x]
    mu = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5
    print(f"    {rot:<22} n={n:3d}  acerto {sum(t['pts'] > 0 for t in x) / n:4.0%}  media {mu:+.2f}R (t={mu / se if se else 0:+.1f})  "
          f"pts/trade {st.mean(t['pts'] for t in x):+.0f}")


if __name__ == "__main__":
    main()
