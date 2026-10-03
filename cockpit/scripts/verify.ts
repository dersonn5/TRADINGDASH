import fs from "fs";
import { montarVisaoGeral } from "../lib/visao-geral";
import { TRADES_DESIGN } from "./fixture-design";
import {
  FRASE_TESTE, aberturaNY, alertasDoDia, alertasParaDisparar, fraseAs, fraseNoticiaAgora, fraseNoticiaAntes, fraseQuantasNoticias, frasePrimeira, horaFalada,
} from "../lib/alertas";
import { escolherVoz } from "../lib/voz";
import { planoDeFala } from "../lib/voz-clipes";
import { EVENTOS_BRASIL, NOMES_EUA, converterFeed, mesclarAgenda } from "../lib/calendario";
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
  MAX_CONTRATOS,
} from "../lib/gate";
import { REVERSAO_HTF, CONTINUIDADE_TENDENCIA, VARRIDA_BARRA_10, PRIMEIRA_PERNA } from "../data/strategies";
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
  { horaSP: "09:00", hour: 9, minute: 0, janelaEsperada: "ABERTURA", scoreMinEsperado: 65 },
  { horaSP: "09:59", hour: 9, minute: 59, janelaEsperada: "ABERTURA", scoreMinEsperado: 65 },
  { horaSP: "11:29", hour: 11, minute: 29, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "11:59", hour: 11, minute: 59, janelaEsperada: "VALIDA", scoreMinEsperado: 80 },
  { horaSP: "12:00", hour: 12, minute: 0, janelaEsperada: "FORA", scoreMinEsperado: Number.POSITIVE_INFINITY },
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
const HORA_OK = { estrategiaId: "varrida_barra_10", operacoesNaHora: 0 };
const gate1 = avaliarGate(itensCaso1, "BULLISH", makeSPDate(10, 30), 65, undefined, undefined, undefined, undefined, HORA_OK);
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
const resPerna = checarEstrategia("primeira_perna.json", PRIMEIRA_PERNA, 6, 3, 100);
const sincroniaOk = resRev.ok && resCont.ok && resVarr.ok && resPerna.ok;
const detalheSincronia = [resRev.detalhe, resCont.detalhe, resVarr.detalhe, resPerna.detalhe].filter(Boolean).join(" | ");

