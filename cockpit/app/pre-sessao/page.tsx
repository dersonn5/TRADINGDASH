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
import { PrintUpload } from "@/components/print-upload";
import { EVENTO_PRESESSAO_SALVA } from "@/components/layout/alertas-voz";
import { mesclarAgenda, EventoCalendario, EVENTOS_BRASIL, NOMES_EUA } from "@/lib/calendario";
import { CARD, LBL, H2, SEGMENTADO, opcaoSegmentada, INPUT, botaoPrimario, BOTAO_SECUNDARIO } from "@/components/v2/estilos";

// Espelho de design/v2/PreSessao.dc.html. A logica (auto-save, fechar, reabrir) nao mudou.

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
        window.dispatchEvent(new Event(EVENTO_PRESESSAO_SALVA));
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
      window.dispatchEvent(new Event(EVENTO_PRESESSAO_SALVA));
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
      window.dispatchEvent(new Event(EVENTO_PRESESSAO_SALVA));
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

  // Calendario automatico (EUA): preenche a agenda da pre-sessao aberta.
  const [importando, setImportando] = useState(false);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const importouAuto = useRef(false);

  const importarCalendario = async (automatico: boolean) => {
    const atual = sessaoRef.current;
    if (!atual || atual.fechada_em) return;
    setImportando(true);
    setImportMsg(null);
    try {
      const res = await fetch(`/api/calendario?data=${atual.data}`);
      const corpo = (await res.json()) as { eventos?: EventoCalendario[]; erro?: string };
      if (!res.ok || !corpo.eventos) {
        setImportMsg(`Não foi possível importar: ${corpo.erro ?? `erro ${res.status}`}`);
        return;
      }
      // Parte do estado mais recente: o operador pode ter editado durante o fetch
      const base = sessaoRef.current ?? atual;
      const nova = mesclarAgenda(base.agenda, corpo.eventos);
      const acrescentados = nova.length - base.agenda.length;
      if (acrescentados > 0 && !base.fechada_em) {
        const atualizada = { ...base, agenda: nova };
        setSessao(atualizada);
        dispararSalvarDebounce(atualizada);
      }
      setImportMsg(
        corpo.eventos.length === 0
          ? "Nenhum evento dos EUA de impacto alto ou médio hoje."
          : acrescentados > 0
            ? `${acrescentados} ${acrescentados === 1 ? "evento importado" : "eventos importados"} dos EUA. Revise e acrescente os do Brasil.`
            : automatico ? null : "A agenda já tem todos os eventos dos EUA de hoje."
      );
    } catch (e) {
      setImportMsg(`Não foi possível importar: ${(e as Error).message}`);
    } finally {
      setImportando(false);
    }
  };

  // Agenda vazia numa pre-sessao aberta: importa sozinho, uma vez
  useEffect(() => {
    if (!sessao || loading || importouAuto.current) return;
    importouAuto.current = true;
    if (!sessao.fechada_em && sessao.agenda.length === 0) importarCalendario(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessao, loading]);

  if (loading || !sessao) {
    return (
      <>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Ritual antes das 10:00</span>
          <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Pré-Sessão</h1>
        </div>
        <div style={{ ...CARD, alignItems: "center", padding: "48px", color: "var(--tx3)", fontSize: "14px" }}>
          {loading ? "Carregando…" : "Pré-sessão indisponível."}
        </div>
      </>
    );
  }

  const isFechada = Boolean(sessao.fechada_em);
  const pendencias = pendenciasDaPreSessao(sessao);
  const bloqueado = pendencias.length > 0;

  const dataExtenso = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", weekday: "long", day: "numeric", month: "long" }).format(new Date());
  const dataFormatada = dataExtenso.charAt(0).toUpperCase() + dataExtenso.slice(1);

  // Os 6 requisitos do fechamento — mesma regra de pendenciasDaPreSessao
  const requisitos = [
    { l: "Print HTF", ok: Boolean(sessao.screenshot_path) },
    { l: "Bias H1", ok: sessao.bias_h1 !== "INDEFINIDO" },
    { l: "Contexto", ok: sessao.contexto !== "INDEFINIDO" },
    { l: "2 níveis", ok: sessao.niveis.length >= 2 },
    { l: "Setup do dia", ok: Boolean(sessao.setup_do_dia) },
    { l: "Tamanho", ok: sessao.setup_do_dia === "NENHUM" || (sessao.contratos_declarados ?? 0) > 0 },
  ];

  const BIAS = [
    { v: "COMPRA", l: "Compra" },
    { v: "VENDA", l: "Venda" },
    { v: "INDEFINIDO", l: "Indefinido" },
  ] as const;
  const CONTEXTOS = [
    { v: "TENDENCIA", l: "Tendência" },
    { v: "RANGE", l: "Range" },
    { v: "INDEFINIDO", l: "Indefinido" },
  ] as const;
  const SETUPS = [
    { v: "reversao_htf", tag: "SETUP A", l: "Reversão HTF", d: "Sweep de liquidez HTF e MSS no 1m" },
    { v: "continuidade_tendencia", tag: "SETUP B", l: "Continuidade", d: "Captura do extremo do swing a favor da tendência" },
    { v: "varrida_barra_10", tag: "SETUP C", l: "Varrida das 10", d: "A barra das 10 varre ou é varrida" },
    { v: "NENHUM", tag: "SEM SETUP", l: "Não operar hoje", d: "Dia fora do plano" },
  ] as const;
  const IMPACTO: Record<string, { l: string; bg: string; cor: string }> = {
    ALTO: { l: "Alto", bg: "var(--ac)", cor: "var(--onac)" },
    MEDIO: { l: "Médio", bg: "var(--acs)", cor: "var(--actx)" },
    BAIXO: { l: "Baixo", bg: "var(--s2)", cor: "var(--tx2)" },
  };
  const nomeBias = (v: string) => BIAS.find((b) => b.v === v)?.l.toLowerCase() ?? v;
  const nomeCtx = CONTEXTOS.find((c) => c.v === sessao.contexto)?.l.toLowerCase() ?? "";
  const eventoAlto = sessao.agenda.find((e) => e.impacto === "ALTO" && e.evento.trim());
  const agendaFrase = sessao.agenda.length === 0
    ? "Nenhum evento registrado para hoje"
    : eventoAlto
      ? `${eventoAlto.evento} às ${eventoAlto.horario} é o evento de maior impacto`
      : "Nenhum evento de impacto alto";
  const contratos = sessao.contratos_declarados ?? 0;
  const semSetup = sessao.setup_do_dia === "NENHUM";
  const nomeSetupDia = SETUPS.find((s) => s.v === sessao.setup_do_dia)?.l ?? "—";

  const escala = (campo: "sono" | "tilt" | "pressao", valor: number) => (
    <div style={{ flexGrow: 1, display: "grid", gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: "4px" }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          type="button"
          aria-label={`${i} de 5`}
          disabled={isFechada}
          onClick={() => updateField(campo, valor === i ? i - 1 : i)}
          style={{ height: "10px", padding: 0, border: 0, borderRadius: "3px", cursor: isFechada ? "not-allowed" : "pointer", background: i <= valor ? "var(--ac)" : "var(--s2)" }}
        />
      ))}
    </div>
  );

  const cabecalhoCard = (label: string, frase: React.ReactNode, direita?: React.ReactNode) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={LBL}>{label}</span>
        <span style={H2}>{frase}</span>
      </div>
      {direita}
    </div>
  );

  const botaoAdicionar = (texto: string, onClick: () => void) =>
    isFechada ? null : (
      <button type="button" onClick={onClick} style={{ height: "40px", padding: "0 16px", borderRadius: "10px", border: 0, background: "var(--acs)", color: "var(--actx)", fontFamily: "inherit", fontSize: "13px", fontWeight: 600, cursor: "pointer", flexShrink: 0 }}>
        + {texto}
      </button>
    );

  const botaoRemover = (onClick: () => void, rotulo: string) =>
    isFechada ? null : (
      <button type="button" aria-label={rotulo} onClick={onClick} style={{ width: "36px", height: "36px", flexShrink: 0, borderRadius: "8px", border: 0, background: "transparent", color: "var(--tx3)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" }}>
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    );

  const campoLinha: React.CSSProperties = { ...INPUT, height: "36px", fontSize: "14px", background: "transparent", border: "1px solid transparent", padding: "0 8px" };

  return (
    <>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "24px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>{dataFormatada} · ritual antes das 10:00</span>
          <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Pré-Sessão</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {!isFechada && (
            <span style={{ fontSize: "12px", color: saveStatus === "erro" ? "var(--negtx)" : "var(--tx3)" }}>
              {saveStatus === "salvando" ? "Salvando…" : saveStatus === "erro" ? "Erro ao salvar" : "Salvo"}
            </span>
          )}
          <span style={{ height: "32px", padding: "0 14px", borderRadius: "999px", display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", background: "var(--s1)", border: "1px solid var(--bd)", color: "var(--tx2)" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: isFechada || !bloqueado ? "var(--ac)" : "var(--tx3)" }} />
            {isFechada ? "Fechada" : bloqueado ? `Aberta · ${pendencias.length} ${pendencias.length === 1 ? "pendência" : "pendências"}` : "Pronta para fechar"}
          </span>
          {isFechada ? (
            <button type="button" onClick={() => setModalReabrir(true)} style={{ ...botaoPrimario(true), background: "transparent", color: "var(--tx2)", border: "1px solid var(--bd)", fontWeight: 400 }}>
              Reabrir
            </button>
          ) : (
            <button type="button" onClick={handleFechar} disabled={fechando || bloqueado} style={botaoPrimario(!bloqueado && !fechando)}>
              {fechando ? "Fechando…" : "Fechar pré-sessão"}
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(0, 1fr))", gap: "12px" }}>
        {requisitos.map((r) => (
          <div key={r.l} style={{ padding: "14px 16px", borderRadius: "14px", background: "var(--s1)", border: "1px solid var(--bd)", display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "24px", height: "24px", flexShrink: 0, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", background: r.ok ? "var(--ac)" : "var(--s2)", color: "var(--onac)" }}>
              {r.ok && (
                <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 3, strokeLinecap: "round", strokeLinejoin: "round" }}>
                  <path d="M5 12.5l4.5 4.5L19 7.5" />
                </svg>
              )}
            </span>
            <span style={{ fontSize: "13px", lineHeight: 1.3, color: r.ok ? "var(--tx)" : "var(--tx3)" }}>{r.l}</span>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "20px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section style={CARD}>
            {cabecalhoCard("1 · Print do gráfico HTF", "60m e 15m com liquidez e arrays marcados")}
            <PrintUpload
              path={sessao.screenshot_path}
              data={sessao.data}
              nome="htf_presessao"
              onChange={(p) => updateField("screenshot_path", p)}
              obrigatorio={true}
              disabled={isFechada}
            />
          </section>

          <section style={CARD}>
            {cabecalhoCard(
              "2 · Liquidez e arrays",
              `${sessao.niveis.length} ${sessao.niveis.length === 1 ? "nível marcado" : "níveis marcados"} · mínimo 2`,
              botaoAdicionar("Adicionar nível", adicionarNivel)
            )}
            {sessao.niveis.length === 0 && (
              <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Nenhum nível marcado. Ex.: BSL 60m, FVG 15m, SSL da 1ª hora.</span>
            )}
            {sessao.niveis.map((nv, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "6px 6px 6px 14px", borderRadius: "12px", background: "var(--bg)", border: "1px solid var(--bd)" }}>
                <input
                  type="text"
                  aria-label="Nível"
                  placeholder="BSL 60m, FVG 15m…"
                  value={nv.label}
                  onChange={(e) => atualizarNivel(idx, "label", e.target.value)}
                  disabled={isFechada}
                  style={{ ...campoLinha, flexGrow: 1 }}
                />
                <input
                  type="text"
                  aria-label="Preço"
                  placeholder="132.500"
                  value={nv.preco}
                  onChange={(e) => atualizarNivel(idx, "preco", e.target.value)}
                  disabled={isFechada}
                  style={{ ...campoLinha, width: "120px", textAlign: "right", fontWeight: 600, fontSize: "15px" }}
                />
                {botaoRemover(() => removerNivel(idx), "Remover nível")}
              </div>
            ))}
          </section>

          <section style={CARD}>
            {cabecalhoCard(
              "5 · Agenda do dia",
              agendaFrase,
              isFechada ? null : (
                <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
                  <button type="button" onClick={() => importarCalendario(false)} disabled={importando} style={{ ...BOTAO_SECUNDARIO, color: "var(--tx2)" }}>
                    {importando ? "Importando…" : "Importar dos EUA"}
                  </button>
                  {botaoAdicionar("Adicionar evento", adicionarEvento)}
                </div>
              )
            )}
            {importMsg && <span style={{ fontSize: "12px", color: "var(--tx3)", lineHeight: 1.5 }}>{importMsg}</span>}
            {/* Nomes que a voz Dora tem gravados: escrito assim, o alerta sai com a voz dela */}
            <datalist id="eventos-conhecidos">
              {[...EVENTOS_BRASIL, ...NOMES_EUA].map((n) => <option key={n} value={n} />)}
            </datalist>
            {sessao.agenda.map((ev, idx) => {
              const imp = IMPACTO[ev.impacto] ?? IMPACTO.MEDIO;
              return (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "8px 0", borderTop: "1px solid var(--bd)" }}>
                  <input
                    type="time"
                    aria-label="Horário"
                    value={ev.horario}
                    onChange={(e) => atualizarEvento(idx, "horario", e.target.value)}
                    disabled={isFechada}
                    style={{ ...campoLinha, width: "84px", fontWeight: 600, fontSize: "15px", padding: 0, colorScheme: "dark light" }}
                  />
                  <input
                    type="text"
                    aria-label="Evento"
                    placeholder="Payroll, CPI, abertura de NY…"
                    list="eventos-conhecidos"
                    value={ev.evento}
                    onChange={(e) => atualizarEvento(idx, "evento", e.target.value)}
                    disabled={isFechada}
                    style={{ ...campoLinha, flexGrow: 1, color: "var(--tx2)" }}
                  />
                  <select
                    aria-label="Impacto"
                    value={ev.impacto}
                    onChange={(e) => atualizarEvento(idx, "impacto", e.target.value)}
                    disabled={isFechada}
                    style={{ height: "26px", padding: "0 12px", borderRadius: "999px", border: 0, fontFamily: "inherit", fontSize: "12px", fontWeight: 600, background: imp.bg, color: imp.cor, appearance: "none", textAlign: "center", cursor: isFechada ? "not-allowed" : "pointer" }}
                  >
                    <option value="ALTO">Alto</option>
                    <option value="MEDIO">Médio</option>
                    <option value="BAIXO">Baixo</option>
                  </select>
                  {botaoRemover(() => removerEvento(idx), "Remover evento")}
                </div>
              );
            })}
          </section>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <section style={CARD}>
            {cabecalhoCard("3 · Bias e contexto", `D1 ${nomeBias(sessao.bias_d1)} · H1 ${nomeBias(sessao.bias_h1)} · ${nomeCtx}`)}
            {([
              ["Bias diário (D1)", "bias_d1", BIAS],
              ["Bias intraday (H1)", "bias_h1", BIAS],
              ["Contexto", "contexto", CONTEXTOS],
            ] as const).map(([rotulo, campo, opcoes]) => (
              <div key={campo} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <span style={{ fontSize: "13px", color: "var(--tx2)" }}>{rotulo}</span>
                <div role="group" aria-label={rotulo} style={SEGMENTADO}>
                  {opcoes.map((o) => {
                    const sel = sessao[campo] === o.v;
                    return (
                      <button key={o.v} type="button" aria-pressed={sel} disabled={isFechada} onClick={() => updateField(campo, o.v as never)} style={opcaoSegmentada(sel, isFechada)}>
                        {o.l}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </section>

          <section style={CARD}>
            {cabecalhoCard("4 · Setup do dia", "Um setup por dia, escolhido agora — não no calor")}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" }}>
              {SETUPS.map((o) => {
                const sel = sessao.setup_do_dia === o.v;
                return (
                  <button
                    key={o.v}
                    type="button"
                    aria-pressed={sel}
                    disabled={isFechada}
                    onClick={() => updateField("setup_do_dia", o.v)}
                    style={{ textAlign: "left", padding: "14px 16px", borderRadius: "12px", cursor: isFechada ? "not-allowed" : "pointer", fontFamily: "inherit", display: "flex", flexDirection: "column", gap: "6px", background: sel ? "var(--acs)" : "var(--bg)", border: `1px solid ${sel ? "var(--ac)" : "var(--bd)"}`, color: "var(--tx)" }}
                  >
                    <span style={{ fontSize: "12px", fontWeight: 600, color: sel ? "var(--actx)" : "var(--tx3)" }}>{o.tag}</span>
                    <span style={{ fontSize: "14px", fontWeight: 600 }}>{o.l}</span>
                    <span style={{ fontSize: "12px", lineHeight: 1.4, color: "var(--tx2)" }}>{o.d}</span>
                  </button>
                );
              })}
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "14px", borderTop: "1px solid var(--bd)", opacity: semSetup ? 0.4 : 1 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ fontSize: "14px", fontWeight: 500 }}>Contratos declarados</span>
                <span style={{ fontSize: "12px", color: "var(--tx3)" }}>{semSetup ? "não se aplica: dia sem setup" : "tamanho fixo para o dia"}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "4px", borderRadius: "12px", border: "1px solid var(--bd)", background: "var(--bg)" }}>
                <button type="button" aria-label="Menos um contrato" disabled={isFechada || semSetup} onClick={() => updateField("contratos_declarados", contratos > 1 ? contratos - 1 : null)} style={{ width: "40px", height: "40px", borderRadius: "9px", border: 0, background: "var(--s2)", color: "var(--tx)", fontFamily: "inherit", fontSize: "18px", cursor: "pointer" }}>−</button>
                <span style={{ width: "44px", textAlign: "center", fontSize: "20px", fontWeight: 600 }}>{contratos}</span>
                <button type="button" aria-label="Mais um contrato" disabled={isFechada || semSetup} onClick={() => updateField("contratos_declarados", contratos + 1)} style={{ width: "40px", height: "40px", borderRadius: "9px", border: 0, background: "var(--s2)", color: "var(--tx)", fontFamily: "inherit", fontSize: "18px", cursor: "pointer" }}>+</button>
              </div>
            </div>
          </section>

          <section style={CARD}>
            {cabecalhoCard("6 · Estado", sessao.tilt > 2 || sessao.pressao > 2 || sessao.sono < 2 ? "Atenção ao estado antes de operar" : "Pronto para operar")}
            {([
              ["Qualidade do sono", "sono"],
              ["Tilt / ansiedade", "tilt"],
              ["Pressão por meta", "pressao"],
            ] as const).map(([rotulo, campo]) => (
              <div key={campo} style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <span style={{ width: "150px", fontSize: "13px", color: "var(--tx2)" }}>{rotulo}</span>
                {escala(campo, sessao[campo])}
                <span style={{ width: "32px", textAlign: "right", fontSize: "13px", fontWeight: 600 }}>{sessao[campo]}</span>
              </div>
            ))}
          </section>
        </div>
      </div>

      {erroFechar && (
        <div style={{ padding: "16px 20px", borderRadius: "14px", background: "var(--s1)", border: "1px solid var(--neg)", color: "var(--negtx)", fontSize: "14px" }}>
          Erro ao fechar: {erroFechar}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: "14px", padding: "18px 22px", borderRadius: "14px", background: "var(--acs)", border: "1px solid var(--bd)" }}>
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0, fill: "none", stroke: "var(--actx)", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" }}>
          <path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z" />
        </svg>
        <span style={{ flexGrow: 1, fontSize: "15px" }}>
          {isFechada
            ? `Fechada às ${new Date(sessao.fechada_em!).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })} · ${nomeSetupDia}${semSetup ? "" : ` · ${contratos} ${contratos === 1 ? "contrato" : "contratos"}`}. As escolhas estão congeladas para o pregão.`
            : bloqueado
              ? `Falta: ${requisitos.filter((r) => !r.ok).map((r) => r.l.toLowerCase()).join(", ")}. O checklist só abre com a pré-sessão fechada.`
              : "Tudo pronto. Fechar congela as escolhas e libera o checklist."}
        </span>
        {isFechada && !semSetup && (
          <Link href="/checklist" style={{ height: "40px", padding: "0 18px", borderRadius: "10px", display: "flex", alignItems: "center", fontSize: "14px", fontWeight: 600, textDecoration: "none", background: "var(--ac)", color: "var(--onac)", flexShrink: 0 }}>
            Ir para o checklist
          </Link>
        )}
      </div>

      {modalReabrir && (
        <div onClick={() => setModalReabrir(false)} style={{ position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.7)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
          <div role="dialog" aria-modal="true" aria-label="Reabrir pré-sessão" onClick={(e) => e.stopPropagation()} style={{ ...CARD, maxWidth: "480px", width: "100%" }}>
            {cabecalhoCard("Reabrir", "Reabrir a pré-sessão do dia")}
            <span style={{ fontSize: "13px", color: "var(--tx2)", lineHeight: 1.5 }}>
              Destrava a pré-sessão para edição e registra o horário e o motivo nas notas da sessão.
            </span>
            <label style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "var(--tx2)" }}>
              Motivo da reabertura
              <textarea
                rows={3}
                placeholder="Ex.: gap rompeu o BSL de 60m antes das 09:15 e invalidou a premissa."
                value={motivoReabrir}
                onChange={(e) => setMotivoReabrir(e.target.value)}
                style={{ ...INPUT, height: "auto", padding: "12px 14px", resize: "vertical", fontSize: "14px" }}
              />
            </label>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button type="button" onClick={() => setModalReabrir(false)} style={BOTAO_SECUNDARIO}>Cancelar</button>
              <button type="button" onClick={handleReabrir} disabled={reabrindo || !motivoReabrir.trim()} style={botaoPrimario(!reabrindo && Boolean(motivoReabrir.trim()))}>
                {reabrindo ? "Reabrindo…" : "Confirmar reabertura"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
