"""Gera amostras da voz Kokoro (pf_dora, portugues do Brasil) para o operador ouvir.

Rodar com o Python do ambiente isolado (fora do projeto, por causa do "Ç" no caminho):
    C:/Users/Pc/kokoro-voz/Scripts/python.exe tools/voz/amostra.py [voz] [velocidade]
Saida: tools/voz/amostras/*.wav — ja com o dicionario de pronuncia (pronuncia.py).
"""
import os
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from pronuncia import para_fala

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "amostras")
os.makedirs(SAIDA, exist_ok=True)

FRASES = {
    "abertura_a_vista": "Abertura do mercado à vista. Janela de entrada aberta.",
    "noticia_payroll": "Atenção: em cinco minutos, Payroll. Impacto alto.",
    "bom_dia": "Bom dia. O pregão abriu. Até as dez, só observar e marcar. Hoje tem uma notícia de impacto alto. A primeira é CPI, inflação ao consumidor, às nove e meia.",
    "fim_janela_nobre": "Fim da janela nobre. A partir de agora, só com score oitenta.",
    "fechar_profit": "Fim do pregão do plano. Feche o Profit.",
    "termos_eua": "Saindo agora: fala do Powell. Saindo agora: ISM de serviços. Saindo agora: JOLTS, vagas de emprego. Saindo agora: núcleo do PCE. Saindo agora: decisão de juros do Fed.",
    "termos_brasil": "Saindo agora: IPCA-15. Saindo agora: decisão do Copom. Saindo agora: PIB brasileiro. Saindo agora: Caged.",
}

VOZ = sys.argv[1] if len(sys.argv) > 1 else "pf_dora"
VELOCIDADE = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

pipeline = KPipeline(lang_code="p", repo_id="hexgrad/Kokoro-82M")
for nome, texto in FRASES.items():
    fala = para_fala(texto)
    pedacos = [audio for _, _, audio in pipeline(fala, voice=VOZ, speed=VELOCIDADE)]
    audio = np.concatenate([np.asarray(p) for p in pedacos])
    caminho = os.path.join(SAIDA, f"{VOZ}_{nome}.wav")
    sf.write(caminho, audio, 24000)
    print(f"{os.path.basename(caminho)}  ({len(audio) / 24000:.1f} s)  fala: {fala}")
