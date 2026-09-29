"""Sweep da barra das 10 (ou da barra que a manipulou) + BPR — ideia do operador em 28/09/2026.

"Quando ele sweepa o fundo da barra que manipulou a barra das 10, ele sweepa e deixa um BPR
e paga mais de 8/1." (28/09: sweep 10:56-10:58, BPR 182.915-183.015, compra 11:01, stop 240 pts,
maxima 184.980 as 11:40 = 8,2R.)

Definicoes confirmadas antes de rodar:
  Barra das 10  = candle de 15 min das 10:00 (B).
  Barra que manipulou = o primeiro candle de 15 min a partir das 10:15 que passou da minima
                  (maxima) de B. O extremo dela vira um nivel novo, valido depois que ela fecha.
  Niveis        = minima e maxima de B (a partir das 10:15) e o extremo da barra que manipulou
                  (a partir do fechamento dela). Varreu minima -> compra; maxima -> venda.
  Sweep         = primeiro minuto que passa do nivel, entre o inicio dele e 11:14.
  BPR           = depois do sweep, o primeiro FVG a favor da reversao (candle i-2 e i sem
                  sobreposicao) que sobrepoe um FVG contrario da pernada que fez o sweep
                  (formado ate 30 candles antes). BPR = a sobreposicao dos dois.
  Entrada       = ordem limitada na borda do BPR (topo na compra, fundo na venda).
                  SEM MSS: vale a partir do candle seguinte ao BPR.
                  COM MSS: so depois de um candle fechar alem do ultimo swing contrario
                  (fractal de 2) formado antes do extremo; MSS ate 11:14.
                  Cancela se o preco passar do stop antes, 30 min sem executar, ou 11:30.
  Stop          = extremo do sweep ate o BPR + 1 tick.
  Alvos (cada um medido separado, saida no maximo 12:00, custo 10 pts, stop e alvo no mesmo
  candle = stop):
     LIQUIDEZ   = proximo swing nao varrido (alvo atual do sistema) + zero a zero em 1R +
                  trailing atras dos swings de 1 min.
     GAP        = fechamento do dia anterior, se estiver a pelo menos 1R a favor; zero a zero
                  em 1R, sem trailing. Sem gap a favor: trailing (como SO TRAILING).
     SO TRAILING = sem alvo; zero a zero em 1R, depois trailing atras dos swings de 1 min.
  1 trade por dia por variante: o primeiro que executa.

Dados: WINFUT 1 min (abr-set/2026) + o pregao de 28/09 do WINV26 (o contrato vigente).
28/09 e o dia que deu a ideia: o resultado sai com e sem ele.
"""

import csv
import datetime as dt
import statistics as st
from collections import defaultdict
from pathlib import Path

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p
import setup_v_sweep as vs

sv = hl.sv
H = bq.hm
AQUI = Path(__file__).parent
DIA_DA_IDEIA = dt.date(2026, 9, 28)


