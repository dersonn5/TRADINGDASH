"""O que a abertura de NY (10:30 BRT, com os EUA em horario de verao) faz com o
range logo antes dela. Contagem descritiva: sem entrada, stop ou alvo.

Definicoes (combinadas com o operador em 22/09/2026, antes de rodar):
  Range pre-evento  = maxima/minima dos N minutos antes do evento.
                      N testado: 10 (10:20-10:29, o principal), 15, 30, 60.
  Movimento         = primeiros 15 min do evento (10:30-10:44).
  Sweep             = o movimento passa da maxima ou da minima do range.
                      Se passar dos dois, vale o primeiro.
  Horizonte         = 60 min apos o evento (11:30).
  Classificacao, olhando do sweep ate o horizonte:
    REVERSAO     - tocou o lado OPOSTO do range.
    CONTINUACAO  - nao tocou o oposto e fechou o horizonte alem do lado varrido.
    NADA         - nem um nem outro.
  Contexto          = direcao dos 30 min antes do evento (fechamento - abertura).
                      Sweep CONTRA o contexto = sweep do lado oposto a ele.

Controle: a mesma conta com o evento em 11:30, 13:30 e 14:30. Se 10:30 nao
diferir desses horarios, a abertura de NY nao tem nada de especial.
"""

import datetime as dt
import sys
from collections import Counter, defaultdict

import backtest_quarters as bq


def mais(t, m):
    return (dt.datetime.combine(dt.date(2000, 1, 1), t) + dt.timedelta(minutes=m)).time()


def analisar(bs, evento, n_range, mov=15, horizonte=60):
    rng = bq.entre(bs, mais(evento, -n_range), evento)
    ctx = bq.entre(bs, mais(evento, -30), evento)
    movim = bq.entre(bs, evento, mais(evento, mov))
    depois = bq.entre(bs, evento, mais(evento, horizonte))
    if len(rng) < n_range * 0.8 or len(movim) < mov * 0.8 or len(depois) < horizonte * 0.8:
        return None
    hi, lo = max(b[2] for b in rng), min(b[3] for b in rng)
    lado = None
    for i, b in enumerate(movim):
        if b[2] > hi and b[3] < lo:
            lado = "cima" if b[1] <= (hi + lo) / 2 else "baixo"  # candle engoliu o range: vale a direcao da abertura
        elif b[2] > hi:
            lado = "cima"
        elif b[3] < lo:
            lado = "baixo"
        if lado:
            i_sweep = i
            break
    if not lado:
        return {"sweep": False}
    resto = depois[i_sweep:]
    if lado == "cima":
        tocou_oposto = any(b[3] <= lo for b in resto[1:])
        alem = resto[-1][4] > hi
        exc = max(b[2] for b in resto) - hi
    else:
        tocou_oposto = any(b[2] >= hi for b in resto[1:])
        alem = resto[-1][4] < lo
        exc = lo - min(b[3] for b in resto)
    if tocou_oposto:
        res = "REVERSAO"
    elif alem:
        res = "CONTINUACAO"
    else:
        res = "NADA"
    dir_ctx = ctx[-1][4] - ctx[0][1]
    if dir_ctx == 0:
        ctx_rel = "neutro"
    else:
        ctx_rel = "a favor" if (dir_ctx > 0) == (lado == "cima") else "contra"
    return {"sweep": True, "lado": lado, "res": res, "ctx": ctx_rel,
            "range": hi - lo, "exc": exc}


def tabela(dias, evento, n_range, mostrar_datas=False):
    rs = {}
    for d, bs in sorted(dias.items()):
        r = analisar(bs, evento, n_range)
        if r is not None:
            rs[d] = r
    n = len(rs)
    sw = {d: r for d, r in rs.items() if r["sweep"]}
    c = Counter(r["res"] for r in sw.values())
    ns = len(sw)
    faixa = sorted(r["range"] for r in rs.values() if "range" in r) or [0]
    tam = sorted(r["range"] for r in sw.values()) or [0]
    linha = (f"{evento.strftime('%H:%M')} range {n_range:2d}m | dias {n:3d} | sweep {ns / n:4.0%} | "
             f"reversao {c['REVERSAO'] / ns:4.0%}  continuacao {c['CONTINUACAO'] / ns:4.0%}  "
             f"nada {c['NADA'] / ns:4.0%} | range mediano {tam[len(tam) // 2]:.0f} pts")
    print(linha)
    if mostrar_datas:
        por = defaultdict(list)
        for d, r in sw.items():
            por[(r["ctx"], r["res"])].append(d)
        print("\n   Cruzado com o contexto (30 min antes), % dos dias com sweep:")
        for ctx in ("contra", "a favor", "neutro"):
            tot = sum(len(v) for (cx, _), v in por.items() if cx == ctx)
            if not tot:
                continue
            partes = []
            for res in ("REVERSAO", "CONTINUACAO", "NADA"):
                partes.append(f"{res.lower()} {len(por[(ctx, res)]) / tot:4.0%}")
            print(f"   sweep {ctx:<8} n={tot:3d}: " + "  ".join(partes))
        print("\n   Datas por caso (para conferir no Profit com DiasAtras):")
        for (ctx, res), ds in sorted(por.items()):
            print(f"   {ctx:<8} {res:<12} {len(ds):3d}  ultimas: {', '.join(str(x) for x in ds[-5:])}")
    return rs


