import * as React from "react";
import {
  agruparPorEstrategia,
  calcularKPIsGerais,
  TradeMetricas,
  formatarBRL,
  formatarR,
  formatarPct,
} from "@/lib/metricas";

interface TabelaEstrategiasProps {
  trades: TradeMetricas[];
}

export function TabelaEstrategias({ trades }: TabelaEstrategiasProps) {
  const dados = agruparPorEstrategia(trades);
  const tot = calcularKPIsGerais(trades);

  const totPnlPositivo = tot.resultadoReais >= 0;
  const totRmPositivo = tot.expectativaR >= 0;

  return (
    <section className="p-6 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="text-[12px] font-medium tracking-[0.06em] uppercase text-[var(--tx3)]">
          Estratégias no mês
        </span>
        <span className="text-[16px] font-semibold leading-tight">
          {dados.fraseTabela || "Sem dados por estratégia"}
        </span>
      </div>

      <div className="w-full overflow-x-auto">
        <div role="table" aria-label="Estratégias no mês" className="w-full min-w-[500px] flex flex-col text-[13px]">
          {/* Cabeçalho */}
          <div
            role="row"
            className="grid grid-cols-[1.6fr_repeat(6,minmax(0,1fr))] gap-2 items-center pb-2.5 text-[var(--tx3)] text-[11px] tracking-[0.06em] uppercase border-b border-[var(--bd)]"
          >
            <span role="columnheader">Estratégia</span>
            <span role="columnheader" className="text-right">Trades</span>
            <span role="columnheader" className="text-right">Acerto</span>
            <span role="columnheader" className="text-right">R médio</span>
            <span role="columnheader" className="text-right">Resultado</span>
            <span role="columnheader" className="text-right">DD máx</span>
            <span role="columnheader" className="text-right">Stop med.</span>
          </div>

          {/* Linhas */}
          {dados.itens.map((e) => {
            const pnlPositivo = e.pnl >= 0;
            const rmPositivo = e.rm >= 0;

            return (
              <div
                key={e.strategy_id}
                role="row"
                className="grid grid-cols-[1.6fr_repeat(6,minmax(0,1fr))] gap-2 items-center py-3.5 border-b border-[var(--bd)]"
              >
                <span role="cell" className="font-medium text-[var(--tx)] truncate">
                  {e.nome}
                </span>
                <span role="cell" className="text-right text-[var(--tx)]">
                  {e.n}
                </span>
                <span role="cell" className="text-right text-[var(--tx2)]">
                  {formatarPct(e.taxaAcerto)}
                </span>
                <span
                  role="cell"
                  className="text-right"
                  style={{ color: rmPositivo ? "var(--actx)" : "var(--negtx)" }}
                >
                  {formatarR(e.rm)}
                </span>
                <span
                  role="cell"
                  className="text-right font-semibold"
                  style={{ color: pnlPositivo ? "var(--actx)" : "var(--negtx)" }}
                >
                  {formatarBRL(e.pnl)}
                </span>
                <span role="cell" className="text-right text-[var(--negtx)]">
                  {formatarBRL(-e.maxDrawdownReais)}
                </span>
                <span role="cell" className="text-right text-[var(--tx2)]">
                  {e.stopMediano} pts
                </span>
              </div>
            );
          })}

          {/* Linha Total */}
          <div
            role="row"
            className="grid grid-cols-[1.6fr_repeat(6,minmax(0,1fr))] gap-2 items-center py-3.5 text-[var(--tx2)] font-medium"
          >
            <span role="cell" className="font-semibold text-[var(--tx)]">
              Total
            </span>
            <span role="cell" className="text-right text-[var(--tx)]">
              {tot.totalTrades}
            </span>
            <span role="cell" className="text-right">
              {formatarPct(tot.taxaAcerto)}
            </span>
            <span
              role="cell"
              className="text-right"
              style={{ color: totRmPositivo ? "var(--actx)" : "var(--negtx)" }}
            >
              {formatarR(tot.expectativaR)}
            </span>
            <span
              role="cell"
              className="text-right font-semibold"
              style={{ color: totPnlPositivo ? "var(--actx)" : "var(--negtx)" }}
            >
              {formatarBRL(tot.resultadoReais)}
            </span>
            <span role="cell" className="text-right text-[var(--negtx)]">
              {formatarBRL(-tot.maxDrawdownReais)}
            </span>
            <span role="cell" className="text-right text-[var(--tx)]">
              {tot.stopMediano} pts
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
