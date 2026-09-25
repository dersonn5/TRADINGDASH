/**
 * lib/metricas.ts
 * Funções puras de cálculo de métricas para a Visão Geral (Cognitive Trading v2).
 * Todas as métricas são determinísticas, sem dependência de banco de dados.
 * Fonte única: §3 e §4 de cockpit/SPEC_FRONT_V2.md.
 */

export interface TradeMetricas {
  id?: string;
  data?: string;
  strategy_id: string;
  mercado?: string;
  direcao: "COMPRA" | "VENDA";
  entrada: number;
  stop: number;
  alvo?: number;
  saida?: number | null;
  pontos_real?: number | null;
  pnl_real?: number | null;
  pnl_plano?: number | null;
  hora_entrada?: string | null;
  hora_saida?: string | null;
  gatilho?: string | null;
  contexto_1h?: string | null;
  setup_c_modo?: string | null;
  respeitou_plano?: boolean | null;
  antecipou_stop?: boolean | null;
  parcial_emocional?: boolean | null;
  mudou_alvo?: boolean | null;
}

export const NOMES_ESTRATEGIAS: Record<string, string> = {
  varrida_barra_10: "Varrida das 10",
  continuidade_tendencia: "Continuidade",
  reversao_htf: "Reversão HTF",
  C: "Varrida das 10",
  B: "Continuidade",
  A: "Reversão HTF",
};

export const NOMES_GATILHOS: Record<string, string> = {
  MSS_FVG: "MSS + FVG",
  MSS_OB: "MSS + OB",
  BPR: "BPR",
  RISK_ENTRY: "Risk entry",
  FVG_POS_SWING: "FVG após swing",
};

export const NOMES_CONTEXTOS: Record<string, string> = {
  CONTINUACAO: "Continuação",
  REVERSAO: "Reversão",
  LATERAL: "Lateral",
};

// ==========================================
// FUNÇÕES UTILITÁRIAS BÁSICAS
// ==========================================

export function somar(valores: number[]): number {
  return valores.reduce((acc, v) => acc + v, 0);
}

export function media(valores: number[]): number {
  if (valores.length === 0) return 0;
  return somar(valores) / valores.length;
}

export function mediana(valores: number[]): number {
  if (valores.length === 0) return 0;
  const ord = [...valores].sort((a, b) => a - b);
  const meio = Math.floor(ord.length / 2);
  if (ord.length % 2 !== 0) {
    return ord[meio];
  }
  return (ord[meio - 1] + ord[meio]) / 2;
}

export function sinal(n: number): string {
  if (n > 0) return "+";
  if (n < 0) return "−";
  return "";
}

export function formatarBRL(valor: number | null | undefined, comSinal = true): string {
  if (valor === null || valor === undefined || isNaN(valor)) return "—";
  const prefixo = comSinal ? sinal(valor) : "";
  const abs = Math.abs(Math.round(valor));
  return `${prefixo}R$ ${abs.toLocaleString("pt-BR")}`;
}

export function formatarR(valor: number | null | undefined, comSinal = true): string {
  if (valor === null || valor === undefined || isNaN(valor)) return "—";
  const prefixo = comSinal ? sinal(valor) : "";
  const abs = Math.abs(valor).toFixed(2).replace(".", ",");
  return `${prefixo}${abs}R`;
}

export function formatarPct(taxa: number | null | undefined): string {
  if (taxa === null || taxa === undefined || isNaN(taxa)) return "—";
  return `${Math.round(taxa * 100)}%`;
}

export function formatarNumero(valor: number | null | undefined, casas = 2): string {
  if (valor === null || valor === undefined || isNaN(valor)) return "—";
  return valor.toFixed(casas).replace(".", ",");
}

// ==========================================
// MÉTRICAS INDIVIDUAIS DO TRADE
// ==========================================

export function calcularRiscoTrade(entrada: number, stop: number): number {
  return Math.abs(entrada - stop);
}

