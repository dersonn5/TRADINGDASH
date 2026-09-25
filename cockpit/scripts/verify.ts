import fs from "fs";
import { montarVisaoGeral } from "../lib/visao-geral";
import { TRADES_DESIGN } from "./fixture-design";
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
  avaliarLimitesDia,
  mercadoPermitido,
} from "../lib/gate";
import { REVERSAO_HTF, CONTINUIDADE_TENDENCIA, VARRIDA_BARRA_10 } from "../data/strategies";
import { gradeFor, pendenciasDaPreSessao, PreSessao, validarCamposNovosTrade } from "../lib/copa-db";
import {
  TradeMetricas,
  calcularKPIsGerais,
  calcularDrawdown,
  agruparPorEstrategia,
  agruparPorHorario,
  agruparPorGatilho,
  calcularDistribuicaoStops,
  calcularDisciplina,
  agruparSetupCeContexto,
  classificarFaixaHorario,
  formatarBRL,
  formatarR,
  formatarNumero,
  formatarPct,
} from "../lib/metricas";

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
// 1. CASOS DE JANELA (8 casos)
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
  { horaSP: "09:30", hour: 9, minute: 30, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
  { horaSP: "09:59", hour: 9, minute: 59, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
  { horaSP: "11:29", hour: 11, minute: 29, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "11:30", hour: 11, minute: 30, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
  { horaSP: "11:59", hour: 11, minute: 59, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
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
// 2. CASOS DE GATE (4 casos)
// -------------------------------------------------------------
const killsBase: ItemAvaliado[] = REVERSAO_HTF.checklist
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

// Cenário 2: Mesmo conjunto às 11:15 -> liberado === false, motivo cita score 70 e mínimo 80
const gate2 = avaliarGate(itensCaso1, "BULLISH", makeSPDate(11, 15));
const gate2Bloqueado = gate2.liberado === false;
const gate2CitaScore = gate2.motivos.some(
  (m) => m.includes("score 70") && m.includes("80")
);
report(
  "Gate Caso 2: Mesmo conjunto às 11:15 -> liberado === false e cita score 70 e mínimo 80",
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
// 3. CASO DE SINCRONIA E PESOS: JSONs vs strategies.ts (1 caso)
// -------------------------------------------------------------
function checarEstrategia(
  filename: string,
  tsStrat: typeof REVERSAO_HTF,
  killsEsperados: number,
  pontosEsperados: number,
  somaPontosEsperada: number
): { ok: boolean; detalhe: string } {
  const possiblePaths = [
    path.resolve(process.cwd(), `copa/strategies/${filename}`),
    path.resolve(__dirname, `../../copa/strategies/${filename}`),
  ];
  const foundPath = possiblePaths.find((p) => fs.existsSync(p));
  if (!foundPath) {
    return { ok: false, detalhe: `Arquivo ${filename} não encontrado` };
  }

  const rawJson = fs.readFileSync(foundPath, "utf-8");
  const jsonStrat = JSON.parse(rawJson);
  const jsonChecklist: Array<{ id: string; tipo: string; peso: number; label: string }> =
    jsonStrat.checklist || [];
  const tsChecklist = tsStrat.checklist;

  const jsonIds = jsonChecklist.map((i) => i.id).sort();
  const tsIds = tsChecklist.map((i) => i.id).sort();

  if (jsonIds.length !== tsIds.length || !jsonIds.every((id, idx) => id === tsIds[idx])) {
    return { ok: false, detalhe: `${filename}: IDs divergem entre JSON e TS` };
  }

  for (const jItem of jsonChecklist) {
    const tItem = tsChecklist.find((t) => t.id === jItem.id);
    if (!tItem) {
      return { ok: false, detalhe: `${filename}: Item ${jItem.id} ausente no TS` };
    }
    if (tItem.tipo !== jItem.tipo || tItem.peso !== jItem.peso || tItem.label !== jItem.label) {
      return {
        ok: false,
        detalhe: `${filename}: Item ${jItem.id} diverge em tipo, peso ou label`,
      };
    }
  }

  const numKills = tsChecklist.filter((i) => i.tipo === "KILL").length;
  const numPontos = tsChecklist.filter((i) => i.tipo === "PONTO").length;
  const somaPontos = tsChecklist
    .filter((i) => i.tipo === "PONTO")
    .reduce((acc, i) => acc + i.peso, 0);

  if (numKills !== killsEsperados || numPontos !== pontosEsperados || somaPontos !== somaPontosEsperada) {
    return {
      ok: false,
      detalhe: `${filename}: contagem ou pesos incorretos (KILL=${numKills}/${killsEsperados}, PONTO=${numPontos}/${pontosEsperados}, soma=${somaPontos}/${somaPontosEsperada})`,
    };
  }

  return { ok: true, detalhe: "" };
}

const resRev = checarEstrategia("reversao_htf.json", REVERSAO_HTF, 7, 6, 100);
const resCont = checarEstrategia("continuidade_tendencia.json", CONTINUIDADE_TENDENCIA, 6, 6, 100);
const resVarr = checarEstrategia("varrida_barra_10.json", VARRIDA_BARRA_10, 7, 5, 100);
const sincroniaOk = resRev.ok && resCont.ok && resVarr.ok;
const detalheSincronia = [resRev.detalhe, resCont.detalhe, resVarr.detalhe].filter(Boolean).join(" | ");

report(
  "Sincronia: três estratégias idênticas aos JSONs e pesos somando 100",
  sincroniaOk,
  detalheSincronia
);

// -------------------------------------------------------------
// 4. CASOS DE SEQUÊNCIA E TRILHA TRAVADA (7 KILL) (6 casos)
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

// -------------------------------------------------------------
// 5. CASOS DE AVALIAR LIMITES DIA (8 casos)
// -------------------------------------------------------------
const baseTime = makeSPDate(10, 30);

// Caso 1: 0 perdas, 0 operações, sem loss -> liberado
const lim1 = avaliarLimitesDia(0, 0, null, baseTime);
report(
  "Limites Caso 1: 0 perdas, 0 operacoes, sem loss -> liberado",
  !lim1.bloqueado && lim1.motivos.length === 0,
  JSON.stringify(lim1.motivos)
);

// Caso 2: 2 perdas, 3 operações, loss há 40 min -> liberado
const loss40 = new Date(baseTime.getTime() - 40 * 60 * 1000);
const lim2 = avaliarLimitesDia(2, 3, loss40, baseTime);
report(
  "Limites Caso 2: 2 perdas, 3 operacoes, loss ha 40 min -> liberado",
  !lim2.bloqueado && lim2.motivos.length === 0,
  JSON.stringify(lim2.motivos)
);

// Caso 3: 3 perdas -> bloqueado, motivo cita pregão encerrado
const lim3 = avaliarLimitesDia(3, 3, null, baseTime);
report(
  "Limites Caso 3: 3 perdas -> bloqueado, motivo cita pregao encerrado",
  lim3.bloqueado && lim3.motivos.some((m) => m.includes("pregão encerrado")),
  JSON.stringify(lim3.motivos)
);

// Caso 4: 5 operações -> bloqueado, motivo cita limite de operações
const lim4 = avaliarLimitesDia(0, 5, null, baseTime);
report(
  "Limites Caso 4: 5 operacoes -> bloqueado, motivo cita limite de operacoes",
  lim4.bloqueado && lim4.motivos.some((m) => m.includes("limite atingido") || m.includes("5 operações")),
  JSON.stringify(lim4.motivos)
);

// Caso 5: 1 perda, loss há 10 min -> bloqueado, motivo cita 20 min restantes
const loss10 = new Date(baseTime.getTime() - 10 * 60 * 1000);
const lim5 = avaliarLimitesDia(1, 1, loss10, baseTime);
report(
  "Limites Caso 5: 1 perda, loss ha 10 min -> bloqueado, motivo cita 20 min restantes",
  lim5.bloqueado && lim5.motivos.some((m) => m.includes("faltam 20 min")),
  JSON.stringify(lim5.motivos)
);

// Caso 6: 1 perda, loss há 31 min -> liberado
const loss31 = new Date(baseTime.getTime() - 31 * 60 * 1000);
const lim6 = avaliarLimitesDia(1, 1, loss31, baseTime);
report(
  "Limites Caso 6: 1 perda, loss ha 31 min -> liberado",
  !lim6.bloqueado && lim6.motivos.length === 0,
  JSON.stringify(lim6.motivos)
);

// Caso 7: loss há exatamente 30 min -> liberado (fronteira inclusiva)
const loss30 = new Date(baseTime.getTime() - 30 * 60 * 1000);
const lim7 = avaliarLimitesDia(1, 1, loss30, baseTime);
report(
  "Limites Caso 7: loss ha exatamente 30 min -> liberado (fronteira inclusiva)",
  !lim7.bloqueado && lim7.motivos.length === 0,
  JSON.stringify(lim7.motivos)
);

// Caso 8: 3 perdas e 5 operações -> bloqueado com os dois motivos
const lim8 = avaliarLimitesDia(3, 5, null, baseTime);
const citaPregao = lim8.motivos.some((m) => m.includes("pregão encerrado"));
const citaOps = lim8.motivos.some((m) => m.includes("limite atingido") || m.includes("5 operações"));
report(
  "Limites Caso 8: 3 perdas e 5 operacoes -> bloqueado com os dois motivos",
  lim8.bloqueado && citaPregao && citaOps,
  JSON.stringify(lim8.motivos)
);

// -------------------------------------------------------------
// 6. CASOS DE AVALIAR GATE INTEGRADO (3 casos)
// -------------------------------------------------------------
const itens80: ItemAvaliado[] = [
  ...killsBase,
  { id: "p_test_80", tipo: "PONTO", label: "Confluências 80", checked: true, peso: 80 },
];
const limLiberado = { bloqueado: false, motivos: [] };

// Caso 9: 7 KILL, 80 pontos, 10:30, limites liberados -> liberado
const gate9 = avaliarGate(itens80, "BULLISH", baseTime, 65, limLiberado, null);
report(
  "Gate Integrado Caso 9: 7 KILL, 80 pts, 10:30, limites liberados -> liberado",
  gate9.liberado === true,
  JSON.stringify(gate9.motivos)
);

// Caso 10: Mesmo caso com tradeAbertoId não nulo -> bloqueado
const gate10 = avaliarGate(itens80, "BULLISH", baseTime, 65, limLiberado, "trade-uuid-123");
report(
  "Gate Integrado Caso 10: Mesmo caso com tradeAbertoId nao nulo -> bloqueado",
  gate10.liberado === false && gate10.motivos.includes("já existe trade aberto"),
  JSON.stringify(gate10.motivos)
);

// Caso 11: Mesmo caso com 3 perdas -> bloqueado citando o pregão encerrado
const lim3Loss = { bloqueado: true, motivos: ["3 perdas no dia: pregão encerrado"] };
const gate11 = avaliarGate(itens80, "BULLISH", baseTime, 65, lim3Loss, null);
report(
  "Gate Integrado Caso 11: Mesmo caso com 3 perdas -> bloqueado citando o pregao encerrado",
  gate11.liberado === false && gate11.motivos.some((m) => m.includes("pregão encerrado")),
  JSON.stringify(gate11.motivos)
);

// Regras tiradas dos trades reais (22/08-22/09/2026): so WIN, entradas 10:00-11:29.
const gate0930 = avaliarGate(itens80, "BULLISH", makeSPDate(9, 30), 65, limLiberado, null);
report(
  "Operacional: 09:30 bloqueado (hora da manipulacao da abertura)",
  gate0930.liberado === false && gate0930.motivos.some((m) => m.includes("10:00–11:30")),
  JSON.stringify(gate0930.motivos)
);
report(
  "Operacional: so WIN -> WIN permitido, WDO e BIT bloqueados",
  mercadoPermitido("WIN") && !mercadoPermitido("WDO") && !mercadoPermitido("BIT"),
  `WIN=${mercadoPermitido("WIN")} WDO=${mercadoPermitido("WDO")} BIT=${mercadoPermitido("BIT")}`
);
const gate1129 = avaliarGate(itens80, "BULLISH", makeSPDate(11, 29), 65, limLiberado, null);
const gate1130 = avaliarGate(itens80, "BULLISH", makeSPDate(11, 30), 65, limLiberado, null);
report(
  "Operacional: 11:29 ainda abre posicao, 11:30 bloqueado",
  gate1129.janela !== "FORA" &&
    gate1130.liberado === false &&
    gate1130.motivos.some((m) => m.includes("fora da janela")),
  `11:29=${gate1129.janela} 11:30 liberado=${gate1130.liberado} motivos=${JSON.stringify(gate1130.motivos)}`
);


// ---------------------------------------------------------------------------
// 6. REGUA DE GRADE: TS vs core/entry_quality.py
// ---------------------------------------------------------------------------
// A regua A+/A/B/C/D existe em duas linguagens. A fonte e o Python; o TS e
// copia, porque o app serverless nao importa modulo Python. Sem esta checagem
// as duas divergem em silencio e toda nota historica muda de significado.
const pySrc = fs.readFileSync(
  path.resolve(__dirname, "../../core/entry_quality.py"),
  "utf8"
);
const pyCortes = [...pySrc.matchAll(/score\s*>=\s*(\d+):\s*return\s*"([^"]+)"/g)].map(
  (m) => ({ corte: Number(m[1]), grade: m[2] })
);
const tsCortes = [
  { corte: 80, grade: "A+" },
  { corte: 65, grade: "A" },
  { corte: 50, grade: "B" },
  { corte: 35, grade: "C" },
];
const reguaBate =
  pyCortes.length === tsCortes.length &&
  tsCortes.every((c, i) => pyCortes[i].corte === c.corte && pyCortes[i].grade === c.grade) &&
  tsCortes.every((c) => gradeFor(c.corte) === c.grade) &&
  gradeFor(34) === "D";
report(
  "Regua de grade: TS identica a core/entry_quality.py",
  reguaBate,
  `python=${JSON.stringify(pyCortes)} ts=${JSON.stringify(tsCortes)}`
);

// -------------------------------------------------------------
// 7. CASOS DE PRÉ-SESSÃO (6 casos)
// -------------------------------------------------------------
const preSessaoCompleta: PreSessao = {
  id: "session-1",
  data: "2026-09-16",
  phase_id: "phase-1",
  bias_d1: "COMPRA",
  bias_h1: "COMPRA",
  contexto: "TENDENCIA",
  niveis: [
    { label: "BSL 15m", preco: "135200" },
    { label: "FVG 60m", preco: "134800" },
  ],
  agenda: [{ evento: "Payroll", horario: "09:30", impacto: "ALTO" }],
  sono: 4,
  tilt: 0,
  pressao: 1,
  setup_do_dia: "reversao_htf",
  contratos_declarados: 2,
  screenshot_path: "uid/2026-09-16/htf-123.png",
  fechada_em: null,
  notas: "",
};

// 1. Objeto vazio -> 6 pendências, começando pelo print
const pVazio = pendenciasDaPreSessao({} as PreSessao);
const caso1Ok = pVazio.length === 6 && pVazio[0] === "print do gráfico HTF não anexado";
report(
  "Pré-sessão Caso 1: Objeto vazio -> 6 pendências, começando pelo print",
  caso1Ok,
  `pendências (${pVazio.length}): ${JSON.stringify(pVazio)}`
);

// 2. Tudo preenchido, setup reversao_htf, 2 contratos -> 0 pendências
const pCompleto = pendenciasDaPreSessao(preSessaoCompleta);
const caso2Ok = pCompleto.length === 0;
report(
  "Pré-sessão Caso 2: Tudo preenchido, setup reversao_htf, 2 contratos -> 0 pendências",
  caso2Ok,
  `pendências: ${JSON.stringify(pCompleto)}`
);

// 3. Tudo preenchido menos o print -> 1 pendência, cita o print
const pSemPrint = pendenciasDaPreSessao({
  ...preSessaoCompleta,
  screenshot_path: null,
});
const caso3Ok = pSemPrint.length === 1 && pSemPrint[0].includes("print");
report(
  "Pré-sessão Caso 3: Tudo preenchido menos o print -> 1 pendência, cita o print",
  caso3Ok,
  `pendências: ${JSON.stringify(pSemPrint)}`
);

// 4. Tudo menos o tamanho, setup reversao_htf -> 1 pendência, cita tamanho
const pSemTamanho = pendenciasDaPreSessao({
  ...preSessaoCompleta,
  contratos_declarados: null,
});
const caso4Ok = pSemTamanho.length === 1 && pSemTamanho[0].includes("tamanho");
report(
  "Pré-sessão Caso 4: Tudo menos o tamanho, setup reversao_htf -> 1 pendência, cita tamanho",
  caso4Ok,
  `pendências: ${JSON.stringify(pSemTamanho)}`
);

// 5. Tudo menos o tamanho, setup NENHUM -> 0 pendências (NENHUM dispensa tamanho)
const pNenhumSemTamanho = pendenciasDaPreSessao({
  ...preSessaoCompleta,
  setup_do_dia: "NENHUM",
  contratos_declarados: null,
});
const caso5Ok = pNenhumSemTamanho.length === 0;
report(
  "Pré-sessão Caso 5: Tudo menos o tamanho, setup NENHUM -> 0 pendências",
  caso5Ok,
  `pendências: ${JSON.stringify(pNenhumSemTamanho)}`
);

// 6. 1 nível marcado -> pendência cita o mínimo de 2
const pUmNivel = pendenciasDaPreSessao({
  ...preSessaoCompleta,
  niveis: [{ label: "BSL 15m", preco: "135200" }],
});
const caso6Ok = pUmNivel.length === 1 && pUmNivel[0].includes("2");
report(
  "Pré-sessão Caso 6: 1 nível marcado -> pendência cita o mínimo de 2",
  caso6Ok,
  `pendências: ${JSON.stringify(pUmNivel)}`
);

// -------------------------------------------------------------
// 8. CASOS DE GATE COM PRÉ-SESSÃO E PRINT (3 casos)
// -------------------------------------------------------------
// 7. Tudo certo, preSessaoFechada: false -> bloqueado citando a pré-sessão
const gatePreSessaoAberta = avaliarGate(
  itens80,
  "BULLISH",
  baseTime,
  65,
  limLiberado,
  null,
  false,
  true
);
const caso7Ok =
  gatePreSessaoAberta.liberado === false &&
  gatePreSessaoAberta.motivos.some((m) => m.includes("pré-sessão do dia não foi fechada"));
report(
  "Gate Pré-sessão/Print Caso 7: preSessaoFechada false -> bloqueado citando pré-sessão",
  caso7Ok,
  JSON.stringify(gatePreSessaoAberta.motivos)
);

// 8. Tudo certo, temPrint: false -> bloqueado citando o print
const gateSemPrint = avaliarGate(
  itens80,
  "BULLISH",
  baseTime,
  65,
  limLiberado,
  null,
  true,
  false
);
const caso8Ok =
  gateSemPrint.liberado === false &&
  gateSemPrint.motivos.some((m) => m.includes("print do trade não anexado"));
report(
  "Gate Pré-sessão/Print Caso 8: temPrint false -> bloqueado citando o print",
  caso8Ok,
  JSON.stringify(gateSemPrint.motivos)
);

// 9. Tudo certo, ambos verdadeiros -> liberado
const gateAmbosTrue = avaliarGate(
  itens80,
  "BULLISH",
  baseTime,
  65,
  limLiberado,
  null,
  true,
  true
);
const caso9Ok = gateAmbosTrue.liberado === true && gateAmbosTrue.motivos.length === 0;
report(
  "Gate Pré-sessão/Print Caso 9: preSessaoFechada true e temPrint true -> liberado",
  caso9Ok,
  JSON.stringify(gateAmbosTrue.motivos)
);

// -------------------------------------------------------------
// 9. VALIDAÇÃO DE CAMPOS NOVOS DO TRADE (FR-005)
// -------------------------------------------------------------
// Caso 1: Sem gatilho -> lança erro citando gatilho
let erroGatilho = false;
try {
  validarCamposNovosTrade({
    strategy_id: "reversao_htf",
    contexto_1h: "REVERSAO",
  });
} catch (e: any) {
  erroGatilho = e.message.includes("gatilho");
}
report("Campos Novos Caso 1: Sem gatilho -> lança erro citando gatilho", erroGatilho);

// Caso 2: Sem contexto_1h -> lança erro citando contexto
let erroCtx = false;
try {
  validarCamposNovosTrade({
    strategy_id: "reversao_htf",
    gatilho: "MSS_FVG",
  });
} catch (e: any) {
  erroCtx = e.message.includes("contexto");
}
report("Campos Novos Caso 2: Sem contexto_1h -> lança erro citando contexto", erroCtx);

// Caso 3: varrida_barra_10 sem setup_c_modo -> lança erro citando modo
let erroModo = false;
try {
  validarCamposNovosTrade({
    strategy_id: "varrida_barra_10",
    gatilho: "MSS_FVG",
    contexto_1h: "REVERSAO",
  });
} catch (e: any) {
  erroModo = e.message.includes("modo do Setup C");
}
report("Campos Novos Caso 3: varrida_barra_10 sem modo -> lança erro citando modo do Setup C", erroModo);

// Caso 4: reversao_htf sem setup_c_modo -> válido (passa sem erro)
let revSemModoOk = false;
try {
  validarCamposNovosTrade({
    strategy_id: "reversao_htf",
    gatilho: "MSS_FVG",
    contexto_1h: "REVERSAO",
  });
  revSemModoOk = true;
} catch (e) {
  revSemModoOk = false;
}
report("Campos Novos Caso 4: reversao_htf com gatilho e contexto -> liberado sem exigir modo", revSemModoOk);

// Caso 5: varrida_barra_10 com C1, gatilho MSS_OB e contexto REVERSAO -> válido
let varrValidaOk = false;
try {
  validarCamposNovosTrade({
    strategy_id: "varrida_barra_10",
    gatilho: "MSS_OB",
    contexto_1h: "REVERSAO",
    setup_c_modo: "C1",
  });
  varrValidaOk = true;
} catch (e) {
  varrValidaOk = false;
}
report("Campos Novos Caso 5: varrida_barra_10 completo (C1 + MSS_OB + REVERSAO) -> liberado", varrValidaOk);

// -------------------------------------------------------------
// 10. MÉTRICAS DA VISÃO GERAL (TASK-402)
// -------------------------------------------------------------
const tradesTeste: TradeMetricas[] = [
  {
    strategy_id: "varrida_barra_10",
    direcao: "COMPRA",
    entrada: 100000,
    stop: 99800,
    saida: 100400,
    pontos_real: 400,
    pnl_real: 240,
    hora_entrada: "2026-09-25T13:05:00Z", // 10:05 SP
    hora_saida: "2026-09-25T13:10:00Z",
    gatilho: "MSS_FVG",
    contexto_1h: "CONTINUACAO",
    setup_c_modo: "C1",
    respeitou_plano: true,
  },
  {
    strategy_id: "reversao_htf",
    direcao: "VENDA",
    entrada: 101000,
    stop: 101150,
    saida: 101150,
    pontos_real: -150,
    pnl_real: -90,
    hora_entrada: "2026-09-25T13:15:00Z", // 10:15 SP
    hora_saida: "2026-09-25T13:20:00Z",
    gatilho: "MSS_OB",
    contexto_1h: "REVERSAO",
    respeitou_plano: true,
  },
  {
    strategy_id: "varrida_barra_10",
    direcao: "COMPRA",
    entrada: 100500,
    stop: 100300,
    saida: 100300,
    pontos_real: -200,
    pnl_real: -120,
    hora_entrada: "2026-09-25T13:30:00Z", // 10:30 SP
    hora_saida: "2026-09-25T13:35:00Z",
    gatilho: "BPR",
    contexto_1h: "LATERAL",
    setup_c_modo: "C2",
    respeitou_plano: true,
  },
  {
    strategy_id: "varrida_barra_10",
    direcao: "VENDA",
    entrada: 100800,
    stop: 101000,
    saida: 100200,
    pontos_real: 600,
    pnl_real: 360,
    hora_entrada: "2026-09-25T13:45:00Z", // 10:45 SP
    hora_saida: "2026-09-25T13:50:00Z",
    gatilho: "MSS_FVG",
    contexto_1h: "CONTINUACAO",
    setup_c_modo: "C1",
    respeitou_plano: true,
  },
];

const kpis = calcularKPIsGerais(tradesTeste);

report(
  "Métricas: Resultado total R$ 390 e 3R",
  kpis.resultadoReais === 390 && kpis.resultadoR === 3,
  `reais=${kpis.resultadoReais}, R=${kpis.resultadoR}`
);

report(
  "Métricas: Taxa de acerto 50% e expectativa 0,75R",
  kpis.taxaAcerto === 0.5 && kpis.expectativaR === 0.75,
  `acerto=${kpis.taxaAcerto}, exp=${kpis.expectativaR}`
);

const pfStr = kpis.profitFactor?.toFixed(3);
const poStr = kpis.payoff?.toFixed(3);
report(
  "Métricas: Profit factor 2,857 e payoff 2,857",
  pfStr === "2.857" && poStr === "2.857",
  `pf=${pfStr}, payoff=${poStr}`
);

report(
  "Métricas: Max Drawdown R$ 210 e 2R",
  kpis.maxDrawdownReais === 210 && kpis.maxDrawdownR === 2,
  `ddReais=${kpis.maxDrawdownReais}, ddR=${kpis.maxDrawdownR}`
);

report(
  "Métricas: Stop mediano 200 pts",
  kpis.stopMediano === 200,
  `stopMediano=${kpis.stopMediano}`
);

// Agrupamento por estratégia
const porStrat = agruparPorEstrategia(tradesTeste);
const stratVarrida = porStrat.itens.find((i) => i.strategy_id === "varrida_barra_10");
const stratReversao = porStrat.itens.find((i) => i.strategy_id === "reversao_htf");

report(
  "Métricas por estratégia: varrida_barra_10 -> R$ 480, DD R$ 120 e 1R",
  stratVarrida?.pnl === 480 && stratVarrida?.maxDrawdownReais === 120 && stratVarrida?.maxDrawdownR === 1,
  `pnl=${stratVarrida?.pnl}, ddReais=${stratVarrida?.maxDrawdownReais}, ddR=${stratVarrida?.maxDrawdownR}`
);

report(
  "Métricas por estratégia: reversao_htf -> R$ -90, DD R$ 90 e 1R",
  stratReversao?.pnl === -90 && stratReversao?.maxDrawdownReais === 90 && stratReversao?.maxDrawdownR === 1,
  `pnl=${stratReversao?.pnl}, ddReais=${stratReversao?.maxDrawdownReais}, ddR=${stratReversao?.maxDrawdownR}`
);

// Lista vazia
const kpisVazio = calcularKPIsGerais([]);
const kpisVazioOk =
  kpisVazio.totalTrades === 0 &&
  kpisVazio.profitFactor === null &&
  kpisVazio.payoff === null &&
  formatarNumero(kpisVazio.profitFactor) === "—" &&
  formatarNumero(kpisVazio.payoff) === "—";
report(
  "Métricas: Lista vazia não quebra e devolve '—' onde não há divisor",
  kpisVazioOk,
  `pf=${formatarNumero(kpisVazio.profitFactor)}, payoff=${formatarNumero(kpisVazio.payoff)}`
);

// Faixa de horário em America/Sao_Paulo
const f1000 = classificarFaixaHorario("2026-09-25T13:14:00Z");
const f1015 = classificarFaixaHorario("2026-09-25T13:15:00Z");
const fForaAntes = classificarFaixaHorario("2026-09-25T12:59:00Z");
const fForaDepois = classificarFaixaHorario("2026-09-25T14:30:00Z");

report(
  "Métricas: Faixas de horário SP (13:14Z = 10:00, 13:15Z = 10:15, fora < 10:00 e >= 11:30)",
  f1000 === "10:00" && f1015 === "10:15" && fForaAntes === "fora da janela" && fForaDepois === "fora da janela",
  `13:14Z=${f1000}, 13:15Z=${f1015}, 12:59Z=${fForaAntes}, 14:30Z=${fForaDepois}`
);

// Visão Geral: os 16 trades de exemplo do design/v2/Main.dc.html
{
  const trades = TRADES_DESIGN;
  const vg = montarVisaoGeral(trades, [], 2026, 9, "2026-09-25");
  const dias = vg.cal.cells.filter((c) => c.d === "1" || c.d === "31").map((c) => c.d).join(",");
  report(
    "Visão Geral: 16 trades do design (resultado +R$ 1.604, DD R$ 222, 13 de 16 no plano, calendário começa em 31/08)",
    vg.kpis[0].valor === "+R$ 1.604" && vg.kpis[4].valor === "−R$ 222" && vg.disc.pct === "81%" &&
      vg.estr[0].nome === "Varrida das 10" && vg.estr[0].n === 8 && dias.startsWith("31") && vg.cal.cells.length === 25,
    `resultado=${vg.kpis[0].valor} dd=${vg.kpis[4].valor} disciplina=${vg.disc.pct} estr0=${vg.estr[0].nome}/${vg.estr[0].n} celulas=${vg.cal.cells.length} dias=${dias}`
  );
  const vazio = montarVisaoGeral([], [], 2026, 9, "2026-09-25");
  report("Visão Geral: mês vazio não quebra", vazio.n === 0 && vazio.kpis.length === 5, `n=${vazio.n}`);
}

if (hasErrors) {
  console.error("\n❌ Verificação finalizou com ERROS.");
  process.exit(1);
} else {
  console.log("\n✅ Todos os testes passaram com sucesso!");
  process.exit(0);
}

