import * as React from "react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ScoreMeterProps {
  score: number;
  grade: string;
  scoreMinimo: number;
  modoDefensivo?: boolean;
}

export function ScoreMeter({ score, grade, scoreMinimo, modoDefensivo }: ScoreMeterProps) {
  const threshold = modoDefensivo ? scoreMinimo + 15 : scoreMinimo;
  const isAprovado = score >= threshold;

  const gradeColor = (g: string) => {
    switch (g) {
      case "A+":
        return "text-emerald-400 bg-emerald-950/40 border-emerald-500/50";
      case "A":
        return "text-emerald-300 bg-emerald-950/20 border-emerald-500/30";
      case "B":
        return "text-sky-400 bg-sky-950/20 border-sky-500/30";
      case "C":
        return "text-amber-400 bg-amber-950/20 border-amber-500/30";
      default:
        return "text-destructive bg-destructive/20 border-destructive/30";
    }
  };

  return (
    <div className="rounded-xl border bg-card/60 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Score de Confluência
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-3xl font-mono font-extrabold text-foreground">
              {score.toFixed(0)}
            </span>
            <span className="text-xs text-muted-foreground">/ 100 pts</span>
            <span className="text-xs font-medium text-muted-foreground ml-2">
              (mínimo exigido: <span className="font-bold text-foreground">{threshold} pts</span>)
            </span>
          </div>
        </div>

        {/* Grade Badge */}
        <div
          className={cn(
            "flex flex-col items-center justify-center rounded-xl border px-4 py-2 font-mono font-black text-2xl shadow-xs",
            gradeColor(grade)
          )}
        >
          <span>{grade}</span>
          <span className="text-[10px] tracking-normal font-sans font-normal opacity-80">
            {isAprovado ? "Aprovado" : "Insuficiente"}
          </span>
        </div>
      </div>

      {/* Barra de Progresso com marcador do mínimo */}
      <div className="relative pt-1">
        <Progress value={score} max={100} className="h-3 bg-muted/60" />
        {/* Marcador do Threshold */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
          style={{ left: `${threshold}%` }}
          title={`Score mínimo: ${threshold}`}
        />
        <div
          className="absolute -top-3.5 -translate-x-1/2 text-[9px] font-mono font-bold text-red-400"
          style={{ left: `${threshold}%` }}
        >
          ▲ {threshold}
        </div>
      </div>

      {modoDefensivo && (
        <p className="text-xs text-amber-400 font-medium">
          ⚠️ Modo Defensivo ativo: score mínimo elevado em +15 pontos ({threshold} pts).
        </p>
      )}
    </div>
  );
}