def carregar():
    dias = bq.carregar()
    extra = defaultdict(list)
    with (AQUI / "WINV26_1min.csv").open() as f:
        for r in csv.DictReader(f):
            t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
            if t.date() > max(dias):
                extra[t.date()].append((t.time(), float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
    dias.update(extra)
    return dias


def niveis(bs):
    """[(tipo, lado_do_trade, nivel, indice_a_partir_de)]"""
    b15 = p.agrega15(bs)
    B = next((b for b in b15 if b[0] == H("10:00")), None)
    if not B:
        return []
    i1015 = sv.idx(bs, H("10:15"))
    out = [("barra10", 1, B[3], i1015), ("barra10", -1, B[2], i1015)]
    for lado in (1, -1):
        m = next((b for b in b15 if H("10:15") <= b[0] <= H("11:00") and ((b[3] < B[3]) if lado == 1 else (b[2] > B[2]))), None)
        if m:
            fim = (dt.datetime.combine(dt.date.today(), m[0]) + dt.timedelta(minutes=15)).time()
            out.append(("manipulou", lado, m[3] if lado == 1 else m[2], sv.idx(bs, fim)))
    return out


def candidatos(bs):
    """Trades candidatos do dia: dict com variante (sem/com MSS), lado, i_fill, entrada, stop."""
    out = []
    i_lim_sweep = sv.idx(bs, H("11:15"))
    i_1130 = sv.idx(bs, H("11:30"))
    for tipo, lado, nivel, i0 in niveis(bs):
        alta = lado == 1
        s = next((i for i in range(i0, i_lim_sweep) if ((bs[i][3] < nivel) if alta else (bs[i][2] > nivel))), None)
        if s is None:
            continue
        # BPR: primeiro FVG a favor depois do sweep que sobrepoe um FVG contrario da pernada
        for i in range(s + 2, i_1130):
            fav = [g for g in sv.fvgs(bs, i, i, alta) if g[0] == i]
            if not fav:
                continue
            _, f_lo, f_hi = fav[0]
            contra = sv.fvgs(bs, max(2, s - 30), i - 1, not alta)
            zona = None
            for _, c_lo, c_hi in reversed(contra):
                lo, hi = max(f_lo, c_lo), min(f_hi, c_hi)
                if lo < hi:
                    zona = (lo, hi)
                    break
            if not zona:
                continue
            trecho = bs[s:i + 1]
            ext = min(b[3] for b in trecho) if alta else max(b[2] for b in trecho)
            i_ext = s + (min(range(len(trecho)), key=lambda k: trecho[k][3]) if alta else max(range(len(trecho)), key=lambda k: trecho[k][2]))
            stop = ext - sv.TICK if alta else ext + sv.TICK
            entrada = zona[1] if alta else zona[0]
            if (entrada <= stop) if alta else (entrada >= stop):
                break
            # MSS: fechamento alem do ultimo swing contrario formado antes do extremo
            topos, fundos = sv.fractais(bs[:i_ext + 1], 2)
            refs = topos if alta else fundos
            i_mss = None
            if refs:
                ref = bs[refs[-1]][2] if alta else bs[refs[-1]][3]
                i_mss = next((k for k in range(i_ext + 1, i_lim_sweep) if ((bs[k][4] > ref) if alta else (bs[k][4] < ref))), None)
            for variante, desde in (("sem MSS", i + 1), ("com MSS", None if i_mss is None else max(i + 1, i_mss + 1))):
                if desde is None:
                    continue
                for f in range(desde, min(desde + 30, i_1130)):
                    b = bs[f]
                    if (b[3] <= stop) if alta else (b[2] >= stop):
                        break
                    if (b[3] <= entrada) if alta else (b[2] >= entrada):
                        out.append(dict(variante=variante, tipo=tipo, lado=lado, i_fill=f, entrada=entrada, stop=stop,
                                        t_sweep=bs[s][0], t_bpr=bs[i][0], t_fill=b[0]))
                        break
            break
    return out


def gerir_gap(bs, i_fill, lado, entrada, stop, alvo):
    """Alvo fixo, zero a zero em 1R, sem trailing, saida 12:00."""
    risco = abs(entrada - stop)
    fim = sv.idx(bs, H("12:00"))
    for i in range(i_fill, min(fim, len(bs))):
        b = bs[i]
        if (b[3] <= stop) if lado == 1 else (b[2] >= stop):
            return (stop - entrada) * lado - sv.CUSTO
        if (b[2] >= alvo) if lado == 1 else (b[3] <= alvo):
            return (alvo - entrada) * lado - sv.CUSTO
        if (b[2] >= entrada + risco) if lado == 1 else (b[3] <= entrada - risco):
            stop = entrada
    return (bs[min(fim, len(bs)) - 1][4] - entrada) * lado - sv.CUSTO


def resultados(bs, prev, c):
    lado, f, e, s = c["lado"], c["i_fill"], c["entrada"], c["stop"]
    risco = abs(e - s)
    out = {}
    out["LIQUIDEZ"] = vs.gerir_ate_12(bs, f, lado, e, s, sv.alvo_liquidez(bs, f, lado, e))[0]
    trailing = vs.gerir_ate_12(bs, f, lado, e, s, None)[0]
    out["SO TRAILING"] = trailing
    pc = prev[-1][4]
    out["GAP"] = gerir_gap(bs, f, lado, e, s, pc) if (pc - e) * lado >= risco else trailing
    i12 = sv.idx(bs, H("12:00"))
    depois = bs[f:i12]
    mfe = (max(b[2] for b in depois) - e) if lado == 1 else (e - min(b[3] for b in depois))
    return {k: dict(pts=v, r=v / risco) for k, v in out.items()}, risco, mfe / risco


def linha(rot, x, meio):
    n = len(x)
    if n < 2:
        print(f"    {rot:<14} n={n:3d}")
        return
    rs = [t["r"] for t in x]
    mu = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5
    a = [t["r"] for t in x if t["data"] <= meio]
    b = [t["r"] for t in x if t["data"] > meio]
    print(f"    {rot:<14} n={n:3d}  acerto {sum(t['pts'] > 0 for t in x) / n:4.0%}  media {mu:+.2f}R (t={mu / se if se else 0:+.1f})  "
          f"metades {st.mean(a) if a else 0:+.2f} | {st.mean(b) if b else 0:+.2f}  "
          f"R$ {sum(t['pts'] for t in x) * 3 * 0.2:+,.0f} (3 ct)".replace(",", "."))


def main():
    dias = carregar()
    o = sorted(dias)
    meio = o[len(o) // 2]
    g = defaultdict(list)
    lista = []
    lista_m = []
    for kd in range(1, len(o)):
        d = o[kd]
        bs = bq.entre(dias[d], H("09:00"), H("17:51"))
        prev = bq.entre(dias[o[kd - 1]], H("09:00"), H("18:00"))
        if len(bs) < 150 or not prev:
            continue
        cs = candidatos(bs)
        # por tipo de nivel, independente de outro trade antes no dia (o 28/09 foi o 2o sweep)
        for tipo in ("barra10", "manipulou"):
            for variante in ("sem MSS", "com MSS"):
                v = sorted((c for c in cs if c["variante"] == variante and c["tipo"] == tipo), key=lambda c: c["i_fill"])
                if v:
                    res, risco, mfe_r = resultados(bs, prev, v[0])
                    for alvo, r in res.items():
                        g[(variante, alvo, tipo)].append(dict(r, data=d, mfe=mfe_r))
                    if tipo == "manipulou" and variante == "sem MSS":
                        lista_m.append((d, v[0], risco, mfe_r, res))
        for variante in ("sem MSS", "com MSS"):
            v = sorted((c for c in cs if c["variante"] == variante), key=lambda c: c["i_fill"])
            if not v:
                continue
            c = v[0]
            res, risco, mfe_r = resultados(bs, prev, c)
            for alvo, r in res.items():
                g[(variante, alvo)].append(dict(r, data=d))
            lista.append((d, variante, c, risco, mfe_r, res))

    print(f"Sweep da barra das 10 / da barra que manipulou + BPR. WIN 1 min, {len(o) - 1} pregoes "
          f"({o[1]:%d/%m} a {o[-1]:%d/%m}/2026).\n")
    for variante in ("sem MSS", "com MSS"):
        print(f"  Entrada {variante}:")
        for alvo in ("LIQUIDEZ", "GAP", "SO TRAILING"):
            x = g[(variante, alvo)]
            linha(alvo, x, meio)
            linha("  sem 28/09", [t for t in x if t["data"] != DIA_DA_IDEIA], meio)
        print()
    print("  Por nivel varrido (o primeiro trade daquele nivel no dia, mesmo que outro tenha vindo antes):")
    for tipo in ("barra10", "manipulou"):
        for variante in ("sem MSS", "com MSS"):
            print(f"   {tipo} · {variante}")
            for alvo in ("LIQUIDEZ", "GAP", "SO TRAILING"):
                x = g[(variante, alvo, tipo)]
                linha(alvo, x, meio)
            x = g[(variante, "LIQUIDEZ", tipo)]
            if x:
                mf = sorted(t["mfe"] for t in x)
                print(f"      maximo a favor ate 12:00: mediana {st.median(mf):.1f}R | chegou a 3R {sum(m >= 3 for m in mf) / len(mf):.0%} "
                      f"| 5R {sum(m >= 5 for m in mf) / len(mf):.0%} | 8R {sum(m >= 8 for m in mf) / len(mf):.0%}")
    print()
    print("  Trades do sweep da barra que manipulou (sem MSS):")
    for d, c, risco, mfe_r, res in lista_m:
        print(f"    {d:%d/%m} {'compra' if c['lado'] == 1 else 'venda '} sweep {c['t_sweep']:%H:%M} BPR {c['t_bpr']:%H:%M} "
              f"entrada {c['t_fill']:%H:%M} risco {risco:4.0f}  maximo a favor {mfe_r:5.1f}R | "
              + "  ".join(f"{k} {v['r']:+.1f}R" for k, v in res.items()))
    print()
    print("  Trades (primeiro do dia, sem MSS):")
    for d, variante, c, risco, mfe_r, res in lista:
        if variante != "sem MSS":
            continue
        print(f"    {d:%d/%m} {'compra' if c['lado'] == 1 else 'venda '} {c['tipo']:<9} sweep {c['t_sweep']:%H:%M} BPR {c['t_bpr']:%H:%M} "
              f"entrada {c['t_fill']:%H:%M} risco {risco:4.0f}  maximo a favor ate 12:00 {mfe_r:5.1f}R | "
              + "  ".join(f"{k} {v['r']:+.1f}R" for k, v in res.items()))


if __name__ == "__main__":
    main()
