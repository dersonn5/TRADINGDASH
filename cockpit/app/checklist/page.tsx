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
  VARRIDA_BARRA_10,
} from "@/data/strategies";
import { Strategy } from "@/lib/types";
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
  GatilhoTrade,
  Contexto1h,
  SetupCModo,
} from "@/lib/copa-db";
import { PrintUpload } from "@/components/print-upload";
import { CARD, LBL, H2, SEGMENTADO, opcaoSegmentada, chip, INPUT, botaoPrimario, BOTAO_SECUNDARIO } from "@/components/v2/estilos";
import { formatarBRL } from "@/lib/metricas";

export default function ChecklistPage() {
  // Estratégia selecionada (padrão: REVERSAO_HTF)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>(REVERSAO_HTF);
  const [checklist, setChecklist] = useState<LiveChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveErro, setSaveErro] = useState(false);
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
  const [gatilho, setGatilho] = useState<GatilhoTrade | "">("");
  const [contexto1h, setContexto1h] = useState<Contexto1h | "">("");
  const [setupCModo, setSetupCModo] = useState<SetupCModo | "">("");

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
        } else if (ps.setup_do_dia === "varrida_barra_10") {
          setSelectedStrategy(VARRIDA_BARRA_10);
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
    setSaveErro(!ok);
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
          nota: "11:00–11:30 · exige score maior",
        };
      case "FORA":
      default:
        return {
          cor: "var(--inst-block)",
          texto: "FORA DA JANELA",
          nota: "entrada só das 10:00 às 11:30 · 09:00–10:00 observar · até 12:00 só gerenciar",
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

  const novosCamposValidos =
    Boolean(gatilho) &&
    Boolean(contexto1h) &&
    (selectedStrategy.id !== "varrida_barra_10" || Boolean(setupCModo));

  const formularioValido =
    precosPreenchidos && validacaoDirecao.ok && numContratos >= 1 && novosCamposValidos;

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
        gatilho,
        contexto_1h: contexto1h,
        setup_c_modo: selectedStrategy.id === "varrida_barra_10" ? setupCModo : null,
      });

      // Sucesso: limpa o checklist e formulário, recarrega o resumo e confirma
      handleReset();
      setEntrada("");
      setStop("");
      setAlvo("");
      setGatilho("");
      setContexto1h("");
      setSetupCModo("");
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

  const cabecalhoPagina = (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Pregão · gate de entrada WIN</span>
      <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Checklist</h1>
    </div>
  );

  if (loading || !checklist || preSessaoLoading) {
    return (
      <>
        {cabecalhoPagina}
        <div style={{ ...CARD, alignItems: "center", padding: "48px", color: "var(--tx3)", fontSize: "14px" }}>Carregando…</div>
      </>
    );
  }

  // Sem pré-sessão fechada, a tela não opera
  if (!preSessao?.fechada_em || preSessao.setup_do_dia === "NENHUM") {
    const naoOperar = preSessao?.fechada_em && preSessao.setup_do_dia === "NENHUM";
    return (
      <>
        {cabecalhoPagina}
        <div style={{ ...CARD, flexDirection: "row", alignItems: "center", gap: "18px" }}>
          <span style={{ width: "52px", height: "52px", flexShrink: 0, borderRadius: "14px", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--s2)", color: "var(--tx3)" }}>
            <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" }}>
              <rect x="5" y="11" width="14" height="10" rx="2" />
              <path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
          </span>
          <div style={{ flexGrow: 1, display: "flex", flexDirection: "column", gap: "6px" }}>
            <span style={{ fontSize: "20px", fontWeight: 600 }}>{naoOperar ? "Hoje é dia de não operar" : "Pré-sessão do dia não foi fechada"}</span>
            <span style={{ fontSize: "13px", color: "var(--tx2)", lineHeight: 1.5 }}>
              {naoOperar
                ? "Decidido na pré-sessão. Preservação de capital."
                : `Falta: ${(preSessao ? pendenciasDaPreSessao(preSessao) : ["pré-sessão não iniciada"]).join(" · ")}`}
            </span>
          </div>
          <Link href="/pre-sessao" style={{ ...BOTAO_SECUNDARIO, height: "44px", display: "flex", alignItems: "center", textDecoration: "none", flexShrink: 0 }}>
            {naoOperar ? "Ver pré-sessão" : "Ir para a pré-sessão"}
          </Link>
        </div>
      </>
    );
  }

  const totalKills = killItems.length;
  const trilhaFrase = feitos >= totalKills ? "Trilha completa" : `Agora: passo ${feitos + 1} de ${totalKills}`;
  const tagSetup = selectedStrategy.id === "varrida_barra_10" ? "C" : selectedStrategy.id === "continuidade_tendencia" ? "B" : "A";
  const minimoMarcador = gate.scoreMinimo === Infinity ? selectedStrategy.score_minimo || 65 : gate.scoreMinimo;
  const janelaCard =
    gate.janela === "PRIME"
      ? { rot: "Janela · Prime", txt: `10:00–10:59 · mínimo ${gate.scoreMinimo}`, destaque: true }
      : gate.janela === "VALIDA"
        ? { rot: "Janela · Válida", txt: `11:00–11:29 · mínimo ${gate.scoreMinimo}`, destaque: true }
        : { rot: "Fora da janela", txt: "entrada só 10:00–11:30", destaque: false };
  const pnlDia = resumo?.pnl_dia ?? 0;
  const podeRegistrar = gate.liberado && formularioValido && !submittingOrdem && !resumo?.trade_aberto_id;
  const motivosGate = gate.motivos.map((m) => m.replace(/^falta obrigatório: .*/, "")).filter(Boolean);
  const faltaPasso = feitos < totalKills ? [`passo ${feitos + 1} da trilha`] : [];
  const gateMotivo = gate.liberado
    ? `Trilha completa e score ${gate.score}. Registre antes de clicar no Profit.`
    : `Falta: ${[...faltaPasso, ...motivosGate].join(" · ")}`;
  const registroFrase = precosPreenchidos
    ? `Risco ${metricasTrade.distStop} pts · RR 1 : ${metricasTrade.rr.toFixed(1).replace(".", ",")} · R$ ${Math.round(metricasTrade.riscoReais).toLocaleString("pt-BR")} em risco`
    : "Preencha entrada, stop e alvo";
  const contratosTravados = Boolean(preSessao?.contratos_declarados);

  const statusCard = (rot: string, valor: React.ReactNode, opts?: { destaque?: boolean; pequeno?: boolean; cor?: string }) => (
    <div style={{ padding: "16px 18px", borderRadius: "14px", background: opts?.destaque ? "var(--acs)" : "var(--s1)", border: "1px solid var(--bd)", display: "flex", flexDirection: "column", gap: "6px" }}>
      <span style={{ fontSize: "11px", letterSpacing: "0.08em", textTransform: "uppercase", color: opts?.destaque ? "var(--actx)" : "var(--tx3)" }}>{rot}</span>
      <span style={{ fontSize: opts?.pequeno ? "15px" : "22px", fontWeight: 600, color: opts?.cor ?? "var(--tx)" }}>{valor}</span>
    </div>
  );

  const chips = <T extends string>(opcoes: Array<{ v: T; l: string }>, atual: string, setar: (v: T) => void) => (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
      {opcoes.map((o) => (
        <button key={o.v} type="button" aria-pressed={atual === o.v} onClick={() => setar(o.v)} style={chip(atual === o.v)}>
          {o.l}
        </button>
      ))}
    </div>
  );

  const campo = (rot: string, valor: string, setar: (v: string) => void, opts?: { disabled?: boolean; nota?: string }) => (
    <label style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "var(--tx2)" }}>
      {rot}
      <input
        type="text"
        inputMode="decimal"
        value={valor}
        disabled={opts?.disabled}
        onChange={(e) => setar(e.target.value)}
        placeholder="0"
        style={{ ...INPUT, opacity: opts?.disabled ? 0.6 : 1 }}
      />
      {opts?.nota && <span style={{ fontSize: "11px", color: "var(--tx3)" }}>{opts.nota}</span>}
    </label>
  );

  const simNao = (rot: string, valor: boolean | null, setar: (v: boolean) => void) => (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", fontSize: "13px" }}>
      <span style={{ color: "var(--tx2)" }}>{rot}</span>
      <div role="group" aria-label={rot} style={{ ...SEGMENTADO, width: "160px" }}>
        {([true, false] as const).map((v) => (
          <button key={String(v)} type="button" aria-pressed={valor === v} onClick={() => setar(v)} style={{ ...opcaoSegmentada(valor === v), height: "34px" }}>
            {v ? "Sim" : "Não"}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <>
      {cabecalhoPagina}

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.3fr repeat(3, minmax(0, 1fr)) 1.3fr", gap: "12px" }}>
        {statusCard("Pregão", spTimeStr)}
        {statusCard(janelaCard.rot, janelaCard.txt, { destaque: janelaCard.destaque, pequeno: true })}
        {statusCard("Perdas", <>{resumo?.perdas_hoje ?? 0} <span style={{ fontSize: "14px", color: "var(--tx3)" }}>/ 3</span></>)}
        {statusCard("Operações", <>{resumo?.operacoes_hoje ?? 0} <span style={{ fontSize: "14px", color: "var(--tx3)" }}>/ 5</span></>)}
        {statusCard("Dia", formatarBRL(pnlDia), { cor: pnlDia > 0 ? "var(--actx)" : pnlDia < 0 ? "var(--negtx)" : "var(--tx)" })}
        {statusCard("Setup do dia", `${tagSetup} · ${NOME_CURTO[selectedStrategy.id] ?? selectedStrategy.nome}`, { pequeno: true })}
      </div>

      {resumo?.trade_aberto_id && (
        <div style={{ display: "flex", alignItems: "center", gap: "14px", padding: "16px 20px", borderRadius: "14px", background: "var(--acs)", border: "1px solid var(--ac)" }}>
          <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "var(--ac)", flexShrink: 0 }} />
          <span style={{ flexGrow: 1, fontSize: "14px" }}>
            <strong style={{ fontWeight: 600 }}>Trade aberto</strong>
            {tradeAberto
              ? ` · ${tradeAberto.direcao === "COMPRA" ? "compra" : "venda"} · entrada ${Number(tradeAberto.entrada).toLocaleString("pt-BR")}, stop ${Number(tradeAberto.stop).toLocaleString("pt-BR")}, alvo ${Number(tradeAberto.alvo).toLocaleString("pt-BR")} · ${tradeAberto.contratos} ct`
              : ""}
          </span>
          <button type="button" onClick={() => { setFechamentoError(null); setModalFechamentoOpen(true); }} style={{ ...botaoPrimario(true), height: "40px" }}>
            Fechar trade
          </button>
        </div>
      )}

      {ordemSuccess && (
        <div style={{ padding: "14px 20px", borderRadius: "14px", background: "var(--acs)", border: "1px solid var(--bd)", color: "var(--actx)", fontSize: "14px", fontWeight: 600 }}>{ordemSuccess}</div>
      )}
      {ordemError && (
        <div style={{ padding: "14px 20px", borderRadius: "14px", background: "var(--s1)", border: "1px solid var(--neg)", color: "var(--negtx)", fontSize: "14px" }}>Erro ao registrar: {ordemError}</div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span style={LBL}>Trilha do Setup {tagSetup} · obrigatórios</span>
                <span style={H2}>{trilhaFrase}</span>
              </div>
              <span style={{ flexShrink: 0, fontSize: "13px", fontWeight: 600, color: "var(--actx)" }}>{feitos} / {totalKills}</span>
            </div>
            <svg width="100%" height="6" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true">
              <rect x="0" y="0" width="100" height="6" rx="3" style={{ fill: "var(--s2)" }} />
              <rect x="0" y="0" width={totalKills ? (feitos / totalKills) * 100 : 0} height="6" rx="3" style={{ fill: "var(--ac)" }} />
            </svg>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {killItems.map((p, i) => {
                const estado = estadosKills[i];
                const feito = estado === "CUMPRIDO";
                const agora = estado === "AGORA";
                const travado = estado === "TRAVADO";
                return (
                  <button
                    key={p.id}
                    type="button"
                    disabled={travado}
                    onClick={() => handleToggleKill(p.id)}
                    style={{
                      textAlign: "left", width: "100%", padding: "14px 16px", borderRadius: "12px", fontFamily: "inherit", display: "flex", gap: "14px", alignItems: "flex-start",
                      cursor: travado ? "not-allowed" : "pointer", background: agora ? "var(--acs)" : "var(--bg)", border: `1px solid ${agora ? "var(--ac)" : "var(--bd)"}`, color: "var(--tx)",
                    }}
                  >
                    <span style={{ width: "28px", height: "28px", flexShrink: 0, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 600, background: feito ? "var(--ac)" : "transparent", color: feito ? "var(--onac)" : agora ? "var(--actx)" : "var(--tx3)", border: `1.5px solid ${feito || agora ? "var(--ac)" : "var(--bd)"}` }}>
                      {feito ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 3, strokeLinecap: "round", strokeLinejoin: "round" }}>
                          <path d="M5 12.5l4.5 4.5L19 7.5" />
                        </svg>
                      ) : (
                        i + 1
                      )}
                    </span>
                    <span style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <span style={{ fontSize: "14px", lineHeight: 1.4, color: travado ? "var(--tx3)" : "var(--tx)" }}>{p.label}</span>
                      {agora && p.ajuda && <span style={{ fontSize: "12px", lineHeight: 1.45, color: "var(--tx2)" }}>{p.ajuda}</span>}
                    </span>
                  </button>
                );
              })}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button type="button" onClick={handleReset} style={{ ...BOTAO_SECUNDARIO, height: "36px", color: "var(--tx2)" }}>Zerar</button>
              <button type="button" onClick={handleSave} disabled={saving} style={{ ...BOTAO_SECUNDARIO, height: "36px" }}>
                {saving ? "Salvando…" : saveSuccess ? "Salvo" : saveErro ? "Não salvou · tentar de novo" : "Salvar progresso"}
              </button>
            </div>
          </section>

          <section style={CARD}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <span style={LBL}>Pontos de qualidade</span>
              <span style={H2}>
                Score {gate.score} de 100 · mínimo {minimoMarcador}
                {gate.janela === "PRIME" ? " na prime" : gate.janela === "VALIDA" ? " depois das 11h" : ""}
              </span>
            </div>
            <svg width="100%" height="28" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">
              <rect x="0" y="8" width="100" height="10" rx="5" style={{ fill: "var(--s2)" }} />
              <rect x="0" y="8" width={Math.min(100, gate.score)} height="10" rx="5" style={{ fill: "var(--ac)" }} />
              <rect x={Math.min(99.2, minimoMarcador - 0.4)} y="2" width="0.8" height="22" style={{ fill: "var(--tx)" }} />
            </svg>
            {pontoItems.map((p) => (
              <label key={p.id} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px 14px", borderRadius: "12px", background: "var(--bg)", border: "1px solid var(--bd)", cursor: "pointer" }}>
                <input type="checkbox" checked={p.checked} onChange={() => handleTogglePonto(p.id)} style={{ width: "18px", height: "18px", accentColor: "var(--ac)" }} />
                <span style={{ flexGrow: 1, fontSize: "14px", lineHeight: 1.4 }}>{p.label}</span>
                <span style={{ fontSize: "13px", fontWeight: 600, color: p.checked ? "var(--actx)" : "var(--tx3)" }}>+{p.weight}</span>
              </label>
            ))}
          </section>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section style={{ padding: "24px", borderRadius: "16px", display: "flex", alignItems: "center", gap: "18px", background: gate.liberado ? "var(--acs)" : "var(--s1)", border: `1px solid ${gate.liberado ? "var(--ac)" : "var(--bd)"}` }}>
            <span style={{ width: "52px", height: "52px", flexShrink: 0, borderRadius: "14px", display: "flex", alignItems: "center", justifyContent: "center", background: gate.liberado ? "var(--ac)" : "var(--s2)", color: gate.liberado ? "var(--onac)" : "var(--tx3)" }}>
              <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" }}>
                <rect x="5" y="11" width="14" height="10" rx="2" />
                <path d={gate.liberado ? "M8 11V7a4 4 0 0 1 7.5-2" : "M8 11V7a4 4 0 0 1 8 0v4"} />
              </svg>
            </span>
            <span style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <span style={{ fontSize: "22px", fontWeight: 600, letterSpacing: "-0.01em", color: gate.liberado ? "var(--actx)" : "var(--tx)" }}>
                {gate.liberado ? "Entrada liberada" : "Entrada bloqueada"}
              </span>
              <span style={{ fontSize: "13px", color: "var(--tx2)", lineHeight: 1.45 }}>{gateMotivo}</span>
            </span>
          </section>

          <section style={CARD}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <span style={LBL}>Registrar trade · WIN</span>
              <span style={H2}>{registroFrase}</span>
            </div>
            <div role="group" aria-label="Lado" style={SEGMENTADO}>
              {(["COMPRA", "VENDA"] as const).map((d) => (
                <button key={d} type="button" aria-pressed={direcao === d} onClick={() => setDirecao(d)} style={opcaoSegmentada(direcao === d)}>
                  {d === "COMPRA" ? "Compra" : "Venda"}
                </button>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "12px", alignItems: "start" }}>
              {campo("Entrada", entrada, setEntrada)}
              {campo("Stop", stop, setStop)}
              {campo("Alvo", alvo, setAlvo)}
              {campo("Contratos", contratos, setContratos, contratosTravados ? { disabled: true, nota: "da pré-sessão" } : undefined)}
            </div>
            {validacaoDirecao.erro && <span style={{ fontSize: "13px", color: "var(--negtx)" }}>{validacaoDirecao.erro}</span>}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Gatilho</span>
              {chips(
                [
                  { v: "MSS_FVG" as GatilhoTrade, l: "MSS + FVG" },
                  { v: "MSS_OB" as GatilhoTrade, l: "MSS + OB" },
                  { v: "BPR" as GatilhoTrade, l: "BPR" },
                  { v: "RISK_ENTRY" as GatilhoTrade, l: "Risk entry" },
                  { v: "FVG_POS_SWING" as GatilhoTrade, l: "FVG após swing" },
                ],
                gatilho,
                setGatilho
              )}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: selectedStrategy.id === "varrida_barra_10" ? "1.6fr 1fr" : "1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Contexto da 1ª hora</span>
                {chips(
                  [
                    { v: "CONTINUACAO" as Contexto1h, l: "Continuação" },
                    { v: "REVERSAO" as Contexto1h, l: "Reversão" },
                    { v: "LATERAL" as Contexto1h, l: "Lateral" },
                  ],
                  contexto1h,
                  setContexto1h
                )}
              </div>
              {selectedStrategy.id === "varrida_barra_10" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Modo do Setup C</span>
                  {chips(
                    [
                      { v: "C1" as SetupCModo, l: "C1" },
                      { v: "C2" as SetupCModo, l: "C2" },
                    ],
                    setupCModo,
                    setSetupCModo
                  )}
                </div>
              )}
            </div>
            <PrintUpload
              path={tradePrintPath}
              data={getDataSaoPaulo()}
              nome={`trade-${Date.now()}`}
              onChange={(p) => setTradePrintPath(p)}
              obrigatorio={true}
              label="Print da entrada · cole com Ctrl+V"
              compacto
            />
            <label style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "var(--tx2)" }}>
              Notas (opcional)
              <textarea
                rows={2}
                value={checklist.notes}
                onChange={(e) => setChecklist({ ...checklist, notes: e.target.value })}
                placeholder="O que você viu na entrada"
                style={{ ...INPUT, height: "auto", padding: "10px 14px", fontSize: "14px", resize: "vertical" }}
              />
            </label>
            <button type="button" onClick={handleAbrirOrdem} disabled={!podeRegistrar} style={{ ...botaoPrimario(podeRegistrar), height: "52px", fontSize: "15px" }}>
              {submittingOrdem ? "Registrando…" : "Registrar trade"}
            </button>
          </section>
        </div>
      </div>

      {modalFechamentoOpen && (
        <div onClick={() => setModalFechamentoOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.7)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
          <div role="dialog" aria-modal="true" aria-label="Fechar trade" onClick={(e) => e.stopPropagation()} style={{ ...CARD, maxWidth: "520px", width: "100%", maxHeight: "90vh", overflowY: "auto" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <span style={LBL}>Fechar trade</span>
              <span style={H2}>
                {tradeAberto ? `${tradeAberto.direcao === "COMPRA" ? "Compra" : "Venda"} · entrada ${Number(tradeAberto.entrada).toLocaleString("pt-BR")}` : "Trade aberto"}
              </span>
            </div>
            <label style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "var(--tx2)" }}>
              Preço de saída
              <input type="text" inputMode="decimal" value={saida} onChange={(e) => setSaida(e.target.value)} placeholder="0" style={INPUT} />
            </label>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Motivo da saída</span>
              <div role="group" aria-label="Motivo da saída" style={SEGMENTADO}>
                {([["ALVO", "Alvo"], ["STOP", "Stop"], ["MANUAL", "Manual"]] as const).map(([v, l]) => (
                  <button key={v} type="button" aria-pressed={motivoSaida === v} onClick={() => setMotivoSaida(v)} style={opcaoSegmentada(motivoSaida === v)}>{l}</button>
                ))}
              </div>
            </div>
            {motivoSaida === "MANUAL" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Depois da saída, o preço…</span>
                <div role="group" aria-label="Desfecho do plano" style={SEGMENTADO}>
                  {([["BATEU_ALVO", "Bateu o alvo"], ["BATEU_STOP", "Bateu o stop"], ["NAO_SEI", "Não sei"]] as const).map(([v, l]) => (
                    <button key={v} type="button" aria-pressed={desfechoPlano === v} onClick={() => setDesfechoPlano(v)} style={opcaoSegmentada(desfechoPlano === v)}>{l}</button>
                  ))}
                </div>
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Nota da execução</span>
              <div role="group" aria-label="Nota da execução" style={SEGMENTADO}>
                {(["A", "B", "C"] as const).map((v) => (
                  <button key={v} type="button" aria-pressed={execucao === v} onClick={() => setExecucao(v)} style={opcaoSegmentada(execucao === v)}>{v}</button>
                ))}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", paddingTop: "12px", borderTop: "1px solid var(--bd)" }}>
              {simNao("Respeitou o plano?", respeitouPlano, setRespeitouPlano)}
              {simNao("Antecipou o stop?", antecipouStop, setAntecipouStop)}
              {simNao("Fez parcial por emoção?", parcialEmocional, setParcialEmocional)}
              {simNao("Mudou o alvo?", mudouAlvo, setMudouAlvo)}
            </div>
            <label style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "var(--tx2)" }}>
              Notas (opcional)
              <textarea rows={2} value={fechamentoNotas} onChange={(e) => setFechamentoNotas(e.target.value)} style={{ ...INPUT, height: "auto", padding: "10px 14px", fontSize: "14px", resize: "vertical" }} />
            </label>
            {fechamentoError && <span style={{ fontSize: "13px", color: "var(--negtx)" }}>{fechamentoError}</span>}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button type="button" onClick={() => setModalFechamentoOpen(false)} style={BOTAO_SECUNDARIO}>Cancelar</button>
              <button type="button" onClick={handleConfirmarFechamento} disabled={fechamentoSubmitting} style={botaoPrimario(!fechamentoSubmitting)}>
                {fechamentoSubmitting ? "Fechando…" : "Confirmar fechamento"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

const NOME_CURTO: Record<string, string> = {
  varrida_barra_10: "Varrida das 10",
  continuidade_tendencia: "Continuidade",
  reversao_htf: "Reversão HTF",
};
