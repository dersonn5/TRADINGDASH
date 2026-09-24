"""Desenha cada trade do backtest R2 (sequencia + captura) para auditoria visual.

Um PNG por dia em profit/backtest_plots/, com:
  caixa Q2 (09:00-10:00) e Q3 (10:00-11:30) em cinza pontilhado,
  sequencia (10:45-11:07) em dourado,
  candle do sweep marcado, entrada, stop, alvo e saida.

A regra desenhada e exatamente a de backtest_quarters.r2_janela. Se o grafico
mostrar um trade que voce nao faria, a regra esta errada naquele ponto - e e
isso que esta auditoria procura.

Uso: python profit/plot_backtest.py            (todos os dias)
     python profit/plot_backtest.py 2026-09-22 (um dia)
"""

import datetime as dt
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import backtest_quarters as bq

SAIDA = Path(__file__).parent / "backtest_plots"


def minutos(t):
    return t.hour * 60 + t.minute


def detalhar(bs, ini, fim, saida):
    """Mesma logica de r2_janela, devolvendo os pontos para desenhar."""
    for sw in bq.entre(bs, ini, fim):
        t = sw[0]
        ref = bq.entre(bs, bq.inicio_quarto(t), t)
        if len(ref) < 5:
            continue
        for topo in (True, False):
            if topo:
                i_ext = max(range(len(ref)), key=lambda i: ref[i][2])
                ext = ref[i_ext][2]
                fez = sw[2] > ext
                recuo = ext - min(b[3] for b in ref[i_ext:])
            else:
                i_ext = min(range(len(ref)), key=lambda i: ref[i][3])
                ext = ref[i_ext][3]
                fez = sw[3] < ext
                recuo = max(b[2] for b in ref[i_ext:]) - ext
            if not fez or recuo < bq.RECUO_MIN:
                continue
            depois = bq.entre(bs, t, saida)[1:]
            extremo = sw[2] if topo else sw[3]
            for j, g in enumerate(depois):
                extremo = max(extremo, g[2]) if topo else min(extremo, g[3])
                if (g[4] < sw[3]) if topo else (g[4] > sw[2]):
                    lado = -1 if topo else 1
                    entrada = g[4]
                    stop = extremo + bq.TICK if topo else extremo - bq.TICK
                    risco = abs(stop - entrada)
                    if risco <= 0:
                        break
                    alvo = entrada + lado * 2 * risco
                    t_saida, p_saida, como = None, None, "tempo"
                    resto = depois[j + 1:]
                    for x in resto:
                        s = x[3] <= stop if lado == 1 else x[2] >= stop
                        a = x[2] >= alvo if lado == 1 else x[3] <= alvo
                        if s:
                            t_saida, p_saida, como = x[0], stop, "stop"
                            break
                        if a:
                            t_saida, p_saida, como = x[0], alvo, "alvo"
                            break
                    if t_saida is None and resto:
                        t_saida, p_saida = resto[-1][0], resto[-1][4]
                    return dict(lado=lado, t_sweep=t, pool=ext, t_pool=ref[i_ext][0],
                                t_ent=g[0], entrada=entrada, stop=stop, alvo=alvo,
                                t_saida=t_saida, p_saida=p_saida, como=como,
                                pts=((p_saida or entrada) - entrada) * lado, risco=risco)
            break
    return None


def desenhar(dia, bs, tr):
    vis = bq.entre(bs, bq.hm("09:00"), bq.hm("12:00"))
    fig, ax = plt.subplots(figsize=(14, 6), dpi=90)
    for t, o, h, l, c in vis:
        x = minutos(t)
        cor = "#2a9d8f" if c >= o else "#b5838d"
        ax.vlines(x, l, h, color="#444", linewidth=0.6)
        ax.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1), color=cor))

    def caixa(a, b, cor, estilo):
        seg = bq.entre(bs, bq.hm(a), bq.hm(b))
        if not seg:
            return
        hi, lo = max(s[2] for s in seg), min(s[3] for s in seg)
        ax.add_patch(Rectangle((minutos(bq.hm(a)), lo), minutos(bq.hm(b)) - minutos(bq.hm(a)), hi - lo,
                               fill=False, edgecolor=cor, linestyle=estilo, linewidth=1))

    caixa("09:00", "10:00", "#999", ":")
    caixa("10:00", "11:30", "#999", ":")
    caixa("10:45", "11:08", "#d4a24c", "-")

    titulo = f"{dia}  "
    if tr:
        e0, e1 = minutos(tr["t_ent"]), minutos(tr["t_saida"] or tr["t_ent"])
        ax.hlines(tr["pool"], minutos(tr["t_pool"]), minutos(tr["t_sweep"]), color="#7a5195", linestyle="--", linewidth=1)
        ax.annotate("sweep", (minutos(tr["t_sweep"]), tr["pool"]), color="#7a5195", fontsize=8)
        ax.hlines(tr["entrada"], e0, e1, color="black", linewidth=1.2)
        ax.hlines(tr["stop"], e0, e1, color="#c0392b", linewidth=1)
        ax.hlines(tr["alvo"], e0, e1, color="#27ae60", linewidth=1)
        ax.plot([e0], [tr["entrada"]], marker="v" if tr["lado"] == -1 else "^", color="black")
        lado = "VENDA" if tr["lado"] == -1 else "COMPRA"
        titulo += (f"{lado} {tr['t_ent'].strftime('%H:%M')} @ {tr['entrada']:.0f}  "
                   f"stop {tr['stop']:.0f}  alvo {tr['alvo']:.0f}  ->  {tr['como']} "
                   f"{tr['pts']:+.0f} pts ({tr['pts'] / tr['risco']:+.2f}R)")
    else:
        titulo += "sem trade"
    ax.set_title(titulo, fontsize=10)
    ticks = list(range(540, 721, 15))
    ax.set_xticks(ticks, [f"{m // 60:02d}:{m % 60:02d}" for m in ticks], fontsize=8)
    ax.set_xlim(538, 722)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    SAIDA.mkdir(exist_ok=True)
    nome = SAIDA / f"{dia}_{'sem' if not tr else tr['como']}.png"
    fig.savefig(nome)
    plt.close(fig)
    return nome


def main():
    dias = bq.carregar()
    alvo_dia = sys.argv[1] if len(sys.argv) > 1 else None
    n = 0
    for dia, bs in sorted(dias.items()):
        if alvo_dia and str(dia) != alvo_dia:
            continue
        tr = detalhar(bs, bq.hm("10:45"), bq.hm("11:08"), bq.hm("11:30"))
        desenhar(dia, bs, tr)
        n += 1
    print(f"{n} graficos em {SAIDA}")


if __name__ == "__main__":
    main()
