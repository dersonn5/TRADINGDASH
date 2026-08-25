"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  copaApi,
  SessionDay,
  SessionDayPayload,
  Bias,
  Contexto,
  Impacto,
  Modo,
  NivelPreco,
  AgendaEvento,
  CopaError,
} from "@/lib/copa-api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Plus, Trash2, ShieldAlert, CheckCircle2, Save, ArrowRight } from "lucide-react";

export function PreSessaoForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hoje = new Date().toISOString().split("T")[0];
  const initialDate = searchParams.get("data") || hoje;

  const [dataStr, setDataStr] = React.useState(initialDate);
  const [biasD1, setBiasD1] = React.useState<Bias>("INDEFINIDO");
  const [biasH1, setBiasH1] = React.useState<Bias>("INDEFINIDO");
  const [contexto, setContexto] = React.useState<Contexto>("TENDENCIA");
  const [niveis, setNiveis] = React.useState<NivelPreco[]>([
    { label: "PDH", preco: 0 },
    { label: "PDL", preco: 0 },
  ]);
  const [agenda, setAgenda] = React.useState<AgendaEvento[]>([]);
  const [sono, setSono] = React.useState<number>(3);
  const [tilt, setTilt] = React.useState<number>(0);
  const [pressao, setPressao] = React.useState<number>(0);
  const [metaDia, setMetaDia] = React.useState<number>(0);
  const [limitePerdaDia, setLimitePerdaDia] = React.useState<number>(300);
  const [maxTradesDia, setMaxTradesDia] = React.useState<number>(3);
  const [modo, setModo] = React.useState<Modo>("NORMAL");
  const [notas, setNotas] = React.useState<string>("");

  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  // Carregar dados da sessão se já existir
  const loadSessionData = React.useCallback(async (targetDate: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const sess = await copaApi.getSession(targetDate);
      if (sess) {
        setBiasD1(sess.bias_d1 || "INDEFINIDO");
        setBiasH1(sess.bias_h1 || "INDEFINIDO");
        setContexto(sess.contexto || "TENDENCIA");
        setNiveis(sess.niveis && sess.niveis.length > 0 ? sess.niveis : [{ label: "PDH", preco: 0 }]);
        setAgenda(sess.agenda || []);
        setSono(sess.sono ?? 3);
        setTilt(sess.tilt ?? 0);
        setPressao(sess.pressao ?? 0);
        setMetaDia(sess.meta_dia ?? 0);
        setLimitePerdaDia(sess.limite_perda_dia ?? 300);
        setMaxTradesDia(sess.max_trades_dia ?? 3);
        setModo(sess.modo || "NORMAL");
        setNotas(sess.notas || "");
      } else {
        // Carregar defaults da config
        const cfg = await copaApi.getConfig();
        if (cfg) {
          if (cfg.limite_perda_dia !== undefined) setLimitePerdaDia(Number(cfg.limite_perda_dia));
          if (cfg.max_trades_dia !== undefined) setMaxTradesDia(Number(cfg.max_trades_dia));
          if (cfg.meta_dia_padrao !== undefined) setMetaDia(Number(cfg.meta_dia_padrao));
        }
      }
    } catch (err: any) {
      console.error("Erro ao carregar sessão:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadSessionData(dataStr);
  }, [dataStr, loadSessionData]);

  // Modo sugerido automático por red flags
  const temNoticiaAlta = agenda.some((ev) => ev.impacto === "ALTO");
  const modoSugerido: Modo =
    tilt >= 3 || sono <= 2 || pressao >= 4 || temNoticiaAlta ? "DEFENSIVO" : "NORMAL";

  // Níveis dinâmicos
  const addNivel = () => setNiveis([...niveis, { label: "", preco: 0 }]);
  const updateNivel = (index: number, field: keyof NivelPreco, val: any) => {
    const updated = [...niveis];
    updated[index] = { ...updated[index], [field]: val };
    setNiveis(updated);
  };
  const removeNivel = (index: number) => setNiveis(niveis.filter((_, i) => i !== index));

  // Agenda dinâmica
  const addAgenda = () => setAgenda([...agenda, { evento: "", horario: "09:00", impacto: "MEDIO" }]);
  const updateAgenda = (index: number, field: keyof AgendaEvento, val: any) => {
    const updated = [...agenda];
    updated[index] = { ...updated[index], [field]: val };
    setAgenda(updated);
  };
  const removeAgenda = (index: number) => setAgenda(agenda.filter((_, i) => i !== index));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const payload: SessionDayPayload = {
      data: dataStr,
      bias_d1: biasD1,
      bias_h1: biasH1,
      contexto,
      niveis: niveis.filter((n) => n.label.trim().length > 0),
      agenda: agenda.filter((a) => a.evento.trim().length > 0),
      sono,
      tilt,
      pressao,
      meta_dia: Number(metaDia) || 0,
      limite_perda_dia: Number(limitePerdaDia) || 300,
      max_trades_dia: Number(maxTradesDia) || 3,
      modo,
      notas,
    };

    try {
      await copaApi.saveSession(dataStr, payload);
      setSuccessMsg("Pré-sessão salva com sucesso! O gate foi atualizado.");
      setTimeout(() => {
        router.push("/copa");
      }, 1200);
    } catch (err: any) {
      if (err instanceof CopaError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg(err.message || "Erro desconhecido ao salvar sessão");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Cabeçalho */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pré-Sessão Diária</h1>
          <p className="text-sm text-muted-foreground">
            Ambiente qualitativo, marcação de liquidez e checagem de estado do operador.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="session-date" className="text-sm text-muted-foreground whitespace-nowrap">
            Data do Pregão:
          </Label>
          <Input
            id="session-date"
            type="date"
            value={dataStr}
            onChange={(e) => setDataStr(e.target.value)}
            className="w-38 font-mono bg-card"
          />
        </div>
      </div>

      {errorMsg && (
        <Alert variant="destructive">
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle>Erro ao salvar</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {successMsg && (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Concluído</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}

      {/* 1. Leitura de Mercado e Macro */}
      <Card>
        <CardHeader>
          <CardTitle>1. Contexto e Direção Macro</CardTitle>
          <CardDescription>Defina o viés de tempo gráfico maior antes de procurar gatilhos.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Bias D1 (Diário)</Label>
            <Select value={biasD1} onChange={(e: any) => setBiasD1(e.target.value as Bias)}>
              <option value="COMPRA">COMPRA (Alta)</option>
              <option value="VENDA">VENDA (Baixa)</option>
              <option value="INDEFINIDO">INDEFINIDO</option>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Bias H1 (60 min — Lição 2)</Label>
            <Select value={biasH1} onChange={(e: any) => setBiasH1(e.target.value as Bias)}>
              <option value="COMPRA">COMPRA (Alta)</option>
              <option value="VENDA">VENDA (Baixa)</option>
              <option value="INDEFINIDO">INDEFINIDO</option>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Contexto de Mercado</Label>
            <Select value={contexto} onChange={(e: any) => setContexto(e.target.value as Contexto)}>
              <option value="TENDENCIA">TENDÊNCIA</option>
              <option value="RANGE">RANGE / CONSOLIDAÇÃO</option>
              <option value="INDEFINIDO">INDEFINIDO</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 2. Mapeamento de Liquidez (Níveis) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>2. Mapeamento de Liquidez e Níveis-Chave</CardTitle>
            <CardDescription>PDH, PDL, EQH, EQL, Gaps e máximas/mínimas relevantes.</CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={addNivel} className="gap-1">
            <Plus className="h-4 w-4" /> Adicionar Nível
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {niveis.map((lvl, index) => (
            <div key={index} className="flex items-center gap-3">
              <Input
                placeholder="Ex: PDH, EQH, Abertura"
                value={lvl.label}
                onChange={(e) => updateNivel(index, "label", e.target.value)}
                className="w-1/2"
              />
              <Input
                type="number"
                step="any"
                placeholder="Preço (ex: 135400)"
                value={lvl.preco || ""}
                onChange={(e) => updateNivel(index, "preco", parseFloat(e.target.value) || 0)}
                className="w-1/2 font-mono"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeNivel(index)}
                className="text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          {niveis.length === 0 && (
            <p className="text-sm text-muted-foreground italic">Nenhum nível marcado ainda.</p>
          )}
        </CardContent>
      </Card>

      {/* 3. Notícias e Agenda Econômica */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>3. Agenda Econômica e Eventos de Risco</CardTitle>
            <CardDescription>Eventos de volatilidade na janela de negociação.</CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={addAgenda} className="gap-1">
            <Plus className="h-4 w-4" /> Adicionar Evento
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {agenda.map((ev, index) => (
            <div key={index} className="grid grid-cols-12 gap-2 items-center">
              <div className="col-span-5">
                <Input
                  placeholder="Evento (ex: Payroll, Copom, NY Open)"
                  value={ev.evento}
                  onChange={(e) => updateAgenda(index, "evento", e.target.value)}
                />
              </div>
              <div className="col-span-3">
                <Input
                  type="time"
                  value={ev.horario}
                  onChange={(e) => updateAgenda(index, "horario", e.target.value)}
                  className="font-mono"
                />
              </div>
              <div className="col-span-3">
                <Select
                  value={ev.impacto}
                  onChange={(e: any) => updateAgenda(index, "impacto", e.target.value as Impacto)}
                >
                  <option value="ALTO">ALTO IMPACTO</option>
                  <option value="MEDIO">MÉDIO IMPACTO</option>
                  <option value="BAIXO">BAIXO IMPACTO</option>
                </Select>
              </div>
              <div className="col-span-1 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeAgenda(index)}
                  className="text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          {agenda.length === 0 && (
            <p className="text-sm text-muted-foreground italic">Sem eventos cadastrados para hoje.</p>
          )}
        </CardContent>
      </Card>

      {/* 4. Estado Psicológico e Fisiológico do Operador */}
      <Card>
        <CardHeader>
          <CardTitle>4. Estado do Operador</CardTitle>
          <CardDescription>Escala de 0 a 5. Seja honesto para autoproteção do capital.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Sono */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>Qualidade do Sono</Label>
              <span className="text-sm font-bold font-mono">{sono}/5</span>
            </div>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((val) => (
                <Button
                  key={val}
                  type="button"
                  variant={sono === val ? "default" : "outline"}
                  size="sm"
                  className="flex-1 font-bold"
                  onClick={() => setSono(val)}
                >
                  {val}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">1=Péssimo, 5=Excelente descanso</p>
          </div>

          {/* Tilt */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>Nível de Tilt / Frustração</Label>
              <span className="text-sm font-bold font-mono text-destructive">{tilt}/5</span>
            </div>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4, 5].map((val) => (
                <Button
                  key={val}
                  type="button"
                  variant={tilt === val ? "destructive" : "outline"}
                  size="sm"
                  className="flex-1 font-bold"
                  onClick={() => setTilt(val)}
                >
                  {val}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">0=Calmo/Neutro, 5=Emocional/Vingativo</p>
          </div>

          {/* Pressão */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>Pressão por Resultado</Label>
              <span className="text-sm font-bold font-mono">{pressao}/5</span>
            </div>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4, 5].map((val) => (
                <Button
                  key={val}
                  type="button"
                  variant={pressao === val ? "default" : "outline"}
                  size="sm"
                  className="flex-1 font-bold"
                  onClick={() => setPressao(val)}
                >
                  {val}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">0=Sem apego, 5=Necessidade urgente de ganho</p>
          </div>
        </CardContent>
      </Card>

      {/* 5. Parâmetros de Gestão do Dia e Modo */}
      <Card>
        <CardHeader>
          <CardTitle>5. Parâmetros e Modo de Operação</CardTitle>
          <CardDescription>Limites estritos de risco e postura para o pregão.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="limite-perda">Limite de Perda Diária (R$)</Label>
              <Input
                id="limite-perda"
                type="number"
                step="50"
                value={limitePerdaDia}
                onChange={(e) => setLimitePerdaDia(parseFloat(e.target.value) || 0)}
                className="font-mono text-destructive font-bold"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-trades">Máximo de Trades</Label>
              <Input
                id="max-trades"
                type="number"
                value={maxTradesDia}
                onChange={(e) => setMaxTradesDia(parseInt(e.target.value, 10) || 1)}
                className="font-mono"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="meta-dia">Meta do Dia (R$ - opcional)</Label>
              <Input
                id="meta-dia"
                type="number"
                step="50"
                value={metaDia}
                onChange={(e) => setMetaDia(parseFloat(e.target.value) || 0)}
                className="font-mono text-emerald-500 font-bold"
              />
            </div>
          </div>

          {/* Banner de Modo Sugerido */}
          <div className="rounded-lg border p-4 bg-muted/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">Diagnóstico do Sistema:</span>
                {modoSugerido === "DEFENSIVO" ? (
                  <Badge variant="destructive" className="gap-1">
                    <ShieldAlert className="h-3 w-3" /> Modo DEFENSIVO Recomendado
                  </Badge>
                ) : (
                  <Badge className="bg-emerald-600 text-white gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Modo NORMAL Recomendado
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {modoSugerido === "DEFENSIVO"
                  ? "Detectadas red flags (sono baixo, tilt, alta pressão ou notícia ALTO impacto). O modo defensivo limita a 1 trade no dia e eleva o score mínimo exigido em +15 pontos."
                  : "Condições psicológicas e de agenda favoráveis para o plano de trade padrão."}
              </p>
            </div>

            <div className="flex items-center gap-2 self-end md:self-auto">
              <Label className="text-xs font-semibold">Modo Escolhido:</Label>
              <div className="flex gap-1">
                <Button
                  type="button"
                  size="sm"
                  variant={modo === "NORMAL" ? "default" : "outline"}
                  onClick={() => setModo("NORMAL")}
                >
                  NORMAL
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={modo === "DEFENSIVO" ? "destructive" : "outline"}
                  onClick={() => setModo("DEFENSIVO")}
                >
                  DEFENSIVO
                </Button>
              </div>
            </div>
          </div>

          {/* Notas Gerais */}
          <div className="space-y-2">
            <Label htmlFor="notas-dia">Anotações / Lembretes de Mentalidade</Label>
            <Textarea
              id="notas-dia"
              placeholder="Ex: Não hesitar na confirmação do CHoCH; não tentar recuperar loss se tomar stop na abertura."
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              rows={3}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-between items-center">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/copa")}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={saving || loading}
            className="gap-2 bg-primary text-primary-foreground font-semibold px-6"
          >
            <Save className="h-4 w-4" />
            {saving ? "Salvando..." : "Salvar Pré-Sessão e Ativar Gate"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
