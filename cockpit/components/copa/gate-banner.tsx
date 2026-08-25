import * as React from "react";
import { GateResult } from "@/lib/copa-api";
import { ShieldCheck, ShieldAlert, AlertTriangle, Lock, Unlock } from "lucide-react";
import { cn } from "@/lib/utils";

interface GateBannerProps {
  gate: GateResult | null;
  loading?: boolean;
}

export function GateBanner({ gate, loading }: GateBannerProps) {
  if (loading) {
    return (
      <div className="w-full rounded-xl border bg-muted/40 p-6 animate-pulse">
        <div className="h-6 w-48 bg-muted rounded mb-2" />
        <div className="h-4 w-96 bg-muted rounded" />
      </div>
    );
  }

  if (!gate) return null;

  const { liberado, motivos, avisos, breakers } = gate;

  return (
    <div
      className={cn(
        "w-full rounded-xl border p-6 shadow-sm transition-all",
        liberado
          ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-100"
          : "border-destructive/40 bg-destructive/15 text-red-100"
      )}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl font-bold",
              liberado
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-destructive/20 text-destructive border border-destructive/30"
            )}
          >
            {liberado ? <Unlock className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight uppercase">
                GATE {liberado ? "LIBERADO PARA OPERAR" : "BLOQUEADO"}
              </span>
              <span
                className={cn(
                  "px-2.5 py-0.5 text-xs font-semibold rounded-full",
                  liberado
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "bg-destructive/30 text-destructive-foreground"
                )}
              >
                Modo {breakers.modo}
              </span>
              {breakers.modo_forcado_por_mulligan && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300">
                  Mulligan Consumido
                </span>
              )}
            </div>
            <p className="text-sm opacity-90 mt-0.5">
              {liberado
                ? "Todos os circuit breakers estão verdes. Apenas execute setups com checklist 100% preenchido."
                : "Você está proibido de abrir novas posições neste momento pelos critérios abaixo:"}
            </p>
          </div>
        </div>

        {/* Status rápido de circuit breakers */}
        <div className="flex flex-wrap items-center gap-3 text-xs md:justify-end">
          <div className="bg-background/40 backdrop-blur-xs rounded-lg px-3 py-1.5 border border-border/50">
            <span className="text-muted-foreground">PnL Hoje: </span>
            <span
              className={cn(
                "font-mono font-bold",
                breakers.pnl_dia > 0
                  ? "text-emerald-400"
                  : breakers.pnl_dia < 0
                  ? "text-red-400"
                  : "text-foreground"
              )}
            >
              R$ {breakers.pnl_dia.toFixed(2)}
            </span>
          </div>

          <div className="bg-background/40 backdrop-blur-xs rounded-lg px-3 py-1.5 border border-border/50">
            <span className="text-muted-foreground">Trades: </span>
            <span className="font-mono font-bold text-foreground">
              {breakers.trades_dia}/{breakers.max_trades_dia}
            </span>
          </div>

          <div className="bg-background/40 backdrop-blur-xs rounded-lg px-3 py-1.5 border border-border/50">
            <span className="text-muted-foreground">Limite Perda: </span>
            <span className="font-mono font-bold text-destructive">
              R$ {(breakers.limite_perda_dia_efetivo ?? breakers.limite_perda_dia).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Lista Explícita de Motivos de Bloqueio */}
      {!liberado && motivos.length > 0 && (
        <div className="mt-4 pt-4 border-t border-destructive/20 space-y-1.5">
          <span className="text-xs font-bold uppercase text-red-300">
            Motivos do Bloqueio:
          </span>
          <ul className="space-y-1 text-sm">
            {motivos.map((motivo, i) => (
              <li key={i} className="flex items-center gap-2 text-destructive font-medium">
                <ShieldAlert className="h-4 w-4 shrink-0" />
                <span>{motivo}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Lista de Avisos (Âmbar) */}
      {avisos.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border/30 space-y-1">
          <span className="text-xs font-bold uppercase text-amber-400">Avisos:</span>
          {avisos.map((aviso, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-amber-300">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
              <span>{aviso}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
