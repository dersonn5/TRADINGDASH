import * as React from "react";
import { StatsPorItem } from "@/lib/copa-api";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, ArrowDownRight, AlertTriangle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsPorItemProps {
  items: StatsPorItem[];
}

export function StatsPorItemTable({ items }: StatsPorItemProps) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        Nenhum dado por item disponível ainda. Feche os primeiros trades para calcular os deltas.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold tracking-tight">O que realmente está pagando?</h3>
          <p className="text-xs text-muted-foreground">
            Comparação empírica de winrate e expectância quando o item foi marcado vs. não marcado.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead>Item de Confluência</TableHead>
              <TableHead className="text-center">Tipo</TableHead>
              <TableHead className="text-center">Com o Item (Marcado)</TableHead>
              <TableHead className="text-center">Sem o Item (Não marcado)</TableHead>
              <TableHead className="text-right">Impacto no Winrate (Δ)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => {
              const deltaPositivo = item.delta_winrate > 0;
              const deltaNeutro = item.delta_winrate === 0;

              return (
                <TableRow key={`${item.strategy_id}-${item.item_id}`}>
                  <TableCell className="max-w-md">
                    <div className="flex items-start gap-2">
                      <span className="font-semibold text-xs text-foreground block">
                        {item.label}
                      </span>
                      {item.amostra_baixa && (
                        <Badge
                          variant="outline"
                          className="text-[9px] py-0 border-amber-500/40 text-amber-400 gap-0.5 shrink-0"
                        >
                          <AlertTriangle className="h-2.5 w-2.5" /> N baixo
                        </Badge>
                      )}
                    </div>
                  </TableCell>

                  <TableCell className="text-center">
                    <Badge
                      variant={item.tipo === "KILL" ? "destructive" : "secondary"}
                      className="text-[10px] py-0 font-bold"
                    >
                      {item.tipo}
                    </Badge>
                  </TableCell>

                  <TableCell className="text-center font-mono text-xs">
                    <div className="font-bold text-foreground">
                      {item.winrate_marcado.toFixed(1)}% ({item.n_marcado} trades)
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Exp: R$ {item.exp_marcado.toFixed(2)}
                    </div>
                  </TableCell>

                  <TableCell className="text-center font-mono text-xs">
                    <div className="font-bold text-muted-foreground">
                      {item.winrate_nao.toFixed(1)}% ({item.n_nao} trades)
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Exp: R$ {item.exp_nao.toFixed(2)}
                    </div>
                  </TableCell>

                  <TableCell className="text-right font-mono font-bold text-sm">
                    <div
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded",
                        deltaPositivo
                          ? "text-emerald-400 bg-emerald-950/30"
                          : deltaNeutro
                          ? "text-muted-foreground"
                          : "text-red-400 bg-destructive/10"
                      )}
                    >
                      {deltaPositivo ? (
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      ) : deltaNeutro ? null : (
                        <ArrowDownRight className="h-3.5 w-3.5" />
                      )}
                      <span>
                        {deltaPositivo ? "+" : ""}
                        {item.delta_winrate.toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
