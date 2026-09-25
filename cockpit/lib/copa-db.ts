import { supabase } from "./supabase";
import { mercadoPermitido } from "./gate";

export type GatilhoTrade = "MSS_FVG" | "MSS_OB" | "BPR" | "RISK_ENTRY" | "FVG_POS_SWING";
export type Contexto1h = "CONTINUACAO" | "REVERSAO" | "LATERAL";
export type SetupCModo = "C1" | "C2";

export interface TradeInput {
  strategy_id: string;
  mercado: "WIN" | "WDO";
  direcao: "COMPRA" | "VENDA";
  janela: "PRIME" | "VALIDA" | "FORA";
  score: number;
  score_minimo: number;
  grade: string;
  entrada: number;
  stop: number;
  alvo: number;
  contratos: number;
  rr_planejado: number;
  itens: Array<{ item_id: string; tipo: "KILL" | "PONTO"; checked: boolean; peso_no_momento: number }>;
  notas?: string;
  screenshot_path?: string | null;
  gatilho?: GatilhoTrade | string | null;
  contexto_1h?: Contexto1h | string | null;
  setup_c_modo?: SetupCModo | string | null;
}

export function validarCamposNovosTrade(input: {
  strategy_id: string;
  gatilho?: string | null;
  contexto_1h?: string | null;
  setup_c_modo?: string | null;
}): void {
  if (!input.gatilho) {
    throw new Error("gatilho é obrigatório para registrar o trade");
  }
  const GATILHOS_VALIDOS: GatilhoTrade[] = ["MSS_FVG", "MSS_OB", "BPR", "RISK_ENTRY", "FVG_POS_SWING"];
  if (!GATILHOS_VALIDOS.includes(input.gatilho as GatilhoTrade)) {
    throw new Error(`gatilho inválido: ${input.gatilho}`);
  }

  if (!input.contexto_1h) {
    throw new Error("contexto da 1ª hora é obrigatório para registrar o trade");
  }
  const CONTEXTOS_VALIDOS: Contexto1h[] = ["CONTINUACAO", "REVERSAO", "LATERAL"];
  if (!CONTEXTOS_VALIDOS.includes(input.contexto_1h as Contexto1h)) {
    throw new Error(`contexto da 1ª hora inválido: ${input.contexto_1h}`);
  }

  if (input.strategy_id === "varrida_barra_10") {
    if (!input.setup_c_modo) {
      throw new Error("modo do Setup C (C1 ou C2) é obrigatório para a estratégia varrida_barra_10");
    }
    const MODOS_VALIDOS: SetupCModo[] = ["C1", "C2"];
    if (!MODOS_VALIDOS.includes(input.setup_c_modo as SetupCModo)) {
      throw new Error(`modo do Setup C inválido: ${input.setup_c_modo}`);
    }
  }
}

export interface ResumoDoDia {
  session_id: string | null;
  trades_fechados: number;
  trades_abertos: number;
  operacoes_hoje: number; // fechados + abertos
  perdas_hoje: number;
  pnl_dia: number;
  ultimo_loss_em: Date | null;
  trade_aberto_id: string | null;
}

export interface FechamentoInput {
  saida: number;
  motivo_saida: "ALVO" | "STOP" | "MANUAL";
  desfecho_plano?: "BATEU_ALVO" | "BATEU_STOP" | "NAO_SEI";
  execucao: "A" | "B" | "C";
  respeitou_plano: boolean;
  antecipou_stop: boolean;
  parcial_emocional: boolean;
  mudou_alvo: boolean;
  notas?: string;
}

/**
 * Retorna a data corrente em America/Sao_Paulo no formato YYYY-MM-DD.
 * Nunca usar toISOString() do navegador, pois após as 21h em SP dá o dia seguinte em UTC.
 */
export function getDataSaoPaulo(data: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(data);
  return parts;
}

/**
 * Converte um score numérico na régua padrão de grade (A+, A, B, C, D).
 */
export function gradeFor(score: number): string {
  if (score >= 80) return "A+";
  if (score >= 65) return "A";
  if (score >= 50) return "B";
  if (score >= 35) return "C";
  return "D";
}

