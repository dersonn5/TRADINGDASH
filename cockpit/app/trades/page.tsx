"use client";

import { useEffect, useState } from "react";
import { fetchTrades, saveTrade, TradingTrade } from "@/lib/trading-db";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CandlestickChart, Plus, TrendingUp, TrendingDown, DollarSign, Activity, Percent, Filter, ShieldCheck } from "lucide-react";

export default function TradesPage() {
  const [trades, setTrades] = useState<TradingTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [filterSymbol, setFilterSymbol] = useState("TODOS");
  const [filterResult, setFilterResult] = useState("TODOS");

  // Form State
  const [symbol, setSymbol] = useState("WIN");
  const [direction, setDirection] = useState<"BUY" | "SELL">("BUY");
  const [strategy, setStrategy] = useState("Silver Bullet");
  const [session, setSession] = useState("B3 Abertura");
  const [contracts, setContracts] = useState<number>(1);
  const [entryPrice, setEntryPrice] = useState<number>(0);
  const [exitPrice, setExitPrice] = useState<number>(0);
  const [stopLoss, setStopLoss] = useState<number>(0);
  const [takeProfit, setTakeProfit] = useState<number>(0);
  const [pnl, setPnl] = useState<number>(0);
  const [result, setResult] = useState<"WIN" | "LOSS" | "BE" | "OPEN">("WIN");
  const [confluenceScore, setConfluenceScore] = useState<number>(85);
  const [notes, setNotes] = useState("");
  const [mistakes, setMistakes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTrades();
  }, []);

  async function loadTrades() {
    setLoading(true);
    const data = await fetchTrades();
    setTrades(data);
    setLoading(false);
  }

  async function handleCreateTrade() {
    if (!symbol || entryPrice <= 0 || stopLoss <= 0) {
      alert("Preencha ao menos Ativo, Preço de Entrada e Stop Loss!");
      return;
    }
    setSaving(true);

    // Calcular RR aproximado
    const risk = Math.abs(entryPrice - stopLoss);
    const reward = exitPrice > 0 ? Math.abs(exitPrice - entryPrice) : Math.abs(takeProfit - entryPrice);
    const rr = risk > 0 ? Number((reward / risk).toFixed(2)) : 0;

    await saveTrade({
      symbol: symbol.toUpperCase(),
      direction,
      strategy,
      session,
      contracts: Number(contracts) || 1,
      entry_price: Number(entryPrice),
      exit_price: Number(exitPrice) || undefined,
      stop_loss: Number(stopLoss),
      take_profit: Number(takeProfit) || undefined,
      pnl: Number(pnl) || 0,
      result,
      rr_achieved: rr,
      confluence_score: Number(confluenceScore) || 80,
      notes: notes.trim() || undefined,
      mistakes_learnings: mistakes.trim() || undefined,
      trade_date: new Date().toISOString(),
    });

    // Reset Form
    setIsDialogOpen(false);
    setSaving(false);
    setNotes("");
    setMistakes("");
    await loadTrades();
  }

  // Estatísticas calculadas
  const totalTrades = trades.length;
  const wins = trades.filter((t) => t.result === "WIN").length;
  const losses = trades.filter((t) => t.result === "LOSS").length;
  const winRate = totalTrades > 0 ? ((wins / totalTrades) * 100).toFixed(1) : "0.0";
  const totalPnL = trades.reduce((acc, t) => acc + (t.pnl || 0), 0);
  const grossProfit = trades.filter((t) => (t.pnl || 0) > 0).reduce((acc, t) => acc + (t.pnl || 0), 0);
  const grossLoss = Math.abs(trades.filter((t) => (t.pnl || 0) < 0).reduce((acc, t) => acc + (t.pnl || 0), 0));
  const profitFactor = grossLoss > 0 ? (grossProfit / grossLoss).toFixed(2) : grossProfit > 0 ? "MAX" : "0.00";

  const filteredTrades = trades.filter((t) => {
    const matchesSymbol = filterSymbol === "TODOS" || t.symbol.toUpperCase() === filterSymbol.toUpperCase();
    const matchesResult = filterResult === "TODOS" || t.result === filterResult;
    return matchesSymbol && matchesResult;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CandlestickChart className="size-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Banco de Todos os Trades</h1>
            <Badge variant="outline" className="text-emerald-400 border-emerald-800/40 bg-emerald-950/20">
              Supabase Live
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Histórico completo de execuções reais, cálculo de R:R e métricas de desempenho.
          </p>
        </div>

        {/* Botão e Modal Novo Trade */}
        <Button
          onClick={() => setIsDialogOpen(true)}
          className="gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-600/90 hover:to-teal-600/90 text-white shadow-lg shadow-emerald-950/50"
        >
          <Plus className="size-4" />
          Registrar Novo Trade
        </Button>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="size-5 text-emerald-400" />
              Registrar Operação no Banco de Trades
            </DialogTitle>
          </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Ativo</label>
                  <Input
                    placeholder="WIN, WDO, NQ, BTC"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    className="mt-1 uppercase font-bold"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Direção</label>
                  <select
                    className="w-full h-9 mt-1 rounded-md border border-input bg-card text-foreground px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring [&_option]:bg-[#18181b] [&_option]:text-[#f4f4f5]"
                    style={{ colorScheme: "dark" }}
                    value={direction}
                    onChange={(e) => setDirection(e.target.value as "BUY" | "SELL")}
                  >
                    <option value="BUY">BUY (Compra)</option>
                    <option value="SELL">SELL (Venda)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Lotes / Contratos</label>
                  <Input
                    type="number"
                    value={contracts}
                    onChange={(e) => setContracts(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Estratégia</label>
                  <Input
                    placeholder="Silver Bullet, Breaker Block, etc."
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Sessão / Horário</label>
                  <Input
                    placeholder="B3 Abertura, NY AM, London"
                    value={session}
                    onChange={(e) => setSession(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2">
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase">Entrada</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="131250"
                    value={entryPrice || ""}
                    onChange={(e) => setEntryPrice(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase">Stop Loss</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="131050"
                    value={stopLoss || ""}
                    onChange={(e) => setStopLoss(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase">Take Profit</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="131750"
                    value={takeProfit || ""}
                    onChange={(e) => setTakeProfit(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase">Saída Real</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="131750"
                    value={exitPrice || ""}
                    onChange={(e) => setExitPrice(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Resultado</label>
                  <select
                    className="w-full h-9 mt-1 rounded-md border border-input bg-card text-foreground px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring [&_option]:bg-[#18181b] [&_option]:text-[#f4f4f5]"
                    style={{ colorScheme: "dark" }}
                    value={result}
                    onChange={(e) => setResult(e.target.value as "WIN" | "LOSS" | "BE" | "OPEN")}
                  >
                    <option value="WIN">WIN (Ganho)</option>
                    <option value="LOSS">LOSS (Perda)</option>
                    <option value="BE">BE (Zero a Zero)</option>
                    <option value="OPEN">OPEN (Em aberto)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">PnL Financeiro ($/R$)</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="+200 ou -100"
                    value={pnl || ""}
                    onChange={(e) => setPnl(Number(e.target.value))}
                    className="mt-1 font-bold"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Score Confluência</label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={confluenceScore}
                    onChange={(e) => setConfluenceScore(Number(e.target.value))}
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Anotações do Trade</label>
                <Textarea
                  placeholder="Contexto: liquidez varrida, comportamento do candle, reação no FVG..."
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="mt-1 text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Erros & Lições Aprendidas</label>
                <Textarea
                  placeholder="O que funcionou bem? Houve hesitação ou quebra de plano?"
                  rows={2}
                  value={mistakes}
                  onChange={(e) => setMistakes(e.target.value)}
                  className="mt-1 text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button
                  onClick={handleCreateTrade}
                  disabled={saving || !symbol || entryPrice <= 0 || stopLoss <= 0}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {saving ? "Registrando..." : "Salvar no Supabase"}
                </Button>
              </div>
            </div>
        </Dialog>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Total de Trades</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center justify-between">
              <span>{totalTrades}</span>
              <Activity className="size-5 text-muted-foreground opacity-40" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Taxa de Acerto (Win Rate)</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-cyan-400 flex items-center justify-between">
              <span>{winRate}%</span>
              <Percent className="size-5 text-cyan-400 opacity-40" />
            </div>
            <div className="text-[11px] text-muted-foreground mt-1">
              {wins} W · {losses} L
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">PnL Líquido Acumulado</span>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold flex items-center justify-between ${
                totalPnL >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              <span>{totalPnL >= 0 ? `+${totalPnL.toFixed(2)}` : totalPnL.toFixed(2)}</span>
              <DollarSign className="size-5 opacity-40" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Fator de Lucro</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-400 flex items-center justify-between">
              <span>{profitFactor}</span>
              <TrendingUp className="size-5 text-purple-400 opacity-40" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Filter className="size-3.5" />
          <span>Filtrar:</span>
        </div>
        <div className="flex gap-1">
          {["TODOS", "WIN", "WDO", "NQ", "XAUUSD"].map((sym) => (
            <button
              key={sym}
              onClick={() => setFilterSymbol(sym)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors border ${
                filterSymbol === sym
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-card/60 text-muted-foreground border-border/40 hover:bg-card"
              }`}
            >
              {sym}
            </button>
          ))}
        </div>
        <div className="flex gap-1 ml-auto">
          {["TODOS", "WIN", "LOSS", "OPEN"].map((res) => (
            <button
              key={res}
              onClick={() => setFilterResult(res)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors border ${
                filterResult === res
                  ? "bg-secondary text-secondary-foreground border-secondary"
                  : "bg-card/60 text-muted-foreground border-border/40 hover:bg-card"
              }`}
            >
              {res}
            </button>
          ))}
        </div>
      </div>

      {/* Tabela de Trades */}
      <Card className="bg-card/70 border-border/60 overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-border/40 bg-muted/30">
                <TableHead className="text-xs">Data</TableHead>
                <TableHead className="text-xs">Ativo</TableHead>
                <TableHead className="text-xs">Direção</TableHead>
                <TableHead className="text-xs">Estratégia</TableHead>
                <TableHead className="text-xs">Entrada / Stop / Alvo</TableHead>
                <TableHead className="text-xs">R:R</TableHead>
                <TableHead className="text-xs">Resultado</TableHead>
                <TableHead className="text-xs text-right">PnL</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                    Carregando trades do Supabase...
                  </TableCell>
                </TableRow>
              ) : filteredTrades.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                    Nenhum trade encontrado nos filtros selecionados.
                  </TableCell>
                </TableRow>
              ) : (
                filteredTrades.map((t) => (
                  <TableRow key={t.id} className="border-border/40 hover:bg-muted/20">
                    <TableCell className="text-xs font-mono text-muted-foreground">
                      {new Date(t.trade_date).toLocaleDateString("pt-BR", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </TableCell>
                    <TableCell className="font-bold text-xs">{t.symbol}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          t.direction === "BUY"
                            ? "text-emerald-400 border-emerald-800/40 bg-emerald-950/20"
                            : "text-red-400 border-red-800/40 bg-red-950/20"
                        }
                      >
                        {t.direction}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs font-medium">{t.strategy}</TableCell>
                    <TableCell className="text-xs font-mono">
                      <span className="text-foreground">{t.entry_price}</span>
                      <span className="text-muted-foreground mx-1">/</span>
                      <span className="text-red-400">{t.stop_loss}</span>
                      <span className="text-muted-foreground mx-1">/</span>
                      <span className="text-emerald-400">{t.take_profit || t.exit_price || "-"}</span>
                    </TableCell>
                    <TableCell className="text-xs font-mono font-semibold">
                      {t.rr_achieved ? `1:${t.rr_achieved}` : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          t.result === "WIN"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                            : t.result === "LOSS"
                            ? "bg-red-500/20 text-red-400 border border-red-500/40"
                            : "bg-muted text-muted-foreground"
                        }
                      >
                        {t.result}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right text-xs font-mono font-bold">
                      <span className={(t.pnl || 0) >= 0 ? "text-emerald-400" : "text-red-400"}>
                        {(t.pnl || 0) >= 0 ? `+${(t.pnl || 0).toFixed(2)}` : (t.pnl || 0).toFixed(2)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
