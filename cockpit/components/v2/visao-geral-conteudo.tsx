"use client";

import * as React from "react";
import { NOMES_COMPLETOS } from "@/lib/metricas";
import type { VisaoGeral } from "@/lib/visao-geral";
import { CARD, LBL, H2, PILL_PEQUENA } from "@/components/v2/estilos";

// Corpo da Visao Geral — espelho de design/v2/Main.dc.html.

function Cabecalho({ label, frase, direita }: { label: string; frase: React.ReactNode; direita?: React.ReactNode }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={LBL}>{label}</span>
        <span style={H2}>{frase}</span>
      </div>
      {direita}
    </div>
  );
}

function AmostraPequena() {
  return <span style={PILL_PEQUENA}>amostra pequena</span>;
}

const CONFIG_SERIES = [
  { id: "Total", label: "Total", cor: "var(--tx)", dash: undefined, dot: true },
  { id: "C", stratId: "varrida_barra_10", label: "MAV", cor: "var(--strat-c)", dash: undefined, dot: false },
  { id: "B", stratId: "continuidade_tendencia", label: "CSI", cor: "var(--strat-b)", dash: "6 3", dot: false },
  { id: "A", stratId: "primeira_perna", label: "RPP", cor: "var(--strat-a)", dash: "2 4", dot: false },
  { id: "R", stratId: "reversao_htf", label: "RHT", cor: "var(--k5)", dash: "8 3 2 3", dot: false },
];

const MAPA_ESTRAT: Record<string, { serieId: string; tag: string; cor: string }> = {
  varrida_barra_10: { serieId: "C", tag: "MAV", cor: "var(--strat-c)" },
  continuidade_tendencia: { serieId: "B", tag: "CSI", cor: "var(--strat-b)" },
  primeira_perna: { serieId: "A", tag: "RPP", cor: "var(--strat-a)" },
  reversao_htf: { serieId: "R", tag: "RHT", cor: "var(--k5)" },
};

