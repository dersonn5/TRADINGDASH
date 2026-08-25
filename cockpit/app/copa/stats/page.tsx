"use client";

import * as React from "react";
import { copaApi, CopaStats } from "@/lib/copa-api";
import { StatsPorItemTable } from "@/components/copa/stats-por-item";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Award,
  AlertOctagon,
  Clock,
  Calendar,
  Layers,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function CopaStatsPage() {
  const [stats, setStats] = React.useState<CopaStats | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await copaApi.getStats();
        setStats(data);
      } catch (err) {
        console.error("Erro ao carregar estatísticas da Copa:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="container py-8 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted/30 animate-pulse" />
          ))}
        </div>
        <div className="h-64 rounded-xl bg-muted/30 animate-pulse" />
      </div>
    );
  }

  const geral = stats?.geral;
  const hasTrades = (geral?.trades || 0) > 0;

  return (
    <div className="container py-6 space-y-8">
      {/* Topo */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Estatísticas & Prova Matemática</h1>
        <p className="text-sm text-muted-foreground">
          Descubra quais confluências geram edge estatístico e quanto a indisciplina custou na Copa.
        </p>
      </div>

      {!hasTrades ? (
        <Card className="p-12 text-center border-dashed">
          <div className="max-w-md mx-auto space-y-3">
            <Badge variant="outline" className="text-xs">
              Aguardando Operações
            </Badge>
            <h2 className="text-xl font-bold">Nenhum Trade Fechado Ainda</h2>
            <p className="text-sm text-muted-foreground">
              Conforme você registrar e fechar trades com auditoria de disciplina, o motor estatístico
              calculará a curva de capital, o delta de winrate por item de checklist e o custo de desvios.
            </p>
          </div>
        </Card>
      ) : (
        <>
          {/* 1. KPIs GERAIS */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            {/* Total PnL */}
            <Card>
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px]">PnL Acumulado</CardDescription>
                <CardTitle
                  className={cn(
                    "text-xl font-mono font-bold",
                    (geral?.pnl_total ?? 0) >= 0 ? "text-emerald-400" : "text-destructive"
                  )}
                >
                  R$ {(geral?.pnl_total ?? 0).toFixed(2)}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground font-mono">
                  {geral?.trades} trades
                </span>
              </CardContent>
            </Card>

            {/* Winrate */}
            <Card>
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px]">Taxa de Acerto</CardDescription>
                <CardTitle
                  className={cn(
                    "text-xl font-mono font-bold",
                    (geral?.winrate ?? 0) >= 50 ? "text-emerald-400" : "text-amber-400"
                  )}
                >
                  {(geral?.winrate ?? 0).toFixed(1)}%
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground">de vitórias</span>
              </CardContent>
            </Card>

            {/* Profit Factor */}
            <Card>
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px]">Fator de Lucro (PF)</CardDescription>
                <CardTitle className="text-xl font-mono font-bold text-foreground">
                  {(geral?.profit_factor ?? 0).toFixed(2)}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground">ganhos / perdas</span>
              </CardContent>
            </Card>

            {/* Expectância */}
            <Card>
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px]">Expectância / Trade</CardDescription>
                <CardTitle
                  className={cn(
                    "text-xl font-mono font-bold",
                    (geral?.expectancia ?? 0) >= 0 ? "text-emerald-400" : "text-destructive"
                  )}
                >
                  R$ {(geral?.expectancia ?? 0).toFixed(2)}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground">média por clique</span>
              </CardContent>
            </Card>

            {/* Max Drawdown */}
            <Card>
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px]">Max Drawdown</CardDescription>
                <CardTitle className="text-xl font-mono font-bold text-destructive">
                  {(geral?.max_drawdown ?? 0).toFixed(1)}%
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground">queda do pico</span>
              </CardContent>
            </Card>

            {/* Custo Indisciplina */}
            <Card className="border-destructive/30 bg-destructive/5">
              <CardHeader className="p-4 pb-1">
                <CardDescription className="text-[11px] text-red-300">
                  Custo da Indisciplina
                </CardDescription>
                <CardTitle className="text-xl font-mono font-bold text-destructive">
                  R$ {(stats?.disciplina.custo_total ?? 0).toFixed(2)}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <span className="text-[10px] text-muted-foreground font-mono">
                  {stats?.disciplina.trades_com_desvio} trades com erro
                </span>
              </CardContent>
            </Card>
          </div>

          {/* 2. CURVA DE CAPITAL (EQUITY) */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Curva de Capital da Copa</CardTitle>
              <CardDescription className="text-xs">Evolução do saldo trade a trade.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats?.equity || []} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
                    <defs>
                      <linearGradient id="eqCopa" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#71717a" minTickGap={30} />
                    <YAxis tick={{ fontSize: 10 }} stroke="#71717a" domain={["auto", "auto"]} width={60} />
                    <Tooltip
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid #27272a",
                        borderRadius: 8,
                        fontSize: 12,
                        color: "#fafafa",
                      }}
                      formatter={(v) => [`R$ ${Number(v).toFixed(2)}`, "Saldo"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="balance"
                      stroke="#10b981"
                      strokeWidth={2}
                      fill="url(#eqCopa)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 3. BLOCO PRINCIPAL: O QUE ESTÁ PAGANDO (STATS POR ITEM) */}
          <Card>
            <CardContent className="pt-6">
              <StatsPorItemTable items={stats?.por_item || []} />
            </CardContent>
          </Card>

          {/* 4. BLOCO CUSTO DA INDISCIPLINA DETALHADO */}
          <Card className="border-destructive/30">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-destructive flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5" /> Auditoria: Custo da Indisciplina
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Diferença monetária (PnL Plano − PnL Real) provocada por quebras do plano operacional.
                  </CardDescription>
                </div>
                <div className="text-right">
                  <span className="text-xs text-muted-foreground block">Prejuízo Evitável:</span>
                  <span className="text-xl font-mono font-extrabold text-destructive">
                    R$ {(stats?.disciplina.custo_total ?? 0).toFixed(2)}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {stats?.disciplina.por_flag.map((item) => (
                  <div key={item.flag} className="rounded-lg border bg-muted/20 p-3 space-y-1">
                    <span className="text-xs font-semibold text-foreground uppercase tracking-wider block">
                      {item.flag.replace(/_/g, " ")}
                    </span>
                    <div className="flex justify-between items-baseline pt-1">
                      <span className="text-xs text-muted-foreground">{item.n} ocorrências</span>
                      <span
                        className={cn(
                          "font-mono font-bold text-sm",
                          item.custo > 0 ? "text-destructive" : "text-foreground"
                        )}
                      >
                        {item.custo > 0 ? `-R$ ${item.custo.toFixed(2)}` : "R$ 0.00"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 5. PERFORMANCE POR GRADE E POR ESTRATÉGIA */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Por Grade */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Performance por Grade (Score)</CardTitle>
                <CardDescription className="text-xs">
                  Validação se A+ realmente performa acima de B/C.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {stats?.por_grade.map((g) => (
                    <div
                      key={g.grade}
                      className="flex items-center justify-between p-2 rounded-lg border bg-muted/10 text-xs font-mono"
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-bold text-xs">
                          {g.grade}
                        </Badge>
                        <span className="text-muted-foreground">({g.n} trades)</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="font-semibold">{g.winrate.toFixed(1)}% WR</span>
                        <span
                          className={cn(
                            "font-bold",
                            g.pnl >= 0 ? "text-emerald-400" : "text-destructive"
                          )}
                        >
                          R$ {g.pnl.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}
                  {(!stats?.por_grade || stats.por_grade.length === 0) && (
                    <p className="text-xs text-muted-foreground italic">Sem dados de grade.</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Por Estratégia */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Performance por Estratégia</CardTitle>
                <CardDescription className="text-xs">Resultado consolidado por modelo.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {stats?.por_estrategia.map((s) => (
                    <div
                      key={s.strategy_id}
                      className="flex items-center justify-between p-2 rounded-lg border bg-muted/10 text-xs font-mono"
                    >
                      <div className="flex items-center gap-2 font-sans font-semibold">
                        <span>{s.nome}</span>
                        <span className="text-muted-foreground text-xs">({s.n} trades)</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="font-semibold">{s.winrate.toFixed(1)}% WR</span>
                        <span
                          className={cn(
                            "font-bold",
                            s.pnl >= 0 ? "text-emerald-400" : "text-destructive"
                          )}
                        >
                          R$ {s.pnl.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}
                  {(!stats?.por_estrategia || stats.por_estrategia.length === 0) && (
                    <p className="text-xs text-muted-foreground italic">Sem dados de estratégia.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 6. PERFORMANCE POR HORÁRIO E DIA DA SEMANA */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Por Hora */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Performance por Janela Horária</CardTitle>
                <CardDescription className="text-xs">Estatística por hora de abertura da operação.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                  {stats?.por_hora.map((h) => (
                    <div key={h.hora} className="p-2.5 rounded-lg border bg-muted/10 space-y-1">
                      <span className="text-muted-foreground font-sans font-semibold block">
                        {h.hora}:00 - {h.hora}:59
                      </span>
                      <div className="font-bold text-foreground">{h.winrate.toFixed(1)}% WR</div>
                      <div
                        className={cn(
                          "font-bold text-[11px]",
                          h.pnl >= 0 ? "text-emerald-400" : "text-destructive"
                        )}
                      >
                        R$ {h.pnl.toFixed(2)}
                      </div>
                      <span className="text-[10px] text-muted-foreground">({h.n} ops)</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Por Dia da Semana */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Performance por Dia da Semana</CardTitle>
                <CardDescription className="text-xs">Segunda a Sexta-feira.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-2 text-center text-xs font-mono">
                  {stats?.por_dia_semana.map((d) => (
                    <div key={d.dia} className="p-2.5 rounded-lg border bg-muted/10 space-y-1">
                      <span className="text-muted-foreground font-sans font-bold uppercase block">
                        {d.dia}
                      </span>
                      <div className="font-bold text-foreground">{d.winrate.toFixed(1)}%</div>
                      <div
                        className={cn(
                          "font-bold text-[11px]",
                          d.pnl >= 0 ? "text-emerald-400" : "text-destructive"
                        )}
                      >
                        R$ {d.pnl.toFixed(2)}
                      </div>
                      <span className="text-[10px] text-muted-foreground">({d.n} ops)</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
