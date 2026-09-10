"use client";

import { useEffect, useState } from "react";
import { fetchTodayChecklist, saveChecklist, LiveChecklist, ChecklistItem } from "@/lib/trading-db";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle2, ShieldCheck, ShieldAlert, AlertTriangle, Save, Flame, RefreshCw, Clock, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function ChecklistPage() {
  const [checklist, setChecklist] = useState<LiveChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadChecklist();
  }, []);

  async function loadChecklist() {
    setLoading(true);
    const data = await fetchTodayChecklist();
    setChecklist(data);
    setLoading(false);
  }

  function handleToggleItem(id: string) {
    if (!checklist) return;
    const updatedItems = checklist.items.map((item) =>
      item.id === id ? { ...item, checked: !item.checked } : item
    );

    // Recalcular Score
    const totalWeight = updatedItems.reduce((acc, it) => acc + it.weight, 0);
    const checkedWeight = updatedItems.filter((it) => it.checked).reduce((acc, it) => acc + it.weight, 0);
    const score = totalWeight > 0 ? Math.round((checkedWeight / totalWeight) * 100) : 0;
    const risk_approved = score >= 70;

    setChecklist({
      ...checklist,
      items: updatedItems,
      score,
      risk_approved,
    });
  }

  async function handleSave() {
    if (!checklist) return;
    setSaving(true);
    const ok = await saveChecklist(checklist);
    setSaving(false);
    if (ok) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  }

  function handleReset() {
    if (!checklist) return;
    const resetItems = checklist.items.map((it) => ({ ...it, checked: false }));
    setChecklist({
      ...checklist,
      items: resetItems,
      score: 0,
      risk_approved: false,
    });
  }

  if (loading || !checklist) {
    return (
      <div className="py-20 text-center text-muted-foreground flex flex-col items-center gap-3">
        <Clock className="size-8 animate-spin text-primary" />
        <span>Carregando checklist do pregão...</span>
      </div>
    );
  }

  const isApproved = checklist.risk_approved;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <ShieldCheck className="size-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Checklist ao Vivo · Pregão</h1>
            <Badge variant="outline" className="text-cyan-400 border-cyan-800/40 bg-cyan-950/20">
              Supabase Live
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Validação rígida de confluências institucionais e autorização de risco antes de cada clique.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReset} className="gap-1 text-xs">
            <RefreshCw className="size-3.5" />
            Resetar Sessão
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={saving}
            className="gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs"
          >
            <Save className="size-3.5" />
            {saving ? "Salvando..." : saveSuccess ? "Salvo no Supabase!" : "Salvar Sessão"}
          </Button>
        </div>
      </div>

      {/* Gate de Aprovação & Score */}
      <Card
        className={`border-2 transition-all shadow-lg ${
          isApproved
            ? "border-emerald-500/60 bg-gradient-to-br from-emerald-950/20 via-card/70 to-card/70"
            : "border-red-500/40 bg-gradient-to-br from-red-950/20 via-card/70 to-card/70"
        }`}
      >
        <CardContent className="p-5 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div
              className={`p-3 rounded-2xl ${
                isApproved ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
              }`}
            >
              {isApproved ? <CheckCircle2 className="size-8" /> : <ShieldAlert className="size-8" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Status do Gate de Risco
                </span>
                <Badge
                  className={
                    isApproved
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                      : "bg-red-500/20 text-red-400 border-red-500/40"
                  }
                >
                  {isApproved ? "OPERACÃO AUTORIZADA" : "BLOQUEADO · CONFLUÊNCIA BAIXA"}
                </Badge>
              </div>
              <h2 className="text-xl font-bold mt-1">
                {isApproved
                  ? "Critérios mínimos atingidos com disciplina."
                  : "Não execute até atingir ao menos 70% de confluência."}
              </h2>
            </div>
          </div>

          <div className="w-full md:w-64 space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-muted-foreground">Score de Confluência</span>
              <span className={isApproved ? "text-emerald-400" : "text-red-400"}>{checklist.score}%</span>
            </div>
            <Progress value={checklist.score} className="h-3" />
          </div>
        </CardContent>
      </Card>

      {/* Configuração da Sessão (Ativo e Viés) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Ativo Operado na Sessão
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {["B3 WIN", "B3 WDO", "NQ Futures", "XAUUSD", "BTC"].map((m) => (
                <button
                  key={m}
                  onClick={() => setChecklist({ ...checklist, market: m })}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold border transition-all ${
                    checklist.market === m
                      ? "bg-primary text-primary-foreground border-primary shadow-sm"
                      : "bg-card/60 text-muted-foreground border-border/40 hover:bg-card"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 border-border/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Viés Diário HTF (Higher Timeframe)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {[
                { id: "BULLISH", label: "BULLISH", icon: ArrowUpRight, color: "text-emerald-400" },
                { id: "BEARISH", label: "BEARISH", icon: ArrowDownRight, color: "text-red-400" },
                { id: "NEUTRO", label: "NEUTRO", icon: Clock, color: "text-amber-400" },
                { id: "NAO_OPERAR", label: "NÃO OPERAR", icon: AlertTriangle, color: "text-muted-foreground" },
              ].map((b) => (
                <button
                  key={b.id}
                  onClick={() => setChecklist({ ...checklist, bias: b.id as any })}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold border transition-all flex items-center justify-center gap-1 ${
                    checklist.bias === b.id
                      ? "bg-secondary text-secondary-foreground border-secondary shadow-sm"
                      : "bg-card/60 text-muted-foreground border-border/40 hover:bg-card"
                  }`}
                >
                  <b.icon className={`size-3.5 ${b.color}`} />
                  <span>{b.label}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Itens do Checklist */}
      <Card className="bg-card/70 border-border/60">
        <CardHeader className="pb-3 border-b border-border/40">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Flame className="size-4 text-primary" />
            Checklist de Confluências & Filtros Mecânicos
          </CardTitle>
          <CardDescription className="text-xs">
            Marque cada confluência observada em tela antes de enviar a ordem.
          </CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-border/40 p-0">
          {checklist.items.map((item) => (
            <div
              key={item.id}
              onClick={() => handleToggleItem(item.id)}
              className={`flex items-start gap-3 p-4 cursor-pointer transition-colors hover:bg-muted/20 ${
                item.checked ? "bg-muted/10" : ""
              }`}
            >
              <Checkbox
                checked={item.checked}
                onCheckedChange={() => handleToggleItem(item.id)}
                className="mt-0.5"
              />
              <div className="flex-1 text-xs">
                <span className={`font-medium ${item.checked ? "text-foreground line-through opacity-80" : "text-foreground"}`}>
                  {item.label}
                </span>
              </div>
              <Badge variant="outline" className="text-[10px] font-mono opacity-60">
                +{item.weight}%
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Notas de Observação do Pregão */}
      <Card className="bg-card/70 border-border/60">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
            Anotações & Observações da Sessão
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="Registre aqui as anotações do dia: comportamento dos players, liquidez deixada para trás, contexto macro..."
            rows={3}
            value={checklist.notes}
            onChange={(e) => setChecklist({ ...checklist, notes: e.target.value })}
            className="text-xs"
          />
        </CardContent>
      </Card>
    </div>
  );
}
