import * as React from "react";
import { TradeMetricas, formatarBRL } from "@/lib/metricas";

interface CalendarioCardProps {
  trades: TradeMetricas[];
  ano: number;
  mes: number; // 1..12
}

export function CalendarioCard({ trades, ano, mes }: CalendarioCardProps) {
  // Mapear PnL por dia do mês (1..31)
  const porDia: Record<number, number> = {};
  for (const t of trades) {
    const raw = t.data || t.hora_entrada;
    if (raw) {
      const d = parseInt(raw.slice(8, 10), 10);
      if (!isNaN(d)) {
        porDia[d] = (porDia[d] || 0) + Number(t.pnl_real ?? 0);
      }
    }
  }

  const diasOperados = Object.keys(porDia).length;
  const diasPositivos = Object.values(porDia).filter((v) => v > 0).length;
  const melhorDiaNum = Object.keys(porDia).sort((a, b) => porDia[Number(b)] - porDia[Number(a)])[0];
  const melhorDiaPnl = melhorDiaNum ? porDia[Number(melhorDiaNum)] : 0;

  const frase = diasOperados > 0
    ? `${diasPositivos} de ${diasOperados} dias positivos${
        melhorDiaPnl > 0
          ? ` · melhor: ${String(melhorDiaNum).padStart(2, "0")}/${String(mes).padStart(2, "0")} ${formatarBRL(melhorDiaPnl)}`
          : ""
      }`
    : "Nenhum dia operado";

  // Gerar semanas para o mês (Segunda a Sexta)
  const primeiroDiaDoMes = new Date(ano, mes - 1, 1);
  const ultimoDiaDoMes = new Date(ano, mes, 0).getDate();

  // Encontrar todas as semanas que contenham dias úteis
  const semanas: Array<Array<{ dia: number; mesAtual: boolean }>> = [];
  let semanaAtual: Array<{ dia: number; mesAtual: boolean }> = [];

  // Começar da segunda-feira da primeira semana
  const dayOfWeek1 = primeiroDiaDoMes.getDay(); // 0 = Domingo, 1 = Seg, ..., 6 = Sab
  // Ajuste para começar em Segunda (1)
  const diffSeg = dayOfWeek1 === 0 ? -6 : 1 - dayOfWeek1;
  const iterData = new Date(ano, mes - 1, 1 + diffSeg);

  while (iterData.getMonth() <= mes - 1 || iterData.getFullYear() < ano || semanaAtual.length > 0) {
    const dow = iterData.getDay();
    // Apenas dias úteis (1 a 5 -> Seg a Sex)
    if (dow >= 1 && dow <= 5) {
      semanaAtual.push({
        dia: iterData.getDate(),
        mesAtual: iterData.getMonth() === mes - 1,
      });

      if (semanaAtual.length === 5) {
        semanas.push(semanaAtual);
        semanaAtual = [];
        if (iterData.getMonth() > mes - 1 || iterData.getFullYear() > ano) {
          break;
        }
      }
    }
    iterData.setDate(iterData.getDate() + 1);
    if (semanas.length >= 6) break;
  }

  const maxAbsPnl = Math.max(1, ...Object.values(porDia).map(Math.abs));

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Calendário
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {frase}
        </span>
      </div>

      <div className="w-full flex flex-col gap-2 pt-1">
        {/* Cabeçalho dias da semana */}
        <div className="grid grid-cols-5 gap-2 text-center text-[11px] font-medium text-[var(--tx3)]">
          <span>Seg</span>
          <span>Ter</span>
          <span>Qua</span>
          <span>Qui</span>
          <span>Sex</span>
        </div>

        {/* Linhas das semanas */}
        {semanas.map((sem, r) => (
          <div key={r} className="grid grid-cols-5 gap-2">
            {sem.map((c, idx) => {
              const temValor = c.mesAtual && porDia[c.dia] !== undefined;
              const val = temValor ? porDia[c.dia] : undefined;
              const pos = val !== undefined && val >= 0;

              let fill = "var(--s2)";
              let op = 0.35;
              let txtVal = "";

              if (temValor && val !== undefined) {
                fill = pos ? "var(--ac)" : "var(--neg)";
                op = 0.2 + 0.5 * (Math.abs(val) / maxAbsPnl);
                txtVal = `${val > 0 ? "+" : val < 0 ? "−" : ""}${Math.abs(Math.round(val)).toLocaleString("pt-BR")}`;
              }

              return (
                <div
                  key={idx}
                  className={`h-11 rounded-lg border border-[var(--bd)] p-1.5 flex flex-col justify-between transition-all ${
                    !c.mesAtual ? "opacity-30 border-transparent bg-transparent" : ""
                  }`}
                  style={{
                    backgroundColor: temValor ? fill : undefined,
                    opacity: temValor ? op : undefined,
                  }}
                >
                  <span
                    className="text-[11px] leading-none"
                    style={{ color: c.mesAtual ? "var(--tx2)" : "var(--tx3)" }}
                  >
                    {c.dia}
                  </span>
                  {txtVal && (
                    <span className="text-[11px] font-semibold text-right leading-none text-[var(--tx)]">
                      {txtVal}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </section>
  );
}
