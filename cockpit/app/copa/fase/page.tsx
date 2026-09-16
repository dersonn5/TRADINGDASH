"use client";

import * as React from "react";
import { copaApi, PlacarFaseResult } from "@/lib/copa-api";
import { PlacarFaseView } from "@/components/copa/placar-fase";
import { InstPage, InstLabel, InstEmpty } from "@/components/inst";

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
    <InstPage
      eyebrow="COPA BTG"
      title="Placar de Fases da Copa BTG"
      right={
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <InstLabel>Consultar Data:</InstLabel>
          <input
            id="data-fase"
            type="date"
            value={dataConsulta}
            onChange={(e) => setDataConsulta(e.target.value)}
            className="mono tabular"
            style={{
              background: "var(--inst-bg-deep)",
              border: "1px solid var(--inst-line-2)",
              borderRadius: "3px",
              color: "var(--inst-text)",
              fontSize: "12px",
              padding: "6px 10px",
              outline: "none",
            }}
          />
        </div>
      }
    >
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Acompanhe o saldo com e sem o descarte oficial do pior dia e o status do seu Mulligan.
      </div>

      {loading ? (
        <InstEmpty>Carregando placar da fase...</InstEmpty>
      ) : placar ? (
        <PlacarFaseView placar={placar} />
      ) : (
        <InstEmpty>Nenhum dado de fase retornado para a data selecionada.</InstEmpty>
      )}
    </InstPage>
  );
}
