/**
 * Alertas de voz do pregao: o que falar e quando. Logica pura, sem navegador.
 * Fonte: cockpit/SPEC_ALERTAS_VOZ.md §3. Testado em scripts/verify.ts.
 */

export type GrupoAlerta = "rotina" | "noticia";

export interface Alerta {
  id: string;
  hora: string; // "HH:MM" em America/Sao_Paulo
  texto: string;
  // Pedacos de fala, cada um com seu audio da voz Dora. Juntos com espaco = texto.
  segmentos: string[];
  grupo: GrupoAlerta;
  ordem: number; // desempate quando dois alertas caem no mesmo minuto
}

export interface EventoAgenda {
  evento: string;
  horario: string; // "HH:MM"
  impacto: "ALTO" | "MEDIO" | "BAIXO";
}

// Feriados da B3 em 2026 (sem pregao). Conferido contra o calendario de feriados
// nacionais + dias sem negociacao da B3 (24/12 e 31/12). Rever todo ano.
export const FERIADOS_B3 = new Set([
  "2026-01-01", "2026-02-16", "2026-02-17", "2026-04-03", "2026-04-21", "2026-05-01",
  "2026-06-04", "2026-09-07", "2026-10-12", "2026-11-02", "2026-11-20", "2026-12-24",
  "2026-12-25", "2026-12-31",
]);

export function ehDiaDePregao(dataISO: string): boolean {
  const [a, m, d] = dataISO.split("-").map(Number);
  const dia = new Date(Date.UTC(a, m - 1, d)).getUTCDay();
  return dia !== 0 && dia !== 6 && !FERIADOS_B3.has(dataISO);
}

