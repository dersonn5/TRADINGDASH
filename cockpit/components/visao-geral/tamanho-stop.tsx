import * as React from "react";
import { calcularDistribuicaoStops, TradeMetricas } from "@/lib/metricas";

interface TamanhoStopProps {
  trades: TradeMetricas[];
}

export function TamanhoStop({ trades }: TamanhoStopProps) {
  const { faixas, medianaStop, frase } = calcularDistribuicaoStops(trades);

  const W = 392;
  const H = 200;
  const groundY = 160;
  const maxCont = Math.max(1, ...faixas.map((f) => f.n));
  const sslot = W / faixas.length;

  const bars = faixas.map((s, i) => {
    const h = (s.n / maxCont) * 110;
    const cx = i * sslot + sslot / 2;
    const isMedian = medianaStop >= s.min && medianaStop < s.max;

    return {
      rotulo: s.rotulo,
      n: s.n,
      cx: cx.toFixed(1),
      x: (cx - 26).toFixed(1),
      y: (groundY - h).toFixed(1),
      h: Math.max(h, s.n > 0 ? 3 : 0).toFixed(1),
      vy: (groundY - h - 8).toFixed(1),
      fill: isMedian ? "var(--k1)" : "var(--k4)",
    };
  });

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Tamanho do stop
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {frase}
        </span>
      </div>

      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto min-w-[320px]"
          role="img"
          aria-label="Distribuição do tamanho dos stops em pontos"
        >
          {/* Linha de base */}
          <line
            x1={0}
            x2={W}
            y1={groundY}
            y2={groundY}
            stroke="var(--bd)"
            strokeWidth={1}
          />

          {/* Barras e rótulos */}
          {bars.map((b, idx) => (
            <g key={idx}>
              <rect
                x={b.x}
                y={b.y}
                width={52}
                height={b.h}
                rx={6}
                fill={b.fill}
              />
              <text
                x={b.cx}
                y={b.vy}
                textAnchor="middle"
                fill="var(--tx)"
                fontSize={12}
                fontWeight={600}
              >
                {b.n}
              </text>
              <text
                x={b.cx}
                y={180}
                textAnchor="middle"
                fill="var(--tx2)"
                fontSize={11}
              >
                {b.rotulo}
              </text>
            </g>
          ))}

          <text
            x={W}
            y={198}
            textAnchor="end"
            fill="var(--tx3)"
            fontSize={11}
          >
            pontos
          </text>
        </svg>
      </div>
    </section>
  );
}
