export type Janela = "PRIME" | "VALIDA" | "FORA";

export interface ItemAvaliado {
  id: string;
  tipo: "KILL" | "PONTO";
  label: string;
  checked: boolean;
  peso: number;
}

export interface GateResult {
  liberado: boolean;
  janela: Janela;
  score: number;
  scoreMinimo: number;
  killsFaltando: string[]; // labels dos KILL não marcados
  motivos: string[]; // todos os motivos de bloqueio, em português
  avisos: string[];
}

export const SCORE_MINIMO_PRIME = 65;
export const BONUS_FORA_DA_PRIME = 15; // VALIDA exige 65 + 15 = 80

/**
 * Converte agora para America/Sao_Paulo e classifica a janela de operação:
 * - PRIME: de 10:00 (inclusive) a 11:00 (exclusive)
 * - VALIDA: de 09:00 (inclusive) a 12:00 (exclusive), fora do PRIME
 * - FORA: qualquer outro horário
 */
export function classificarJanela(agora: Date): Janela {
  const formatter = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const parts = formatter.formatToParts(agora);
  const hourStr = parts.find((p) => p.type === "hour")?.value ?? "0";
  const minuteStr = parts.find((p) => p.type === "minute")?.value ?? "0";
  const hour = parseInt(hourStr, 10);
  const minute = parseInt(minuteStr, 10);
  const minutos = hour * 60 + minute;

  // PRIME: de 10:00 (inclusive, 600 min) a 11:00 (exclusive, 660 min)
  if (minutos >= 600 && minutos < 660) {
    return "PRIME";
  }

  // VALIDA: de 09:00 (inclusive, 540 min) a 12:00 (exclusive, 720 min), fora do PRIME
  if (minutos >= 540 && minutos < 720) {
    return "VALIDA";
  }

  // FORA: o resto
  return "FORA";
}

/**
 * Retorna o score mínimo exigido pela janela:
 * - PRIME -> base (65)
 * - VALIDA -> base + 15 (80)
 * - FORA -> Infinity (bloqueado)
 */
export function scoreMinimoEfetivo(janela: Janela, base: number = SCORE_MINIMO_PRIME): number {
  if (janela === "PRIME") return base;
  if (janela === "VALIDA") return base + BONUS_FORA_DA_PRIME;
  return Number.POSITIVE_INFINITY;
}

/**
 * Avalia o gate de entrada para a sessão/trade:
 * Acumula todos os motivos de bloqueio se houver.
 */
export function avaliarGate(
  itens: ItemAvaliado[],
  bias: string,
  agora: Date,
  scoreMinimoBase: number = SCORE_MINIMO_PRIME
): GateResult {
  const janela = classificarJanela(agora);
  const scoreMinimo = scoreMinimoEfetivo(janela, scoreMinimoBase);
  const score = itens
    .filter((i) => i.tipo === "PONTO" && i.checked)
    .reduce((acc, i) => acc + i.peso, 0);
  const killsFaltando = itens
    .filter((i) => i.tipo === "KILL" && !i.checked)
    .map((i) => i.label);

  const motivos: string[] = [];
  const avisos: string[] = [];

  if (bias === "NAO_OPERAR") {
    motivos.push("bias do dia marcado como NAO_OPERAR");
  }

  if (janela === "FORA") {
    motivos.push("fora da janela de operação 09:00–12:00");
  }

  for (const label of killsFaltando) {
    motivos.push(`falta obrigatório: ${label}`);
  }

  if (score < scoreMinimo && janela !== "FORA") {
    motivos.push(`score ${score} abaixo do mínimo ${scoreMinimo}`);
  }

  if (janela === "VALIDA") {
    avisos.push("fora da janela nobre 10:00–11:00 — exige score 80");
  }

  const liberado = motivos.length === 0;

  return {
    liberado,
    janela,
    score,
    scoreMinimo,
    killsFaltando,
    motivos,
    avisos,
  };
}

/**
 * Quantos KILL consecutivos, a partir do primeiro, estão marcados.
 * É o número de passos cumpridos da trilha.
 */
export function passosCumpridos(itens: ItemAvaliado[]): number {
  const kills = itens.filter((i) => i.tipo === "KILL");
  let count = 0;
  for (const k of kills) {
    if (k.checked) {
      count++;
    } else {
      break;
    }
  }
  return count;
}

/**
 * Estado de cada KILL, na ordem do array:
 * "CUMPRIDO" — já marcado
 * "AGORA"    — o próximo, único clicável
 * "TRAVADO"  — ainda não liberado
 */
export function estadoDosPassos(itens: ItemAvaliado[]): Array<"CUMPRIDO" | "AGORA" | "TRAVADO"> {
  const kills = itens.filter((i) => i.tipo === "KILL");
  const cumpridos = passosCumpridos(itens);
  return kills.map((_, i) => {
    const n = i + 1;
    if (n <= cumpridos) return "CUMPRIDO";
    if (n === cumpridos + 1) return "AGORA";
    return "TRAVADO";
  });
}

/**
 * Aplica um clique num KILL e devolve a lista nova.
 * - clicar no passo AGORA: marca ele
 * - clicar num passo CUMPRIDO de índice n: desmarca ele E TODOS OS SEGUINTES
 * - clicar num passo TRAVADO: não faz nada (devolve a lista inalterada)
 */
export function alternarPasso(itens: ItemAvaliado[], id: string): ItemAvaliado[] {
  const kills = itens.filter((i) => i.tipo === "KILL");
  const killIndex = kills.findIndex((k) => k.id === id);
  if (killIndex === -1) {
    return itens;
  }

  const estados = estadoDosPassos(itens);
  const estado = estados[killIndex];

  if (estado === "TRAVADO") {
    return itens;
  }

  if (estado === "AGORA") {
    return itens.map((item) => {
      if (item.id === id) {
        return { ...item, checked: true };
      }
      return item;
    });
  }

  if (estado === "CUMPRIDO") {
    // Desmarca este KILL e todos os KILLs seguintes
    const idsToUncheck = new Set(kills.slice(killIndex).map((k) => k.id));
    return itens.map((item) => {
      if (idsToUncheck.has(item.id)) {
        return { ...item, checked: false };
      }
      return item;
    });
  }

  return itens;
}

