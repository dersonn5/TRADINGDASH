import * as React from "react";
import {
  agruparPorEstrategia,
  TradeMetricas,
  formatarBRL,
  formatarR,
  formatarPct,
} from "@/lib/metricas";

interface PorEstrategiaProps {
  trades: TradeMetricas[];
}

export function PorEstrategia({ trades }: PorEstrategiaProps) {
  const dados = agruparPorEstrategia(trades);
  const maxN = Math.max(1, ...dados.itens.map((i) => i.n));

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Por estratégia
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {dados.fraseResumo || "Sem trades no mês"}
        </span>
      </div>

      <div className="flex flex-col gap-4">
        {dados.itens.map((e) => {
          const wPct = Math.max(4, Math.round((e.n / maxN) * 100));
          const pnlPositivo = e.pnl >= 0;
          const rmPositivo = e.rm >= 0;

          return (
            <div
              key={e.strategy_id}
              className="flex flex-col gap-2 pt-4 first:pt-0 border-t first:border-0 border-[var(--bd)]"
            >
              <div className="flex justify-between items-baseline">
                <span className="text-[14px] font-medium text-[var(--tx)]">
                  {e.nome}
                </span>
                <span
                  className="text-[15px] font-semibold"
                  style={{ color: pnlPositivo ? "var(--actx)" : "var(--negtx)" }}
                >
                  {formatarBRL(e.pnl)}
                </span>
              </div>

              {/* Barra horizontal */}
              <div className="w-full h-2 rounded-full bg-[var(--s2)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--k1)] transition-all duration-300"
                  style={{ width: `${wPct}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-[12px] text-[var(--tx2)]">
                <span>
                  {e.n} {e.n === 1 ? "trade" : "trades"} · {formatarPct(e.taxaAcerto)} acerto
                </span>
                <span style={{ color: rmPositivo ? "var(--actx)" : "var(--negtx)" }}>
                  {formatarR(e.rm)} médio
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