/**
 * Retorna a versão vigente (UUID da linha em copa_strategy_versions com maior versao)
 * de uma estratégia.
 */
export async function getVersaoVigente(strategyId: string): Promise<string | null> {
  const { data, error } = await supabase
    .from("copa_strategy_versions")
    .select("id, versao")
    .eq("strategy_id", strategyId)
    .order("versao", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) {
    throw new Error(`Erro ao buscar versão vigente: ${error.message}`);
  }

  return data?.id ?? null;
}

/**
 * Localiza a sessão do dia para o usuário autenticado em America/Sao_Paulo.
 * Não cria mais sessão implicitamente: exige que a pré-sessão esteja fechada.
 */
/**
 * Devolve o id da sessao de hoje, e SO se ela estiver fechada.
 *
 * Nao cria sessao. Criar sessao e ato do ritual de pre-sessao, nunca efeito
 * colateral de registrar trade — se criasse, a pre-sessao deixaria de ser
 * obrigatoria na pratica.
 */
export async function getSessaoFechadaDoDia(): Promise<string> {
  const hoje = getDataSaoPaulo();

  const { data: session, error: errSelect } = await supabase
    .from("copa_sessions")
    .select("id, fechada_em")
    .eq("data", hoje)
    .maybeSingle();

  if (errSelect) {
    throw new Error(`Erro ao buscar sessão do dia: ${errSelect.message}`);
  }

  if (!session || !session.fechada_em) {
    throw new Error("pré-sessão do dia não foi fechada");
  }

  return session.id;
}

/**
 * Retorna o resumo operacional do pregão de hoje.
 */
export async function getResumoDoDia(): Promise<ResumoDoDia> {
  const hoje = getDataSaoPaulo();

  const { data: session, error: errSession } = await supabase
    .from("copa_sessions")
    .select("id")
    .eq("data", hoje)
    .maybeSingle();

  if (errSession) {
    throw new Error(`Erro ao buscar sessão do dia: ${errSession.message}`);
  }

  if (!session) {
    return {
      session_id: null,
      trades_fechados: 0,
      trades_abertos: 0,
      operacoes_hoje: 0,
      perdas_hoje: 0,
      pnl_dia: 0,
      ultimo_loss_em: null,
      trade_aberto_id: null,
    };
  }

  const { data: trades, error: errTrades } = await supabase
    .from("copa_trades")
    .select("id, status, pnl_real, hora_entrada, hora_saida, created_at")
    .eq("session_id", session.id);

  if (errTrades) {
    throw new Error(`Erro ao buscar trades da sessão: ${errTrades.message}`);
  }

  const lista = trades || [];
  let tradesFechados = 0;
  let tradesAbertos = 0;
  let perdasHoje = 0;
  let pnlDia = 0;
  let tradeAbertoId: string | null = null;
  let ultimoLossEm: Date | null = null;

  for (const t of lista) {
    if (t.status === "ABERTO") {
      tradesAbertos++;
      if (!tradeAbertoId) {
        tradeAbertoId = t.id;
      }
    } else if (t.status === "FECHADO") {
      tradesFechados++;
      const pnl = Number(t.pnl_real) || 0;
      pnlDia += pnl;

      if (pnl < 0) {
        perdasHoje++;
        const lossTimeStr = t.hora_saida || t.created_at;
        if (lossTimeStr) {
          const lossDate = new Date(lossTimeStr);
          if (!ultimoLossEm || lossDate.getTime() > ultimoLossEm.getTime()) {
            ultimoLossEm = lossDate;
          }
        }
      }
    }
  }

  return {
    session_id: session.id,
    trades_fechados: tradesFechados,
    trades_abertos: tradesAbertos,
    operacoes_hoje: tradesFechados + tradesAbertos,
    perdas_hoje: perdasHoje,
    pnl_dia: Number(pnlDia.toFixed(2)),
    ultimo_loss_em: ultimoLossEm,
    trade_aberto_id: tradeAbertoId,
  };
}

/**
 * Busca dados de um trade específico.
 */
export async function getTrade(id: string) {
  const { data, error } = await supabase
    .from("copa_trades")
    .select("*")
    .eq("id", id)
    .maybeSingle();

  if (error) {
    throw new Error(`Erro ao buscar trade ${id}: ${error.message}`);
  }
  return data;
}

