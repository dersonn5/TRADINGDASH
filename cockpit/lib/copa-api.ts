import { DEFAULT_STRATEGIES } from "@/data/strategies";

// Cliente da API da Copa BTG (FastAPI em :8010 local ou rota serverless na Vercel)
const BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? ""
    : "http://localhost:8010");

export class CopaError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail || `Erro na API da Copa (${status})`);
    this.name = "CopaError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `Erro na requisição (${res.status})`;
    try {
      const errBody = await res.json();
      if (errBody && errBody.detail) {
        detail = typeof errBody.detail === "string" ? errBody.detail : JSON.stringify(errBody.detail);
      }
    } catch {
      // Ignora erro de parse e mantém detail padrão
    }
    throw new CopaError(res.status, detail);
  }

  return (await res.json()) as T;
}

// ==========================================
// TIPOS TS
// ==========================================

export type Mercado = "WIN" | "WDO";
export type Direcao = "COMPRA" | "VENDA";
export type Contexto = "TENDENCIA" | "RANGE" | "INDEFINIDO";
export type Bias = "COMPRA" | "VENDA" | "INDEFINIDO";
export type Impacto = "ALTO" | "MEDIO" | "BAIXO";
export type Modo = "NORMAL" | "DEFENSIVO";
export type ItemTipo = "KILL" | "PONTO";
export type TradeStatus = "ABERTO" | "FECHADO";
export type MotivoSaida = "ALVO" | "STOP" | "MANUAL";
export type DesfechoPlano = "BATEU_ALVO" | "BATEU_STOP" | "NAO_SEI";
export type Ambiente = "FAVORAVEL" | "NEUTRA" | "DESFAVORAVEL";

export interface NivelPreco {
  label: string;
  preco: number;
}

export interface AgendaEvento {
  evento: string;
  horario: string;
  impacto: Impacto;
}

export interface HorarioJanela {
  inicio: string;
  fim: string;
}

export interface CopaConfig {
  banca_inicial?: number;
  meta_dia_padrao?: number;
  limite_perda_dia?: number;
  max_trades_dia?: number;
  max_perdas_seguidas?: number;
  cooldown_min?: number;
  bloquear_apos_meta?: boolean;
  horarios_validos?: HorarioJanela[];
  exposicao_maxima_contratos?: number;
  fator_perda_pos_descarte?: number;
  [key: string]: any;
}

export interface ChecklistItem {
  id: string;
  tipo: ItemTipo;
  peso: number;
  label: string;
  ajuda: string;
}

export interface RegraAmbiente {
  campo: string;
  op: string;
  valor: any;
  efeito: Ambiente;
  motivo: string;
}

export interface Strategy {
  id: string;
  ordem?: number;
  nome: string;
  mercado: Mercado[];
  descricao: string;
  score_minimo: number;
  ambiente_favoravel: string[];
  ambiente_desfavoravel: string[];
  horarios_validos: HorarioJanela[];
  regras_ambiente: RegraAmbiente[];
  checklist: ChecklistItem[];
  calibracao?: {
    status?: string;
    observacao?: string;
    atualizado_em?: string;
    [key: string]: any;
  };
  [key: string]: any;
}

export interface SessionDay {
  data: string;
  bias_d1: Bias;
  bias_h1: Bias;
  contexto: Contexto;
  niveis: NivelPreco[];
  agenda: AgendaEvento[];
  sono: number;
  tilt: number;
  pressao: number;
  meta_dia: number;
  limite_perda_dia: number;
  max_trades_dia: number;
  modo: Modo;
  notas: string;
  criado_em?: string;
  fase_id?: string | null;
}

export type SessionDayPayload = Omit<SessionDay, "criado_em">;

export interface GateBreakers {
  pre_sessao_ok: boolean;
  dentro_horario: boolean;
  pnl_dia: number;
  limite_perda_dia: number;
  limite_perda_dia_efetivo?: number;
  trades_dia: number;
  max_trades_dia: number;
  perdas_seguidas: number;
  max_perdas_seguidas: number;
  cooldown_ate: string | null;
  trade_aberto_id: number | null;
  modo: Modo;
  bonus_score_defensivo: number;
  mulligan_disponivel?: boolean;
  modo_forcado_por_mulligan?: boolean;
}

export interface GateResult {
  liberado: boolean;
  motivos: string[];
  avisos: string[];
  breakers: GateBreakers;
}

export interface StrategyRanking {
  strategy_id: string;
  nome: string;
  ambiente: Ambiente;
  motivos: string[];
}

export interface Trade {
  id: number;
  data: string;
  strategy_id: string;
  mercado: Mercado;
  direcao: Direcao;
  checklist: Record<string, boolean>;
  score: number;
  grade: string;
  entrada: number;
  stop: number;
  alvo: number;
  contratos: number;
  rr_planejado: number;
  status: TradeStatus;
  saida?: number | null;
  motivo_saida?: MotivoSaida | null;
  desfecho_plano?: DesfechoPlano | null;
  pnl_real?: number | null;
  pnl_plano?: number | null;
  pontos_real?: number | null;
  respeitou_plano?: number | null;
  antecipou_stop?: number | null;
  parcial_emocional?: number | null;
  mudou_alvo?: number | null;
  notas: string;
  screenshot_path?: string | null;
  criado_em: string;
  fechado_em?: string | null;
}

export interface CreateTradePayload {
  data: string;
  strategy_id: string;
  mercado: Mercado;
  direcao: Direcao;
  checklist: Record<string, boolean>;
  entrada: number;
  stop: number;
  alvo: number;
  contratos: number;
  notas?: string;
  agora?: string;
}

