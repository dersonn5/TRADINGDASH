/**
 * Voz do navegador (Web Speech API). Fonte: cockpit/SPEC_ALERTAS_VOZ.md §2.
 * escolherVoz e pura (testada); falar/pararTudo so rodam no navegador.
 */

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

export function pararTudo() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
}
