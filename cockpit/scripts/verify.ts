import fs from "fs";
import path from "path";
import {
  classificarJanela,
  scoreMinimoEfetivo,
  avaliarGate,
  passosCumpridos,
  estadoDosPassos,
  alternarPasso,
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

// -------------------------------------------------------------
// 4. CASOS DE SEQUÊNCIA E TRILHA TRAVADA (7 KILL)
// -------------------------------------------------------------
const make7Kills = (checkedIndices: number[] = []): ItemAvaliado[] => {
  const set = new Set(checkedIndices);
  return Array.from({ length: 7 }, (_, i) => ({
    id: `k${i + 1}`,
    tipo: "KILL",
    label: `Passo ${i + 1}`,
    checked: set.has(i + 1),
    peso: 0,
  }));
};

// Caso 1: Nenhum marcado -> passosCumpridos = 0; estados = ["AGORA", "TRAVADO" x 6]
const seq1Itens = make7Kills([]);
const seq1Cumpridos = passosCumpridos(seq1Itens);
const seq1Estados = estadoDosPassos(seq1Itens);
const seq1Esperado = ["AGORA", "TRAVADO", "TRAVADO", "TRAVADO", "TRAVADO", "TRAVADO", "TRAVADO"];
const seq1Ok =
  seq1Cumpridos === 0 &&
  seq1Estados.length === 7 &&
  seq1Estados.every((e, idx) => e === seq1Esperado[idx]);
report(
  "Sequência Caso 1: Nenhum marcado -> cumpridos=0, estados=['AGORA', 'TRAVADO' x 6]",
  seq1Ok,
  `cumpridos=${seq1Cumpridos}, estados=${JSON.stringify(seq1Estados)}`
);

// Caso 2: k1-k3 marcados -> passosCumpridos = 3; estado do k4 = AGORA, k5 = TRAVADO
const seq2Itens = make7Kills([1, 2, 3]);
const seq2Cumpridos = passosCumpridos(seq2Itens);
const seq2Estados = estadoDosPassos(seq2Itens);
const seq2Ok =
  seq2Cumpridos === 3 &&
  seq2Estados[3] === "AGORA" &&
  seq2Estados[4] === "TRAVADO";
report(
  "Sequência Caso 2: k1-k3 marcados -> cumpridos=3, k4=AGORA, k5=TRAVADO",
  seq2Ok,
  `cumpridos=${seq2Cumpridos}, k4=${seq2Estados[3]}, k5=${seq2Estados[4]}`
);

// Caso 3: alternarPasso no k4 quando k1-k3 estão marcados -> k4 marcado, cumpridos = 4
const seq3Itens = alternarPasso(seq2Itens, "k4");
const seq3K4Marcado = seq3Itens.find((i) => i.id === "k4")?.checked === true;
const seq3Cumpridos = passosCumpridos(seq3Itens);
const seq3Ok = seq3K4Marcado && seq3Cumpridos === 4;
report(
  "Sequência Caso 3: alternarPasso no k4 com k1-k3 marcados -> k4 marcado, cumpridos=4",
  seq3Ok,
  `k4=${seq3K4Marcado}, cumpridos=${seq3Cumpridos}`
);

// Caso 4: alternarPasso no k6 quando só k1-k3 estão marcados -> lista inalterada (travado não responde)
const seq4Itens = alternarPasso(seq2Itens, "k6");
const seq4Inalterada =
  seq4Itens.length === seq2Itens.length &&
  seq4Itens.every((item, idx) => item.checked === seq2Itens[idx].checked && item.id === seq2Itens[idx].id);
report(
  "Sequência Caso 4: alternarPasso no k6 com k1-k3 marcados -> lista inalterada (travado não responde)",
  seq4Inalterada,
  `inalterada=${seq4Inalterada}`
);

// Caso 5: k1-k7 todos marcados, alternarPasso no k3 -> k3, k4, k5, k6, k7 desmarcados, k1 e k2 intactos, cumpridos = 2
const seq5Todos = make7Kills([1, 2, 3, 4, 5, 6, 7]);
const seq5DepoisK3 = alternarPasso(seq5Todos, "k3");
const seq5K1K2Intactos =
  seq5DepoisK3.find((i) => i.id === "k1")?.checked === true &&
  seq5DepoisK3.find((i) => i.id === "k2")?.checked === true;
const seq5K3aK7Desmarcados = [3, 4, 5, 6, 7].every(
  (n) => seq5DepoisK3.find((i) => i.id === `k${n}`)?.checked === false
);
const seq5Cumpridos = passosCumpridos(seq5DepoisK3);
const seq5Ok = seq5K1K2Intactos && seq5K3aK7Desmarcados && seq5Cumpridos === 2;
report(
  "Sequência Caso 5: k1-k7 marcados, alternarPasso no k3 -> k3-k7 desmarcados, k1-k2 intactos, cumpridos=2",
  seq5Ok,
  `k1,k2=${seq5K1K2Intactos}, k3-k7 desmarcados=${seq5K3aK7Desmarcados}, cumpridos=${seq5Cumpridos}`
);

// Caso 6: Marcar KILL fora de ordem direto no array (k1 e k5 marcados, k2-k4 não) -> passosCumpridos = 1 (conta só os consecutivos do começo)
const seq6Itens = make7Kills([1, 5]);
const seq6Cumpridos = passosCumpridos(seq6Itens);
const seq6Ok = seq6Cumpridos === 1;
report(
  "Sequência Caso 6: KILL fora de ordem (k1 e k5 marcados) -> cumpridos=1 (só consecutivos)",
  seq6Ok,
  `cumpridos=${seq6Cumpridos}`
);

if (hasErrors) {
  console.error("\n❌ Verificação finalizou com ERROS.");
  process.exit(1);
} else {
  console.log("\n✅ Todos os testes passaram com sucesso!");
  process.exit(0);
}