export interface TradeHistorico {
  id: string;
  data: string;
  strategy_id: string;
  mercado: string;
  direcao: "COMPRA" | "VENDA";
  janela: string;
  status: "ABERTO" | "FECHADO";
  hora_entrada: string;
  hora_saida: string | null;
  score: number;
  grade: string;
  entrada: number;
  stop: number;
  alvo: number;
  contratos: number;
  rr_planejado: number;
  saida: number | null;
  motivo_saida: string | null;
  pontos_real: number | null;
  pnl_real: number | null;
  pnl_plano: number | null;
  respeitou_plano: boolean | null;
  antecipou_stop: boolean | null;
  parcial_emocional: boolean | null;
  mudou_alvo: boolean | null;
  notas: string | null;
  gatilho?: GatilhoTrade | null;
  contexto_1h?: Contexto1h | null;
  setup_c_modo?: SetupCModo | null;
}

/**
 * Todos os trades registrados pelo checklist, do mais recente para o mais antigo.
 */
export async function listarTrades(): Promise<TradeHistorico[]> {
  const { data, error } = await supabase
    .from("copa_trades")
    .select("*, copa_sessions(data), copa_strategy_versions(strategy_id)")
    .order("hora_entrada", { ascending: false });

  if (error) {
    throw new Error(`Erro ao buscar trades: ${error.message}`);
  }

  return (data || []).map((t: any) => ({
    ...t,
    data: t.copa_sessions?.data ?? t.hora_entrada?.slice(0, 10) ?? "",
    strategy_id: t.copa_strategy_versions?.strategy_id ?? "",
  }));
}

/**
 * Trades fechados do mês especificado (ano, mês 1..12), ordenados por hora_saida ASC.
 * Filtra pela data da sessão (copa_sessions.data) entre o primeiro e o último dia do mês.
 */
export async function listarTradesDoMes(
  ano: number,
  mes: number
): Promise<TradeHistorico[]> {
  const mesStr = String(mes).padStart(2, "0");
  const dataInicio = `${ano}-${mesStr}-01`;
  const ultimoDia = new Date(ano, mes, 0).getDate();
  const dataFim = `${ano}-${mesStr}-${String(ultimoDia).padStart(2, "0")}`;

  const { data, error } = await supabase
    .from("copa_trades")
    .select("*, copa_sessions!inner(data), copa_strategy_versions(strategy_id)")
    .eq("status", "FECHADO")
    .gte("copa_sessions.data", dataInicio)
    .lte("copa_sessions.data", dataFim)
    .order("hora_saida", { ascending: true, nullsFirst: false });

  if (error) {
    // Fallback caso o filtro em join dê erro na sintaxe
    const { data: fallbackData, error: fallbackError } = await supabase
      .from("copa_trades")
      .select("*, copa_sessions(data), copa_strategy_versions(strategy_id)")
      .eq("status", "FECHADO")
      .order("hora_saida", { ascending: true, nullsFirst: false });

    if (fallbackError) {
      throw new Error(`Erro ao buscar trades do mês: ${fallbackError.message}`);
    }

    return (fallbackData || [])
      .map((t: any) => ({
        ...t,
        data: t.copa_sessions?.data ?? t.hora_entrada?.slice(0, 10) ?? "",
        strategy_id: t.copa_strategy_versions?.strategy_id ?? "",
      }))
      .filter((t: any) => t.data >= dataInicio && t.data <= dataFim);
  }

  return (data || []).map((t: any) => ({
    ...t,
    data: t.copa_sessions?.data ?? t.hora_entrada?.slice(0, 10) ?? "",
    strategy_id: t.copa_strategy_versions?.strategy_id ?? "",
  }));
}

/**
 * Registra a abertura de um trade em duas etapas:
 * 1. insere em copa_trades
 * 2. insere todos os itens em copa_trade_items
 * Se o passo 2 falhar, apaga o trade do passo 1 e propaga o erro.
 */
