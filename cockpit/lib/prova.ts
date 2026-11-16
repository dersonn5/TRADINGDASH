/**
 * Prova da mesa (Zero7, plano Pleno): regras da mesa + plano do operador, em funcoes puras.
 * Testadas em scripts/verify.ts. Trade System, secao "Prova da mesa" (11/11/2026).
 *
 * Do regulamento (14/10/2026): meta liquida de R$ 4.997, minimo de 5 pregoes, um pregao
 * conta no maximo 50% da meta, perda diaria R$ 1.247 trava o dia, perda total elimina, trade
 * de 10 pts ou menos no WIN nao conta, zeragem as 17:30 e leilao proibido.
 *
 * Do plano do operador (simulado em 11/11/2026 para fechar em ate 8 pregoes): 10 contratos,
 * o dia acaba antes do limite da mesa, ganho do dia limitado ao que a mesa conta, a mao
 * desce quando a prova aperta e a saida e na meta mais uma folga para custos.
 */
import type { Conta } from "./contas";
import { REGRAS_DA_HORA, type LimitesDia, type RegrasDaHora } from "./gate";

/**
 * Horas da prova (decisao do operador em 16/11/2026, com a prova em -R$ 3.552 depois de 16
 * trades): nada na 1a hora (6 trades, 6 perdas, -R$ 2.072), 2 trades na hora das 10:00 e 1 a
 * partir das 11:30 (abertura de NY fora do horario de verao dos EUA). 3 trades no dia, e 2
 * stops encerram: sao max_operacoes_dia e max_perdas_seguidas da conta (migration_prova_plano.sql).
 */
export const REGRAS_DA_HORA_PROVA: RegrasDaHora = {
  ABERTURA: { ...REGRAS_DA_HORA.ABERTURA, maxTrades: 0 },
  PRIME: { ...REGRAS_DA_HORA.PRIME, maxTrades: 2 },
  VALIDA: { ...REGRAS_DA_HORA.VALIDA, maxTrades: 1, aPartirDeMin: 11 * 60 + 30 },
};

/** Setups e cotas por hora da conta: a prova tem as dela, a real segue o plano por hora. */
export function regrasDaHoraDaConta(conta: Conta): RegrasDaHora {
  return conta.tipo === "PROVA" ? REGRAS_DA_HORA_PROVA : REGRAS_DA_HORA;
}

/** A mesa corta o dia em R$ 1.247; o plano para antes: o proximo stop tem de caber aqui. */
export const CORTE_PERDA_DIA_RS = 1200;
/** A mesa so conta ate 50% da meta (R$ 2.498,50) por pregao; acima de R$ 2.400 o dia acaba. */
export const TETO_GANHO_DIA_RS = 2400;
/** Metade da folga de R$ 6.500: com esse prejuizo acumulado a mao desce. */
export const RECUO_PERDA_RS = 3200;
export const CONTRATOS_RECUO = 5;
/** Meta de R$ 4.997 mais folga para custos (R$ 0,37 por contrato de WIN). */
export const SAIDA_RS = 5100;
/** O plano mira a aprovacao em ate 8 pregoes (o prazo da mesa e ilimitado). */
export const PREGOES_ALVO = 8;

const VALOR_PONTO_WIN = 0.2;

export interface TradeProva {
  data: string; // YYYY-MM-DD da sessao
  pnl_real?: number | null;
  pontos_real?: number | null;
}

export interface ResumoProva {
  pnlBruto: number; // soma de tudo o que foi fechado
  resultadoValido: number; // o que conta para a meta (teto por pregao, sem ganho de 10 pts ou menos)
  excedenteTeto: number; // lucro de pregao acima do teto, que nao conta
  naoContam: { n: number; ganhosIgnorados: number }; // trades de pts_minimos_validos ou menos
  pregoes: number; // dias com ao menos um trade
  porDia: Record<string, number>;
  maiorDia: { data: string; valor: number } | null;
  piorAcumulado: number; // menor ponto do acumulado (<= 0): a perda total usada
  emRecuo: boolean; // a mao esta reduzida (desceu em -RECUO_PERDA_RS, volta ao zerar)
}

