// Cliente da API do cockpit (FastAPI em :8010)
const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8010";

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const r = await fetch(`${BASE}${path}`, { cache: "no-store" });
    if (!r.ok) return fallback;
    return (await r.json()) as T;
  } catch {
    return fallback;
  }
}

export type Metrics = {
  profit_factor: number; win_rate: number; total_pnl: number;
  max_drawdown: number; trades: number; expectancy: number; final_balance?: number;
};
export type EquityPoint = { t: string; balance: number };
export type Trade = {
  id: number; date: string; symbol: string; side: string; rr: number;
  result: string; pnl: number; grade: string; reason?: string;
};
export type Lesson = { title: string; snippet: string };
export type Status = { bot: string; mode: string; last_scan: string; next_killzone: string };

export const api = {
  metrics: () => get<Metrics>("/api/metrics", { profit_factor: 0, win_rate: 0, total_pnl: 0, max_drawdown: 0, trades: 0, expectancy: 0 }),
  equity: () => get<EquityPoint[]>("/api/equity", []),
  trades: () => get<Trade[]>("/api/trades", []),
  lessons: () => get<Lesson[]>("/api/lessons", []),
  status: () => get<Status>("/api/status", { bot: "?", mode: "?", last_scan: "", next_killzone: "" }),
  meta: () => get<{ sample: boolean; generated?: string }>("/api/meta", { sample: true }),
};
