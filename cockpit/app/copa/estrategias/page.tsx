"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, Strategy, StatsPorEstrategia } from "@/lib/copa-api";
import { DEFAULT_STRATEGIES } from "@/data/strategies";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BookOpen,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  Layers,
  Play,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function EstrategiasCopaPage() {
  const [strategies, setStrategies] = React.useState<Strategy[]>(DEFAULT_STRATEGIES);
  const [statsStrat, setStatsStrat] = React.useState<StatsPorEstrategia[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    async function load() {
      try {
        const [strats, st] = await Promise.all([
          copaApi.getStrategies().catch(() => DEFAULT_STRATEGIES),
          copaApi.getStats().catch(() => ({ por_estrategia: [] } as any)),
        ]);
        if (strats && strats.length > 0) {
          setStrategies(strats);
        }
        if (st && st.por_estrategia) {
          setStatsStrat(st.por_estrategia);
        }
      } catch (err) {
        console.error("Erro ao carregar estratégias:", err);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="container py-8 space-y-6">
        <div className="h-64 rounded-xl bg-muted/30 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="container py-6 space-y-8">
      {/* Topo */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Fichas Técnicas das Estratégias</h1>
          <p className="text-sm text-muted-foreground">
            Modelos validados em arquivo de configuração. Estude os gatilhos, filtros de ambiente e pesos de confluência.
          </p>
        </div>
      </div>

      <div className="space-y-8">
        {strategies.map((strategy) => {
          const stratStat = statsStrat.find((s) => s.strategy_id === strategy.id);
          const kills = strategy.checklist.filter((i) => i.tipo === "KILL");
          const pontos = strategy.checklist.filter((i) => i.tipo === "PONTO");
          const somaPesos = pontos.reduce((acc, p) => acc + p.peso, 0);

          return (
            <Card key={strategy.id} className="border-border/80 shadow-sm overflow-hidden">
              <CardHeader className="bg-muted/20 pb-4 border-b">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl font-bold">{strategy.nome}</CardTitle>
                      <Badge variant="outline" className="font-mono text-xs">
                        {strategy.id}
                      </Badge>
                      <div className="flex gap-1">
                        {strategy.mercado.map((m) => (
                          <Badge key={m} className="font-mono font-bold text-xs">
                            {m}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <CardDescription className="text-sm text-foreground/90 mt-1">
                      {strategy.descricao}
                    </CardDescription>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link href={`/copa/novo?strategy=${strategy.id}`}>
                      <Button className="gap-1.5 font-bold bg-primary text-primary-foreground">
                        <Play className="h-4 w-4" /> Operar no Checklist
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Parâmetros Rápidos */}
                <div className="flex flex-wrap gap-4 pt-3 text-xs text-muted-foreground font-mono">
                  <div>
                    Score Mínimo: <span className="font-bold text-foreground">{strategy.score_minimo} pts</span> (Grade A)
                  </div>
                  <div>•</div>
                  <div>
                    Horários:{" "}
                    <span className="font-bold text-foreground">
                      {strategy.horarios_validos.map((h) => `${h.inicio}-${h.fim}`).join(", ")}
                    </span>
                  </div>
                  {stratStat && (
                    <>
                      <div>•</div>
                      <div className="text-emerald-400 font-bold">
                        Winrate Histórico: {stratStat.winrate.toFixed(1)}% ({stratStat.n} trades)
                      </div>
                    </>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-6 space-y-6">
                {/* Ambientes Favoráveis e Desfavoráveis */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Favorável */}
                  <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4 space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4" /> Onde o Modelo Funciona (Edge Alto)
                    </span>
                    <ul className="space-y-1 text-xs text-foreground/80 pl-4 list-disc">
                      {strategy.ambiente_favoravel.map((cond, i) => (
                        <li key={i}>{cond}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Desfavorável */}
                  <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-destructive flex items-center gap-1.5">
                      <XCircle className="h-4 w-4" /> Onde o Modelo Falha (Evitar / Reduzir Risco)
                    </span>
                    <ul className="space-y-1 text-xs text-foreground/80 pl-4 list-disc">
                      {strategy.ambiente_desfavoravel.map((cond, i) => (
                        <li key={i}>{cond}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Checklist Completo */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
                    Checklist & Critérios de Pontuação (Total: {somaPesos} pts)
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Itens KILL */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between pb-1 border-b">
                        <span className="text-xs font-bold text-destructive uppercase">
                          Itens KILL (Bloqueiam se faltar)
                        </span>
                        <span className="text-xs font-mono font-bold text-destructive">
                          {kills.length} itens obrigatórios
                        </span>
                      </div>
                      <div className="space-y-2">
                        {kills.map((k) => (
                          <div key={k.id} className="rounded-lg border bg-muted/20 p-2.5 space-y-0.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold text-foreground">{k.label}</span>
                              <Badge variant="destructive" className="text-[9px] py-0 font-bold">
                                KILL
                              </Badge>
                            </div>
                            {k.ajuda && (
                              <p className="text-[11px] text-muted-foreground">{k.ajuda}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Itens PONTO */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between pb-1 border-b">
                        <span className="text-xs font-bold text-primary uppercase">
                          Itens PONTO (Confluências)
                        </span>
                        <span className="text-xs font-mono font-bold text-primary">
                          {pontos.length} itens ({somaPesos} pts)
                        </span>
                      </div>
                      <div className="space-y-2">
                        {pontos.map((p) => (
                          <div key={p.id} className="rounded-lg border bg-muted/20 p-2.5 space-y-0.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold text-foreground">{p.label}</span>
                              <Badge variant="outline" className="text-[10px] font-mono font-bold py-0 text-primary border-primary">
                                +{p.peso} pts
                              </Badge>
                            </div>
                            {p.ajuda && (
                              <p className="text-[11px] text-muted-foreground">{p.ajuda}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
