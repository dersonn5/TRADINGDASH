# Spec: Sino de Abertura do Pregão Viva Voz

## 1. Objetivo
Adicionar o som clássico de sino de pregão viva voz (badaladas ressonantes de sineta de bronze) para alertar de forma imersiva e inconfundível o início das sessões de negociação:
1. Às **09:00** (abertura do mini-índice / mercado futuro WIN);
2. Às **10:00** (abertura do mercado à vista de ações e início da janela operacional de entradas).
O sino toca as badaladas anunciando a abertura e, em seguida, a voz Dora prossegue com a fala de instrução e resumo do pregão. O operador também pode testar o som, regular o volume e ligar/desligar o sino no painel de alertas.

## 2. Arquivos (só estes)
- `cockpit/lib/alertas.ts` (campo opcional `som?: "sino"` na interface `Alerta` e marcação nos alertas de rotina das 09:00 e 10:00)
- `cockpit/lib/voz.ts` (função exportada `tocarSino(volume?: number): Promise<void>`)
- `cockpit/components/layout/alertas-voz.tsx` (integração do sino antes das falas de 09:00/10:00, controle no painel com checkbox, botão "Testar sino" e ícone indicador na lista)
- `cockpit/scripts/verify.ts` (testes automatizados de validação do sino, integridade dos alertas e existência do áudio)

## 3. NÃO MEXER — com o motivo de cada item
- `cockpit/public/voz/manifest.json` e arquivos OGG de voz da Dora: Contrato de áudios sintetizados pelo Kokoro. O sino é um efeito sonoro (`/sons/sino-pregao.ogg`), não uma palavra falada, e não deve entrar no manifest de fala para não quebrar a cobertura do teste de frases.
- `cockpit/lib/voz-clipes.ts`: Contrato de resolução de segmentos de texto para clipes de voz.
- `cockpit/lib/visao-geral.ts` e `cockpit/lib/copa-db.ts`: Regras de negócio, PnL e persistência no banco.
- Gate, Checklist e Pré-sessão: Regras de disciplina operacional intocadas.

## 4. Contratos

### `cockpit/lib/alertas.ts`
```ts
export type SomAlerta = "sino";

export interface Alerta {
  id: string;
  hora: string; // "HH:MM" em America/Sao_Paulo
  texto: string;
  segmentos: string[];
  grupo: GrupoAlerta;
  ordem: number;
  som?: SomAlerta; // Quando presente, aciona o efeito sonoro antes das falas
}
```
Nos alertas de rotina de `alertasDoDia`:
- `09:00` possui `som: "sino"`
- `10:00` possui `som: "sino"`
- Demais alertas NÃO possuem `som`.
- `segmentos` das 09:00 e 10:00 permanecem inalterados.

### `cockpit/lib/voz.ts`
```ts
export function tocarSino(volume?: number): Promise<void>;
```
Toca o arquivo `/sons/sino-pregao.ogg` respeitando o volume atual e resolvendo a Promise quando o áudio termina (ou em caso de erro), integrando com o encadeamento e cancelamento do `pararTudo()`.

### `cockpit/components/layout/alertas-voz.tsx`
Configuração salva no `localStorage`:
```ts
interface Config {
  ligado: boolean;
  volume: number;
  motor: "dora" | "navegador";
  voz: string | null;
  rotina: boolean;
  noticias: boolean;
  sino: boolean; // default: true
}
```
Comportamento no disparo e no botão "ouvir":
- Se `alerta.som === "sino"` e `config.sino !== false`: executa `tocarSino(config.volume)` antes da fala dos segmentos.
- Painel contém controle `[x] Sino de abertura (09:00 e 10:00)` e botão `🔔 Testar sino`.

## 5. Critério de aceite — mecânico, não interpretável
1. `node node_modules/typescript/lib/tsc.js --noEmit` → exit 0, nenhum erro de tipos.
2. `npx -y tsx scripts/verify.ts` → exit 0, todos os testes (incluindo o novo teste do sino) passando.
3. `fs.existsSync("cockpit/public/sons/sino-pregao.ogg") === true`.
4. Os testes de cobertura de frases do Kokoro e segmentos das 09:00 continuam 100% verdes.
5. `git diff -U0 | grep "^-.*//"` → vazio, nenhum comentário removido.
6. `git diff --stat` → restrito aos 4 arquivos autorizados da lista.

## 6. Armadilhas já pagas nesta área
- **Nunca colocar "sino" em `a.segmentos`**: O script `verify.ts` varre todos os segmentos de `alertasDoDia` contra `public/voz/manifest.json`. Se o sino estivesse nos segmentos, o teste de cobertura de fala falharia por ausência de clipe de voz.
- **Formato de áudio**: OGG Vorbis é padrão web com baixa latência e compatibilidade no Edge e Chrome. O arquivo gerado possui fade-out no fim para evitar cliques no driver de som.
- **Cancelamento**: Ao chamar `pararTudo()` (ex: desligar alertas no meio do toque), o sino deve parar imediatamente junto com qualquer fala.