export async function registrarTrade(input: TradeInput): Promise<string> {
  // Trava na gravacao, e nao so na tela: nenhum caminho da interface consegue
  // registrar um mercado fora do operacional.
  if (!mercadoPermitido(input.mercado)) {
    throw new Error(`${input.mercado} fora do operacional: so WIN`);
  }

  // Trava na gravação para os novos campos obrigatórios (FR-005)
  validarCamposNovosTrade(input);

  const sessionId = await getSessaoFechadaDoDia();
  const versionId = await getVersaoVigente(input.strategy_id);

  if (!versionId) {
    throw new Error(`Nenhuma versão vigente encontrada para a estratégia: ${input.strategy_id}`);
  }

  const { data: trade, error: errTrade } = await supabase
    .from("copa_trades")
    .insert({
      session_id: sessionId,
      version_id: versionId,
      mercado: input.mercado,
      direcao: input.direcao,
      janela: input.janela,
      hora_entrada: new Date().toISOString(),
      score: input.score,
      score_minimo: input.score_minimo,
      grade: input.grade,
      entrada: input.entrada,
      stop: input.stop,
      alvo: input.alvo,
      contratos: input.contratos,
      rr_planejado: input.rr_planejado,
      status: "ABERTO",
      notas: input.notas || "",
      screenshot_path: input.screenshot_path || null,
      gatilho: input.gatilho,
      contexto_1h: input.contexto_1h,
      setup_c_modo: input.setup_c_modo || null,
    })
    .select("id")
    .single();

  if (errTrade) {
    throw new Error(errTrade.message);
  }

  const tradeId = trade.id;

  const itemsToInsert = input.itens.map((it) => ({
    trade_id: tradeId,
    item_id: it.item_id,
    tipo: it.tipo,
    checked: it.checked,
    peso_no_momento: it.peso_no_momento,
  }));

  const { error: errItems } = await supabase
    .from("copa_trade_items")
    .insert(itemsToInsert);

  if (errItems) {
    // Apaga o trade criado no passo 1 e propaga o erro real
    await supabase.from("copa_trades").delete().eq("id", tradeId);
    throw new Error(errItems.message);
  }

  return tradeId;
}

/**
 * Fecha um trade aberto calculando pontos_real, pnl_real, pnl_plano
 * e prefixando as notas com [EXEC:A], [EXEC:B] ou [EXEC:C].
 */
export async function fecharTrade(id: string, f: FechamentoInput): Promise<void> {
  const { data: trade, error: errFetch } = await supabase
    .from("copa_trades")
    .select("id, entrada, stop, alvo, contratos, mercado, direcao, notas")
    .eq("id", id)
    .single();

  if (errFetch || !trade) {
    throw new Error(`Trade ${id} não encontrado: ${errFetch?.message || "Registro inexistente"}`);
  }

  const sinal = trade.direcao === "COMPRA" ? 1 : -1;
  const valorPonto = trade.mercado === "WIN" ? 0.2 : 10.0;
  const pontosReal = (f.saida - trade.entrada) * sinal;
  const pnlReal = Number((pontosReal * trade.contratos * valorPonto).toFixed(2));

  let pnlPlano = pnlReal;
  if (f.motivo_saida === "ALVO" || f.motivo_saida === "STOP") {
    pnlPlano = pnlReal;
  } else if (f.motivo_saida === "MANUAL") {
    if (f.desfecho_plano === "BATEU_ALVO") {
      const pontosPlano = (trade.alvo - trade.entrada) * sinal;
      pnlPlano = Number((pontosPlano * trade.contratos * valorPonto).toFixed(2));
    } else if (f.desfecho_plano === "BATEU_STOP") {
      const pontosPlano = (trade.stop - trade.entrada) * sinal;
      pnlPlano = Number((pontosPlano * trade.contratos * valorPonto).toFixed(2));
    } else {
      pnlPlano = pnlReal;
    }
  }

  const prefixo = `[EXEC:${f.execucao}]`;
  const notasFinal = f.notas && f.notas.trim() ? `${prefixo} ${f.notas.trim()}` : prefixo;

  const { error: errUpdate } = await supabase
    .from("copa_trades")
    .update({
      status: "FECHADO",
      saida: f.saida,
      hora_saida: new Date().toISOString(),
      motivo_saida: f.motivo_saida,
      desfecho_plano: f.desfecho_plano ?? null,
      pontos_real: Number(pontosReal.toFixed(2)),
      pnl_real: pnlReal,
      pnl_plano: pnlPlano,
      respeitou_plano: f.respeitou_plano,
      antecipou_stop: f.antecipou_stop,
      parcial_emocional: f.parcial_emocional,
      mudou_alvo: f.mudou_alvo,
      notas: notasFinal,
    })
    .eq("id", id);

  if (errUpdate) {
    throw new Error(errUpdate.message);
  }
}