report(
  "Sincronia: quatro estratégias idênticas aos JSONs e pesos somando 100",
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
// 5. CASOS DE AVALIAR LIMITES DIA (03/10/2026: 3 stops, 5 trades, sem pausa)
// -------------------------------------------------------------
const baseTime = makeSPDate(10, 30);
const lim1 = avaliarLimitesDia(0, 0);
report("Limites Caso 1: 0 perdas, 0 operacoes -> liberado", !lim1.bloqueado && lim1.motivos.length === 0, JSON.stringify(lim1.motivos));
const lim2 = avaliarLimitesDia(2, 4);
report("Limites Caso 2: 2 perdas e 4 operacoes -> liberado (sem pausa depois de loss)", !lim2.bloqueado, JSON.stringify(lim2.motivos));
const lim3 = avaliarLimitesDia(3, 3);
report("Limites Caso 3: 3 perdas -> bloqueado, motivo cita pregao encerrado",
  lim3.bloqueado && lim3.motivos.some((m) => m.includes("3 perdas") && m.includes("pregão encerrado")), JSON.stringify(lim3.motivos));
const lim4 = avaliarLimitesDia(0, 5);
report("Limites Caso 4: 5 operacoes -> bloqueado", lim4.bloqueado && lim4.motivos.some((m) => m.includes("5 operações")), JSON.stringify(lim4.motivos));
const lim5 = avaliarLimitesDia(3, 5);
report("Limites Caso 5: 3 perdas e 5 operacoes -> os dois motivos", lim5.bloqueado && lim5.motivos.length === 2, JSON.stringify(lim5.motivos));
report("Limites: maximo de 3 contratos", MAX_CONTRATOS === 3, String(MAX_CONTRATOS));
let erroContratos = "";
try {
  validarCamposNovosTrade({ strategy_id: "continuidade_tendencia", gatilho: "MSS_FVG", contexto_1h: "REVERSAO", contratos: 4 });
} catch (e) {
  erroContratos = (e as Error).message;
}
report("Gravacao: 4 contratos recusado", erroContratos.includes("3 contratos"), erroContratos);

// -------------------------------------------------------------
// 6. CASOS DE AVALIAR GATE INTEGRADO (3 casos)
// -------------------------------------------------------------
const itens80: ItemAvaliado[] = [
  ...killsBase,
  { id: "p_test_80", tipo: "PONTO", label: "Confluências 80", checked: true, peso: 80 },
];
const limLiberado = { bloqueado: false, motivos: [] };

// Caso 9: 7 KILL, 80 pontos, 10:30, limites liberados -> liberado
const gate9 = avaliarGate(itens80, "BULLISH", baseTime, 65, limLiberado, null, undefined, undefined, HORA_OK);
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

// Setups e cotas por hora (03/10/2026): 1a hora V (1), 2a hora C ou B (3), 3a hora B (1).
const ctx = (estrategiaId: string, operacoesNaHora = 0) => ({ estrategiaId, operacoesNaHora });
const gh = (h: number, m: number, c: ReturnType<typeof ctx>) => avaliarGate(itens80, "BULLISH", makeSPDate(h, m), 65, limLiberado, null, true, true, c);
const casosHora: Array<[string, boolean, ReturnType<typeof avaliarGate>, string]> = [
  ["09:30 setup das 10 -> bloqueado", false, gh(9, 30, ctx("varrida_barra_10")), "só RPP"],
  ["09:30 primeira perna, 1o trade -> liberado", true, gh(9, 30, ctx("primeira_perna")), ""],
  ["09:30 primeira perna, ja feito -> bloqueado", false, gh(9, 30, ctx("primeira_perna", 1)), "limite de 1 trade"],
  ["10:30 primeira perna -> bloqueado", false, gh(10, 30, ctx("primeira_perna")), "MAV ou CSI"],
  ["10:30 setup das 10, 2 feitos -> liberado", true, gh(10, 30, ctx("varrida_barra_10", 2)), ""],
  ["10:30 continuidade -> liberado", true, gh(10, 30, ctx("continuidade_tendencia")), ""],
  ["10:30 setup das 10, 3 feitos -> bloqueado", false, gh(10, 30, ctx("varrida_barra_10", 3)), "limite de 3 trades"],
  ["10:30 reversao HTF (fora do sistema) -> bloqueado", false, gh(10, 30, ctx("reversao_htf")), "2ª hora"],
  ["11:15 continuidade -> liberado", true, gh(11, 15, ctx("continuidade_tendencia")), ""],
  ["11:15 setup das 10 -> bloqueado", false, gh(11, 15, ctx("varrida_barra_10")), "só CSI"],
  ["11:15 continuidade, 1 feito -> bloqueado", false, gh(11, 15, ctx("continuidade_tendencia", 1)), "limite de 1 trade"],
];
for (const [nome, esperado, g, trecho] of casosHora) {
  report(`Hora: ${nome}`, g.liberado === esperado && (esperado || g.motivos.some((m) => m.includes(trecho))), JSON.stringify(g.motivos));
}
report(
  "Operacional: so WIN -> WIN permitido, WDO e BIT bloqueados",
  mercadoPermitido("WIN") && !mercadoPermitido("WDO") && !mercadoPermitido("BIT"),
  `WIN=${mercadoPermitido("WIN")} WDO=${mercadoPermitido("WDO")} BIT=${mercadoPermitido("BIT")}`
);
const gate1159 = avaliarGate(itens80, "BULLISH", makeSPDate(11, 59), 65, limLiberado, null, true, true, ctx("continuidade_tendencia"));
const gate1200 = avaliarGate(itens80, "BULLISH", makeSPDate(12, 0), 65, limLiberado, null, true, true, ctx("continuidade_tendencia"));
report(
  "Operacional: 11:59 ainda abre posicao, 12:00 bloqueado",
  gate1159.liberado === true && gate1200.liberado === false && gate1200.motivos.some((m) => m.includes("fora da janela")),
  `11:59=${gate1159.janela} ${JSON.stringify(gate1159.motivos)} 12:00 liberado=${gate1200.liberado}`
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
  true,
  HORA_OK
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
  erroModo = e.message.includes("modo da MAV");
}
report("Campos Novos Caso 3: varrida_barra_10 sem modo -> lança erro citando modo da MAV", erroModo);

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
      vg.estr[0].nome === "MAV" && vg.estr[0].n === 8 && dias.startsWith("31") && vg.cal.cells.length === 25,
    `resultado=${vg.kpis[0].valor} dd=${vg.kpis[4].valor} disciplina=${vg.disc.pct} estr0=${vg.estr[0].nome}/${vg.estr[0].n} celulas=${vg.cal.cells.length} dias=${dias}`
  );
  const vazio = montarVisaoGeral([], [], 2026, 9, "2026-09-25");
  report("Visão Geral: mês vazio não quebra", vazio.n === 0 && vazio.kpis.length === 5, `n=${vazio.n}`);
}

