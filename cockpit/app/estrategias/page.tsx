"use client";

import * as React from "react";
import Link from "next/link";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import {
  CheckCircle2,
  XCircle,
  Play,
} from "lucide-react";

export default function EstrategiasTradingPage() {
  const [selectedId, setSelectedId] = React.useState<string>("playbook_anderson");
  const strategies = DEFAULT_STRATEGIES;
  const currentStrategy = strategies.find((s) => s.id === selectedId) || strategies[0];

  const kills = currentStrategy.checklist.filter((i) => i.tipo === "KILL");
  const pontos = currentStrategy.checklist.filter((i) => i.tipo === "PONTO");
  const somaPesos = pontos.reduce((acc, p) => acc + p.peso, 0);

  return (
    <div className="-m-4 md:-m-6 px-6 md:px-10 pt-8 pb-10" style={{ display: "flex", flexDirection: "column", gap: "20px", color: "var(--tx)" }}>
      {/* Cabeçalho v2 */}
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Os três setups do trade system · regras vigentes</span>
        <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Estratégias</h1>
      </div>      {/* Layout grid v2: lista de estratégias (340px) + detalhe */}
      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "20px", alignItems: "start" }}>
        {/* Lista de cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {strategies.map((strat) => {
            const isSelected = strat.id === selectedId;
            return (
              <button
                key={strat.id}
                type="button"
                aria-pressed={isSelected}
                onClick={() => setSelectedId(strat.id)}
                style={{
                  textAlign: "left",
                  padding: "20px",
                  borderRadius: "16px",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  color: "var(--tx)",
                  background: isSelected ? "var(--acs)" : "var(--s1)",
                  border: `1px solid ${isSelected ? "var(--ac)" : "var(--bd)"}`,
                  transition: "all 0.15s",
                }}
              >
                <span style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 600, letterSpacing: "0.06em", color: isSelected ? "var(--actx)" : "var(--tx3)" }}>
                    {strat.mercado.join(" · ")}
                  </span>
                  <span
                    style={{
                      height: "24px",
                      padding: "0 10px",
                      borderRadius: "999px",
                      display: "inline-flex",
                      alignItems: "center",
                      fontSize: "11px",
                      fontWeight: 600,
                      background: "var(--s1)",
                      color: "var(--tx2)",
                      border: "1px solid var(--bd)",
                    }}
                  >
                    {strat.checklist.length} itens
                  </span>
                </span>
                <span style={{ fontSize: "17px", fontWeight: 600 }}>{strat.nome}</span>
                <span
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                    gap: "8px",
                    paddingTop: "12px",
                    borderTop: `1px solid ${isSelected ? "rgba(34,211,238,0.2)" : "var(--bd)"}`,
                  }}
                >
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>KILLs</span>
                    <span style={{ fontSize: "15px", fontWeight: 600 }}>{strat.checklist.filter((i) => i.tipo === "KILL").length}</span>
                  </span>
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>Score mín</span>
                    <span style={{ fontSize: "15px", fontWeight: 600, color: isSelected ? "var(--actx)" : "var(--tx)" }}>{strat.score_minimo} pts</span>
                  </span>
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>Pontos</span>
                    <span style={{ fontSize: "15px", fontWeight: 600, color: isSelected ? "var(--actx)" : "var(--tx)" }}>{strat.checklist.filter((i) => i.tipo === "PONTO").reduce((a, p) => a + p.peso, 0)} pts</span>
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        {/* Painel de detalhe */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section
            style={{
              padding: "24px",
              borderRadius: "16px",
              background: "var(--s1)",
              border: "1px solid var(--bd)",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 500,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: "var(--tx3)",
                  }}
                >
                  {currentStrategy.mercado.join(" · ")}
                </span>
                <span style={{ fontSize: "24px", fontWeight: 600, letterSpacing: "-0.01em" }}>
                  {currentStrategy.nome}
                </span>
              </div>
              <Link href="/checklist">
                <button
                  type="button"
                  style={{
                    height: "44px",
                    padding: "0 18px",
                    borderRadius: "12px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    fontSize: "14px",
                    fontWeight: 600,
                    textDecoration: "none",
                    background: "var(--ac)",
                    color: "var(--onac)",
                    border: 0,
                    fontFamily: "inherit",
                    cursor: "pointer",
                    flexShrink: 0,
                  }}
                >
                  <Play style={{ width: "14px", height: "14px" }} />
                  Abrir checklist
                </button>
              </Link>
            </div>

            <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.6, color: "var(--tx2)" }}>
              {currentStrategy.descricao}
            </p>

            {/* Fatos rápidos */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "12px" }}>
              {[
                { l: "Janela", v: currentStrategy.horarios_validos.map((h) => `${h.inicio}–${h.fim}`).join(", ") },
                { l: "Score mín", v: `${currentStrategy.score_minimo} pts` },
                { l: "KILLs", v: String(kills.length) },
                { l: "Pontos máx", v: `${somaPesos} pts` },
              ].map((f) => (
                <div
                  key={f.l}
                  style={{
                    padding: "14px 16px",
                    borderRadius: "12px",
                    background: "var(--bg)",
                    border: "1px solid var(--bd)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <span style={{ fontSize: "11px", color: "var(--tx3)" }}>{f.l}</span>
                  <span style={{ fontSize: "14px", fontWeight: 600 }}>{f.v}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Ambientes e KILLs + Pontos */}
          {currentStrategy.ambiente_favoravel && currentStrategy.ambiente_favoravel.length > 0 && (
            <section
              style={{
                padding: "24px",
                borderRadius: "16px",
                background: "var(--s1)",
                border: "1px solid var(--bd)",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 500,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  color: "var(--tx3)",
                }}
              >
                Ambiente
              </span>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "12px",
                    background: "var(--acs)",
                    border: "1px solid var(--ac)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--actx)" }}>
                    <CheckCircle2 style={{ width: "12px", height: "12px", display: "inline", marginRight: "6px" }} />
                    Ambiente ideal
                  </span>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--tx2)", lineHeight: 1.6 }}>
                    {currentStrategy.ambiente_favoravel.map((cond, i) => (
                      <li key={i}>{cond}</li>
                    ))}
                  </ul>
                </div>
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "12px",
                    background: "var(--s1)",
                    border: "1px solid var(--bd)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--tx3)" }}>
                    <XCircle style={{ width: "12px", height: "12px", display: "inline", marginRight: "6px" }} />
                    Evitar
                  </span>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--tx2)", lineHeight: 1.6 }}>
                    {currentStrategy.ambiente_desfavoravel.map((cond, i) => (
                      <li key={i}>{cond}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
          )}

          <section
            style={{
              padding: "24px",
              borderRadius: "16px",
              background: "var(--s1)",
              border: "1px solid var(--bd)",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <span
              style={{
                fontSize: "12px",
                fontWeight: 500,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "var(--tx3)",
              }}
            >
              Critérios de validação
            </span>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {/* KILLs */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    paddingBottom: "6px",
                    borderBottom: "1px solid var(--bd)",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--neg, var(--tx2))" }}>Mandatórios (KILL)</span>
                  <span style={{ fontSize: "11px", color: "var(--tx3)" }}>{kills.length} itens</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {kills.map((k) => (
                    <div
                      key={k.id}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "10px",
                        background: "var(--bg)",
                        border: "1px solid var(--bd)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600 }}>{k.label}</span>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: "999px",
                            background: "var(--s1)",
                            color: "var(--tx3)",
                            border: "1px solid var(--bd)",
                          }}
                        >
                          KILL
                        </span>
                      </div>
                      {k.ajuda && <div style={{ fontSize: "11px", color: "var(--tx3)", lineHeight: 1.4 }}>{k.ajuda}</div>}
                    </div>
                  ))}
                </div>
              </div>
              {/* PONTOs */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    paddingBottom: "6px",
                    borderBottom: "1px solid var(--bd)",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--actx)" }}>Confluncias (PONTOS)</span>
                  <span style={{ fontSize: "11px", color: "var(--tx3)" }}>{pontos.length} itens ({somaPesos} pts)</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {pontos.map((p) => (
                    <div
                      key={p.id}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "10px",
                        background: "var(--bg)",
                        border: "1px solid var(--bd)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600 }}>{p.label}</span>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: "999px",
                            background: "var(--acs)",
                            color: "var(--actx)",
                            border: "1px solid var(--ac)",
                          }}
                        >
                          +{p.peso} pts
                        </span>
                      </div>
                      {p.ajuda && <div style={{ fontSize: "11px", color: "var(--tx3)", lineHeight: 1.4 }}>{p.ajuda}</div>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
