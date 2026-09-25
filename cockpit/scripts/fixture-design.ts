import type { TradeVG } from "../lib/visao-geral";

// Os 16 trades de exemplo de design/v2/Main.dc.html. Usado so em testes e na
// previa local de layout — nunca na tela real.

const ID: Record<string, string> = { A: "reversao_htf", B: "continuidade_tendencia", C: "varrida_barra_10" };

const BASE: Array<[number, string, string, number, number, string, string, string, number]> = [
  [1, "10:07", "C", 210, 2.4, "MSS_FVG", "REVERSAO", "C1", 0], [2, "10:22", "A", 180, -1, "MSS_FVG", "REVERSAO", "", 0],
  [3, "10:41", "B", 150, 1.6, "FVG_POS_SWING", "CONTINUACAO", "", 0], [4, "10:18", "C", 230, -1, "MSS_OB", "LATERAL", "C2", 0],
  [8, "10:33", "C", 200, 4.1, "MSS_FVG", "REVERSAO", "C1", 0], [9, "11:05", "A", 260, -1, "BPR", "REVERSAO", "", 90],
  [10, "10:12", "B", 140, 0.8, "MSS_FVG", "CONTINUACAO", "", 0], [11, "10:47", "C", 190, 1.8, "MSS_FVG", "CONTINUACAO", "C2", 0],
  [15, "10:26", "C", 220, 2.9, "MSS_OB", "REVERSAO", "C1", 0], [16, "11:18", "A", 300, -1, "RISK_ENTRY", "LATERAL", "", 120],
  [17, "10:09", "B", 160, 2.0, "FVG_POS_SWING", "CONTINUACAO", "", 0], [18, "10:38", "C", 210, -1, "MSS_FVG", "LATERAL", "C2", 0],
  [22, "10:15", "C", 180, 5.2, "MSS_FVG", "REVERSAO", "C1", 0], [23, "10:52", "A", 240, 1.3, "BPR", "REVERSAO", "", 0],
  [24, "10:29", "C", 200, -1, "MSS_OB", "CONTINUACAO", "C2", 150], [25, "10:03", "B", 170, -1, "MSS_FVG", "CONTINUACAO", "", 0],
];

export const TRADES_DESIGN: TradeVG[] = BASE.map(([d, h, e, risco, r, gat, ctx, modo, custo]) => {
  const [hh, mm] = h.split(":").map(Number);
  const dia = String(d).padStart(2, "0");
  const pnl = Math.round(r * risco * 0.6);
  return {
    data: `2026-09-${dia}`, strategy_id: ID[e], direcao: "COMPRA", entrada: 100000, stop: 100000 - risco,
    pontos_real: r * risco, pnl_real: pnl, pnl_plano: pnl + custo,
    hora_entrada: `2026-09-${dia}T${String(hh + 3).padStart(2, "0")}:${String(mm).padStart(2, "0")}:00Z`,
    gatilho: gat, contexto_1h: ctx, setup_c_modo: modo || null,
    respeitou_plano: custo === 0, antecipou_stop: custo === 90, mudou_alvo: custo === 120, parcial_emocional: custo === 150,
  };
});
