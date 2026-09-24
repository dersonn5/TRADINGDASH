"""Filtro de contexto da barra das 10, observado pelo operador em 23/09/2026.

Regime da 1a hora (4 barras de 15 min, 09:00-09:59), definido antes de rodar:
  TENDENCIA = pelo menos 3 das 4 barras na mesma cor E movimento liquido
              (fechamento 09:59 - abertura 09:00) >= 475 pts, no sentido dessa cor.
  LATERAL   = o resto.

Regras do operador:
  LATERAL   -> operar CONTRA a barra do a vista depois da varrida dela
               (varrida = barra de 15 min seguinte passa do extremo e fecha de volta;
               varreu o topo -> venda, varreu o fundo -> compra).
  TENDENCIA -> so a favor da tendencia:
               a) o a vista manipula contra a tendencia (varre o extremo do lado
                  contrario) -> gatilho a favor da tendencia depois da varrida;
               b) sem essa manipulacao -> continuidade: MSS + FVG a favor da
                  tendencia entre 10:15 e 11:15.
               Varrida que pediria trade CONTRA a tendencia: nao opera.

Gatilho e gestao: os de sempre (hierarquia_liquidez.gatilhos_do_dia; alvo no
BSL/SSL + trailing; custo 10 pts). Um trade por dia.
"""

import statistics as st

import backtest_quarters as bq
import hierarquia_liquidez as hl
import padrao_15m as p

H = bq.hm
LIMITE = 475
CT, V = 3, 0.20


def regime(bs):
    b15 = [b for b in p.agrega15(bs) if 540 <= p.minutos(b[0]) < 600]
    if len(b15) < 4:
        return None, 0
    alta = sum(b[4] > b[1] for b in b15)
    baixa = sum(b[4] < b[1] for b in b15)
    mov = b15[-1][4] - b15[0][1]
    if alta >= 3 and mov >= LIMITE:
        return "tendencia", 1
    if baixa >= 3 and mov <= -LIMITE:
        return "tendencia", -1
    return "lateral", 0


def trade_do_dia(bs, ant):
    reg, tend = regime(bs)
    if reg is None:
        return None
    gs = hl.gatilhos_do_dia(bs, ant)
    r = p.analisar(p.agrega15(bs), 10, bs)
    varrida = r if r and not r.get("sem") else None

    def gatilho_apos_varrida(lado):
        ini = p.minutos(varrida["barra"])
        c = [g for g in gs if g["lado"] == lado and ini <= p.minutos(g["t_mss"]) < ini + 45]
        return c[0] if c else None

    if reg == "lateral":
        if varrida:
            g = gatilho_apos_varrida(varrida["lado"])
            if g:
                return dict(reg=reg, tipo="lateral: contra a barra", **g)
        return dict(reg=reg, tipo="lateral: sem trade")
    # tendencia
    if varrida and varrida["lado"] == tend:
        g = gatilho_apos_varrida(tend)
        if g:
            return dict(reg=reg, tipo="tendencia: manipulacao a favor", **g)
    c = [g for g in gs if g["lado"] == tend and H("10:15") <= g["t_mss"] < H("11:15")]
    if c:
        return dict(reg=reg, tipo="tendencia: continuidade", **c[0])
    return dict(reg=reg, tipo="tendencia: sem trade")


def linha(rot, ts):
    ts = [t for t in ts if "r" in t]
    n = len(ts)
    if not n:
        print(f"  {rot:<34} sem trades")
        return
    rs = [t["r"] for t in ts]
    m = st.mean(rs)
    se = st.pstdev(rs) / n ** 0.5 if n > 1 else 0
    f = lambda k: sum(t["mfe"] >= k for t in ts) / n
    rs_ = sum(t["pts"] for t in ts) * CT * V
    print(f"  {rot:<34} n={n:3d} | 3R {f(3):4.0%} 5R {f(5):4.0%} | media {m:+.2f}R (t={m / se if se else 0:+.1f})"
          f" | R$ {rs_:+7,.0f} com {CT} ct".replace(",", "."))


def main():
    dias = bq.carregar()
    o = sorted(dias)
    meio = o[len(o) // 2]
    res = []
    for k in range(1, len(o)):
        bs = bq.entre(dias[o[k]], H("09:00"), H("17:51"))
        ant = bq.entre(dias[o[k - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        t = trade_do_dia(bs, ant)
        if t:
            t["data"] = o[k]
            res.append(t)
    from collections import Counter
    print(f"{len(res)} pregoes | regimes: {dict(Counter(t['reg'] for t in res))}")
    print(f"tipos: {dict(Counter(t['tipo'] for t in res))}\n")
    linha("REGRA DO OPERADOR (tudo)", res)
    for tp in ("lateral: contra a barra", "tendencia: manipulacao a favor", "tendencia: continuidade"):
        linha(tp, [t for t in res if t["tipo"] == tp])
    linha("  1a metade", [t for t in res if t["data"] <= meio])
    linha("  2a metade", [t for t in res if t["data"] > meio])

    # O que a regra corta: varrida em dia de tendencia pedindo trade CONTRA a tendencia
    cortados = []
    for k in range(1, len(o)):
        bs = bq.entre(dias[o[k]], H("09:00"), H("17:51"))
        ant = bq.entre(dias[o[k - 1]], H("09:00"), H("18:00"))
        if len(bs) < 300:
            continue
        reg, tend = regime(bs)
        r = p.analisar(p.agrega15(bs), 10, bs)
        if reg == "tendencia" and r and not r.get("sem") and r["lado"] != tend:
            ini = p.minutos(r["barra"])
            c = [g for g in hl.gatilhos_do_dia(bs, ant)
                 if g["lado"] == r["lado"] and ini <= p.minutos(g["t_mss"]) < ini + 45]
            if c:
                cortados.append(c[0])
    print()
    linha("CORTADO: contra a tendencia", cortados)


if __name__ == "__main__":
    main()
