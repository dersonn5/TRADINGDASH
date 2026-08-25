"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, Trade } from "@/lib/copa-api";
import { FecharTradeDialog } from "@/components/copa/fechar-trade-dialog";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table";
import {
  PlusCircle,
  CheckCircle,
  AlertOctagon,
  Trash2,
  Lock,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

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
    <div className="container py-6 space-y-8">
      {/* Topo */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Journal & Histórico de Trades</h1>
          <p className="text-sm text-muted-foreground">
            Registro auditado de execuções e compliance disciplinar na Copa BTG.
          </p>
        </div>
        <Link href="/copa/novo">
          <Button className="gap-2 font-bold bg-primary text-primary-foreground">
            <PlusCircle className="h-4 w-4" /> Novo Trade (Checklist)
          </Button>
        </Link>
      </div>

      {/* 1. SEÇÃO DE TRADES ABERTOS */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-bold tracking-tight">Posições Abertas</h2>
          <Badge variant={tradesAbertos.length > 0 ? "default" : "outline"} className="text-xs">
            {tradesAbertos.length} em andamento
          </Badge>
        </div>

        {tradesAbertos.length === 0 ? (
          <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground bg-muted/10">
            Nenhum trade em andamento. O gate físico está liberado para nova oportunidade.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tradesAbertos.map((trade) => (
              <Card key={trade.id} className="border-primary/40 bg-card shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-lg">#{trade.id}</span>
                      <Badge variant="outline" className="font-mono font-bold">
                        {trade.mercado}
                      </Badge>
                      <Badge
                        className={cn(
                          "font-bold gap-1",
                          trade.direcao === "COMPRA"
                            ? "bg-emerald-600 text-white"
                            : "bg-rose-600 text-white"
                        )}
                      >
                        {trade.direcao === "COMPRA" ? (
                          <ArrowUpRight className="h-3 w-3" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3" />
                        )}
                        {trade.direcao}
                      </Badge>
                    </div>

                    <Badge className="bg-primary/20 text-primary font-mono font-bold">
                      Grade {trade.grade} ({trade.score} pts)
                    </Badge>
                  </div>
                  <CardDescription className="text-xs mt-1">
                    Estratégia: <span className="font-semibold text-foreground">{trade.strategy_id}</span> • Aberto em: {trade.criado_em.split("T")[1]?.slice(0, 5) || trade.criado_em}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid grid-cols-4 gap-2 rounded-lg bg-muted/30 p-3 text-center">
                    <div>
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                        Entrada
                      </span>
                      <span className="font-mono font-bold text-sm">{trade.entrada}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                        Stop Loss
                      </span>
                      <span className="font-mono font-bold text-sm text-destructive">{trade.stop}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                        Alvo
                      </span>
                      <span className="font-mono font-bold text-sm text-emerald-400">{trade.alvo}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                        RR Plan
                      </span>
                      <span className="font-mono font-bold text-sm text-primary">
                        1:{trade.rr_planejado}
                      </span>
                    </div>
                  </div>

                  {trade.notas && (
                    <p className="text-xs text-muted-foreground italic bg-muted/20 p-2 rounded">
                      "{trade.notas}"
                    </p>
                  )}

                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteTrade(trade.id)}
                      className="text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" /> Cancelar
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      className="flex-1 font-bold bg-primary text-primary-foreground gap-1.5"
                      onClick={() => handleOpenCloseDialog(trade)}
                    >
                      <CheckCircle className="h-4 w-4" /> Fechar & Auditar Trade
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 2. SEÇÃO DE HISTÓRICO DE TRADES FECHADOS */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold tracking-tight">Histórico de Operações</h2>
            <Badge variant="outline" className="text-xs font-mono">
              {tradesFechados.length} trades encerrados
            </Badge>
          </div>
        </div>

        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 text-center">#</TableHead>
                  <TableHead>Data / Hora</TableHead>
                  <TableHead>Ativo / Lado</TableHead>
                  <TableHead>Estratégia</TableHead>
                  <TableHead className="text-center">Grade</TableHead>
                  <TableHead className="text-right">Entrada / Stop / Alvo</TableHead>
                  <TableHead className="text-center">Saída / Motivo</TableHead>
                  <TableHead className="text-right">Pontos</TableHead>
                  <TableHead className="text-right">PnL Real</TableHead>
                  <TableHead className="text-right">PnL Plano</TableHead>
                  <TableHead className="text-center">Disciplina</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tradesFechados.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={11} className="text-center py-8 text-muted-foreground">
                      Nenhum trade encerrado registrado no banco ainda.
                    </TableCell>
                  </TableRow>
                ) : (
                  tradesFechados.map((t) => {
                    const teveDesvio =
                      t.respeitou_plano === 0 ||
                      t.antecipou_stop === 1 ||
                      t.parcial_emocional === 1 ||
                      t.mudou_alvo === 1;

                    const pnlReal = t.pnl_real ?? 0;
                    const pnlPlano = t.pnl_plano ?? pnlReal;
                    const custoDesvio = pnlPlano - pnlReal;

                    return (
                      <TableRow
                        key={t.id}
                        className={cn(
                          "transition-colors",
                          teveDesvio && "border-l-4 border-l-destructive bg-destructive/5"
                        )}
                      >
                        <TableCell className="font-mono text-center font-bold text-xs">
                          {t.id}
                        </TableCell>
                        <TableCell className="text-xs whitespace-nowrap">
                          <span className="font-medium block">{t.data}</span>
                          <span className="text-[10px] text-muted-foreground font-mono">
                            {t.criado_em.split("T")[1]?.slice(0, 5) || ""} →{" "}
                            {t.fechado_em?.split("T")[1]?.slice(0, 5) || ""}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono font-bold text-xs">{t.mercado}</span>
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-[10px] py-0 px-1 font-bold",
                                t.direcao === "COMPRA"
                                  ? "text-emerald-400 border-emerald-500/30"
                                  : "text-rose-400 border-rose-500/30"
                              )}
                            >
                              {t.direcao}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-xs font-medium">
                          {t.strategy_id}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className="font-mono text-xs font-bold">
                            {t.grade} ({t.score}p)
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs whitespace-nowrap">
                          <span>{t.entrada}</span> /{" "}
                          <span className="text-destructive">{t.stop}</span> /{" "}
                          <span className="text-emerald-400">{t.alvo}</span>
                        </TableCell>
                        <TableCell className="text-center text-xs">
                          <div className="font-mono font-bold">{t.saida ?? "—"}</div>
                          <Badge variant="secondary" className="text-[9px] py-0">
                            {t.motivo_saida}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs font-semibold">
                          {t.pontos_real ?? 0} pts
                        </TableCell>
                        <TableCell
                          className={cn(
                            "text-right font-mono font-bold text-sm whitespace-nowrap",
                            pnlReal > 0
                              ? "text-emerald-400"
                              : pnlReal < 0
                              ? "text-red-400"
                              : "text-foreground"
                          )}
                        >
                          R$ {pnlReal.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-muted-foreground whitespace-nowrap">
                          R$ {pnlPlano.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-center">
                          {teveDesvio ? (
                            <div className="flex flex-col items-center gap-1">
                              <Badge variant="destructive" className="text-[9px] py-0 font-bold">
                                DESVIO
                              </Badge>
                              {custoDesvio > 0 && (
                                <span className="text-[9px] font-mono text-destructive font-bold">
                                  -R$ {custoDesvio.toFixed(0)}
                                </span>
                              )}
                            </div>
                          ) : (
                            <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[9px] py-0">
                              PLANO 100%
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>

      {/* Modal de Fechamento */}
      <FecharTradeDialog
        trade={selectedTradeToClose}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onTradeClosed={handleTradeClosed}
      />
    </div>
  );
}
