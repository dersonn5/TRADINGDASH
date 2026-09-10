"use client";

import { useEffect, useState, useMemo } from "react";
import {
  fetchTodayChecklist,
  saveChecklist,
  LiveChecklist,
  ChecklistItem,
} from "@/lib/trading-db";
import {
  avaliarGate,
  classificarJanela,
  scoreMinimoEfetivo,
  GateResult,
  Janela,
} from "@/lib/gate";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  CheckCircle2,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Save,
  RefreshCw,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  XCircle,
  Zap,
} from "lucide-react";

export default function ChecklistPage() {
  const [checklist, setChecklist] = useState<LiveChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [now, setNow] = useState<Date>(() => new Date());

  // Atualizar o relógio a cada 30 segundos e limpar no unmount
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    loadChecklist();
  }, []);

  async function loadChecklist() {
    setLoading(true);
    const data = await fetchTodayChecklist();
    setChecklist(data);
    setLoading(false);
  }

  // Hora corrente formatada em America/Sao_Paulo
  const spTimeStr = useMemo(() => {
    try {
      return new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(now);
    } catch {
      return "--:--";
    }
  }, [now]);

  // Avaliação do Gate em tempo real com regras de horário e confluência
  const gate: GateResult = useMemo(() => {
    if (!checklist) {
      return {
        liberado: false,
        janela: "FORA",
        score: 0,
        scoreMinimo: 65,
        killsFaltando: [],
        motivos: [],
        avisos: [],
      };
    }
    return avaliarGate(
      checklist.items.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now
    );
  }, [checklist, now]);

  function handleToggleItem(id: string) {
    if (!checklist) return;
    const updatedItems = checklist.items.map((item) =>
      item.id === id ? { ...item, checked: !item.checked } : item
    );

    // Recalcular Score
    const nextGate = avaliarGate(
      updatedItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now
    );

    setChecklist({
      ...checklist,
      items: updatedItems,
      score: nextGate.score,
      risk_approved: nextGate.liberado,
    });
  }

  function handleBiasChange(newBias: LiveChecklist["bias"]) {
    if (!checklist) return;
    const nextGate = avaliarGate(
      checklist.items.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      newBias,
      now
    );

    setChecklist({
      ...checklist,
      bias: newBias,
      risk_approved: nextGate.liberado,
    });
  }

  async function handleSave() {
    if (!checklist) return;
    setSaving(true);
    const toSave: LiveChecklist = {
      ...checklist,
      score: gate.score,
      risk_approved: gate.liberado,
    };
    const ok = await saveChecklist(toSave);
    setSaving(false);
    if (ok) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  }

  function handleReset() {
    if (!checklist) return;
    const resetItems = checklist.items.map((it) => ({ ...it, checked: false }));
    const nextGate = avaliarGate(
      resetItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: false,
        peso: i.weight,
      })),
      checklist.bias,
      now
    );
    setChecklist({
      ...checklist,
      items: resetItems,
      score: nextGate.score,
      risk_approved: nextGate.liberado,
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

  const killItems = checklist.items.filter((i) => i.tipo === "KILL");
  const pontoItems = checklist.items.filter((i) => i.tipo === "PONTO");
  const killsCheckedCount = killItems.filter((i) => i.checked).length;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header Superior com Hora e Controles */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <ShieldCheck className="size-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Checklist ao Vivo · Pregão</h1>
            <Badge variant="outline" className="text-primary border-primary/40 bg-primary/10 font-mono text-xs">
              Playbook Anderson
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Validação estrita de itens obrigatórios KILL e confluências antes de qualquer entrada.
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
            className="gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold"
          >
            <Save className="size-3.5" />
            {saving ? "Salvando..." : saveSuccess ? "Salvo no Supabase!" : "Salvar Sessão"}
          </Button>
        </div>
      </div>

      {/* 5a. FAIXA DE GATE NO TOPO (Acima de tudo, sempre visível) */}
      <Card
        className={`border-2 transition-all shadow-lg overflow-hidden ${
          gate.liberado
            ? "border-emerald-500/80 bg-gradient-to-br from-emerald-950/40 via-card to-card"
            : "border-red-500/80 bg-gradient-to-br from-red-950/40 via-card to-card"
        }`}
      >
        <CardContent className="p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div
                className={`p-3 rounded-2xl shrink-0 ${
                  gate.liberado
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                    : "bg-red-500/20 text-red-400 ring-1 ring-red-500/40"
                }`}
              >
                {gate.liberado ? (
                  <CheckCircle2 className="size-8" />
                ) : (
                  <ShieldAlert className="size-8" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Status do Gate de Risco
                  </span>
                  <Badge
                    className={`font-mono font-bold text-xs tracking-wide px-2.5 py-0.5 ${
                      gate.liberado
                        ? "bg-emerald-500 text-black border-emerald-400 font-extrabold"
                        : "bg-red-500 text-white border-red-400 font-extrabold"
                    }`}
                  >
                    {gate.liberado ? "LIBERADO" : "BLOQUEADO"}
                  </Badge>
                </div>

                <h2 className="text-lg md:text-xl font-bold mt-1 text-foreground">
                  {gate.liberado
                    ? "Operação autorizada para execução no pregão."
                    : "Entrada proibida · critérios de proteção pendentes."}
                </h2>
              </div>
            </div>

            {/* 5b. Indicador de Janela e Horário de São Paulo */}
            <div className="shrink-0 p-3 rounded-xl border bg-background/60 space-y-1 text-right">
              <div className="flex items-center justify-end gap-1.5 text-xs text-muted-foreground font-mono">
                <Clock className="size-3.5" />
                <span>São Paulo: <b className="text-foreground">{spTimeStr}</b></span>
              </div>
              <div>
                {gate.janela === "PRIME" && (
                  <span className="text-xs font-bold text-emerald-400 inline-flex items-center gap-1">
                    <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                    JANELA NOBRE · 10:00–11:00 · score mínimo 65
                  </span>
                )}
                {gate.janela === "VALIDA" && (
                  <span className="text-xs font-bold text-amber-400 inline-flex items-center gap-1">
                    <span className="size-2 rounded-full bg-amber-400" />
                    Fora da janela nobre · score mínimo 80
                  </span>
                )}
                {gate.janela === "FORA" && (
                  <span className="text-xs font-bold text-red-400 inline-flex items-center gap-1">
                    <span className="size-2 rounded-full bg-red-400" />
                    Fora da janela de operação 09:00–12:00
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Motivos de Bloqueio (listados individualmente por linha quando bloqueado) */}
          {!gate.liberado && gate.motivos.length > 0 && (
            <div className="mt-3 p-4 rounded-xl bg-red-950/20 border border-red-500/30 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                <XCircle className="size-4 shrink-0" />
                Motivos de Bloqueio ({gate.motivos.length}):
              </span>
              <ul className="space-y-1 pl-1">
                {gate.motivos.map((motivo, idx) => (
                  <li key={idx} className="text-xs text-red-200 font-mono flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>{motivo}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Avisos em Âmbar (bloco separado dos motivos) */}
          {gate.avisos.length > 0 && (
            <div className="mt-2 p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 flex items-center gap-2">
              <AlertTriangle className="size-4 text-amber-400 shrink-0" />
              <span className="text-xs text-amber-300 font-mono font-medium">
                {gate.avisos.join(" · ")}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 5d. SCORE DE CONFLUÊNCIA & BARRA COM MARCAÇÃO */}
      <Card className="bg-card/70 border-border/60">
        <CardContent className="p-5 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Score de Confluência (Itens PONTO)
              </span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className={`text-3xl font-extrabold ${gate.score >= gate.scoreMinimo ? "text-emerald-400" : "text-foreground"}`}>
                  {gate.score}
                </span>
                <span className="text-sm text-muted-foreground font-mono">
                  / {gate.scoreMinimo === Number.POSITIVE_INFINITY ? "Bloqueado" : `${gate.scoreMinimo} pts mín.`}
                </span>
              </div>
            </div>

            <div className="text-xs font-mono text-muted-foreground">
              Exigência atual: <b className="text-foreground">{gate.scoreMinimo === Number.POSITIVE_INFINITY ? "Operação Bloqueada" : `${gate.scoreMinimo} pontos`}</b>
            </div>
          </div>

          {/* Barra de Progresso com marcador do score mínimo */}
          <div className="space-y-1 pt-1">
            <div className="relative">
              <Progress value={Math.min(100, gate.score)} className="h-3.5 bg-muted/60" />
              {gate.scoreMinimo <= 100 && (
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-primary z-10"
                  style={{ left: `${gate.scoreMinimo}%` }}
                  title={`Mínimo: ${gate.scoreMinimo} pts`}
                />
              )}
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>0 pts</span>
              <span>Meta Prime: 65 pts</span>
              <span>Meta Fora Nobre: 80 pts</span>
              <span>100 pts</span>
            </div>
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
              {["B3 WIN", "B3 WDO", "NQ Futures", "XAUUSD"].map((m) => (
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
                { id: "NAO_OPERAR", label: "NÃO OPERAR", icon: AlertTriangle, color: "text-red-400" },
              ].map((b) => (
                <button
                  key={b.id}
                  onClick={() => handleBiasChange(b.id as any)}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold border transition-all flex items-center justify-center gap-1 ${
                    checklist.bias === b.id
                      ? "bg-secondary text-secondary-foreground border-secondary ring-1 ring-primary/40 shadow-sm"
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

      {/* 5c. DOIS BLOCOS SEPARADOS: OBRIGATÓRIOS E CONFLUÊNCIA */}

      {/* BLOCO 1: OBRIGATÓRIOS (KILL) */}
      <Card className="bg-card/70 border-destructive/40 shadow-md">
        <CardHeader className="pb-3 border-b border-destructive/20 bg-destructive/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="destructive" className="font-mono text-[10px] uppercase font-bold tracking-wider">
                sem isso, não entra
              </Badge>
              <CardTitle className="text-sm font-bold text-destructive">
                ITENS OBRIGATÓRIOS (KILL)
              </CardTitle>
            </div>
            <span className="text-xs font-mono font-bold text-muted-foreground">
              {killsCheckedCount} de {killItems.length} marcados
            </span>
          </div>
          <CardDescription className="text-xs text-muted-foreground">
            A ausência de qualquer um destes 7 itens bloqueia fisicamente a operação.
          </CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-border/40 p-0">
          {killItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleToggleItem(item.id)}
              className={`flex items-start gap-3 p-4 cursor-pointer transition-colors hover:bg-destructive/5 ${
                item.checked ? "bg-destructive/10" : ""
              }`}
            >
              <Checkbox
                checked={item.checked}
                onCheckedChange={() => handleToggleItem(item.id)}
                className="mt-0.5 border-destructive data-[state=checked]:bg-destructive data-[state=checked]:text-destructive-foreground"
              />
              <div className="flex-1 space-y-1 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className={`font-semibold ${item.checked ? "text-foreground line-through opacity-70" : "text-foreground"}`}>
                    {item.label}
                  </span>
                  <Badge variant="destructive" className="text-[9px] py-0 px-1.5 font-bold shrink-0">
                    KILL
                  </Badge>
                </div>
                {item.ajuda && (
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    {item.ajuda}
                  </p>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* BLOCO 2: CONFLUÊNCIA (PONTO) */}
      <Card className="bg-card/70 border-primary/40 shadow-md">
        <CardHeader className="pb-3 border-b border-primary/20 bg-primary/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-primary border-primary/40 font-mono text-[10px] uppercase font-bold tracking-wider">
                soma 100 pontos
              </Badge>
              <CardTitle className="text-sm font-bold text-primary">
                ITENS DE CONFLUÊNCIA (PONTO)
              </CardTitle>
            </div>
            <span className="text-xs font-mono font-bold text-primary">
              {gate.score} pts acumulados
            </span>
          </div>
          <CardDescription className="text-xs text-muted-foreground">
            Critérios analíticos que fortalecem o edge probabilístico do setup.
          </CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-border/40 p-0">
          {pontoItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleToggleItem(item.id)}
              className={`flex items-start gap-3 p-4 cursor-pointer transition-colors hover:bg-primary/5 ${
                item.checked ? "bg-primary/10" : ""
              }`}
            >
              <Checkbox
                checked={item.checked}
                onCheckedChange={() => handleToggleItem(item.id)}
                className="mt-0.5 border-primary data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
              />
              <div className="flex-1 space-y-1 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className={`font-semibold ${item.checked ? "text-foreground line-through opacity-70" : "text-foreground"}`}>
                    {item.label}
                  </span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant="outline" className="text-[9px] font-mono font-bold text-amber-400 border-amber-700/40 bg-amber-950/20 py-0 px-1">
                      ESTIMADO
                    </Badge>
                    <Badge variant="outline" className="text-[10px] font-mono font-bold py-0 text-primary border-primary">
                      +{item.weight} pts
                    </Badge>
                  </div>
                </div>
                {item.ajuda && (
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    {item.ajuda}
                  </p>
                )}
              </div>
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
