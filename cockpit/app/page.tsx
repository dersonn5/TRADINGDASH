import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EquityChart } from "@/components/equity-chart";

function KPI({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "up" | "down" | "neutral" }) {
  const color = tone === "up" ? "text-emerald-500" : tone === "down" ? "text-red-500" : "text-foreground";
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
      </CardContent>
    </Card>
  );
}

export default async function Page() {
  const [m, eq, trades, lessons, status, meta] = await Promise.all([
    api.metrics(), api.equity(), api.trades(), api.lessons(), api.status(), api.meta(),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            Visão Geral · Top-Down v2
            {meta.sample && <Badge variant="outline" className="text-amber-500 border-amber-500">dados de amostra</Badge>}
          </h1>
          <p className="text-sm text-muted-foreground">Desempenho do robô inteligente</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">próx. killzone: <b className="text-foreground">{status.next_killzone}</b></span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPI label="Profit Factor" value={m.profit_factor.toFixed(2)} tone={m.profit_factor >= 1 ? "up" : "down"} />
        <KPI label="Win Rate" value={`${m.win_rate.toFixed(1)}%`} />
        <KPI label="PnL líquido" value={`$${m.total_pnl.toFixed(0)}`} tone={m.total_pnl >= 0 ? "up" : "down"} />
        <KPI label="Max Drawdown" value={`${m.max_drawdown.toFixed(1)}%`} tone="down" />
        <KPI label="Trades" value={`${m.trades}`} />
        <KPI label="Expectância" value={`$${m.expectancy.toFixed(1)}`} sub="por trade" tone={m.expectancy >= 0 ? "up" : "down"} />
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Curva de Capital</CardTitle></CardHeader>
        <CardContent><EquityChart data={eq} /></CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2"><CardTitle className="text-sm">Histórico de Trades</CardTitle></CardHeader>
          <CardContent>
            <div className="max-h-[420px] overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead><TableHead>Ativo</TableHead><TableHead>Lado</TableHead>
                    <TableHead>Grade</TableHead><TableHead>RR</TableHead>
                    <TableHead className="text-right">Resultado</TableHead><TableHead className="text-right">PnL</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell className="text-xs text-muted-foreground">{t.date}</TableCell>
                      <TableCell>{t.symbol}</TableCell>
                      <TableCell><Badge variant={t.side === "BUY" ? "default" : "secondary"}>{t.side}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{t.grade}</Badge></TableCell>
                      <TableCell>{t.rr}</TableCell>
                      <TableCell className="text-right">
                        <span className={t.result === "WIN" ? "text-emerald-500" : "text-red-500"}>{t.result}</span>
                      </TableCell>
                      <TableCell className={`text-right font-medium ${t.pnl >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                        {t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {trades.length === 0 && (
                    <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">sem trades ainda</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">📓 Lições Aprendidas</CardTitle></CardHeader>
          <CardContent className="space-y-3 max-h-[420px] overflow-auto">
            {lessons.map((l, i) => (
              <div key={i} className="border-l-2 border-primary/50 pl-3">
                <div className="text-sm font-medium">{l.title}</div>
                <div className="text-xs text-muted-foreground line-clamp-3">{l.snippet}</div>
              </div>
            ))}
            {lessons.length === 0 && <div className="text-sm text-muted-foreground">nenhuma lição registrada</div>}
          </CardContent>
        </Card>
      </div>

      <p className="text-center text-xs text-muted-foreground pt-4">
        ICT Cognitive Cockpit · backend FastAPI :8010 · dados {meta.sample ? "de amostra" : "reais do backtest"}
      </p>
    </div>
  );
}