// -----------------------------------------------------------------------------
// RITUAL DE PRÉ-SESSÃO
// -----------------------------------------------------------------------------

export interface PreSessao {
  id: string | null;
  data: string;
  phase_id: string | null;
  bias_d1: "COMPRA" | "VENDA" | "INDEFINIDO";
  bias_h1: "COMPRA" | "VENDA" | "INDEFINIDO";
  contexto: "TENDENCIA" | "RANGE" | "INDEFINIDO";
  niveis: Array<{ label: string; preco: string }>;
  agenda: Array<{ evento: string; horario: string; impacto: "ALTO" | "MEDIO" | "BAIXO" }>;
  sono: number;
  tilt: number;
  pressao: number;
  setup_do_dia: "reversao_htf" | "continuidade_tendencia" | "varrida_barra_10" | "NENHUM" | null;
  contratos_declarados: number | null;
  screenshot_path: string | null;
  fechada_em: string | null;
  notas: string;
}

/**
 * O que falta para poder fechar. Vazio = pode fechar.
 * Espelha o CHECK chk_presessao_completa do banco.
 */
export function pendenciasDaPreSessao(p: PreSessao): string[] {
  const pendencias: string[] = [];

  if (!p?.screenshot_path) {
    pendencias.push("print do gráfico HTF não anexado");
  }

  if (!p?.bias_h1 || p.bias_h1 === "INDEFINIDO") {
    pendencias.push("bias H1 não definido");
  }

  if (!p?.contexto || p.contexto === "INDEFINIDO") {
    pendencias.push("contexto não definido");
  }

  if (!p?.niveis || p.niveis.length < 2) {
    pendencias.push("marque ao menos 2 níveis de liquidez ou array");
  }

  if (!p?.setup_do_dia) {
    pendencias.push("setup do dia não escolhido");
  }

  if (p?.setup_do_dia !== "NENHUM" && (!p?.contratos_declarados || p.contratos_declarados <= 0)) {
    pendencias.push("tamanho não declarado");
  }

  return pendencias;
}

/**
 * Retorna a pré-sessão de hoje do usuário em America/Sao_Paulo.
 * Se ainda não existir registro no banco, devolve os valores padrão abertos.
 */
export async function getPreSessaoDeHoje(): Promise<PreSessao> {
  const hoje = getDataSaoPaulo();
  const { data, error } = await supabase
    .from("copa_sessions")
    .select("*")
    .eq("data", hoje)
    .maybeSingle();

  if (error) {
    throw new Error(`Erro ao buscar pré-sessão de hoje: ${error.message}`);
  }

  if (!data) {
    return {
      id: null,
      data: hoje,
      phase_id: null,
      bias_d1: "INDEFINIDO",
      bias_h1: "INDEFINIDO",
      contexto: "INDEFINIDO",
      niveis: [],
      agenda: [],
      sono: 3,
      tilt: 0,
      pressao: 0,
      setup_do_dia: null,
      contratos_declarados: null,
      screenshot_path: null,
      fechada_em: null,
      notas: "",
    };
  }

  return {
    id: data.id,
    data: data.data || hoje,
    phase_id: data.phase_id || null,
    bias_d1: data.bias_d1 || "INDEFINIDO",
    bias_h1: data.bias_h1 || "INDEFINIDO",
    contexto: data.contexto || "INDEFINIDO",
    niveis: Array.isArray(data.niveis) ? data.niveis : [],
    agenda: Array.isArray(data.agenda) ? data.agenda : [],
    sono: data.sono ?? 3,
    tilt: data.tilt ?? 0,
    pressao: data.pressao ?? 0,
    setup_do_dia: data.setup_do_dia || null,
    contratos_declarados: data.contratos_declarados || null,
    screenshot_path: data.screenshot_path || null,
    fechada_em: data.fechada_em || null,
    notas: data.notas || "",
  };
}

