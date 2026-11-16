/**
 * Contas (SPEC_CONTAS.md): a prova da mesa e a conta real sao perfis separados. Cada sessao
 * pertence a uma conta, e toda tela e o gate leem so a conta ativa.
 *
 * Sem a migracao (migration_contas.sql) ou sem sessao, o cockpit funciona como antes: uma
 * conta real "padrao", sem id, que nao filtra nada.
 */
import { supabase } from "./supabase";
import { modoDemo } from "./demo";
import { MAX_CONTRATOS, MAX_OPERACOES_DIA, MAX_PERDAS_DIA, MAX_RISCO_TRADE_RS } from "./gate";

export type TipoConta = "REAL" | "PROVA";
export type StatusConta = "ATIVA" | "APROVADA" | "ELIMINADA" | "ENCERRADA";

export interface Conta {
  id: string | null;
  nome: string;
  tipo: TipoConta;
  status: StatusConta;
  max_contratos: number;
  max_risco_trade_rs: number;
  max_perdas_seguidas: number;
  max_operacoes_dia: number;
  // regras da mesa: null na conta real
  limite_perda_diaria_rs: number | null;
  limite_perda_total_rs: number | null;
  meta_rs: number | null;
  min_pregoes: number | null;
  teto_dia_pct: number | null; // 0.5 = um pregao conta no maximo 50% da meta
  pts_minimos_validos: number | null; // operacao com esse tanto de pontos ou menos nao conta
}

/** Os limites que o gate ja usava antes das contas. */
export const CONTA_REAL_PADRAO: Conta = {
  id: null,
  nome: "Conta real",
  tipo: "REAL",
  status: "ATIVA",
  max_contratos: MAX_CONTRATOS,
  max_risco_trade_rs: MAX_RISCO_TRADE_RS,
  max_perdas_seguidas: MAX_PERDAS_DIA,
  max_operacoes_dia: MAX_OPERACOES_DIA,
  limite_perda_diaria_rs: null,
  limite_perda_total_rs: null,
  meta_rs: null,
  min_pregoes: null,
  teto_dia_pct: null,
  pts_minimos_validos: null,
};

/**
 * Prova Zero7, plano Pleno (regulamento de 14/10/2026 + tela da compra de 11/11/2026).
 * Perda total R$ 6.500 e o valor da compra; o regulamento traz R$ 4.997 para o Pleno.
 * Os mesmos valores vao no INSERT de migration_contas.sql.
 */
export const CONTA_PROVA_ZERO7: Conta = {
  id: null,
  nome: "Prova Zero7 (Pleno)",
  tipo: "PROVA",
  status: "ATIVA",
  max_contratos: 10,
  max_risco_trade_rs: 530,
  // 16/11/2026: 2 stops encerram e 3 trades no dia (eram 3 e 5). Ver REGRAS_DA_HORA_PROVA.
  max_perdas_seguidas: 2,
  max_operacoes_dia: 3,
  limite_perda_diaria_rs: 1247,
  limite_perda_total_rs: 6500,
  meta_rs: 4997,
  min_pregoes: 5,
  teto_dia_pct: 0.5,
  pts_minimos_validos: 10,
};

/** Contas do modo demonstracao: nada disso existe no banco. */
export const CONTAS_DEMO: Conta[] = [
  { ...CONTA_REAL_PADRAO, id: "demo-real" },
  { ...CONTA_PROVA_ZERO7, id: "demo-prova" },
];

const CHAVE = "cognitive-conta";

let ativa: Conta = CONTA_REAL_PADRAO;

export function getContaAtiva(): Conta {
  return ativa;
}

export function definirContaAtiva(c: Conta): void {
  ativa = c;
}

/**
 * Id da conta ativa para filtrar o banco. Null = nao filtra (banco sem a migracao, ou conta
 * do demo, que nao existe no banco).
 */
export function contaAtivaId(): string | null {
  const id = ativa.id;
  return id && !id.startsWith("demo-") ? id : null;
}

const num = (x: unknown): number | null => (x === null || x === undefined ? null : Number(x));

function daLinha(r: Record<string, unknown>): Conta {
  return {
    id: String(r.id),
    nome: String(r.nome),
    tipo: r.tipo === "PROVA" ? "PROVA" : "REAL",
    status: (r.status as StatusConta) ?? "ATIVA",
    max_contratos: Number(r.max_contratos),
    max_risco_trade_rs: Number(r.max_risco_trade_rs),
    max_perdas_seguidas: Number(r.max_perdas_seguidas ?? MAX_PERDAS_DIA),
    max_operacoes_dia: Number(r.max_operacoes_dia ?? MAX_OPERACOES_DIA),
    limite_perda_diaria_rs: num(r.limite_perda_diaria_rs),
    limite_perda_total_rs: num(r.limite_perda_total_rs),
    meta_rs: num(r.meta_rs),
    min_pregoes: num(r.min_pregoes),
    teto_dia_pct: num(r.teto_dia_pct),
    pts_minimos_validos: num(r.pts_minimos_validos),
  };
}

/** Contas do usuario, a real primeiro. Sem a tabela (migracao nao rodada): so a real padrao. */
export async function carregarContas(): Promise<Conta[]> {
  const { data, error } = await supabase.from("copa_contas").select("*").order("criada_em", { ascending: true });
  // O demo so troca os trades das telas de leitura; pre-sessao e checklist continuam no banco.
  // Por isso ele usa as contas de verdade quando existem, e as ficticias so sem banco ou sem login.
  if (error || !data || data.length === 0) return modoDemo() ? CONTAS_DEMO : [CONTA_REAL_PADRAO];
  return data.map(daLinha).sort((a, b) => (a.tipo === b.tipo ? 0 : a.tipo === "REAL" ? -1 : 1));
}

/** A conta que o operador usou por ultimo; sem escolha, a real. */
export function escolherConta(contas: Conta[]): Conta {
  let salva: string | null = null;
  try {
    salva = localStorage.getItem(CHAVE);
  } catch {
    // sem localStorage abre na conta real
  }
  return contas.find((c) => c.id === salva) ?? contas.find((c) => c.tipo === "REAL") ?? contas[0] ?? CONTA_REAL_PADRAO;
}

export function lembrarConta(id: string | null): void {
  try {
    if (id) localStorage.setItem(CHAVE, id);
    else localStorage.removeItem(CHAVE);
  } catch {
    // sem localStorage a escolha vale so ate recarregar
  }
}
