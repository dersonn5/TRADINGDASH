import * as React from "react";
import { ChecklistItem, Strategy } from "@/lib/copa-api";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { ScoreMeter } from "@/components/copa/score-meter";
import { ShieldAlert, CheckCircle, AlertCircle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChecklistFormProps {
  strategy: Strategy;
  marcado: Record<string, boolean>;
  onChange: (novoMarcado: Record<string, boolean>) => void;
  modoDefensivo?: boolean;
}

export function ChecklistForm({
  strategy,
  marcado,
  onChange,
  modoDefensivo = false,
}: ChecklistFormProps) {
  const checklist = strategy.checklist || [];

  const kills = checklist.filter((i) => i.tipo === "KILL");
  const pontos = checklist.filter((i) => i.tipo === "PONTO");

  // Calcular score ao vivo no cliente
  const score = pontos.reduce((acc, item) => {
    return acc + (marcado[item.id] ? item.peso : 0);
  }, 0);

  const gradeFor = (s: number) => {
    if (s >= 80) return "A+";
    if (s >= 65) return "A";
    if (s >= 50) return "B";
    if (s >= 35) return "C";
    return "D";
  };

  const grade = gradeFor(score);
  const threshold = modoDefensivo ? strategy.score_minimo + 15 : strategy.score_minimo;
  const killsFaltando = kills.filter((k) => !marcado[k.id]);
  const pontosFaltando = Math.max(0, threshold - score);

  const toggleItem = (id: string) => {
    const updated = { ...marcado, [id]: !marcado[id] };
    onChange(updated);
  };

  return (
    <div className="space-y-6">
      {/* Medidor de Score no Topo */}
      <ScoreMeter
        score={score}
        grade={grade}
        scoreMinimo={strategy.score_minimo}
        modoDefensivo={modoDefensivo}
      />

      {/* Painel de Status do que Falta */}
      <div
        className={cn(
          "rounded-xl border p-4 transition-all text-sm",
          killsFaltando.length === 0 && score >= threshold
            ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-200"
            : "border-destructive/30 bg-destructive/10 text-red-200"
        )}
      >
        <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-xs">
          {killsFaltando.length === 0 && score >= threshold ? (
            <>
              <CheckCircle className="h-4 w-4 text-emerald-400" />
              <span>Checklist Aprovado — Confluências Validadas</span>
            </>
          ) : (
            <>
              <ShieldAlert className="h-4 w-4 text-destructive" />
              <span>Pendências para Liberação do Gate:</span>
            </>
          )}
        </div>

        {(killsFaltando.length > 0 || pontosFaltando > 0) && (
          <ul className="mt-2 space-y-1 text-xs opacity-90 pl-5 list-disc">
            {killsFaltando.map((k) => (
              <li key={k.id} className="text-destructive font-medium">
                Falta marcar KILL: <span className="underline">{k.label}</span>
              </li>
            ))}
            {pontosFaltando > 0 && (
              <li className="text-amber-300 font-medium">
                Faltam <span className="font-bold">{pontosFaltando} pontos</span> de confluência para atingir o score mínimo ({threshold} pts).
              </li>
            )}
          </ul>
        )}
      </div>

      {/* Bloco 1: Itens KILL (Obrigatórios) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="destructive" className="font-bold text-xs uppercase tracking-wider">
              KILL — Obrigatórios
            </Badge>
            <span className="text-xs text-muted-foreground">
              Sem todos os 6 marcados, a ordem é recusada.
            </span>
          </div>
          <span className="text-xs font-mono font-bold">
            {kills.length - killsFaltando.length}/{kills.length}
          </span>
        </div>

        <div className="grid gap-2">
          {kills.map((item) => {
            const isChecked = !!marcado[item.id];
            return (
              <div
                key={item.id}
                onClick={() => toggleItem(item.id)}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer select-none",
                  isChecked
                    ? "bg-card border-primary/40 text-foreground"
                    : "bg-muted/20 border-border hover:border-border/80 text-muted-foreground"
                )}
              >
                <Checkbox
                  checked={isChecked}
                  onCheckedChange={() => toggleItem(item.id)}
                  className="mt-0.5"
                />
                <div className="space-y-0.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span className={cn("text-sm font-semibold", isChecked && "text-foreground font-bold")}>
                      {item.label}
                    </span>
                    <Badge variant="destructive" className="text-[10px] uppercase font-bold py-0 h-4">
                      KILL
                    </Badge>
                  </div>
                  {item.ajuda && (
                    <p className="text-xs text-muted-foreground/80">{item.ajuda}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bloco 2: Itens PONTO (Confluências) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-bold text-xs uppercase tracking-wider text-primary border-primary">
              PONTOS — Confluências
            </Badge>
            <span className="text-xs text-muted-foreground">
              Somam peso para atingir a nota mínima ({threshold} pts).
            </span>
          </div>
          <span className="text-xs font-mono font-bold text-primary">
            {score}/100 pts
          </span>
        </div>

        <div className="grid gap-2">
          {pontos.map((item) => {
            const isChecked = !!marcado[item.id];
            return (
              <div
                key={item.id}
                onClick={() => toggleItem(item.id)}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer select-none",
                  isChecked
                    ? "bg-card border-emerald-500/40 text-foreground"
                    : "bg-muted/20 border-border hover:border-border/80 text-muted-foreground"
                )}
              >
                <Checkbox
                  checked={isChecked}
                  onCheckedChange={() => toggleItem(item.id)}
                  className="mt-0.5"
                />
                <div className="space-y-0.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span className={cn("text-sm", isChecked && "text-foreground font-semibold")}>
                      {item.label}
                    </span>
                    <Badge
                      className={cn(
                        "text-xs font-mono font-bold py-0 h-5",
                        isChecked
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      +{item.peso} pts
                    </Badge>
                  </div>
                  {item.ajuda && (
                    <p className="text-xs text-muted-foreground/80">{item.ajuda}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
