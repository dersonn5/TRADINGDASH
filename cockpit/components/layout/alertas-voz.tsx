"use client";

import * as React from "react";
import { getDataSaoPaulo, getPreSessaoDeHoje } from "@/lib/copa-db";
import { Alerta, EventoAgenda, FRASE_TESTE, alertasDoDia, alertasParaDisparar, ehDiaDePregao } from "@/lib/alertas";
import { carregarManifest, carregarVozes, escolherVoz, pararTudo, tocarPlano, vozesEmPortugues } from "@/lib/voz";
import { ManifestVoz, planoDeFala } from "@/lib/voz-clipes";
import { CARD, LBL, BOTAO_SECUNDARIO } from "@/components/v2/estilos";

// Alertas de voz do pregao (cockpit/SPEC_ALERTAS_VOZ.md). Montado na barra lateral:
// um botao de alto-falante que abre o painel, e o relogio que dispara as falas.

interface Config {
  ligado: boolean;
  volume: number;
  motor: "dora" | "navegador"; // dora = audios gravados (Kokoro); navegador = Web Speech
  voz: string | null; // voiceURI da voz do navegador (tambem cobre o que a Dora nao tem gravado)
  rotina: boolean;
  noticias: boolean;
}

const CONFIG_PADRAO: Config = { ligado: true, volume: 1, motor: "dora", voz: null, rotina: true, noticias: true };
const CHAVE_CONFIG = "alertas-voz-config";
const OPCAO_DORA = "__dora__";
const chaveFalados = (data: string) => `alertas-falados-${data}`;
// Evento disparado pela pre-sessao quando salva, fecha ou reabre: recarrega a agenda.
export const EVENTO_PRESESSAO_SALVA = "presessao-salva";

function lerLocal<T>(chave: string, padrao: T): T {
  try {
    const v = localStorage.getItem(chave);
    return v ? { ...padrao, ...JSON.parse(v) } : padrao;
  } catch {
    return padrao;
  }
}

function lerFalados(data: string): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(chaveFalados(data)) || "[]"));
  } catch {
    return new Set();
  }
}

function gravarFalados(data: string, ids: Set<string>) {
  try {
    localStorage.setItem(chaveFalados(data), JSON.stringify([...ids]));
  } catch {
    // sem localStorage: o pior caso e repetir um alerta ao recarregar
  }
}

// Relogio simulado, SO em desenvolvimento: ?relogio=09:59:50&data=2026-09-25
function relogioSimulado(): { offsetMs: number; data: string | null } {
  if (process.env.NODE_ENV === "production" || typeof window === "undefined") return { offsetMs: 0, data: null };
  const q = new URLSearchParams(window.location.search);
  const r = q.get("relogio");
  const data = q.get("data");
  if (!r || !/^\d{2}:\d{2}(:\d{2})?$/.test(r)) return { offsetMs: 0, data };
  const [h, m, s = 0] = r.split(":").map(Number);
  const agora = new Date();
  const partes = new Intl.DateTimeFormat("en-GB", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).formatToParts(agora);
  const v = (t: string) => Number(partes.find((p) => p.type === t)?.value ?? 0);
  const atual = (v("hour") % 24) * 3600 + v("minute") * 60 + v("second");
  return { offsetMs: (h * 3600 + m * 60 + s - atual) * 1000, data };
}

