"use client";

import * as React from "react";
import Link from "next/link";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstBadge,
  InstNum,
  InstDivider,
} from "@/components/inst";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  Flame,
  Target,
  ArrowRight,
} from "lucide-react";

export default function EstrategiasTradingPage() {
  const [selectedId, setSelectedId] = React.useState<string>("playbook_anderson");
  const strategies = DEFAULT_STRATEGIES;
  const currentStrategy = strategies.find((s) => s.id === selectedId) || strategies[0];

  const kills = currentStrategy.checklist.filter((i) => i.tipo === "KILL");
  const pontos = currentStrategy.checklist.filter((i) => i.tipo === "PONTO");
  const somaPesos = pontos.reduce((acc, p) => acc + p.peso, 0);

  return (
    <InstPage
      eyebrow="PLAYBOOKS · COGNITIVO"
      title="Estratégias & Playbooks Validados"
      right={
        <Link href="/checklist">
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
      }
    >
      {/* Top Header */}
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Parâmetros mecânicos, condições de ambiente e regras de execução de cada modelo institucional.
      </div>

      {/* Tabs / Seletor de Estratégias */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
        {strategies.map((strat) => {
          const isSelected = strat.id === selectedId;
          return (
            <div
              key={strat.id}
              onClick={() => setSelectedId(strat.id)}
              style={{
                borderRadius: "3px",
                border: isSelected ? "1px solid var(--inst-ok)" : "1px solid var(--inst-line)",
                background: isSelected ? "var(--inst-panel-2)" : "var(--inst-panel)",
                padding: "14px 16px",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                transition: "border-color 0.15s ease",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--inst-text)" }}>{strat.nome}</span>
                <div style={{ display: "flex", gap: "4px" }}>
                  {strat.mercado.map((m) => (
                    <InstBadge key={m} tom="neutro">
                      {m}
                    </InstBadge>
                  ))}
                </div>
              </div>
              <div style={{ fontSize: "11px", color: "var(--inst-dim)", lineHeight: 1.4 }}>
                {strat.descricao}
              </div>
              <div
                className="mono tabular"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: "auto",
                  paddingTop: "8px",
                  borderTop: "1px solid var(--inst-line-2)",
                  fontSize: "11px",
                }}
              >
                <span style={{ color: "var(--inst-dim)" }}>
                  Score Mín:{" "}
                  <b style={{ color: "var(--inst-text)" }}>
                    <InstNum value={`${strat.score_minimo} pts`} size="sm" />
                  </b>
                </span>
                <span style={{ color: "var(--inst-ok)", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
                  {strat.checklist.length} itens <ArrowRight style={{ width: "12px", height: "12px" }} />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detalhes da Estratégia Selecionada */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span style={{ fontSize: "18px", fontWeight: 700, letterSpacing: "-0.015em", color: "var(--inst-text)" }}>
                  {currentStrategy.nome}
                </span>
                <InstBadge tom="neutro">{currentStrategy.id}</InstBadge>
              </div>
              <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "6px", maxWidth: "800px", lineHeight: 1.5 }}>
                {currentStrategy.descricao}
              </div>
            </div>

            <Link href={`/copa/novo?strategy=${currentStrategy.id}`}>
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
                  flexShrink: 0,
                }}
              >
                <Play style={{ width: "14px", height: "14px" }} /> Iniciar com este Playbook
              </button>
            </Link>
          </div>

          {/* Parâmetros e Horários */}
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
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <Clock style={{ width: "13px", height: "13px", color: "var(--inst-dim)" }} />
              <span>Janela de Operação:</span>{" "}
              <b style={{ color: "var(--inst-text)" }}>
                {currentStrategy.horarios_validos.map((h) => `${h.inicio} às ${h.fim}`).join(", ")}
              </b>
            </div>
            <div style={{ color: "var(--inst-lock)" }}>•</div>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <Target style={{ width: "13px", height: "13px", color: "var(--inst-ok)" }} />
              <span>Score Mínimo:</span>{" "}
              <b style={{ color: "var(--inst-text)" }}>
                <InstNum value={`${currentStrategy.score_minimo} pontos`} size="sm" />
              </b>
            </div>
          </div>

          <InstDivider />

          {/* Ambientes Favoráveis e Desfavoráveis */}
          {currentStrategy.ambiente_favoravel && currentStrategy.ambiente_favoravel.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
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
                    Ambiente Ideal (Edge Institucional Alto)
                  </span>
                </div>
                <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--inst-text)", lineHeight: 1.6, display: "flex", flexDirection: "column", gap: "4px" }}>
                  {currentStrategy.ambiente_favoravel.map((cond, i) => (
                    <li key={i}>{cond}</li>
                  ))}
                </ul>
              </div>

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
                    Ambiente Tóxico (Evitar / Abortar Ordem)
                  </span>
                </div>
                <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "var(--inst-text)", lineHeight: 1.6, display: "flex", flexDirection: "column", gap: "4px" }}>
                  {currentStrategy.ambiente_desfavoravel.map((cond, i) => (
                    <li key={i}>{cond}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Checklist Detalhado */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "4px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Flame style={{ width: "14px", height: "14px", color: "var(--inst-ok)" }} />
              <InstLabel>Critérios de Validação & Pontuação (Total de Confluências: {somaPesos} pts)</InstLabel>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              {/* Itens KILL */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: "6px", borderBottom: "1px solid var(--inst-line-2)" }}>
                  <span className="mono" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--inst-block)" }}>
                    Itens Mandatórios (KILL)
                  </span>
                  <span className="mono tabular" style={{ fontSize: "10px", fontWeight: 700, color: "var(--inst-block)" }}>
                    {kills.length} obrigatórios
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
                    Itens de Confluência (PONTOS)
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
    </InstPage>
  );
}
