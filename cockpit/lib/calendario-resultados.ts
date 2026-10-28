/**
 * Modelo do Calendário de Resultados: transforma os trades do mês em grade de pregão
 * (segunda a sexta) com acumulado por semana e total do mês.
 * Função pura, sem Supabase — testada em scripts/verify.ts.
 * Fonte: cockpit/SPEC_CALENDARIO.md.
 */

import { FERIADOS_B3 } from "./alertas";
import {
  TradeMetricas,
  rDoTrade,
  somar,
} from "./metricas";

export interface DiaCal {
  iso: string;
  dia: number;
  doMes: boolean;
  futuro: boolean;
  feriado: boolean;
  hoje: boolean;
  trades: number;
  ganhos: number;
  perdas: number;
  pnl: number;
  r: number;
}

export interface SemanaCal {
  n: number;
  dias: DiaCal[];
  trades: number;
  ganhos: number;
  perdas: number;
  pnl: number;
  r: number;
  wr: number | null;
  pf: number | null;
}

export interface CalendarioMes {
  semanas: SemanaCal[];
  total: {
    trades: number;
    ganhos: number;
    perdas: number;
    pnl: number;
    r: number;
    wr: number | null;
    pf: number | null;
  };
  semanasPositivas: number;
  semanasComTrade: number;
}

export type TradeEntradaCal = TradeMetricas & { data?: string };

export function montarCalendarioMes(
  trades: TradeEntradaCal[],
  ano: number,
  mes: number,
  hojeIso: string
): CalendarioMes {
  // Mapa de trades agrupados por data (apenas para trades com data)
  const porDia: Record<string, TradeEntradaCal[]> = {};
  for (const t of trades) {
    const dataIso = t.data ?? t.hora_entrada?.slice(0, 10);
    if (!dataIso) continue;
    if (!porDia[dataIso]) porDia[dataIso] = [];
    porDia[dataIso].push(t);
  }

  const primeiro = new Date(Date.UTC(ano, mes - 1, 1));
  const desloc = (primeiro.getUTCDay() + 6) % 7; // 0 = segunda
  // segunda-feira da semana do dia 1 (se o dia 1 cair no fim de semana, começa na segunda seguinte)
  const seg =
    desloc <= 4
      ? new Date(Date.UTC(ano, mes - 1, 1 - desloc))
      : new Date(Date.UTC(ano, mes - 1, 1 + (7 - desloc)));
  const ultimo = new Date(Date.UTC(ano, mes, 0));

  const semanas: SemanaCal[] = [];
  let n = 1;

  for (
    let semana = new Date(seg);
    semana <= ultimo;
    semana = new Date(semana.getTime() + 7 * 864e5), n++
  ) {
    const dias: DiaCal[] = [];
    let semanaGanhosGross = 0;
    let semanaPerdasGross = 0;

    for (let c = 0; c < 5; c++) {
      const d = new Date(semana.getTime() + c * 864e5);
      const iso = d.toISOString().slice(0, 10);
      const doMes = d.getUTCMonth() === mes - 1;
      const futuro = iso > hojeIso;
      const feriado = FERIADOS_B3.has(iso);
      const hoje = iso === hojeIso;
      const diaNum = d.getUTCDate();

      if (!doMes) {
        dias.push({
          iso,
          dia: diaNum,
          doMes: false,
          futuro,
          feriado,
          hoje,
          trades: 0,
          ganhos: 0,
          perdas: 0,
          pnl: 0,
          r: 0,
        });
        continue;
      }

      const ts = porDia[iso] ?? [];
      let diaPnl = 0;
      let diaR = 0;
      let diaGanhos = 0;
      let diaPerdas = 0;

      for (const t of ts) {
        const pnl = Number(t.pnl_real ?? 0);
        const r = rDoTrade(t);

        diaPnl += pnl;
        if (r !== null) {
          diaR += r;
        }

        if (pnl > 0) {
          diaGanhos++;
          semanaGanhosGross += pnl;
        } else if (pnl < 0) {
          diaPerdas++;
          semanaPerdasGross += Math.abs(pnl);
        }
      }

      dias.push({
        iso,
        dia: diaNum,
        doMes: true,
        futuro,
        feriado,
        hoje,
        trades: ts.length,
        ganhos: diaGanhos,
        perdas: diaPerdas,
        pnl: diaPnl,
        r: diaR,
      });
    }

    const semanaTrades = somar(dias.map((d) => d.trades));
    const semanaGanhos = somar(dias.map((d) => d.ganhos));
    const semanaPerdas = somar(dias.map((d) => d.perdas));
    const semanaPnl = somar(dias.map((d) => d.pnl));
    const semanaR = somar(dias.map((d) => d.r));

    const wr = semanaTrades > 0 ? semanaGanhos / semanaTrades : null;
    const pf = semanaPerdasGross > 0 ? semanaGanhosGross / semanaPerdasGross : null;

    semanas.push({
      n,
      dias,
      trades: semanaTrades,
      ganhos: semanaGanhos,
      perdas: semanaPerdas,
      pnl: semanaPnl,
      r: semanaR,
      wr,
      pf,
    });
  }

  const totalTrades = somar(semanas.map((s) => s.trades));
  const totalGanhos = somar(semanas.map((s) => s.ganhos));
  const totalPerdas = somar(semanas.map((s) => s.perdas));
  const totalPnl = somar(semanas.map((s) => s.pnl));
  const totalR = somar(semanas.map((s) => s.r));

  let totalGanhosGross = 0;
  let totalPerdasGross = 0;
  for (const s of semanas) {
    for (const d of s.dias) {
      if (!d.doMes) continue;
      const ts = porDia[d.iso] ?? [];
      for (const t of ts) {
        const pnl = Number(t.pnl_real ?? 0);
        if (pnl > 0) totalGanhosGross += pnl;
        else if (pnl < 0) totalPerdasGross += Math.abs(pnl);
      }
    }
  }

  const totalWr = totalTrades > 0 ? totalGanhos / totalTrades : null;
  const totalPf = totalPerdasGross > 0 ? totalGanhosGross / totalPerdasGross : null;

  const semanasPositivas = semanas.filter((s) => s.pnl > 0).length;
  const semanasComTrade = semanas.filter((s) => s.trades > 0).length;

  return {
    semanas,
    total: {
      trades: totalTrades,
      ganhos: totalGanhos,
      perdas: totalPerdas,
      pnl: totalPnl,
      r: totalR,
      wr: totalWr,
      pf: totalPf,
    },
    semanasPositivas,
    semanasComTrade,
  };
}
