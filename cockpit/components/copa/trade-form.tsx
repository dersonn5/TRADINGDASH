"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  copaApi,
  Strategy,
  GateResult,
  StrategyRanking,
  Mercado,
  Direcao,
  CreateTradePayload,
  CopaError,
} from "@/lib/copa-api";
import { ChecklistForm } from "@/components/copa/checklist-form";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  Lock,
  Unlock,
  ShieldAlert,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Calculator,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const VALOR_PONTO: Record<Mercado, number> = {
  WIN: 0.2,
  WDO: 10.0,
};

export function TradeForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hoje = new Date().toISOString().split("T")[0];

  const paramStrategy = searchParams.get("strategy");

  const [strategies, setStrategies] = React.useState<Strategy[]>([]);
  const [selectedStratId, setSelectedStratId] = React.useState<string>(paramStrategy || "playbook_anderson");
  const [gate, setGate] = React.useState<GateResult | null>(null);
  const [ranking, setRanking] = React.useState<StrategyRanking[]>([]);

  const [mercado, setMercado] = React.useState<Mercado>("WIN");
  const [direcao, setDirecao] = React.useState<Direcao>("COMPRA");
  const [checklist, setChecklist] = React.useState<Record<string, boolean>>({});
  const [entrada, setEntrada] = React.useState<string>("");
  const [stop, setStop] = React.useState<string>("");
  const [alvo, setAlvo] = React.useState<string>("");
  const [contratos, setContratos] = React.useState<number>(1);
  const [notas, setNotas] = React.useState<string>("");

  const [submitting, setSubmitting] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  // Carregar dados iniciais
  React.useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [strats, gateRes, rankRes] = await Promise.all([
          copaApi.getStrategies(),
          copaApi.getGate(hoje),
          copaApi.getRanking(hoje),
        ]);
        setStrategies(strats);
        setGate(gateRes);
        setRanking(rankRes);
        if (paramStrategy && strats.some((s) => s.id === paramStrategy)) {
          setSelectedStratId(paramStrategy);
        } else if (strats.length > 0) {
          setSelectedStratId(strats[0].id);
        }
      } catch (err) {
        console.error("Erro ao carregar dados do formulário de trade:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [hoje, paramStrategy]);

  const activeStrategy = strategies.find((s) => s.id === selectedStratId) || strategies[0];
  const activeRanking = ranking.find((r) => r.strategy_id === selectedStratId);
  const modoDefensivo = gate?.breakers.modo === "DEFENSIVO";

  // Cálculos de Preço e Risco ao vivo
  const numEntrada = parseFloat(entrada) || 0;
  const numStop = parseFloat(stop) || 0;
  const numAlvo = parseFloat(alvo) || 0;
  const numContratos = parseInt(contratos as any, 10) || 1;

  let rr = 0;
  let riscoReais = 0;
  let retornoReais = 0;
  let direcaoValida = false;
  let motivoInvalidoPreco = "";

  const diffRisco = Math.abs(numEntrada - numStop);
  const diffRetorno = Math.abs(numAlvo - numEntrada);

  if (numEntrada > 0 && numStop > 0 && numAlvo > 0 && diffRisco > 0) {
    rr = Math.round((diffRetorno / diffRisco) * 100) / 100;
    const fator = VALOR_PONTO[mercado] || 0.2;
    riscoReais = Math.round(diffRisco * numContratos * fator * 100) / 100;
    retornoReais = Math.round(diffRetorno * numContratos * fator * 100) / 100;

    if (direcao === "COMPRA") {
      if (numStop < numEntrada && numEntrada < numAlvo) {
        direcaoValida = true;
      } else {
        motivoInvalidoPreco = "Compra exige: Stop < Entrada < Alvo";
      }
    } else {
      if (numAlvo < numEntrada && numEntrada < numStop) {
        direcaoValida = true;
      } else {
        motivoInvalidoPreco = "Venda exige: Alvo < Entrada < Stop";
      }
    }
  }

  // Auditar condições do Gate
  const kills = activeStrategy?.checklist.filter((i) => i.tipo === "KILL") || [];
  const pontos = activeStrategy?.checklist.filter((i) => i.tipo === "PONTO") || [];

  const killsFaltando = kills.filter((k) => !checklist[k.id]);
  const scoreAtual = pontos.reduce((acc, item) => acc + (checklist[item.id] ? item.peso : 0), 0);
  const thresholdScore = modoDefensivo
    ? (activeStrategy?.score_minimo || 65) + 15
    : activeStrategy?.score_minimo || 65;

  // Validação do Gate Completo
  const bloqueiosRegistro: string[] = [];

  if (!gate?.liberado) {
    bloqueiosRegistro.push(...(gate?.motivos || ["Gate do dia bloqueado"]));
  }
  if (killsFaltando.length > 0) {
    bloqueiosRegistro.push(`Faltam ${killsFaltando.length} itens KILL obrigatórios`);
  }
  if (scoreAtual < thresholdScore) {
    bloqueiosRegistro.push(`Score (${scoreAtual} pts) abaixo do mínimo (${thresholdScore} pts)`);
  }
  if (numEntrada <= 0 || numStop <= 0 || numAlvo <= 0) {
    bloqueiosRegistro.push("Preencha todos os preços (Entrada, Stop e Alvo)");
  } else if (!direcaoValida) {
    bloqueiosRegistro.push(motivoInvalidoPreco || "Níveis de preço incoerentes");
  } else if (rr < 2.0) {
    bloqueiosRegistro.push(`RR planejado (${rr.toFixed(2)}) abaixo de 2.0`);
  }

  const podeLiberar = bloqueiosRegistro.length === 0 && !submitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!podeLiberar) return;

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const payload: CreateTradePayload = {
      data: hoje,
      strategy_id: selectedStratId,
      mercado,
      direcao,
      checklist,
      entrada: numEntrada,
      stop: numStop,
      alvo: numAlvo,
      contratos: numContratos,
      notas,
    };

    try {
      const created = await copaApi.createTrade(payload);
      setSuccessMsg(`Trade #${created.id} liberado e registrado com sucesso!`);
      setTimeout(() => {
        router.push("/copa/trades");
      }, 1000);
    } catch (err: any) {
      if (err instanceof CopaError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg(err.message || "Erro ao registrar trade");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-muted-foreground">Carregando setup...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Topo */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Registro de Trade & Gate Físico</h1>
          <p className="text-sm text-muted-foreground">
            A ordem só é liberada se o setup cumprir a sequência completa e o RR mínimo.
          </p>
        </div>
        <Badge variant={gate?.liberado ? "default" : "destructive"} className="gap-1 px-3 py-1 font-bold">
          {gate?.liberado ? <Unlock className="h-3.5 w-3.5" /> : <Lock className="h-3.5 w-3.5" />}
          GATE {gate?.liberado ? "LIBERADO" : "TRAVADO"}
        </Badge>
      </div>

      {errorMsg && (
        <Alert variant="destructive">
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle>Registro Recusado pelo Servidor</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {successMsg && (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Liberado!</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}

      {/* Aviso de Estratégia Desfavorável hoje */}
      {activeRanking && activeRanking.ambiente === "DESFAVORAVEL" && (
        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Aviso de Ambiente Desfavorável Hoje</AlertTitle>
          <AlertDescription>
            A sua pré-sessão indicou que esta estratégia está desfavorável para hoje:{" "}
            <span className="font-semibold">{activeRanking.motivos.join("; ")}</span>.
            Você ainda pode registrar se confirmar todos os critérios, mas opere com cautela.
          </AlertDescription>
        </Alert>
      )}

      {/* 1. Escolha da Estratégia e Ativo */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>1. Estratégia e Ativo</CardTitle>
          <CardDescription>Selecione a estratégia correspondente ao setup que você identificou.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Estratégia</Label>
            <Select
              value={selectedStratId}
              onChange={(e: any) => {
                setSelectedStratId(e.target.value);
                setChecklist({});
              }}
            >
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Mercado / Ativo</Label>
            <div className="flex gap-2">
              {(["WIN", "WDO"] as Mercado[]).map((m) => (
                <Button
                  key={m}
                  type="button"
                  variant={mercado === m ? "default" : "outline"}
                  onClick={() => setMercado(m)}
                  className="flex-1 font-bold font-mono"
                >
                  {m} ({m === "WIN" ? "Mini Índice" : "Mini Dólar"})
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Direção da Operação</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={direcao === "COMPRA" ? "default" : "outline"}
                onClick={() => setDirecao("COMPRA")}
                className={cn(
                  "flex-1 font-bold gap-1",
                  direcao === "COMPRA" && "bg-emerald-600 hover:bg-emerald-500 text-white"
                )}
              >
                <ArrowUpRight className="h-4 w-4" /> COMPRA
              </Button>
              <Button
                type="button"
                variant={direcao === "VENDA" ? "default" : "outline"}
                onClick={() => setDirecao("VENDA")}
                className={cn(
                  "flex-1 font-bold gap-1",
                  direcao === "VENDA" && "bg-rose-600 hover:bg-rose-500 text-white"
                )}
              >
                <ArrowDownRight className="h-4 w-4" /> VENDA
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Checklist Interativo com Score ao Vivo */}
      {activeStrategy && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>2. Checklist Obrigatório — {activeStrategy.nome}</CardTitle>
                <CardDescription className="text-xs">{activeStrategy.descricao}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ChecklistForm
              strategy={activeStrategy}
              marcado={checklist}
              onChange={setChecklist}
              modoDefensivo={modoDefensivo}
            />
          </CardContent>
        </Card>
      )}

      {/* 3. Parâmetros de Entrada, Stop, Alvo e Risco */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>3. Níveis de Preço e Gestão de Risco</CardTitle>
          <CardDescription>O trade deve ter stop e alvo técnicos definidos antes do clique.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="trade-entrada">Preço de Entrada</Label>
              <Input
                id="trade-entrada"
                type="number"
                step="any"
                placeholder="Ex: 135200"
                value={entrada}
                onChange={(e) => setEntrada(e.target.value)}
                className="font-mono text-base font-bold"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trade-stop">Stop Loss (Técnico)</Label>
              <Input
                id="trade-stop"
                type="number"
                step="any"
                placeholder="Ex: 135000"
                value={stop}
                onChange={(e) => setStop(e.target.value)}
                className="font-mono text-base font-bold text-destructive"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trade-alvo">Alvo / Take Profit</Label>
              <Input
                id="trade-alvo"
                type="number"
                step="any"
                placeholder="Ex: 135600"
                value={alvo}
                onChange={(e) => setAlvo(e.target.value)}
                className="font-mono text-base font-bold text-emerald-500"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trade-contratos">Contratos</Label>
              <Input
                id="trade-contratos"
                type="number"
                min="1"
                value={contratos}
                onChange={(e) => setContratos(parseInt(e.target.value, 10) || 1)}
                className="font-mono text-base font-bold"
              />
            </div>
          </div>

          {/* Resumo do Cálculo ao Vivo */}
          <div className="rounded-xl border bg-muted/40 p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">
                Relação Risco:Retorno (RR)
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span
                  className={cn(
                    "text-2xl font-mono font-extrabold",
                    rr >= 2.0 ? "text-emerald-400" : "text-destructive"
                  )}
                >
                  1 : {rr > 0 ? rr.toFixed(2) : "—"}
                </span>
                <span className="text-xs text-muted-foreground">
                  {rr >= 2.0 ? "(Mínimo 2.0 cumprido)" : "(Exige mínimo 1:2.0)"}
                </span>
              </div>
            </div>

            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">
                Risco Máximo Estimado
              </span>
              <div className="text-2xl font-mono font-extrabold text-destructive mt-1">
                R$ {riscoReais.toFixed(2)}
              </div>
            </div>

            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">
                Retorno Potencial no Alvo
              </span>
              <div className="text-2xl font-mono font-extrabold text-emerald-400 mt-1">
                R$ {retornoReais.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="trade-notas">Notas da Operação (Opcional)</Label>
            <Textarea
              id="trade-notas"
              placeholder="Ex: Sweep no PDH com displacement no 1m, entrada no 50% do FVG."
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              rows={2}
            />
          </div>
        </CardContent>

        <CardFooter className="flex flex-col items-stretch gap-3 border-t pt-4">
          <Button
            type="submit"
            size="lg"
            disabled={!podeLiberar}
            className={cn(
              "w-full h-14 text-base font-extrabold tracking-wide uppercase gap-2 transition-all",
              podeLiberar
                ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/40 cursor-pointer"
                : "bg-muted text-muted-foreground cursor-not-allowed opacity-60"
            )}
          >
            {podeLiberar ? (
              <>
                <Unlock className="h-5 w-5" /> LIBERAR E REGISTRAR ENTRADA
              </>
            ) : (
              <>
                <Lock className="h-5 w-5" /> ENTRADA BLOQUEADA PELO GATE
              </>
            )}
          </Button>

          {/* Motivo do Bloqueio sempre visível */}
          {!podeLiberar && bloqueiosRegistro.length > 0 && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-3">
              <span className="text-xs font-bold text-destructive uppercase tracking-wider block mb-1">
                Critérios Pendentes para Desbloqueio:
              </span>
              <ul className="space-y-0.5 text-xs text-red-200 list-disc pl-4">
                {bloqueiosRegistro.map((motivo, i) => (
                  <li key={i}>{motivo}</li>
                ))}
              </ul>
            </div>
          )}
        </CardFooter>
      </Card>
    </form>
  );
}
