import * as React from "react";
import { KPIsGerais, formatarBRL, formatarR, formatarPct, formatarNumero } from "@/lib/metricas";

interface KPICardsProps {
  atual: KPIsGerais;
  anterior?: KPIsGerais | null;
  nomeMesAtual: string;
  nomeMesAnterior?: string;
}

export function KPICards({ atual, anterior, nomeMesAnterior }: KPICardsProps) {
  const hasAnt = Boolean(anterior && anterior.totalTrades > 0);

  // Delta de resultado
  let deltaResultado = "—";
  if (hasAnt && anterior) {
    const diff = atual.resultadoReais - anterior.resultadoReais;
    deltaResultado = `${formatarBRL(diff)} vs ${nomeMesAnterior || "mês anterior"}`;
  }

  // Delta de trades
  let deltaTrades = hasAnt && anterior
    ? `${nomeMesAnterior || "mês ant."}: ${anterior.totalTrades} trades · ${formatarPct(anterior.taxaAcerto)}`
    : "—";

  // Delta de expectativa
  let deltaExp = hasAnt && anterior
    ? `${nomeMesAnterior || "mês ant."}: ${formatarR(anterior.expectativaR)}`
    : "—";

  // Delta de profit factor
  let deltaPF = hasAnt && anterior && anterior.profitFactor !== null
    ? `${nomeMesAnterior || "mês ant."}: ${formatarNumero(anterior.profitFactor)}`
    : "—";

  // Delta de drawdown
  let deltaDD = hasAnt && anterior
    ? `${nomeMesAnterior || "mês ant."}: ${formatarBRL(-anterior.maxDrawdownReais)}`
    : "—";

  const cards = [
    {
      label: "Resultado",
      valor: formatarBRL(atual.resultadoReais),
      cor: atual.resultadoReais >= 0 ? "var(--actx)" : "var(--negtx)",
      sub: `${formatarR(atual.resultadoR)} no mês`,
      delta: deltaResultado,
    },
    {
      label: "Trades",
      valor: String(atual.totalTrades),
      cor: "var(--tx)",
      sub: `${formatarPct(atual.taxaAcerto)} de acerto`,
      delta: deltaTrades,
    },
    {
      label: "Expectativa",
      valor: formatarR(atual.expectativaR),
      cor: atual.expectativaR >= 0 ? "var(--actx)" : "var(--negtx)",
      sub: `por trade · payoff ${formatarNumero(atual.payoff)}`,
      delta: deltaExp,
    },
    {
      label: "Profit factor",
      valor: formatarNumero(atual.profitFactor),
      cor: "var(--tx)",
      sub: `${formatarBRL(atual.resultadoReais >= 0 ? atual.resultadoReais : 0, false)} saldo`,
      delta: deltaPF,
    },
    {
      label: "Drawdown máximo",
      valor: formatarBRL(-atual.maxDrawdownReais),
      cor: "var(--negtx)",
      sub: `${formatarR(-atual.maxDrawdownR)} no pior trecho`,
      delta: deltaDD,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {cards.map((k, i) => (
        <div
          key={i}
          className="flex flex-col gap-2 p-5 rounded-2xl bg-[var(--s1)] border border-[var(--bd)]"
        >
          <span className="text-[11px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
            {k.label}
          </span>
          <span
            className="text-[26px] sm:text-[28px] font-semibold tracking-[-0.02em] font-sans"
            style={{ color: k.cor }}
          >
            {k.valor}
          </span>
          <span className="text-[13px] text-[var(--tx2)] truncate">
            {k.sub}
          </span>
          <span className="mt-1 pt-2.5 border-t border-[var(--bd)] text-[12px] text-[var(--tx3)] truncate">
            {k.delta}
          </span>
        </div>
      ))}
    </div>
  );
}
