import * as React from "react";
import { TradeMetricas, formatarBRL, calcularDrawdown } from "@/lib/metricas";

interface CurvaCapitalProps {
  trades: TradeMetricas[];
  nomeMes: string;
}

export function CurvaCapital({ trades, nomeMes }: CurvaCapitalProps) {
  const n = trades.length;

  if (n === 0) {
    return (
      <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
            Curva de capital
          </span>
          <span className="text-[16px] font-semibold">Sem trades para traçar a curva</span>
        </div>
      </section>
    );
  }

  // Acumulados
  const pnlList = trades.map((t) => Number(t.pnl_real ?? 0));
  const cum = [0];
  for (const p of pnlList) {
    cum.push(cum[cum.length - 1] + p);
  }

  // Por estratégia
  const acumStrat = (stratFilter: (id: string) => boolean) => {
    const a = [0];
    for (const t of trades) {
      const match = stratFilter(t.strategy_id);
      a.push(a[a.length - 1] + (match ? Number(t.pnl_real ?? 0) : 0));
    }
    return a;
  };

  const sC = acumStrat((id) => id === "varrida_barra_10" || id === "C");
  const sB = acumStrat((id) => id === "continuidade_tendencia" || id === "B");
  const sA = acumStrat((id) => id === "reversao_htf" || id === "A");

  const ddRes = calcularDrawdown(pnlList);
  const maxDD = ddRes.maxDrawdown;

  // Escala SVG
  const W = 688;
  const H = 250;
  const pl = 64;
  const pr = 16;
  const pt = 24;
  const pb = 32;

  const todos = [...cum, ...sA, ...sB, ...sC];
  const maxVal = Math.max(...todos);
  const minVal = Math.min(0, ...todos);
  const step = Math.max(200, Math.ceil((maxVal - minVal) / 4 / 100) * 100);
  const top = Math.ceil(Math.max(step, maxVal) / step) * step;
  const bot = Math.floor(Math.min(0, minVal) / step) * step;
  const range = top - bot || 1;

  const X = (i: number) => pl + (i * (W - pl - pr)) / (n || 1);
  const Y = (v: number) => pt + ((top - v) / range) * (H - pt - pb);

  const makePath = (arr: number[]) =>
    arr.map((v, i) => `${i === 0 ? "M" : "L"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join(" ");

  const pathCum = makePath(cum);
  const pathA = makePath(sA);
  const pathB = makePath(sB);
  const pathC = makePath(sC);

  const areaCum = `${pathCum} L${X(n).toFixed(1)} ${Y(bot).toFixed(1)} L${X(0).toFixed(1)} ${Y(bot).toFixed(1)} Z`;

  // Ticks eixo Y
  const ticks = [];
  for (let v = bot; v <= top; v += step) {
    ticks.push({
      v,
      y: Y(v).toFixed(1),
      label: v === 0 ? "0" : formatarBRL(v, false),
    });
  }

  // Ticks eixo X (datas)
  const formatDia = (t?: TradeMetricas) => {
    if (!t) return "";
    const raw = t.data || t.hora_entrada;
    if (!raw) return "";
    return raw.slice(8, 10) + "/" + raw.slice(5, 7);
  };

  const xLabelsIndices = Array.from(new Set([
    0,
    Math.floor(n / 4),
    Math.floor(n / 2),
    Math.floor((3 * n) / 4),
    n - 1,
  ])).filter((idx) => idx >= 0 && idx < n);

  const pico = Math.max(...cum);
  const iPico = cum.indexOf(pico);
  const diaPico = iPico > 0 ? formatDia(trades[iPico - 1]) : "início";

  // Trecho de Drawdown
  const hasDD = maxDD > 0 && ddRes.valeIndex > ddRes.picoIndex;
  const ddx = X(ddRes.picoIndex);
  const ddw = Math.max(16, X(ddRes.valeIndex) - ddx);

  const diaDDPico = ddRes.picoIndex > 0 ? formatDia(trades[ddRes.picoIndex - 1]) : "início";
  const diaDDVale = ddRes.valeIndex > 0 ? formatDia(trades[ddRes.valeIndex - 1]) : "fim";

  const frase = hasDD
    ? `Pico de ${formatarBRL(pico)} em ${diaPico} · pior trecho ${formatarBRL(-maxDD)} (${diaDDPico} → ${diaDDVale})`
    : `Pico de ${formatarBRL(pico)} · sem drawdown significativo`;

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
            Curva de capital
          </span>
          <span className="text-[16px] font-semibold leading-tight">
            {frase}
          </span>
        </div>
        <div className="flex items-center gap-3 flex-wrap text-[12px] text-[var(--tx2)]">
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-[3px] rounded-full bg-[var(--tx)]"></span>Total
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-[3px] rounded-full bg-[var(--k1)]"></span>Varrida das 10
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-[3px] rounded-full bg-[var(--k3)]"></span>Continuidade
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-[3px] rounded-full bg-[var(--k2)]"></span>Reversão HTF
          </span>
        </div>
      </div>

      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto min-w-[500px]"
          role="img"
          aria-label="Curva de capital do mês"
        >
          {/* Região do Drawdown Máximo */}
          {hasDD && (
            <g>
              <rect
                x={ddx.toFixed(1)}
                y={4}
                width={ddw.toFixed(1)}
                height={H - pb - 4}
                rx={6}
                fill="var(--neg)"
                fillOpacity={0.14}
              />
              <text
                x={(ddx + ddw / 2).toFixed(1)}
                y={16}
                textAnchor="middle"
                fill="var(--negtx)"
                fontSize={11}
                fontWeight={600}
              >
                {formatarBRL(-maxDD)}
              </text>
            </g>
          )}

          {/* Grid horizontal e ticks de valor */}
          {ticks.map((t, idx) => (
            <g key={idx}>
              <line
                x1={pl}
                x2={W - pr}
                y1={t.y}
                y2={t.y}
                stroke="var(--ln)"
                strokeWidth={1}
              />
              <text
                x={pl - 8}
                y={Number(t.y) + 4}
                textAnchor="end"
                fill="var(--tx3)"
                fontSize={11}
              >
                {t.label}
              </text>
            </g>
          ))}

          {/* Área sob a curva */}
          <path d={areaCum} fill="var(--ac)" fillOpacity={0.08} />

          {/* Linhas por setup */}
          <path
            d={pathA}
            fill="none"
            stroke="var(--k2)"
            strokeWidth={1.5}
            strokeDasharray="4 4"
          />
          <path
            d={pathB}
            fill="none"
            stroke="var(--k3)"
            strokeWidth={1.5}
            strokeDasharray="2 3"
          />
          <path
            d={pathC}
            fill="none"
            stroke="var(--k1)"
            strokeWidth={1.8}
          />

          {/* Linha principal total */}
          <path
            d={pathCum}
            fill="none"
            stroke="var(--tx)"
            strokeWidth={2.4}
            strokeLinejoin="round"
          />

          {/* Marcador final */}
          <circle
            cx={X(n).toFixed(1)}
            cy={Y(cum[n]).toFixed(1)}
            r={5}
            fill="var(--bg)"
            stroke="var(--tx)"
            strokeWidth={2.4}
          />

          {/* Eixo X labels */}
          {xLabelsIndices.map((i) => (
            <text
              key={i}
              x={X(i + 1).toFixed(1)}
              y={H - 8}
              textAnchor="middle"
              fill="var(--tx3)"
              fontSize={11}
            >
              {formatDia(trades[i])}
            </text>
          ))}
        </svg>
      </div>
    </section>
  );
}
