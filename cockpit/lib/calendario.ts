/**
 * Calendario economico automatico (EUA). Fonte: ForexFactory, feed semanal gratuito.
 * Converte o feed para a agenda da pre-sessao. Logica pura — testada em verify.ts.
 * Spec: cockpit/SPEC_ALERTAS_VOZ.md §4.
 */
import type { EventoAgenda } from "./alertas";

export const FONTE_CALENDARIO = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";

export interface EventoFeed {
  title: string;
  country: string;
  date: string; // ISO com fuso, ex. 2026-09-21T11:00:00-04:00
  impact: string; // High | Medium | Low | Holiday
  forecast?: string;
  previous?: string;
}

export interface EventoCalendario extends EventoAgenda {
  impacto: "ALTO" | "MEDIO";
  titulo_original: string;
}

// Nome falado em portugues. O que nao estiver aqui fica com o titulo original.
const NOMES: Record<string, string> = {
  "Non-Farm Employment Change": "Payroll",
  "Unemployment Rate": "taxa de desemprego americana",
  "CPI m/m": "CPI, inflação ao consumidor",
  "CPI y/y": "CPI, inflação ao consumidor",
  "Core CPI m/m": "núcleo do CPI",
  "PPI m/m": "PPI, inflação ao produtor",
  "Core PPI m/m": "núcleo do PPI",
  "Core PCE Price Index m/m": "núcleo do PCE",
  "Retail Sales m/m": "vendas no varejo",
  "Core Retail Sales m/m": "núcleo das vendas no varejo",
  "Unemployment Claims": "pedidos de seguro-desemprego",
  "Advance GDP q/q": "PIB americano",
  "Prelim GDP q/q": "PIB americano",
  "Final GDP q/q": "PIB americano",
  "ISM Manufacturing PMI": "ISM da indústria",
  "ISM Services PMI": "ISM de serviços",
  "JOLTS Job Openings": "JOLTS, vagas de emprego",
  "ADP Non-Farm Employment Change": "ADP, emprego privado",
  "Federal Funds Rate": "decisão de juros do Fed",
  "FOMC Statement": "decisão de juros do Fed",
  "FOMC Press Conference": "entrevista do Powell",
  "Fed Chair Powell Speaks": "fala do Powell",
  "Prelim UoM Consumer Sentiment": "confiança do consumidor de Michigan",
  "Crude Oil Inventories": "estoques de petróleo",
  "Revised UoM Consumer Sentiment": "confiança do consumidor de Michigan",
  "Prelim UoM Inflation Expectations": "expectativa de inflação de Michigan",
  "Revised UoM Inflation Expectations": "expectativa de inflação de Michigan",
  "President Trump Speaks": "fala do Trump",
  "Fed Chair Powell Testifies": "depoimento do Powell",
  "FOMC Meeting Minutes": "ata do Fed",
  "Average Hourly Earnings m/m": "salário médio por hora",
  "Core PCE Price Index y/y": "núcleo do PCE",
  "Durable Goods Orders m/m": "encomendas de bens duráveis",
  "Core Durable Goods Orders m/m": "núcleo das encomendas de bens duráveis",
  "Empire State Manufacturing Index": "índice Empire State",
  "Philly Fed Manufacturing Index": "índice do Fed da Filadélfia",
  "CB Consumer Confidence": "confiança do consumidor",
  "Flash Manufacturing PMI": "PMI preliminar da indústria",
  "Flash Services PMI": "PMI preliminar de serviços",
  "New Home Sales": "vendas de casas novas",
  "Existing Home Sales": "vendas de casas usadas",
  "Pending Home Sales m/m": "vendas pendentes de casas",
  "Trade Balance": "balança comercial americana",
};

export function nomeEmPortugues(titulo: string): string {
  return NOMES[titulo] ?? titulo;
}

function dataHoraSP(iso: string): { data: string; hora: string } | null {
  const instante = new Date(iso);
  if (isNaN(instante.getTime())) return null;
  const partes = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false,
  }).formatToParts(instante);
  const v = (t: string) => partes.find((p) => p.type === t)?.value ?? "";
  return { data: `${v("year")}-${v("month")}-${v("day")}`, hora: `${v("hour") === "24" ? "00" : v("hour")}:${v("minute")}` };
}

/** Eventos dos EUA de impacto Alto e Medio no dia `hojeISO` (Sao Paulo), ordenados por horario. */
export function converterFeed(feed: EventoFeed[], hojeISO: string): EventoCalendario[] {
  const vistos = new Set<string>();
  return feed
    .filter((e) => e.country === "USD" && (e.impact === "High" || e.impact === "Medium"))
    .map((e) => {
      const sp = dataHoraSP(e.date);
      if (!sp || sp.data !== hojeISO) return null;
      return {
        evento: nomeEmPortugues(e.title),
        horario: sp.hora,
        impacto: e.impact === "High" ? ("ALTO" as const) : ("MEDIO" as const),
        titulo_original: e.title,
      };
    })
    .filter((e): e is EventoCalendario => {
      if (!e) return false;
      // CPI m/m e CPI y/y viram o mesmo nome no mesmo horario: fica um so
      const chave = `${e.horario}-${e.evento}`;
      if (vistos.has(chave)) return false;
      vistos.add(chave);
      return true;
    })
    .sort((a, b) => a.horario.localeCompare(b.horario));
}

/** Junta os eventos importados na agenda sem duplicar (mesmo horario e mesmo nome). */
export function mesclarAgenda(agenda: EventoAgenda[], novos: EventoAgenda[]): EventoAgenda[] {
  const existe = new Set(agenda.map((e) => `${e.horario}-${e.evento.trim().toLowerCase()}`));
  const extras = novos
    .filter((e) => !existe.has(`${e.horario}-${e.evento.trim().toLowerCase()}`))
    .map((e) => ({ evento: e.evento, horario: e.horario, impacto: e.impacto }));
  return [...agenda, ...extras].sort((a, b) => a.horario.localeCompare(b.horario));
}