// Alertas de voz (SPEC_ALERTAS_VOZ.md)
{
  report("Alertas: NY abre 10:30 em setembro e 11:30 em janeiro", aberturaNY("2026-09-25") === "10:30" && aberturaNY("2026-01-15") === "11:30",
    `set=${aberturaNY("2026-09-25")} jan=${aberturaNY("2026-01-15")}`);
  report("Alertas: sábado e feriado sem alerta", alertasDoDia("2026-09-26", [], true).length === 0 && alertasDoDia("2026-09-07", [], true).length === 0);

  const agendaAlto = [{ evento: "Payroll", horario: "10:30", impacto: "ALTO" as const }];
  const a1 = alertasDoDia("2026-09-25", agendaAlto, true).filter((a) => a.grupo === "noticia");
  report("Alertas: notícia Alta às 10:30 gera 10:25 e 10:30", a1.length === 2 && a1[0].hora === "10:25" && a1[1].hora === "10:30",
    JSON.stringify(a1.map((a) => a.hora)));
  const med = alertasDoDia("2026-09-25", [{ evento: "ISM", horario: "11:00", impacto: "MEDIO" }], true).filter((a) => a.grupo === "noticia");
  const baixo = alertasDoDia("2026-09-25", [{ evento: "X", horario: "11:00", impacto: "BAIXO" }], true).filter((a) => a.grupo === "noticia");
  const fora = alertasDoDia("2026-09-25", [{ evento: "Y", horario: "15:00", impacto: "ALTO" }], true).filter((a) => a.grupo === "noticia");
  report("Alertas: Médio só na hora, Baixo e fora da janela não falam", med.length === 1 && med[0].hora === "11:00" && baixo.length === 0 && fora.length === 0);

  const temAviso = (fechada: boolean) => alertasDoDia("2026-09-25", [], fechada).some((a) => a.hora === "09:45");
  report("Alertas: aviso das 09:45 só com a pré-sessão aberta", temAviso(false) && !temAviso(true));

  const doDia = alertasDoDia("2026-09-25", agendaAlto, true);
  const as1000 = (s: number) => new Date(Date.UTC(2026, 8, 25, 13, 0, s));
  const d1 = alertasParaDisparar(doDia, as1000(30), new Set()).map((a) => a.hora);
  const d2 = alertasParaDisparar(doDia, as1000(91), new Set()).map((a) => a.hora);
  const idDez = doDia.find((a) => a.hora === "10:00")!.id;
  const d3 = alertasParaDisparar(doDia, as1000(30), new Set([idDez])).map((a) => a.hora);
  report("Alertas: dispara até 90 s depois e não repete", d1.join() === "10:00" && d2.length === 0 && d3.length === 0,
    `10:00:30=${d1} 10:01:31=${d2} repetido=${d3}`);

  const abertura = doDia.find((a) => a.hora === "09:00")!.texto;
  report("Alertas: hora falada e resumo das 09:00",
    horaFalada("09:45") === "nove e quarenta e cinco" && horaFalada("10:30") === "dez e meia" && horaFalada("12:00") === "meio-dia" &&
      abertura.includes("Hoje tem uma notícia de impacto alto. A primeira é Payroll, às dez e meia."),
    abertura);

  const nyInverno = alertasDoDia("2026-01-15", [], true).filter((a) => a.hora === "11:30").map((a) => a.texto);
  report("Alertas: no inverno dos EUA, NY abre as 11:30 (sem aviso de fim de janela desde 01/10)", nyInverno[0] === "Abertura de Nova York." && nyInverno.length === 1,
    JSON.stringify(nyInverno));
  const doDiaRotina = alertasDoDia("2026-10-01", [], true).map((a) => a.hora);
  report("Alertas: sem 11:25 e 11:30; 11:55 e 12:00 continuam",
    !doDiaRotina.includes("11:25") && !doDiaRotina.includes("11:30") && doDiaRotina.includes("11:55") && doDiaRotina.includes("12:00"),
    JSON.stringify(doDiaRotina));

  const comSino = doDia.filter((a) => a.som === "sino").map((a) => a.hora);
  const caminhoSino = path.resolve(__dirname, "../public/sons/sino-pregao.ogg");
  report("Alertas: sino de pregão viva voz nas aberturas das 09:00 e 10:00 e arquivo presente",
    comSino.join() === "09:00,10:00" && fs.existsSync(caminhoSino),
    `sino=${comSino.join()} arquivo=${fs.existsSync(caminhoSino)}`);

  const vozes = [
    { name: "Microsoft Daniel", lang: "pt-BR", voiceURI: "d" },
    { name: "Google português do Brasil", lang: "pt-BR", voiceURI: "g" },
    { name: "Microsoft Francisca Online (Natural)", lang: "pt-BR", voiceURI: "f" },
    { name: "Samantha", lang: "en-US", voiceURI: "s" },
  ];
  report("Voz: prefere Francisca, respeita a salva e cai em qualquer pt-BR",
    escolherVoz(vozes)?.voiceURI === "f" && escolherVoz(vozes, "g")?.voiceURI === "g" &&
      escolherVoz([vozes[0], vozes[3]])?.voiceURI === "d" && escolherVoz([vozes[3]]) === null);

  const feed = [
    { title: "Non-Farm Employment Change", country: "USD", date: "2026-09-25T08:30:00-04:00", impact: "High" },
    { title: "CPI m/m", country: "USD", date: "2026-09-25T08:30:00-04:00", impact: "High" },
    { title: "CPI y/y", country: "USD", date: "2026-09-25T08:30:00-04:00", impact: "High" },
    { title: "ISM Services PMI", country: "USD", date: "2026-09-25T10:00:00-04:00", impact: "Medium" },
    { title: "Some Low", country: "USD", date: "2026-09-25T10:00:00-04:00", impact: "Low" },
    { title: "ECB Speaks", country: "EUR", date: "2026-09-25T09:00:00-04:00", impact: "High" },
    { title: "Unemployment Claims", country: "USD", date: "2026-09-24T08:30:00-04:00", impact: "High" },
  ];
  const conv = converterFeed(feed, "2026-09-25");
  report("Calendário: só EUA, Alto/Médio, de hoje, em São Paulo e em português",
    conv.length === 3 && conv[0].horario === "09:30" && conv[0].evento === "Payroll" && conv[1].evento === "CPI, inflação ao consumidor" &&
      conv[2].horario === "11:00" && conv[2].impacto === "MEDIO",
    JSON.stringify(conv.map((e) => `${e.horario} ${e.evento} ${e.impacto}`)));
  // Voz Dora (SPEC_VOZ_KOKORO.md)
  const comResumo = alertasDoDia("2026-09-25", agendaAlto, false);
  const bomDia = comResumo.find((a) => a.hora === "09:00")!;
  report("Voz Dora: segmentos juntos formam o texto; resumo das 09:00 em 4 pedaços",
    comResumo.every((a) => a.segmentos.join(" ") === a.texto) && bomDia.segmentos.length === 4,
    JSON.stringify(bomDia.segmentos));
  const manifestFalso = { voz: "pf_dora", velocidade: 1, clipes: { "Bom dia.": "a.ogg", "Fim.": "b.ogg" } };
  const plano = planoDeFala(["Bom dia.", "  Nome   novo, ", "Fim."], manifestFalso);
  report("Voz Dora: plano usa o áudio que existe e o navegador no resto, na ordem",
    plano.length === 3 && plano[0].tipo === "arquivo" && plano[1].tipo === "navegador" && (plano[1] as { texto: string }).texto === "Nome novo," &&
      plano[2].tipo === "arquivo" && (plano[2] as { url: string }).url === "/voz/b.ogg" && planoDeFala(["Bom dia."], null)[0].tipo === "navegador",
    JSON.stringify(plano));
  const manifestPath = path.resolve(__dirname, "../public/voz/manifest.json");
  if (fs.existsSync(manifestPath)) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    const nomes = [...NOMES_EUA, ...EVENTOS_BRASIL];
    const precisa = [
      FRASE_TESTE,
      ...["2026-09-25", "2026-01-15"].flatMap((d) => alertasDoDia(d, [], false).flatMap((a) => a.segmentos)),
      ...nomes.flatMap((n) => [fraseNoticiaAntes(n), fraseNoticiaAgora(n), frasePrimeira(n)]),
      ...[1, 2, 3, 4, 5, 6].map(fraseQuantasNoticias),
      fraseAs("09:30"), fraseAs("10:25"), fraseAs("11:55"),
    ];
    const faltando = precisa.filter((t) => planoDeFala([t], manifest)[0].tipo !== "arquivo");
    report("Voz Dora: toda frase fixa e todo nome conhecido têm áudio gravado", faltando.length === 0,
      faltando.length ? `sem áudio: ${JSON.stringify(faltando.slice(0, 5))} — rodar listar-frases-voz.ts e gerar.py` : `${precisa.length} frases`);
    const arquivosFaltando = Object.values(manifest.clipes as Record<string, string>).filter((a) => !fs.existsSync(path.resolve(__dirname, "../public/voz", a)));
    report("Voz Dora: todo arquivo do manifest existe em public/voz", arquivosFaltando.length === 0, arquivosFaltando.slice(0, 3).join());
  } else {
    report("Voz Dora: public/voz/manifest.json existe", false, "rodar tools/voz/gerar.py");
  }

  const mesc = mesclarAgenda([{ evento: "Payroll", horario: "09:30", impacto: "ALTO" }, { evento: "Copom", horario: "18:30", impacto: "ALTO" }], conv);
  report("Calendário: importar não duplica o que já está na agenda", mesc.length === 4 && mesc.filter((e) => e.evento === "Payroll").length === 1,
    JSON.stringify(mesc.map((e) => `${e.horario} ${e.evento}`)));
}

if (hasErrors) {
  console.error("\n❌ Verificação finalizou com ERROS.");
  process.exit(1);
} else {
  console.log("\n✅ Todos os testes passaram com sucesso!");
  process.exit(0);
}

