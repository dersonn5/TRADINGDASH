import * as React from "react";
import {
  calcularDisciplina,
  calcularCustoDesvio,
  temDesvio,
  TradeMetricas,
  formatarBRL,
  formatarPct,
} from "@/lib/metricas";

interface DisciplinaCardProps {
  trades: TradeMetricas[];
}

export function DisciplinaCard({ trades }: DisciplinaCardProps) {
  const { pctNoPlano, tradesNoPlano, totalTrades, custoTotal, frase } = calcularDisciplina(trades);

  const desvios = trades
    .filter((t) => temDesvio(t))
    .map((t) => {
      const custo = calcularCustoDesvio(t);
      const raw = t.data || t.hora_entrada;
      const dataStr = raw ? `${raw.slice(8, 10)}/${raw.slice(5, 7)}` : "";

      let tipo = "Desvio do plano";
      if (t.antecipou_stop) tipo = "Antecipou o stop";
      else if (t.mudou_alvo) tipo = "Mudou o alvo";
      else if (t.parcial_emocional) tipo = "Parcial emocional";
      else if (t.respeitou_plano === false) tipo = "Não respeitou o plano";

      return {
        id: t.id || Math.random().toString(),
        data: dataStr,
        tipo,
        custo,
      };
    });

  const barWidth = Math.round(pctNoPlano * 100);

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Disciplina
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {frase}
        </span>
      </div>

      <div className="flex items-baseline gap-2.5">
        <span className="text-[36px] sm:text-[40px] font-semibold tracking-[-0.02em] text-[var(--actx)] leading-none">
          {formatarPct(pctNoPlano)}
        </span>
        <span className="text-[13px] text-[var(--tx2)]">
          {tradesNoPlano} de {totalTrades} no plano
        </span>
      </div>

      {/* Barra de progresso */}
      <div className="w-full h-2.5 rounded-full bg-[var(--neg)]/30 overflow-hidden">
        <div
          className="h-full rounded-full bg-[var(--ac)] transition-all duration-300"
          style={{ width: `${barWidth}%` }}
        />
      </div>

      {/* Lista de desvios */}
      <div className="flex flex-col gap-2.5 pt-3 border-t border-[var(--bd)]">
        <span className="text-[12px] text-[var(--tx3)]">
          Desvios do plano
        </span>
        {desvios.length === 0 ? (
          <span className="text-[13px] text-[var(--tx2)] italic">
            Nenhum desvio registrado no mês
          </span>
        ) : (
          desvios.slice(0, 3).map((d) => (
            <div
              key={d.id}
              className="flex justify-between items-center text-[13px]"
            >
              <span className="text-[var(--tx2)] truncate">
                {d.data} · {d.tipo}
              </span>
              <span className="font-semibold text-[var(--negtx)] shrink-0">
                {formatarBRL(-d.custo)}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
