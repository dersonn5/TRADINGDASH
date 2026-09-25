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

/** Limites espelhados do Profit Chart, que trava nestes números. */
export const MAX_PERDAS_DIA = 3;
export const MAX_OPERACOES_DIA = 5;
export const COOLDOWN_APOS_LOSS_MIN = 30;

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

/** Minutos que faltam do cooldown, ou 0. */
export function cooldownRestante(ultimoLossEm: Date | null, agora: Date): number {
  if (!ultimoLossEm) return 0;
  const diffMs = agora.getTime() - ultimoLossEm.getTime();
  if (diffMs < 0) return COOLDOWN_APOS_LOSS_MIN;
  const passedMinutes = diffMs / (1000 * 60);
  // Fronteira inclusiva: se passou exatamente 30 min (ou mais), o cooldown acabou
  if (passedMinutes >= COOLDOWN_APOS_LOSS_MIN) return 0;
  return Math.ceil(COOLDOWN_APOS_LOSS_MIN - passedMinutes);
}

export function avaliarLimitesDia(
  perdasHoje: number,
  operacoesHoje: number,
  ultimoLossEm: Date | null,
  agora: Date
): LimitesDia {
  const motivos: string[] = [];

  if (perdasHoje >= MAX_PERDAS_DIA) {
    motivos.push("3 perdas no dia: pregão encerrado");
  }

  if (operacoesHoje >= MAX_OPERACOES_DIA) {
    motivos.push("5 operações no dia: limite atingido");
  }

  const rest = cooldownRestante(ultimoLossEm, agora);
  if (rest > 0) {
    motivos.push(`pausa após loss: faltam ${rest} min`);
  }

  return {
    bloqueado: motivos.length > 0,
    motivos,
  };
}

/**
 * Converte agora para America/Sao_Paulo e classifica a janela de operação:
 * - PRIME: de 10:00 (inclusive) a 11:00 (exclusive)
 * - VALIDA: de 11:00 (inclusive) a 11:30 (exclusive)
 * - FORA: qualquer outro horário, inclusive 09:00-09:59 e 11:30-12:00
 *
 * 09:00-09:59 saiu da janela em 22/09/2026 (teste de 2 semanas). E a hora em que
 * o indice faz a manipulacao da abertura, antes de o volume do a vista (10:00) e
 * de NY (10:30) definir um lado. Nos trades reais de WIN: 19% de acerto e
 * -R$ 800 nessa hora na conta real; 10:00-11:59 foi o melhor trecho nas duas contas.
 *
 * Abertura de posicao so ate 11:29 (decisao do operador, 22/09/2026). A tela fica
 * aberta ate 12:00 para gerenciar o que ja esta posicionado. 11:30-11:59 foi misto:
 * +R$ 1.087 na conta real, -R$ 3.240 na Copa (a sequencia de stops de 22/09).
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

  // VALIDA: de 11:00 (inclusive, 660 min) a 11:30 (exclusive, 690 min)
  if (minutos >= 660 && minutos < 690) {
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
  scoreMinimoBase: number = SCORE_MINIMO_PRIME,
  limites?: LimitesDia,
  tradeAbertoId?: string | null,
  preSessaoFechada?: boolean,
  temPrint?: boolean
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
    motivos.push("fora da janela de entrada 10:00–11:30");
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
