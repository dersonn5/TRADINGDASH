"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, Strategy, StatsPorEstrategia } from "@/lib/copa-api";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstBadge,
  InstNum,
  InstEmpty,
  InstDivider,
} from "@/components/inst";
import {
  CheckCircle2,
  XCircle,
  Play,
} from "lucide-react";

export default function EstrategiasCopaPage() {
  const [strategies, setStrategies] = React.useState<Strategy[]>(DEFAULT_STRATEGIES);
  const [statsStrat, setStatsStrat] = React.useState<StatsPorEstrategia[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    async function load() {
      try {
        const [strats, st] = await Promise.all([
          copaApi.getStrategies().catch(() => DEFAULT_STRATEGIES),
          copaApi.getStats().catch(() => ({ por_estrategia: [] } as any)),
        ]);
        if (strats && strats.length > 0) {
          setStrategies(strats);
        }
        if (st && st.por_estrategia) {
          setStatsStrat(st.por_estrategia);
        }
      } catch (err) {
        console.error("Erro ao carregar estratégias:", err);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <InstPage eyebrow="COPA BTG · ESTRATÉGIAS" title="Fichas Técnicas das Estratégias">
        <InstEmpty>Carregando estratégias...</InstEmpty>
      </InstPage>
    );
  }

  return (
    <InstPage eyebrow="COPA BTG · ESTRATÉGIAS" title="Fichas Técnicas das Estratégias">
      {/* Topo */}
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Modelos validados em arquivo de configuração. Estude os gatilhos, filtros de ambiente e pesos de confluência.
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {strategies.map((strategy) => {
          const stratStat = statsStrat.find((s) => s.strategy_id === strategy.id);
          const kills = strategy.checklist.filter((i) => i.tipo === "KILL");
          const pontos = strategy.checklist.filter((i) => i.tipo === "PONTO");
          const somaPesos = pontos.reduce((acc, p) => acc + p.peso, 0);

          return (
            <InstCard key={strategy.id}>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                      <span style={{ fontSize: "18px", fontWeight: 700, letterSpacing: "-0.015em", color: "var(--inst-text)" }}>
                        {strategy.nome}
                      </span>
                      <InstBadge tom="neutro">{strategy.id}</InstBadge>
                      <div style={{ display: "flex", gap: "4px" }}>
                        {strategy.mercado.map((m) => (
                          <InstBadge key={m} tom="neutro">
                            {m}
                          </InstBadge>
                        ))}
                      </div>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "6px", maxWidth: "800px", lineHeight: 1.5 }}>
                      {strategy.descricao}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
                    <Link href={`/copa/novo?strategy=${strategy.id}`}>
                      <button
                        type="button"
                        className="mono tabular"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          background: "var(--inst-ok)",
                          border: "1px solid var(--inst-ok)",
                          color: "var(--inst-on-ok)",
                          borderRadius: "3px",
                          padding: "6px 14px",
                          fontSize: "11px",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        <Play style={{ width: "14px", height: "14px" }} /> Operar no Checklist
                      </button>
                    </Link>
                  </div>
                </div>

                {/* Parâmetros Rápidos */}
                <div
                  className="mono tabular"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    flexWrap: "wrap",
                    fontSize: "11px",
                    color: "var(--inst-dim)",
                    paddingTop: "4px",
                    borderTop: "1px solid var(--inst-line-2)",
                  }}
                >
                  <div>
                    Score Mínimo:{" "}
                    <span style={{ fontWeight: 700, color: "var(--inst-text)" }}>
                      <InstNum value={`${strategy.score_minimo} pts`} size="sm" />
                    </span>{" "}
                    (Grade A)
                  </div>
                  <div style={{ color: "var(--inst-lock)" }}>•</div>
                  <div>
                    Horários:{" "}
                    <span style={{ fontWeight: 700, color: "var(--inst-text)" }}>
                      {strategy.horarios_validos.map((h) => `${h.inicio}-${h.fim}`).join(", ")}
                    </span>
                  </div>
                  {stratStat && (
                    <>
                      <div style={{ color: "var(--inst-lock)" }}>•</div>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        Winrate Histórico:{" "}
                        <InstNum
                          value={`${stratStat.winrate.toFixed(1)}%`}
                          tom={stratStat.winrate >= 50 ? "ok" : "block"}
                          size="sm"
                        />{" "}
                        ({stratStat.n} trades)
                      </div>
                    </>
                  )}
                </div>

                <InstDivider />

                {/* Ambientes Favoráveis e Desfavoráveis */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
                  {/* Favorável */}
                  <div
                    style={{
                      border: "1px solid var(--inst-ok-line)",
                      background: "var(--inst-ok-bg)",
                      borderRadius: "3px",
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <CheckCircle2 style={{ width: "14px", height: "14px", color: "var(--inst-ok)" }} />
                      <span className="mono" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--inst-ok)" }}>
                        Onde o Modelo Funciona (Edge Alto)
                      </span>
                    </div>
                    <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--inst-text)", lineHeight: 1.6, display: "flex", flexDirection: "column", gap: "4px" }}>
                      {strategy.ambiente_favoravel.map((cond, i) => (
                        <li key={i}>{cond}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Desfavorável */}
                  <div
                    style={{
                      border: "1px solid var(--inst-block-line)",
                      background: "var(--inst-block-bg)",
                      borderRadius: "3px",
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <XCircle style={{ width: "14px", height: "14px", color: "var(--inst-block)" }} />
                      <span className="mono" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--inst-block)" }}>
                        Onde o Modelo Falha (Evitar / Reduzir Risco)
                      </span>
                    </div>
                    <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--inst-text)", lineHeight: 1.6, display: "flex", flexDirection: "column", gap: "4px" }}>
                      {strategy.ambiente_desfavoravel.map((cond, i) => (
                        <li key={i}>{cond}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Checklist Completo */}
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "4px" }}>
                  <InstLabel>Checklist & Critérios de Pontuação (Total: {somaPesos} pts)</InstLabel>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
                    {/* Itens KILL */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: "6px", borderBottom: "1px solid var(--inst-line-2)" }}>
                        <span className="mono" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--inst-block)" }}>
                          Itens KILL (Bloqueiam se faltar)
                        </span>
                        <span className="mono tabular" style={{ fontSize: "10px", fontWeight: 700, color: "var(--inst-block)" }}>
                          {kills.length} itens obrigatórios
                        </span>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {kills.map((k) => (
                          <div
                            key={k.id}
                            style={{
                              borderRadius: "3px",
                              border: "1px solid var(--inst-line-2)",
                              background: "var(--inst-panel-2)",
                              padding: "10px 12px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "4px",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                              <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--inst-text)" }}>{k.label}</span>
                              <InstBadge tom="block">KILL</InstBadge>
                            </div>
                            {k.ajuda && (
                              <div style={{ fontSize: "11px", color: "var(--inst-dim)", lineHeight: 1.4 }}>{k.ajuda}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Itens PONTO */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: "6px", borderBottom: "1px solid var(--inst-line-2)" }}>
                        <span className="mono" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--inst-ok)" }}>
                          Itens PONTO (Confluências)
                        </span>
                        <span className="mono tabular" style={{ fontSize: "10px", fontWeight: 700, color: "var(--inst-ok)" }}>
                          {pontos.length} itens ({somaPesos} pts)
                        </span>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {pontos.map((p) => (
                          <div
                            key={p.id}
                            style={{
                              borderRadius: "3px",
                              border: "1px solid var(--inst-line-2)",
                              background: "var(--inst-panel-2)",
                              padding: "10px 12px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "4px",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                              <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--inst-text)" }}>{p.label}</span>
                              <InstBadge tom="ok">+{p.peso} pts</InstBadge>
                            </div>
                            {p.ajuda && (
                              <div style={{ fontSize: "11px", color: "var(--inst-dim)", lineHeight: 1.4 }}>{p.ajuda}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </InstCard>
          );
        })}
      </div>
    </InstPage>
  );
}
