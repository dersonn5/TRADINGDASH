import * as React from "react";
import { agruparPorHorario, TradeMetricas, formatarR } from "@/lib/metricas";

interface PorHorarioProps {
  trades: TradeMetricas[];
}

export function PorHorario({ trades }: PorHorarioProps) {
  const { itens, frase, amostraPequena } = agruparPorHorario(trades);

  // Dimensões do SVG
  const W = 504;
  const H = 220;
  const pt = 20;
  const pb = 50;
  const plotH = H - pt - pb;
  const y0 = pt + plotH / 2;
  const slot = (W - 36) / 6;

  const maxAbsR = Math.max(1, Math.ceil(Math.max(...itens.map((b) => Math.abs(b.rm))) * 2) / 2);

  const bars = itens.map((b, i) => {
    const h = (Math.abs(b.rm) / maxAbsR) * (plotH / 2);
    const cx = 36 + i * slot + slot / 2;
    const y = b.rm >= 0 ? y0 - h : y0;
    const fill = b.rm >= 0 ? "var(--ac)" : "var(--neg)";
    const vy = b.rm >= 0 ? y0 - h - 6 : y0 + h + 14;

    return {
      faixa: b.faixa,
      cx: cx.toFixed(1),
      x: (cx - 22).toFixed(1),
      y: y.toFixed(1),
      h: Math.max(h, b.n > 0 ? 3 : 0).toFixed(1),
      fill,
      val: b.n > 0 ? formatarR(b.rm) : "—",
      vy: vy.toFixed(1),
      nTxt: `${b.n} ${b.n === 1 ? "trade" : "trades"}`,
    };
  });

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex justify-between items-start gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
            Por horário de entrada
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

      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto min-w-[440px]"
          role="img"
          aria-label="R médio por faixa de 15 minutos"
        >
          {/* Linha zero */}
          <line
            x1={36}
            x2={W}
            y1={y0}
            y2={y0}
            stroke="var(--bd)"
            strokeWidth={1}
          />

          {/* Rótulos do eixo Y */}
          <text
            x={30}
            y={pt + 4}
            textAnchor="end"
            fill="var(--tx3)"
            fontSize={11}
          >
            +{String(maxAbsR).replace(".", ",")}R
          </text>
          <text
            x={30}
            y={y0 + 4}
            textAnchor="end"
            fill="var(--tx3)"
            fontSize={11}
          >
            0
          </text>
          <text
            x={30}
            y={pt + plotH + 4}
            textAnchor="end"
            fill="var(--tx3)"
            fontSize={11}
          >
            −{String(maxAbsR).replace(".", ",")}R
          </text>

          {/* Barras e rótulos */}
          {bars.map((b, idx) => (
            <g key={idx}>
              <rect
                x={b.x}
                y={b.y}
                width={44}
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
                {b.val}
              </text>
              <text
                x={b.cx}
                y={196}
                textAnchor="middle"
                fill="var(--tx2)"
                fontSize={12}
              >
                {b.faixa}
              </text>
              <text
                x={b.cx}
                y={213}
                textAnchor="middle"
                fill="var(--k1)"
                fontSize={11}
              >
                {b.nTxt}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </section>
  );
}
