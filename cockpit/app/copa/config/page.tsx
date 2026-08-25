"use client";

import * as React from "react";
import { copaApi, CopaConfig, HorarioJanela } from "@/lib/copa-api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table";
import {
  Download,
  Save,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  Calendar,
  Shield,
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
    return <div className="container py-12 text-center text-muted-foreground">Carregando configurações...</div>;
  }

  return (
    <div className="container py-6 space-y-8 max-w-4xl mx-auto pb-16">
      {/* Topo */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Configurações & Backup da Copa</h1>
          <p className="text-sm text-muted-foreground">
            Ajuste parâmetros de circuit breakers, limites de risco e faça download do banco SQLite.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={handleExport}
          className="gap-2 font-semibold border-primary/40 text-foreground"
        >
          <Download className="h-4 w-4 text-primary" /> Exportar Banco (copa.db)
        </Button>
      </div>

      {successMsg && (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Sucesso</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}

      {/* Formulário de Configuração */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* 1. Circuit Breakers e Limites de Risco */}
        <Card>
          <CardHeader>
            <CardTitle>1. Circuit Breakers Globais</CardTitle>
            <CardDescription>
              Travas mecânicas diárias que impedem o clique em caso de indisciplina ou excesso de perdas.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="limite-perda">Limite de Perda Diária Padrão (R$)</Label>
                <Input
                  id="limite-perda"
                  type="number"
                  step="50"
                  value={config.limite_perda_dia}
                  onChange={(e) =>
                    setConfig({ ...config, limite_perda_dia: parseFloat(e.target.value) || 0 })
                  }
                  className="font-mono font-bold text-destructive"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="max-trades">Máximo de Trades por Dia (Padrão)</Label>
                <Input
                  id="max-trades"
                  type="number"
                  value={config.max_trades_dia}
                  onChange={(e) =>
                    setConfig({ ...config, max_trades_dia: parseInt(e.target.value, 10) || 1 })
                  }
                  className="font-mono font-bold"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="max-perdas">Máx. de Losses Seguidos (Gatilho de Cooldown)</Label>
                <Input
                  id="max-perdas"
                  type="number"
                  value={config.max_perdas_seguidas}
                  onChange={(e) =>
                    setConfig({ ...config, max_perdas_seguidas: parseInt(e.target.value, 10) || 1 })
                  }
                  className="font-mono font-bold"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="cooldown-min">Tempo de Cooldown após Losses (Minutos)</Label>
                <Input
                  id="cooldown-min"
                  type="number"
                  value={config.cooldown_min}
                  onChange={(e) =>
                    setConfig({ ...config, cooldown_min: parseInt(e.target.value, 10) || 1 })
                  }
                  className="font-mono font-bold"
                />
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/20">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold block">Travar Gate Após Bater a Meta</span>
                <span className="text-xs text-muted-foreground">
                  Se ativado, impede novas operações no dia caso o PnL alcance a meta definida.
                </span>
              </div>
              <Switch
                checked={config.bloquear_apos_meta}
                onCheckedChange={(val) => setConfig({ ...config, bloquear_apos_meta: val })}
              />
            </div>
          </CardContent>
        </Card>

        {/* 2. Parâmetros Específicos da Copa BTG */}
        <Card>
          <CardHeader>
            <CardTitle>2. Parâmetros do Torneio Copa BTG</CardTitle>
            <CardDescription>
              Regras do regulamento para gestão de fases, descarte e exposição máxima.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="exp-max">
                Exposição Máxima de Contratos (Parametrizada pelo BTG)
              </Label>
              <Input
                id="exp-max"
                type="number"
                value={config.exposicao_maxima_contratos}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    exposicao_maxima_contratos: parseInt(e.target.value, 10) || 0,
                  })
                }
                className="font-mono"
                placeholder="0 = não informado ainda"
              />
              <p className="text-[11px] text-muted-foreground">
                O BTG comunica o limite de contratos antes de cada fase.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="fator-perda">Fator de Corte de Risco Pós-Mulligan</Label>
              <Input
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
                className="font-mono font-bold"
              />
              <p className="text-[11px] text-muted-foreground">
                Ex: 0.5 = limite de perda diária é cortado para 50% após o 1º dia negativo.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 3. Janelas Horárias Permitidas */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>3. Janelas Horárias Permitidas</CardTitle>
              <CardDescription>
                Fora dessas janelas, o gate físico bloqueia o registro de novos trades.
              </CardDescription>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={addHorario} className="gap-1">
              <Plus className="h-4 w-4" /> Adicionar Janela
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {(config.horarios_validos || []).map((h, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <Label className="text-xs">Início:</Label>
                  <Input
                    type="time"
                    value={h.inicio}
                    onChange={(e) => updateHorario(index, "inicio", e.target.value)}
                    className="font-mono"
                  />
                </div>
                <div className="flex items-center gap-2 flex-1">
                  <Label className="text-xs">Fim:</Label>
                  <Input
                    type="time"
                    value={h.fim}
                    onChange={(e) => updateHorario(index, "fim", e.target.value)}
                    className="font-mono"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeHorario(index)}
                  className="text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
          <CardFooter className="border-t pt-4 flex justify-end">
            <Button
              type="submit"
              disabled={saving}
              className="gap-2 font-bold px-8 bg-primary text-primary-foreground"
            >
              <Save className="h-4 w-4" /> {saving ? "Salvando..." : "Salvar Configurações"}
            </Button>
          </CardFooter>
        </Card>
      </form>

      {/* 4. Calendário Oficial das Fases da Copa (Somente Leitura) */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-amber-400" />
            <CardTitle>Calendário Oficial — Copa BTG Trader 2026</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Certificado SPA/ME 03.051033/2026. Somente leitura.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Fase</TableHead>
                  <TableHead>Período Oficial</TableHead>
                  <TableHead className="text-center">Pregões</TableHead>
                  <TableHead>Regra de Descarte</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {FASES_OFICIAIS_INFO.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell className="font-semibold text-xs text-foreground">
                      {f.nome}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{f.datas}</TableCell>
                    <TableCell className="text-center font-mono font-bold text-xs">
                      {f.dias}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{f.descarte}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
