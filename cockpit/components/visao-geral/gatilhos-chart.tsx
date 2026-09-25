import * as React from "react";
import { agruparPorGatilho, TradeMetricas, formatarR, formatarPct } from "@/lib/metricas";

interface GatilhosChartProps {
  trades: TradeMetricas[];
}

export function GatilhosChart({ trades }: GatilhosChartProps) {
  const { itens, frase, maisUsado, pagaMais } = agruparPorGatilho(trades);
  const total = trades.length;

  const coresK = ["var(--k1)", "var(--k2)", "var(--k3)", "var(--k4)", "var(--k5)"];
  const circ = 2 * Math.PI * 66;

  let acc = 0;
  const donutSegments = itens.map((g, i) => {
    const len = total > 0 ? (g.n / total) * circ : 0;
    const seg = Math.max(len - 3, 0);
    const dash = `${seg.toFixed(1)} ${(circ - seg).toFixed(1)}`;
    const off = (-acc).toFixed(1);
    acc += len;

    return {
      ...g,
      cor: coresK[i % coresK.length],
      dash,
      off,
    };
  });

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Gatilhos
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {frase}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6 sm:gap-8 pt-2">
        {/* Donut circular */}
        <div className="shrink-0 relative flex items-center justify-center">
          <svg
            width="184"
            height="184"
            viewBox="0 0 184 184"
            role="img"
            aria-label="Distribuição dos gatilhos"
          >
            {/* Círculo de fundo */}
            <circle
              cx="92"
              cy="92"
              r="66"
              fill="none"
              stroke="var(--s2)"
              strokeWidth="20"
            />
            {/* Segmentos */}
            {donutSegments.map((g, idx) => (
              <circle
                key={idx}
                cx="92"
                cy="92"
                r="66"
                transform="rotate(-90 92 92)"
                strokeDasharray={g.dash}
                strokeDashoffset={g.off}
                fill="none"
                stroke={g.cor}
                strokeWidth="20"
              />
            ))}
            <text
              x="92"
              y="90"
              textAnchor="middle"
              fill="var(--tx)"
              fontSize="30"
              fontWeight="600"
            >
              {total}
            </text>
            <text
              x="92"
              y="112"
              textAnchor="middle"
              fill="var(--tx3)"
              fontSize="12"
            >
              trades
            </text>
          </svg>
        </div>

        {/* Legenda lateral */}
        <div className="grow w-full flex flex-col gap-3">
          {donutSegments.map((g, idx) => {
            const rmPositivo = g.rm >= 0;
            return (
              <div
                key={idx}
                className="flex items-center gap-2.5 text-[13px]"
              >
                <span
                  className="w-2.5 h-2.5 rounded-[3px] shrink-0"
                  style={{ background: g.cor }}
                />
                <span className="grow truncate text-[var(--tx)]">
                  {g.nome}
                </span>
                <span className="w-14 text-right text-[var(--tx2)] shrink-0">
                  {g.n} · {formatarPct(g.pct)}
                </span>
                <span
                  className="w-16 text-right font-semibold shrink-0"
                  style={{ color: rmPositivo ? "var(--actx)" : "var(--negtx)" }}
                >
                  {formatarR(g.rm)}
                </span>
              </div>
            );
          })}
          <span className="text-[11px] text-[var(--tx3)] text-right pt-1">
            quantidade · R médio
          </span>
        </div>
      </div>
    </section>
  );
}
