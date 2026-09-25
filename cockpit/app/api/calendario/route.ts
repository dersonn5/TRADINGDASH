import { NextRequest, NextResponse } from "next/server";
import { FONTE_CALENDARIO, converterFeed, EventoFeed } from "@/lib/calendario";

// Eventos dos EUA de impacto Alto e Medio do dia, com horario de Sao Paulo.
// O navegador nao pode chamar a fonte direto (CORS), por isso passa por aqui.
// A data vem do cliente (?data=AAAA-MM-DD): ler searchParams deixa a rota dinamica,
// e o feed fica 1 h no cache de fetch — a fonte pede para nao ser chamada toda hora.

function hojeSP() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}

export async function GET(request: NextRequest) {
  const pedida = request.nextUrl.searchParams.get("data");
  const data = pedida && /^\d{4}-\d{2}-\d{2}$/.test(pedida) ? pedida : hojeSP();

  try {
    const res = await fetch(FONTE_CALENDARIO, { next: { revalidate: 3600 } });
    if (!res.ok) {
      return NextResponse.json({ erro: `fonte do calendário respondeu ${res.status}` }, { status: 502 });
    }
    const feed = (await res.json()) as EventoFeed[];
    if (!Array.isArray(feed)) {
      return NextResponse.json({ erro: "fonte do calendário devolveu formato inesperado" }, { status: 502 });
    }
    return NextResponse.json({ data, eventos: converterFeed(feed, data) });
  } catch (e) {
    return NextResponse.json({ erro: `falha ao buscar o calendário: ${(e as Error).message}` }, { status: 502 });
  }
}