export function calcularRTrade(pontosReal: number, risco: number): number {
  if (risco <= 0) return 0;
  return pontosReal / risco;
}

export function temDesvio(t: TradeMetricas): boolean {
  return (
    t.respeitou_plano === false ||
    Boolean(t.antecipou_stop) ||
    Boolean(t.parcial_emocional) ||
    Boolean(t.mudou_alvo)
  );
}

export function calcularCustoDesvio(t: TradeMetricas): number {
  if (!temDesvio(t)) return 0;
  const pnlPlano = Number(t.pnl_plano ?? 0);
  const pnlReal = Number(t.pnl_real ?? 0);
  const diff = pnlPlano - pnlReal;
  return diff > 0 ? diff : 0;
}

// ==========================================
// FAIXA DE HORÁRIO (AMERICA/SAO_PAULO)
// ==========================================

export function classificarFaixaHorario(horaEntrada: string | Date | null | undefined): string {
  if (!horaEntrada) return "fora da janela";
  const date = typeof horaEntrada === "string" ? new Date(horaEntrada) : horaEntrada;
  if (isNaN(date.getTime())) return "fora da janela";

  const parts = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date);

  const hStr = parts.find((p) => p.type === "hour")?.value ?? "0";
  const mStr = parts.find((p) => p.type === "minute")?.value ?? "0";
  const hour = parseInt(hStr, 10);
  const minute = parseInt(mStr, 10);
  const totalMinutos = hour * 60 + minute;

  // Janela operacional WIN: 10:00 (600 min) até 11:29 (689 min)
  if (totalMinutos < 600 || totalMinutos >= 690) {
    return "fora da janela";
  }

  const faixaMinutos = Math.floor(totalMinutos / 15) * 15;
  const fHour = Math.floor(faixaMinutos / 60);
  const fMin = faixaMinutos % 60;
  return `${String(fHour).padStart(2, "0")}:${String(fMin).padStart(2, "0")}`;
}

export function fimDaFaixa(faixa: string): string {
  if (faixa === "fora da janela") return "";
  const [h, m] = faixa.split(":").map(Number);
  const fim = h * 60 + m + 14;
  const fh = Math.floor(fim / 60);
  const fm = fim % 60;
  return `${String(fh).padStart(2, "0")}:${String(fm).padStart(2, "0")}`;
}

// ==========================================
// DRAWDOWN
// ==========================================

export interface DrawdownResult {
  maxDrawdown: number;
  picoIndex: number;
  valeIndex: number;
}

export function calcularDrawdown(valores: number[]): DrawdownResult {
  let acumulado = 0;
  let pico = 0;
  let maxDD = 0;
  let currentPicoIndex = 0;
  let picoIndex = 0;
  let valeIndex = 0;

  for (let i = 0; i < valores.length; i++) {
    acumulado += valores[i];
    if (acumulado > pico) {
      pico = acumulado;
      currentPicoIndex = i + 1;
    }
    const dd = pico - acumulado;
    if (dd > maxDD) {
      maxDD = dd;
      picoIndex = currentPicoIndex;
      valeIndex = i + 1;
    }
  }

  return { maxDrawdown: maxDD, picoIndex, valeIndex };
}

// ==========================================
// RESUMO DE CONJUNTO DE TRADES (KPIS GERAIS)
// ==========================================

export interface KPIsGerais {
  totalTrades: number;
  resultadoReais: number;
  resultadoR: number;
  taxaAcerto: number; // 0..1
  expectativaR: number;
  profitFactor: number | null;
  payoff: number | null;
  maxDrawdownReais: number;
  maxDrawdownR: number;
  stopMediano: number;
}

