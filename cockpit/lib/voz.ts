/**
 * Voz dos alertas: audios gravados da Dora (SPEC_VOZ_KOKORO.md) e, para o que nao tem
 * audio, a voz do navegador (Web Speech API, SPEC_ALERTAS_VOZ.md §2).
 * escolherVoz e pura (testada); o resto so roda no navegador.
 */
import type { ManifestVoz, PassoFala } from "./voz-clipes";

export interface VozInfo {
  name: string;
  lang: string;
  voiceURI: string;
}

// Vozes femininas em pt-BR, da mais natural para a menos:
// Francisca/Thalita = neurais do Edge; Maria = Windows; Google = Chrome.
const PREFERENCIA = ["francisca", "thalita", "maria", "google português do brasil", "luciana"];

function ptBR(v: VozInfo) {
  return v.lang.toLowerCase().replace("_", "-") === "pt-br";
}

/** A voz salva pelo operador, se ainda existir; senao a melhor feminina pt-BR; senao qualquer pt-BR; senao null. */
export function escolherVoz<T extends VozInfo>(vozes: T[], preferidaURI?: string | null): T | null {
  if (preferidaURI) {
    const salva = vozes.find((v) => v.voiceURI === preferidaURI);
    if (salva) return salva;
  }
  const br = vozes.filter(ptBR);
  for (const nome of PREFERENCIA) {
    const v = br.find((x) => x.name.toLowerCase().includes(nome));
    if (v) return v;
  }
  return br[0] ?? null;
}

export function vozesEmPortugues<T extends VozInfo>(vozes: T[]): T[] {
  return vozes.filter(ptBR);
}

/** Lista de vozes do navegador. Chega vazia no primeiro instante: espera o voiceschanged. */
export function carregarVozes(): Promise<SpeechSynthesisVoice[]> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return Promise.resolve([]);
  const agora = window.speechSynthesis.getVoices();
  if (agora.length) return Promise.resolve(agora);
  return new Promise((resolve) => {
    const pronto = () => resolve(window.speechSynthesis.getVoices());
    window.speechSynthesis.addEventListener("voiceschanged", pronto, { once: true });
    setTimeout(pronto, 2000);
  });
}

/** Enfileira uma fala. O speechSynthesis ja fala uma de cada vez, na ordem. */
export function falar(texto: string, opcoes: { voz: SpeechSynthesisVoice | null; volume: number }) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(texto);
  u.lang = "pt-BR";
  if (opcoes.voz) u.voice = opcoes.voz;
  u.volume = Math.min(1, Math.max(0, opcoes.volume));
  u.rate = 1;
  window.speechSynthesis.speak(u);
}

let manifestPromessa: Promise<ManifestVoz | null> | null = null;

/** manifest.json dos audios da Dora, carregado uma vez. Falhou: tudo cai na voz do navegador. */
export function carregarManifest(): Promise<ManifestVoz | null> {
  if (!manifestPromessa) {
    manifestPromessa = fetch("/voz/manifest.json")
      .then((r) => (r.ok ? (r.json() as Promise<ManifestVoz>) : null))
      .catch(() => null);
  }
  return manifestPromessa;
}

// Fila unica: um alerta termina antes do proximo comecar. pararTudo troca a geracao e
// o que ja estava na fila e descartado.
let fila: Promise<void> = Promise.resolve();
let geracao = 0;
let audioAtual: HTMLAudioElement | null = null;
const PAUSA_MS = 120;

function tocarArquivo(url: string, volume: number): Promise<void> {
  return new Promise((resolve) => {
    const audio = new Audio(url);
    audio.volume = Math.min(1, Math.max(0, volume));
    audioAtual = audio;
    const fim = () => {
      if (audioAtual === audio) audioAtual = null;
      resolve();
    };
    audio.onended = fim;
    audio.onerror = fim;
    audio.onpause = fim;
    audio.play().catch(fim);
  });
}

function falarEsperando(texto: string, voz: SpeechSynthesisVoice | null, volume: number): Promise<void> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return Promise.resolve();
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = "pt-BR";
    if (voz) u.voice = voz;
    u.volume = Math.min(1, Math.max(0, volume));
    u.onend = () => resolve();
    u.onerror = () => resolve();
    window.speechSynthesis.speak(u);
  });
}

/** Enfileira um alerta: arquivos da Dora e, no que faltar, a voz do navegador. */
export function tocarPlano(plano: PassoFala[], opcoes: { volume: number; vozNavegador: SpeechSynthesisVoice | null }) {
  const minha = geracao;
  fila = fila.then(async () => {
    for (let i = 0; i < plano.length; i++) {
      if (minha !== geracao) return;
      const passo = plano[i];
      if (passo.tipo === "arquivo") await tocarArquivo(passo.url, opcoes.volume);
      else await falarEsperando(passo.texto, opcoes.vozNavegador, opcoes.volume);
      if (i < plano.length - 1) await new Promise((r) => setTimeout(r, PAUSA_MS));
    }
    await new Promise((r) => setTimeout(r, PAUSA_MS * 3));
  });
}

export function pararTudo() {
  geracao++;
  audioAtual?.pause();
  audioAtual = null;
  if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
}
