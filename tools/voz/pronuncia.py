"""Dicionario de pronuncia para a voz Kokoro pf_dora (portugues do Brasil).

A voz le tudo como portugues: termo em ingles e sigla saem errados. Antes de gerar o
audio, cada termo e trocado pela grafia de como se fala. O texto na tela nao muda —
so o que a voz fala. O id do audio continua vindo do texto ORIGINAL.

Para corrigir uma palavra: acrescentar aqui, rodar tools/voz/amostra.py para ouvir e
depois regerar os audios.
"""
import re

# termo (como aparece no texto) -> como a voz deve ler. Ordem importa: o mais longo primeiro.
PRONUNCIA = [
    ("Empire State", "Émpaier Stêit"),
    ("IPCA-15", "í pê cê á quinze"),
    ("IBC-Br", "í bê cê bê érre"),
    ("IGP-M", "í gê pê ême"),
    ("Payroll", "Pêirôu"),
    ("Profit", "Prófit"),
    ("score", "iscór"),
    ("Powell", "Páuel"),
    ("Trump", "Trâmp"),
    ("Michigan", "Míchigan"),
    ("JOLTS", "Djôults"),
    ("Focus", "Fócus"),
    ("Caged", "Cajéd"),
    ("Copom", "Copôm"),
    ("Selic", "Sélic"),
    ("IPCA", "í pê cê á"),
    ("CPI", "cê pê í"),
    ("PPI", "pê pê í"),
    ("PCE", "pê cê é"),
    ("PMI", "pê ême í"),
    ("ISM", "í ésse ême"),
    ("ADP", "á dê pê"),
    ("PIB", "píbi"),
    ("Fed", "Féd"),
]


def para_fala(texto: str) -> str:
    """Troca os termos pela pronuncia. So palavra inteira, sem mexer em pedacos de outras."""
    for termo, fala in PRONUNCIA:
        texto = re.sub(rf"(?<![\wÀ-ÿ]){re.escape(termo)}(?![\wÀ-ÿ])", fala, texto)
    return texto