export function calcularKPIsGerais(trades: TradeMetricas[]): KPIsGerais {
  const n = trades.length;
  if (n === 0) {
    return {
      totalTrades: 0,
      resultadoReais: 0,
      resultadoR: 0,
      taxaAcerto: 0,
      expectativaR: 0,
      profitFactor: null,
      payoff: null,
      maxDrawdownReais: 0,
      maxDrawdownR: 0,
      stopMediano: 0,
    };
  }

  const pnlList = trades.map((t) => Number(t.pnl_real ?? 0));
  const rList = trades.map((t) => {
    const risco = calcularRiscoTrade(Number(t.entrada), Number(t.stop));
    return calcularRTrade(Number(t.pontos_real ?? 0), risco);
  });
  const riscoList = trades.map((t) => calcularRiscoTrade(Number(t.entrada), Number(t.stop)));

  const resultadoReais = somar(pnlList);
  const resultadoR = somar(rList);
  const ganhos = pnlList.filter((p) => p > 0);
  const perdas = pnlList.filter((p) => p < 0);
  const somaGanhos = somar(ganhos);
  const somaPerdas = Math.abs(somar(perdas));

  const taxaAcerto = ganhos.length / n;
  const expectativaR = resultadoR / n;

  const profitFactor = somaPerdas > 0 ? somaGanhos / somaPerdas : null;
  const mediaGanhos = media(ganhos);
  const mediaPerdas = Math.abs(media(perdas));
  const payoff = perdas.length > 0 && mediaPerdas > 0 ? mediaGanhos / mediaPerdas : null;

  const ddReais = calcularDrawdown(pnlList).maxDrawdown;
  const ddR = calcularDrawdown(rList).maxDrawdown;
  const stopMed = mediana(riscoList);

  return {
    totalTrades: n,
    resultadoReais,
    resultadoR,
    taxaAcerto,
    expectativaR,
    profitFactor,
    payoff,
    maxDrawdownReais: ddReais,
    maxDrawdownR: ddR,
    stopMediano: stopMed,
  };
}

// ==========================================
// AGRUPAMENTOS DA VISÃO GERAL (§3)
// ==========================================

export interface MetricasEstrategia {
  strategy_id: string;
  nome: string;
  n: number;
  pnl: number;
  totalR: number;
  rm: number;
  taxaAcerto: number;
  maxDrawdownReais: number;
  maxDrawdownR: number;
  stopMediano: number;
}

export function agruparPorEstrategia(trades: TradeMetricas[]): {
  itens: MetricasEstrategia[];
  maisTrades: MetricasEstrategia | null;
  maisResultado: MetricasEstrategia | null;
  piorResultado: MetricasEstrategia | null;
  fraseResumo: string;
  fraseTabela: string;
} {
  const ids = Array.from(new Set(trades.map((t) => t.strategy_id))).filter(Boolean);
  if (ids.length === 0) {
    return {
      itens: [],
      maisTrades: null,
      maisResultado: null,
      piorResultado: null,
      fraseResumo: "Nenhum trade registrado",
      fraseTabela: "Nenhum dado por estratégia",
    };
  }

  const itens = ids.map((id) => {
    const ts = trades.filter((t) => t.strategy_id === id);
    const kpis = calcularKPIsGerais(ts);
    return {
      strategy_id: id,
      nome: NOMES_ESTRATEGIAS[id] || id,
      n: kpis.totalTrades,
      pnl: kpis.resultadoReais,
      totalR: kpis.resultadoR,
      rm: kpis.expectativaR,
      taxaAcerto: kpis.taxaAcerto,
      maxDrawdownReais: kpis.maxDrawdownReais,
      maxDrawdownR: kpis.maxDrawdownR,
      stopMediano: kpis.stopMediano,
    };
  });

  const maisTrades = [...itens].sort((a, b) => b.n - a.n)[0] || null;
  const maisResultado = [...itens].sort((a, b) => b.pnl - a.pnl)[0] || null;
  const piorResultado = [...itens].sort((a, b) => a.pnl - b.pnl)[0] || null;

  const fraseResumo = maisTrades && maisResultado
    ? `Mais trades: ${maisTrades.nome} (${maisTrades.n}) · mais resultado: ${maisResultado.nome}`
    : "";

  const fraseTabela = maisResultado && piorResultado
    ? `${maisResultado.nome} carrega o mês com ${formatarBRL(maisResultado.pnl)}; ${piorResultado.nome}${
        piorResultado.pnl < 0 ? " está negativa: " : " tem o menor resultado: "
      }${formatarBRL(piorResultado.pnl)}`
    : "";

  return { itens, maisTrades, maisResultado, piorResultado, fraseResumo, fraseTabela };
}

