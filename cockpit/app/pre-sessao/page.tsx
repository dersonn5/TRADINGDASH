"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import {
  getPreSessaoDeHoje,
  salvarPreSessao,
  fecharPreSessao,
  reabrirPreSessao,
  pendenciasDaPreSessao,
  PreSessao,
} from "@/lib/copa-db";
import { REVERSAO_HTF, CONTINUIDADE_TENDENCIA, VARRIDA_BARRA_10 } from "@/data/strategies";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstBadge,
  InstBand,
  InstDivider,
  InstEmpty,
  InstNum,
} from "@/components/inst";
import { PrintUpload } from "@/components/print-upload";
import { Plus, Trash2, Check, Lock, Unlock, AlertCircle, ArrowRight, X } from "lucide-react";

export default function PreSessaoPage() {
  const [sessao, setSessao] = useState<PreSessao | null>(null);
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<"salvo" | "salvando" | "erro" | null>("salvo");
  const [fechando, setFechando] = useState(false);
  const [erroFechar, setErroFechar] = useState<string | null>(null);
  const [modalReabrir, setModalReabrir] = useState(false);
  const [motivoReabrir, setMotivoReabrir] = useState("");
  const [reabrindo, setReabrindo] = useState(false);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const sessaoRef = useRef<PreSessao | null>(null);
  sessaoRef.current = sessao;

  // Carrega pré-sessão de hoje
  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const s = await getPreSessaoDeHoje();
      setSessao(s);
    } catch (err: any) {
      console.error("Erro ao carregar pré-sessão:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // Função para salvar com debounce automático de 800ms
  const dispararSalvarDebounce = useCallback((proximaSessao: PreSessao) => {
    if (proximaSessao.fechada_em) return; // Não salva se já fechada

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    setSaveStatus("salvando");
    debounceTimerRef.current = setTimeout(async () => {
      try {
        await salvarPreSessao(proximaSessao);
        setSaveStatus("salvo");
      } catch (err: any) {
        console.error("Erro no auto-save:", err);
        setSaveStatus("erro");
      }
    }, 800);
  }, []);

  const updateField = <K extends keyof PreSessao>(campo: K, valor: PreSessao[K]) => {
    if (!sessao || sessao.fechada_em) return;
    const atualizada = { ...sessao, [campo]: valor };
    setSessao(atualizada);
    dispararSalvarDebounce(atualizada);
  };

  const handleFechar = async () => {
    if (!sessao) return;
    setErroFechar(null);
    setFechando(true);
    try {
      // Salva imediatamente antes de tentar fechar para sincronizar estado
      await salvarPreSessao(sessao);
      await fecharPreSessao();
      const recarregada = await getPreSessaoDeHoje();
      setSessao(recarregada);
      setSaveStatus("salvo");
    } catch (err: any) {
      setErroFechar(err.message || "Erro ao fechar pré-sessão");
    } finally {
      setFechando(false);
    }
  };

  const handleReabrir = async () => {
    if (!motivoReabrir.trim()) return;
    setReabrindo(true);
    try {
      await reabrirPreSessao(motivoReabrir.trim());
      setModalReabrir(false);
      setMotivoReabrir("");
      const recarregada = await getPreSessaoDeHoje();
      setSessao(recarregada);
    } catch (err: any) {
      alert("Erro ao reabrir pré-sessão: " + err.message);
    } finally {
      setReabrindo(false);
    }
  };

  // Funções de apoio para listas
  const adicionarNivel = () => {
    if (!sessao || sessao.fechada_em) return;
    const novos = [...sessao.niveis, { label: "", preco: "" }];
    updateField("niveis", novos);
  };

  const atualizarNivel = (index: number, campo: "label" | "preco", val: string) => {
    if (!sessao || sessao.fechada_em) return;
    const novos = sessao.niveis.map((n, i) => (i === index ? { ...n, [campo]: val } : n));
    updateField("niveis", novos);
  };

  const removerNivel = (index: number) => {
    if (!sessao || sessao.fechada_em) return;
    const novos = sessao.niveis.filter((_, i) => i !== index);
    updateField("niveis", novos);
  };

  const adicionarEvento = () => {
    if (!sessao || sessao.fechada_em) return;
    const novos = [...sessao.agenda, { evento: "", horario: "09:30", impacto: "MEDIO" as const }];
    updateField("agenda", novos);
  };

  const atualizarEvento = (index: number, campo: "evento" | "horario" | "impacto", val: any) => {
    if (!sessao || sessao.fechada_em) return;
    const novos = sessao.agenda.map((e, i) => (i === index ? { ...e, [campo]: val } : e));
    updateField("agenda", novos);
  };

  const removerEvento = (index: number) => {
    if (!sessao || sessao.fechada_em) return;
    const novos = sessao.agenda.filter((_, i) => i !== index);
    updateField("agenda", novos);
  };

  if (loading) {
    return (
      <InstPage eyebrow="RITUAL MATINAL" title="Pré-sessão">
        <InstEmpty>Carregando ritual de pré-sessão...</InstEmpty>
      </InstPage>
    );
  }

  if (!sessao) {
    return (
      <InstPage eyebrow="RITUAL MATINAL" title="Pré-sessão">
        <InstEmpty>Sessão não disponível.</InstEmpty>
      </InstPage>
    );
  }

  const isFechada = Boolean(sessao.fechada_em);
  const pendencias = pendenciasDaPreSessao(sessao);

  // Formatação do cabeçalho
  const dataHojeObj = new Date();
  const formatadorData = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const dataExtenso = formatadorData.format(dataHojeObj);
  const dataFormatada = dataExtenso.charAt(0).toUpperCase() + dataExtenso.slice(1);
  const eyebrowTexto = dataFormatada;

  const inputStyle: React.CSSProperties = {
    background: "var(--inst-panel-2)",
    border: "1px solid var(--inst-line)",
    color: "var(--inst-text)",
    borderRadius: "10px",
    padding: "8px 12px",
    fontSize: "12px",
    outline: "none",
  };

  const btnChoiceStyle = (selecionado: boolean, disabled: boolean): React.CSSProperties => ({
    background: selecionado ? "var(--inst-panel-2)" : "transparent",
    border: selecionado ? "1px solid var(--inst-ok)" : "1px solid var(--inst-line)",
    color: selecionado ? "var(--inst-ok)" : "var(--inst-dim)",
    padding: "8px 16px",
    borderRadius: "10px",
    fontSize: "11px",
    fontWeight: selecionado ? 700 : 500,
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled && !selecionado ? 0.4 : 1,
    transition: "all 0.15s ease",
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", color: "var(--tx)" }}>
      {/* Cabeçalho v2 */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "24px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>
            {eyebrowTexto} · ritual antes das 10:00
          </span>
          <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>
            Pré-Sessão
          </h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {!isFechada && (
            <span style={{ fontSize: "12px", color: saveStatus === "salvando" ? "var(--ac)" : "var(--tx3)" }}>
              {saveStatus === "salvando" ? "Salvando..." : "Salvo"}
            </span>
          )}
          <span
            style={{
              height: "32px",
              padding: "0 14px",
              borderRadius: "999px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "13px",
              background: "var(--s1)",
              border: "1px solid var(--bd)",
              color: "var(--tx2)",
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: isFechada ? "var(--tx3)" : "var(--ac)",
              }}
            />
            {isFechada ? "Fechada" : "Aberta"}
          </span>
          {isFechada ? (
            <button
              type="button"
              onClick={() => setModalReabrir(true)}
              style={{
                height: "44px",
                padding: "0 22px",
                borderRadius: "12px",
                border: "1px solid var(--bd)",
                background: "transparent",
                color: "var(--tx2)",
                fontFamily: "inherit",
                fontSize: "14px",
                cursor: "pointer",
              }}
            >
              Reabrir
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFechar}
              disabled={fechando || pendencias.length > 0}
              style={{
                height: "44px",
                padding: "0 22px",
                borderRadius: "12px",
                border: 0,
                fontFamily: "inherit",
                fontSize: "14px",
                fontWeight: 600,
                cursor: fechando || pendencias.length > 0 ? "not-allowed" : "pointer",
                background: pendencias.length > 0 ? "var(--s1)" : "var(--ac)",
                color: pendencias.length > 0 ? "var(--tx3)" : "var(--onac)",
                opacity: fechando ? 0.7 : 1,
              }}
            >
              {fechando ? "Fechando..." : "Fechar pré-sessão"}
            </button>
          )}
        </div>
      </div>
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Mapeamento institucional frio e declaração mecânica antes da abertura do pregão.
      </div>

      {isFechada && (
        <InstBand
          tom="ok"
          titulo="PRÉ-SESSÃO FECHADA E AUDITADA"
          linhas={[
            `Fechada em ${new Date(sessao.fechada_em!).toLocaleTimeString("pt-BR")}. As escolhas foram congeladas para o pregão.`,
            `Setup: ${sessao.setup_do_dia || "NENHUM"} | Tamanho: ${sessao.contratos_declarados || 0} contrato(s)`,
          ]}
          acao={
            <Link href="/checklist">
              <button
                type="button"
                className="mono tabular"
                style={{
                  background: "var(--inst-ok)",
                  border: "1px solid var(--inst-ok)",
                  color: "var(--onac)",
                  borderRadius: "10px",
                  padding: "8px 16px",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Ir para o Checklist Pregão
              </button>
            </Link>
          }
        />
      )}

      {/* 1. PRINT DO GRÁFICO HTF */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
              1 · Print do Gráfico HTF (Obrigatório)
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              60m e 15m com liquidez e arrays marcados, antes das 09:00.
            </div>
          </div>

          <PrintUpload
            path={sessao.screenshot_path}
            data={sessao.data}
            nome="htf_presessao"
            onChange={(p) => updateField("screenshot_path", p)}
            obrigatorio={true}
            disabled={isFechada}
          />
        </div>
      </InstCard>

      {/* 2. LIQUIDEZ E ARRAYS */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
                2 · Liquidez e Arrays
              </div>
              <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
                Mapeie os níveis institucionais de destino e origem no HTF.
              </div>
            </div>

            <div className="mono tabular" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "11px", color: sessao.niveis.length >= 2 ? "var(--inst-ok)" : "var(--inst-block)", fontWeight: 700 }}>
                {sessao.niveis.length} marcados — mínimo 2
              </span>
              {!isFechada && (
                <button
                  type="button"
                  onClick={adicionarNivel}
                  className="mono tabular"
                  style={{
                    background: "var(--inst-panel-2)",
                    border: "1px solid var(--inst-line)",
                    color: "var(--inst-text)",
                    borderRadius: "10px",
                    padding: "4px 10px",
                    fontSize: "11px",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <Plus style={{ width: "12px", height: "12px" }} /> Adicionar Nível
                </button>
              )}
            </div>
          </div>

          {sessao.niveis.length === 0 ? (
            <div className="mono" style={{ fontSize: "11px", color: "var(--inst-faint)", padding: "12px 0", textAlign: "center" }}>
              Nenhum nível marcado. Adicione ao menos 2 níveis (ex: BSL 60m, FVG 15m).
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {sessao.niveis.map((n, idx) => (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <input
                    type="text"
                    placeholder="Identificação (ex: BSL 60m, FVG 15m, Equal Lows)"
                    value={n.label}
                    onChange={(e) => atualizarNivel(idx, "label", e.target.value)}
                    disabled={isFechada}
                    className="mono"
                    style={{ ...inputStyle, flex: 2 }}
                  />
                  <input
                    type="text"
                    placeholder="Preço (ex: 132.500)"
                    value={n.preco}
                    onChange={(e) => atualizarNivel(idx, "preco", e.target.value)}
                    disabled={isFechada}
                    className="mono tabular"
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  {!isFechada && (
                    <button
                      type="button"
                      onClick={() => removerNivel(idx)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--inst-block)",
                        cursor: "pointer",
                        padding: "6px",
                      }}
                      title="Remover"
                    >
                      <Trash2 style={{ width: "14px", height: "14px" }} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </InstCard>

      {/* 3. CONTEXTO */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
              3 · Contexto Macro de Mercado
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              Classificação do regime de liquidez atual. INDEFINIDO bloqueia o fechamento.
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {(["TENDENCIA", "RANGE", "INDEFINIDO"] as const).map((ctx) => (
              <button
                key={ctx}
                type="button"
                onClick={() => updateField("contexto", ctx)}
                disabled={isFechada}
                className="mono"
                style={btnChoiceStyle(sessao.contexto === ctx, isFechada)}
              >
                {ctx === "TENDENCIA" ? "TENDÊNCIA" : ctx}
              </button>
            ))}
          </div>
        </div>
      </InstCard>

      {/* 4. BIAS */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
              4 · Direcional / Bias (D1 e H1)
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              Bias H1 é obrigatório e precisa estar definido como COMPRA ou VENDA.
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
            {/* Bias D1 */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <InstLabel>Bias Diário (D1)</InstLabel>
              <div style={{ display: "flex", gap: "6px" }}>
                {(["COMPRA", "VENDA", "INDEFINIDO"] as const).map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => updateField("bias_d1", b)}
                    disabled={isFechada}
                    className="mono"
                    style={{ ...btnChoiceStyle(sessao.bias_d1 === b, isFechada), flex: 1, textAlign: "center" }}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>

            {/* Bias H1 */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <InstLabel>Bias Intraday (H1)</InstLabel>
                <span style={{ fontSize: "11px", color: "var(--inst-block)", fontWeight: 700 }}>*</span>
              </div>
              <div style={{ display: "flex", gap: "6px" }}>
                {(["COMPRA", "VENDA", "INDEFINIDO"] as const).map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => updateField("bias_h1", b)}
                    disabled={isFechada}
                    className="mono"
                    style={{ ...btnChoiceStyle(sessao.bias_h1 === b, isFechada), flex: 1, textAlign: "center" }}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </InstCard>

      {/* 5. SETUP DO DIA */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
              5 · Setup do Dia (Decisão Fria)
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              A escolha é feita antes da abertura e congela o pregão. NENHUM tem o mesmo peso visual.
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
            <button
              type="button"
              onClick={() => updateField("setup_do_dia", "reversao_htf")}
              disabled={isFechada}
              className="mono"
              style={{
                ...btnChoiceStyle(sessao.setup_do_dia === "reversao_htf", isFechada),
                padding: "16px 14px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span style={{ fontSize: "13px", fontWeight: 700 }}>REVERSÃO HTF</span>
              <span style={{ fontSize: "11px", opacity: 0.7 }}>7 KILLs · 6 PONTOS</span>
            </button>

            <button
              type="button"
              onClick={() => updateField("setup_do_dia", "continuidade_tendencia")}
              disabled={isFechada}
              className="mono"
              style={{
                ...btnChoiceStyle(sessao.setup_do_dia === "continuidade_tendencia", isFechada),
                padding: "16px 14px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span style={{ fontSize: "13px", fontWeight: 700 }}>CONTINUIDADE DE TENDÊNCIA</span>
              <span style={{ fontSize: "11px", opacity: 0.7 }}>6 KILLs · 6 PONTOS</span>
            </button>

            <button
              type="button"
              onClick={() => updateField("setup_do_dia", "varrida_barra_10")}
              disabled={isFechada}
              className="mono"
              style={{
                ...btnChoiceStyle(sessao.setup_do_dia === "varrida_barra_10", isFechada),
                padding: "16px 14px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span style={{ fontSize: "13px", fontWeight: 700 }}>VARRIDA DA BARRA DAS 10</span>
              <span style={{ fontSize: "11px", opacity: 0.7 }}>7 KILLs · 5 PONTOS · EM TESTE</span>
            </button>

            <button
              type="button"
              onClick={() => updateField("setup_do_dia", "NENHUM")}
              disabled={isFechada}
              className="mono"
              style={{
                ...btnChoiceStyle(sessao.setup_do_dia === "NENHUM", isFechada),
                padding: "16px 14px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span style={{ fontSize: "13px", fontWeight: 700 }}>NENHUM (NÃO OPERAR)</span>
              <span style={{ fontSize: "11px", opacity: 0.7 }}>Preservação de Capital</span>
            </button>
          </div>

          {sessao.setup_do_dia && (
            <div
              className="mono"
              style={{
                fontSize: "11px",
                color: "var(--inst-dim)",
                background: "var(--inst-panel-2)",
                border: "1px solid var(--inst-line-2)",
                borderRadius: "10px",
                padding: "10px 14px",
                lineHeight: 1.5,
              }}
            >
              {sessao.setup_do_dia === "reversao_htf" && REVERSAO_HTF.descricao}
              {sessao.setup_do_dia === "continuidade_tendencia" && CONTINUIDADE_TENDENCIA.descricao}
              {sessao.setup_do_dia === "varrida_barra_10" && VARRIDA_BARRA_10.descricao}
              {sessao.setup_do_dia === "NENHUM" &&
                "Hoje é dia de não operar. Decisão válida e sem risco ao capital. O checklist não permitirá novas ordens."}
            </div>
          )}
        </div>
      </InstCard>

      {/* 6. TAMANHO DECLARADO (se setup !== NENHUM) */}
      {sessao.setup_do_dia !== "NENHUM" && (
        <InstCard>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
                6 · Tamanho Declarado
              </div>
              <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
                Declarado agora, frio. Trava durante o pregão.
              </div>
            </div>

            <div style={{ maxWidth: "240px", display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Quantidade de Contratos</InstLabel>
              <input
                type="number"
                min="1"
                step="1"
                placeholder="Ex: 1 ou 2"
                value={sessao.contratos_declarados || ""}
                onChange={(e) => updateField("contratos_declarados", parseInt(e.target.value, 10) || null)}
                disabled={isFechada}
                className="mono tabular"
                style={{ ...inputStyle, fontWeight: 700 }}
              />
            </div>
          </div>
        </InstCard>
      )}

      {/* 7. AGENDA */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
                7 · Agenda e Notícias Macro
              </div>
              <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
                Eventos econômicos que podem gerar volatilidade artificial.
              </div>
            </div>

            {!isFechada && (
              <button
                type="button"
                onClick={adicionarEvento}
                className="mono tabular"
                style={{
                  background: "var(--inst-panel-2)",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-text)",
                  borderRadius: "10px",
                  padding: "4px 10px",
                  fontSize: "11px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <Plus style={{ width: "12px", height: "12px" }} /> Adicionar Notícia
              </button>
            )}
          </div>

          {sessao.agenda.length === 0 ? (
            <div className="mono" style={{ fontSize: "11px", color: "var(--inst-faint)", padding: "8px 0", textAlign: "center" }}>
              Nenhum evento registrado para hoje.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {sessao.agenda.map((ev, idx) => (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <input
                    type="text"
                    placeholder="Evento (ex: Payroll, CPI, Vencimento)"
                    value={ev.evento}
                    onChange={(e) => atualizarEvento(idx, "evento", e.target.value)}
                    disabled={isFechada}
                    className="mono"
                    style={{ ...inputStyle, flex: 2 }}
                  />
                  <input
                    type="time"
                    value={ev.horario}
                    onChange={(e) => atualizarEvento(idx, "horario", e.target.value)}
                    disabled={isFechada}
                    className="mono tabular"
                    style={{ ...inputStyle, width: "95px" }}
                  />
                  <select
                    value={ev.impacto}
                    onChange={(e) => atualizarEvento(idx, "impacto", e.target.value)}
                    disabled={isFechada}
                    className="mono"
                    style={{ ...inputStyle, width: "110px" }}
                  >
                    <option value="BAIXO">BAIXO</option>
                    <option value="MEDIO">MÉDIO</option>
                    <option value="ALTO">ALTO</option>
                  </select>
                  {!isFechada && (
                    <button
                      type="button"
                      onClick={() => removerEvento(idx)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--inst-block)",
                        cursor: "pointer",
                        padding: "6px",
                      }}
                      title="Remover"
                    >
                      <Trash2 style={{ width: "14px", height: "14px" }} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </InstCard>

      {/* 8. ESTADO EMOCIONAL */}
      <InstCard>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
              8 · Autoavaliação de Estado Físico & Emocional
            </div>
            <div style={{ fontSize: "11px", color: "var(--inst-dim)", marginTop: "2px" }}>
              Notas de 0 a 5 em botões discretos.
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
            {/* Sono */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <InstLabel>Qualidade do Sono</InstLabel>
                <span className="mono tabular" style={{ fontSize: "11px", color: "var(--inst-text)" }}>
                  {sessao.sono} / 5
                </span>
              </div>
              <div style={{ display: "flex", gap: "4px" }}>
                {[0, 1, 2, 3, 4, 5].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => updateField("sono", val)}
                    disabled={isFechada}
                    className="mono tabular"
                    style={{ ...btnChoiceStyle(sessao.sono === val, isFechada), flex: 1, padding: "6px 0", textAlign: "center" }}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>

            {/* Tilt */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <InstLabel>Nível de Tilt / Ansiedade</InstLabel>
                <span className="mono tabular" style={{ fontSize: "11px", color: sessao.tilt > 2 ? "var(--inst-block)" : "var(--inst-text)" }}>
                  {sessao.tilt} / 5
                </span>
              </div>
              <div style={{ display: "flex", gap: "4px" }}>
                {[0, 1, 2, 3, 4, 5].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => updateField("tilt", val)}
                    disabled={isFechada}
                    className="mono tabular"
                    style={{ ...btnChoiceStyle(sessao.tilt === val, isFechada), flex: 1, padding: "6px 0", textAlign: "center" }}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>

            {/* Pressão */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <InstLabel>Sensação de Pressão / Meta</InstLabel>
                <span className="mono tabular" style={{ fontSize: "11px", color: sessao.pressao > 2 ? "var(--inst-block)" : "var(--inst-text)" }}>
                  {sessao.pressao} / 5
                </span>
              </div>
              <div style={{ display: "flex", gap: "4px" }}>
                {[0, 1, 2, 3, 4, 5].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => updateField("pressao", val)}
                    disabled={isFechada}
                    className="mono tabular"
                    style={{ ...btnChoiceStyle(sessao.pressao === val, isFechada), flex: 1, padding: "6px 0", textAlign: "center" }}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </InstCard>

      {/* RODAPÉ — FECHAR */}
      {!isFechada && (
        <div>
          {erroFechar && (
            <div style={{ marginBottom: "10px" }}>
              <InstBand tom="block" titulo="ERRO AO FECHAR" linhas={[erroFechar]} />
            </div>
          )}

          {pendencias.length > 0 ? (
            <InstBand
              tom="block"
              titulo="PRÉ-SESSÃO INCOMPLETA"
              linhas={pendencias}
              acao={
                <button
                  type="button"
                  disabled={true}
                  className="mono tabular"
                  style={{
                    background: "var(--inst-panel-2)",
                    border: "1px solid var(--inst-line)",
                    color: "var(--inst-faint)",
                    padding: "10px 20px",
                    borderRadius: "10px",
                    fontSize: "12px",
                    fontWeight: 700,
                    cursor: "not-allowed",
                    opacity: 0.6,
                  }}
                >
                  Fechar Pré-Sessão
                </button>
              }
            />
          ) : (
            <InstBand
              tom="ok"
              titulo="PRONTA PARA FECHAR"
              linhas={[
                "Todos os requisitos foram preenchidos. Fechar trava as escolhas para a sessão de hoje e libera o Checklist Pregão.",
              ]}
              acao={
                <button
                  type="button"
                  onClick={handleFechar}
                  disabled={fechando}
                  className="mono tabular"
                  style={{
                    background: "var(--inst-ok)",
                    border: "1px solid var(--inst-ok)",
                    color: "var(--onac)",
                    padding: "10px 24px",
                    borderRadius: "10px",
                    fontSize: "12px",
                    fontWeight: 700,
                    cursor: fechando ? "not-allowed" : "pointer",
                  }}
                >
                  {fechando ? "Fechando..." : "Fechar Pré-Sessão"}
                </button>
              }
            />
          )}
        </div>
      )}

      {/* Modal de Reabertura */}
      {modalReabrir && (
        <div
          onClick={() => setModalReabrir(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "var(--inst-panel)",
              border: "1px solid var(--inst-line)",
              borderRadius: "10px",
              padding: "20px",
              maxWidth: "480px",
              width: "100%",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)" }}>
                Reabrir Pré-Sessão do Dia
              </span>
              <button
                type="button"
                onClick={() => setModalReabrir(false)}
                style={{ background: "none", border: "none", color: "var(--inst-dim)", cursor: "pointer" }}
              >
                <X style={{ width: "16px", height: "16px" }} />
              </button>
            </div>

            <div style={{ fontSize: "12px", color: "var(--inst-dim)", lineHeight: 1.5 }}>
              Reabrir destrava a pré-sessão para edição, mas registra o horário e o motivo explicitamente nas notas
              da sessão para fins de auditoria de disciplina.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <InstLabel>Motivo da Reabertura</InstLabel>
              <textarea
                placeholder="Ex: Mercado abriu com gap rompendo BSL de 60m antes das 09:15, invalidando a premissa de continuidade..."
                rows={3}
                value={motivoReabrir}
                onChange={(e) => setMotivoReabrir(e.target.value)}
                className="mono"
                style={{ ...inputStyle, width: "100%", resize: "vertical" }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button
                type="button"
                onClick={() => setModalReabrir(false)}
                className="mono tabular"
                style={{
                  background: "transparent",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-dim)",
                  padding: "6px 14px",
                  borderRadius: "10px",
                  fontSize: "11px",
                  cursor: "pointer",
                }}
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleReabrir}
                disabled={reabrindo || !motivoReabrir.trim()}
                className="mono tabular"
                style={{
                  background: "var(--inst-ok)",
                  border: "1px solid var(--inst-ok)",
                  color: "var(--onac)",
                  padding: "6px 16px",
                  borderRadius: "10px",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: reabrindo || !motivoReabrir.trim() ? "not-allowed" : "pointer",
                  opacity: reabrindo || !motivoReabrir.trim() ? 0.6 : 1,
                }}
              >
                {reabrindo ? "Reabrindo..." : "Confirmar Reabertura"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
