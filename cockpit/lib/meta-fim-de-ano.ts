/**
 * Plano de fim de ano (02/11/2026, Trade System §2.1): novembro com 3 contratos e meta de
 * R$ 6.000; dezembro sobe a mão em degraus (5, 7, 10 contratos) se novembro cumprir os
 * requisitos, e desce pelas regras de recuo. Funcao pura — testada em scripts/verify.ts.
 */
import { TradeMetricas, formatarBRL, formatarPct, somar, temDesvio } from "./metricas";

export interface TradeMeta extends TradeMetricas {
  data: string; // YYYY-MM-DD da sessao
}

export const META_NOVEMBRO_RS = 6000;
export const CONTRATOS_NOVEMBRO = 3;
export const REQ_DISCIPLINA = 0.9;
export const REQ_TRADES = 50;
/** Dezembro: degrau pelo lucro do mes. Perda maxima por trade na proporcao de hoje (R$ 160 com 3). */
export const DEGRAUS_DEZEMBRO = [
  { contratos: 5, aPartirDe: 0, perdaMaxima: 265 },
  { contratos: 7, aPartirDe: 2000, perdaMaxima: 370 },
  { contratos: 10, aPartirDe: 4000, perdaMaxima: 530 },
];
export const RECUO_DO_PICO_RS = 2000;
export const COLCHAO_MINIMO_RS = 3000;

// Feriados da B3 em nov/dez de 2026 (sem pregao)
const FERIADOS = new Set(["2026-11-02", "2026-11-20", "2026-12-24", "2026-12-25", "2026-12-31"]);

