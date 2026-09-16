"use client";

import * as React from "react";
import { copaApi, CopaConfig, HorarioJanela } from "@/lib/copa-api";
import { Switch } from "@/components/ui/switch";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstNum,
  InstBand,
  InstTable,
  InstRow,
  InstEmpty,
  InstDivider,
} from "@/components/inst";
import {
  Download,
  Save,
  Plus,
  Trash2,
} from "lucide-react";

const FASES_OFICIAIS_INFO = [
  { id: "etapa1", nome: "Classificatória Etapa 1", datas: "14/09/2026 – 17/09/2026", dias: 4, descarte: "Sim (1 pior dia)" },
  { id: "etapa2", nome: "Classificatória Etapa 2", datas: "21/09/2026 – 24/09/2026", dias: 4, descarte: "Sim (1 pior dia)" },
  { id: "repescagem", nome: "Repescagem", datas: "28/09/2026 – 30/09/2026", dias: 3, descarte: "Sim (1 pior dia)" },
  { id: "semifinal", nome: "Semifinal", datas: "13/10/2026 – 16/10/2026", dias: 4, descarte: "Sim (1 pior dia)" },
  { id: "final", nome: "Final Presencial (SP)", datas: "29/10/2026", dias: 1, descarte: "Não (2 baterias de 45m)" },
];

