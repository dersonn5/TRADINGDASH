/**
 * Lista todas as frases que precisam de audio da voz Dora e grava tools/voz/frases.json.
 * Depois: tools/voz/gerar.py gera os audios que faltam. Spec: SPEC_VOZ_KOKORO.md §3.
 * Rodar sempre que mudar um texto em lib/alertas.ts ou um nome em lib/calendario.ts:
 *   npx tsx scripts/listar-frases-voz.ts
 */
import fs from "fs";
import path from "path";
import {
  FRASE_TESTE, alertasDoDia, fraseAs, fraseNoticiaAgora, fraseNoticiaAntes, fraseQuantasNoticias, frasePrimeira, somarMinutos,
} from "../lib/alertas";
import { EVENTOS_BRASIL, NOMES_EUA } from "../lib/calendario";
import { normalizarFala } from "../lib/voz-clipes";

const frases = new Set<string>();
const add = (t: string) => frases.add(normalizarFala(t));

add(FRASE_TESTE);

// Rotina: NY as 10:30 (setembro) e as 11:30 (janeiro), pre-sessao aberta (inclui o aviso das 09:45)
for (const data of ["2026-09-25", "2026-01-15"]) {
  for (const a of alertasDoDia(data, [], false)) a.segmentos.forEach(add);
}

// Noticias e resumo das 09:00
const nomes = [...NOMES_EUA, ...EVENTOS_BRASIL];
for (const nome of nomes) {
  add(fraseNoticiaAntes(nome));
  add(fraseNoticiaAgora(nome));
  add(frasePrimeira(nome));
}
for (let n = 1; n <= 6; n++) add(fraseQuantasNoticias(n));
for (let h = somarMinutos("08:00", 0); ; h = somarMinutos(h, 5)) {
  add(fraseAs(h));
  if (h === "18:00") break;
}

const saida = path.resolve(__dirname, "../../tools/voz/frases.json");
fs.writeFileSync(saida, JSON.stringify([...frases], null, 2) + "\n", "utf-8");
console.log(`${frases.size} frases -> ${saida}`);
