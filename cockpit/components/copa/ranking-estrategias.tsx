import * as React from "react";
import Link from "next/link";
import { StrategyRanking } from "@/lib/copa-api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, XCircle, ArrowRight, Play } from "lucide-react";
import { cn } from "@/lib/utils";

interface RankingEstrategiasProps {
  ranking: StrategyRanking[];
  loading?: boolean;
}

export function RankingEstrategias({ ranking, loading }: RankingEstrategiasProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-40 rounded-xl border bg-muted/30 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!ranking || ranking.length === 0) {
    return (
      <div className="rounded-xl border border-dashed p-8 text-center text-muted-foreground">
        Nenhuma estratégia configurada.
      </div>
    );
  }

  const ambienteBadge = (ambiente: string) => {
    switch (ambiente) {
      case "FAVORAVEL":
        return (
          <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 gap-1 font-semibold">
            <CheckCircle2 className="h-3 w-3" /> FAVORÁVEL HOJE
          </Badge>
        );
      case "DESFAVORAVEL":
        return (
          <Badge className="bg-destructive/20 text-destructive border border-destructive/30 gap-1 font-semibold">
            <XCircle className="h-3 w-3" /> DESFAVORÁVEL
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground gap-1 font-semibold">
            <AlertCircle className="h-3 w-3" /> NEUTRA
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight">Estratégias para Hoje</h2>
          <p className="text-xs text-muted-foreground">
            Recomendações automáticas derivadas do contexto da sua pré-sessão.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ranking.map((item) => {
          const isFavoravel = item.ambiente === "FAVORAVEL";
          const isDesfavoravel = item.ambiente === "DESFAVORAVEL";

          return (
            <Card
              key={item.strategy_id}
              className={cn(
                "flex flex-col justify-between transition-all hover:border-primary/50",
                isFavoravel && "border-emerald-500/30 bg-emerald-950/10",
                isDesfavoravel && "border-destructive/20 opacity-80"
              )}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base font-semibold">{item.nome}</CardTitle>
                  {ambienteBadge(item.ambiente)}
                </div>
                <CardDescription className="text-xs">
                  ID: <span className="font-mono">{item.strategy_id}</span>
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3 flex-1 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold text-muted-foreground uppercase">
                    Diagnóstico de Ambiente:
                  </span>
                  {item.motivos.length > 0 ? (
                    <ul className="mt-1 space-y-1 text-xs">
                      {item.motivos.map((motivo, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-muted-foreground">
                          <span className="text-primary">•</span>
                          <span>{motivo}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-1 text-xs text-muted-foreground italic">
                      Nenhuma restrição específica ativada.
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t">
                  <Link href={`/copa/novo?strategy=${item.strategy_id}`} className="w-full">
                    <Button
                      variant={isFavoravel ? "default" : "outline"}
                      size="sm"
                      className="w-full gap-2 font-medium"
                    >
                      <Play className="h-3.5 w-3.5" /> Operar com este Checklist
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
