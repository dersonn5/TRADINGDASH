"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import {
  fetchTodayChecklist,
  saveChecklist,
  LiveChecklist,
  getDefaultChecklist,
} from "@/lib/trading-db";
import {
  avaliarGate,
  passosCumpridos,
  estadoDosPassos,
  alternarPasso,
  avaliarLimitesDia,
  GateResult,
  ItemAvaliado,
  LimitesDia,
} from "@/lib/gate";
import Link from "next/link";
import {
  DEFAULT_STRATEGIES,
  REVERSAO_HTF,
  CONTINUIDADE_TENDENCIA,
} from "@/data/strategies";
import { Strategy } from "@/lib/copa-api";
import {
  getResumoDoDia,
  registrarTrade,
  fecharTrade,
  getTrade,
  gradeFor,
  getDataSaoPaulo,
  getPreSessaoDeHoje,
  pendenciasDaPreSessao,
  PreSessao,
  ResumoDoDia,
} from "@/lib/copa-db";
import { PrintUpload } from "@/components/copa/print-upload";
import { InstBand } from "@/components/inst";

export default function ChecklistPage() {
  // Estratégia selecionada (padrão: REVERSAO_HTF)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>(REVERSAO_HTF);
  const [checklist, setChecklist] = useState<LiveChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [now, setNow] = useState<Date>(() => new Date());

  // Pré-sessão do dia
  const [preSessao, setPreSessao] = useState<PreSessao | null>(null);
  const [preSessaoLoading, setPreSessaoLoading] = useState(true);
  const [tradePrintPath, setTradePrintPath] = useState<string | null>(null);

  // Resumo do dia e trade aberto
  const [resumo, setResumo] = useState<ResumoDoDia | null>(null);
  const [resumoLoading, setResumoLoading] = useState(true);
  const [tradeAberto, setTradeAberto] = useState<any | null>(null);

  // Mensagens de feedback
  const [ordemError, setOrdemError] = useState<string | null>(null);
  const [ordemSuccess, setOrdemSuccess] = useState<string | null>(null);
  const [submittingOrdem, setSubmittingOrdem] = useState(false);

  // Formulário de abertura de trade
  const [mercado, setMercado] = useState<"WIN" | "WDO">("WIN");
  const [direcao, setDirecao] = useState<"COMPRA" | "VENDA">("COMPRA");
  const [entrada, setEntrada] = useState<string>("");
  const [stop, setStop] = useState<string>("");
  const [alvo, setAlvo] = useState<string>("");
  const [contratos, setContratos] = useState<string>("1");

  // Diálogo de fechamento de trade
  const [modalFechamentoOpen, setModalFechamentoOpen] = useState(false);
  const [fechamentoSubmitting, setFechamentoSubmitting] = useState(false);
  const [fechamentoError, setFechamentoError] = useState<string | null>(null);
  const [saida, setSaida] = useState<string>("");
  const [motivoSaida, setMotivoSaida] = useState<"ALVO" | "STOP" | "MANUAL" | "">("");
  const [desfechoPlano, setDesfechoPlano] = useState<"BATEU_ALVO" | "BATEU_STOP" | "NAO_SEI" | "">("");
  const [execucao, setExecucao] = useState<"A" | "B" | "C" | "">("");
  const [respeitouPlano, setRespeitouPlano] = useState<boolean | null>(null);
  const [antecipouStop, setAntecipouStop] = useState<boolean | null>(null);
  const [parcialEmocional, setParcialEmocional] = useState<boolean | null>(null);
  const [mudouAlvo, setMudouAlvo] = useState<boolean | null>(null);
  const [fechamentoNotas, setFechamentoNotas] = useState<string>("");

  // Relógio do pregão (atualizado a cada segundo)
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Carrega o resumo do dia e detalhes de trade aberto se houver
  const loadResumo = useCallback(async () => {
    setResumoLoading(true);
    try {
      const res = await getResumoDoDia();
      setResumo(res);
      if (res.trade_aberto_id) {
        try {
          const t = await getTrade(res.trade_aberto_id);
          setTradeAberto(t);
        } catch {
          setTradeAberto(null);
        }
      } else {
        setTradeAberto(null);
      }
    } catch (err: any) {
      console.error("Erro ao carregar resumo do dia:", err);
    } finally {
      setResumoLoading(false);
    }
  }, []);

  // Carrega o checklist para a estratégia selecionada
  const loadChecklist = useCallback(async (strat: Strategy) => {
    setLoading(true);
    try {
      const data = await fetchTodayChecklist(strat);
      setChecklist(data);
    } catch (err) {
      console.error("Erro ao carregar checklist:", err);
      const hoje = getDataSaoPaulo();
      setChecklist(getDefaultChecklist(hoje, strat));
    } finally {
      setLoading(false);
    }
  }, []);

  // Carrega a pré-sessão de hoje e sincroniza setup e tamanho
  const loadPreSessao = useCallback(async () => {
    setPreSessaoLoading(true);
    try {
      const ps = await getPreSessaoDeHoje();
      setPreSessao(ps);
      if (ps.fechada_em) {
        if (ps.setup_do_dia === "reversao_htf") {
          setSelectedStrategy(REVERSAO_HTF);
        } else if (ps.setup_do_dia === "continuidade_tendencia") {
          setSelectedStrategy(CONTINUIDADE_TENDENCIA);
        }
        if (ps.contratos_declarados) {
          setContratos(String(ps.contratos_declarados));
        }
      }
    } catch (err) {
      console.error("Erro ao carregar pré-sessão:", err);
    } finally {
      setPreSessaoLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPreSessao();
  }, [loadPreSessao]);

  useEffect(() => {
    loadChecklist(selectedStrategy);
    loadResumo();
  }, [loadChecklist, loadResumo, selectedStrategy]);

  // Troca de estratégia com confirmação se houver itens marcados
  async function handleSelectStrategy(strat: Strategy) {
    if (strat.id === selectedStrategy.id) return;
    const hasCheckedItems = checklist?.items?.some((i) => i.checked);
    if (hasCheckedItems) {
      const confirmReset = window.confirm(
        "Existem itens marcados no checklist. Trocar de estratégia vai resetar o checklist. Deseja continuar?"
      );
      if (!confirmReset) return;
    }
    setSelectedStrategy(strat);
    await loadChecklist(strat);
  }

  // Hora corrente formatada em America/Sao_Paulo
  const spTimeStr = useMemo(() => {
    try {
      return new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }).format(now);
    } catch {
      return "--:--:--";
    }
  }, [now]);

  // Avaliação dos limites diários espelhados do Profit Chart
  const limites: LimitesDia = useMemo(() => {
    if (!resumo) return { bloqueado: false, motivos: [] };
    return avaliarLimitesDia(
      resumo.perdas_hoje,
      resumo.operacoes_hoje,
      resumo.ultimo_loss_em,
      now
    );
  }, [resumo, now]);

  // Avaliação do Gate em tempo real com regras de horário, confluência e limites
  const gate: GateResult = useMemo(() => {
    if (!checklist) {
      return {
        liberado: false,
        janela: "FORA",
        score: 0,
        scoreMinimo: selectedStrategy.score_minimo || 65,
        killsFaltando: [],
        motivos: [],
        avisos: [],
      };
    }
    return avaliarGate(
      checklist.items.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now,
      selectedStrategy.score_minimo || 65,
      limites,
      resumo?.trade_aberto_id,
      Boolean(preSessao?.fechada_em),
      Boolean(tradePrintPath)
    );
  }, [checklist, now, selectedStrategy, limites, resumo?.trade_aberto_id, preSessao?.fechada_em, tradePrintPath]);

  const itensAvaliados: ItemAvaliado[] = useMemo(() => {
    if (!checklist) return [];
    return checklist.items.map((i) => ({
      id: i.id,
      tipo: i.tipo,
      label: i.label,
      checked: i.checked,
      peso: i.weight,
    }));
  }, [checklist]);

  const feitos = useMemo(() => {
    return passosCumpridos(itensAvaliados);
  }, [itensAvaliados]);

  const estadosKills = useMemo(() => {
    return estadoDosPassos(itensAvaliados);
  }, [itensAvaliados]);

  const killItems = useMemo(() => {
    if (!checklist) return [];
    return checklist.items.filter((i) => i.tipo === "KILL");
  }, [checklist]);

  const pontoItems = useMemo(() => {
    if (!checklist) return [];
    return checklist.items.filter((i) => i.tipo === "PONTO");
  }, [checklist]);

  function handleToggleKill(id: string) {
    if (!checklist) return;
    const novosAvaliados = alternarPasso(itensAvaliados, id);
    const updatedItems = checklist.items.map((item) => {
      const matching = novosAvaliados.find((a) => a.id === item.id);
      return matching ? { ...item, checked: matching.checked } : item;
    });

    const nextGate = avaliarGate(
      updatedItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now,
      selectedStrategy.score_minimo || 65,
      limites,
      resumo?.trade_aberto_id,
      Boolean(preSessao?.fechada_em),
      Boolean(tradePrintPath)
    );

    setChecklist({
      ...checklist,
      items: updatedItems,
      score: nextGate.score,
      risk_approved: nextGate.liberado,
    });
  }

  function handleTogglePonto(id: string) {
    if (!checklist) return;
    const updatedItems = checklist.items.map((item) =>
      item.id === id ? { ...item, checked: !item.checked } : item
    );

    const nextGate = avaliarGate(
      updatedItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now,
      selectedStrategy.score_minimo || 65,
      limites,
      resumo?.trade_aberto_id,
      Boolean(preSessao?.fechada_em),
      Boolean(tradePrintPath)
    );

    setChecklist({
      ...checklist,
      items: updatedItems,
      score: nextGate.score,
      risk_approved: nextGate.liberado,
    });
  }

  function handleBiasChange(newBias: LiveChecklist["bias"]) {
    if (!checklist) return;
    const nextGate = avaliarGate(
      itensAvaliados,
      newBias,
      now,
      selectedStrategy.score_minimo || 65,
      limites,
      resumo?.trade_aberto_id,
      Boolean(preSessao?.fechada_em),
      Boolean(tradePrintPath)
    );
    setChecklist({
      ...checklist,
      bias: newBias,
      risk_approved: nextGate.liberado,
    });
  }

  function handleReset() {
    if (!checklist) return;
    const resetItems = checklist.items.map((it) => ({ ...it, checked: false }));
    const nextGate = avaliarGate(
      resetItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: false,
        peso: i.weight,
      })),
      checklist.bias,
      now,
      selectedStrategy.score_minimo || 65,
      limites,
      resumo?.trade_aberto_id,
      Boolean(preSessao?.fechada_em),
      Boolean(tradePrintPath)
    );
    setChecklist({
      ...checklist,
      items: resetItems,
      score: nextGate.score,
      risk_approved: nextGate.liberado,
    });
  }

  async function handleSave() {
    if (!checklist) return;
    setSaving(true);
    const toSave: LiveChecklist = {
      ...checklist,
      strategy_id: selectedStrategy.id,
      score: gate.score,
      risk_approved: gate.liberado,
    };
    const ok = await saveChecklist(toSave);
    setSaving(false);
    if (ok) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  }

  // Informações de cores da janela de operação
  const janelaInfo = useMemo(() => {
    switch (gate.janela) {
      case "PRIME":
        return {
          cor: "var(--inst-ok)",
          texto: "PRIME · 10:00–11:00",
          nota: "abertura do à vista + abertura americana",
        };
      case "VALIDA":
        return {
          cor: "var(--inst-now)",
          texto: "FORA DA NOBRE",
          nota: "dentro de 09:00–12:00 · exige score maior",
        };
      case "FORA":
      default:
        return {
          cor: "var(--inst-block)",
          texto: "FORA DA JANELA",
          nota: "operação permitida só das 09:00 às 12:00",
        };
    }
  }, [gate.janela]);

  const scoreOk = useMemo(() => {
    return gate.score >= gate.scoreMinimo;
  }, [gate.score, gate.scoreMinimo]);

  const gateMotivosExibidos = useMemo(() => {
    if (gate.motivos.length > 0) {
      return gate.motivos;
    }
    if (gate.liberado) {
      return ["sequência completa · confluência suficiente · limites liberados"];
    }
    return [];
  }, [gate.motivos, gate.liberado]);

  // Cálculos dinâmicos e validação do formulário de trade
  const numEntrada = parseFloat(entrada.replace(",", "."));
  const numStop = parseFloat(stop.replace(",", "."));
  const numAlvo = parseFloat(alvo.replace(",", "."));
  const numContratos = parseInt(contratos, 10) || 1;

  const precosPreenchidos =
    !isNaN(numEntrada) &&
    numEntrada > 0 &&
    !isNaN(numStop) &&
    numStop > 0 &&
    !isNaN(numAlvo) &&
    numAlvo > 0;

  const validacaoDirecao = useMemo(() => {
    if (!precosPreenchidos) return { ok: false, erro: null };
    if (direcao === "COMPRA") {
      if (!(numStop < numEntrada && numEntrada < numAlvo)) {
        return { ok: false, erro: "COMPRA exige: Stop < Entrada < Alvo" };
      }
    } else {
      if (!(numAlvo < numEntrada && numEntrada < numStop)) {
        return { ok: false, erro: "VENDA exige: Alvo < Entrada < Stop" };
      }
    }
    return { ok: true, erro: null };
  }, [precosPreenchidos, direcao, numEntrada, numStop, numAlvo]);

  const metricasTrade = useMemo(() => {
    if (!precosPreenchidos) {
      return { distStop: 0, distAlvo: 0, riscoReais: 0, retornoReais: 0, rr: 0 };
    }
    const valorPonto = mercado === "WIN" ? 0.2 : 10.0;
    const distStop = Math.abs(numEntrada - numStop);
    const distAlvo = Math.abs(numAlvo - numEntrada);
    const riscoReais = distStop * numContratos * valorPonto;
    const retornoReais = distAlvo * numContratos * valorPonto;
    const rr = distStop > 0 ? distAlvo / distStop : 0;
    return { distStop, distAlvo, riscoReais, retornoReais, rr };
  }, [precosPreenchidos, mercado, numEntrada, numStop, numAlvo, numContratos]);

  const formularioValido = precosPreenchidos && validacaoDirecao.ok && numContratos >= 1;

  // Handler para abrir ordem
  async function handleAbrirOrdem() {
    if (!gate.liberado || !formularioValido || !checklist) return;
    setSubmittingOrdem(true);
    setOrdemError(null);
    setOrdemSuccess(null);

    try {
      const itemsSnapshot = checklist.items.map((i) => ({
        item_id: i.id,
        tipo: i.tipo,
        checked: i.checked,
        peso_no_momento: i.weight,
      }));

      await registrarTrade({
        strategy_id: selectedStrategy.id,
        mercado,
        direcao,
        janela: gate.janela,
        score: gate.score,
        score_minimo: gate.scoreMinimo === Infinity ? 65 : gate.scoreMinimo,
        grade: gradeFor(gate.score),
        entrada: numEntrada,
        stop: numStop,
        alvo: numAlvo,
        contratos: numContratos,
        rr_planejado: Number(metricasTrade.rr.toFixed(2)),
        itens: itemsSnapshot,
        notas: checklist.notes || "",
        screenshot_path: tradePrintPath,
      });

      // Sucesso: limpa o checklist e formulário, recarrega o resumo e confirma
      handleReset();
      setEntrada("");
      setStop("");
      setAlvo("");
      setTradePrintPath(null);
      setOrdemSuccess("Ordem aberta e registrada com sucesso!");
      await loadResumo();
      setTimeout(() => setOrdemSuccess(null), 5000);
    } catch (err: any) {
      // Falha: vermelho com o erro real do Supabase, checklist PRESERVADO
      setOrdemError(err?.message || "Erro desconhecido ao abrir ordem");
    } finally {
      setSubmittingOrdem(false);
    }
  }

  // Handler para fechar trade
  async function handleConfirmarFechamento() {
    if (!resumo?.trade_aberto_id) return;
    const numSaida = parseFloat(saida.replace(",", "."));
    if (isNaN(numSaida) || numSaida <= 0) {
      setFechamentoError("Informe um preço de saída válido.");
      return;
    }
    if (!motivoSaida) {
      setFechamentoError("Selecione o motivo da saída.");
      return;
    }
    if (motivoSaida === "MANUAL" && !desfechoPlano) {
      setFechamentoError("Para saída MANUAL, informe o desfecho segundo o plano.");
      return;
    }
    if (!execucao) {
      setFechamentoError("Classifique a nota da sua EXECUÇÃO (A, B ou C).");
      return;
    }
    if (
      respeitouPlano === null ||
      antecipouStop === null ||
      parcialEmocional === null ||
      mudouAlvo === null
    ) {
      setFechamentoError("Responda todas as 4 perguntas de disciplina.");
      return;
    }

    setFechamentoSubmitting(true);
    setFechamentoError(null);

    try {
      await fecharTrade(resumo.trade_aberto_id, {
        saida: numSaida,
        motivo_saida: motivoSaida,
        desfecho_plano: motivoSaida === "MANUAL" && desfechoPlano !== "" ? desfechoPlano : undefined,
        execucao,
        respeitou_plano: respeitouPlano,
        antecipou_stop: antecipouStop,
        parcial_emocional: parcialEmocional,
        mudou_alvo: mudouAlvo,
        notas: fechamentoNotas,
      });

      setModalFechamentoOpen(false);
      // Reset campos do fechamento
      setSaida("");
      setMotivoSaida("");
      setDesfechoPlano("");
      setExecucao("");
      setRespeitouPlano(null);
      setAntecipouStop(null);
      setParcialEmocional(null);
      setMudouAlvo(null);
      setFechamentoNotas("");

      await loadResumo();
    } catch (err: any) {
      setFechamentoError(err?.message || "Erro ao fechar trade.");
    } finally {
      setFechamentoSubmitting(false);
    }
  }

  if (loading || !checklist || preSessaoLoading) {
    return (
      <div
        className="-m-4 md:-m-6 flex flex-1 items-center justify-center min-h-[calc(100vh-4rem)]"
        style={{ background: "var(--inst-bg)", color: "var(--inst-dim)" }}
      >
        <div className="mono tabular" style={{ fontSize: "12px", letterSpacing: "0.1em" }}>
          CARREGANDO INSTRUMENTO...
        </div>
      </div>
    );
  }

  // 5a. Sem pré-sessão fechada, a tela não opera
  if (!preSessao?.fechada_em) {
    const pendencias = preSessao ? pendenciasDaPreSessao(preSessao) : ["pre-sessao nao iniciada"];
    return (
      <div
        className="-m-4 md:-m-6 flex flex-1 flex-col min-h-[calc(100vh-4rem)] p-6"
        style={{ background: "var(--inst-bg)", color: "var(--inst-text)", gap: "20px" }}
      >
        <div style={{ borderBottom: "1px solid var(--inst-line-2)", paddingBottom: "18px" }}>
          <span className="mono" style={{ fontSize: "10px", letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--inst-faint)" }}>
            CHECKLIST OPERACIONAL
          </span>
          <h1 style={{ fontSize: "23px", fontWeight: 600, letterSpacing: "-0.015em", marginTop: "4px" }}>
            Checklist Pregão
          </h1>
        </div>

        <InstBand
          tom="block"
          titulo="PRÉ-SESSÃO DO DIA NÃO FOI FECHADA"
          linhas={[
            "O gate operacional exige que o ritual de pré-sessão seja concluído e fechado antes de liberar qualquer operação.",
            ...pendencias,
          ]}
          acao={
            <Link href="/pre-sessao">
              <button
                type="button"
                className="mono tabular"
                style={{
                  background: "var(--inst-ok)",
                  border: "1px solid var(--inst-ok)",
                  color: "#08150F",
                  borderRadius: "3px",
                  padding: "10px 20px",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Ir para a Pré-Sessão
              </button>
            </Link>
          }
        />
      </div>
    );
  }

  // 5b. Se setup_do_dia for NENHUM, hoje é dia de não operar
  if (preSessao.setup_do_dia === "NENHUM") {
    return (
      <div
        className="-m-4 md:-m-6 flex flex-1 flex-col min-h-[calc(100vh-4rem)] p-6"
        style={{ background: "var(--inst-bg)", color: "var(--inst-text)", gap: "20px" }}
      >
        <div style={{ borderBottom: "1px solid var(--inst-line-2)", paddingBottom: "18px" }}>
          <span className="mono" style={{ fontSize: "10px", letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--inst-faint)" }}>
            CHECKLIST OPERACIONAL
          </span>
          <h1 style={{ fontSize: "23px", fontWeight: 600, letterSpacing: "-0.015em", marginTop: "4px" }}>
            Checklist Pregão
          </h1>
        </div>

        <InstBand
          tom="lock"
          titulo="HOJE É DIA DE NÃO OPERAR"
          linhas={["Decidido na pré-sessão do dia. Preservação de capital ativa."]}
          acao={
            <Link href="/pre-sessao">
              <button
                type="button"
                className="mono tabular"
                style={{
                  background: "var(--inst-panel-2)",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-text)",
                  borderRadius: "3px",
                  padding: "8px 16px",
                  fontSize: "11px",
                  cursor: "pointer",
                }}
              >
                Ver Pré-Sessão
              </button>
            </Link>
          }
        />
      </div>
    );
  }

  const restam = killItems.length - feitos;
  const dica =
    feitos === killItems.length
      ? "Sequência completa. O trade agora termina no alvo ou no stop."
      : `Só o passo ${feitos + 1} está clicável. Faltam ${restam} para a sequência fechar.`;

  return (
    <div
      className="-m-4 md:-m-6 flex flex-1 flex-col min-h-[calc(100vh-4rem)]"
      style={{ background: "var(--inst-bg)", color: "var(--inst-text)" }}
    >
      {/* ============ 6a. SETUP DO DIA TRAVADO ============ */}
      <div
        style={{
          padding: "14px 24px",
          background: "#0A0D10",
          borderBottom: "1px solid var(--inst-line-2)",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <span className="mono" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)", textTransform: "uppercase" }}>
          SETUP DO DIA
        </span>
        <span style={{ color: "var(--inst-line-2)" }}>·</span>
        <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
          {selectedStrategy.nome}
        </span>
        <span style={{ color: "var(--inst-line-2)" }}>·</span>
        <span className="mono tabular" style={{ fontSize: "11px", color: "var(--inst-dim)", fontStyle: "italic" }}>
          declarado às {preSessao?.fechada_em ? new Date(preSessao.fechada_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "--:--"}
        </span>
        <Link href="/pre-sessao" style={{ marginLeft: "auto" }}>
          <span className="mono tabular" style={{ fontSize: "10.5px", color: "var(--inst-faint)", textDecoration: "underline", cursor: "pointer" }}>
            Ver Pré-Sessão
          </span>
        </Link>
      </div>

      {/* ============ 6b. BARRA DE ESTADO COM DADO REAL ============ */}
      <div
        style={{
          display: "flex",
          alignItems: "stretch",
          borderBottom: "1px solid var(--inst-line-2)",
          background: "var(--inst-panel)",
          flexWrap: "wrap",
        }}
      >
        {/* PREGÃO */}
        <div
          style={{
            padding: "12px 20px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "160px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            PREGÃO
          </span>
          <span className="mono tabular" style={{ fontSize: "18px", fontWeight: 600, letterSpacing: "-0.01em" }}>
            {spTimeStr}
          </span>
        </div>

        {/* JANELA */}
        <div
          style={{
            padding: "12px 20px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            flexGrow: 1,
            minWidth: "240px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            JANELA
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                background: janelaInfo.cor,
              }}
            />
            <span
              className="mono tabular"
              style={{ fontSize: "12px", fontWeight: 600, color: janelaInfo.cor, letterSpacing: "0.02em" }}
            >
              {janelaInfo.texto}
            </span>
            <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
              {janelaInfo.nota}
            </span>
          </div>
        </div>

        {/* OPERAÇÕES (operacoes_hoje / 5) */}
        <div
          style={{
            padding: "12px 20px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "130px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            OPERAÇÕES
          </span>
          <span
            className="mono tabular"
            style={{
              fontSize: "15px",
              fontWeight: 600,
              color: resumoLoading || !resumo
                ? "var(--inst-dim)"
                : resumo.operacoes_hoje >= 5
                ? "var(--inst-block)"
                : resumo.operacoes_hoje === 4
                ? "var(--inst-now)"
                : "var(--inst-text)",
            }}
          >
            {resumoLoading || !resumo ? "—" : `${resumo.operacoes_hoje} / 5`}
          </span>
        </div>

        {/* PERDAS (perdas_hoje / 3) */}
        <div
          style={{
            padding: "12px 20px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "120px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            PERDAS
          </span>
          <span
            className="mono tabular"
            style={{
              fontSize: "15px",
              fontWeight: 600,
              color: resumoLoading || !resumo
                ? "var(--inst-dim)"
                : resumo.perdas_hoje >= 3
                ? "var(--inst-block)"
                : resumo.perdas_hoje >= 1
                ? "var(--inst-now)"
                : "var(--inst-text)",
            }}
          >
            {resumoLoading || !resumo ? "—" : `${resumo.perdas_hoje} / 3`}
          </span>
        </div>

        {/* PNL DIA */}
        <div
          style={{
            padding: "12px 20px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "130px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            PNL DIA
          </span>
          <span
            className="mono tabular"
            style={{
              fontSize: "15px",
              fontWeight: 600,
              color: resumoLoading || !resumo
                ? "var(--inst-dim)"
                : resumo.pnl_dia > 0
                ? "var(--inst-ok)"
                : resumo.pnl_dia < 0
                ? "var(--inst-block)"
                : "var(--inst-dim)",
            }}
          >
            {resumoLoading || !resumo
              ? "—"
              : `${resumo.pnl_dia >= 0 ? "+" : ""}R$ ${resumo.pnl_dia.toLocaleString("pt-BR", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`}
          </span>
        </div>

        {/* BOTÕES RESETAR E SALVAR */}
        <div
          style={{
            padding: "10px 20px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginLeft: "auto",
          }}
        >
          <button
            type="button"
            onClick={handleReset}
            className="mono tabular hover:text-[#E8ECEF] hover:border-[#394148] transition-colors"
            style={{
              background: "transparent",
              border: "1px solid var(--inst-line-2)",
              borderRadius: "3px",
              color: "var(--inst-dim)",
              padding: "6px 12px",
              fontSize: "10px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              cursor: "pointer",
            }}
          >
            RESETAR
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="mono tabular hover:border-[#394148] transition-colors"
            style={{
              background: saveSuccess ? "var(--inst-ok-bg)" : "var(--inst-line)",
              border: `1px solid ${saveSuccess ? "var(--inst-ok-line)" : "var(--inst-line-2)"}`,
              borderRadius: "3px",
              color: saveSuccess ? "var(--inst-ok)" : "var(--inst-text)",
              padding: "6px 14px",
              fontSize: "10px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              cursor: saving ? "not-allowed" : "pointer",
            }}
          >
            {saving ? "SALVANDO..." : saveSuccess ? "SALVO" : "SALVAR"}
          </button>
        </div>
      </div>

      {/* ============ 6e. FAIXA DE TRADE ABERTO ============ */}
      {resumo?.trade_aberto_id && (
        <div
          style={{
            padding: "12px 24px",
            background: "#18140B",
            borderBottom: "1px solid #573B11",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            <span
              style={{
                background: "var(--inst-now)",
                color: "#18140B",
                fontSize: "10px",
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: "2px",
                letterSpacing: "0.08em",
              }}
              className="mono tabular"
            >
              TRADE ABERTO
            </span>
            <span className="mono tabular" style={{ fontSize: "13px", fontWeight: 600, color: "var(--inst-text)" }}>
              {tradeAberto
                ? `${tradeAberto.mercado} ${tradeAberto.direcao} · Entrada: ${tradeAberto.entrada} · Stop: ${tradeAberto.stop} · Alvo: ${tradeAberto.alvo} · ${tradeAberto.contratos} ct (RR 1:${tradeAberto.rr_planejado})`
                : `ID: ${resumo.trade_aberto_id}`}
            </span>
          </div>
          <button
            type="button"
            onClick={() => {
              setFechamentoError(null);
              setModalFechamentoOpen(true);
            }}
            className="mono tabular transition-colors"
            style={{
              background: "var(--inst-now)",
              color: "#0B0E11",
              border: "none",
              borderRadius: "3px",
              padding: "7px 16px",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.08em",
              cursor: "pointer",
            }}
          >
            FECHAR TRADE
          </button>
        </div>
      )}

      {/* FEEDBACK DE SUCESSO OU ERRO NA ABERTURA DE ORDEM */}
      {ordemSuccess && (
        <div
          style={{
            padding: "10px 24px",
            background: "var(--inst-ok-bg)",
            borderBottom: "1px solid var(--inst-ok-line)",
            color: "var(--inst-ok)",
            fontSize: "12px",
            fontWeight: 600,
          }}
          className="mono tabular"
        >
          ✓ {ordemSuccess}
        </div>
      )}
      {ordemError && (
        <div
          style={{
            padding: "10px 24px",
            background: "var(--inst-block-bg)",
            borderBottom: "1px solid var(--inst-block-line)",
            color: "var(--inst-block)",
            fontSize: "12px",
            fontWeight: 600,
          }}
          className="mono tabular"
        >
          ✕ ERRO AO ABRIR ORDEM: {ordemError}
        </div>
      )}

      <div
        className="flex flex-col lg:flex-row flex-grow items-stretch"
        style={{ minHeight: 0 }}
      >
        {/* ============ TRILHA (Coluna Principal) ============ */}
        <div
          className="flex-grow flex flex-col"
          style={{
            padding: "24px 28px 32px 28px",
            gap: "18px",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.16em", color: "var(--inst-faint)" }}>
                  {selectedStrategy.nome.toUpperCase()} · {checklist.market || "WIN"}
                </span>
                <span style={{ color: "var(--inst-line-2)", fontSize: "10px" }}>·</span>
                <div style={{ display: "inline-flex", gap: "4px" }}>
                  {(["BULLISH", "BEARISH", "NEUTRO", "NAO_OPERAR"] as const).map((b) => {
                    const active = checklist.bias === b;
                    return (
                      <button
                        key={b}
                        type="button"
                        onClick={() => handleBiasChange(b)}
                        className="mono tabular"
                        style={{
                          fontSize: "9px",
                          letterSpacing: "0.08em",
                          padding: "2px 6px",
                          borderRadius: "2px",
                          background: active
                            ? b === "NAO_OPERAR"
                              ? "var(--inst-block-bg)"
                              : "var(--inst-now-bg)"
                            : "transparent",
                          color: active
                            ? b === "NAO_OPERAR"
                              ? "var(--inst-block)"
                              : "var(--inst-now)"
                            : "var(--inst-faint)",
                          border: `1px solid ${
                            active
                              ? b === "NAO_OPERAR"
                                ? "var(--inst-block-line)"
                                : "var(--inst-now-line)"
                              : "var(--inst-line-2)"
                          }`,
                          cursor: "pointer",
                        }}
                      >
                        {b === "NAO_OPERAR" ? "NÃO OPERAR" : b}
                      </button>
                    );
                  })}
                </div>
              </div>
              <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 600, letterSpacing: "-0.015em" }}>
                Trilha do setup ({selectedStrategy.nome})
              </h1>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
              <span
                className="mono tabular"
                style={{
                  fontSize: "30px",
                  fontWeight: 600,
                  color: feitos === killItems.length ? "var(--inst-ok)" : "var(--inst-now)",
                  lineHeight: 1,
                }}
              >
                {feitos}
              </span>
              <span className="mono tabular" style={{ fontSize: "15px", color: "var(--inst-faint)" }}>
                / {killItems.length}
              </span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {killItems.map((k, i) => {
              const n = i + 1;
              const estado = estadosKills[i] ?? "TRAVADO";
              const done = estado === "CUMPRIDO";
              const nowStep = estado === "AGORA";

              const marca = done ? "var(--inst-ok)" : (nowStep ? "var(--inst-now)" : "var(--inst-lock)");
              const borda = nowStep ? "var(--inst-now-line)" : "var(--inst-line)";
              const fundo = nowStep ? "var(--inst-now-bg)" : (done ? "var(--inst-panel-2)" : "#0D1013");
              const corTexto = done ? "var(--inst-text-2)" : (nowStep ? "var(--inst-text)" : "var(--inst-ghost)");
              const corAjuda = nowStep ? "var(--inst-dim)" : (done ? "var(--inst-ghost)" : "#333B42");
              const simbolo = done ? "✓" : String(n);
              const isLive = done || nowStep;

              return (
                <div
                  key={k.id}
                  className={`step ${isLive ? "step-live" : ""}`}
                  onClick={isLive ? () => handleToggleKill(k.id) : undefined}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "40px 1fr auto",
                    gap: "16px",
                    alignItems: "start",
                    padding: "13px 16px",
                    border: `1px solid ${borda}`,
                    borderLeft: `3px solid ${marca}`,
                    background: fundo,
                    borderRadius: "3px",
                    cursor: isLive ? "pointer" : "default",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "26px",
                      height: "26px",
                      border: `1px solid ${marca}`,
                      borderRadius: "2px",
                    }}
                  >
                    <span className="mono tabular" style={{ fontSize: "12px", fontWeight: 600, color: marca }}>
                      {simbolo}
                    </span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <span style={{ fontSize: "13.5px", fontWeight: 500, color: corTexto, lineHeight: 1.35 }}>
                      {k.label}
                    </span>
                    {k.ajuda && (
                      <span style={{ fontSize: "11.5px", color: corAjuda, lineHeight: 1.45, maxWidth: "62ch" }}>
                        {k.ajuda}
                      </span>
                    )}
                  </div>

                  <span
                    className="mono tabular"
                    style={{
                      fontSize: "10px",
                      letterSpacing: "0.12em",
                      color: marca,
                      paddingTop: "5px",
                    }}
                  >
                    {estado}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Dica de orientação */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "10px 14px",
              border: "1px dashed var(--inst-line-2)",
              borderRadius: "3px",
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--inst-faint)" strokeWidth="1.6" strokeLinecap="round">
              <path d="M12 8v5"></path>
              <path d="M12 16.5v.01"></path>
              <circle cx="12" cy="12" r="9"></circle>
            </svg>
            <span style={{ fontSize: "12px", color: "var(--inst-dim)" }}>
              {dica}
            </span>
          </div>

          {/* Anotações da Sessão */}
          <div style={{ marginTop: "auto", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
            <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
              ANOTAÇÕES DA SESSÃO
            </span>
            <textarea
              value={checklist.notes || ""}
              onChange={(e) => setChecklist({ ...checklist, notes: e.target.value })}
              placeholder="Observações do pregão, contexto de mercado, comportamento dos players..."
              rows={2}
              style={{
                width: "100%",
                background: "#0D1013",
                border: "1px solid var(--inst-line-2)",
                borderRadius: "3px",
                color: "var(--inst-text)",
                fontSize: "12px",
                padding: "8px 12px",
                resize: "vertical",
                outline: "none",
                fontFamily: "inherit",
              }}
              className="focus:border-[#394148] transition-colors"
            />
          </div>
        </div>

        {/* ============ CONFLUÊNCIA + GATE + FORMULÁRIO (Painel Lateral) ============ */}
        <div
          className="w-full lg:w-[460px] shrink-0 border-t lg:border-t-0 lg:border-l flex flex-col"
          style={{
            borderColor: "var(--inst-line-2)",
            background: "var(--inst-panel)",
          }}
        >
          {/* Cabeçalho de Score */}
          <div
            style={{
              padding: "20px 24px 16px 24px",
              borderBottom: "1px solid var(--inst-line-2)",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
              <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.16em", color: "var(--inst-faint)" }}>
                CONFLUÊNCIA
              </span>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span
                  className="mono tabular"
                  style={{
                    fontSize: "26px",
                    fontWeight: 600,
                    color: scoreOk && gate.janela !== "FORA" ? "var(--inst-ok)" : "var(--inst-now)",
                    lineHeight: 1,
                  }}
                >
                  {gate.score}
                </span>
                <span className="mono tabular" style={{ fontSize: "13px", color: "var(--inst-faint)" }}>
                  / {gate.janela === "FORA" ? "—" : gate.scoreMinimo}
                </span>
              </div>
            </div>

            {/* Barra de Progresso com marcador vertical */}
            <div
              style={{
                position: "relative",
                height: "6px",
                background: "#1B1F23",
                borderRadius: "1px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: `${Math.min(100, Math.max(0, gate.score))}%`,
                  background: scoreOk && gate.janela !== "FORA" ? "var(--inst-ok)" : "var(--inst-now)",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  top: "-3px",
                  bottom: "-3px",
                  left: `${
                    gate.janela === "FORA"
                      ? 100
                      : gate.scoreMinimo === Number.POSITIVE_INFINITY
                      ? 100
                      : Math.min(100, gate.scoreMinimo)
                  }%`,
                  width: "1px",
                  background: "var(--inst-dim)",
                }}
              />
            </div>

            <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)", letterSpacing: "0.06em" }}>
              {gate.janela === "PRIME"
                ? `MÍNIMO ${selectedStrategy.score_minimo || 65} NA JANELA NOBRE`
                : gate.janela === "VALIDA"
                ? `MÍNIMO ${(selectedStrategy.score_minimo || 65) + 15} FORA DA JANELA NOBRE`
                : "BLOQUEADO PELO HORÁRIO"}
            </span>
          </div>

          {/* Lista compacta de Itens PONTO */}
          <div
            style={{
              padding: "8px 12px",
              display: "flex",
              flexDirection: "column",
              gap: "1px",
              borderBottom: "1px solid var(--inst-line-2)",
            }}
          >
            {pontoItems.map((p) => {
              const on = p.checked;
              return (
                <div
                  key={p.id}
                  className="step step-live"
                  onClick={() => handleTogglePonto(p.id)}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "16px 1fr auto",
                    gap: "12px",
                    alignItems: "start",
                    padding: "8px 12px",
                    borderRadius: "3px",
                    background: on ? "var(--inst-ok-bg)" : "transparent",
                    cursor: "pointer",
                  }}
                >
                  <div
                    style={{
                      width: "13px",
                      height: "13px",
                      border: `1px solid ${on ? "var(--inst-ok)" : "var(--inst-lock)"}`,
                      background: on ? "var(--inst-ok)" : "transparent",
                      borderRadius: "2px",
                      marginTop: "2px",
                    }}
                  />
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span
                      style={{
                        fontSize: "12px",
                        color: on ? "var(--inst-text)" : "#6E787F",
                        lineHeight: 1.35,
                      }}
                    >
                      {p.label}
                    </span>
                  </div>
                  <span
                    className="mono tabular"
                    style={{
                      fontSize: "11px",
                      fontWeight: 500,
                      color: on ? "var(--inst-ok)" : "var(--inst-ghost)",
                      paddingTop: "1px",
                    }}
                  >
                    {p.weight}
                  </span>
                </div>
              );
            })}
          </div>

          {/* ============ 6c. FORMULÁRIO DE TRADE ============ */}
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--inst-line-2)",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              background: "#0E1114",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
                PARÂMETROS DA OPERAÇÃO
              </span>
              <div style={{ display: "flex", gap: "6px" }}>
                <button
                  type="button"
                  onClick={() => setMercado("WIN")}
                  className="mono tabular"
                  style={{
                    padding: "3px 8px",
                    fontSize: "10px",
                    borderRadius: "2px",
                    border: `1px solid ${mercado === "WIN" ? "var(--inst-ok)" : "var(--inst-line-2)"}`,
                    background: mercado === "WIN" ? "var(--inst-ok-bg)" : "transparent",
                    color: mercado === "WIN" ? "var(--inst-ok)" : "var(--inst-faint)",
                    cursor: "pointer",
                  }}
                >
                  WIN
                </button>
                <button
                  type="button"
                  onClick={() => setMercado("WDO")}
                  className="mono tabular"
                  style={{
                    padding: "3px 8px",
                    fontSize: "10px",
                    borderRadius: "2px",
                    border: `1px solid ${mercado === "WDO" ? "var(--inst-ok)" : "var(--inst-line-2)"}`,
                    background: mercado === "WDO" ? "var(--inst-ok-bg)" : "transparent",
                    color: mercado === "WDO" ? "var(--inst-ok)" : "var(--inst-faint)",
                    cursor: "pointer",
                  }}
                >
                  WDO
                </button>
              </div>
            </div>

            {/* Direção */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              <button
                type="button"
                onClick={() => setDirecao("COMPRA")}
                className="mono tabular"
                style={{
                  padding: "8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  borderRadius: "3px",
                  border: `1px solid ${direcao === "COMPRA" ? "var(--inst-ok)" : "var(--inst-line-2)"}`,
                  background: direcao === "COMPRA" ? "var(--inst-ok-bg)" : "transparent",
                  color: direcao === "COMPRA" ? "var(--inst-ok)" : "var(--inst-faint)",
                  cursor: "pointer",
                }}
              >
                COMPRA
              </button>
              <button
                type="button"
                onClick={() => setDirecao("VENDA")}
                className="mono tabular"
                style={{
                  padding: "8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  borderRadius: "3px",
                  border: `1px solid ${direcao === "VENDA" ? "var(--inst-block)" : "var(--inst-line-2)"}`,
                  background: direcao === "VENDA" ? "var(--inst-block-bg)" : "transparent",
                  color: direcao === "VENDA" ? "var(--inst-block)" : "var(--inst-faint)",
                  cursor: "pointer",
                }}
              >
                VENDA
              </button>
            </div>

            {/* Preços: Entrada, Stop, Alvo, Contratos */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              <div>
                <label className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block", marginBottom: "3px" }}>
                  ENTRADA
                </label>
                <input
                  type="number"
                  step="any"
                  value={entrada}
                  onChange={(e) => setEntrada(e.target.value)}
                  placeholder="0.00"
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "2px",
                    color: "var(--inst-text)",
                    fontSize: "12px",
                    outline: "none",
                  }}
                />
              </div>

              <div>
                <label className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block", marginBottom: "3px" }}>
                  STOP LOSS
                </label>
                <input
                  type="number"
                  step="any"
                  value={stop}
                  onChange={(e) => setStop(e.target.value)}
                  placeholder="0.00"
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "2px",
                    color: "var(--inst-text)",
                    fontSize: "12px",
                    outline: "none",
                  }}
                />
              </div>

              <div>
                <label className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block", marginBottom: "3px" }}>
                  ALVO (TAKE PROFIT)
                </label>
                <input
                  type="number"
                  step="any"
                  value={alvo}
                  onChange={(e) => setAlvo(e.target.value)}
                  placeholder="0.00"
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "2px",
                    color: "var(--inst-text)",
                    fontSize: "12px",
                    outline: "none",
                  }}
                />
              </div>

              <div>
                <label className="mono tabular" style={{ fontSize: "9px", color: "var(--inst-faint)", display: "block", marginBottom: "3px" }}>
                  CONTRATOS
                </label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={contratos}
                  disabled={true}
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "2px",
                    color: "var(--inst-text)",
                    fontSize: "12px",
                    outline: "none",
                    opacity: 0.8,
                    cursor: "not-allowed",
                  }}
                />
                <span className="mono" style={{ fontSize: "9px", color: "var(--inst-dim)", marginTop: "2px", display: "block" }}>
                  Declarado na pré-sessão. Alterar exige reabrir.
                </span>
              </div>
            </div>

            {/* Validação de Direção */}
            {validacaoDirecao.erro && (
              <div
                className="mono tabular"
                style={{
                  fontSize: "10px",
                  color: "var(--inst-block)",
                  background: "var(--inst-block-bg)",
                  padding: "6px 8px",
                  borderRadius: "2px",
                  border: "1px solid var(--inst-block-line)",
                }}
              >
                {validacaoDirecao.erro}
              </div>
            )}

            {/* Risco e RR em Tempo Real */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: "6px",
                background: "#080A0C",
                padding: "8px 10px",
                borderRadius: "2px",
                border: "1px solid var(--inst-line-2)",
              }}
            >
              <div>
                <span className="mono tabular" style={{ fontSize: "8px", color: "var(--inst-faint)", display: "block" }}>
                  RISCO (R$)
                </span>
                <span className="mono tabular" style={{ fontSize: "12px", fontWeight: 600, color: "var(--inst-block)" }}>
                  {metricasTrade.riscoReais > 0
                    ? `R$ ${metricasTrade.riscoReais.toFixed(2)}`
                    : "—"}
                </span>
              </div>
              <div>
                <span className="mono tabular" style={{ fontSize: "8px", color: "var(--inst-faint)", display: "block" }}>
                  RETORNO (R$)
                </span>
                <span className="mono tabular" style={{ fontSize: "12px", fontWeight: 600, color: "var(--inst-ok)" }}>
                  {metricasTrade.retornoReais > 0
                    ? `R$ ${metricasTrade.retornoReais.toFixed(2)}`
                    : "—"}
                </span>
              </div>
              <div>
                <span className="mono tabular" style={{ fontSize: "8px", color: "var(--inst-faint)", display: "block" }}>
                  R:R ESTIMADO
                </span>
                <span
                  className="mono tabular"
                  style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: metricasTrade.rr >= 2 ? "var(--inst-ok)" : "var(--inst-now)",
                  }}
                >
                  {metricasTrade.rr > 0 ? `1 : ${metricasTrade.rr.toFixed(2)}` : "—"}
                </span>
              </div>
            </div>
          </div>

          {/* ============ 6d. BLOCO DO GATE & BOTÃO ABRIR ORDEM ============ */}
          <div
            style={{
              borderTop: `1px solid ${gate.liberado ? "var(--inst-ok-line)" : "var(--inst-block-line)"}`,
              background: gate.liberado ? "#0D1512" : "var(--inst-block-bg)",
              padding: "16px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              marginTop: "auto",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: gate.liberado ? "var(--inst-ok)" : "var(--inst-block)",
                }}
              />
              <span
                className="mono tabular"
                style={{
                  fontSize: "14px",
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  color: gate.liberado ? "var(--inst-ok)" : "var(--inst-block)",
                }}
              >
                {gate.liberado ? "GATE LIBERADO" : "GATE BLOQUEADO"}
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {gateMotivosExibidos.map((texto, idx) => (
                <div key={idx} style={{ display: "grid", gridTemplateColumns: "12px 1fr", gap: "8px", alignItems: "start" }}>
                  <span
                    className="mono tabular"
                    style={{
                      fontSize: "11px",
                      color: gate.liberado ? "var(--inst-ok)" : "var(--inst-block)",
                      lineHeight: 1.4,
                    }}
                  >
                    —
                  </span>
                  <span style={{ fontSize: "11.5px", color: "var(--inst-text-2)", lineHeight: 1.4 }}>
                    {texto}
                  </span>
                </div>
              ))}
            </div>

            {gate.avisos.length > 0 && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                  padding: "6px 10px",
                  background: "var(--inst-now-bg)",
                  border: "1px solid var(--inst-now-line)",
                  borderRadius: "2px",
                }}
              >
                {gate.avisos.map((aviso, idx) => (
                  <div key={idx} style={{ display: "grid", gridTemplateColumns: "12px 1fr", gap: "6px", alignItems: "start" }}>
                    <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-now)", lineHeight: 1.4 }}>
                      !
                    </span>
                    <span style={{ fontSize: "10.5px", color: "var(--inst-now)", lineHeight: 1.4 }}>
                      {aviso}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Print do Trade (Obrigatório antes de abrir ordem) */}
            <div style={{ marginBottom: "6px" }}>
              <PrintUpload
                path={tradePrintPath}
                data={getDataSaoPaulo()}
                nome={`trade-${Date.now()}`}
                onChange={(p) => setTradePrintPath(p)}
                obrigatorio={true}
                label="Print do Trade (Setup Antes do Desfecho)"
              />
            </div>

            {/* BOTÃO ABRIR ORDEM: sempre visível, travado quando bloqueado ou formulário inválido */}
            {(() => {
              const podeAbrir = gate.liberado && formularioValido && !submittingOrdem && !resumo?.trade_aberto_id;
              return (
                <button
                  type="button"
                  disabled={!podeAbrir}
                  onClick={handleAbrirOrdem}
                  className="mono tabular transition-all"
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "14px",
                    border: `1px solid ${podeAbrir ? "var(--inst-ok)" : "#2A3138"}`,
                    background: podeAbrir ? "var(--inst-ok)" : "transparent",
                    borderRadius: "3px",
                    cursor: podeAbrir ? "pointer" : "not-allowed",
                  }}
                >
                  <span
                    style={{
                      fontSize: "12.5px",
                      fontWeight: 700,
                      letterSpacing: "0.1em",
                      color: podeAbrir ? "#08150F" : "var(--inst-ghost)",
                    }}
                  >
                    {submittingOrdem ? "REGISTRANDO ORDEM..." : "ABRIR ORDEM"}
                  </span>
                </button>
              );
            })()}
          </div>
        </div>
      </div>

      {/* ============ 7. DIÁLOGO DE FECHAMENTO ============ */}
      {modalFechamentoOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "#0D1114",
              border: "1px solid var(--inst-line-2)",
              borderRadius: "4px",
              width: "100%",
              maxWidth: "580px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              boxShadow: "0 20px 40px rgba(0,0,0,0.6)",
            }}
          >
            {/* Header Fechamento */}
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", borderBottom: "1px solid var(--inst-line-2)", paddingBottom: "12px" }}>
              <div>
                <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.16em", color: "var(--inst-now)" }}>
                  JOURNAL DE SAÍDA
                </span>
                <h2 style={{ margin: "4px 0 0 0", fontSize: "18px", fontWeight: 700, letterSpacing: "-0.01em" }}>
                  Encerramento da Operação
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setModalFechamentoOpen(false)}
                className="mono tabular"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--inst-faint)",
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            {/* Erro de validação no fechamento */}
            {fechamentoError && (
              <div
                className="mono tabular"
                style={{
                  padding: "8px 12px",
                  background: "var(--inst-block-bg)",
                  border: "1px solid var(--inst-block-line)",
                  color: "var(--inst-block)",
                  fontSize: "11px",
                  borderRadius: "2px",
                }}
              >
                {fechamentoError}
              </div>
            )}

            {/* Preço de saída e motivo */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)", display: "block", marginBottom: "4px" }}>
                  PREÇO DE SAÍDA *
                </label>
                <input
                  type="number"
                  step="any"
                  value={saida}
                  onChange={(e) => setSaida(e.target.value)}
                  placeholder="0.00"
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "3px",
                    color: "var(--inst-text)",
                    fontSize: "13px",
                    outline: "none",
                  }}
                />
              </div>

              <div>
                <label className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)", display: "block", marginBottom: "4px" }}>
                  MOTIVO DA SAÍDA *
                </label>
                <select
                  value={motivoSaida}
                  onChange={(e) => setMotivoSaida(e.target.value as any)}
                  className="mono tabular"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "3px",
                    color: "var(--inst-text)",
                    fontSize: "12px",
                    outline: "none",
                  }}
                >
                  <option value="">Selecione...</option>
                  <option value="ALVO">ALVO (Bateu Take Profit)</option>
                  <option value="STOP">STOP (Bateu Stop Loss)</option>
                  <option value="MANUAL">MANUAL (Zeragem antecipada)</option>
                </select>
              </div>
            </div>

            {/* Se MANUAL: desfecho no plano obrigatório */}
            {motivoSaida === "MANUAL" && (
              <div style={{ padding: "10px 14px", background: "#13161A", border: "1px solid var(--inst-line-2)", borderRadius: "3px" }}>
                <label className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-now)", display: "block", marginBottom: "6px" }}>
                  DESFECHO SEGUNDO O PLANO (OBRIGATÓRIO PARA SAÍDA MANUAL) *
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                  {[
                    { val: "BATEU_ALVO", lbl: "Bateu no Alvo" },
                    { val: "BATEU_STOP", lbl: "Bateu no Stop" },
                    { val: "NAO_SEI", lbl: "Não sei / Outro" },
                  ].map((d) => (
                    <button
                      key={d.val}
                      type="button"
                      onClick={() => setDesfechoPlano(d.val as any)}
                      className="mono tabular"
                      style={{
                        padding: "6px 8px",
                        fontSize: "11px",
                        borderRadius: "2px",
                        border: `1px solid ${desfechoPlano === d.val ? "var(--inst-now)" : "var(--inst-line-2)"}`,
                        background: desfechoPlano === d.val ? "var(--inst-now-bg)" : "transparent",
                        color: desfechoPlano === d.val ? "var(--inst-now)" : "var(--inst-faint)",
                        cursor: "pointer",
                      }}
                    >
                      {d.lbl}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* A PERGUNTA MAIS IMPORTANTE: EXECUÇÃO (A / B / C) */}
            <div
              style={{
                padding: "14px 16px",
                background: "#080A0C",
                border: "1px solid var(--inst-line-2)",
                borderRadius: "3px",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <div>
                <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--inst-text)" }}>
                  Como foi a EXECUÇÃO? <span style={{ color: "var(--inst-now)", fontWeight: 400 }}>(não o resultado)</span>
                </div>
                <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px", lineHeight: 1.4 }}>
                  Avalie o seu processo e disciplina. Vitória com execução C reforça vício e é o resultado mais perigoso no trading.
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {[
                  {
                    nota: "A",
                    titulo: "A — Fiz exatamente o que devia",
                    desc: "Sem hesitar, sem perseguir, sem antecipar. Respeito integral ao sistema.",
                    cor: "var(--inst-ok)",
                    bg: "var(--inst-ok-bg)",
                  },
                  {
                    nota: "B",
                    titulo: "B — Executei, mas com ruído",
                    desc: "Hesitei, entrei um pouco torto, saí cedo ou hesitei na confirmação.",
                    cor: "var(--inst-now)",
                    bg: "var(--inst-now-bg)",
                  },
                  {
                    nota: "C",
                    titulo: "C — Forcei / quebrei regra",
                    desc: "Entortei a regra, antecipei sem confirmação, busquei recuperar ou cometi erro de tilt.",
                    cor: "var(--inst-block)",
                    bg: "var(--inst-block-bg)",
                  },
                ].map((item) => {
                  const sel = execucao === item.nota;
                  return (
                    <div
                      key={item.nota}
                      onClick={() => setExecucao(item.nota as any)}
                      style={{
                        padding: "10px 12px",
                        border: `1px solid ${sel ? item.cor : "var(--inst-line-2)"}`,
                        background: sel ? item.bg : "transparent",
                        borderRadius: "3px",
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        gap: "2px",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span className="mono tabular" style={{ fontSize: "12px", fontWeight: 700, color: sel ? item.cor : "var(--inst-text)" }}>
                          {item.titulo}
                        </span>
                        {sel && <span style={{ color: item.cor, fontSize: "12px" }}>✓</span>}
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--inst-dim)", lineHeight: 1.35 }}>
                        {item.desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* As 4 perguntas de disciplina */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
                CHECKLIST DE DISCIPLINA *
              </span>

              {[
                { label: "Respeitou o plano?", val: respeitouPlano, set: setRespeitouPlano },
                { label: "Antecipou o stop?", val: antecipouStop, set: setAntecipouStop },
                { label: "Fez parcial emocional?", val: parcialEmocional, set: setParcialEmocional },
                { label: "Mudou o alvo durante o trade?", val: mudouAlvo, set: setMudouAlvo },
              ].map((perg, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 12px",
                    background: "#080A0C",
                    border: "1px solid var(--inst-line-2)",
                    borderRadius: "2px",
                  }}
                >
                  <span style={{ fontSize: "12px", color: "var(--inst-text-2)" }}>{perg.label}</span>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <button
                      type="button"
                      onClick={() => perg.set(true)}
                      className="mono tabular"
                      style={{
                        padding: "3px 10px",
                        fontSize: "10px",
                        borderRadius: "2px",
                        border: `1px solid ${perg.val === true ? "var(--inst-ok)" : "var(--inst-line-2)"}`,
                        background: perg.val === true ? "var(--inst-ok-bg)" : "transparent",
                        color: perg.val === true ? "var(--inst-ok)" : "var(--inst-faint)",
                        cursor: "pointer",
                      }}
                    >
                      SIM
                    </button>
                    <button
                      type="button"
                      onClick={() => perg.set(false)}
                      className="mono tabular"
                      style={{
                        padding: "3px 10px",
                        fontSize: "10px",
                        borderRadius: "2px",
                        border: `1px solid ${perg.val === false ? "var(--inst-block)" : "var(--inst-line-2)"}`,
                        background: perg.val === false ? "var(--inst-block-bg)" : "transparent",
                        color: perg.val === false ? "var(--inst-block)" : "var(--inst-faint)",
                        cursor: "pointer",
                      }}
                    >
                      NÃO
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Notas livres de encerramento */}
            <div>
              <label className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)", display: "block", marginBottom: "4px" }}>
                OBSERVAÇÕES DO FECHAMENTO
              </label>
              <textarea
                value={fechamentoNotas}
                onChange={(e) => setFechamentoNotas(e.target.value)}
                placeholder="Sentimento, contexto da saída, motivos de eventual desvio..."
                rows={2}
                className="mono tabular"
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  background: "#080A0C",
                  border: "1px solid var(--inst-line-2)",
                  borderRadius: "3px",
                  color: "var(--inst-text)",
                  fontSize: "12px",
                  outline: "none",
                  resize: "vertical",
                }}
              />
            </div>

            {/* Botões de Ação do Diálogo */}
            <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => setModalFechamentoOpen(false)}
                className="mono tabular"
                style={{
                  flex: 1,
                  padding: "12px",
                  background: "transparent",
                  border: "1px solid var(--inst-line-2)",
                  color: "var(--inst-dim)",
                  borderRadius: "3px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                CANCELAR
              </button>
              <button
                type="button"
                onClick={handleConfirmarFechamento}
                disabled={fechamentoSubmitting}
                className="mono tabular"
                style={{
                  flex: 2,
                  padding: "12px",
                  background: "var(--inst-ok)",
                  border: "1px solid var(--inst-ok)",
                  color: "#08150F",
                  borderRadius: "3px",
                  fontSize: "11px",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  cursor: fechamentoSubmitting ? "not-allowed" : "pointer",
                }}
              >
                {fechamentoSubmitting ? "FECHANDO..." : "CONFIRMAR FECHAMENTO"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
