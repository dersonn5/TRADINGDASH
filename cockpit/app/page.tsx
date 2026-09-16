import { api } from "@/lib/api";
import { EquityChart } from "@/components/equity-chart";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstNum,
  InstBadge,
  InstTable,
  InstRow,
  InstCell,
  InstEmpty,
} from "@/components/inst";

function KPI({
  label,
  value,
  sub,
  tom,
}: {
  label: string;
  value: string;
  sub?: string;
  tom?: "ok" | "now" | "block" | "neutro";
}) {
  return (
    <InstCard label={label}>
      <InstNum value={value} tom={tom} size="lg" />
      {sub && <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>{sub}</span>}
    </InstCard>
  );
}

export default async function Page() {
  const [m, eq, trades, lessons, status, meta] = await Promise.all([
    api.metrics(),
    api.equity(),
    api.trades(),
    api.lessons(),
    api.status(),
    api.meta(),
  ]);

  return (
    <InstPage
      eyebrow="COCKPIT GERAL"
      title={
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span>Visão Geral · Top-Down v2</span>
          {meta.sample && <InstBadge tom="now">dados de amostra</InstBadge>}
        </div>
      }
      right={
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <InstLabel>próx. killzone:</InstLabel>
          <span className="mono tabular" style={{ fontSize: "13px", fontWeight: 600 }}>
            {status.next_killzone}
          </span>
        </div>
      }
    >
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPI
          label="Profit Factor"
          value={m.profit_factor.toFixed(2)}
          tom={m.profit_factor >= 1 ? "ok" : "block"}
        />
        <KPI label="Win Rate" value={`${m.win_rate.toFixed(1)}%`} tom="neutro" />
        <KPI
          label="PnL líquido"
          value={`$${m.total_pnl.toFixed(0)}`}
          tom={m.total_pnl >= 0 ? "ok" : "block"}
        />
        <KPI
          label="Max Drawdown"
          value={`${m.max_drawdown.toFixed(1)}%`}
          tom="block"
        />
        <KPI label="Trades" value={`${m.trades}`} tom="neutro" />
        <KPI
          label="Expectância"
          value={`$${m.expectancy.toFixed(1)}`}
          sub="por trade"
          tom={m.expectancy >= 0 ? "ok" : "block"}
        />
      </div>

      <InstCard label="CURVA DE CAPITAL">
        <EquityChart data={eq} />
      </InstCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InstCard label="HISTÓRICO DE TRADES">
            {trades.length === 0 ? (
              <InstEmpty>sem trades ainda</InstEmpty>
            ) : (
              <div className="max-h-[420px] overflow-auto">
                <InstTable
                  colunas={[
                    "Data",
                    "Ativo",
                    "Lado",
                    "Grade",
                    "RR",
                    { label: "Resultado", align: "right" },
                    { label: "PnL", align: "right" },
                  ]}
                >
                  {trades.map((t) => (
                    <InstRow key={t.id} tom={t.result === "WIN" ? "ok" : "block"}>
                      <InstCell>
                        <span className="mono tabular" style={{ color: "var(--inst-faint)" }}>
                          {t.date}
                        </span>
                      </InstCell>
                      <InstCell>{t.symbol}</InstCell>
                      <InstCell>
                        <InstBadge tom={t.side === "BUY" ? "ok" : "block"}>{t.side}</InstBadge>
                      </InstCell>
                      <InstCell>
                        <InstBadge tom="neutro">{t.grade}</InstBadge>
                      </InstCell>
                      <InstCell>
                        <span className="mono tabular">{t.rr}</span>
                      </InstCell>
                      <InstCell align="right">
                        <InstNum
                          value={t.result}
                          tom={t.result === "WIN" ? "ok" : "block"}
                          size="sm"
                        />
                      </InstCell>
                      <InstCell align="right">
                        <InstNum
                          value={`${t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}`}
                          tom={t.pnl >= 0 ? "ok" : "block"}
                          size="sm"
                        />
                      </InstCell>
                    </InstRow>
                  ))}
                </InstTable>
              </div>
            )}
          </InstCard>
        </div>

        <div>
          <InstCard label="📓 LIÇÕES APRENDIDAS">
            <div className="space-y-3 max-h-[420px] overflow-auto">
              {lessons.map((l, i) => (
                <div
                  key={i}
                  style={{
                    borderLeft: "2px solid var(--inst-line-2)",
                    paddingLeft: "12px",
                  }}
                >
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--inst-text)" }}>
                    {l.title}
                  </div>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "var(--inst-dim)",
                      marginTop: "2px",
                      lineHeight: 1.4,
                    }}
                    className="line-clamp-3"
                  >
                    {l.snippet}
                  </div>
                </div>
              ))}
              {lessons.length === 0 && <InstEmpty>nenhuma lição registrada</InstEmpty>}
            </div>
          </InstCard>
        </div>
      </div>

      <p className="mono tabular text-center text-xs text-[var(--inst-faint)] pt-2">
        ICT Cognitive Cockpit · backend FastAPI :8010 · dados {meta.sample ? "de amostra" : "reais do backtest"}
      </p>
    </InstPage>
  );
}