const svg = (d: React.ReactNode) => (
  <svg width={16} height={16} viewBox="0 0 24 24" aria-hidden="true" style={{ fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round" }}>
    {d}
  </svg>
);

export function AlertasVoz() {
  const [config, setConfig] = React.useState<Config>(CONFIG_PADRAO);
  const [aberto, setAberto] = React.useState(false);
  const [vozes, setVozes] = React.useState<SpeechSynthesisVoice[]>([]);
  const [manifest, setManifest] = React.useState<ManifestVoz | null>(null);
  const [desbloqueado, setDesbloqueado] = React.useState(false);
  const [agenda, setAgenda] = React.useState<EventoAgenda[]>([]);
  const [fechada, setFechada] = React.useState(false);
  const [falados, setFalados] = React.useState<Set<string>>(new Set());
  const [agora, setAgora] = React.useState(() => new Date());
  const simulado = React.useRef({ offsetMs: 0, data: null as string | null });
  const painelRef = React.useRef<HTMLDivElement | null>(null);

  // Configuracao salva, vozes e relogio simulado
  React.useEffect(() => {
    setConfig(lerLocal(CHAVE_CONFIG, CONFIG_PADRAO));
    simulado.current = relogioSimulado();
    // Em desenvolvimento, o relogio simulado vale como pagina liberada (teste sem clique)
    if (simulado.current.offsetMs !== 0) setDesbloqueado(true);
    carregarVozes().then(setVozes);
    carregarManifest().then(setManifest);
  }, []);

  const salvarConfig = (parcial: Partial<Config>) => {
    setConfig((c) => {
      const nova = { ...c, ...parcial };
      try {
        localStorage.setItem(CHAVE_CONFIG, JSON.stringify(nova));
      } catch {
        // sem localStorage: vale so nesta aba
      }
      if (!nova.ligado) pararTudo();
      return nova;
    });
  };

  // O navegador so deixa falar depois de um clique ou tecla na pagina
  React.useEffect(() => {
    const liberar = () => setDesbloqueado(true);
    window.addEventListener("pointerdown", liberar, { once: true });
    window.addEventListener("keydown", liberar, { once: true });
    return () => {
      window.removeEventListener("pointerdown", liberar);
      window.removeEventListener("keydown", liberar);
    };
  }, []);

  // Agenda e estado da pre-sessao: ao montar, a cada 5 min e quando a pre-sessao salva
  React.useEffect(() => {
    let vivo = true;
    const carregar = () =>
      getPreSessaoDeHoje()
        .then((p) => {
          if (!vivo) return;
          setAgenda(p.agenda ?? []);
          setFechada(Boolean(p.fechada_em));
        })
        .catch(() => {
          // sem pre-sessao legivel: segue so com a rotina
        });
    carregar();
    const t = setInterval(carregar, 5 * 60 * 1000);
    window.addEventListener(EVENTO_PRESESSAO_SALVA, carregar);
    return () => {
      vivo = false;
      clearInterval(t);
      window.removeEventListener(EVENTO_PRESESSAO_SALVA, carregar);
    };
  }, []);

  // Relogio de 1 s
  React.useEffect(() => {
    const t = setInterval(() => setAgora(new Date(Date.now() + simulado.current.offsetMs)), 1000);
    return () => clearInterval(t);
  }, []);

  const hoje = simulado.current.data ?? getDataSaoPaulo(agora);
  React.useEffect(() => setFalados(lerFalados(hoje)), [hoje]);

  const alertas = React.useMemo(() => alertasDoDia(hoje, agenda, fechada), [hoje, agenda, fechada]);
  const ativos = React.useMemo(
    () => alertas.filter((a) => (a.grupo === "rotina" ? config.rotina : config.noticias)),
    [alertas, config.rotina, config.noticias]
  );
  const voz = React.useMemo(() => escolherVoz(vozes, config.voz), [vozes, config.voz]);
  const dora = config.motor === "dora" && manifest !== null;
  const falarSegmentos = React.useCallback(
    (segmentos: string[]) => tocarPlano(planoDeFala(segmentos, dora ? manifest : null), { volume: config.volume, vozNavegador: voz }),
    [dora, manifest, config.volume, voz]
  );

  // Disparo
  React.useEffect(() => {
    if (!config.ligado || !desbloqueado) return;
    const disparar = alertasParaDisparar(ativos, agora, falados);
    if (!disparar.length) return;
    const novos = new Set(falados);
    for (const a of disparar) {
      falarSegmentos(a.segmentos);
      novos.add(a.id);
      if (process.env.NODE_ENV !== "production") console.info(`[voz] ${a.hora} ${a.texto}`);
    }
    setFalados(novos);
    gravarFalados(hoje, novos);
  }, [agora, ativos, falados, config.ligado, desbloqueado, falarSegmentos, hoje]);

  // Fecha o painel ao clicar fora
  React.useEffect(() => {
    if (!aberto) return;
    const fora = (e: MouseEvent) => {
      if (painelRef.current && !painelRef.current.contains(e.target as Node)) setAberto(false);
    };
    document.addEventListener("mousedown", fora);
    return () => document.removeEventListener("mousedown", fora);
  }, [aberto]);

  const ouvir = (a: Alerta | string) => {
    pararTudo();
    falarSegmentos(typeof a === "string" ? [a] : a.segmentos);
  };
  const pendenteClique = config.ligado && !desbloqueado;
  const vozesBR = vozesEmPortugues(vozes);

  const botaoIcone: React.CSSProperties = {
    width: "36px", height: "36px", borderRadius: "10px", border: `1px solid ${config.ligado ? "var(--ac)" : "var(--bd)"}`,
    background: config.ligado ? "var(--acs)" : "transparent", color: config.ligado ? "var(--actx)" : "var(--tx2)",
    display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", position: "relative",
  };
  const linhaCheck: React.CSSProperties = { display: "flex", alignItems: "center", gap: "10px", fontSize: "13px", cursor: "pointer" };

  return (
    <div ref={painelRef} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        aria-label="Alertas de voz"
        aria-expanded={aberto}
        title={config.ligado ? "Alertas de voz ligados" : "Alertas de voz desligados"}
        style={botaoIcone}
      >
        {config.ligado
          ? svg(<><path d="M11 5L6 9H3v6h3l5 4z" /><path d="M15.5 8.5a5 5 0 0 1 0 7" /><path d="M18.5 5.5a9 9 0 0 1 0 13" /></>)
          : svg(<><path d="M11 5L6 9H3v6h3l5 4z" /><path d="M22 9l-6 6M16 9l6 6" /></>)}
        {pendenteClique && (
          <span aria-hidden="true" style={{ position: "absolute", top: "-3px", right: "-3px", width: "9px", height: "9px", borderRadius: "50%", background: "var(--ac)", border: "2px solid var(--bg)" }} />
        )}
      </button>

      {aberto && (
        <div role="dialog" aria-label="Alertas de voz" style={{ position: "fixed", left: "16px", bottom: "76px", width: "340px", maxHeight: "72vh", overflowY: "auto", zIndex: 50, borderRadius: "16px", background: "var(--s1)", border: "1px solid var(--bd)", boxShadow: "0 16px 40px rgba(0,0,0,0.35)" }}>
          <div style={{ ...CARD, border: 0, background: "transparent" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <span style={LBL}>Alertas de voz</span>
              <span style={{ fontSize: "15px", fontWeight: 600 }}>{config.ligado ? "Ligados" : "Desligados"}</span>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={config.ligado}
              aria-label="Ligar alertas de voz"
              onClick={() => salvarConfig({ ligado: !config.ligado })}
              style={{ width: "46px", height: "26px", borderRadius: "999px", border: 0, padding: "3px", cursor: "pointer", background: config.ligado ? "var(--ac)" : "var(--s2)", display: "flex", justifyContent: config.ligado ? "flex-end" : "flex-start" }}
            >
              <span style={{ width: "20px", height: "20px", borderRadius: "50%", background: config.ligado ? "var(--onac)" : "var(--tx3)" }} />
            </button>
          </div>

          {pendenteClique && (
            <span style={{ fontSize: "12px", color: "var(--actx)", lineHeight: 1.5 }}>
              O navegador só libera a voz depois de um clique. Clique em qualquer lugar da página.
            </span>
          )}

          <label style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "13px", color: "var(--tx2)" }}>
            Voz
            {vozesBR.length || manifest ? (
              <select
                value={dora ? OPCAO_DORA : voz?.voiceURI ?? ""}
                onChange={(e) =>
                  salvarConfig(e.target.value === OPCAO_DORA ? { motor: "dora" } : { motor: "navegador", voz: e.target.value })
                }
                style={{ height: "40px", borderRadius: "10px", border: "1px solid var(--bd)", background: "var(--bg)", color: "var(--tx)", fontFamily: "inherit", fontSize: "13px", padding: "0 10px" }}
              >
                {manifest && <option value={OPCAO_DORA}>Dora (Kokoro)</option>}
                {vozesBR.map((v) => (
                  <option key={v.voiceURI} value={v.voiceURI}>{v.name}</option>
                ))}
              </select>
            ) : (
              <span style={{ fontSize: "12px", color: "var(--negtx)" }}>Este navegador não tem voz em português. No Edge, a voz Francisca é a mais natural.</span>
            )}
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "13px", color: "var(--tx2)" }}>
            Volume · {Math.round(config.volume * 100)}%
            <input type="range" min={0} max={1} step={0.05} value={config.volume} onChange={(e) => salvarConfig({ volume: Number(e.target.value) })} style={{ accentColor: "var(--ac)" }} />
          </label>

          <div style={{ display: "flex", gap: "18px" }}>
            <label style={linhaCheck}>
              <input type="checkbox" checked={config.rotina} onChange={() => salvarConfig({ rotina: !config.rotina })} style={{ width: "16px", height: "16px", accentColor: "var(--ac)" }} />
              Rotina do pregão
            </label>
            <label style={linhaCheck}>
              <input type="checkbox" checked={config.noticias} onChange={() => salvarConfig({ noticias: !config.noticias })} style={{ width: "16px", height: "16px", accentColor: "var(--ac)" }} />
              Notícias
            </label>
          </div>

          <button type="button" onClick={() => ouvir(FRASE_TESTE)} style={{ ...BOTAO_SECUNDARIO, width: "100%" }}>
            Testar a voz
          </button>

          <div style={{ display: "flex", flexDirection: "column", gap: "4px", paddingTop: "12px", borderTop: "1px solid var(--bd)" }}>
            <span style={{ fontSize: "12px", color: "var(--tx3)", paddingBottom: "4px" }}>Hoje</span>
            {!ehDiaDePregao(hoje) ? (
              <span style={{ fontSize: "13px", color: "var(--tx2)" }}>Hoje não tem pregão.</span>
            ) : (
              alertas.map((a) => {
                const ja = falados.has(a.id);
                const ativo = a.grupo === "rotina" ? config.rotina : config.noticias;
                return (
                  <div key={a.id} style={{ display: "flex", alignItems: "flex-start", gap: "10px", padding: "8px 0", borderTop: "1px solid var(--bd)", opacity: ativo ? 1 : 0.45 }}>
                    <span style={{ width: "42px", flexShrink: 0, fontSize: "13px", fontWeight: 600, color: ja ? "var(--tx3)" : "var(--tx)" }}>{a.hora}</span>
                    <span style={{ flexGrow: 1, fontSize: "12px", lineHeight: 1.45, color: ja ? "var(--tx3)" : "var(--tx2)" }}>{a.texto}</span>
                    <button type="button" onClick={() => ouvir(a)} aria-label={`Ouvir o alerta das ${a.hora}`} style={{ width: "28px", height: "28px", flexShrink: 0, borderRadius: "8px", border: "1px solid var(--bd)", background: "transparent", color: "var(--tx2)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {svg(<path d="M8 5v14l11-7z" />)}
                    </button>
                  </div>
                );
              })
            )}
          </div>
          </div>
        </div>
      )}
    </div>
  );
}