def main():
    dias = bq.carregar()
    print(f"{len(dias)} pregoes, {min(dias)} a {max(dias)}\n")
    print("== Abertura de NY (10:30), variando o range ==")
    for n in (10, 15, 30, 60):
        tabela(dias, bq.hm("10:30"), n)
    print("\n== Controle: range de 10 min em outros horarios ==")
    for ev in ("10:30", "11:30", "13:30", "14:30"):
        tabela(dias, bq.hm(ev), 10)
    print("\n== Detalhe: 10:30, range 10:20-10:29 ==")
    tabela(dias, bq.hm("10:30"), 10, mostrar_datas=True)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Versao 2 (unica redefinicao combinada, 22/09/2026, antes de rodar):
#   Liquidez = ultimo fundo e ultimo topo de SWING (fractal K candles de cada
#              lado) na janela [evento-30, evento-5), confirmados dentro dela.
#   Sweep    = entre evento-5 e evento+10 (10:25-10:40). Primeiro que ocorrer.
#   Oposto   = o swing do outro lado; sem swing do outro lado, o extremo da
#              janela de referencia.
#   Classificacao ate evento+60, igual a versao 1.
# Motivo: em 22/09 a varrida do fundo das 10:16 foi as 10:28-10:29, antes das
# 10:30, e a versao 1 (range 10:20-10:29) nao enxergou.
# ---------------------------------------------------------------------------
K = 3


def swings(ref):
    alto = baixo = None
    for i in range(K, len(ref) - K):
        viz = ref[i - K:i] + ref[i + 1:i + 1 + K]
        if all(ref[i][2] > v[2] for v in viz):
            alto = (ref[i][0], ref[i][2])
        if all(ref[i][3] < v[3] for v in viz):
            baixo = (ref[i][0], ref[i][3])
    return alto, baixo


def analisar2(bs, evento, horizonte=60):
    ref = bq.entre(bs, mais(evento, -30), mais(evento, -5))
    janela = bq.entre(bs, mais(evento, -5), mais(evento, 10))
    ate = bq.entre(bs, mais(evento, -5), mais(evento, horizonte))
    if len(ref) < 20 or len(janela) < 12 or len(ate) < horizonte * 0.8:
        return None
    alto, baixo = swings(ref)
    if not alto and not baixo:
        return {"sweep": False}
    oposto_alto = alto[1] if alto else max(b[2] for b in ref)
    oposto_baixo = baixo[1] if baixo else min(b[3] for b in ref)
    lado = None
    for i, b in enumerate(janela):
        pega_baixo = baixo and b[3] < baixo[1]
        pega_alto = alto and b[2] > alto[1]
        if pega_baixo and pega_alto:
            lado = "baixo" if b[4] > b[1] else "cima"  # fechou pra cima: a varrida foi embaixo
        elif pega_baixo:
            lado = "baixo"
        elif pega_alto:
            lado = "cima"
        if lado:
            t_sweep = b[0]
            break
    if not lado:
        return {"sweep": False}
    resto = [x for x in ate if x[0] >= t_sweep]
    if lado == "baixo":
        tocou = any(x[2] >= oposto_alto for x in resto[1:])
        alem = resto[-1][4] < baixo[1]
    else:
        tocou = any(x[3] <= oposto_baixo for x in resto[1:])
        alem = resto[-1][4] > alto[1]
    res = "REVERSAO" if tocou else ("CONTINUACAO" if alem else "NADA")
    return {"sweep": True, "lado": lado, "res": res, "t": t_sweep,
            "nivel": baixo[1] if lado == "baixo" else alto[1]}


def tabela2(dias, evento, datas=False):
    rs = {d: analisar2(bs, evento) for d, bs in sorted(dias.items())}
    rs = {d: r for d, r in rs.items() if r is not None}
    sw = {d: r for d, r in rs.items() if r["sweep"]}
    c = Counter(r["res"] for r in sw.values())
    ns = len(sw)
    print(f"{evento.strftime('%H:%M')} | dias {len(rs):3d} | sweep {ns / len(rs):4.0%} | "
          f"reversao {c['REVERSAO'] / ns:4.0%}  continuacao {c['CONTINUACAO'] / ns:4.0%}  nada {c['NADA'] / ns:4.0%}")
    if datas:
        for res in ("REVERSAO", "CONTINUACAO", "NADA"):
            ds = [d for d, r in sw.items() if r["res"] == res]
            print(f"   {res:<12} {len(ds):3d}  ultimas: {', '.join(str(x) for x in ds[-6:])}")
    return rs


def main2():
    dias = bq.carregar()
    print("== Versao 2: sweep de swing 10:25-10:40, controle nos outros horarios ==")
    for ev in ("10:30", "11:30", "13:30", "14:30"):
        tabela2(dias, bq.hm(ev), datas=(ev == "10:30"))
