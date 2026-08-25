"use client";

import * as React from "react";
import { Trade, MotivoSaida, DesfechoPlano, CloseTradePayload, copaApi, CopaError } from "@/lib/copa-api";
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

interface FecharTradeDialogProps {
  trade: Trade | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTradeClosed: (updated: Trade) => void;
}

export function FecharTradeDialog({
  trade,
  open,
  onOpenChange,
  onTradeClosed,
}: FecharTradeDialogProps) {
  const [saida, setSaida] = React.useState<string>("");
  const [motivoSaida, setMotivoSaida] = React.useState<MotivoSaida>("ALVO");
  const [desfechoPlano, setDesfechoPlano] = React.useState<DesfechoPlano | "">("");

  // 4 flags de disciplina obrigatórias (sem default)
  const [respeitouPlano, setRespeitouPlano] = React.useState<boolean | null>(null);
  const [antecipouStop, setAntecipouStop] = React.useState<boolean | null>(null);
  const [parcialEmocional, setParcialEmocional] = React.useState<boolean | null>(null);
  const [mudouAlvo, setMudouAlvo] = React.useState<boolean | null>(null);

  const [notas, setNotas] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  // Inicializar quando o trade abrir
  React.useEffect(() => {
    if (trade) {
      setSaida(trade.alvo ? String(trade.alvo) : "");
      setMotivoSaida("ALVO");
      setDesfechoPlano("");
      setRespeitouPlano(null);
      setAntecipouStop(null);
      setParcialEmocional(null);
      setMudouAlvo(null);
      setNotas("");
      setErrorMsg(null);
    }
  }, [trade]);

  // Se motivo for ALVO ou STOP, pré-preencher preço
  const handleMotivoChange = (novoMotivo: MotivoSaida) => {
    setMotivoSaida(novoMotivo);
    if (trade) {
      if (novoMotivo === "ALVO") {
        setSaida(String(trade.alvo));
        setDesfechoPlano("");
      } else if (novoMotivo === "STOP") {
        setSaida(String(trade.stop));
        setDesfechoPlano("");
      } else if (novoMotivo === "MANUAL") {
        setDesfechoPlano("NAO_SEI");
      }
    }
  };

  const handleQuickSaida = (target: "ALVO" | "STOP") => {
    if (!trade) return;
    if (target === "ALVO") {
      setMotivoSaida("ALVO");
      setSaida(String(trade.alvo));
    } else {
      setMotivoSaida("STOP");
      setSaida(String(trade.stop));
    }
  };

  if (!trade) return null;

  // Validação estrita
  const numSaida = parseFloat(saida);
  const isSaidaValida = !isNaN(numSaida) && numSaida > 0;
  const isDesfechoValido = motivoSaida !== "MANUAL" || desfechoPlano !== "";
  const isDisciplinaCompleta =
    respeitouPlano !== null &&
    antecipouStop !== null &&
    parcialEmocional !== null &&
    mudouAlvo !== null;

  const podeFechar = isSaidaValida && isDesfechoValido && isDisciplinaCompleta && !submitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!podeFechar) return;

    setSubmitting(true);
    setErrorMsg(null);

    const payload: CloseTradePayload = {
      saida: numSaida,
      motivo_saida: motivoSaida,
      desfecho_plano: motivoSaida === "MANUAL" ? (desfechoPlano as DesfechoPlano) : null,
      respeitou_plano: respeitouPlano ? 1 : 0,
      antecipou_stop: antecipouStop ? 1 : 0,
      parcial_emocional: parcialEmocional ? 1 : 0,
      mudou_alvo: mudouAlvo ? 1 : 0,
      notas: notas.trim(),
    };

    try {
      const closed = await copaApi.closeTrade(trade.id, payload);
      onTradeClosed(closed);
      onOpenChange(false);
    } catch (err: any) {
      if (err instanceof CopaError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg(err.message || "Erro ao encerrar trade");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogClose onClose={() => onOpenChange(false)} />
      <DialogHeader>
        <div className="flex items-center gap-2">
          <DialogTitle>Encerrar Trade #{trade.id}</DialogTitle>
          <Badge variant="outline" className="font-mono text-xs">
            {trade.mercado} {trade.direcao}
          </Badge>
          <Badge className="font-mono text-xs bg-primary/20 text-primary">
            Grade {trade.grade} ({trade.score} pts)
          </Badge>
        </div>
        <DialogDescription className="text-xs">
          Entrada: <span className="font-mono font-bold text-foreground">{trade.entrada}</span> |
          Stop: <span className="font-mono font-bold text-destructive">{trade.stop}</span> |
          Alvo: <span className="font-mono font-bold text-emerald-400">{trade.alvo}</span> |
          Contratos: <span className="font-mono font-bold text-foreground">{trade.contratos}</span>
        </DialogDescription>
      </DialogHeader>

      <form onSubmit={handleSubmit} className="space-y-4 mt-2">
        {errorMsg && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Erro ao encerrar</AlertTitle>
            <AlertDescription>{errorMsg}</AlertDescription>
          </Alert>
        )}

        {/* 1. Preço de Saída e Motivo */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="close-motivo">Motivo de Saída</Label>
            <Select
              value={motivoSaida}
              onChange={(e: any) => handleMotivoChange(e.target.value as MotivoSaida)}
            >
              <option value="ALVO">Bateu no Alvo (Take Profit)</option>
              <option value="STOP">Bateu no Stop Loss</option>
              <option value="MANUAL">Saída Manual / Discricionária</option>
            </Select>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <Label htmlFor="close-saida">Preço de Saída</Label>
              <div className="flex gap-1 text-[10px]">
                <button
                  type="button"
                  onClick={() => handleQuickSaida("ALVO")}
                  className="text-emerald-400 hover:underline cursor-pointer"
                >
                  Alvo
                </button>
                <span>|</span>
                <button
                  type="button"
                  onClick={() => handleQuickSaida("STOP")}
                  className="text-red-400 hover:underline cursor-pointer"
                >
                  Stop
                </button>
              </div>
            </div>
            <Input
              id="close-saida"
              type="number"
              step="any"
              value={saida}
              onChange={(e) => setSaida(e.target.value)}
              className="font-mono text-base font-bold"
              placeholder="Preço executado"
            />
          </div>
        </div>

        {/* Se Saída Manual: O que o preço fez depois? */}
        {motivoSaida === "MANUAL" && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 space-y-1.5 animate-in fade-in-0">
            <Label className="text-xs font-bold text-amber-300">
              Desfecho do Plano (O que o mercado fez após você sair manualmente?) *
            </Label>
            <Select
              value={desfechoPlano}
              onChange={(e: any) => setDesfechoPlano(e.target.value as DesfechoPlano)}
            >
              <option value="">Selecione o que aconteceu...</option>
              <option value="BATEU_ALVO">Teria batido no Alvo original</option>
              <option value="BATEU_STOP">Teria batido no Stop Loss original</option>
              <option value="NAO_SEI">Mercado fechou / Não sei informar</option>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              Essencial para quantificar o Custo da Indisciplina e medir saídas prematuras.
            </p>
          </div>
        )}

        {/* 2. Auditoria Obrigatória de Disciplina (4 Perguntas) */}
        <div className="space-y-2.5 rounded-lg border bg-muted/20 p-3">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <span className="text-xs font-bold uppercase tracking-wider text-foreground">
              Auditoria de Disciplina Operacional (Obrigatório)
            </span>
          </div>

          {/* Q1 */}
          <div className="flex items-center justify-between gap-2 text-xs py-1 border-b border-border/40">
            <span>1. Respeitou o plano do início ao fim?</span>
            <div className="flex gap-1 shrink-0">
              <Button
                type="button"
                size="sm"
                variant={respeitouPlano === true ? "default" : "outline"}
                className={cn("h-7 px-2.5 text-xs", respeitouPlano === true && "bg-emerald-600")}
                onClick={() => setRespeitouPlano(true)}
              >
                Sim
              </Button>
              <Button
                type="button"
                size="sm"
                variant={respeitouPlano === false ? "destructive" : "outline"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setRespeitouPlano(false)}
              >
                Não
              </Button>
            </div>
          </div>

          {/* Q2 */}
          <div className="flex items-center justify-between gap-2 text-xs py-1 border-b border-border/40">
            <span>2. Antecipou o stop loss antes da técnica?</span>
            <div className="flex gap-1 shrink-0">
              <Button
                type="button"
                size="sm"
                variant={antecipouStop === true ? "destructive" : "outline"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setAntecipouStop(true)}
              >
                Sim
              </Button>
              <Button
                type="button"
                size="sm"
                variant={antecipouStop === false ? "default" : "outline"}
                className={cn("h-7 px-2.5 text-xs", antecipouStop === false && "bg-emerald-600")}
                onClick={() => setAntecipouStop(false)}
              >
                Não
              </Button>
            </div>
          </div>

          {/* Q3 */}
          <div className="flex items-center justify-between gap-2 text-xs py-1 border-b border-border/40">
            <span>3. Fez saída parcial emocional no susto?</span>
            <div className="flex gap-1 shrink-0">
              <Button
                type="button"
                size="sm"
                variant={parcialEmocional === true ? "destructive" : "outline"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setParcialEmocional(true)}
              >
                Sim
              </Button>
              <Button
                type="button"
                size="sm"
                variant={parcialEmocional === false ? "default" : "outline"}
                className={cn("h-7 px-2.5 text-xs", parcialEmocional === false && "bg-emerald-600")}
                onClick={() => setParcialEmocional(false)}
              >
                Não
              </Button>
            </div>
          </div>

          {/* Q4 */}
          <div className="flex items-center justify-between gap-2 text-xs py-1">
            <span>4. Mudou o alvo durante o andamento do trade?</span>
            <div className="flex gap-1 shrink-0">
              <Button
                type="button"
                size="sm"
                variant={mudouAlvo === true ? "destructive" : "outline"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setMudouAlvo(true)}
              >
                Sim
              </Button>
              <Button
                type="button"
                size="sm"
                variant={mudouAlvo === false ? "default" : "outline"}
                className={cn("h-7 px-2.5 text-xs", mudouAlvo === false && "bg-emerald-600")}
                onClick={() => setMudouAlvo(false)}
              >
                Não
              </Button>
            </div>
          </div>
        </div>

        {/* Notas adicionais */}
        <div className="space-y-1">
          <Label htmlFor="close-notas" className="text-xs">
            Aprendizado / Observação Pós-Trade
          </Label>
          <Textarea
            id="close-notas"
            placeholder="O que você sentiu durante o trade? Executou a frieza das 5 lições?"
            value={notas}
            onChange={(e) => setNotas(e.target.value)}
            rows={2}
          />
        </div>

        <DialogFooter className="mt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={!podeFechar}
            className={cn(
              "font-bold px-6",
              podeFechar ? "bg-primary" : "bg-muted text-muted-foreground"
            )}
          >
            {submitting ? "Gravando..." : "Confirmar Fechamento e Auditoria"}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
