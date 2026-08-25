"use client";

import * as React from "react";
import Link from "next/link";
import { copaApi, GateResult, StrategyRanking, SessionDay, Trade } from "@/lib/copa-api";
import { GateBanner } from "@/components/copa/gate-banner";
import { RankingEstrategias } from "@/components/copa/ranking-estrategias";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  PlusCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  History,
  AlertCircle,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function CopaHomePage() {
  const hoje = new Date().toISOString().split("T")[0];

  const [session, setSession] = React.useState<SessionDay | null>(null);
  const [gate, setGate] = React.useState<GateResult | null>(null);
  const [ranking, setRanking] = React.useState<StrategyRanking[]>([]);
  const [todayTrades, setTodayTrades] = React.useState<Trade[]>([]);
  const [loading, setLoading] = React.useState(true);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const [sess, gateRes, rankRes, trades] = await Promise.all([
        copaApi.getSession(hoje),
        copaApi.getGate(hoje),
        copaApi.getRanking(hoje),
        copaApi.listTrades({ data: hoje }),
      ]);
      setSession(sess);
      setGate(gateRes);
      setRanking(rankRes);
      setTodayTrades(trades);
    } catch (err) {
      console.error("Erro ao carregar dados da home da Copa:", err);
    } finally {
      setLoading(false);
    }
  }, [hoje]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="container py-8 space-y-6">
        <div className="h-28 rounded-xl bg-muted/30 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted/30 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // ESTADO 1: Sem pré-sessão preenchida hoje
  if (!session) {
    return (
      <div className="container py-12 max-w-2xl mx-auto text-center space-y-6">
        <div className="flex justify-center">
          <div className="h-16 w-16 rounded-2xl bg-destructive/10 border border-destructive/30 flex items-center justify-center text-destructive">
            <Shield className="h-8 w-8" />
          </div>
        </div>

        <div className="space-y-2">
          <Badge variant="destructive" className="font-semibold uppercase tracking-wider">
            Gate Físico Travado
          </Badge>
          <h1 className="text-3xl font-bold tracking-tight">Pré-Sessão Não Preenchida</h1>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            A regra fundamental da Copa BTG é: nenhum trade é liberado sem o diagnóstico pré-mercado,
            mapeamento de liquidez e checagem de estado emocional.
          </p>
        </div>

        <Card className="border-border/60 bg-card/60 backdrop-blur-xs text-left p-6">
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
              O que você vai preencher em 60 segundos:
            </h3>
            <ul className="text-sm space-y-2 text-muted-foreground">
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                Viés macro (Bias D1 e H1) e contexto (Tendência / Range)
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                Níveis-chave de liquidez (PDH, PDL, EQH/EQL)
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                Agenda econômica de alto impacto
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                Estado do operador (sono, tilt e pressão)
              </li>
            </ul>
          </div>
        </Card>

        <div className="pt-2">
          <Link href="/copa/pre-sessao">
            <Button size="lg" className="gap-2 font-bold px-8 h-12 text-base">
              <FileText className="h-5 w-5" /> Preencher Pré-Sessão Agora
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // ESTADO 2: Com pré-sessão preenchida
  const pnlDia = gate?.breakers.pnl_dia ?? 0;
  const tradesDia = gate?.breakers.trades_dia ?? 0;
  const maxTradesDia = gate?.breakers.max_trades_dia ?? 3;
  const limitePerda = gate?.breakers.limite_perda_dia_efetivo ?? gate?.breakers.limite_perda_dia ?? 300;
  const perdasSeguidas = gate?.breakers.perdas_seguidas ?? 0;
  const distanciaLimitePerda = Math.max(0, limitePerda + pnlDia);

  return (
    <div className="container py-6 space-y-6">
      {/* Topo / Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Cockpit Operacional da Copa</h1>
            <Badge variant="outline" className="font-mono text-xs">
              {hoje}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Gate de disciplina e controle de risco para WIN / WDO na Copa BTG.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Link href="/copa/pre-sessao">
            <Button variant="outline" size="sm" className="gap-1.5">
              <FileText className="h-4 w-4" /> Editar Pré-Sessão
            </Button>
          </Link>

          <Link href="/copa/novo">
            <Button
              size="sm"
              disabled={!gate?.liberado}
              className="gap-1.5 font-bold bg-primary text-primary-foreground"
            >
              <PlusCircle className="h-4 w-4" /> Novo Trade (Checklist)
            </Button>
          </Link>
        </div>
      </div>

      {/* Banner Principal do Gate */}
      <GateBanner gate={gate} />

      {/* KPIs do Dia */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* PnL do Dia */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">PnL Fechado Hoje</CardDescription>
            <CardTitle
              className={cn(
                "text-2xl font-mono font-bold",
                pnlDia > 0 ? "text-emerald-400" : pnlDia < 0 ? "text-red-400" : "text-foreground"
              )}
            >
              R$ {pnlDia.toFixed(2)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              {pnlDia >= 0 ? "Dentro da expectativa" : "Monitorando perda"}
            </span>
          </CardContent>
        </Card>

        {/* Trades Usados */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Trades do Dia</CardDescription>
            <CardTitle className="text-2xl font-mono font-bold">
              {tradesDia} / {maxTradesDia}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              {maxTradesDia - tradesDia} restantes
            </span>
          </CardContent>
        </Card>

        {/* Distância pro Limite */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Folga para Limite de Perda</CardDescription>
            <CardTitle className="text-2xl font-mono font-bold text-foreground">
              R$ {distanciaLimitePerda.toFixed(2)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              Limite diário: R$ {limitePerda.toFixed(2)}
            </span>
          </CardContent>
        </Card>

        {/* Perdas Seguidas / Cooldown */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Sequência de Losses</CardDescription>
            <CardTitle
              className={cn(
                "text-2xl font-mono font-bold",
                perdasSeguidas > 0 ? "text-amber-400" : "text-foreground"
              )}
            >
              {perdasSeguidas} de {gate?.breakers.max_perdas_seguidas ?? 2}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-muted-foreground">
              {gate?.breakers.cooldown_ate
                ? `Cooldown até ${gate.breakers.cooldown_ate}`
                : "Sem cooldown ativo"}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Ranking de Estratégias do Dia */}
      <RankingEstrategias ranking={ranking} />

      {/* Trades Abertos ou Recentes do Dia */}
      {todayTrades.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base">Trades de Hoje ({todayTrades.length})</CardTitle>
              <CardDescription className="text-xs">Operações registradas no pregão atual.</CardDescription>
            </div>
            <Link href="/copa/trades">
              <Button variant="ghost" size="sm" className="gap-1 text-xs">
                Ver Journal Completo <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border/40">
              {todayTrades.map((t) => (
                <div key={t.id} className="py-2.5 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <Badge variant={t.status === "ABERTO" ? "default" : "outline"} className="text-xs">
                      {t.status}
                    </Badge>
                    <div>
                      <span className="text-sm font-semibold">
                        #{t.id} • {t.mercado} {t.direcao}
                      </span>
                      <span className="text-xs text-muted-foreground ml-2">
                        {t.strategy_id} (Grade {t.grade})
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-sm font-mono">
                    <span>
                      Entrada: {t.entrada} | Stop: {t.stop} | Alvo: {t.alvo}
                    </span>
                    {t.status === "FECHADO" && (
                      <span
                        className={cn(
                          "font-bold",
                          (t.pnl_real ?? 0) > 0
                            ? "text-emerald-400"
                            : (t.pnl_real ?? 0) < 0
                            ? "text-red-400"
                            : "text-foreground"
                        )}
                      >
                        R$ {(t.pnl_real ?? 0).toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
