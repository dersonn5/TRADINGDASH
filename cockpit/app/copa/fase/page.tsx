"use client";

import * as React from "react";
import { copaApi, PlacarFaseResult } from "@/lib/copa-api";
import { PlacarFaseView } from "@/components/copa/placar-fase";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function CopaFasePage() {
  const hoje = new Date().toISOString().split("T")[0];
  const [dataConsulta, setDataConsulta] = React.useState(hoje);
  const [placar, setPlacar] = React.useState<PlacarFaseResult | null>(null);
  const [loading, setLoading] = React.useState(true);

  const carregarFase = React.useCallback(async (dt: string) => {
    setLoading(true);
    try {
      const res = await copaApi.getFase(dt);
      setPlacar(res);
    } catch (err) {
      console.error("Erro ao carregar dados da fase:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    carregarFase(dataConsulta);
  }, [dataConsulta, carregarFase]);

  return (
    <div className="container py-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Placar de Fases da Copa BTG</h1>
          <p className="text-sm text-muted-foreground">
            Acompanhe o saldo com e sem o descarte oficial do pior dia e o status do seu Mulligan.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Label htmlFor="data-fase" className="text-xs text-muted-foreground whitespace-nowrap">
            Consultar Data:
          </Label>
          <Input
            id="data-fase"
            type="date"
            value={dataConsulta}
            onChange={(e) => setDataConsulta(e.target.value)}
            className="w-38 font-mono bg-card text-xs"
          />
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-muted-foreground animate-pulse">
          Carregando placar da fase...
        </div>
      ) : (
        placar && <PlacarFaseView placar={placar} />
      )}
    </div>
  );
}
