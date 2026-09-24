"""A abertura das 09:00 vai pra um lado e depois reverte? Contagem descritiva.

Definicoes (combinadas em 22/09/2026, antes de rodar):
  Inicio   = um horario (09:00 e, como controle, 10:00, 11:00, 13:00, 14:00, 15:00).
  Impulso  = direcao dos primeiros 5 min: fechamento do 5o candle - abertura do 1o.
             Tamanho do impulso = o quanto o preco foi a favor dele nesses 5 min.
  Horizonte = do 6o minuto ate 60 min depois do inicio.
  Reversao LEVE  = no horizonte, o preco cruza de volta o preco de abertura.
  Reversao MEDIA = cruza a abertura E anda do outro lado pelo menos o tamanho
                   do impulso.
  Reversao FORTE = rompe o extremo oposto dos primeiros 15 min.

A comparacao com outros horarios e o controle: a pergunta nao e so "quanto
reverte", e "reverte MAIS que no resto do dia".

Saida: resumo no terminal e profit/abertura_0900_por_dia.csv, um pregao por
linha, para conferir no Profit.
"""

import csv
import datetime as dt
from pathlib import Path

import backtest_quarters as bq
from ny_1030 import mais


def medir(bs, inicio):
    x = bq.entre(bs, inicio, mais(inicio, 60))
    if len(x) < 55:
        return None
    o0 = x[0][1]
    imp = x[4][4] - o0
    if imp == 0:
        return None
    up = imp > 0
    tam = (max(b[2] for b in x[:5]) - o0) if up else (o0 - min(b[3] for b in x[:5]))
    hi15, lo15 = max(b[2] for b in x[:15]), min(b[3] for b in x[:15])
    resto = x[5:]
    if up:
        leve = any(b[3] < o0 for b in resto)
        media = any(b[3] <= o0 - tam for b in resto)
        forte = any(b[3] < lo15 for b in x[15:])
    else:
        leve = any(b[2] > o0 for b in resto)
        media = any(b[2] >= o0 + tam for b in resto)
        forte = any(b[2] > hi15 for b in x[15:])
    fim = x[-1][4]
    return dict(dir="alta" if up else "baixa", impulso=round(tam), leve=leve, media=media,
                forte=forte, abertura=o0, fech_60=fim,
                fechou_contra=(fim < o0) if up else (fim > o0))


def main():
    dias = bq.carregar()
    print(f"{len(dias)} pregoes\n")
    print(f"{'inicio':<7} {'dias':>4}  {'leve':>5} {'media':>6} {'forte':>6}  {'fechou contra em 60min':>22}")
    for h in ("09:00", "10:00", "11:00", "13:00", "14:00", "15:00"):
        rs = [r for r in (medir(bs, bq.hm(h)) for bs in dias.values()) if r]
        n = len(rs)
        f = lambda k: sum(r[k] for r in rs) / n
        print(f"{h:<7} {n:4d}  {f('leve'):5.0%} {f('media'):6.0%} {f('forte'):6.0%}  {f('fechou_contra'):22.0%}")

    destino = Path(__file__).parent / "abertura_0900_por_dia.csv"
    with destino.open("w", newline="") as fp:
        w = csv.writer(fp, delimiter=";")
        w.writerow(["data", "impulso_5min", "tamanho_pts", "rev_leve", "rev_media", "rev_forte",
                    "abertura_0900", "fech_1000", "fechou_contra"])
        for d, bs in sorted(dias.items()):
            r = medir(bs, bq.hm("09:00"))
            if r:
                sn = lambda v: "sim" if v else "nao"
                w.writerow([d, r["dir"], r["impulso"], sn(r["leve"]), sn(r["media"]), sn(r["forte"]),
                            int(r["abertura"]), int(r["fech_60"]), sn(r["fechou_contra"])])
    print(f"\ndia a dia: {destino.name}")


if __name__ == "__main__":
    main()
