/**
 * Modo demonstracao: as telas de leitura (Visao Geral, Historico, Estrategias) mostram
 * trades ficticios em vez dos do banco. Nada e gravado no Supabase.
 * Liga com ?demo=1 na URL, desliga com ?demo=0 ou pelo aviso no topo da tela.
 */
import type { TradeHistorico } from "./copa-db";
import { FERIADOS_B3 } from "./alertas";

const CHAVE = "cognitive-demo";

export function modoDemo(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const q = new URLSearchParams(window.location.search).get("demo");
    if (q === "1") localStorage.setItem(CHAVE, "1");
    if (q === "0") localStorage.removeItem(CHAVE);
    return localStorage.getItem(CHAVE) === "1";
  } catch {
    return false;
  }
}

export function sairDoDemo() {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    // sem localStorage o demo so vale pela URL
  }
  window.location.href = window.location.pathname;
}

// Gerador fixo (mulberry32): os mesmos trades toda vez que a tela abre
function sorteio(semente: number) {
  let a = semente;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const ESTRATEGIAS = [
  { id: "varrida_barra_10", gatilhos: ["MSS_FVG", "MSS_OB"] },
  { id: "continuidade_tendencia", gatilhos: ["FVG_POS_SWING", "MSS_FVG"] },
  { id: "reversao_htf", gatilhos: ["BPR", "MSS_FVG", "RISK_ENTRY"] },
];
const VALOR_PONTO = 0.2; // R$ por ponto por contrato no WIN
const CONTRATOS = 3;
// Escolhida entre varias para os tres meses parecerem um trader real: acerto perto de
// 50%, resultado positivo e alguns desvios de plano
const SEMENTE = 39595;

function diasDePregao(ano: number, mes: number, ate: string): string[] {
  const dias: string[] = [];
  const ultimo = new Date(Date.UTC(ano, mes, 0)).getUTCDate();
  for (let d = 1; d <= ultimo; d++) {
    const iso = `${ano}-${String(mes).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const semana = new Date(Date.UTC(ano, mes - 1, d)).getUTCDay();
    if (iso > ate) break;
    if (semana !== 0 && semana !== 6 && !FERIADOS_B3.has(iso)) dias.push(iso);
  }
  return dias;
}

/** Trades ficticios fechados do mes, do dia 1 ate `ate` (inclusive), em ordem de saida. */
export function tradesDemoDoMes(ano: number, mes: number, ate: string): TradeHistorico[] {
  const r = sorteio(SEMENTE + ano * 100 + mes);
  const trades: TradeHistorico[] = [];
  for (const dia of diasDePregao(ano, mes, ate)) {
    const quantos = r() < 0.25 ? 0 : r() < 0.7 ? 1 : 2;
    let minuto = -15;
    for (let i = 0; i < quantos; i++) {
      const x = r();
      const est = x < 0.5 ? ESTRATEGIAS[0] : x < 0.8 ? ESTRATEGIAS[1] : ESTRATEGIAS[2];
      minuto = Math.max(minuto + 15, Math.floor(r() * 80));
      if (minuto > 88) break; // entrada so ate 11:28
      const hh = 10 + Math.floor(minuto / 60);
      const mm = minuto % 60;
      const duracao = 8 + Math.floor(r() * 40);
      const venda = r() < 0.45;
      const sinal = venda ? -1 : 1;
      const entrada = Math.round((128000 + r() * 6000) / 5) * 5;
      const risco = Math.round((140 + r() * 160) / 5) * 5;
      const rrPlano = [2, 2.5, 3][Math.floor(r() * 3)];
      const ganhou = r() < 0.52;
      const resultadoR = ganhou ? Math.round((1 + r() * 3.2) * 10) / 10 : -1;
      const pontos = Math.round(resultadoR * risco);
      const desvio = r();
      const custo = desvio < 0.1 ? Math.round(risco * 0.3 * VALOR_PONTO * CONTRATOS) : 0;
      const pnl = Math.round(pontos * VALOR_PONTO * CONTRATOS);
      const score = 65 + Math.floor(r() * 30);
      const utc = (h: number, m: number) => `${dia}T${String(h + 3).padStart(2, "0")}:${String(m).padStart(2, "0")}:00Z`;
      const fim = mm + duracao;
      trades.push({
        id: `demo-${dia}-${i}`,
        data: dia,
        strategy_id: est.id,
        mercado: "WIN",
        direcao: venda ? "VENDA" : "COMPRA",
        janela: hh === 10 ? "PRIME" : "VALIDA",
        status: "FECHADO",
        hora_entrada: utc(hh, mm),
        hora_saida: utc(hh + Math.floor(fim / 60), fim % 60),
        score,
        grade: score >= 80 ? "A+" : "A",
        entrada,
        stop: entrada - sinal * risco,
        alvo: entrada + sinal * Math.round(risco * rrPlano),
        contratos: CONTRATOS,
        rr_planejado: rrPlano,
        saida: entrada + sinal * pontos,
        motivo_saida: ganhou ? (resultadoR >= rrPlano ? "ALVO" : "MANUAL") : "STOP",
        pontos_real: pontos,
        pnl_real: pnl,
        pnl_plano: pnl + custo,
        respeitou_plano: custo === 0,
        antecipou_stop: custo > 0 && desvio < 0.04,
        parcial_emocional: custo > 0 && desvio >= 0.04 && desvio < 0.07,
        mudou_alvo: custo > 0 && desvio >= 0.07,
        notas: null,
        gatilho: est.gatilhos[Math.floor(r() * est.gatilhos.length)] as TradeHistorico["gatilho"],
        contexto_1h: (["CONTINUACAO", "REVERSAO", "LATERAL"] as const)[Math.floor(r() * 3)],
        setup_c_modo: est.id === "varrida_barra_10" ? (r() < 0.6 ? "C1" : "C2") : null,
      });
    }
  }
  return trades;
}

/** Julho, agosto e setembro de 2026 ate `hoje`, do mais recente para o mais antigo. */
export function tradesDemo(hoje: string): TradeHistorico[] {
  const [ano, mes] = hoje.split("-").map(Number);
  const todos: TradeHistorico[] = [];
  for (let k = 2; k >= 0; k--) {
    const m = mes - k;
    const a = m < 1 ? ano - 1 : ano;
    const mm = m < 1 ? m + 12 : m;
    todos.push(...tradesDemoDoMes(a, mm, hoje));
  }
  return todos.sort((x, y) => y.hora_entrada.localeCompare(x.hora_entrada));
}