const pnlDe = (t: TradeProva) => Number(t.pnl_real ?? 0);

/** Teto de lucro de um pregao que a mesa conta, em R$. Null = sem teto. */
export function tetoDoDia(conta: Conta): number | null {
  return conta.meta_rs !== null && conta.teto_dia_pct !== null ? conta.meta_rs * conta.teto_dia_pct : null;
}

/** Trade que a mesa nao conta: no WIN, 10 pts ou menos (em modulo). */
function naoConta(t: TradeProva, conta: Conta): boolean {
  return conta.pts_minimos_validos !== null && t.pontos_real != null && Math.abs(Number(t.pontos_real)) <= conta.pts_minimos_validos;
}

/**
 * Tudo o que a prova precisa saber dos trades fechados, em ordem de saida.
 * Trade de 10 pts ou menos: a perda conta, o ganho nao (leitura conservadora do regulamento,
 * que diz so que a operacao "nao conta"). Pregao acima do teto: o excedente nao conta.
 */
export function calcularProva(trades: TradeProva[], conta: Conta): ResumoProva {
  const teto = tetoDoDia(conta);
  const porDia: Record<string, number> = {};
  const validoPorDia: Record<string, number> = {};
  let ganhosIgnorados = 0;
  let nNaoContam = 0;
  let acum = 0;
  let pior = 0;
  let recuo = false;

  for (const t of trades) {
    const p = pnlDe(t);
    porDia[t.data] = (porDia[t.data] ?? 0) + p;
    let valido = p;
    if (naoConta(t, conta)) {
      nNaoContam++;
      if (p > 0) {
        ganhosIgnorados += p;
        valido = 0;
      }
    }
    validoPorDia[t.data] = (validoPorDia[t.data] ?? 0) + valido;

    acum += p;
    pior = Math.min(pior, acum);
    if (acum <= -RECUO_PERDA_RS) recuo = true;
    else if (acum >= 0) recuo = false;
  }

  let resultadoValido = 0;
  let excedente = 0;
  for (const dia of Object.keys(validoPorDia)) {
    const v = validoPorDia[dia];
    if (teto !== null && v > teto) {
      resultadoValido += teto;
      excedente += v - teto;
    } else {
      resultadoValido += v;
    }
  }

  const dias = Object.keys(porDia);
  const maiorData = [...dias].sort((a, b) => porDia[b] - porDia[a])[0];

  return {
    pnlBruto: acum,
    resultadoValido,
    excedenteTeto: excedente,
    naoContam: { n: nNaoContam, ganhosIgnorados },
    pregoes: dias.length,
    porDia,
    maiorDia: maiorData !== undefined ? { data: maiorData, valor: porDia[maiorData] } : null,
    piorAcumulado: pior,
    emRecuo: recuo,
  };
}

/** Contratos permitidos na entrada: o maximo da conta, ou o recuo quando a prova aperta. */
export function contratosPermitidos(conta: Conta, emRecuo: boolean): number {
  if (conta.tipo !== "PROVA" || !emRecuo) return conta.max_contratos;
  return Math.min(CONTRATOS_RECUO, conta.max_contratos);
}

/**
 * Risco maximo de um trade em R$: o da conta vale para a mao cheia. No recuo ele desce junto
 * com a mao (10 contratos e R$ 530 viram 5 e R$ 265), para o stop continuar em 265 pts.
 */
export function riscoMaximoTrade(conta: Conta, emRecuo: boolean): number {
  if (conta.tipo !== "PROVA" || conta.max_contratos <= 0) return conta.max_risco_trade_rs;
  return (conta.max_risco_trade_rs * contratosPermitidos(conta, emRecuo)) / conta.max_contratos;
}

