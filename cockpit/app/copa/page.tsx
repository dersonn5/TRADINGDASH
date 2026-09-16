"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, GateResult, StrategyRanking, SessionDay, Trade } from "@/lib/copa-api";
import { GateBanner } from "@/components/copa/gate-banner";
import { RankingEstrategias } from "@/components/copa/ranking-estrategias";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstNum,
  InstBadge,
  InstBand,
  InstEmpty,
  InstTable,
  InstRow,
  InstCell,
} from "@/components/inst";
import { FileText, PlusCircle, ArrowRight } from "lucide-react";

export default function CopaHomePage() {
  const hoje = new Date().toISOString().split("T")[0];

  const [session, setSession] = React.useState<SessionDay | null>(null);
  const [gate, setGate] = React.useState<GateResult | null>(null);
  const [ranking, setRanking] = React.useState<StrategyRanking[]>([]);
  const [todayTrades, setTodayTrades] = React.useState<Trade[]>([]);
  const [loading, setLoading] = React.useState(true);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const [sess, gateRes, rankRes, trades] = await Promise.all([
        copaApi.getSession(hoje),
        copaApi.getGate(hoje),
        copaApi.getRanking(hoje),
        copaApi.listTrades({ data: hoje }),
      ]);
      setSession(sess);
      setGate(gateRes);
      setRanking(rankRes);
      setTodayTrades(trades);
    } catch (err) {
      console.error("Erro ao carregar dados da home da Copa:", err);
    } finally {
      setLoading(false);
    }
  }, [hoje]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <InstPage eyebrow="COPA BTG" title="Cockpit Operacional da Copa">
        <InstEmpty>Carregando dados da sessão e do gate...</InstEmpty>
      </InstPage>
    );
  }

  // ESTADO 1: Sem pré-sessão preenchida hoje
  if (!session) {
    return (
      <InstPage eyebrow="COPA BTG · GATE" title="Pré-Sessão Não Preenchida">
        <InstBand
          tom="block"
          titulo="GATE FÍSICO TRAVADO"
          linhas={[
            "Nenhum trade é liberado sem o diagnóstico pré-mercado, mapeamento de liquidez e checagem de estado emocional.",
            "A Copa BTG exige respeito rigoroso aos protocolos antes de qualquer clique.",
          ]}
        />

        <InstCard label="O QUE VOCÊ VAI PREENCHER EM 60 SEGUNDOS:">
          <ul style={{ display: "flex", flexDirection: "column", gap: "8px", margin: 0, paddingLeft: "18px", fontSize: "12.5px", color: "var(--inst-text-2)" }}>
            <li>Viés macro (Bias D1 e H1) e contexto (Tendência / Range)</li>
            <li>Níveis-chave de liquidez (PDH, PDL, EQH/EQL)</li>
            <li>Agenda econômica de alto impacto</li>
            <li>Estado do operador (sono, tilt e pressão)</li>
          </ul>

          <div style={{ paddingTop: "12px" }}>
            <Link href="/copa/pre-sessao">
              <button
                type="button"
                className="mono tabular"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "var(--inst-now)",
                  color: "var(--inst-bg-deep)",
                  border: "none",
                  borderRadius: "3px",
                  padding: "12px 24px",
                  fontSize: "12px",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  cursor: "pointer",
                }}
              >
                <FileText className="h-4 w-4" /> PREENCHER PRÉ-SESSÃO AGORA
              </button>
            </Link>
          </div>
        </InstCard>
      </InstPage>
    );
  }

  // ESTADO 2: Com pré-sessão preenchida
  const pnlDia = gate?.breakers.pnl_dia ?? 0;
  const tradesDia = gate?.breakers.trades_dia ?? 0;
  const maxTradesDia = gate?.breakers.max_trades_dia ?? 3;
  const limitePerda = gate?.breakers.limite_perda_dia_efetivo ?? gate?.breakers.limite_perda_dia ?? 300;
  const perdasSeguidas = gate?.breakers.perdas_seguidas ?? 0;
  const distanciaLimitePerda = Math.max(0, limitePerda + pnlDia);

  return (
    <InstPage
      eyebrow="COPA BTG · OPERACIONAL"
      title="Cockpit Operacional da Copa"
      right={
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <Link href="/copa/pre-sessao">
            <button
              type="button"
              className="mono tabular"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "transparent",
                border: "1px solid var(--inst-line-2)",
                color: "var(--inst-dim)",
                borderRadius: "3px",
                padding: "6px 12px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <FileText className="h-3.5 w-3.5" /> Editar Pré-Sessão
            </button>
          </Link>

          <Link href="/copa/novo">
            <button
              type="button"
              disabled={!gate?.liberado}
              className="mono tabular"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: gate?.liberado ? "var(--inst-ok)" : "transparent",
                border: `1px solid ${gate?.liberado ? "var(--inst-ok)" : "var(--inst-line-2)"}`,
                color: gate?.liberado ? "var(--inst-on-ok)" : "var(--inst-ghost)",
                borderRadius: "3px",
                padding: "6px 14px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: gate?.liberado ? "pointer" : "not-allowed",
              }}
            >
              <PlusCircle className="h-3.5 w-3.5" /> Novo Trade (Checklist)
            </button>
          </Link>
        </div>
      }
    >
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "4px" }}>
        Gate de disciplina e controle de risco para WIN / WDO na Copa BTG.
      </div>

      {/* Banner Principal do Gate */}
      <GateBanner gate={gate} />

      {/* KPIs do Dia */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* PnL do Dia */}
        <InstCard label="PNL FECHADO HOJE">
          <InstNum
            value={`R$ ${pnlDia.toFixed(2)}`}
            tom={pnlDia > 0 ? "ok" : pnlDia < 0 ? "block" : "neutro"}
            size="lg"
          />
          <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
            {pnlDia >= 0 ? "Dentro da expectativa" : "Monitorando perda"}
          </span>
        </InstCard>

        {/* Trades Usados */}
        <InstCard label="TRADES DO DIA">
          <InstNum value={`${tradesDia} / ${maxTradesDia}`} size="lg" />
          <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
            {maxTradesDia - tradesDia} restantes
          </span>
        </InstCard>

        {/* Distância pro Limite */}
        <InstCard label="FOLGA PARA LIMITE DE PERDA">
          <InstNum value={`R$ ${distanciaLimitePerda.toFixed(2)}`} size="lg" />
          <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
            Limite diário: R$ {limitePerda.toFixed(2)}
          </span>
        </InstCard>

        {/* Perdas Seguidas / Cooldown */}
        <InstCard label="SEQUÊNCIA DE LOSSES">
          <InstNum
            value={`${perdasSeguidas} de ${gate?.breakers.max_perdas_seguidas ?? 2}`}
            tom={perdasSeguidas > 0 ? "now" : "neutro"}
            size="lg"
          />
          <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
            {gate?.breakers.cooldown_ate
              ? `Cooldown até ${gate.breakers.cooldown_ate}`
              : "Sem cooldown ativo"}
          </span>
        </InstCard>
      </div>

      {/* Ranking de Estratégias do Dia */}
      <RankingEstrategias ranking={ranking} />

      {/* Trades Abertos ou Recentes do Dia */}
      {todayTrades.length > 0 && (
        <InstCard
          label={`TRADES DE HOJE (${todayTrades.length})`}
          right={
            <Link href="/copa/trades" style={{ fontSize: "11px", color: "var(--inst-now)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
              Ver Journal Completo <ArrowRight className="h-3 w-3" />
            </Link>
          }
        >
          <InstTable
            colunas={[
              "ID / Operação",
              "Setup",
              "Entrada",
              "Stop",
              "Alvo",
              { label: "Status", align: "center" },
              { label: "Resultado", align: "right" },
            ]}
          >
            {todayTrades.map((t) => {
              const pnl = t.pnl_real ?? 0;
              return (
                <InstRow key={t.id} tom={t.status === "FECHADO" ? (pnl > 0 ? "ok" : pnl < 0 ? "block" : "neutro") : "now"}>
                  <InstCell>
                    <span className="mono tabular" style={{ fontWeight: 600 }}>
                      #{t.id} • {t.mercado} {t.direcao}
                    </span>
                  </InstCell>
                  <InstCell>
                    <span style={{ color: "var(--inst-dim)" }}>
                      {t.strategy_id} (Grade {t.grade})
                    </span>
                  </InstCell>
                  <InstCell>
                    <span className="mono tabular">{t.entrada}</span>
                  </InstCell>
                  <InstCell>
                    <span className="mono tabular">{t.stop}</span>
                  </InstCell>
                  <InstCell>
                    <span className="mono tabular">{t.alvo}</span>
                  </InstCell>
                  <InstCell align="center">
                    <InstBadge tom={t.status === "ABERTO" ? "now" : "neutro"}>
                      {t.status}
                    </InstBadge>
                  </InstCell>
                  <InstCell align="right">
                    {t.status === "FECHADO" ? (
                      <InstNum
                        value={`R$ ${pnl.toFixed(2)}`}
                        tom={pnl > 0 ? "ok" : pnl < 0 ? "block" : "neutro"}
                        size="sm"
                      />
                    ) : (
                      <span className="mono tabular" style={{ color: "var(--inst-faint)" }}>
                        EM ABERTO
                      </span>
                    )}
                  </InstCell>
                </InstRow>
              );
            })}
          </InstTable>
        </InstCard>
      )}
    </InstPage>
  );
}