/**
 * Salva (cria ou atualiza) os campos da pré-sessão no banco de dados.
 */
export async function salvarPreSessao(p: Partial<PreSessao>): Promise<string> {
  const hoje = getDataSaoPaulo();

  const { data: existing, error: errSelect } = await supabase
    .from("copa_sessions")
    .select("id, phase_id")
    .eq("data", hoje)
    .maybeSingle();

  if (errSelect) {
    throw new Error(`Erro ao verificar sessão: ${errSelect.message}`);
  }

  const payload: any = {};
  if (p.bias_d1 !== undefined) payload.bias_d1 = p.bias_d1;
  if (p.bias_h1 !== undefined) payload.bias_h1 = p.bias_h1;
  if (p.contexto !== undefined) payload.contexto = p.contexto;
  if (p.niveis !== undefined) payload.niveis = p.niveis;
  if (p.agenda !== undefined) payload.agenda = p.agenda;
  if (p.sono !== undefined) payload.sono = p.sono;
  if (p.tilt !== undefined) payload.tilt = p.tilt;
  if (p.pressao !== undefined) payload.pressao = p.pressao;
  if (p.setup_do_dia !== undefined) payload.setup_do_dia = p.setup_do_dia;
  if (p.contratos_declarados !== undefined) payload.contratos_declarados = p.contratos_declarados;
  if (p.screenshot_path !== undefined) payload.screenshot_path = p.screenshot_path;
  if (p.notas !== undefined) payload.notas = p.notas;

  if (existing?.id) {
    const { error: errUpdate } = await supabase
      .from("copa_sessions")
      .update(payload)
      .eq("id", existing.id);

    if (errUpdate) {
      throw new Error(`Erro ao atualizar pré-sessão: ${errUpdate.message}`);
    }
    return existing.id;
  }

  const { data: inserted, error: errInsert } = await supabase
    .from("copa_sessions")
    .insert({
      data: hoje,
      ...payload,
    })
    .select("id")
    .single();

  if (errInsert) {
    throw new Error(`Erro ao criar pré-sessão: ${errInsert.message}`);
  }

  return inserted.id;
}

/**
 * Fecha a pré-sessão do dia se não houver pendências.
 */
export async function fecharPreSessao(): Promise<void> {
  const sess = await getPreSessaoDeHoje();
  const pendencias = pendenciasDaPreSessao(sess);
  if (pendencias.length > 0) {
    throw new Error(`Pré-sessão incompleta: ${pendencias.join(", ")}`);
  }

  const agoraIso = new Date().toISOString();
  const hoje = getDataSaoPaulo();

  const { error } = await supabase
    .from("copa_sessions")
    .update({ fechada_em: agoraIso })
    .eq("data", hoje);

  if (error) {
    throw new Error(`Erro ao fechar pré-sessão: ${error.message}`);
  }
}

/**
 * Zera fechada_em e registra a reabertura no notas da sessão.
 */
export async function reabrirPreSessao(motivo: string): Promise<void> {
  const hoje = getDataSaoPaulo();
  const { data: session, error: errFetch } = await supabase
    .from("copa_sessions")
    .select("notas")
    .eq("data", hoje)
    .maybeSingle();

  if (errFetch || !session) {
    throw new Error(`Sessão de hoje não encontrada: ${errFetch?.message || ""}`);
  }

  const formatter = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const hhmm = formatter.format(new Date());

  const linhaReabertura = `[REABERTA ${hhmm}] ${motivo.trim()}`;
  const notasAtuais = session.notas ? session.notas.trim() : "";
  const novasNotas = notasAtuais ? `${notasAtuais}\n${linhaReabertura}` : linhaReabertura;

  const { error: errUpdate } = await supabase
    .from("copa_sessions")
    .update({
      fechada_em: null,
      notas: novasNotas,
    })
    .eq("data", hoje);

  if (errUpdate) {
    throw new Error(`Erro ao reabrir pré-sessão: ${errUpdate.message}`);
  }
}