function horaEm(fuso: string, instante: Date): string {
  const partes = new Intl.DateTimeFormat("en-GB", { timeZone: fuso, hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(instante);
  const h = partes.find((p) => p.type === "hour")?.value ?? "00";
  const m = partes.find((p) => p.type === "minute")?.value ?? "00";
  return `${h === "24" ? "00" : h}:${m}`;
}

/** 09:30 em Nova York convertido para Sao Paulo. 10:30 no horario de verao dos EUA, 11:30 fora dele. */
export function aberturaNY(dataISO: string): string {
  const [a, m, d] = dataISO.split("-").map(Number);
  for (const offset of [4, 5]) {
    const instante = new Date(Date.UTC(a, m - 1, d, 9 + offset, 30));
    if (horaEm("America/New_York", instante) === "09:30") return horaEm("America/Sao_Paulo", instante);
  }
  return "10:30";
}

export function somarMinutos(hora: string, minutos: number): string {
  const [h, m] = hora.split(":").map(Number);
  const total = (((h * 60 + m + minutos) % 1440) + 1440) % 1440;
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

const UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta"];

function numeroPorExtenso(n: number, feminino = false): string {
  if (feminino && n === 1) return "uma";
  if (feminino && n === 2) return "duas";
  if (n < 20) return UNIDADES[n];
  const dez = DEZENAS[Math.floor(n / 10)];
  const uni = n % 10;
  return uni ? `${dez} e ${numeroPorExtenso(uni, feminino)}` : dez;
}

/** "10:30" → "dez e meia", "09:45" → "nove e quarenta e cinco", "12:00" → "meio-dia". */
export function horaFalada(hora: string): string {
  const [h, m] = hora.split(":").map(Number);
  const base = h === 12 ? "meio-dia" : h === 0 ? "meia-noite" : numeroPorExtenso(h, true);
  if (m === 0) return base;
  if (m === 30) return `${base} e meia`;
  return `${base} e ${numeroPorExtenso(m)}`;
}

// Frases com nome ou numero variavel. Exportadas para o script que lista o que precisa de
// audio (scripts/listar-frases-voz.ts): mudou um texto aqui, regerar os audios.
export const FRASE_TESTE = "Alertas de voz ativados. Eu aviso a abertura do pregão e as notícias do dia.";
export const FRASE_BOM_DIA = "Bom dia. O pregão abriu. Até as dez, só observar e marcar.";
export const FRASE_SEM_NOTICIA = "Hoje não tem notícia de impacto alto.";
export const fraseQuantasNoticias = (n: number) => `Hoje tem ${numeroPorExtenso(n, true)} ${n === 1 ? "notícia" : "notícias"} de impacto alto.`;
export const frasePrimeira = (nome: string) => `A primeira é ${nome},`;
export const fraseAs = (hora: string) => `às ${horaFalada(hora)}.`;
export const fraseNoticiaAntes = (nome: string) => `Atenção: em cinco minutos, ${nome}. Impacto alto.`;
export const fraseNoticiaAgora = (nome: string) => `Saindo agora: ${nome}.`;

function paraMinutos(hora: string): number {
  const [h, m] = hora.split(":").map(Number);
  return h * 60 + m;
}

export function alertasDoDia(dataISO: string, agenda: EventoAgenda[], preSessaoFechada: boolean): Alerta[] {
  if (!ehDiaDePregao(dataISO)) return [];

  const eventos = agenda
    .filter((e) => e.evento?.trim() && /^\d{2}:\d{2}$/.test(e.horario))
    .map((e) => ({ ...e, evento: e.evento.trim() }));
  const altos = eventos.filter((e) => e.impacto === "ALTO").sort((a, b) => paraMinutos(a.horario) - paraMinutos(b.horario));
  const resumo = altos.length === 0
    ? [FRASE_SEM_NOTICIA]
    : [fraseQuantasNoticias(altos.length), frasePrimeira(altos[0].evento), fraseAs(altos[0].horario)];

  const ny = aberturaNY(dataISO);
  const rotina: Array<[string, string | string[], number]> = [
    ["09:00", [FRASE_BOM_DIA, ...resumo], 1],
    ["09:55", "Cinco minutos para a abertura do mercado à vista.", 1],
    ["10:00", "Abertura do mercado à vista. Janela de entrada aberta.", 1],
    [somarMinutos(ny, -5), "Cinco minutos para a abertura de Nova York.", 0],
    [ny, "Abertura de Nova York.", 0],
    ["11:00", "Fim da janela nobre. A partir de agora, só com score oitenta.", 1],
    ["11:25", "Cinco minutos para fechar a janela de entrada.", 1],
    ["11:30", "Janela de entrada fechada. Agora é só gerenciar o que está aberto.", 1],
    ["11:55", "Faltam cinco minutos. Ao meio-dia, feche o Profit.", 1],
    ["12:00", "Fim do pregão do plano. Feche o Profit.", 1],
  ];
  if (!preSessaoFechada) rotina.push(["09:45", "Faltam quinze minutos para a janela. A pré-sessão ainda não foi fechada.", 1]);

  const alertas: Alerta[] = rotina.map(([hora, fala, ordem]) => {
    const segmentos = typeof fala === "string" ? [fala] : fala;
    return { id: `rotina-${hora}-${ordem}`, hora, texto: segmentos.join(" "), segmentos, grupo: "rotina", ordem };
  });

  eventos
    .filter((e) => e.horario >= "09:00" && e.horario <= "12:00")
    .forEach((e) => {
      const chave = `${e.horario}-${e.evento}`;
      if (e.impacto === "ALTO") {
        alertas.push({ id: `noticia-pre-${chave}`, hora: somarMinutos(e.horario, -5), texto: fraseNoticiaAntes(e.evento), segmentos: [fraseNoticiaAntes(e.evento)], grupo: "noticia", ordem: 2 });
      }
      if (e.impacto === "ALTO" || e.impacto === "MEDIO") {
        alertas.push({ id: `noticia-${chave}`, hora: e.horario, texto: fraseNoticiaAgora(e.evento), segmentos: [fraseNoticiaAgora(e.evento)], grupo: "noticia", ordem: 2 });
      }
    });

  return alertas.sort((a, b) => paraMinutos(a.hora) - paraMinutos(b.hora) || a.ordem - b.ordem);
}

/** Segundos desde a meia-noite em Sao Paulo. */
export function segundosDoDiaSP(agora: Date): number {
  const partes = new Intl.DateTimeFormat("en-GB", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).formatToParts(agora);
  const v = (t: string) => Number(partes.find((p) => p.type === t)?.value ?? 0);
  return (v("hour") % 24) * 3600 + v("minute") * 60 + v("second");
}

export const JANELA_DISPARO_S = 90;

/** Alertas cujo horario chegou ha no maximo 90 s e que ainda nao foram falados. */
export function alertasParaDisparar(alertas: Alerta[], agora: Date, jaFalados: Set<string>): Alerta[] {
  const s = segundosDoDiaSP(agora);
  return alertas.filter((a) => {
    const delta = s - paraMinutos(a.hora) * 60;
    return delta >= 0 && delta <= JANELA_DISPARO_S && !jaFalados.has(a.id);
  });
}
