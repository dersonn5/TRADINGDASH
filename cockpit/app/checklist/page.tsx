"use client";

import { useEffect, useState, useMemo } from "react";
import {
  fetchTodayChecklist,
  saveChecklist,
  LiveChecklist,
} from "@/lib/trading-db";
import {
  avaliarGate,
  passosCumpridos,
  estadoDosPassos,
  alternarPasso,
  GateResult,
  ItemAvaliado,
} from "@/lib/gate";

export default function ChecklistPage() {
  const [checklist, setChecklist] = useState<LiveChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [now, setNow] = useState<Date>(() => new Date());

  // Atualizar o relógio a cada 30 segundos e limpar no unmount
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    loadChecklist();
  }, []);

  async function loadChecklist() {
    setLoading(true);
    const data = await fetchTodayChecklist();
    setChecklist(data);
    setLoading(false);
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

  // Avaliação do Gate em tempo real com regras de horário e confluência
  const gate: GateResult = useMemo(() => {
    if (!checklist) {
      return {
        liberado: false,
        janela: "FORA",
        score: 0,
        scoreMinimo: 65,
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
      now
    );
  }, [checklist, now]);

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

    // Recalcular Score
    const nextGate = avaliarGate(
      updatedItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now
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

    // Recalcular Score
    const nextGate = avaliarGate(
      updatedItems.map((i) => ({
        id: i.id,
        tipo: i.tipo,
        label: i.label,
        checked: i.checked,
        peso: i.weight,
      })),
      checklist.bias,
      now
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
    const nextGate = avaliarGate(itensAvaliados, newBias, now);
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
      now
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
      return ["sequência completa · risco definido · janela nobre"];
    }
    return [];
  }, [gate.motivos, gate.liberado]);

  if (loading || !checklist) {
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

  const restam = 7 - feitos;
  const dica =
    feitos === 7
      ? "Sequência completa. O trade agora termina no alvo ou no stop."
      : `Só o passo ${feitos + 1} está clicável. Faltam ${restam} para a sequência fechar.`;

  return (
    <div
      className="-m-4 md:-m-6 flex flex-1 flex-col min-h-[calc(100vh-4rem)]"
      style={{ background: "var(--inst-bg)", color: "var(--inst-text)" }}
    >
      {/* ============ BARRA DE ESTADO ============ */}
      <div
        style={{
          display: "flex",
          alignItems: "stretch",
          borderBottom: "1px solid var(--inst-line-2)",
          background: "var(--inst-panel)",
          flexWrap: "wrap",
        }}
      >
        <div
          style={{
            padding: "14px 24px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            minWidth: "190px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            PREGÃO
          </span>
          <span className="mono tabular" style={{ fontSize: "20px", fontWeight: 600, letterSpacing: "-0.01em" }}>
            {spTimeStr}
          </span>
        </div>

        <div
          style={{
            padding: "14px 24px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            flexGrow: 1,
            minWidth: "260px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            JANELA
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "9px", flexWrap: "wrap" }}>
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
              style={{ fontSize: "13px", fontWeight: 600, color: janelaInfo.cor, letterSpacing: "0.02em" }}
            >
              {janelaInfo.texto}
            </span>
            <span style={{ fontSize: "12px", color: "var(--inst-faint)" }}>
              {janelaInfo.nota}
            </span>
          </div>
        </div>

        <div
          style={{
            padding: "14px 24px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            minWidth: "150px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            PERDA DIA
          </span>
          <span className="mono tabular" style={{ fontSize: "15px", fontWeight: 500, color: "var(--inst-dim)" }}>
            —
          </span>
        </div>

        <div
          style={{
            padding: "14px 24px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            minWidth: "140px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            TRADES
          </span>
          <span className="mono tabular" style={{ fontSize: "15px", fontWeight: 500, color: "var(--inst-dim)" }}>
            —
          </span>
        </div>

        <div
          style={{
            padding: "14px 24px",
            borderRight: "1px solid var(--inst-line-2)",
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            minWidth: "150px",
          }}
        >
          <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.14em", color: "var(--inst-faint)" }}>
            MULLIGAN
          </span>
          <span className="mono tabular" style={{ fontSize: "13px", fontWeight: 600, color: "var(--inst-dim)" }}>
            —
          </span>
        </div>

        <div
          style={{
            padding: "12px 24px",
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

      <div
        className="flex flex-col lg:flex-row flex-grow items-stretch"
        style={{ minHeight: 0 }}
      >
        {/* ============ TRILHA (Coluna Principal) ============ */}
        <div
          className="flex-grow flex flex-col"
          style={{
            padding: "26px 28px 32px 28px",
            gap: "18px",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span className="mono tabular" style={{ fontSize: "10px", letterSpacing: "0.16em", color: "var(--inst-faint)" }}>
                  PLAYBOOK ANDERSON · {checklist.market || "WIN"}
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
                          background: active ? (b === "NAO_OPERAR" ? "var(--inst-block-bg)" : "var(--inst-now-bg)") : "transparent",
                          color: active ? (b === "NAO_OPERAR" ? "var(--inst-block)" : "var(--inst-now)") : "var(--inst-faint)",
                          border: `1px solid ${active ? (b === "NAO_OPERAR" ? "var(--inst-block-line)" : "var(--inst-now-line)") : "var(--inst-line-2)"}`,
                          cursor: "pointer",
                        }}
                      >
                        {b === "NAO_OPERAR" ? "NÃO OPERAR" : b}
                      </button>
                    );
                  })}
                </div>
              </div>
              <h1 style={{ margin: 0, fontSize: "21px", fontWeight: 600, letterSpacing: "-0.015em" }}>
                Trilha do setup
              </h1>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
              <span
                className="mono tabular"
                style={{
                  fontSize: "30px",
                  fontWeight: 600,
                  color: feitos === 7 ? "var(--inst-ok)" : "var(--inst-now)",
                  lineHeight: 1,
                }}
              >
                {feitos}
              </span>
              <span className="mono tabular" style={{ fontSize: "15px", color: "var(--inst-faint)" }}>
                / 7
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
                    <span style={{ fontSize: "14px", fontWeight: 500, color: corTexto, lineHeight: 1.35 }}>
                      {k.label}
                    </span>
                    {k.ajuda && (
                      <span style={{ fontSize: "12px", color: corAjuda, lineHeight: 1.45, maxWidth: "62ch" }}>
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

        {/* ============ CONFLUÊNCIA + GATE (Painel Lateral) ============ */}
        <div
          className="w-full lg:w-[452px] shrink-0 border-t lg:border-t-0 lg:border-l flex flex-col"
          style={{
            borderColor: "var(--inst-line-2)",
            background: "var(--inst-panel)",
          }}
        >
          {/* Cabeçalho de Score */}
          <div
            style={{
              padding: "22px 24px 18px 24px",
              borderBottom: "1px solid var(--inst-line-2)",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
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
                  left: `${gate.janela === "FORA" ? 100 : (gate.scoreMinimo === Number.POSITIVE_INFINITY ? 100 : Math.min(100, gate.scoreMinimo))}%`,
                  width: "1px",
                  background: "var(--inst-dim)",
                }}
              />
            </div>

            <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-faint)", letterSpacing: "0.06em" }}>
              {gate.janela === "PRIME"
                ? "MÍNIMO 65 NA JANELA NOBRE"
                : gate.janela === "VALIDA"
                ? "MÍNIMO 80 FORA DA JANELA NOBRE"
                : "BLOQUEADO PELO HORÁRIO"}
            </span>
          </div>

          {/* Lista compacta de Itens PONTO */}
          <div
            style={{
              flexGrow: 1,
              padding: "8px 12px",
              display: "flex",
              flexDirection: "column",
              gap: "1px",
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
                    padding: "9px 12px",
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
                        fontSize: "12.5px",
                        color: on ? "var(--inst-text)" : "#6E787F",
                        lineHeight: 1.35,
                      }}
                    >
                      {p.label}
                    </span>
                    <span className="mono tabular" style={{ fontSize: "9px", letterSpacing: "0.1em", color: "var(--inst-ghost)" }}>
                      ESTIMADO
                    </span>
                  </div>
                  <span
                    className="mono tabular"
                    style={{
                      fontSize: "12px",
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

          {/* Bloco do GATE */}
          <div
            style={{
              borderTop: `1px solid ${gate.liberado ? "var(--inst-ok-line)" : "var(--inst-block-line)"}`,
              background: gate.liberado ? "#0D1512" : "var(--inst-block-bg)",
              padding: "18px 24px 22px 24px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
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
                  fontSize: "15px",
                  fontWeight: 600,
                  letterSpacing: "0.06em",
                  color: gate.liberado ? "var(--inst-ok)" : "var(--inst-block)",
                }}
              >
                {gate.liberado ? "LIBERADO" : "BLOQUEADO"}
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
              {gateMotivosExibidos.map((texto, idx) => (
                <div key={idx} style={{ display: "grid", gridTemplateColumns: "12px 1fr", gap: "9px", alignItems: "start" }}>
                  <span
                    className="mono tabular"
                    style={{
                      fontSize: "11px",
                      color: gate.liberado ? "var(--inst-ok)" : "var(--inst-block)",
                      lineHeight: 1.5,
                    }}
                  >
                    —
                  </span>
                  <span style={{ fontSize: "12px", color: "var(--inst-text-2)", lineHeight: 1.5 }}>
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
                  padding: "8px 12px",
                  background: "var(--inst-now-bg)",
                  border: "1px solid var(--inst-now-line)",
                  borderRadius: "3px",
                }}
              >
                {gate.avisos.map((aviso, idx) => (
                  <div key={idx} style={{ display: "grid", gridTemplateColumns: "12px 1fr", gap: "8px", alignItems: "start" }}>
                    <span className="mono tabular" style={{ fontSize: "11px", color: "var(--inst-now)", lineHeight: 1.5 }}>
                      !
                    </span>
                    <span style={{ fontSize: "11px", color: "var(--inst-now)", lineHeight: 1.5 }}>
                      {aviso}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Botão ABRIR ORDEM: sempre visível */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "15px",
                border: `1px solid ${gate.liberado ? "var(--inst-ok)" : "#2A3138"}`,
                background: gate.liberado ? "var(--inst-ok)" : "transparent",
                borderRadius: "3px",
                marginTop: "2px",
                cursor: gate.liberado ? "pointer" : "not-allowed",
              }}
            >
              <span
                className="mono tabular"
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  color: gate.liberado ? "#08150F" : "var(--inst-ghost)",
                }}
              >
                ABRIR ORDEM
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
