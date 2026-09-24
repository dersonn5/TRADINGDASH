"""Analise dos trades reais do operador (export "Graficos e Operacoes" do Profit).

Uso: python profit/analise_trades.py "<arquivo.csv>" [...]

Mede, com o dinheiro do proprio operador:
  - resultado por horario de entrada;
  - resultado pela ordem da operacao no dia (1a, 2a, 3a, 4a+);
  - operacoes feitas depois de 2 stops no dia;
  - resultado por ativo e por operacao com preco medio (Medio = Sim);
  - o cenario com as regras de processo: entrada so 09:00-11:59, no maximo 3
    operacoes por dia, parar depois do 2o stop.
Os arquivos ficam fora do repositorio (dados pessoais da conta).
"""

import csv
import datetime as dt
import sys
from collections import defaultdict


def num(s):
    s = (s or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def ler(caminho):
    linhas = open(caminho, "rb").read().decode("cp1252").splitlines()
    i = next(k for k, l in enumerate(linhas) if l.startswith("Ativo;"))
    ops = []
    for r in csv.reader(linhas[i + 1:], delimiter=";"):
        if len(r) < 14 or not r[0].strip():
            continue
        ab = dt.datetime.strptime(r[1].strip(), "%d/%m/%Y %H:%M:%S")
        fe = dt.datetime.strptime(r[2].strip(), "%d/%m/%Y %H:%M:%S")
        ops.append(dict(ativo=r[0].strip(), ab=ab, fe=fe, lado=r[6].strip(),
                        qtd=max(num(r[4]), num(r[5])), medio=r[10].strip().lower().startswith("s"),
                        res=num(r[13]), pts=num(r[12])))
    ops.sort(key=lambda o: o["ab"])
    por_dia = defaultdict(list)
    for o in ops:
        por_dia[o["ab"].date()].append(o)
    for dia in por_dia.values():
        stops = 0
        for k, o in enumerate(dia):
            o["ordem"] = k + 1
            o["stops_antes"] = stops
            if o["res"] < 0:
                stops += 1
    return ops, por_dia


def estat(ops):
    n = len(ops)
    if not n:
        return "  -"
    g = [o["res"] for o in ops if o["res"] > 0]
    p = [o["res"] for o in ops if o["res"] < 0]
    fl = sum(g) / -sum(p) if p else float("inf")
    return (f"n={n:3d}  acerto {len(g) / n:4.0%}  resultado R$ {sum(o['res'] for o in ops):+9,.0f}  "
            f"fator {fl:4.2f}  medio R$ {sum(o['res'] for o in ops) / n:+6.0f}").replace(",", ".")


def faixa_hora(o):
    h = o["ab"].hour * 60 + o["ab"].minute
    if h < 600:
        return "1) 09:00-09:59"
    if h < 660:
        return "2) 10:00-10:59"
    if h < 720:
        return "3) 11:00-11:59"
    if h < 840:
        return "4) 12:00-13:59"
    return "5) 14:00 em diante"


def relatorio(caminho):
    ops, por_dia = ler(caminho)
    nome = caminho.replace("\\", "/").split("/")[-1]
    print(f"\n{'=' * 100}\n{nome}: {len(ops)} operacoes em {len(por_dia)} pregoes "
          f"({len(ops) / len(por_dia):.1f} por dia)\n{'=' * 100}")
    print(f"TOTAL               {estat(ops)}")

    print("\nPor horario de entrada:")
    grupos = defaultdict(list)
    for o in ops:
        grupos[faixa_hora(o)].append(o)
    for k in sorted(grupos):
        print(f"  {k:<18} {estat(grupos[k])}")

    print("\nPela ordem da operacao no dia:")
    for rot, f in (("1a", lambda o: o["ordem"] == 1), ("2a", lambda o: o["ordem"] == 2),
                   ("3a", lambda o: o["ordem"] == 3), ("4a em diante", lambda o: o["ordem"] >= 4)):
        print(f"  {rot:<18} {estat([o for o in ops if f(o)])}")

    print("\nStops ja tomados no dia antes da operacao:")
    for rot, f in (("0 stops", lambda o: o["stops_antes"] == 0), ("1 stop", lambda o: o["stops_antes"] == 1),
                   ("2 ou mais", lambda o: o["stops_antes"] >= 2)):
        print(f"  {rot:<18} {estat([o for o in ops if f(o)])}")

    print("\nPor ativo:")
    for a in sorted({o["ativo"][:3] for o in ops}):
        print(f"  {a:<18} {estat([o for o in ops if o['ativo'].startswith(a)])}")
    print(f"\nCom preco medio     {estat([o for o in ops if o['medio']])}")
    print(f"Sem preco medio     {estat([o for o in ops if not o['medio']])}")

    # Cenario com as regras de processo
    filtrado = []
    for dia in por_dia.values():
        feitas = stops = 0
        for o in dia:
            if not (9 <= o["ab"].hour < 12):
                continue
            if feitas >= 3 or stops >= 2:
                break
            filtrado.append(o)
            feitas += 1
            if o["res"] < 0:
                stops += 1
    fora = [o for o in ops if o not in filtrado]
    print("\nREGRAS: so 09:00-11:59, max 3 operacoes/dia, parar no 2o stop")
    print(f"  mantidas           {estat(filtrado)}")
    print(f"  cortadas           {estat(fora)}")

    print("\nPiores dias (resultado) e quantas operacoes:")
    dias = sorted(por_dia.items(), key=lambda kv: sum(o["res"] for o in kv[1]))
    for d, dia in dias[:5]:
        tarde = sum(1 for o in dia if o["ab"].hour >= 12)
        print(f"  {d}  R$ {sum(o['res'] for o in dia):+7,.0f}  {len(dia):2d} operacoes ({tarde} a tarde)".replace(",", "."))


if __name__ == "__main__":
    for arq in sys.argv[1:]:
        relatorio(arq)
