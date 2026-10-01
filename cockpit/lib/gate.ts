export type Janela = "ABERTURA" | "PRIME" | "VALIDA" | "FORA";

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
 * Limites espelhados do Profit Chart, que trava nestes números (decisão do operador
 * em 01/10/2026, depois de 4 pregões: 6 operações, 4 stops, sem pausa depois de loss).
 */
export const MAX_PERDAS_DIA = 4;
export const MAX_OPERACOES_DIA = 6;
export const MAX_CONTRATOS = 3;

/** O único trade permitido antes das 10:00: contra a primeira perna do dia. */
export const ESTRATEGIA_PRIMEIRA_PERNA = "primeira_perna";

/**
 * Mercados liberados para operar. So WIN.
 *
 * Nos trades reais de 22/08 a 22/09/2026 (export do Profit), o WIN fez todo o
 * lucro da conta da Copa (+R$ 20.576, 44% de acerto); WDO e Bitcoin tiraram
 * R$ 7.137 e dividiram a atencao nos momentos decisivos.
 */
export const MERCADOS_PERMITIDOS = ["WIN"] as const;

export function mercadoPermitido(mercado: string): boolean {
  return (MERCADOS_PERMITIDOS as readonly string[]).includes(mercado);
}

export interface LimitesDia {
  bloqueado: boolean;
  motivos: string[];
}

export function avaliarLimitesDia(perdasHoje: number, operacoesHoje: number): LimitesDia {
  const motivos: string[] = [];

  if (perdasHoje >= MAX_PERDAS_DIA) {
    motivos.push(`${MAX_PERDAS_DIA} perdas no dia: pregão encerrado`);
  }

  if (operacoesHoje >= MAX_OPERACOES_DIA) {
    motivos.push(`${MAX_OPERACOES_DIA} operações no dia: limite atingido`);
  }

  return {
    bloqueado: motivos.length > 0,
    motivos,
  };
}

/**
 * Converte agora para America/Sao_Paulo e classifica a janela de operação:
 * - ABERTURA: 09:00-09:59 — só o trade contra a primeira perna (1 por dia)
 * - PRIME: de 10:00 (inclusive) a 11:00 (exclusive)
 * - VALIDA: de 11:00 (inclusive) a 12:00 (exclusive) — exige score maior
 * - FORA: qualquer outro horário
 *
 * 09:00-09:59 tinha saido em 22/09/2026 (19% de acerto e -R$ 800 nessa hora na conta
 * real; de 28/09 a 01/10, -R$ 376 em trades antes das 10:00). Em 01/10/2026 o operador
 * liberou UM trade nela: contra a primeira perna do dia (800+ pts a partir das 09:00),
 * alvo nos 75% da perna — o V das 09:00 (Estudo_Reversao_Abertura_Vista, itens 7 e 9).
 *
 * Entradas ate 11:59 desde 01/10/2026 (antes: 11:29). A tela fecha as 12:00.
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

  if (minutos >= 540 && minutos < 600) {
    return "ABERTURA";
  }

  // PRIME: de 10:00 (inclusive, 600 min) a 11:00 (exclusive, 660 min)
  if (minutos >= 600 && minutos < 660) {
    return "PRIME";
  }

  // VALIDA: de 11:00 (inclusive, 660 min) a 12:00 (exclusive, 720 min)
  if (minutos >= 660 && minutos < 720) {
    return "VALIDA";
  }

  // FORA: o resto
  return "FORA";
}

/**
 * Retorna o score mínimo exigido pela janela:
 * - ABERTURA, PRIME -> base (65)
 * - VALIDA -> base + 15 (80)
 * - FORA -> Infinity (bloqueado)
 */
export function scoreMinimoEfetivo(janela: Janela, base: number = SCORE_MINIMO_PRIME): number {
  if (janela === "PRIME" || janela === "ABERTURA") return base;
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
  scoreMinimoBase: number = SCORE_MINIMO_PRIME,
  limites?: LimitesDia,
  tradeAbertoId?: string | null,
  preSessaoFechada?: boolean,
  temPrint?: boolean,
  primeiraPerna?: { estrategiaId: string; operacoesAntesDas10: number }
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
    motivos.push("fora da janela de entrada 09:00–12:00");
  }

  if (primeiraPerna) {
    const ehPrimeiraPerna = primeiraPerna.estrategiaId === ESTRATEGIA_PRIMEIRA_PERNA;
    if (janela === "ABERTURA" && !ehPrimeiraPerna) {
      motivos.push("antes das 10:00, só o trade contra a primeira perna");
    }
    if (janela === "ABERTURA" && ehPrimeiraPerna && primeiraPerna.operacoesAntesDas10 >= 1) {
      motivos.push("o trade contra a primeira perna já foi feito hoje");
    }
    if ((janela === "PRIME" || janela === "VALIDA") && ehPrimeiraPerna) {
      motivos.push("o trade contra a primeira perna é só antes das 10:00");
    }
  } else if (janela === "ABERTURA") {
    motivos.push("antes das 10:00, só o trade contra a primeira perna");
  }

  for (const label of killsFaltando) {
    motivos.push(`falta obrigatório: ${label}`);
  }

  if (score < scoreMinimo && janela !== "FORA") {
    motivos.push(`score ${score} abaixo do mínimo ${scoreMinimo}`);
  }

  if (janela === "VALIDA") {
    avisos.push("depois das 11:00 — exige score 80");
  }

  if (limites && limites.bloqueado) {
    motivos.push(...limites.motivos);
  }

  if (tradeAbertoId) {
    motivos.push("já existe trade aberto");
  }

  if (preSessaoFechada === false) {
    motivos.push("pré-sessão do dia não foi fechada");
  }

  if (temPrint === false) {
    motivos.push("print do trade não anexado");
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