export interface FaixaHorarioItem {
  faixa: string;
  fim: string;
  n: number;
  rm: number;
  pnl: number;
}

export function agruparPorHorario(trades: TradeMetricas[]): {
  itens: FaixaHorarioItem[];
  melhor: FaixaHorarioItem | null;
  frase: string;
  amostraPequena: boolean;
} {
  const faixasPadrao = ["10:00", "10:15", "10:30", "10:45", "11:00", "11:15"];
  const itens = faixasPadrao.map((f) => {
    const ts = trades.filter((t) => classificarFaixaHorario(t.hora_entrada) === f);
    const pnl = somar(ts.map((t) => Number(t.pnl_real ?? 0)));
    const rList = ts.map((t) => {
      const risco = calcularRiscoTrade(Number(t.entrada), Number(t.stop));
      return calcularRTrade(Number(t.pontos_real ?? 0), risco);
    });
    return {
      faixa: f,
      fim: fimDaFaixa(f),
      n: ts.length,
      rm: ts.length > 0 ? media(rList) : 0,
      pnl,
    };
  });

  const comTrades = itens.filter((i) => i.n > 0);
  const melhor = comTrades.length > 0 ? [...comTrades].sort((a, b) => b.rm - a.rm)[0] : null;

  const amostraPequena = melhor ? melhor.n < 10 : true;
  const frase = melhor
    ? `Melhor faixa: ${melhor.faixa}–${melhor.fim} · ${formatarR(melhor.rm)} médio · ${melhor.n} ${
        melhor.n === 1 ? "trade" : "trades"
      }`
    : "Sem dados suficientes de horário";

  return { itens, melhor, frase, amostraPequena };
}

export interface GatilhoItem {
  gatilho: string;
  nome: string;
  n: number;
  pct: number;
  rm: number;
}

export function agruparPorGatilho(trades: TradeMetricas[]): {
  itens: GatilhoItem[];
  maisUsado: GatilhoItem | null;
  pagaMais: GatilhoItem | null;
  frase: string;
  amostraPequena: boolean;
} {
  const total = trades.length;
  if (total === 0) {
    return { itens: [], maisUsado: null, pagaMais: null, frase: "Nenhum gatilho registrado", amostraPequena: true };
  }

  const chaves = Object.keys(NOMES_GATILHOS);
  const itens: GatilhoItem[] = chaves
    .map((k) => {
      const ts = trades.filter((t) => t.gatilho === k);
      const rList = ts.map((t) => {
        const risco = calcularRiscoTrade(Number(t.entrada), Number(t.stop));
        return calcularRTrade(Number(t.pontos_real ?? 0), risco);
      });
      return {
        gatilho: k,
        nome: NOMES_GATILHOS[k] || k,
        n: ts.length,
        pct: ts.length / total,
        rm: ts.length > 0 ? media(rList) : 0,
      };
    })
    .filter((g) => g.n > 0)
    .sort((a, b) => b.n - a.n);

  const maisUsado = itens[0] || null;
  const comAmostra = itens.filter((g) => g.n >= 2);
  const pagaMais = comAmostra.length > 0 ? [...comAmostra].sort((a, b) => b.rm - a.rm)[0] : itens[0] || null;

  const frase = maisUsado && pagaMais
    ? `Mais usado: ${maisUsado.nome} (${maisUsado.n} de ${total}) · paga mais: ${pagaMais.nome} ${formatarR(pagaMais.rm)}`
    : "Sem dados de gatilho";

  return { itens, maisUsado, pagaMais, frase, amostraPequena: total < 10 };
}

