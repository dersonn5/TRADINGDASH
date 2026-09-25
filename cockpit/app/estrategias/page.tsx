"use client";

import * as React from "react";
import Link from "next/link";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import { listarTradesDoMes, getDataSaoPaulo, TradeHistorico } from "@/lib/copa-db";
import { calcularRTrade, calcularRiscoTrade, formatarBRL, formatarR, media, somar } from "@/lib/metricas";
import { CARD, LBL, H2 } from "@/components/v2/estilos";

// Espelho de design/v2/Estrategias.dc.html.

const TAG: Record<string, string> = { varrida_barra_10: "SETUP C", continuidade_tendencia: "SETUP B", reversao_htf: "SETUP A" };
const NOME: Record<string, string> = {
  varrida_barra_10: "Varrida da Barra das 10",
  continuidade_tendencia: "Continuidade de Tendência",
  reversao_htf: "Reversão HTF",
};
const STATUS: Record<string, string> = { EM_CALIBRACAO: "Em calibração", NAO_CALIBRADO: "Não calibrado", CALIBRADO: "Calibrado" };
const ORDEM = ["varrida_barra_10", "continuidade_tendencia", "reversao_htf"];

export default function EstrategiasPage() {
  const estrategias = ORDEM.map((id) => DEFAULT_STRATEGIES.find((s) => s.id === id)).filter(Boolean) as typeof DEFAULT_STRATEGIES;
  const [selId, setSelId] = React.useState(estrategias[0]?.id ?? "");
  const [trades, setTrades] = React.useState<TradeHistorico[]>([]);

  React.useEffect(() => {
    const [ano, mes] = getDataSaoPaulo().split("-").map(Number);
    listarTradesDoMes(ano, mes).then(setTrades).catch(() => setTrades([]));
  }, []);

  const doMes = (id: string) => {
    const ts = trades.filter((t) => t.strategy_id === id);
    const rs = ts.map((t) => calcularRTrade(Number(t.pontos_real ?? 0), calcularRiscoTrade(Number(t.entrada), Number(t.stop))));
    const pnl = somar(ts.map((t) => Number(t.pnl_real ?? 0)));
    const rm = media(rs);
    return { n: ts.length, rm: ts.length ? formatarR(rm) : "—", pnl: ts.length ? formatarBRL(pnl) : "—", cor: pnl >= 0 ? "var(--actx)" : "var(--negtx)" };
  };

  const d = estrategias.find((s) => s.id === selId) ?? estrategias[0];
  const kills = d.checklist.filter((i) => i.tipo === "KILL");
  const pontos = d.checklist.filter((i) => i.tipo === "PONTO");
  const maxPeso = Math.max(1, ...pontos.map((p) => p.peso));
  const horario = d.horarios_validos?.length ? `${d.horarios_validos[0].inicio} – ${d.horarios_validos[d.horarios_validos.length - 1].fim}` : "10:00 – 11:30";
  const fatos = [
    { l: "Mercado", v: d.mercado.join(" · ") || "WIN" },
    { l: "Entrada", v: horario },
    { l: "Score mínimo", v: `${d.score_minimo} · ${d.score_minimo + 15} depois das 11h` },
    { l: "Limites", v: "3 perdas · 5 operações" },
  ];

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Os três setups do trade system · regras vigentes</span>
        <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Estratégias</h1>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "20px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {estrategias.map((e) => {
            const sel = e.id === d.id;
            const m = doMes(e.id);
            return (
              <button
                key={e.id}
                type="button"
                aria-pressed={sel}
                onClick={() => setSelId(e.id)}
                style={{
                  textAlign: "left", padding: "20px", borderRadius: "16px", cursor: "pointer", fontFamily: "inherit",
                  display: "flex", flexDirection: "column", gap: "12px", color: "var(--tx)",
                  background: sel ? "var(--acs)" : "var(--s1)", border: `1px solid ${sel ? "var(--ac)" : "var(--bd)"}`,
                }}
              >
                <span style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 600, letterSpacing: "0.06em", color: sel ? "var(--actx)" : "var(--tx3)" }}>{TAG[e.id]}</span>
                  <span style={{ height: "24px", padding: "0 10px", borderRadius: "999px", display: "inline-flex", alignItems: "center", fontSize: "11px", fontWeight: 600, background: "var(--s2)", color: "var(--tx2)" }}>
                    {STATUS[e.calibracao?.status ?? ""] ?? "Não calibrado"}
                  </span>
                </span>
                <span style={{ fontSize: "17px", fontWeight: 600 }}>{NOME[e.id] ?? e.nome}</span>
                <span style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "8px", paddingTop: "12px", borderTop: "1px solid var(--bd)" }}>
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>Trades</span>
                    <span style={{ fontSize: "15px", fontWeight: 600 }}>{m.n}</span>
                  </span>
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>R médio</span>
                    <span style={{ fontSize: "15px", fontWeight: 600, color: m.n ? m.cor : "var(--tx3)" }}>{m.rm}</span>
                  </span>
                  <span style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>Mês</span>
                    <span style={{ fontSize: "15px", fontWeight: 600, color: m.n ? m.cor : "var(--tx3)" }}>{m.pnl}</span>
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <span style={LBL}>{TAG[d.id]}</span>
                <span style={{ fontSize: "24px", fontWeight: 600, letterSpacing: "-0.01em" }}>{NOME[d.id] ?? d.nome}</span>
              </div>
              <Link href="/checklist" style={{ height: "44px", padding: "0 18px", borderRadius: "12px", display: "flex", alignItems: "center", fontSize: "14px", fontWeight: 600, textDecoration: "none", background: "var(--ac)", color: "var(--onac)", flexShrink: 0 }}>
                Abrir checklist
              </Link>
            </div>
            <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.6, color: "var(--tx2)" }}>{d.descricao}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "12px" }}>
              {fatos.map((f) => (
                <div key={f.l} style={{ padding: "14px 16px", borderRadius: "12px", background: "var(--bg)", border: "1px solid var(--bd)", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "11px", color: "var(--tx3)" }}>{f.l}</span>
                  <span style={{ fontSize: "14px", fontWeight: 600 }}>{f.v}</span>
                </div>
              ))}
            </div>
          </section>

          <div style={{ display: "grid", gridTemplateColumns: "1.15fr 1fr", gap: "20px", alignItems: "start" }}>
            <section style={CARD}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span style={LBL}>Obrigatórios · em ordem</span>
                <span style={H2}>Todos precisam estar cumpridos</span>
              </div>
              {kills.map((k, i) => (
                <div key={k.id} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "12px 0", borderTop: "1px solid var(--bd)" }}>
                  <span style={{ width: "26px", height: "26px", flexShrink: 0, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 600, background: "var(--acs)", color: "var(--actx)" }}>{i + 1}</span>
                  <span style={{ fontSize: "14px", lineHeight: 1.45 }}>{k.label}</span>
                </div>
              ))}
            </section>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <section style={CARD}>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <span style={LBL}>Pontos de qualidade</span>
                  <span style={H2}>Somam {somar(pontos.map((p) => p.peso))} · mínimo {d.score_minimo}</span>
                </div>
                {pontos.map((p) => (
                  <div key={p.id} style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "10px 0", borderTop: "1px solid var(--bd)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", fontSize: "13px" }}>
                      <span style={{ lineHeight: 1.4 }}>{p.label}</span>
                      <span style={{ fontWeight: 600, color: "var(--actx)" }}>{p.peso}</span>
                    </div>
                    <svg width="100%" height="6" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true">
                      <rect x="0" y="0" width="100" height="6" rx="3" style={{ fill: "var(--s2)" }} />
                      <rect x="0" y="0" width={(p.peso / maxPeso) * 100} height="6" rx="3" style={{ fill: "var(--k1)" }} />
                    </svg>
                  </div>
                ))}
              </section>

              <section style={{ padding: "20px 24px", borderRadius: "16px", background: "var(--acs)", border: "1px solid var(--bd)", display: "flex", flexDirection: "column", gap: "8px" }}>
                <span style={LBL}>Calibração</span>
                <span style={{ fontSize: "13px", lineHeight: 1.55 }}>{d.calibracao?.observacao || "Sem amostra suficiente para calibrar. Pesos estimados."}</span>
              </section>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