export interface CloseTradePayload {
  saida: number;
  motivo_saida: MotivoSaida;
  desfecho_plano?: DesfechoPlano | null;
  respeitou_plano: number;
  antecipou_stop: number;
  parcial_emocional: number;
  mudou_alvo: number;
  notas?: string;
}

export interface StatsGeral {
  trades: number;
  winrate: number;
  profit_factor: number;
  expectancia: number;
  pnl_total: number;
  max_drawdown: number;
  banca_atual: number;
  meta_copa: number;
  falta_para_meta: number;
}

export interface StatsPorItem {
  strategy_id: string;
  item_id: string;
  label: string;
  tipo: ItemTipo;
  n_marcado: number;
  winrate_marcado: number;
  exp_marcado: number;
  n_nao: number;
  winrate_nao: number;
  exp_nao: number;
  delta_winrate: number;
  amostra_baixa: boolean;
}

export interface StatsPorEstrategia {
  strategy_id: string;
  nome: string;
  n: number;
  winrate: number;
  expectancia: number;
  pnl: number;
}

export interface StatsPorGrade {
  grade: string;
  n: number;
  winrate: number;
  expectancia: number;
  pnl: number;
}

export interface StatsPorHora {
  hora: string;
  n: number;
  winrate: number;
  pnl: number;
}

export interface StatsPorDiaSemana {
  dia: string;
  n: number;
  winrate: number;
  pnl: number;
}

export interface StatsDisciplina {
  trades_com_desvio: number;
  custo_total: number;
  por_flag: Array<{ flag: string; n: number; custo: number }>;
}

export interface CopaStats {
  geral: StatsGeral;
  equity: Array<{ t: string; balance: number }>;
  por_estrategia: StatsPorEstrategia[];
  por_grade: StatsPorGrade[];
  por_item: StatsPorItem[];
  por_hora: StatsPorHora[];
  por_dia_semana: StatsPorDiaSemana[];
  disciplina: StatsDisciplina;
}

export interface DiaFase {
  data: string;
  pnl: number;
  trades: number;
  contratos: number;
  descartado: boolean;
}

export interface MulliganState {
  disponivel: boolean;
  consumido_por: string | null;
  motivo: string;
}

export interface PlacarFaseResult {
  fase: {
    id: string;
    nome: string;
    data_inicio: string;
    data_fim: string;
    dias: number;
    tem_descarte: boolean;
  } | null;
  dias?: DiaFase[];
  dias_operados?: number;
  dias_restantes?: number;
  placar_bruto?: number;
  placar_efetivo?: number;
  pior_dia?: { data: string; pnl: number } | null;
  mulligan?: MulliganState;
  contratos_total?: number;
  reais_por_contrato?: number;
}

// ==========================================
// CLIENTE API COPA
// ==========================================

export const copaApi = {
  getConfig: () => request<CopaConfig>("/api/copa/config"),
  updateConfig: (payload: Partial<CopaConfig>) =>
    request<CopaConfig>("/api/copa/config", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  getStrategies: async () => {
    try {
      return await request<Strategy[]>("/api/copa/strategies");
    } catch {
      return DEFAULT_STRATEGIES;
    }
  },

  getSession: async (data: string) => {
    try {
      return await request<SessionDay | null>(`/api/copa/session/${data}`);
    } catch {
      return null;
    }
  },
  saveSession: (data: string, payload: SessionDayPayload) =>
    request<SessionDay>(`/api/copa/session/${data}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  getGate: async (data: string, agora?: string) => {
    try {
      const params = new URLSearchParams({ data });
      if (agora) params.append("agora", agora);
      return await request<GateResult>(`/api/copa/gate?${params.toString()}`);
    } catch {
      return {
        liberado: true,
        motivos: ["Playbook Anderson ativo"],
        avisos: [],
        breakers: {
          pre_sessao_ok: true,
          dentro_horario: true,
          pnl_dia: 0,
          limite_perda_dia: 300,
          trades_dia: 0,
          max_trades_dia: 3,
          perdas_seguidas: 0,
          max_perdas_seguidas: 2,
          cooldown_ate: null,
          trade_aberto_id: null,
          modo: "NORMAL" as Modo,
          bonus_score_defensivo: 0,
        },
      };
    }
  },

  getRanking: async (data: string) => {
    try {
      return await request<StrategyRanking[]>(`/api/copa/ranking?data=${data}`);
    } catch {
      return [
        {
          strategy_id: "playbook_anderson",
          nome: "Playbook Anderson",
          ambiente: "FAVORAVEL" as Ambiente,
          motivos: ["Array HTF não-mitigado mapeado", "Liquidez de transporte identificada"],
        },
      ];
    }
  },

  createTrade: (payload: CreateTradePayload) =>
    request<Trade>("/api/copa/trades", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listTrades: (params?: { status?: string; data?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.data) query.append("data", params.data);
    const qs = query.toString();
    return request<Trade[]>(`/api/copa/trades${qs ? `?${qs}` : ""}`);
  },

  closeTrade: (id: number, payload: CloseTradePayload) =>
    request<Trade>(`/api/copa/trades/${id}/fechar`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteTrade: (id: number) =>
    request<{ ok: boolean }>(`/api/copa/trades/${id}`, {
      method: "DELETE",
    }),

  getStats: () => request<CopaStats>("/api/copa/stats"),

  getFase: (data: string) => request<PlacarFaseResult>(`/api/copa/fase?data=${data}`),

  getExportUrl: () => `${BASE}/api/copa/export`,
};
