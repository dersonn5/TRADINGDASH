"use client";

import { useEffect, useState } from "react";
import { fetchTrades, saveTrade, TradingTrade } from "@/lib/trading-db";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstBadge,
  InstNum,
  InstTable,
  InstRow,
  InstEmpty,
} from "@/components/inst";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plus, Filter, ShieldCheck } from "lucide-react";

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

  const inputStyle: React.CSSProperties = {
    background: "var(--inst-panel-2)",
    border: "1px solid var(--inst-line)",
    color: "var(--inst-text)",
    borderRadius: "3px",
    padding: "8px 12px",
    fontSize: "13px",
    outline: "none",
    width: "100%",
  };

  return (
    <InstPage
      eyebrow="SUPABASE · HISTÓRICO"
      title="Banco de Todos os Trades"
      right={
        <button
          type="button"
          onClick={() => setIsDialogOpen(true)}
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
          <Plus style={{ width: "14px", height: "14px" }} /> Registrar Novo Trade
        </button>
      }
    >
      {/* Header */}
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Histórico completo de execuções reais, cálculo de R:R e métricas de desempenho.
      </div>

      {/* Botão e Modal Novo Trade */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            <ShieldCheck className="size-5 text-emerald-400" />
            Registrar Operação no Banco de Trades
          </DialogTitle>
        </DialogHeader>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px", paddingTop: "8px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Ativo</InstLabel>
              <input
                placeholder="WIN, WDO, NQ, BTC"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="mono"
                style={{ ...inputStyle, fontWeight: 700, textTransform: "uppercase" }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Direção</InstLabel>
              <select
                className="mono"
                style={{ ...inputStyle, height: "37px" }}
                value={direction}
                onChange={(e) => setDirection(e.target.value as "BUY" | "SELL")}
              >
                <option value="BUY">BUY (Compra)</option>
                <option value="SELL">SELL (Venda)</option>
              </select>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Lotes / Contratos</InstLabel>
              <input
                type="number"
                value={contracts}
                onChange={(e) => setContracts(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Estratégia</InstLabel>
              <input
                placeholder="Silver Bullet, Breaker Block, etc."
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Sessão / Horário</InstLabel>
              <input
                placeholder="B3 Abertura, NY AM, London"
                value={session}
                onChange={(e) => setSession(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "8px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Entrada</InstLabel>
              <input
                type="number"
                step="any"
                placeholder="131250"
                value={entryPrice || ""}
                onChange={(e) => setEntryPrice(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Stop Loss</InstLabel>
              <input
                type="number"
                step="any"
                placeholder="131050"
                value={stopLoss || ""}
                onChange={(e) => setStopLoss(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Take Profit</InstLabel>
              <input
                type="number"
                step="any"
                placeholder="131750"
                value={takeProfit || ""}
                onChange={(e) => setTakeProfit(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Saída Real</InstLabel>
              <input
                type="number"
                step="any"
                placeholder="131750"
                value={exitPrice || ""}
                onChange={(e) => setExitPrice(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Resultado</InstLabel>
              <select
                className="mono"
                style={{ ...inputStyle, height: "37px" }}
                value={result}
                onChange={(e) => setResult(e.target.value as "WIN" | "LOSS" | "BE" | "OPEN")}
              >
                <option value="WIN">WIN (Ganho)</option>
                <option value="LOSS">LOSS (Perda)</option>
                <option value="BE">BE (Zero a Zero)</option>
                <option value="OPEN">OPEN (Em aberto)</option>
              </select>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>PnL Financeiro ($/R$)</InstLabel>
              <input
                type="number"
                step="any"
                placeholder="+200 ou -100"
                value={pnl || ""}
                onChange={(e) => setPnl(Number(e.target.value))}
                className="mono tabular"
                style={{ ...inputStyle, fontWeight: 700 }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Score Confluência</InstLabel>
              <input
                type="number"
                min="0"
                max="100"
                value={confluenceScore}
                onChange={(e) => setConfluenceScore(Number(e.target.value))}
                className="mono tabular"
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <InstLabel>Anotações do Trade</InstLabel>
            <textarea
              placeholder="Contexto: liquidez varrida, comportamento do candle, reação no FVG..."
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ ...inputStyle, fontFamily: "inherit" }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <InstLabel>Erros & Lições Aprendidas</InstLabel>
            <textarea
              placeholder="O que funcionou bem? Houve hesitação ou quebra de plano?"
              rows={2}
              value={mistakes}
              onChange={(e) => setMistakes(e.target.value)}
              style={{ ...inputStyle, fontFamily: "inherit" }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", paddingTop: "8px" }}>
            <button
              type="button"
              onClick={() => setIsDialogOpen(false)}
              className="mono tabular"
              style={{
                background: "transparent",
                border: "1px solid var(--inst-line)",
                color: "var(--inst-dim)",
                borderRadius: "3px",
                padding: "8px 16px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleCreateTrade}
              disabled={saving || !symbol || entryPrice <= 0 || stopLoss <= 0}
              className="mono tabular"
              style={{
                background: "var(--inst-ok)",
                border: "1px solid var(--inst-ok)",
                color: "var(--inst-on-ok)",
                borderRadius: "3px",
                padding: "8px 16px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: saving || !symbol || entryPrice <= 0 || stopLoss <= 0 ? "not-allowed" : "pointer",
                opacity: saving || !symbol || entryPrice <= 0 || stopLoss <= 0 ? 0.6 : 1,
              }}
            >
              {saving ? "Registrando..." : "Salvar no Supabase"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* KPIs Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
        <InstCard>
          <InstLabel>Total de Trades</InstLabel>
          <div style={{ marginTop: "6px" }}>
            <InstNum value={totalTrades} size="lg" />
          </div>
        </InstCard>

        <InstCard>
          <InstLabel>Taxa de Acerto (Win Rate)</InstLabel>
          <div style={{ marginTop: "6px" }}>
            <InstNum
              value={`${winRate}%`}
              tom={Number(winRate) >= 50 ? "ok" : totalTrades > 0 ? "block" : "neutro"}
              size="lg"
            />
          </div>
          <div className="mono tabular" style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "4px" }}>
            {wins} W · {losses} L
          </div>
        </InstCard>

        <InstCard>
          <InstLabel>PnL Líquido Acumulado</InstLabel>
          <div style={{ marginTop: "6px" }}>
            <InstNum
              value={totalPnL >= 0 ? `+${totalPnL.toFixed(2)}` : totalPnL.toFixed(2)}
              tom={totalPnL > 0 ? "ok" : totalPnL < 0 ? "block" : "neutro"}
              size="lg"
            />
          </div>
        </InstCard>

        <InstCard>
          <InstLabel>Fator de Lucro</InstLabel>
          <div style={{ marginTop: "6px" }}>
            <InstNum
              value={profitFactor}
              tom={profitFactor !== "0.00" && profitFactor !== "NaN" ? "ok" : "neutro"}
              size="lg"
            />
          </div>
        </InstCard>
      </div>

      {/* Filtros */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
          padding: "10px 14px",
          background: "var(--inst-panel)",
          border: "1px solid var(--inst-line)",
          borderRadius: "3px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Filter style={{ width: "13px", height: "13px", color: "var(--inst-dim)" }} />
          <InstLabel>Filtrar:</InstLabel>
        </div>

        <div style={{ display: "flex", gap: "4px" }}>
          {["TODOS", "WIN", "WDO", "NQ", "XAUUSD"].map((sym) => {
            const active = filterSymbol === sym;
            return (
              <button
                key={sym}
                onClick={() => setFilterSymbol(sym)}
                className="mono tabular"
                style={{
                  padding: "4px 10px",
                  borderRadius: "2px",
                  fontSize: "11px",
                  fontWeight: active ? 700 : 500,
                  cursor: "pointer",
                  background: active ? "var(--inst-panel-2)" : "transparent",
                  border: active ? "1px solid var(--inst-text)" : "1px solid var(--inst-line)",
                  color: active ? "var(--inst-text)" : "var(--inst-dim)",
                }}
              >
                {sym}
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: "4px", marginLeft: "auto" }}>
          {["TODOS", "WIN", "LOSS", "OPEN"].map((res) => {
            const active = filterResult === res;
            return (
              <button
                key={res}
                onClick={() => setFilterResult(res)}
                className="mono tabular"
                style={{
                  padding: "4px 10px",
                  borderRadius: "2px",
                  fontSize: "11px",
                  fontWeight: active ? 700 : 500,
                  cursor: "pointer",
                  background: active ? "var(--inst-panel-2)" : "transparent",
                  border: active ? "1px solid var(--inst-text)" : "1px solid var(--inst-line)",
                  color: active ? "var(--inst-text)" : "var(--inst-dim)",
                }}
              >
                {res}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tabela de Trades */}
      <InstTable
        colunas={[
          { label: "Data" },
          { label: "Ativo" },
          { label: "Direção" },
          { label: "Estratégia" },
          { label: "Entrada / Stop / Alvo" },
          { label: "R:R" },
          { label: "Resultado" },
          { label: "PnL", align: "right" },
        ]}
      >
        {loading ? (
          <InstRow>
            <td colSpan={8} style={{ padding: "20px" }}>
              <InstEmpty>Carregando trades do Supabase...</InstEmpty>
            </td>
          </InstRow>
        ) : filteredTrades.length === 0 ? (
          <InstRow>
            <td colSpan={8} style={{ padding: "20px" }}>
              <InstEmpty>Nenhum trade encontrado nos filtros selecionados.</InstEmpty>
            </td>
          </InstRow>
        ) : (
          filteredTrades.map((t) => {
            const tomRow = t.result === "WIN" ? "ok" : t.result === "LOSS" ? "block" : "neutro";
            return (
              <InstRow key={t.id} tom={tomRow}>
                <td className="mono tabular" style={{ padding: "10px 16px", fontSize: "11px", color: "var(--inst-dim)" }}>
                  {new Date(t.trade_date).toLocaleDateString("pt-BR", {
                    day: "2-digit",
                    month: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </td>
                <td style={{ padding: "10px 16px", fontSize: "12px", fontWeight: 700, color: "var(--inst-text)" }}>
                  {t.symbol}
                </td>
                <td style={{ padding: "10px 16px" }}>
                  <InstBadge tom={t.direction === "BUY" ? "ok" : "block"}>
                    {t.direction}
                  </InstBadge>
                </td>
                <td style={{ padding: "10px 16px", fontSize: "12px", color: "var(--inst-text)" }}>
                  {t.strategy}
                </td>
                <td className="mono tabular" style={{ padding: "10px 16px", fontSize: "12px" }}>
                  <span style={{ color: "var(--inst-text)" }}>{t.entry_price}</span>
                  <span style={{ color: "var(--inst-dim)", margin: "0 4px" }}>/</span>
                  <span style={{ color: "var(--inst-block)" }}>{t.stop_loss}</span>
                  <span style={{ color: "var(--inst-dim)", margin: "0 4px" }}>/</span>
                  <span style={{ color: "var(--inst-ok)" }}>{t.take_profit || t.exit_price || "-"}</span>
                </td>
                <td className="mono tabular" style={{ padding: "10px 16px", fontSize: "12px", color: "var(--inst-text)" }}>
                  {t.rr_achieved ? `1:${t.rr_achieved}` : "-"}
                </td>
                <td style={{ padding: "10px 16px" }}>
                  <InstBadge tom={t.result === "WIN" ? "ok" : t.result === "LOSS" ? "block" : "neutro"}>
                    {t.result}
                  </InstBadge>
                </td>
                <td style={{ padding: "10px 16px", textAlign: "right" }}>
                  <InstNum
                    value={(t.pnl || 0) >= 0 ? `+${(t.pnl || 0).toFixed(2)}` : (t.pnl || 0).toFixed(2)}
                    tom={(t.pnl || 0) > 0 ? "ok" : (t.pnl || 0) < 0 ? "block" : "neutro"}
                    size="sm"
                  />
                </td>
              </InstRow>
            );
          })
        )}
      </InstTable>
    </InstPage>
  );
}