export interface FaixaStopItem {
  rotulo: string;
  min: number;
  max: number;
  n: number;
}

export function calcularDistribuicaoStops(trades: TradeMetricas[]): {
  faixas: FaixaStopItem[];
  medianaStop: number;
  acima250: number;
  frase: string;
} {
  const limites = [
    { rotulo: "< 150", min: 0, max: 150 },
    { rotulo: "150–199", min: 150, max: 200 },
    { rotulo: "200–249", min: 200, max: 250 },
    { rotulo: "250–299", min: 250, max: 300 },
    { rotulo: "300+", min: 300, max: Infinity },
  ];

  const riscos = trades.map((t) => calcularRiscoTrade(Number(t.entrada), Number(t.stop)));
  const medianaStop = mediana(riscos);
  const acima250 = riscos.filter((r) => r >= 250).length;

  const faixas = limites.map((l) => ({
    rotulo: l.rotulo,
    min: l.min,
    max: l.max,
    n: riscos.filter((r) => r >= l.min && r < l.max).length,
  }));

  const frase = `Stop mediano ${medianaStop} pts · ${acima250} ${
    acima250 === 1 ? "stop" : "stops"
  } de 250 pts ou mais`;

  return { faixas, medianaStop, acima250, frase };
}

export interface DisciplinaResumo {
  pctNoPlano: number;
  tradesNoPlano: number;
  totalTrades: number;
  custoTotal: number;
  frase: string;
}

export function calcularDisciplina(trades: TradeMetricas[]): DisciplinaResumo {
  const n = trades.length;
  if (n === 0) {
    return { pctNoPlano: 1, tradesNoPlano: 0, totalTrades: 0, custoTotal: 0, frase: "Sem trades no mês" };
  }

  const desvios = trades.filter((t) => temDesvio(t));
  const tradesNoPlano = n - desvios.length;
  const pctNoPlano = tradesNoPlano / n;
  const custoTotal = somar(desvios.map((t) => calcularCustoDesvio(t)));

  const frase =
    desvios.length === 0
      ? "100% dos trades respeitaram o plano"
      : custoTotal > 0
        ? `Desvios custaram ${formatarBRL(custoTotal, false)} no mês`
        : `${desvios.length} ${desvios.length === 1 ? "desvio" : "desvios"} do plano, sem custo medido`;

  return { pctNoPlano, tradesNoPlano, totalTrades: n, custoTotal, frase };
}

export interface SetupCContextoResumo {
  modos: Array<{ nome: string; n: number; taxaAcerto: number; rm: number }>;
  contextos: Array<{ nome: string; n: number; taxaAcerto: number; rm: number }>;
  frase: string;
  amostraPequena: boolean;
}

export function agruparSetupCeContexto(trades: TradeMetricas[]): SetupCContextoResumo {
  const tradesSetupC = trades.filter((t) => t.strategy_id === "varrida_barra_10" || t.strategy_id === "C");

  const modos = ["C1", "C2"].map((m) => {
    const ts = tradesSetupC.filter((t) => t.setup_c_modo === m);
    const k = calcularKPIsGerais(ts);
    return {
      nome: m,
      n: k.totalTrades,
      taxaAcerto: k.taxaAcerto,
      rm: k.expectativaR,
    };
  });

  const contextos = ["CONTINUACAO", "REVERSAO", "LATERAL"].map((ctx) => {
    const ts = trades.filter((t) => t.contexto_1h === ctx);
    const k = calcularKPIsGerais(ts);
    return {
      nome: NOMES_CONTEXTOS[ctx] || ctx,
      n: k.totalTrades,
      taxaAcerto: k.taxaAcerto,
      rm: k.expectativaR,
    };
  });

  const total = trades.length;
  const frase = `C1 ${formatarR(modos[0].rm)} × C2 ${formatarR(modos[1].rm)} por trade`;

  return { modos, contextos, frase, amostraPequena: total < 10 };
}
