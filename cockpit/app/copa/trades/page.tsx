"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, Trade } from "@/lib/copa-api";
import { FecharTradeDialog } from "@/components/copa/fechar-trade-dialog";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstNum,
  InstBadge,
  InstEmpty,
  InstTable,
  InstRow,
  InstCell,
} from "@/components/inst";
import { PlusCircle, CheckCircle, Trash2, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function TradesJournalPage() {
  const [trades, setTrades] = React.useState<Trade[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedTradeToClose, setSelectedTradeToClose] = React.useState<Trade | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);

  const loadTrades = React.useCallback(async () => {
    setLoading(true);
    try {
      const list = await copaApi.listTrades();
      setTrades(list);
    } catch (err) {
      console.error("Erro ao carregar trades:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  const tradesAbertos = trades.filter((t) => t.status === "ABERTO");
  const tradesFechados = trades.filter((t) => t.status === "FECHADO");

  const handleOpenCloseDialog = (trade: Trade) => {
    setSelectedTradeToClose(trade);
    setDialogOpen(true);
  };

  const handleTradeClosed = (updated: Trade) => {
    setTrades((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  };

  const handleDeleteTrade = async (id: number) => {
    if (!confirm(`Tem certeza que deseja excluir o trade aberto #${id}?`)) return;
    try {
      await copaApi.deleteTrade(id);
      setTrades((prev) => prev.filter((t) => t.id !== id));
    } catch (err: any) {
      alert(err.detail || "Erro ao excluir trade");
    }
  };

  return (
    <InstPage
      eyebrow="COPA BTG · JOURNAL"
      title="Journal & Histórico de Trades"
      right={
        <Link href="/copa/novo">
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
            <PlusCircle className="h-3.5 w-3.5" /> Novo Trade (Checklist)
          </button>
        </Link>
      }
    >
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "4px" }}>
        Registro auditado de execuções e compliance disciplinar na Copa BTG.
      </div>

      {/* 1. SEÇÃO DE TRADES ABERTOS */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "14px", fontWeight: 700, letterSpacing: "-0.01em" }}>
            Posições Abertas
          </span>
          <InstBadge tom={tradesAbertos.length > 0 ? "now" : "neutro"}>
            {tradesAbertos.length} em andamento
          </InstBadge>
        </div>

        {tradesAbertos.length === 0 ? (
          <InstEmpty>
            Nenhum trade em andamento. O gate físico está liberado para nova oportunidade.
          </InstEmpty>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tradesAbertos.map((trade) => (
              <InstCard
                key={trade.id}
                label={
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span className="mono tabular" style={{ fontSize: "14px", fontWeight: 700 }}>
                      #{trade.id}
                    </span>
                    <InstBadge tom="neutro">{trade.mercado}</InstBadge>
                    <InstBadge tom={trade.direcao === "COMPRA" ? "ok" : "block"}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                        {trade.direcao === "COMPRA" ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                        {trade.direcao}
                      </span>
                    </InstBadge>
                  </div>
                }
                right={
                  <InstBadge tom="now">
                    Grade {trade.grade} ({trade.score} pts)
                  </InstBadge>
                }
              >
                <div style={{ fontSize: "11px", color: "var(--inst-dim)" }}>
                  Estratégia: <strong style={{ color: "var(--inst-text)" }}>{trade.strategy_id}</strong> • Aberto em: {trade.criado_em.split("T")[1]?.slice(0, 5) || trade.criado_em}
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr 1fr 1fr",
                    gap: "6px",
                    background: "var(--inst-bg-deep)",
                    padding: "10px",
                    borderRadius: "3px",
                    border: "1px solid var(--inst-line-2)",
                    textAlign: "center",
                  }}
                >
                  <div>
                    <span className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block" }}>
                      ENTRADA
                    </span>
                    <InstNum value={trade.entrada} size="sm" />
                  </div>
                  <div>
                    <span className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block" }}>
                      STOP LOSS
                    </span>
                    <InstNum value={trade.stop} tom="block" size="sm" />
                  </div>
                  <div>
                    <span className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block" }}>
                      ALVO
                    </span>
                    <InstNum value={trade.alvo} tom="ok" size="sm" />
                  </div>
                  <div>
                    <span className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block" }}>
                      RR PLAN
                    </span>
                    <InstNum value={`1:${trade.rr_planejado}`} tom="now" size="sm" />
                  </div>
                </div>

                {trade.notas && (
                  <div
                    style={{
                      fontSize: "11px",
                      color: "var(--inst-dim)",
                      fontStyle: "italic",
                      background: "var(--inst-bg-deep)",
                      padding: "8px",
                      borderRadius: "2px",
                      border: "1px solid var(--inst-line-2)",
                    }}
                  >
                    "{trade.notas}"
                  </div>
                )}

                <div style={{ display: "flex", gap: "8px", paddingTop: "4px" }}>
                  <button
                    type="button"
                    onClick={() => handleDeleteTrade(trade.id)}
                    className="mono tabular"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      background: "transparent",
                      border: "1px solid var(--inst-block-line)",
                      color: "var(--inst-block)",
                      borderRadius: "3px",
                      padding: "6px 12px",
                      fontSize: "11px",
                      cursor: "pointer",
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={() => handleOpenCloseDialog(trade)}
                    className="mono tabular"
                    style={{
                      flex: 1,
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
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
                    <CheckCircle className="h-3.5 w-3.5" /> Fechar & Auditar Trade
                  </button>
                </div>
              </InstCard>
            ))}
          </div>
        )}
      </div>

      {/* 2. SEÇÃO DE HISTÓRICO DE TRADES FECHADOS */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "14px", fontWeight: 700, letterSpacing: "-0.01em" }}>
            Histórico de Operações
          </span>
          <InstBadge tom="neutro">
            {tradesFechados.length} trades encerrados
          </InstBadge>
        </div>

        {tradesFechados.length === 0 ? (
          <InstEmpty>Nenhum trade encerrado registrado no banco ainda.</InstEmpty>
        ) : (
          <InstTable
            colunas={[
              "#",
              "Data / Hora",
              "Ativo / Lado",
              "Estratégia",
              { label: "Grade", align: "center" },
              { label: "Entrada / Stop / Alvo", align: "right" },
              { label: "Saída / Motivo", align: "center" },
              { label: "Pontos", align: "right" },
              { label: "PnL Real", align: "right" },
              { label: "PnL Plano", align: "right" },
              { label: "Disciplina", align: "center" },
            ]}
          >
            {tradesFechados.map((t) => {
              const teveDesvio =
                t.respeitou_plano === 0 ||
                t.antecipou_stop === 1 ||
                t.parcial_emocional === 1 ||
                t.mudou_alvo === 1;

              const pnlReal = t.pnl_real ?? 0;
              const pnlPlano = t.pnl_plano ?? pnlReal;
              const custoDesvio = pnlPlano - pnlReal;

              return (
                <InstRow
                  key={t.id}
                  tom={teveDesvio ? "block" : pnlReal > 0 ? "ok" : pnlReal < 0 ? "block" : "neutro"}
                >
                  <InstCell>
                    <span className="mono tabular" style={{ fontWeight: 700 }}>
                      #{t.id}
                    </span>
                  </InstCell>
                  <InstCell>
                    <span className="mono tabular" style={{ fontSize: "12px", display: "block" }}>
                      {t.data}
                    </span>
                    <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)" }}>
                      {t.criado_em.split("T")[1]?.slice(0, 5) || ""} → {t.fechado_em?.split("T")[1]?.slice(0, 5) || ""}
                    </span>
                  </InstCell>
                  <InstCell>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span className="mono tabular" style={{ fontWeight: 700 }}>{t.mercado}</span>
                      <InstBadge tom={t.direcao === "COMPRA" ? "ok" : "block"}>
                        {t.direcao}
                      </InstBadge>
                    </div>
                  </InstCell>
                  <InstCell>
                    <span style={{ fontSize: "12px" }}>{t.strategy_id}</span>
                  </InstCell>
                  <InstCell align="center">
                    <InstBadge tom="neutro">
                      {t.grade} ({t.score}p)
                    </InstBadge>
                  </InstCell>
                  <InstCell align="right">
                    <span className="mono tabular" style={{ fontSize: "11.5px" }}>
                      {t.entrada} / <span style={{ color: "var(--inst-block)" }}>{t.stop}</span> / <span style={{ color: "var(--inst-ok)" }}>{t.alvo}</span>
                    </span>
                  </InstCell>
                  <InstCell align="center">
                    <span className="mono tabular" style={{ fontWeight: 700, display: "block" }}>
                      {t.saida ?? "—"}
                    </span>
                    <InstBadge tom="neutro">{t.motivo_saida}</InstBadge>
                  </InstCell>
                  <InstCell align="right">
                    <span className="mono tabular">{t.pontos_real ?? 0} pts</span>
                  </InstCell>
                  <InstCell align="right">
                    <InstNum
                      value={`R$ ${pnlReal.toFixed(2)}`}
                      tom={pnlReal > 0 ? "ok" : pnlReal < 0 ? "block" : "neutro"}
                      size="sm"
                    />
                  </InstCell>
                  <InstCell align="right">
                    <span className="mono tabular" style={{ color: "var(--inst-faint)" }}>
                      R$ {pnlPlano.toFixed(2)}
                    </span>
                  </InstCell>
                  <InstCell align="center">
                    {teveDesvio ? (
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
                        <InstBadge tom="block">DESVIO</InstBadge>
                        {custoDesvio > 0 && (
                          <span className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-block)", fontWeight: 700 }}>
                            -R$ {custoDesvio.toFixed(0)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <InstBadge tom="ok">PLANO 100%</InstBadge>
                    )}
                  </InstCell>
                </InstRow>
              );
            })}
          </InstTable>
        )}
      </div>

      {/* Modal de Fechamento */}
      <FecharTradeDialog
        trade={selectedTradeToClose}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onTradeClosed={handleTradeClosed}
      />
    </InstPage>
  );
}
