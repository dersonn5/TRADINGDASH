"use client";

import * as React from "react";
import { listarTradesDoMes, TradeHistorico } from "@/lib/copa-db";
import {
  calcularKPIsGerais,
  agruparPorEstrategia,
  agruparPorHorario,
  formatarBRL,
  formatarR,
} from "@/lib/metricas";
import { KPICards } from "@/components/visao-geral/kpi-cards";
import { CurvaCapital } from "@/components/visao-geral/curva-capital";
import { PorEstrategia } from "@/components/visao-geral/por-estrategia";
import { PorHorario } from "@/components/visao-geral/por-horario";
import { GatilhosChart } from "@/components/visao-geral/gatilhos-chart";
import { TabelaEstrategias } from "@/components/visao-geral/tabela-estrategias";
import { TamanhoStop } from "@/components/visao-geral/tamanho-stop";
import { CalendarioCard } from "@/components/visao-geral/calendario-card";
import { DisciplinaCard } from "@/components/visao-geral/disciplina-card";
import { SetupCCard } from "@/components/visao-geral/setup-c-card";

const NOMES_MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

function getMesAnterior(ano: number, mes: number) {
  if (mes === 1) return { ano: ano - 1, mes: 12 };
  return { ano, mes: mes - 1 };
}

export default function VisaoGeralPage() {
  // Pega data atual no fuso SP
  const hojeSP = new Date();
  const [ano, setAno] = React.useState<number>(hojeSP.getFullYear());
  const [mes, setMes] = React.useState<number>(hojeSP.getMonth() + 1); // 1..12

  const [trades, setTrades] = React.useState<TradeHistorico[]>([]);
  const [tradesAnt, setTradesAnt] = React.useState<TradeHistorico[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  // Opções de meses no seletor: o mês de HOJE e os 2 anteriores. Ancorado em hoje,
  // não no mês escolhido — senão, ao escolher um mês passado, o atual some da lista.
  const opcoesMes = React.useMemo(() => {
    const list = [];
    let curAno = hojeSP.getFullYear();
    let curMes = hojeSP.getMonth() + 1;
    for (let i = 0; i < 3; i++) {
      list.unshift({ ano: curAno, mes: curMes, label: NOMES_MESES[curMes - 1] });
      const ant = getMesAnterior(curAno, curMes);
      curAno = ant.ano;
      curMes = ant.mes;
    }
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const carregarDados = React.useCallback(async (targetAno: number, targetMes: number) => {
    setLoading(true);
    setErro(null);
    try {
      const ant = getMesAnterior(targetAno, targetMes);
      const [dadosMes, dadosAnt] = await Promise.all([
        listarTradesDoMes(targetAno, targetMes),
        listarTradesDoMes(ant.ano, ant.mes),
      ]);
      setTrades(dadosMes);
      setTradesAnt(dadosAnt);
    } catch (e: any) {
      setErro(e.message || "Erro ao carregar trades do mês");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    carregarDados(ano, mes);
  }, [ano, mes, carregarDados]);

  const nomeMesAtual = NOMES_MESES[mes - 1];
  const antInfo = getMesAnterior(ano, mes);
  const nomeMesAnt = NOMES_MESES[antInfo.mes - 1];

  // Cálculos do resumo e KPIs
  const kpisAtual = React.useMemo(() => calcularKPIsGerais(trades), [trades]);
  const kpisAnt = React.useMemo(() => calcularKPIsGerais(tradesAnt), [tradesAnt]);
  const porStrat = React.useMemo(() => agruparPorEstrategia(trades), [trades]);
  const porHora = React.useMemo(() => agruparPorHorario(trades), [trades]);

  const textoResumo = React.useMemo(() => {
    if (trades.length === 0) return `Nenhum trade fechado em ${nomeMesAtual}.`;
    const totalPnl = kpisAtual.resultadoReais;
    const totalR = kpisAtual.resultadoR;
    const n = trades.length;
    const maisP = porStrat.maisResultado;
    const melhorH = porHora.melhor;

    let txt = `${nomeMesAtual} está em ${formatarBRL(totalPnl)} com ${n} ${n === 1 ? "trade" : "trades"} (${formatarR(totalR)}).`;
    if (maisP) {
      txt += ` ${maisP.nome} carrega o mês;`;
    }
    if (melhorH && melhorH.n > 0) {
      txt += ` o melhor horário é ${melhorH.faixa}–${melhorH.fim}.`;
    }
    return txt;
  }, [trades, kpisAtual, porStrat, porHora, nomeMesAtual]);

  const horaAtual = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());

  return (
    <div className="-m-4 md:-m-6 px-6 md:px-10 pt-8 pb-10 flex flex-col gap-5">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="text-[13px] text-[var(--tx3)]">
            {nomeMesAtual} {ano} · atualizado às {horaAtual}
          </span>
          <h1 className="text-[28px] sm:text-[30px] font-semibold tracking-[-0.02em] text-[var(--tx)]">
            Visão Geral
          </h1>
        </div>

        {/* Seletor de mês */}
        <div
          role="group"
          aria-label="Mês"
          className="flex items-center gap-1 p-1 bg-[var(--s1)] border border-[var(--bd)] rounded-xl self-start sm:self-auto"
        >
          {opcoesMes.map((opt) => {
            const isActive = opt.ano === ano && opt.mes === mes;
            return (
              <button
                key={`${opt.ano}-${opt.mes}`}
                type="button"
                aria-pressed={isActive}
                onClick={() => {
                  setAno(opt.ano);
                  setMes(opt.mes);
                }}
                className={`h-9 px-4 rounded-lg text-[13px] font-medium transition-all ${
                  isActive
                    ? "bg-[var(--ac)] text-[var(--onac)] font-semibold shadow-xs"
                    : "text-[var(--tx2)] hover:text-[var(--tx)]"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tratamento de Erro */}
      {erro && (
        <div className="p-5 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] text-[var(--negtx)] text-[14px]">
          {erro}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="p-12 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] text-center text-[var(--tx3)] text-[14px]">
          Carregando dados da Visão Geral…
        </div>
      ) : trades.length === 0 ? (
        /* Estado Vazio */
        <div className="py-20 px-8 rounded-2xl bg-[var(--s1)] border border-[var(--bd)] flex flex-col items-center justify-center gap-3 text-center">
          <span className="text-[18px] font-semibold text-[var(--tx)]">
            Nenhum trade fechado em {nomeMesAtual} de {ano}.
          </span>
          <span className="text-[14px] text-[var(--tx3)] max-w-md">
            Assim que você registrar e fechar operações no checklist durante o pregão deste mês, as métricas e gráficos aparecerão aqui.
          </span>
        </div>
      ) : (
        /* Conteúdo Completo da Visão Geral */
        <>
          {/* Card Resumo executivo */}
          <div className="flex items-center gap-3.5 p-4 sm:p-5 rounded-2xl bg-[var(--acs)] border border-[var(--bd)]">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              aria-hidden="true"
              className="shrink-0 stroke-[var(--actx)] stroke-[1.8] fill-none"
            >
              <path d="M3 17l6-6 4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M15 7h6v6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-[14px] sm:text-[15px] leading-relaxed text-[var(--tx)] font-medium">
              {textoResumo}
            </span>
          </div>

          {/* 5 KPIs */}
          <KPICards
            atual={kpisAtual}
            anterior={kpisAnt}
            nomeMesAtual={nomeMesAtual}
            nomeMesAnterior={nomeMesAnt}
          />

          {/* Linha 2: Curva de Capital (2fr) + Por Estratégia (1fr) */}
          <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
            <CurvaCapital trades={trades} nomeMes={nomeMesAtual} />
            <PorEstrategia trades={trades} />
          </div>

          {/* Linha 3: Por Horário de Entrada (1fr) + Gatilhos (1fr) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <PorHorario trades={trades} />
            <GatilhosChart trades={trades} />
          </div>

          {/* Linha 4: Estratégias no Mês (3fr) + Tamanho do Stop (2fr) */}
          <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-5">
            <TabelaEstrategias trades={trades} />
            <TamanhoStop trades={trades} />
          </div>

          {/* Linha 5: Calendário (1.3fr) + Disciplina (1fr) + Setup C e Contexto (1fr) */}
          <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_1fr_1fr] gap-5">
            <CalendarioCard trades={trades} ano={ano} mes={mes} />
            <DisciplinaCard trades={trades} />
            <SetupCCard trades={trades} />
          </div>
        </>
      )}
    </div>
  );
}
