"use client";

import * as React from "react";
import Link from "next/link";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  Layers,
  Play,
  Flame,
  Target,
  ArrowRight,
  BookOpen,
} from "lucide-react";

export default function EstrategiasTradingPage() {
  const [selectedId, setSelectedId] = React.useState<string>("playbook_anderson");
  const strategies = DEFAULT_STRATEGIES;
  const currentStrategy = strategies.find((s) => s.id === selectedId) || strategies[0];

  const kills = currentStrategy.checklist.filter((i) => i.tipo === "KILL");
  const pontos = currentStrategy.checklist.filter((i) => i.tipo === "PONTO");
  const somaPesos = pontos.reduce((acc, p) => acc + p.peso, 0);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Activity className="size-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Estratégias & Playbooks Validados</h1>
            <Badge variant="outline" className="text-emerald-400 border-emerald-800/40 bg-emerald-950/20">
              Operacional Ativo
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Parâmetros mecânicos, condições de ambiente e regras de execução de cada modelo institucional.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/checklist">
            <Button className="gap-2 bg-gradient-to-r from-primary to-cyan-600 hover:from-primary/90 hover:to-cyan-600/90 text-primary-foreground shadow-lg shadow-primary/20">
              <Play className="size-4" />
              Operar no Checklist
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs / Seletor de Estratégias */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {strategies.map((strat) => {
          const isSelected = strat.id === selectedId;
          return (
            <div
              key={strat.id}
              onClick={() => setSelectedId(strat.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-card border-primary ring-1 ring-primary/40 shadow-md"
                  : "bg-card/50 border-border/60 hover:bg-card hover:border-border"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-foreground">{strat.nome}</span>
                <div className="flex gap-1">
                  {strat.mercado.map((m) => (
                    <Badge key={m} variant="outline" className="text-[10px] font-mono font-bold">
                      {m}
                    </Badge>
                  ))}
                </div>
              </div>
              <p className="text-xs text-muted-foreground line-clamp-2 mt-2 leading-relaxed">
                {strat.descricao}
              </p>
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/40 text-[11px]">
                <span className="text-muted-foreground">Score Mín: <b className="text-foreground">{strat.score_minimo} pts</b></span>
                <span className="text-cyan-400 font-semibold flex items-center gap-1">
                  {strat.checklist.length} itens <ArrowRight className="size-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detalhes da Estratégia Selecionada */}
      <Card className="border-border/80 shadow-md overflow-hidden bg-card/70">
        <CardHeader className="bg-muted/20 pb-5 border-b border-border/40">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl font-bold">{currentStrategy.nome}</CardTitle>
                <Badge variant="outline" className="font-mono text-xs text-primary border-primary">
                  {currentStrategy.id}
                </Badge>
              </div>
              <CardDescription className="text-sm text-foreground/90 mt-1 max-w-3xl leading-relaxed">
                {currentStrategy.descricao}
              </CardDescription>
            </div>

            <Link href={`/copa/novo?strategy=${currentStrategy.id}`}>
              <Button className="gap-2 font-bold bg-emerald-600 hover:bg-emerald-700 text-white shrink-0">
                <Play className="size-4" /> Iniciar com este Playbook
              </Button>
            </Link>
          </div>

          {/* Parâmetros e Horários */}
          <div className="flex flex-wrap gap-4 pt-3 text-xs text-muted-foreground font-mono">
            <div className="flex items-center gap-1">
              <Clock className="size-3.5 text-primary" />
              <span>Janela de Operação:</span>{" "}
              <b className="text-foreground">
                {currentStrategy.horarios_validos.map((h) => `${h.inicio} às ${h.fim}`).join(", ")}
              </b>
            </div>
            <div>•</div>
            <div className="flex items-center gap-1">
              <Target className="size-3.5 text-cyan-400" />
              <span>Score Mínimo:</span> <b className="text-foreground">{currentStrategy.score_minimo} pontos</b>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {/* Ambientes Favoráveis e Desfavoráveis */}
          {currentStrategy.ambiente_favoravel && currentStrategy.ambiente_favoravel.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="size-4" /> Ambiente Ideal (Edge Institucional Alto)
                </span>
                <ul className="space-y-1.5 text-xs text-foreground/80 pl-4 list-disc">
                  {currentStrategy.ambiente_favoravel.map((cond, i) => (
                    <li key={i}>{cond}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-red-500/30 bg-red-950/10 p-4 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                  <XCircle className="size-4" /> Ambiente Tóxico (Evitar / Abortar Ordem)
                </span>
                <ul className="space-y-1.5 text-xs text-foreground/80 pl-4 list-disc">
                  {currentStrategy.ambiente_desfavoravel.map((cond, i) => (
                    <li key={i}>{cond}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Checklist Detalhado */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
              <Flame className="size-4 text-primary" />
              Critérios de Validação & Pontuação (Total de Confluências: {somaPesos} pts)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Itens KILL */}
              <div className="space-y-2">
                <div className="flex items-center justify-between pb-1 border-b border-border/40">
                  <span className="text-xs font-bold text-red-400 uppercase">
                    Itens Mandatórios (KILL)
                  </span>
                  <span className="text-xs font-mono font-bold text-red-400">
                    {kills.length} obrigatórios
                  </span>
                </div>
                <div className="space-y-2">
                  {kills.map((k) => (
                    <div key={k.id} className="rounded-lg border border-red-900/30 bg-red-950/10 p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground">{k.label}</span>
                        <Badge variant="destructive" className="text-[9px] py-0 font-bold">
                          KILL
                        </Badge>
                      </div>
                      {k.ajuda && <p className="text-[11px] text-muted-foreground">{k.ajuda}</p>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Itens PONTO */}
              <div className="space-y-2">
                <div className="flex items-center justify-between pb-1 border-b border-border/40">
                  <span className="text-xs font-bold text-primary uppercase">
                    Itens de Confluência (PONTOS)
                  </span>
                  <span className="text-xs font-mono font-bold text-primary">
                    {pontos.length} itens ({somaPesos} pts)
                  </span>
                </div>
                <div className="space-y-2">
                  {pontos.map((p) => (
                    <div key={p.id} className="rounded-lg border border-border/60 bg-muted/20 p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground">{p.label}</span>
                        <Badge variant="outline" className="text-[10px] font-mono font-bold py-0 text-primary border-primary/50">
                          +{p.peso} pts
                        </Badge>
                      </div>
                      {p.ajuda && <p className="text-[11px] text-muted-foreground">{p.ajuda}</p>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
