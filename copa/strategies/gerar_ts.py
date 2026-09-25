"""Gera cockpit/data/strategies.ts a partir dos tres JSONs desta pasta.

Os JSONs sao a fonte: nunca editar o strategies.ts a mao. Rodar depois de mudar
qualquer JSON:  python copa/strategies/gerar_ts.py
O teste de sincronia (cockpit/scripts/verify.ts) confere JSON x TS.
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "..", "..", "cockpit", "data", "strategies.ts")
BLOCOS = [
    ("REVERSAO_HTF", "reversao_htf.json"),
    ("CONTINUIDADE_TENDENCIA", "continuidade_tendencia.json"),
    ("VARRIDA_BARRA_10", "varrida_barra_10.json"),
]


def ts(v):
    return json.dumps(v, ensure_ascii=False)


def bloco(const, j):
    L = [
        f"export const {const}: Strategy = {{",
        f"  id: {ts(j['id'])},",
        f"  ordem: {j['ordem']},",
        f"  nome: {ts(j['nome'])},",
        f"  mercado: {ts(j['mercado'])},",
        f"  descricao:\n    {ts(j['descricao'])},",
        f"  score_minimo: {j['score_minimo']},",
        "  calibracao: {",
        f"    status: {ts(j['calibracao']['status'])},",
        f"    observacao:\n      {ts(j['calibracao']['observacao'])},",
        f"    atualizado_em: {ts(j['calibracao']['atualizado_em'])},",
        "  },",
    ]
    for k in ("ambiente_favoravel", "ambiente_desfavoravel"):
        L.append(f"  {k}: [")
        L += [f"    {ts(x)}," for x in j[k]]
        L.append("  ],")
    L.append("  horarios_validos: [" + ", ".join(f"{{ inicio: {ts(h['inicio'])}, fim: {ts(h['fim'])} }}" for h in j["horarios_validos"]) + "],")
    L.append("  regras_ambiente: [")
    for r in j["regras_ambiente"]:
        L += ["    {", f"      campo: {ts(r['campo'])},", f"      op: {ts(r['op'])},", f"      valor: {json.dumps(r['valor'])},",
              f"      efeito: {ts(r['efeito'])},", f"      motivo: {ts(r['motivo'])},", "    },"]
    L.append("  ],")
    L.append("  checklist: [")
    for it in j["checklist"]:
        L += ["    {", f"      id: {ts(it['id'])},", f"      tipo: {ts(it['tipo'])},", f"      peso: {it['peso']},",
              f"      label: {ts(it['label'])},", f"      ajuda: {ts(it['ajuda'])},"]
        if "origem" in it:
            L.append(f"      origem: {ts(it['origem'])},")
        L.append("    },")
    L += ["  ] as any,", "};", ""]
    return "\n".join(L)


partes = ['import { Strategy } from "@/lib/types";', "",
          "// GERADO por copa/strategies/gerar_ts.py a partir dos JSONs. Nao editar a mao.", ""]
for const, arq in BLOCOS:
    j = json.load(open(os.path.join(AQUI, arq), encoding="utf-8"))
    partes.append(bloco(const, j))
partes.append("export const DEFAULT_STRATEGIES: Strategy[] = [" + ", ".join(c for c, _ in BLOCOS) + "];\n")
open(SAIDA, "w", encoding="utf-8").write("\n".join(partes))
print("strategies.ts gerado")
