"use client";

import * as React from "react";
import { copaApi, CopaStats } from "@/lib/copa-api";
import { StatsPorItemTable } from "@/components/copa/stats-por-item";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstNum,
  InstBadge,
  InstBand,
  InstEmpty,
} from "@/components/inst";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { ShieldAlert } from "lucide-react";

export default function CopaStatsPage() {
  const [stats, setStats] = React.useState<CopaStats | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await copaApi.getStats();
        setStats(data);
      } catch (err) {
        console.error("Erro ao carregar estatísticas da Copa:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <InstPage eyebrow="COPA BTG · ESTATÍSTICA" title="Estatísticas & Prova Matemática">
        <InstEmpty>Carregando estatísticas da Copa...</InstEmpty>
      </InstPage>
    );
  }

  const geral = stats?.geral;
  const hasTrades = (geral?.trades || 0) > 0;

  return (
    <InstPage
      eyebrow="COPA BTG · ESTATÍSTICA"
      title="Estatísticas & Prova Matemática"
    >
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "4px" }}>
        Descubra quais confluências geram edge estatístico e quanto a indisciplina custou na Copa.
      </div>

      {!hasTrades ? (
        <InstEmpty>
          <InstBadge tom="now">Aguardando Operações</InstBadge>
          <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--inst-text)", marginTop: "6px" }}>
            Nenhum Trade Fechado Ainda
          </div>
          <div style={{ maxWidth: "480px", color: "var(--inst-dim)", lineHeight: 1.4 }}>
            Conforme você registrar e fechar trades com auditoria de disciplina, o motor estatístico
            calculará a curva de capital, o delta de winrate por item de checklist e o custo de desvios.
          </div>
        </InstEmpty>
      ) : (
        <>
          {/* 1. KPIs GERAIS */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            {/* Total PnL */}
            <InstCard label="PNL ACUMULADO">
              <InstNum
                value={`R$ ${(geral?.pnl_total ?? 0).toFixed(2)}`}
                tom={(geral?.pnl_total ?? 0) >= 0 ? "ok" : "block"}
                size="lg"
              />
              <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)" }}>
                {geral?.trades} trades
              </span>
            </InstCard>

            {/* Winrate */}
            <InstCard label="TAXA DE ACERTO">
              <InstNum
                value={`${(geral?.winrate ?? 0).toFixed(1)}%`}
                tom={(geral?.winrate ?? 0) >= 50 ? "ok" : "now"}
                size="lg"
              />
              <span style={{ fontSize: "10px", color: "var(--inst-faint)" }}>de vitórias</span>
            </InstCard>

            {/* Profit Factor */}
            <InstCard label="FATOR DE LUCRO (PF)">
              <InstNum value={(geral?.profit_factor ?? 0).toFixed(2)} size="lg" />
              <span style={{ fontSize: "10px", color: "var(--inst-faint)" }}>ganhos / perdas</span>
            </InstCard>

            {/* Expectância */}
            <InstCard label="EXPECTÂNCIA / TRADE">
              <InstNum
                value={`R$ ${(geral?.expectancia ?? 0).toFixed(2)}`}
                tom={(geral?.expectancia ?? 0) >= 0 ? "ok" : "block"}
                size="lg"
              />
              <span style={{ fontSize: "10px", color: "var(--inst-faint)" }}>média por clique</span>
            </InstCard>

            {/* Max Drawdown */}
            <InstCard label="MAX DRAWDOWN">
              <InstNum
                value={`${(geral?.max_drawdown ?? 0).toFixed(1)}%`}
                tom="block"
                size="lg"
              />
              <span style={{ fontSize: "10px", color: "var(--inst-faint)" }}>queda do pico</span>
            </InstCard>

            {/* Custo Indisciplina */}
            <InstCard label="CUSTO INDISCIPLINA">
              <InstNum
                value={`R$ ${(stats?.disciplina.custo_total ?? 0).toFixed(2)}`}
                tom="block"
                size="lg"
              />
              <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)" }}>
                {stats?.disciplina.trades_com_desvio} trades com erro
              </span>
            </InstCard>
          </div>

          {/* 2. CURVA DE CAPITAL (EQUITY) */}
          <InstCard label="CURVA DE CAPITAL DA COPA">
            <div className="h-64 w-full" style={{ marginTop: "4px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats?.equity || []} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
                  <defs>
                    <linearGradient id="eqCopa" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--inst-ok)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="var(--inst-ok)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--inst-line)" vertical={false} />
                  <XAxis dataKey="t" tick={{ fontSize: 10, fill: "var(--inst-faint)" }} stroke="var(--inst-line)" minTickGap={30} />
                  <YAxis tick={{ fontSize: 10, fill: "var(--inst-faint)" }} stroke="var(--inst-line)" domain={["auto", "auto"]} width={60} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--inst-panel)",
                      border: "1px solid var(--inst-line-2)",
                      borderRadius: 3,
                      fontSize: 12,
                      color: "var(--inst-text)",
                    }}
                    formatter={(v) => [`R$ ${Number(v).toFixed(2)}`, "Saldo"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="balance"
                    stroke="var(--inst-ok)"
                    strokeWidth={2}
                    fill="url(#eqCopa)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </InstCard>

          {/* 3. BLOCO PRINCIPAL: STATS POR ITEM */}
          <InstCard label="EDGE ESTATÍSTICO POR ITEM DE CHECKLIST">
            <StatsPorItemTable items={stats?.por_item || []} />
          </InstCard>

          {/* 4. BLOCO CUSTO DA INDISCIPLINA DETALHADO */}
          <InstCard
            label={
              <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", color: "var(--inst-block)" }}>
                <ShieldAlert className="h-4 w-4" /> AUDITORIA: CUSTO DA INDISCIPLINA
              </span>
            }
            right={
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "10px", color: "var(--inst-faint)", display: "block" }}>
                  Prejuízo Evitável:
                </span>
                <span className="mono tabular" style={{ fontSize: "16px", fontWeight: 700, color: "var(--inst-block)" }}>
                  R$ {(stats?.disciplina.custo_total ?? 0).toFixed(2)}
                </span>
              </div>
            }
          >
            <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginBottom: "4px" }}>
              Diferença monetária (PnL Plano − PnL Real) provocada por quebras do plano operacional.
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {stats?.disciplina.por_flag.map((item) => (
                <div
                  key={item.flag}
                  style={{
                    borderRadius: "3px",
                    border: "1px solid var(--inst-line-2)",
                    background: "var(--inst-bg-deep)",
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <span className="mono tabular" style={{ fontSize: "11px", fontWeight: 700, color: "var(--inst-text)" }}>
                    {item.flag.replace(/_/g, " ")}
                  </span>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: "4px" }}>
                    <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
                      {item.n} ocorrências
                    </span>
                    <span
                      className="mono tabular"
                      style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: item.custo > 0 ? "var(--inst-block)" : "var(--inst-text)",
                      }}
                    >
                      {item.custo > 0 ? `-R$ ${item.custo.toFixed(2)}` : "R$ 0.00"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </InstCard>

          {/* 5. PERFORMANCE POR GRADE E POR ESTRATÉGIA */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Por Grade */}
            <InstCard
              label="PERFORMANCE POR GRADE (SCORE)"
              right={<span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>Validação A+ vs B/C</span>}
            >
              <div className="space-y-2">
                {stats?.por_grade.map((g) => (
                  <div
                    key={g.grade}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      borderRadius: "3px",
                      border: "1px solid var(--inst-line-2)",
                      background: "var(--inst-bg-deep)",
                      fontSize: "12px",
                    }}
                    className="mono tabular"
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <InstBadge tom="neutro">{g.grade}</InstBadge>
                      <span style={{ color: "var(--inst-faint)" }}>({g.n} trades)</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <span style={{ fontWeight: 600 }}>{g.winrate.toFixed(1)}% WR</span>
                      <InstNum
                        value={`R$ ${g.pnl.toFixed(2)}`}
                        tom={g.pnl >= 0 ? "ok" : "block"}
                        size="sm"
                      />
                    </div>
                  </div>
                ))}
                {(!stats?.por_grade || stats.por_grade.length === 0) && (
                  <span style={{ fontSize: "12px", color: "var(--inst-faint)", fontStyle: "italic" }}>
                    Sem dados de grade.
                  </span>
                )}
              </div>
            </InstCard>

            {/* Por Estratégia */}
            <InstCard
              label="PERFORMANCE POR ESTRATÉGIA"
              right={<span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>Resultado consolidado</span>}
            >
              <div className="space-y-2">
                {stats?.por_estrategia.map((s) => (
                  <div
                    key={s.strategy_id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      borderRadius: "3px",
                      border: "1px solid var(--inst-line-2)",
                      background: "var(--inst-bg-deep)",
                      fontSize: "12px",
                    }}
                    className="mono tabular"
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontWeight: 600, color: "var(--inst-text)" }}>{s.nome}</span>
                      <span style={{ color: "var(--inst-faint)" }}>({s.n} trades)</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <span style={{ fontWeight: 600 }}>{s.winrate.toFixed(1)}% WR</span>
                      <InstNum
                        value={`R$ ${s.pnl.toFixed(2)}`}
                        tom={s.pnl >= 0 ? "ok" : "block"}
                        size="sm"
                      />
                    </div>
                  </div>
                ))}
                {(!stats?.por_estrategia || stats.por_estrategia.length === 0) && (
                  <span style={{ fontSize: "12px", color: "var(--inst-faint)", fontStyle: "italic" }}>
                    Sem dados de estratégia.
                  </span>
                )}
              </div>
            </InstCard>
          </div>

          {/* 6. PERFORMANCE POR HORÁRIO E DIA DA SEMANA */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Por Hora */}
            <InstCard label="PERFORMANCE POR JANELA HORÁRIA">
              <div className="grid grid-cols-3 gap-2 text-center mono tabular" style={{ fontSize: "12px" }}>
                {stats?.por_hora.map((h) => (
                  <div
                    key={h.hora}
                    style={{
                      padding: "10px",
                      borderRadius: "3px",
                      border: "1px solid var(--inst-line-2)",
                      background: "var(--inst-bg-deep)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "3px",
                    }}
                  >
                    <span style={{ color: "var(--inst-faint)", fontSize: "10px" }}>
                      {h.hora}:00 - {h.hora}:59
                    </span>
                    <span style={{ fontWeight: 700 }}>{h.winrate.toFixed(1)}% WR</span>
                    <InstNum
                      value={`R$ ${h.pnl.toFixed(2)}`}
                      tom={h.pnl >= 0 ? "ok" : "block"}
                      size="sm"
                    />
                    <span style={{ fontSize: "9px", color: "var(--inst-faint)" }}>({h.n} ops)</span>
                  </div>
                ))}
              </div>
            </InstCard>

            {/* Por Dia da Semana */}
            <InstCard label="PERFORMANCE POR DIA DA SEMANA">
              <div className="grid grid-cols-5 gap-2 text-center mono tabular" style={{ fontSize: "12px" }}>
                {stats?.por_dia_semana.map((d) => (
                  <div
                    key={d.dia}
                    style={{
                      padding: "10px",
                      borderRadius: "3px",
                      border: "1px solid var(--inst-line-2)",
                      background: "var(--inst-bg-deep)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "3px",
                    }}
                  >
                    <span style={{ color: "var(--inst-faint)", fontSize: "10px", textTransform: "uppercase" }}>
                      {d.dia}
                    </span>
                    <span style={{ fontWeight: 700 }}>{d.winrate.toFixed(1)}%</span>
                    <InstNum
                      value={`R$ ${d.pnl.toFixed(2)}`}
                      tom={d.pnl >= 0 ? "ok" : "block"}
                      size="sm"
                    />
                    <span style={{ fontSize: "9px", color: "var(--inst-faint)" }}>({d.n} ops)</span>
                  </div>
                ))}
              </div>
            </InstCard>
          </div>
        </>
      )}
    </InstPage>
  );
}