const brl = (v: number) => `${v < 0 ? "−" : ""}R$ ${Math.abs(Math.round(v)).toLocaleString("pt-BR")}`;
const brl2 = (v: number) => `R$ ${v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const STATUS_TXT: Record<string, string> = {
  APROVADA: "prova aprovada: conta encerrada",
  ELIMINADA: "prova eliminada: conta encerrada",
  ENCERRADA: "conta encerrada",
};

export interface EstadoProva {
  pnlDia: number; // R$ de hoje
  resumo: ResumoProva; // a conta inteira, ja com hoje
}

/**
 * Motivos que impedem uma nova entrada na prova (alem dos do gate normal): o dia ja acabou
 * por perda ou por ganho, a prova foi eliminada, ou a meta foi batida.
 */
export function avaliarLimitesProva(conta: Conta, e: EstadoProva): LimitesDia {
  const motivos: string[] = [];
  if (conta.tipo !== "PROVA") return { bloqueado: false, motivos };

  if (conta.status !== "ATIVA") motivos.push(STATUS_TXT[conta.status] ?? "conta encerrada");

  if (e.pnlDia <= -CORTE_PERDA_DIA_RS) {
    motivos.push(`perda do dia em ${brl(-e.pnlDia)}: limite de ${brl(CORTE_PERDA_DIA_RS)} atingido (a mesa corta em ${brl(conta.limite_perda_diaria_rs ?? 0)})`);
  }

  if (e.pnlDia >= TETO_GANHO_DIA_RS) {
    const teto = tetoDoDia(conta);
    motivos.push(`ganho do dia acima de ${brl(TETO_GANHO_DIA_RS)}: encerra${teto !== null ? ` (a mesa só conta ${brl2(teto)} por pregão)` : ""}`);
  }

  if (conta.limite_perda_total_rs !== null && -e.resumo.piorAcumulado >= conta.limite_perda_total_rs) {
    motivos.push(`perda total de ${brl(conta.limite_perda_total_rs)} atingida: prova eliminada`);
  }

  if (conta.meta_rs !== null && e.resumo.resultadoValido >= Math.max(SAIDA_RS, conta.meta_rs) && e.resumo.pregoes >= (conta.min_pregoes ?? 0)) {
    motivos.push(`meta da prova batida (${brl(e.resumo.resultadoValido)}): peça a aprovação na Zero7 e pare`);
  }

  return { bloqueado: motivos.length > 0, motivos };
}

/**
 * O trade que o operador esta montando cabe nas regras? Devolve os problemas, vazio = ok.
 * Risco em R$ = distancia do stop x contratos x R$ 0,20.
 */
export function validarRiscoProva(conta: Conta, riscoRs: number, e: EstadoProva): string[] {
  if (conta.tipo !== "PROVA" || !(riscoRs > 0)) return [];
  const erros: string[] = [];

  const riscoMax = riscoMaximoTrade(conta, e.resumo.emRecuo);
  if (riscoRs > riscoMax) {
    erros.push(`Risco de ${brl(riscoRs)} acima do máximo de ${brl(riscoMax)} por trade${e.resumo.emRecuo ? " (mão reduzida)" : ""}`);
  }

  const cabeNoDia = CORTE_PERDA_DIA_RS + e.pnlDia;
  if (riscoRs > cabeNoDia) {
    erros.push(`O stop (${brl(riscoRs)}) não cabe no limite do dia: restam ${brl(Math.max(0, cabeNoDia))} dos ${brl(CORTE_PERDA_DIA_RS)}`);
  }

  if (conta.limite_perda_total_rs !== null) {
    const cabeNaTotal = conta.limite_perda_total_rs + e.resumo.pnlBruto;
    if (riscoRs > cabeNaTotal) {
      erros.push(`O stop (${brl(riscoRs)}) não cabe na perda total: restam ${brl(Math.max(0, cabeNaTotal))}`);
    }
  }

  return erros;
}

/** Risco em R$ de um trade de WIN. */
export function riscoDoTradeRs(entrada: number, stop: number, contratos: number): number {
  return Math.abs(entrada - stop) * contratos * VALOR_PONTO_WIN;
}

// -----------------------------------------------------------------------------
// Card da Visao Geral
// -----------------------------------------------------------------------------

export type TomProva = "ok" | "atencao" | "perigo";

export interface BlocoProva {
  label: string;
  valor: string;
  sub: string;
  pct: number | null; // 0..1, barra; null = sem barra
  tom: TomProva;
}

export interface Prova {
  nome: string;
  status: "EM_ANDAMENTO" | "META_BATIDA" | "ELIMINADA";
  frase: string;
  ritmo: string;
  blocos: BlocoProva[];
}

const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;
const tomPorUso = (uso: number): TomProva => (uso >= 0.85 ? "perigo" : uso >= 0.5 ? "atencao" : "ok");
const diaMes = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;

/** O card da prova: meta, perda total, perda de hoje, pregoes, maior pregao, nao contam, mao. */
export function montarProva(trades: TradeProva[], conta: Conta, hojeIso: string): Prova | null {
  if (conta.tipo !== "PROVA" || conta.meta_rs === null) return null;

  const r = calcularProva(trades, conta);
  const meta = conta.meta_rs;
  const limiteTotal = conta.limite_perda_total_rs;
  const limiteDia = conta.limite_perda_diaria_rs;
  const minPregoes = conta.min_pregoes ?? 0;
  const teto = tetoDoDia(conta);
  const pnlHoje = r.porDia[hojeIso] ?? 0;
  const usadaTotal = -r.piorAcumulado;

  // O cockpit soma o resultado sem os custos da mesa: a prova so esta ganha na saida do plano
  // (meta + folga de custos), o mesmo ponto em que o gate para de liberar entrada.
  const saida = Math.max(SAIDA_RS, meta);
  const eliminada = conta.status === "ELIMINADA" || (limiteTotal !== null && usadaTotal >= limiteTotal);
  const metaBatida = !eliminada && r.resultadoValido >= saida && r.pregoes >= minPregoes;
  const status: Prova["status"] = eliminada ? "ELIMINADA" : metaBatida ? "META_BATIDA" : "EM_ANDAMENTO";

  const falta = Math.max(0, saida - r.resultadoValido);
  const faltamPregoes = Math.max(0, minPregoes - r.pregoes);
  const frase =
    status === "ELIMINADA"
      ? `Prova eliminada: a perda total de ${brl(limiteTotal ?? 0)} foi atingida`
      : status === "META_BATIDA"
        ? `Meta batida com ${r.pregoes} pregões: peça a aprovação na Zero7 e pare de operar`
        : r.pregoes === 0
          ? `Prova zerada: faltam ${brl(saida)} e ${plural(minPregoes, "pregão", "pregões")} no mínimo`
          : falta > 0
            ? `Faltam ${brl(falta)} para a saída${faltamPregoes > 0 ? ` e ${plural(faltamPregoes, "pregão", "pregões")} no mínimo` : ""}`
            : `Resultado na saída: ${faltamPregoes === 1 ? "falta" : "faltam"} ${plural(faltamPregoes, "pregão", "pregões")} para o mínimo de ${minPregoes}`;

  const restam = Math.max(1, PREGOES_ALVO - r.pregoes);
  const ritmo =
    status !== "EM_ANDAMENTO"
      ? ""
      : r.pregoes >= PREGOES_ALVO
        ? `Passou dos ${PREGOES_ALVO} pregões do plano: sem pressa, o prazo da mesa é ilimitado`
        : `Para fechar em ${PREGOES_ALVO} pregões: ${brl(falta / restam)} por pregão nos ${restam} que restam`;

  const blocos: BlocoProva[] = [
    {
      label: "Resultado para a meta",
      valor: brl(r.resultadoValido),
      sub: `meta de ${brl(meta)} · saída em ${brl(saida)}, com folga para custos${r.excedenteTeto > 0 ? ` · ${brl(r.excedenteTeto)} acima do teto não contam` : ""}`,
      pct: Math.max(0, Math.min(1, r.resultadoValido / saida)),
      tom: "ok",
    },
  ];

  if (limiteTotal !== null) {
    // o limite e fixo sobre o saldo inicial: o que esta usado e o prejuizo de agora, nao o pior ponto
    const usadaAgora = Math.max(0, -r.pnlBruto);
    const uso = usadaAgora / limiteTotal;
    blocos.push({
      label: "Perda total usada",
      valor: brl(usadaAgora),
      sub: `de ${brl(limiteTotal)} · folga de ${brl(Math.max(0, limiteTotal - usadaAgora))}${usadaTotal > usadaAgora ? ` · pior ponto ${brl(-usadaTotal)}` : ""}`,
      pct: Math.max(0, Math.min(1, uso)),
      tom: tomPorUso(uso),
    });
  }

  if (limiteDia !== null) {
    const perdaHoje = Math.max(0, -pnlHoje);
    const uso = perdaHoje / limiteDia;
    blocos.push({
      label: "Perda de hoje",
      valor: brl(perdaHoje),
      sub: `de ${brl(limiteDia)} da mesa · corte do plano ${brl(CORTE_PERDA_DIA_RS)}`,
      pct: Math.max(0, Math.min(1, uso)),
      tom: tomPorUso(perdaHoje / CORTE_PERDA_DIA_RS),
    });
  }

  blocos.push({
    label: "Pregões operados",
    valor: String(r.pregoes),
    sub: minPregoes > 0 ? `mínimo de ${minPregoes}${r.pregoes >= minPregoes ? " · cumprido" : ""}` : "sem mínimo",
    pct: minPregoes > 0 ? Math.min(1, r.pregoes / minPregoes) : null,
    tom: "ok",
  });

  if (teto !== null) {
    const maior = r.maiorDia && r.maiorDia.valor > 0 ? r.maiorDia : null;
    blocos.push({
      label: "Maior pregão",
      valor: maior ? brl(maior.valor) : "—",
      sub: maior ? `${diaMes(maior.data)} · teto de ${brl2(teto)} por pregão${maior.valor > teto ? " · passou, o excedente não conta" : ""}` : `teto de ${brl2(teto)} por pregão`,
      pct: maior ? Math.min(1, maior.valor / teto) : null,
      tom: maior ? tomPorUso(maior.valor / teto) : "ok",
    });
  }

  if (conta.pts_minimos_validos !== null) {
    blocos.push({
      label: `Trades de ${conta.pts_minimos_validos} pts ou menos`,
      valor: String(r.naoContam.n),
      sub: r.naoContam.n > 0 ? `a mesa não conta${r.naoContam.ganhosIgnorados > 0 ? ` · ${brl(r.naoContam.ganhosIgnorados)} de ganho ignorado` : ""}` : "nenhum até agora",
      pct: null,
      tom: r.naoContam.n > 0 ? "atencao" : "ok",
    });
  }

  const maoAtual = contratosPermitidos(conta, r.emRecuo);
  blocos.push({
    label: "Mão da próxima entrada",
    valor: `${maoAtual} contratos`,
    sub: r.emRecuo ? `recuo: desce de ${conta.max_contratos} até o acumulado voltar ao zero` : `recua para ${Math.min(CONTRATOS_RECUO, conta.max_contratos)} com ${brl(RECUO_PERDA_RS)} de prejuízo acumulado`,
    pct: null,
    tom: r.emRecuo ? "atencao" : "ok",
  });

  return { nome: conta.nome, status, frase, ritmo, blocos };
}
