import * as React from "react";
import { agruparSetupCeContexto, TradeMetricas, formatarR, formatarPct } from "@/lib/metricas";

interface SetupCCardProps {
  trades: TradeMetricas[];
}

export function SetupCCard({ trades }: SetupCCardProps) {
  const { modos, contextos, frase, amostraPequena } = agruparSetupCeContexto(trades);

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex justify-between items-start gap-2">
        <div className="flex flex-col gap-1">
          <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
            Setup C e contexto
          </span>
          <span className="text-[16px] font-semibold leading-tight">
            {frase}
          </span>
        </div>
        {amostraPequena && (
          <span className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-[var(--s2)] border border-[var(--bd)] text-[var(--tx3)]">
            amostra pequena
          </span>
        )}
      </div>

      {/* Modos do Setup C */}
      <div className="flex flex-col gap-1">
        <span className="text-[12px] text-[var(--tx3)] pb-1">
          Modo (Varrida das 10)
        </span>
        {modos.map((m) => {
          const rmPositivo = m.rm >= 0;
          return (
            <div
              key={m.nome}
              className="flex items-center gap-2.5 py-2 border-t border-[var(--bd)] text-[13px]"
            >
              <span className="w-7 font-semibold text-[var(--tx)]">
                {m.nome}
              </span>
              <span className="grow text-[var(--tx2)] truncate">
                {m.n} {m.n === 1 ? "trade" : "trades"} · {formatarPct(m.taxaAcerto)}
              </span>
              <span
                className="font-semibold shrink-0"
                style={{ color: rmPositivo ? "var(--actx)" : "var(--negtx)" }}
              >
                {formatarR(m.rm)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Contexto da 1ª hora */}
      <div className="flex flex-col gap-1 pt-1">
        <span className="text-[12px] text-[var(--tx3)] pb-1">
          Contexto da 1ª hora (todos os setups)
        </span>
        {contextos.map((ctx) => {
          const rmPositivo = ctx.rm >= 0;
          return (
            <div
              key={ctx.nome}
              className="flex items-center gap-2.5 py-2 border-t border-[var(--bd)] text-[13px]"
            >
              <span className="grow text-[var(--tx)] truncate">
                {ctx.nome}
              </span>
              <span className="text-[var(--tx2)] shrink-0">
                {ctx.n} {ctx.n === 1 ? "trade" : "trades"}
              </span>
              <span
                className="w-16 text-right font-semibold shrink-0"
                style={{ color: rmPositivo ? "var(--actx)" : "var(--negtx)" }}
              >
                {formatarR(ctx.rm)}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
