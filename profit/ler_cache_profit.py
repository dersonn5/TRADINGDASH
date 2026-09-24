"""Converte o cache local do Profit (arquivos .min) em CSV.

O "Exportar dados" do Profit nao gerou arquivo. Mas o Profit guarda o historico
que ja baixou em AppData/Roaming/Nelogica/Profit/database/assets/<ATIVO>/,
um arquivo por ativo, periodo e ano.

Formato do .min (descoberto e conferido contra precos conhecidos de 22/09/2026):
  registro fixo de 128 bytes, little-endian
    offset  0: double  data/hora no formato TDateTime do Delphi
                       (dias desde 30/12/1899), horario de Brasilia
    offset 16: double  abertura
    offset 24: double  maxima
    offset 32: double  minima
    offset 40: double  fechamento
  o resto do registro (volume, negocios...) nao e usado aqui.

Nome do arquivo: <ATIVO>_F_0_1_<minutos>_1_1_0_<ano>.min
  ex.: WINFUT_F_0_1_1_1_1_0_2026.min  -> 1 minuto, 2026
       WINFUT_F_0_1_15_1_1_0_2025.min -> 15 minutos, 2025

O cache so tem o que o Profit ja carregou num grafico. Para ter mais historico,
abrir o grafico no periodo desejado e rolar para a esquerda antes de rodar.

Uso:
  python profit/ler_cache_profit.py WINFUT 1
  python profit/ler_cache_profit.py WINFUT 15
"""

import csv
import datetime as dt
import struct
import sys
from pathlib import Path

CACHE = Path.home() / "AppData/Roaming/Nelogica/Profit/database/assets"
SAIDA = Path(__file__).parent
REGISTRO = 128
DELPHI_ZERO = dt.datetime(1899, 12, 30)


def ler_arquivo(caminho: Path):
    dados = caminho.read_bytes()
    if len(dados) % REGISTRO != 0:
        raise ValueError(f"{caminho.name}: tamanho {len(dados)} nao e multiplo de {REGISTRO}")
    for k in range(len(dados) // REGISTRO):
        base = k * REGISTRO
        (t,) = struct.unpack_from("<d", dados, base)
        o, h, l, c = struct.unpack_from("<4d", dados, base + 16)
        # Arredonda para o segundo: o double do Delphi carrega ruido de ponto flutuante.
        quando = DELPHI_ZERO + dt.timedelta(seconds=round(t * 86400))
        yield quando, o, h, l, c


def main():
    ativo = sys.argv[1] if len(sys.argv) > 1 else "WINFUT"
    minutos = sys.argv[2] if len(sys.argv) > 2 else "1"

    pasta = CACHE / f"{ativo}_F_0"
    arquivos = sorted(pasta.glob(f"{ativo}_F_0_1_{minutos}_1_1_0_*.min"))
    if not arquivos:
        sys.exit(f"Nenhum arquivo de {minutos} min para {ativo} em {pasta}")

    barras = {}
    for arq in arquivos:
        for linha in ler_arquivo(arq):
            barras[linha[0]] = linha  # dedup por horario entre arquivos

    ordenadas = [barras[k] for k in sorted(barras)]
    destino = SAIDA / f"{ativo}_{minutos}min.csv"
    with destino.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datetime", "open", "high", "low", "close"])
        for quando, o, h, l, c in ordenadas:
            w.writerow([quando.strftime("%Y-%m-%d %H:%M:%S"), o, h, l, c])

    dias = sorted({b[0].date() for b in ordenadas})
    print(f"{destino.name}: {len(ordenadas)} barras, {len(dias)} dias, {dias[0]} a {dias[-1]}")


if __name__ == "__main__":
    main()
