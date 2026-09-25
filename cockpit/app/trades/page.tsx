"use client";

import * as React from "react";
import Link from "next/link";
import { listarTrades, TradeHistorico } from "@/lib/copa-db";
import {
  NOMES_CONTEXTOS,
  NOMES_ESTRATEGIAS,
  NOMES_GATILHOS,
  formatarBRL,
  temDesvio,
} from "@/lib/metricas";

function hora(iso: string | null) {
  if (!iso) return "";
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function sinalR(r: number) {
  const abs = Math.abs(r).toFixed(1).replace(".", ",");
  if (r > 0) return `+${abs}R`;
  if (r < 0) return `−${abs}R`;
  return "0R";
}

function preco(v: number | null) {
  return v === null || v === undefined ? "—" : Number(v).toLocaleString("pt-BR");
}

function dataCurta(iso: string) {
  const [, m, d] = iso.split("-");
  return d && m ? `${d}/${m}` : iso;
}

const FILTROS = [
  { v: "TODOS", l: "Todos" },
  { v: "reversao_htf", l: "Reversão HTF" },
  { v: "continuidade_tendencia", l: "Continuidade" },
  { v: "varrida_barra_10", l: "Varrida das 10" },
];

export default function HistoricoPage() {
  const [trades, setTrades] = React.useState<TradeHistorico[]>([]);
  const [erro, setErro] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [filtro, setFiltro] = React.useState("TODOS");

  React.useEffect(() => {
    listarTrades()
      .then(setTrades)
      .catch((e) => setErro(e.message))
      .finally(() => setLoading(false));
  }, []);

  const abertos = trades.filter((t) => t.status === "ABERTO");
  const fechados = trades.filter((t) => t.status === "FECHADO");
  const visiveis =
    filtro === "TODOS"
      ? fechados
      : fechados.filter((t) => t.strategy_id === filtro);

  // KPIs
  const totalTrades = visiveis.length;
  const winners = visiveis.filter((t) => (Number(t.pnl_real) || 0) > 0);
  const acerto =
    totalTrades > 0 ? Math.round((winners.length / totalTrades) * 100) : 0;
  const somaR = visiveis.reduce((a, t) => {
    const pts = Number(t.pontos_real) || 0;
    const risk =
      Number(t.stop) && Number(t.entrada)
        ? Math.abs(Number(t.entrada) - Number(t.stop))
        : 1;
    return a + (risk > 0 ? pts / risk : 0);
  }, 0);
  const rMedio = totalTrades > 0 ? somaR / totalTrades : 0;
  const resultado = visiveis.reduce(
    (a, t) => a + (Number(t.pnl_real) || 0),
    0
  );

  const mesTitulo = new Intl.DateTimeFormat("pt-BR", {
    month: "long",
    year: "numeric",
    timeZone: "America/Sao_Paulo",
  }).format(new Date());
  const mesCap = mesTitulo.charAt(0).toUpperCase() + mesTitulo.slice(1);

  return (
    <div
      className="-m-4 md:-m-6 px-6 md:px-10 pt-8 pb-10"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        color: "var(--tx)",
      }}
    >
      {/* Cabeçalho v2 */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: "24px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>
            {mesCap} · trades registrados pelo checklist
          </span>
          <h1
            style={{
              margin: 0,
              fontSize: "30px",
              fontWeight: 600,
              letterSpacing: "-0.02em",
            }}
          >
            Histórico
          </h1>
        </div>
        {/* Filtros pill */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {FILTROS.map((o) => {
            const sel = filtro === o.v;
            return (
              <button
                key={o.v}
                type="button"
                aria-pressed={sel}
                onClick={() => setFiltro(o.v)}
                style={{
                  height: "36px",
                  padding: "0 14px",
                  borderRadius: "999px",
                  fontFamily: "inherit",
                  fontSize: "13px",
                  cursor: "pointer",
                  background: sel ? "var(--ac)" : "transparent",
                  color: sel ? "var(--onac)" : "var(--tx2)",
                  border: `1px solid ${sel ? "var(--ac)" : "var(--bd)"}`,
                  fontWeight: sel ? 600 : 400,
                  transition: "all 0.15s",
                }}
              >
                {o.l}
              </button>
            );
          })}
        </div>
      </div>

      {/* Banner trade aberto */}
      {abertos.length > 0 && (
        <Link
          href="/checklist"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "14px",
            padding: "16px 20px",
            borderRadius: "14px",
            background: "var(--acs)",
            border: "1px solid var(--ac)",
            textDecoration: "none",
            color: "var(--tx)",
          }}
        >
          <span
            style={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              background: "var(--ac)",
              flexShrink: 0,
            }}
          />
          <span style={{ flexGrow: 1, fontSize: "14px" }}>
            <strong style={{ fontWeight: 600 }}>
              {abertos.length} {abertos.length === 1 ? "trade aberto" : "trades abertos"}
            </strong>
            {` · ${hora(abertos[0].hora_entrada)} · ${abertos[0].direcao === "COMPRA" ? "compra" : "venda"} · ${NOMES_ESTRATEGIAS[abertos[0].strategy_id] ?? abertos[0].strategy_id} · entrada ${preco(abertos[0].entrada)}, stop ${preco(abertos[0].stop)}`}
          </span>
          <span
            style={{ fontSize: "13px", fontWeight: 600, color: "var(--actx)" }}
          >
            Fechar no checklist →
          </span>
        </Link>
      )}

      {/* Erro */}
      {erro && (
        <div
          style={{
            padding: "14px 18px",
            borderRadius: "12px",
            background: "var(--s1)",
            border: "1px solid var(--bd)",
            fontSize: "13px",
            color: "var(--tx2)",
          }}
        >
          {erro}
        </div>
      )}

      {/* 4 KPI cards */}
      {!loading && fechados.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: "16px",
          }}
        >
          {[
            { l: "Trades", v: String(totalTrades), cor: "var(--tx)" },
            { l: "Acerto", v: `${acerto}%`, cor: "var(--tx)" },
            {
              l: "R médio",
              v: sinalR(rMedio),
              cor: rMedio >= 0 ? "var(--actx)" : "var(--negtx)",
            },
            {
              l: "Resultado",
              v: formatarBRL(resultado),
              cor: resultado >= 0 ? "var(--actx)" : "var(--negtx)",
            },
          ].map((k) => (
            <div
              key={k.l}
              style={{
                padding: "18px 20px",
                borderRadius: "16px",
                background: "var(--s1)",
                border: "1px solid var(--bd)",
                display: "flex",
                flexDirection: "column",
                gap: "6px",
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
                {k.l}
              </span>
              <span
                style={{ fontSize: "24px", fontWeight: 600, color: k.cor }}
              >
                {k.v}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Tabela v2 */}
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
        {loading ? (
          <div
            style={{
              fontSize: "14px",
              color: "var(--tx3)",
              textAlign: "center",
              padding: "32px 0",
            }}
          >
            Carregando…
          </div>
        ) : fechados.length === 0 ? (
          <div
            style={{
              fontSize: "14px",
              color: "var(--tx3)",
              textAlign: "center",
              padding: "32px 0",
            }}
          >
            Nenhum trade fechado ainda.
          </div>
        ) : visiveis.length === 0 ? (
          <div
            style={{
              fontSize: "14px",
              color: "var(--tx3)",
              textAlign: "center",
              padding: "32px 0",
            }}
          >
            Nenhum trade com esse filtro.
          </div>
        ) : (
          <div
            role="table"
            aria-label="Trades fechados"
            style={{ display: "flex", flexDirection: "column", fontSize: "13px" }}
          >
            {/* Cabeçalho da tabela */}
            <div
              role="row"
              style={{
                display: "grid",
                gridTemplateColumns:
                  "92px 1.3fr 76px 1.1fr 1fr 1.5fr 64px 70px 96px 72px",
                gap: "10px",
                alignItems: "center",
                paddingBottom: "12px",
                color: "var(--tx3)",
                fontSize: "11px",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              <span role="columnheader">Data</span>
              <span role="columnheader">Estratégia</span>
              <span role="columnheader">Lado</span>
              <span role="columnheader">Gatilho</span>
              <span role="columnheader">Contexto</span>
              <span role="columnheader">Entrada → Saída</span>
              <span role="columnheader" style={{ textAlign: "right" }}>
                Risco
              </span>
              <span role="columnheader" style={{ textAlign: "right" }}>
                R
              </span>
              <span role="columnheader" style={{ textAlign: "right" }}>
                Resultado
              </span>
              <span role="columnheader" style={{ textAlign: "right" }}>
                Plano
              </span>
            </div>
            {/* Linhas */}
            {visiveis.map((t) => {
              const pnl = Number(t.pnl_real) || 0;
              const desvio = temDesvio(t);
              const pts = Number(t.pontos_real) || 0;
              const risk =
                Number(t.stop) && Number(t.entrada)
                  ? Math.abs(Number(t.entrada) - Number(t.stop))
                  : 0;
              const rVal = risk > 0 ? pts / risk : 0;
              const compra = t.direcao === "COMPRA";
              return (
                <div
                  key={t.id}
                  role="row"
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "92px 1.3fr 76px 1.1fr 1fr 1.5fr 64px 70px 96px 72px",
                    gap: "10px",
                    alignItems: "center",
                    padding: "12px 0",
                    borderTop: "1px solid var(--bd)",
                  }}
                >
                  {/* Data */}
                  <span
                    role="cell"
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    <span style={{ fontWeight: 500 }}>{dataCurta(t.data)}</span>
                    <span style={{ fontSize: "11px", color: "var(--tx3)" }}>
                      {hora(t.hora_entrada)}
                    </span>
                  </span>
                  {/* Estratégia */}
                  <span role="cell" style={{ fontSize: "12px" }}>
                    {NOMES_ESTRATEGIAS[t.strategy_id] ?? t.strategy_id}
                  </span>
                  {/* Lado */}
                  <span role="cell">
                    <span
                      style={{
                        height: "24px",
                        padding: "0 10px",
                        borderRadius: "999px",
                        display: "inline-flex",
                        alignItems: "center",
                        fontSize: "12px",
                        fontWeight: 600,
                        background: compra ? "var(--acs)" : "var(--s1)",
                        color: compra ? "var(--actx)" : "var(--tx2)",
                        border: "1px solid var(--bd)",
                      }}
                    >
                      {compra ? "Compra" : "Venda"}
                    </span>
                  </span>
                  {/* Gatilho */}
                  <span
                    role="cell"
                    style={{ color: "var(--tx2)", fontSize: "12px" }}
                  >
                    {t.gatilho ? NOMES_GATILHOS[t.gatilho] : "\u2014"}
                  </span>
                  {/* Contexto */}
                  <span
                    role="cell"
                    style={{ color: "var(--tx2)", fontSize: "12px" }}
                  >
                    {t.contexto_1h ? NOMES_CONTEXTOS[t.contexto_1h] : "\u2014"}
                  </span>
                  {/* Preços */}
                  <span
                    role="cell"
                    style={{ color: "var(--tx2)", fontSize: "12px" }}
                  >
                    {`${preco(t.entrada)} \u2192 ${preco(t.saida)}`}
                  </span>
                  {/* Risco */}
                  <span
                    role="cell"
                    style={{
                      textAlign: "right",
                      color: "var(--tx2)",
                      fontSize: "12px",
                    }}
                  >
                    {risk > 0 ? `${risk} pts` : "\u2014"}
                  </span>
                  {/* R */}
                  <span
                    role="cell"
                    style={{
                      textAlign: "right",
                      fontWeight: 600,
                      color:
                        pnl > 0
                          ? "var(--actx)"
                          : pnl < 0
                          ? "var(--negtx)"
                          : "var(--tx2)",
                    }}
                  >
                    {sinalR(rVal)}
                  </span>
                  {/* Resultado */}
                  <span
                    role="cell"
                    style={{
                      textAlign: "right",
                      fontWeight: 600,
                      color:
                        pnl > 0
                          ? "var(--actx)"
                          : pnl < 0
                          ? "var(--negtx)"
                          : "var(--tx2)",
                    }}
                  >
                    {formatarBRL(pnl)}
                  </span>
                  {/* Plano */}
                  <span role="cell" style={{ textAlign: "right" }}>
                    <span
                      style={{
                        height: "24px",
                        padding: "0 10px",
                        borderRadius: "999px",
                        display: "inline-flex",
                        alignItems: "center",
                        fontSize: "11px",
                        fontWeight: 600,
                        background: desvio ? "var(--neg)" : "var(--acs)",
                        color: desvio ? "var(--bg)" : "var(--actx)",
                      }}
                    >
                      {desvio ? "Desvio" : "No plano"}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
