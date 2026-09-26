/**
 * Audios pre-gravados da voz Dora (Kokoro pf_dora). Logica pura — testada em verify.ts.
 * Spec: cockpit/SPEC_VOZ_KOKORO.md. Os arquivos ficam em public/voz e o manifest.json
 * diz qual texto tem audio. Gerados por tools/voz/gerar.py.
 */

export interface ManifestVoz {
  voz: string;
  velocidade: number;
  clipes: Record<string, string>; // texto normalizado -> arquivo em /voz
}

export type PassoFala = { tipo: "arquivo"; url: string } | { tipo: "navegador"; texto: string };

/** Mesma normalizacao do gerar.py: sem espacos nas pontas, espacos repetidos viram um. */
export function normalizarFala(texto: string): string {
  return texto.trim().replace(/\s+/g, " ");
}

/** Cada segmento vira o audio gravado, se existir; senao a voz do navegador fala aquele pedaco. */
export function planoDeFala(segmentos: string[], manifest: ManifestVoz | null): PassoFala[] {
  return segmentos
    .map(normalizarFala)
    .filter(Boolean)
    .map((texto) => {
      const arquivo = manifest?.clipes[texto];
      return arquivo ? { tipo: "arquivo" as const, url: `/voz/${arquivo}` } : { tipo: "navegador" as const, texto };
    });
}
