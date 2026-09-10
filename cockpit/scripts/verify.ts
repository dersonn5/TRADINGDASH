import fs from "fs";
import path from "path";
import {
  classificarJanela,
  scoreMinimoEfetivo,
  avaliarGate,
  ItemAvaliado,
  Janela,
} from "../lib/gate";
import { PLAYBOOK_ANDERSON } from "../data/strategies";

let hasErrors = false;

function report(testName: string, passed: boolean, details?: string) {
  if (passed) {
    console.log(`[OK] ${testName}`);
  } else {
    hasErrors = true;
    console.error(`[FALHOU] ${testName}${details ? ` -> ${details}` : ""}`);
  }
}

/**
 * Cria uma Date em UTC correspondente a hora:minuto exatos em America/Sao_Paulo (UTC-3 fixo).
 */
function makeSPDate(hour: number, minute: number): Date {
  return new Date(Date.UTC(2026, 8, 14, hour + 3, minute, 0));
}

console.log("=== VERIFICAÇÃO DE GATE, JANELAS E SINCRONIA ===\n");

// -------------------------------------------------------------
// 1. CASOS DE JANELA
// -------------------------------------------------------------
const casosJanela: Array<{
  horaSP: string;
  hour: number;
  minute: number;
  janelaEsperada: Janela;
  scoreMinEsperado: number;
}> = [
  { horaSP: "10:30", hour: 10, minute: 30, janelaEsperada: "PRIME", scoreMinEsperado: 65 },
  { horaSP: "10:00", hour: 10, minute: 0, janelaEsperada: "PRIME", scoreMinEsperado: 65 },
  { horaSP: "10:59", hour: 10, minute: 59, janelaEsperada: "PRIME", scoreMinEsperado: 65 },
  { horaSP: "11:00", hour: 11, minute: 0, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "09:30", hour: 9, minute: 30, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "11:59", hour: 11, minute: 59, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "08:59", hour: 8, minute: 59, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
  { horaSP: "13:00", hour: 13, minute: 0, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
];

for (const caso of casosJanela) {
  const d = makeSPDate(caso.hour, caso.minute);
  const j = classificarJanela(d);
  const s = scoreMinimoEfetivo(j, 65);
  const janelaOk = j === caso.janelaEsperada;
  const scoreOk = s === caso.scoreMinEsperado;
  report(
    `Janela ${caso.horaSP} (esperado ${caso.janelaEsperada}, score min ${caso.scoreMinEsperado === Infinity ? "bloqueado" : caso.scoreMinEsperado})`,
    janelaOk && scoreOk,
    `obteve janela=${j}, scoreMin=${s}`
  );
}

// -------------------------------------------------------------
// 2. CASOS DE GATE
// -------------------------------------------------------------
const killsBase: ItemAvaliado[] = PLAYBOOK_ANDERSON.checklist
  .filter((i) => i.tipo === "KILL")
  .map((i) => ({
    id: i.id,
    tipo: "KILL",
    label: i.label,
    checked: true,
    peso: 0,
  }));

// Cenário 1: Todos os 7 KILL marcados + PONTO somando 70, às 10:30 -> liberado === true
const itensCaso1: ItemAvaliado[] = [
  ...killsBase,
  { id: "p_test_70", tipo: "PONTO", label: "Confluências 70", checked: true, peso: 70 },
];
const gate1 = avaliarGate(itensCaso1, "BULLISH", makeSPDate(10, 30));
report("Gate Caso 1: 7 KILLs + 70 pts às 10:30 -> liberado === true", gate1.liberado === true, JSON.stringify(gate1.motivos));

// Cenário 2: Mesmo conjunto às 09:30 -> liberado === false, motivo cita score 70 e mínimo 80
const gate2 = avaliarGate(itensCaso1, "BULLISH", makeSPDate(9, 30));
const gate2Bloqueado = gate2.liberado === false;
const gate2CitaScore = gate2.motivos.some(
  (m) => m.includes("score 70") && m.includes("80")
);
report(
  "Gate Caso 2: Mesmo conjunto às 09:30 -> liberado === false e cita score 70 e mínimo 80",
  gate2Bloqueado && gate2CitaScore,
  `liberado=${gate2.liberado}, motivos=${JSON.stringify(gate2.motivos)}`
);

// Cenário 3: Todos os PONTO marcados (100) e um KILL faltando, às 10:30 -> liberado === false, motivo nomeia o KILL que falta
const killsComUmFaltando = killsBase.map((k, idx) =>
  idx === 0 ? { ...k, checked: false } : { ...k, checked: true }
);
const itensCaso3: ItemAvaliado[] = [
  ...killsComUmFaltando,
  { id: "p_test_100", tipo: "PONTO", label: "Confluências 100", checked: true, peso: 100 },
];
const gate3 = avaliarGate(itensCaso3, "BULLISH", makeSPDate(10, 30));
const gate3Bloqueado = gate3.liberado === false;
const killFaltanteLabel = killsBase[0].label;
const gate3NomeiaKill = gate3.motivos.some((m) => m.includes(killFaltanteLabel));
report(
  "Gate Caso 3: 100 pts com um KILL faltando às 10:30 -> liberado === false e nomeia o KILL",
  gate3Bloqueado && gate3NomeiaKill,
  `liberado=${gate3.liberado}, motivos=${JSON.stringify(gate3.motivos)}`
);

// Cenário 4: bias === "NAO_OPERAR" com tudo marcado às 10:30 -> liberado === false
const todosMarcados: ItemAvaliado[] = [
  ...killsBase,
  { id: "p_test_100", tipo: "PONTO", label: "Confluências 100", checked: true, peso: 100 },
];
const gate4 = avaliarGate(todosMarcados, "NAO_OPERAR", makeSPDate(10, 30));
const gate4Bloqueado = gate4.liberado === false;
const gate4MotivoBias = gate4.motivos.includes("bias do dia marcado como NAO_OPERAR");
report(
  "Gate Caso 4: bias === 'NAO_OPERAR' com tudo marcado às 10:30 -> liberado === false",
  gate4Bloqueado && gate4MotivoBias,
  `liberado=${gate4.liberado}, motivos=${JSON.stringify(gate4.motivos)}`
);

// -------------------------------------------------------------
// 3. CASO DE SINCRONIA: playbook_anderson.json vs strategies.ts
// -------------------------------------------------------------
const possibleJsonPaths = [
  path.resolve(process.cwd(), "copa/strategies/playbook_anderson.json"),
  path.resolve(__dirname, "../../copa/strategies/playbook_anderson.json"),
];
const jsonPath = possibleJsonPaths.find((p) => fs.existsSync(p));

if (!jsonPath) {
  report("Sincronia: encontrar playbook_anderson.json", false, "Arquivo JSON não encontrado");
} else {
  try {
    const rawJson = fs.readFileSync(jsonPath, "utf-8");
    const jsonPlaybook = JSON.parse(rawJson);
    const jsonChecklist: Array<{ id: string; tipo: string; peso: number }> = jsonPlaybook.checklist || [];
    const tsChecklist = PLAYBOOK_ANDERSON.checklist;

    const jsonIds = jsonChecklist.map((i) => i.id).sort();
    const tsIds = tsChecklist.map((i) => i.id).sort();

    const idsIguais =
      jsonIds.length === tsIds.length &&
      jsonIds.every((id, idx) => id === tsIds[idx]);

    let tiposPesosIguais = true;
    let detalheErro = "";

    if (idsIguais) {
      for (const jItem of jsonChecklist) {
        const tItem = tsChecklist.find((t) => t.id === jItem.id);
        if (!tItem) {
          tiposPesosIguais = false;
          detalheErro = `Item ${jItem.id} ausente no TS`;
          break;
        }
        if (tItem.tipo !== jItem.tipo || tItem.peso !== jItem.peso) {
          tiposPesosIguais = false;
          detalheErro = `Item ${jItem.id} diverge: JSON(tipo=${jItem.tipo}, peso=${jItem.peso}) vs TS(tipo=${tItem.tipo}, peso=${tItem.peso})`;
          break;
        }
      }
    }

    report(
      "Sincronia: mesmo conjunto de IDs, mesmo tipo e mesmo peso entre JSON e TS",
      idsIguais && tiposPesosIguais,
      detalheErro
    );
  } catch (err: any) {
    report("Sincronia: leitura e parsing do JSON", false, err?.message);
  }
}

if (hasErrors) {
  console.error("\n❌ Verificação finalizou com ERROS.");
  process.exit(1);
} else {
  console.log("\n✅ Todos os testes passaram com sucesso!");
  process.exit(0);
}