export default function CopaConfigPage() {
  const [config, setConfig] = React.useState<CopaConfig>({
    limite_perda_dia: 300,
    max_trades_dia: 3,
    max_perdas_seguidas: 2,
    cooldown_min: 60,
    bloquear_apos_meta: false,
    exposicao_maxima_contratos: 0,
    fator_perda_pos_descarte: 0.5,
    horarios_validos: [{ inicio: "09:00", fim: "12:00" }],
  });

  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const cfg = await copaApi.getConfig();
        if (cfg) {
          setConfig({
            limite_perda_dia: Number(cfg.limite_perda_dia) || 300,
            max_trades_dia: Number(cfg.max_trades_dia) || 3,
            max_perdas_seguidas: Number(cfg.max_perdas_seguidas) || 2,
            cooldown_min: Number(cfg.cooldown_min) || 60,
            bloquear_apos_meta: Boolean(cfg.bloquear_apos_meta),
            exposicao_maxima_contratos: Number(cfg.exposicao_maxima_contratos) || 0,
            fator_perda_pos_descarte: Number(cfg.fator_perda_pos_descarte) || 0.5,
            horarios_validos: Array.isArray(cfg.horarios_validos)
              ? cfg.horarios_validos
              : [{ inicio: "09:00", fim: "12:00" }],
          });
        }
      } catch (err) {
        console.error("Erro ao carregar configurações da Copa:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    try {
      await copaApi.updateConfig(config);
      setSuccessMsg("Configurações salvas com sucesso!");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      alert("Erro ao salvar configurações: " + (err.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const addHorario = () => {
    const updated = [...(config.horarios_validos || []), { inicio: "09:00", fim: "12:00" }];
    setConfig({ ...config, horarios_validos: updated });
  };

  const updateHorario = (index: number, field: keyof HorarioJanela, val: string) => {
    const updated = [...(config.horarios_validos || [])];
    updated[index] = { ...updated[index], [field]: val };
    setConfig({ ...config, horarios_validos: updated });
  };

  const removeHorario = (index: number) => {
    const updated = (config.horarios_validos || []).filter((_, i) => i !== index);
    setConfig({ ...config, horarios_validos: updated });
  };

  const handleExport = () => {
    window.location.href = copaApi.getExportUrl();
  };

  if (loading) {
    return (
      <InstPage eyebrow="COPA BTG · CONFIGURAÇÃO" title="Configurações & Backup da Copa">
        <InstEmpty>Carregando configurações...</InstEmpty>
      </InstPage>
    );
  }

  const inputStyle: React.CSSProperties = {
    background: "var(--inst-panel-2)",
    border: "1px solid var(--inst-line)",
    color: "var(--inst-text)",
    borderRadius: "3px",
    padding: "8px 12px",
    fontSize: "13px",
    outline: "none",
    width: "100%",
  };

  return (
    <InstPage
      eyebrow="COPA BTG · CONFIGURAÇÃO"
      title="Configurações & Backup da Copa"
      right={
        <button
          type="button"
          onClick={handleExport}
          className="mono tabular"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            background: "var(--inst-panel-2)",
            border: "1px solid var(--inst-line)",
            color: "var(--inst-text)",
            borderRadius: "3px",
            padding: "6px 14px",
            fontSize: "11px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          <Download style={{ width: "14px", height: "14px", color: "var(--inst-dim)" }} /> Exportar Banco (copa.db)
        </button>
      }
    >
      {/* Topo */}
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Ajuste parâmetros de circuit breakers, limites de risco e faça download do banco SQLite.
      </div>

      {successMsg && (
        <InstBand
          tom="ok"
          titulo="Sucesso"
          linhas={[successMsg]}
        />
      )}

      {/* Formulário de Configuração */}
      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* 1. Circuit Breakers e Limites de Risco */}
        <InstCard>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--inst-text)", letterSpacing: "-0.01em" }}>
                1. Circuit Breakers Globais
              </div>
              <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "2px" }}>
                Travas mecânicas diárias que impedem o clique em caso de indisciplina ou excesso de perdas.
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Limite de Perda Diária Padrão (R$)</InstLabel>
                <input
                  id="limite-perda"
                  type="number"
                  step="50"
                  value={config.limite_perda_dia}
                  onChange={(e) =>
                    setConfig({ ...config, limite_perda_dia: parseFloat(e.target.value) || 0 })
                  }
                  className="mono tabular"
                  style={{ ...inputStyle, color: "var(--inst-block)", fontWeight: 700 }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Máximo de Trades por Dia (Padrão)</InstLabel>
                <input
                  id="max-trades"
                  type="number"
                  value={config.max_trades_dia}
                  onChange={(e) =>
                    setConfig({ ...config, max_trades_dia: parseInt(e.target.value, 10) || 1 })
                  }
                  className="mono tabular"
                  style={{ ...inputStyle, fontWeight: 700 }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Máx. de Losses Seguidos (Gatilho de Cooldown)</InstLabel>
                <input
                  id="max-perdas"
                  type="number"
                  value={config.max_perdas_seguidas}
                  onChange={(e) =>
                    setConfig({ ...config, max_perdas_seguidas: parseInt(e.target.value, 10) || 1 })
                  }
                  className="mono tabular"
                  style={{ ...inputStyle, fontWeight: 700 }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Tempo de Cooldown após Losses (Minutos)</InstLabel>
                <input
                  id="cooldown-min"
                  type="number"
                  value={config.cooldown_min}
                  onChange={(e) =>
                    setConfig({ ...config, cooldown_min: parseInt(e.target.value, 10) || 1 })
                  }
                  className="mono tabular"
                  style={{ ...inputStyle, fontWeight: 700 }}
                />
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 14px",
                borderRadius: "3px",
                border: "1px solid var(--inst-line)",
                background: "var(--inst-panel-2)",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--inst-text)" }}>
                  Travar Gate Após Bater a Meta
                </span>
                <span style={{ fontSize: "11px", color: "var(--inst-dim)" }}>
                  Se ativado, impede novas operações no dia caso o PnL alcance a meta definida.
                </span>
              </div>
              <Switch
                checked={config.bloquear_apos_meta}
                onCheckedChange={(val) => setConfig({ ...config, bloquear_apos_meta: val })}
              />
            </div>
          </div>
        </InstCard>

        {/* 2. Parâmetros Específicos da Copa BTG */}
        <InstCard>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--inst-text)", letterSpacing: "-0.01em" }}>
                2. Parâmetros do Torneio Copa BTG
              </div>
              <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "2px" }}>
                Regras do regulamento para gestão de fases, descarte e exposição máxima.
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Exposição Máxima de Contratos (Parametrizada pelo BTG)</InstLabel>
                <input
                  id="exp-max"
                  type="number"
                  value={config.exposicao_maxima_contratos}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      exposicao_maxima_contratos: parseInt(e.target.value, 10) || 0,
                    })
                  }
                  className="mono tabular"
                  style={inputStyle}
                  placeholder="0 = não informado ainda"
                />
                <div style={{ fontSize: "11px", color: "var(--inst-dim)" }}>
                  O BTG comunica o limite de contratos antes de cada fase.
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <InstLabel>Fator de Corte de Risco Pós-Mulligan</InstLabel>
                <input
                  id="fator-perda"
                  type="number"
                  step="0.05"
                  min="0.1"
                  max="1.0"
                  value={config.fator_perda_pos_descarte}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      fator_perda_pos_descarte: parseFloat(e.target.value) || 0.5,
                    })
                  }
                  className="mono tabular"
                  style={{ ...inputStyle, fontWeight: 700 }}
                />
                <div style={{ fontSize: "11px", color: "var(--inst-dim)" }}>
                  Ex: 0.5 = limite de perda diária é cortado para 50% após o 1º dia negativo.
                </div>
              </div>
            </div>
          </div>
        </InstCard>

        {/* 3. Janelas Horárias Permitidas */}
        <InstCard>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--inst-text)", letterSpacing: "-0.01em" }}>
                  3. Janelas Horárias Permitidas
                </div>
                <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "2px" }}>
                  Fora dessas janelas, o gate físico bloqueia o registro de novos trades.
                </div>
              </div>
              <button
                type="button"
                onClick={addHorario}
                className="mono tabular"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  background: "var(--inst-panel-2)",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-text)",
                  borderRadius: "3px",
                  padding: "6px 12px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                <Plus style={{ width: "13px", height: "13px" }} /> Adicionar Janela
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {(config.horarios_validos || []).map((h, index) => (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    background: "var(--inst-panel-2)",
                    border: "1px solid var(--inst-line)",
                    borderRadius: "3px",
                    padding: "8px 12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
                    <InstLabel>Início:</InstLabel>
                    <input
                      type="time"
                      value={h.inicio}
                      onChange={(e) => updateHorario(index, "inicio", e.target.value)}
                      className="mono tabular"
                      style={{ ...inputStyle, width: "auto" }}
                    />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
                    <InstLabel>Fim:</InstLabel>
                    <input
                      type="time"
                      value={h.fim}
                      onChange={(e) => updateHorario(index, "fim", e.target.value)}
                      className="mono tabular"
                      style={{ ...inputStyle, width: "auto" }}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeHorario(index)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--inst-block)",
                      cursor: "pointer",
                      padding: "6px",
                      display: "flex",
                      alignItems: "center",
                    }}
                    title="Remover Janela"
                  >
                    <Trash2 style={{ width: "14px", height: "14px" }} />
                  </button>
                </div>
              ))}
            </div>

            <InstDivider />

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={saving}
                className="mono tabular"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "var(--inst-ok)",
                  border: "1px solid var(--inst-ok)",
                  color: "var(--inst-on-ok)",
                  borderRadius: "3px",
                  padding: "8px 24px",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: saving ? "not-allowed" : "pointer",
                  opacity: saving ? 0.6 : 1,
                }}
              >
                <Save style={{ width: "14px", height: "14px" }} /> {saving ? "Salvando..." : "Salvar Configurações"}
              </button>
            </div>
          </div>
        </InstCard>
      </form>

      {/* 4. Calendário Oficial das Fases da Copa (Somente Leitura) */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--inst-text)", letterSpacing: "-0.01em" }}>
              Calendário Oficial — Copa BTG Trader 2026
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              Certificado SPA/ME 03.051033/2026. Somente leitura.
            </div>
          </div>

          <InstTable
            colunas={[
              { label: "Fase" },
              { label: "Período Oficial" },
              { label: "Pregões", align: "center" },
              { label: "Regra de Descarte" },
            ]}
          >
            {FASES_OFICIAIS_INFO.map((f) => (
              <InstRow key={f.id}>
                <td style={{ padding: "10px 16px", fontSize: "12px", fontWeight: 600, color: "var(--inst-text)" }}>
                  {f.nome}
                </td>
                <td className="mono tabular" style={{ padding: "10px 16px", fontSize: "12px", color: "var(--inst-text)" }}>
                  {f.datas}
                </td>
                <td className="mono tabular" style={{ padding: "10px 16px", fontSize: "12px", fontWeight: 700, textAlign: "center", color: "var(--inst-text)" }}>
                  <InstNum value={f.dias} size="sm" />
                </td>
                <td style={{ padding: "10px 16px", fontSize: "12px", color: "var(--inst-dim)" }}>
                  {f.descarte}
                </td>
              </InstRow>
            ))}
          </InstTable>
        </div>
      </InstCard>
    </InstPage>
  );
}
