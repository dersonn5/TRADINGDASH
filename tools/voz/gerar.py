"""Gera os audios da voz Dora (Kokoro pf_dora) para os alertas do cockpit.

Le tools/voz/frases.json (gerado por cockpit/scripts/listar-frases-voz.ts), grava so os
audios que ainda nao existem em cockpit/public/voz/ e reescreve o manifest.json.
Idempotente: rodar de novo nao gera nada que ja existe.

    C:/Users/Pc/kokoro-voz/Scripts/python.exe tools/voz/gerar.py

Mudou o dicionario de pronuncia (pronuncia.py)? Apagar os .ogg das frases afetadas
(ou a pasta inteira) e rodar de novo.
"""
import hashlib
import json
import os
import re

import numpy as np
import soundfile as sf

from pronuncia import para_fala

VOZ = "pf_dora"
VELOCIDADE = 1.0

AQUI = os.path.dirname(os.path.abspath(__file__))
FRASES = os.path.join(AQUI, "frases.json")
DESTINO = os.path.normpath(os.path.join(AQUI, "..", "..", "cockpit", "public", "voz"))


def normalizar(texto: str) -> str:
    # igual a normalizarFala() em cockpit/lib/voz-clipes.ts
    return re.sub(r"\s+", " ", texto.strip())


def arquivo_da_frase(texto: str) -> str:
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12] + ".ogg"


def main():
    os.makedirs(DESTINO, exist_ok=True)
    with open(FRASES, encoding="utf-8") as f:
        frases = [normalizar(t) for t in json.load(f)]

    faltam = [t for t in frases if not os.path.exists(os.path.join(DESTINO, arquivo_da_frase(t)))]
    print(f"{len(frases)} frases, {len(faltam)} sem audio")

    if faltam:
        from kokoro import KPipeline  # so carrega o modelo quando ha o que gerar

        pipeline = KPipeline(lang_code="p", repo_id="hexgrad/Kokoro-82M")
        for i, texto in enumerate(faltam, 1):
            fala = para_fala(texto)
            pedacos = [np.asarray(audio) for _, _, audio in pipeline(fala, voice=VOZ, speed=VELOCIDADE)]
            audio = np.concatenate(pedacos)
            sf.write(os.path.join(DESTINO, arquivo_da_frase(texto)), audio, 24000, format="OGG", subtype="VORBIS")
            print(f"[{i}/{len(faltam)}] {texto}")

    clipes = {t: arquivo_da_frase(t) for t in frases if os.path.exists(os.path.join(DESTINO, arquivo_da_frase(t)))}
    manifest = {"voz": VOZ, "velocidade": VELOCIDADE, "clipes": clipes}
    with open(os.path.join(DESTINO, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    total = sum(os.path.getsize(os.path.join(DESTINO, a)) for a in os.listdir(DESTINO))
    print(f"manifest: {len(clipes)} clipes · pasta {total / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
