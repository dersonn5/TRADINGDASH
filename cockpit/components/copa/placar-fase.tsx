import * as React from "react";
import { PlacarFaseResult } from "@/lib/copa-api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Trophy,
  ShieldCheck,
  ShieldAlert,
  Calendar,
  Layers,
  Coins,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PlacarFaseProps {
  placar: PlacarFaseResult;
}

export function PlacarFaseView({ placar }: PlacarFaseProps) {
  const {
    fase,
    dias = [],
    dias_operados = 0,
    dias_restantes = 0,
    placar_bruto = 0,
    placar_efetivo = 0,
    pior_dia,
    mulligan,
    contratos_total = 0,
    reais_por_contrato = 0,
  } = placar;

  if (!fase) {
    return (
      <Card className="p-12 text-center border-dashed">
        <div className="max-w-md mx-auto space-y-3">
          <Badge variant="outline" className="text-xs">
            Modo Treino / Fora de Fase Oficial
          </Badge>
          <h2 className="text-xl font-bold">Data Fora do Calendário da Copa</h2>
          <p className="text-sm text-muted-foreground">
            As fases oficiais da Copa BTG iniciam em 14/09/2026. As operações registradas nesta data
            são tratadas como treino e alimentam seu diário de bordo e estatísticas normais.
          </p>
        </div>
      </Card>
    );
  }

  const mulliganDisponivel = mulligan?.disponivel ?? true;

  return (
    <div className="space-y-6">
      {/* Cabeçalho da Fase */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Trophy className="h-6 w-6 text-amber-400" />
            <h2 className="text-2xl font-bold tracking-tight">{fase.nome}</h2>
            <Badge variant="outline" className="font-mono text-xs">
              {fase.id}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Período Oficial: <span className="font-mono">{fase.data_inicio}</span> até{" "}
            <span className="font-mono">{fase.data_fim}</span> ({fase.dias} pregões)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-muted-foreground block">Progresso da Fase:</span>
            <span className="text-sm font-bold font-mono">
              {dias_operados} / {fase.dias} dias operados ({dias_restantes} restantes)
            </span>
          </div>
        </div>
      </div>

      {/* Semáforo do Mulligan — Elemento mais importante de gestão da fase */}
      <div
        className={cn(
          "rounded-xl border p-5 transition-all shadow-xs",
          mulliganDisponivel
            ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-100"
            : "border-destructive/40 bg-destructive/15 text-red-100"
        )}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl font-bold",
                mulliganDisponivel
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-destructive/20 text-destructive border border-destructive/30"
              )}
            >
              {mulliganDisponivel ? (
                <ShieldCheck className="h-6 w-6" />
              ) : (
                <ShieldAlert className="h-6 w-6" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold uppercase tracking-wider">
                  {mulliganDisponivel ? "MULLIGAN DISPONÍVEL" : "MULLIGAN CONSUMIDO"}
                </span>
                <span
                  className={cn(
                    "px-2 py-0.5 text-xs font-semibold rounded-full",
                    mulliganDisponivel
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-destructive/30 text-destructive-foreground"
                  )}
                >
                  {fase.tem_descarte ? "1 Descarte Permitido" : "Sem Descarte Nesta Fase"}
                </span>
              </div>
              <p className="text-xs opacity-90 mt-1">
                {mulliganDisponivel
                  ? "Você ainda não teve dias negativos nesta fase. Um eventual dia ruim será 100% descartado do ranking oficial."
                  : `Mulligan consumido pelo dia ${mulligan?.consumido_por || "negativo"}. A partir de agora, qualquer novo dia negativo entrará direto no placar oficial. Limite de perda diária cortado pela metade e modo defensivo ativado.`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Dois Planares Lado a Lado: Bruto vs Efetivo */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Placar Efetivo (Oficial com Descarte) */}
        <Card className="border-primary/50 bg-primary/5 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-primary flex items-center gap-1.5">
                <Trophy className="h-4 w-4" /> Placar Efetivo Oficial da Copa
              </CardTitle>
              <Badge className="bg-primary text-primary-foreground text-xs font-semibold">
                Critério de Classificação
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Resultado em R$ com descarte automático do pior dia da fase.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            <div
              className={cn(
                "text-4xl font-mono font-black",
                placar_efetivo >= 0 ? "text-emerald-400" : "text-destructive"
              )}
            >
              R$ {placar_efetivo.toFixed(2)}
            </div>
            <span className="text-xs text-muted-foreground">
              {fase.tem_descarte && pior_dia && dias_operados >= 2
                ? `Descartado o dia ${pior_dia.data} (R$ ${pior_dia.pnl.toFixed(2)})`
                : "Sem descarte aplicado ainda"}
            </span>
          </CardContent>
        </Card>

        {/* Placar Bruto Real */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">Placar Bruto (Sem Descarte)</CardTitle>
              <Badge variant="outline" className="text-xs">
                Soma Real
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Soma literal de todos os pregões operados na fase.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            <div
              className={cn(
                "text-4xl font-mono font-bold",
                placar_bruto >= 0 ? "text-emerald-400" : "text-destructive"
              )}
            >
              R$ {placar_bruto.toFixed(2)}
            </div>
            <span className="text-xs text-muted-foreground">
              Total acumulado em caixa
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Eficiência de Contratos (Critério Oficial de Desempate da Copa) */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Coins className="h-4 w-4 text-amber-400" /> Eficiência de Contratos (Desempate Oficial)
              </CardTitle>
              <CardDescription className="text-xs">
                O regulamento da Copa BTG define como 1º critério de desempate quem operou o MENOR número de contratos.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div className="rounded-lg border bg-muted/20 p-3">
            <span className="text-xs text-muted-foreground uppercase font-semibold block">
              Contratos Acumulados
            </span>
            <span className="text-2xl font-mono font-bold text-foreground">
              {contratos_total} contratos
            </span>
          </div>

          <div className="rounded-lg border bg-muted/20 p-3">
            <span className="text-xs text-muted-foreground uppercase font-semibold block">
              Rentabilidade por Contrato
            </span>
            <span
              className={cn(
                "text-2xl font-mono font-bold",
                reais_por_contrato >= 0 ? "text-emerald-400" : "text-destructive"
              )}
            >
              R$ {reais_por_contrato.toFixed(2)} / ctr
            </span>
          </div>

          <div className="rounded-lg border bg-muted/20 p-3">
            <span className="text-xs text-muted-foreground uppercase font-semibold block">
              Alavancagem Média
            </span>
            <span className="text-2xl font-mono font-bold text-foreground">
              {dias_operados > 0 ? (contratos_total / dias_operados).toFixed(1) : "0.0"} ctr/dia
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Linha do Tempo dos Dias da Fase */}
      <div className="space-y-3">
        <h3 className="text-base font-bold tracking-tight">Evolução Dia a Dia da Fase</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {dias.map((d, index) => (
            <Card
              key={d.data}
              className={cn(
                "transition-all",
                d.descartado && "opacity-50 border-destructive/40 bg-destructive/5 line-through"
              )}
            >
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-mono font-bold block">
                    Dia {index + 1} • {d.data}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {d.trades} trades • {d.contratos} ctrs
                  </span>
                </div>
                {d.descartado && (
                  <Badge variant="destructive" className="text-[9px] uppercase font-bold py-0 no-underline">
                    DESCARTADO
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div
                  className={cn(
                    "text-xl font-mono font-bold",
                    d.pnl > 0 ? "text-emerald-400" : d.pnl < 0 ? "text-red-400" : "text-foreground"
                  )}
                >
                  R$ {d.pnl.toFixed(2)}
                </div>
              </CardContent>
            </Card>
          ))}

          {Array.from({ length: dias_restantes }).map((_, i) => (
            <Card key={`restante-${i}`} className="border-dashed bg-muted/10">
              <CardHeader className="p-4 pb-2">
                <span className="text-xs font-mono font-semibold text-muted-foreground">
                  Pregão Futuro #{dias_operados + i + 1}
                </span>
              </CardHeader>
              <CardContent className="p-4 pt-1 text-xs text-muted-foreground italic">
                Aguardando pregão
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