export function VisaoGeralConteudo({ vg }: { vg: VisaoGeral }) {
  const [highlightSerie, setHighlightSerie] = React.useState<string | null>(null);

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: "14px", padding: "16px 20px", borderRadius: "14px", background: "var(--acs)", border: "1px solid var(--bd)" }}>
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0, fill: "none", stroke: "var(--actx)", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" }}>
          <path d="M3 17l6-6 4 4 8-8" />
          <path d="M15 7h6v6" />
        </svg>
        <span style={{ fontSize: "15px", lineHeight: 1.5 }}>{vg.resumo}</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: "16px" }}>
        {vg.kpis.map((k) => (
          <div key={k.label} style={{ padding: "20px", borderRadius: "16px", background: "var(--s1)", border: "1px solid var(--bd)", display: "flex", flexDirection: "column", gap: "8px" }}>
            <span style={LBL}>{k.label}</span>
            <span style={{ fontSize: "28px", fontWeight: 600, letterSpacing: "-0.02em", color: k.cor }}>{k.valor}</span>
            <span style={{ fontSize: "13px", color: "var(--tx2)" }}>{k.sub}</span>
            <span style={{ marginTop: "4px", paddingTop: "10px", borderTop: "1px solid var(--bd)", fontSize: "12px", color: "var(--tx3)" }}>{k.delta}</span>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
        <section style={CARD}>
          <Cabecalho
            label="Curva de capital"
            frase={vg.curva.frase}
            direita={
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end", fontSize: "12px" }}>
                {CONFIG_SERIES.map((s) => {
                  const ativo = highlightSerie === s.id;
                  const apagado = highlightSerie !== null && !ativo;
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onMouseEnter={() => setHighlightSerie(s.id)}
                      onMouseLeave={() => setHighlightSerie(null)}
                      onClick={() => setHighlightSerie(highlightSerie === s.id ? null : s.id)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        background: ativo ? "var(--s2)" : "transparent",
                        border: `1px solid ${ativo ? s.cor : "transparent"}`,
                        borderRadius: "6px",
                        padding: "3px 8px",
                        cursor: "pointer",
                        fontFamily: "inherit",
                        fontSize: "12px",
                        color: apagado ? "var(--tx3)" : "var(--tx2)",
                        opacity: apagado ? 0.4 : 1,
                        transition: "all 0.15s ease",
                      }}
                      title={ativo ? "Clique para desmarcar foco" : `Destacar ${s.label}`}
                    >
                      <svg width="20" height="10" viewBox="0 0 20 10" style={{ display: "block", flexShrink: 0 }} aria-hidden="true">
                        <line
                          x1="0"
                          y1="5"
                          x2="20"
                          y2="5"
                          stroke={s.cor}
                          strokeWidth={s.id === "Total" ? 2.5 : 2}
                          strokeDasharray={s.dash}
                          strokeLinecap="round"
                        />
                        {s.dot && <circle cx="10" cy="5" r="2.5" fill="var(--bg)" stroke={s.cor} strokeWidth="1.8" />}
                      </svg>
                      <span style={{ fontWeight: ativo ? 600 : 400, color: ativo ? "var(--tx)" : undefined }}>
                        {s.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            }
          />
          <svg width="100%" viewBox={vg.curva.vb} role="img" aria-label="Curva de capital do mês" style={{ display: "block" }}>
            {vg.curva.temDD && (
              <>
                <rect x={vg.curva.ddx} y={vg.curva.ddy} width={vg.curva.ddw} height={vg.curva.ddh} rx="6" style={{ fill: "var(--neg)", fillOpacity: 0.14 }} />
                <text x={vg.curva.ddlx} y={vg.curva.ddty} textAnchor="middle" style={{ fill: "var(--negtx)", fontSize: "11px", fontWeight: 600 }}>{vg.curva.ddTxt}</text>
              </>
            )}
            {vg.curva.ticks.map((t) => (
              <g key={t.y}>
                <line x1={vg.curva.x0} x2={vg.curva.x1} y1={t.y} y2={t.y} style={{ stroke: "var(--ln)", strokeWidth: 1 }} />
                <text x={vg.curva.lx} y={t.yt} textAnchor="end" style={{ fill: "var(--tx3)", fontSize: "11px" }}>{t.label}</text>
              </g>
            ))}
            <path
              d={vg.curva.area}
              style={{
                fill: "var(--ac)",
                fillOpacity: highlightSerie && highlightSerie !== "Total" ? 0.03 : 0.08,
                transition: "fill-opacity 0.2s ease",
              }}
            />
            <path
              d={vg.curva.R}
              style={{
                fill: "none",
                stroke: "var(--k5)",
                strokeWidth: highlightSerie === "R" ? 2.8 : 1.8,
                strokeDasharray: "8 3 2 3",
                strokeLinecap: "round",
                opacity: highlightSerie && highlightSerie !== "R" ? 0.2 : 1,
                transition: "opacity 0.2s ease, stroke-width 0.2s ease",
              }}
            />
            <path
              d={vg.curva.A}
              style={{
                fill: "none",
                stroke: "var(--strat-a)",
                strokeWidth: highlightSerie === "A" ? 2.8 : 1.8,
                strokeDasharray: "2 4",
                strokeLinecap: "round",
                opacity: highlightSerie && highlightSerie !== "A" ? 0.2 : 1,
                transition: "opacity 0.2s ease, stroke-width 0.2s ease",
              }}
            />
            <path
              d={vg.curva.B}
              style={{
                fill: "none",
                stroke: "var(--strat-b)",
                strokeWidth: highlightSerie === "B" ? 2.8 : 1.8,
                strokeDasharray: "6 3",
                strokeLinecap: "round",
                opacity: highlightSerie && highlightSerie !== "B" ? 0.2 : 1,
                transition: "opacity 0.2s ease, stroke-width 0.2s ease",
              }}
            />
            <path
              d={vg.curva.C}
              style={{
                fill: "none",
                stroke: "var(--strat-c)",
                strokeWidth: highlightSerie === "C" ? 3.0 : 2.0,
                opacity: highlightSerie && highlightSerie !== "C" ? 0.2 : 1,
                transition: "opacity 0.2s ease, stroke-width 0.2s ease",
              }}
            />
            <path
              d={vg.curva.d}
              style={{
                fill: "none",
                stroke: "var(--tx)",
                strokeWidth: highlightSerie === "Total" ? 3.2 : 2.4,
                strokeLinejoin: "round",
                opacity: highlightSerie && highlightSerie !== "Total" ? 0.35 : 1,
                transition: "opacity 0.2s ease, stroke-width 0.2s ease",
              }}
            />
            <circle
              cx={vg.curva.endx}
              cy={vg.curva.endy}
              r={highlightSerie === "Total" ? 6 : 5}
              style={{
                fill: "var(--bg)",
                stroke: "var(--tx)",
                strokeWidth: 2.4,
                opacity: highlightSerie && highlightSerie !== "Total" ? 0.35 : 1,
                transition: "all 0.2s ease",
              }}
            />
            {vg.curva.xl.map((x) => (
              <text key={x.x} x={x.x} y={vg.curva.xly} textAnchor={x.anchor} style={{ fill: "var(--tx3)", fontSize: "11px" }}>{x.label}</text>
            ))}
          </svg>
        </section>

        <section style={{ ...CARD, gap: "20px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <span style={LBL}>Por estratégia</span>
            <span style={{ ...H2, lineHeight: 1.4 }}>{vg.estrFrase}</span>
          </div>
          {vg.estr.map((e) => {
            const meta = MAPA_ESTRAT[e.id] ?? { serieId: "C", tag: "SETUP", cor: "var(--strat-c)" };
            const isRowHighlighted = highlightSerie === meta.serieId;
            return (
              <div
                key={e.id}
                onMouseEnter={() => setHighlightSerie(meta.serieId)}
                onMouseLeave={() => setHighlightSerie(null)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  paddingTop: "16px",
                  borderTop: "1px solid var(--bd)",
                  cursor: "pointer",
                  borderRadius: "8px",
                  padding: "12px 8px 4px 8px",
                  background: isRowHighlighted ? "var(--s2)" : "transparent",
                  transition: "background 0.15s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: 0 }}>
                    <span
                      style={{
                        flexShrink: 0,
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "var(--s2)",
                        color: meta.cor,
                        border: `1px solid ${meta.cor}`,
                        letterSpacing: "0.04em",
                      }}
                    >
                      {meta.tag}
                    </span>
                    <span style={{ fontSize: "14px", fontWeight: isRowHighlighted ? 600 : 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={NOMES_COMPLETOS[e.id] ?? e.nome}>{NOMES_COMPLETOS[e.id] ?? e.nome}</span>
                  </div>
                  <span style={{ flexShrink: 0, whiteSpace: "nowrap", fontSize: "15px", fontWeight: 600, color: e.cor }}>{e.pnlTxt}</span>
                </div>
                <svg width="100%" height="8" viewBox="0 0 300 8" preserveAspectRatio="none" aria-hidden="true">
                  <rect x="0" y="0" width="300" height="8" rx="4" style={{ fill: "var(--s2)" }} />
                  <rect x="0" y="0" width={e.wN} height="8" rx="4" style={{ fill: meta.cor }} />
                </svg>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--tx2)" }}>
                  <span>{e.nTxt} · {e.acerto} acerto</span>
                  <span style={{ color: e.rmCor }}>{e.rm} médio</span>
                </div>
              </div>
            );
          })}
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "20px" }}>
        <section style={CARD}>
          <Cabecalho label="Por horário de entrada" frase={vg.hora.frase} direita={vg.hora.pequena ? <AmostraPequena /> : null} />
          <svg width="100%" viewBox="0 0 504 220" role="img" aria-label="R médio por faixa de 15 minutos" style={{ display: "block" }}>
            <line x1="36" x2="504" y1={vg.hora.y0} y2={vg.hora.y0} style={{ stroke: "var(--bd)", strokeWidth: 1 }} />
            <text x="30" y={vg.hora.yTop} textAnchor="end" style={{ fill: "var(--tx3)", fontSize: "11px" }}>{vg.hora.topTxt}</text>
            <text x="30" y={vg.hora.y0t} textAnchor="end" style={{ fill: "var(--tx3)", fontSize: "11px" }}>0</text>
            <text x="30" y={vg.hora.yBot} textAnchor="end" style={{ fill: "var(--tx3)", fontSize: "11px" }}>{vg.hora.botTxt}</text>
            {vg.hora.bars.map((b) => (
              <g key={b.f}>
                <rect x={b.x} y={b.y} width="44" height={b.h} rx="6" style={{ fill: b.fill }} />
                <text x={b.cx} y={b.vy} textAnchor="middle" style={{ fill: "var(--tx)", fontSize: "12px", fontWeight: 600 }}>{b.val}</text>
                <text x={b.cx} y="196" textAnchor="middle" style={{ fill: "var(--tx2)", fontSize: "12px" }}>{b.f}</text>
                <text x={b.cx} y="213" textAnchor="middle" style={{ fill: "var(--k1)", fontSize: "11px" }}>{b.nTxt}</text>
              </g>
            ))}
          </svg>
        </section>

        <section style={CARD}>
          <Cabecalho label="Gatilhos" frase={vg.gat.frase} />
          <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
            <svg width="184" height="184" viewBox="0 0 184 184" role="img" aria-label="Distribuição dos gatilhos" style={{ flexShrink: 0 }}>
              <circle cx="92" cy="92" r="66" style={{ fill: "none", stroke: "var(--s2)", strokeWidth: 20 }} />
              {vg.gat.itens.map((g) => (
                <circle key={g.nome} cx="92" cy="92" r="66" transform="rotate(-90 92 92)" strokeDasharray={g.dash} strokeDashoffset={g.off} style={{ fill: "none", stroke: g.cor, strokeWidth: 20 }} />
              ))}
              <text x="92" y="90" textAnchor="middle" style={{ fill: "var(--tx)", fontSize: "30px", fontWeight: 600 }}>{vg.gat.n}</text>
              <text x="92" y="112" textAnchor="middle" style={{ fill: "var(--tx3)", fontSize: "12px" }}>trades</text>
            </svg>
            <div style={{ flexGrow: 1, display: "flex", flexDirection: "column", gap: "12px" }}>
              {vg.gat.itens.map((g) => (
                <div key={g.nome} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
                  <span style={{ width: "10px", height: "10px", borderRadius: "3px", flexShrink: 0, background: g.cor }} />
                  <span style={{ flexGrow: 1 }}>{g.nome}</span>
                  <span style={{ width: "56px", textAlign: "right", color: "var(--tx2)" }}>{g.n} · {g.pct}</span>
                  <span style={{ width: "64px", textAlign: "right", fontWeight: 600, color: g.rmCor }}>{g.rmTxt}</span>
                </div>
              ))}
              <span style={{ fontSize: "11px", color: "var(--tx3)", textAlign: "right" }}>
                quantidade · R médio{vg.gat.semGatilho > 0 ? ` · ${vg.gat.semGatilho} sem gatilho registrado` : ""}
              </span>
            </div>
          </div>
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: "20px" }}>
        <section style={CARD}>
          <Cabecalho label="Estratégias no mês" frase={vg.tabFrase} />
          <div role="table" aria-label="Estratégias no mês" style={{ display: "flex", flexDirection: "column", fontSize: "13px" }}>
            <div role="row" style={{ ...LINHA, paddingBottom: "10px", color: "var(--tx3)", fontSize: "11px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              <span role="columnheader">Estratégia</span>
              {["Trades", "Acerto", "R médio", "Resultado", "DD máx", "Stop med."].map((h) => (
                <span key={h} role="columnheader" style={{ textAlign: "right" }}>{h}</span>
              ))}
            </div>
            {vg.estr.map((e) => (
              <div key={e.id} role="row" style={{ ...LINHA, padding: "14px 0", borderTop: "1px solid var(--bd)" }}>
                <span role="cell" style={{ fontWeight: 500 }}>{e.nome}</span>
                <span role="cell" style={{ textAlign: "right" }}>{e.n}</span>
                <span role="cell" style={{ textAlign: "right", color: "var(--tx2)" }}>{e.acerto}</span>
                <span role="cell" style={{ textAlign: "right", color: e.rmCor }}>{e.rm}</span>
                <span role="cell" style={{ textAlign: "right", fontWeight: 600, color: e.cor }}>{e.pnlTxt}</span>
                <span role="cell" style={{ textAlign: "right", color: "var(--negtx)" }}>{e.dd}</span>
                <span role="cell" style={{ textAlign: "right", color: "var(--tx2)" }}>{e.stop}</span>
              </div>
            ))}
            <div role="row" style={{ ...LINHA, padding: "14px 0", borderTop: "1px solid var(--bd)", color: "var(--tx2)" }}>
              <span role="cell" style={{ fontWeight: 600, color: "var(--tx)" }}>Total</span>
              <span role="cell" style={{ textAlign: "right" }}>{vg.tot.n}</span>
              <span role="cell" style={{ textAlign: "right" }}>{vg.tot.acerto}</span>
              <span role="cell" style={{ textAlign: "right", color: vg.tot.rmCor }}>{vg.tot.rm}</span>
              <span role="cell" style={{ textAlign: "right", fontWeight: 600, color: vg.tot.cor }}>{vg.tot.pnl}</span>
              <span role="cell" style={{ textAlign: "right", color: "var(--negtx)" }}>{vg.tot.dd}</span>
              <span role="cell" style={{ textAlign: "right" }}>{vg.tot.stop}</span>
            </div>
          </div>
        </section>

        <section style={CARD}>
          <Cabecalho label="Tamanho do stop" frase={vg.stops.frase} />
          <svg width="100%" viewBox="0 0 392 200" role="img" aria-label="Distribuição do tamanho dos stops em pontos" style={{ display: "block" }}>
            <line x1="0" x2="392" y1="160" y2="160" style={{ stroke: "var(--bd)", strokeWidth: 1 }} />
            {vg.stops.bars.map((b) => (
              <g key={b.l}>
                <rect x={b.x} y={b.y} width="52" height={b.h} rx="6" style={{ fill: b.fill }} />
                <text x={b.cx} y={b.vy} textAnchor="middle" style={{ fill: "var(--tx)", fontSize: "12px", fontWeight: 600 }}>{b.n}</text>
                <text x={b.cx} y="180" textAnchor="middle" style={{ fill: "var(--tx2)", fontSize: "11px" }}>{b.l}</text>
              </g>
            ))}
            <text x="392" y="198" textAnchor="end" style={{ fill: "var(--tx3)", fontSize: "11px" }}>pontos</text>
          </svg>
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1fr", gap: "20px" }}>
        <section style={CARD}>
          <Cabecalho label="Calendário" frase={vg.cal.frase} />
          <svg width="100%" viewBox={`0 0 380 ${vg.cal.altura}`} role="img" aria-label="Resultado por dia do mês" style={{ display: "block" }}>
            {vg.cal.dow.map((w) => (
              <text key={w.l} x={w.x} y="12" textAnchor="middle" style={{ fill: "var(--tx3)", fontSize: "11px" }}>{w.l}</text>
            ))}
            {vg.cal.cells.map((c) => (
              <g key={`${c.x}-${c.y}`}>
                <rect x={c.x} y={c.y} width="70" height="42" rx="8" style={{ fill: String(c.fill), fillOpacity: Number(c.op), stroke: "var(--bd)", strokeOpacity: Number(c.so) }} />
                <text x={c.tx} y={c.ty} style={{ fill: String(c.dcor), fontSize: "11px" }}>{c.d}</text>
                <text x={c.vx} y={c.vy} textAnchor="end" style={{ fill: "var(--tx)", fontSize: "11px", fontWeight: 600 }}>{c.v}</text>
              </g>
            ))}
          </svg>
        </section>

        <section style={CARD}>
          <Cabecalho label="Disciplina" frase={vg.disc.frase} />
          <div style={{ display: "flex", alignItems: "baseline", gap: "10px" }}>
            <span style={{ fontSize: "40px", fontWeight: 600, letterSpacing: "-0.02em", color: "var(--actx)" }}>{vg.disc.pct}</span>
            <span style={{ fontSize: "13px", color: "var(--tx2)" }}>{vg.disc.sub}</span>
          </div>
          <svg width="100%" height="10" viewBox="0 0 280 10" preserveAspectRatio="none" aria-hidden="true">
            <rect x="0" y="0" width="280" height="10" rx="5" style={{ fill: "var(--neg)", fillOpacity: 0.35 }} />
            <rect x="0" y="0" width={vg.disc.w} height="10" rx="5" style={{ fill: "var(--ac)" }} />
          </svg>
          {vg.disc.itens.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", paddingTop: "12px", borderTop: "1px solid var(--bd)" }}>
              <span style={{ fontSize: "12px", color: "var(--tx3)" }}>Desvios do plano</span>
              {vg.disc.itens.map((d, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                  <span style={{ color: "var(--tx2)" }}>{d.data} · {d.tipo}</span>
                  <span style={{ color: "var(--negtx)", fontWeight: 600 }}>{d.custo}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section style={CARD}>
          <Cabecalho label="MAV e contexto" frase={vg.sc.frase} direita={vg.sc.pequena ? <AmostraPequena /> : null} />
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <span style={{ fontSize: "12px", color: "var(--tx3)", paddingBottom: "4px" }}>Modo da MAV</span>
            {vg.sc.modos.map((m) => (
              <div key={m.nome} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 0", borderTop: "1px solid var(--bd)", fontSize: "13px" }}>
                <span style={{ width: "28px", fontWeight: 600 }}>{m.nome}</span>
                <span style={{ flexGrow: 1, color: "var(--tx2)" }}>{m.n} trades · {m.acerto}</span>
                <span style={{ fontWeight: 600, color: m.cor }}>{m.rm}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <span style={{ fontSize: "12px", color: "var(--tx3)", paddingBottom: "4px" }}>Contexto da 1ª hora (todos os setups)</span>
            {vg.sc.ctx.map((m) => (
              <div key={m.nome} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 0", borderTop: "1px solid var(--bd)", fontSize: "13px" }}>
                <span style={{ flexGrow: 1 }}>{m.nome}</span>
                <span style={{ color: "var(--tx2)" }}>{m.n} trades</span>
                <span style={{ width: "64px", textAlign: "right", fontWeight: 600, color: m.cor }}>{m.rm}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

const LINHA: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1.7fr repeat(6, minmax(0, 1fr))",
  gap: "8px",
  alignItems: "center",
};
