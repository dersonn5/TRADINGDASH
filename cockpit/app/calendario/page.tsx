"use client";

import * as React from "react";
import { listarTradesDoMes, getDataSaoPaulo, TradeHistorico } from "@/lib/copa-db";
import { montarCalendarioMes } from "@/lib/calendario-resultados";
import { CARD, LBL } from "@/components/v2/estilos";
import {
  NOMES_ESTRATEGIAS,
  SIGLAS,
  calcularRTrade,
  calcularRiscoTrade,
  formatarBRL,
  formatarPct,
  formatarR,
  somar,
  temDesvio,
} from "@/lib/metricas";

const MESES = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

const DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];

function mesAnterior(ano: number, mes: number) {
  return mes === 1 ? { ano: ano - 1, mes: 12 } : { ano, mes: mes - 1 };
}

function mesSeguinte(ano: number, mes: number) {
  return mes === 12 ? { ano: ano + 1, mes: 1 } : { ano, mes: mes + 1 };
}

function hora(iso: string | null | undefined) {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function dataCurta(iso: string) {
  const [, m, d] = iso.split("-");
  return d && m ? `${d}/${m}` : iso;
}

export default function CalendarioPage() {
  const hojeIso = getDataSaoPaulo();
  const [anoHoje, mesHoje] = hojeIso.split("-").map(Number);
  const [sel, setSel] = React.useState({ ano: anoHoje, mes: mesHoje });
  const [trades, setTrades] = React.useState<TradeHistorico[] | null>(null);
  const [erro, setErro] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [diaSelecionado, setDiaSelecionado] = React.useState<string | null>(null);

  React.useEffect(() => {
    let ativo = true;
    setLoading(true);
    setErro(null);
    setDiaSelecionado(null);

    listarTradesDoMes(sel.ano, sel.mes)
      .then((dados) => {
        if (!ativo) return;
        setTrades(dados);
      })
      .catch((e) => {
        if (!ativo) return;
        setErro(e.message || "Erro ao carregar trades do mês");
      })
      .finally(() => {
        if (ativo) setLoading(false);
      });

    return () => {
      ativo = false;
    };
  }, [sel.ano, sel.mes]);

  const cal = React.useMemo(() => {
    return montarCalendarioMes(trades || [], sel.ano, sel.mes, hojeIso);
  }, [trades, sel.ano, sel.mes, hojeIso]);

  const nomeMes = MESES[sel.mes - 1];
  const ehMesAtual = sel.ano === anoHoje && sel.mes === mesHoje;

  const tradesDoDiaSelecionado = React.useMemo(() => {
    if (!diaSelecionado || !trades) return [];
    return trades.filter((t) => t.data === diaSelecionado);
  }, [diaSelecionado, trades]);

  return (
    <>
      <style>{`
        .cal-layout-linha {
          display: flex;
          gap: 12px;
          align-items: stretch;
        }
        .cal-layout-dias {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 10px;
          flex: 1;
        }
        .cal-layout-semana {
          width: 220px;
          flex-shrink: 0;
        }
        @media (max-width: 1099px) {
          .cal-layout-linha {
            flex-direction: column;
          }
          .cal-layout-semana {
            width: 100%;
          }
          .cal-header-semana-label {
            display: none;
          }
        }
      `}</style>

      {/* Cabeçalho FR-002 */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>
            Calendário · resultado por dia
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h1
              style={{
                margin: 0,
                fontSize: "30px",
                fontWeight: 600,
                letterSpacing: "-0.02em",
              }}
            >
              {nomeMes} {sel.ano}
            </h1>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                background: "var(--s1)",
                border: "1px solid var(--bd)",
                borderRadius: "10px",
                padding: "2px",
              }}
            >
              <button
                type="button"
                onClick={() => setSel(mesAnterior(sel.ano, sel.mes))}
                aria-label="Mês anterior"
                title="Mês anterior"
                style={{
                  width: "32px",
                  height: "32px",
                  border: 0,
                  borderRadius: "8px",
                  background: "transparent",
                  color: "var(--tx2)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "16px",
                  fontWeight: 600,
                }}
              >
                ‹
              </button>
              <button
                type="button"
                disabled={ehMesAtual}
                onClick={() => {
                  if (!ehMesAtual) setSel(mesSeguinte(sel.ano, sel.mes));
                }}
                aria-label="Mês seguinte"
                title="Mês seguinte"
                style={{
                  width: "32px",
                  height: "32px",
                  border: 0,
                  borderRadius: "8px",
                  background: "transparent",
                  color: ehMesAtual ? "var(--tx3)" : "var(--tx2)",
                  cursor: ehMesAtual ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "16px",
                  fontWeight: 600,
                  opacity: ehMesAtual ? 0.35 : 1,
                }}
              >
                ›
              </button>
            </div>
          </div>
          <div style={{ fontSize: "14px", color: "var(--tx2)" }}>
            {formatarBRL(cal.total.pnl)} no mês · {cal.total.ganhos}{" "}
            {cal.total.ganhos === 1 ? "ganho" : "ganhos"} · {cal.total.perdas}{" "}
            {cal.total.perdas === 1 ? "perda" : "perdas"} · {cal.semanasPositivas} de{" "}
            {cal.semanasComTrade}{" "}
            {cal.semanasComTrade === 1 ? "semana positiva" : "semanas positivas"}
          </div>
        </div>
      </div>

      {erro ? (
        <div style={{ ...CARD, color: "var(--negtx)", fontSize: "14px" }}>
          {erro}
        </div>
      ) : loading ? (
        <div
          style={{
            ...CARD,
            alignItems: "center",
            padding: "48px",
            color: "var(--tx3)",
            fontSize: "14px",
          }}
        >
          Carregando…
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Cabeçalho dos dias da semana (Segunda a Sexta) */}
          <div className="cal-layout-linha" style={{ padding: "0 4px" }}>
            <div className="cal-layout-dias">
              {DIAS_SEMANA.map((nome) => (
                <span
                  key={nome}
                  style={{
                    ...LBL,
                    fontSize: "11px",
                    padding: "4px 8px",
                  }}
                >
                  {nome}
                </span>
              ))}
            </div>
            <div className="cal-layout-semana cal-header-semana-label">
              <span
                style={{
                  ...LBL,
                  fontSize: "11px",
                  padding: "4px 8px",
                }}
              >
                Semana
              </span>
            </div>
          </div>

          {/* Grade de Semanas e Dias */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {cal.semanas.map((semana) => (
              <div key={semana.n} className="cal-layout-linha">
                {/* 5 Dias da Semana */}
                <div className="cal-layout-dias">
                  {semana.dias.map((dia) => {
                    const clicavel = dia.trades > 0;
                    const selecionado = diaSelecionado === dia.iso;

                    let bgFundo = "var(--s1)";
                    let borda = dia.hoje ? "1.5px solid var(--ac)" : "1px solid var(--bd)";
                    if (selecionado) {
                      borda = "1.5px solid var(--actx)";
                    }

                    if (!dia.doMes) {
                      bgFundo = "transparent";
                    } else if (dia.trades > 0) {
                      if (dia.pnl > 0) {
                        bgFundo = "var(--acs)";
                      } else if (dia.pnl < 0) {
                        bgFundo = "color-mix(in srgb, var(--neg) 14%, transparent)";
                      }
                    }

                    return (
                      <div
                        key={dia.iso}
                        role={clicavel ? "button" : undefined}
                        tabIndex={clicavel ? 0 : undefined}
                        onClick={() => {
                          if (clicavel) {
                            setDiaSelecionado((prev) => (prev === dia.iso ? null : dia.iso));
                          }
                        }}
                        onKeyDown={(e) => {
                          if (clicavel && (e.key === "Enter" || e.key === " ")) {
                            e.preventDefault();
                            setDiaSelecionado((prev) => (prev === dia.iso ? null : dia.iso));
                          }
                        }}
                        style={{
                          minHeight: "106px",
                          padding: "12px",
                          borderRadius: "14px",
                          border: borda,
                          background: bgFundo,
                          opacity: !dia.doMes ? 0.32 : dia.futuro && dia.trades === 0 ? 0.45 : 1,
                          cursor: clicavel ? "pointer" : "default",
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "space-between",
                          position: "relative",
                          transition: "border-color 140ms ease, background 140ms ease",
                          boxSizing: "border-box",
                        }}
                      >
                        {/* Linha superior: Dia e Selo / Feriado */}
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: "4px",
                          }}
                        >
                          <span
                            style={{
                              fontSize: "13px",
                              fontWeight: 600,
                              color: dia.doMes ? "var(--tx)" : "var(--tx3)",
                            }}
                          >
                            {dia.dia}
                          </span>
                          {dia.trades > 0 ? (
                            <span
                              style={{
                                fontSize: "10px",
                                fontWeight: 500,
                                padding: "2px 6px",
                                borderRadius: "6px",
                                background: "var(--s2)",
                                color: "var(--tx2)",
                                border: "1px solid var(--bd)",
                              }}
                            >
                              {dia.trades} {dia.trades === 1 ? "trade" : "trades"}
                            </span>
                          ) : dia.doMes && dia.feriado ? (
                            <span
                              style={{
                                fontSize: "10px",
                                color: "var(--tx3)",
                                fontWeight: 500,
                              }}
                            >
                              Feriado
                            </span>
                          ) : null}
                        </div>

                        {/* Centro: PnL em R$ */}
                        <div style={{ margin: "6px 0" }}>
                          {!dia.doMes ? (
                            <div style={{ height: "22px" }} />
                          ) : dia.trades > 0 ? (
                            <div
                              style={{
                                fontSize: "17px",
                                fontWeight: 600,
                                color:
                                  dia.pnl > 0
                                    ? "var(--actx)"
                                    : dia.pnl < 0
                                    ? "var(--negtx)"
                                    : "var(--tx3)",
                              }}
                            >
                              {formatarBRL(dia.pnl)}
                            </div>
                          ) : (
                            <div
                              style={{
                                fontSize: "15px",
                                fontWeight: 500,
                                color: "var(--tx3)",
                              }}
                            >
                              R$ 0
                            </div>
                          )}
                        </div>

                        {/* Linha inferior: R e Placar W · L */}
                        <div>
                          {dia.trades > 0 ? (
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                fontSize: "11px",
                                color: "var(--tx3)",
                              }}
                            >
                              <span
                                style={{
                                  fontWeight: 600,
                                  color:
                                    dia.r > 0
                                    ? "var(--actx)"
                                    : dia.r < 0
                                    ? "var(--negtx)"
                                    : "var(--tx3)",
                                }}
                              >
                                {formatarR(dia.r)}
                              </span>
                              <span>
                                {dia.ganhos}W · {dia.perdas}L
                              </span>
                            </div>
                          ) : (
                            <div style={{ height: "14px" }} />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Coluna / Cartão da Semana FR-004 */}
                <div
                  className="cal-layout-semana"
                  style={{
                    padding: "14px 16px",
                    borderRadius: "14px",
                    border: "1px solid var(--bd)",
                    background:
                      semana.trades > 0
                        ? semana.pnl > 0
                          ? "var(--acs)"
                          : semana.pnl < 0
                          ? "color-mix(in srgb, var(--neg) 12%, transparent)"
                          : "var(--s1)"
                        : "var(--s1)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "8px",
                    boxSizing: "border-box",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "var(--tx2)",
                        textTransform: "uppercase",
                        letterSpacing: "0.04em",
                      }}
                    >
                      Semana {semana.n}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        color: semana.trades > 0 ? "var(--tx2)" : "var(--tx3)",
                      }}
                    >
                      {semana.trades} {semana.trades === 1 ? "trade" : "trades"}
                    </span>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: "8px",
                      margin: "4px 0",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "18px",
                        fontWeight: 600,
                        color:
                          semana.trades === 0
                            ? "var(--tx3)"
                            : semana.pnl > 0
                            ? "var(--actx)"
                            : semana.pnl < 0
                            ? "var(--negtx)"
                            : "var(--tx3)",
                      }}
                    >
                      {semana.trades === 0 ? "R$ 0" : formatarBRL(semana.pnl)}
                    </span>
                    {semana.trades > 0 && (
                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color:
                            semana.r > 0
                              ? "var(--actx)"
                              : semana.r < 0
                              ? "var(--negtx)"
                              : "var(--tx3)",
                        }}
                      >
                        {formatarR(semana.r)}
                      </span>
                    )}
                  </div>

                  <div>
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "3px 8px",
                        borderRadius: "999px",
                        background: "var(--s2)",
                        border: "1px solid var(--bd)",
                        color: semana.trades > 0 ? "var(--tx)" : "var(--tx3)",
                        display: "inline-block",
                      }}
                    >
                      WR {semana.wr !== null ? formatarPct(semana.wr) : "—"} · PF{" "}
                      {semana.pf !== null ? semana.pf.toFixed(2).replace(".", ",") : "—"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Detalhe do dia ao clicar FR-005 */}
          {diaSelecionado && (
            <section
              style={{
                ...CARD,
                marginTop: "8px",
                border: "1.5px solid var(--actx)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <h2 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>
                    Trades de {dataCurta(diaSelecionado)}
                  </h2>
                  <span
                    style={{
                      fontSize: "12px",
                      color: "var(--tx3)",
                      fontWeight: 500,
                    }}
                  >
                    {tradesDoDiaSelecionado.length}{" "}
                    {tradesDoDiaSelecionado.length === 1 ? "trade" : "trades"} ·{" "}
                    {formatarBRL(somar(tradesDoDiaSelecionado.map((t) => Number(t.pnl_real ?? 0))))}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setDiaSelecionado(null)}
                  style={{
                    height: "32px",
                    padding: "0 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--bd)",
                    background: "transparent",
                    color: "var(--tx2)",
                    fontFamily: "inherit",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  Fechar
                </button>
              </div>

              <div
                role="table"
                aria-label={`Trades de ${diaSelecionado}`}
                style={{ display: "flex", flexDirection: "column", fontSize: "13px" }}
              >
                {/* Cabeçalho da tabela */}
                <div
                  role="row"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "80px 1.2fr 80px 80px 110px 80px",
                    gap: "10px",
                    alignItems: "center",
                    paddingBottom: "10px",
                    color: "var(--tx3)",
                    fontSize: "11px",
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                  }}
                >
                  <span role="columnheader">Hora</span>
                  <span role="columnheader">Setup</span>
                  <span role="columnheader">Lado</span>
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

                {tradesDoDiaSelecionado.map((t) => {
                  const pnl = Number(t.pnl_real ?? 0);
                  const desvio = temDesvio(t);
                  const pts = Number(t.pontos_real ?? 0);
                  const risco = calcularRiscoTrade(Number(t.entrada ?? 0), Number(t.stop ?? 0));
                  const rVal = calcularRTrade(pts, risco);
                  const compra = t.direcao === "COMPRA";
                  const sigla =
                    NOMES_ESTRATEGIAS[t.strategy_id] ??
                    SIGLAS[t.strategy_id] ??
                    t.strategy_id;

                  return (
                    <div
                      key={t.id}
                      role="row"
                      style={{
                        display: "grid",
                        gridTemplateColumns: "80px 1.2fr 80px 80px 110px 80px",
                        gap: "10px",
                        alignItems: "center",
                        padding: "10px 0",
                        borderTop: "1px solid var(--bd)",
                      }}
                    >
                      <span role="cell" style={{ color: "var(--tx2)" }}>
                        {hora(t.hora_entrada)}
                      </span>
                      <span role="cell" style={{ fontWeight: 500 }}>
                        {sigla}
                      </span>
                      <span role="cell">
                        <span
                          style={{
                            height: "22px",
                            padding: "0 8px",
                            borderRadius: "999px",
                            display: "inline-flex",
                            alignItems: "center",
                            fontSize: "11px",
                            fontWeight: 600,
                            background: compra ? "var(--acs)" : "var(--s1)",
                            color: compra ? "var(--actx)" : "var(--tx2)",
                            border: "1px solid var(--bd)",
                          }}
                        >
                          {compra ? "Compra" : "Venda"}
                        </span>
                      </span>
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
                        {formatarR(rVal)}
                      </span>
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
                      <span role="cell" style={{ textAlign: "right" }}>
                        <span
                          style={{
                            height: "22px",
                            padding: "0 8px",
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
            </section>
          )}

          {/* Rodapé do mês FR-006 */}
          <div
            style={{
              ...CARD,
              padding: "16px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "12px",
              fontSize: "14px",
              color: "var(--tx2)",
            }}
          >
            <span>
              <strong style={{ color: "var(--tx)" }}>Total do mês:</strong>{" "}
              <span
                style={{
                  fontWeight: 600,
                  color:
                    cal.total.pnl > 0
                      ? "var(--actx)"
                      : cal.total.pnl < 0
                      ? "var(--negtx)"
                      : "var(--tx)",
                }}
              >
                {formatarBRL(cal.total.pnl)}
              </span>{" "}
              ·{" "}
              <span
                style={{
                  fontWeight: 600,
                  color:
                    cal.total.r > 0
                      ? "var(--actx)"
                      : cal.total.r < 0
                      ? "var(--negtx)"
                      : "var(--tx)",
                }}
              >
                {formatarR(cal.total.r)}
              </span>{" "}
              · {cal.total.trades} {cal.total.trades === 1 ? "trade" : "trades"} · WR{" "}
              {cal.total.wr !== null ? formatarPct(cal.total.wr) : "—"} · PF{" "}
              {cal.total.pf !== null ? cal.total.pf.toFixed(2).replace(".", ",") : "—"}
            </span>
          </div>
        </div>
      )}
    </>
  );
}