/** Pregoes do mes (dias uteis menos feriados da B3), em YYYY-MM-DD. */
export function pregoesDoMes(ano: number, mes: number): string[] {
  const dias: string[] = [];
  const ultimo = new Date(Date.UTC(ano, mes, 0)).getUTCDate();
  for (let d = 1; d <= ultimo; d++) {
    const dow = new Date(Date.UTC(ano, mes - 1, d)).getUTCDay();
    const iso = `${ano}-${String(mes).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    if (dow !== 0 && dow !== 6 && !FERIADOS.has(iso)) dias.push(iso);
  }
  return dias;
}

const pnl = (t: TradeMetricas) => Number(t.pnl_real ?? 0);

export interface Requisito {
  label: string;
  atual: string;
  ok: boolean;
}

/** Os 4 requisitos para dezembro abrir com 5 contratos, medidos nos trades de novembro. */
export function requisitosDezembro(nov: TradeMeta[]): Requisito[] {
  const n = nov.length;
  const total = somar(nov.map(pnl));
  const noPlano = nov.filter((t) => !temDesvio(t)).length;
  const disc = n ? noPlano / n : 0;
  const maior = n ? Math.max(...nov.map(pnl)) : 0;
  const semMaior = total - Math.max(0, maior);
  return [
    { label: `Resultado de ${formatarBRL(META_NOVEMBRO_RS, false)} ou mais`, atual: formatarBRL(total), ok: total >= META_NOVEMBRO_RS },
    { label: `Disciplina de ${formatarPct(REQ_DISCIPLINA)} ou mais`, atual: n ? formatarPct(disc) : "—", ok: n > 0 && disc >= REQ_DISCIPLINA },
    { label: `${REQ_TRADES} trades ou mais`, atual: String(n), ok: n >= REQ_TRADES },
    { label: "Positivo sem o maior trade", atual: n ? formatarBRL(semMaior) : "—", ok: n > 0 && semMaior > 0 },
  ];
}

/** Degrau de dezembro: lucro do mes, pico, recuo e colchao (lucro de novembro + dezembro). */
export function degrauDezembro(nov: TradeMeta[], dez: TradeMeta[]) {
  const liberado = requisitosDezembro(nov).every((r) => r.ok);
  const lucroNov = somar(nov.map(pnl));
  let acum = 0;
  let pico = 0;
  for (const t of dez) {
    acum += pnl(t);
    pico = Math.max(pico, acum);
  }
  const colchao = lucroNov + acum;
  if (!liberado || colchao <= COLCHAO_MINIMO_RS) {
    return {
      contratos: CONTRATOS_NOVEMBRO, perdaMaxima: 160, lucroDez: acum, colchao, proximo: null as null | { contratos: number; falta: number },
      motivo: !liberado ? "Novembro não cumpriu os requisitos: dezembro segue com 3 contratos" : `Colchão em ${formatarBRL(colchao, false)}: volta para 3 contratos`,
    };
  }
  let i = DEGRAUS_DEZEMBRO.filter((d) => acum >= d.aPartirDe).length - 1;
  const recuou = pico - acum >= RECUO_DO_PICO_RS;
  if (recuou) i = Math.max(0, i - 1);
  const atual = DEGRAUS_DEZEMBRO[i];
  const prox = DEGRAUS_DEZEMBRO[i + 1];
  return {
    contratos: atual.contratos, perdaMaxima: atual.perdaMaxima, lucroDez: acum, colchao,
    proximo: prox ? { contratos: prox.contratos, falta: Math.max(0, prox.aPartirDe - acum) } : null,
    motivo: recuou ? `Recuou ${formatarBRL(pico - acum, false)} do pico de dezembro: desceu um degrau` : `Degrau de ${atual.contratos} contratos`,
  };
}

/** Card "Meta do mês" da Visao Geral. So existe em novembro e dezembro de 2026. */
export function montarMeta(trades: TradeMeta[], anteriores: TradeMeta[], ano: number, mes: number, hojeIso: string) {
  if (ano !== 2026 || (mes !== 11 && mes !== 12)) return null;
  const pregoes = pregoesDoMes(ano, mes);
  const feitos = pregoes.filter((d) => d <= hojeIso).length;
  const restantes = pregoes.length - feitos;
  const total = somar(trades.map(pnl));

  if (mes === 11) {
    const esperado = Math.round((META_NOVEMBRO_RS * feitos) / pregoes.length);
    const diff = total - esperado;
    const falta = Math.max(0, META_NOVEMBRO_RS - total);
    return {
      tipo: "novembro" as const,
      label: "Meta de novembro",
      frase: `${formatarBRL(total)} de ${formatarBRL(META_NOVEMBRO_RS, false)} · ${feitos} de ${pregoes.length} pregões`,
      pct: Math.max(0, Math.min(1, total / META_NOVEMBRO_RS)),
      marcaPct: Math.min(1, esperado / META_NOVEMBRO_RS),
      ritmo: feitos === 0 ? "O mês ainda não começou" : `Esperado até hoje: ${formatarBRL(esperado, false)} · ${diff >= 0 ? "acima" : "abaixo"} em ${formatarBRL(Math.abs(diff), false)}`,
      ritmoOk: diff >= 0,
      faltaTxt: falta === 0 ? "Meta batida" : restantes > 0 ? `Faltam ${formatarBRL(falta, false)} em ${restantes} pregões · ${formatarBRL(Math.ceil(falta / restantes), false)} por pregão` : `Faltaram ${formatarBRL(falta, false)}`,
      mao: `${CONTRATOS_NOVEMBRO} contratos · perda máxima de R$ 160 por trade`,
      requisitos: requisitosDezembro(trades),
    };
  }

  const d = degrauDezembro(anteriores, trades);
  return {
    tipo: "dezembro" as const,
    label: "Escada de dezembro",
    frase: `${d.contratos} contratos · perda máxima de ${formatarBRL(d.perdaMaxima, false)} por trade`,
    pct: d.proximo ? Math.max(0, Math.min(1, d.lucroDez / (d.lucroDez + d.proximo.falta || 1))) : 1,
    marcaPct: null as number | null,
    ritmo: d.motivo,
    ritmoOk: d.contratos > CONTRATOS_NOVEMBRO,
    faltaTxt: d.proximo ? `Próximo degrau (${d.proximo.contratos} contratos) a ${formatarBRL(d.proximo.falta, false)}` : "Degrau máximo",
    mao: `Dezembro ${formatarBRL(d.lucroDez)} · colchão ${formatarBRL(d.colchao)} · recuo: −${formatarBRL(RECUO_DO_PICO_RS, false)} do pico desce um degrau; colchão de ${formatarBRL(COLCHAO_MINIMO_RS, false)} volta a 3`,
    requisitos: requisitosDezembro(anteriores),
  };
}

export type MetaDoMes = NonNullable<ReturnType<typeof montarMeta>>;
