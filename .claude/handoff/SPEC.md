# SPEC — Ritual de pré-sessão: decisão fria trava o pregão

## Objetivo

Três lacunas de controle são o mesmo buraco com nomes diferentes: **decisão
tomada durante o pregão que deveria ter sido tomada antes dele.**

| Hoje | Depois |
|---|---|
| dá para operar sem ter mapeado nada | sem pré-sessão fechada, o gate não libera |
| o setup é escolhido no calor | é escolhido frio e **trava** |
| `contratos` é digitado na hora | é declarado frio e **trava** |
| nenhuma evidência do que foi visto | print do gráfico HTF obrigatório |

O banco já foi migrado (`migration_presessao.sql`, aplicado). As colunas
`setup_do_dia`, `contratos_declarados`, `screenshot_path` e `fechada_em` existem
em `copa_sessions`, com um `CHECK` que **recusa fechar pré-sessão incompleta** —
a regra não depende da tela.

Falta o app.

**Leia antes:** `Cerebro_Obsidian/Trading AI/B05 Trade System/Controle_e_Processo.md`
(os 12 controles e as lacunas) e `cockpit/app/checklist/page.tsx` (a estética e
o padrão da trilha travada).

---

## Arquivos (só estes)

1. `cockpit/lib/storage.ts` — **novo**, upload e URL assinada
2. `cockpit/lib/copa-db.ts` — sessão completa
3. `cockpit/components/copa/print-upload.tsx` — **novo**
4. `cockpit/app/pre-sessao/page.tsx` — **novo**
5. `cockpit/app/checklist/page.tsx` — gate de pré-sessão, setup e tamanho travados, print obrigatório
6. `cockpit/lib/gate.ts` — motivo de bloqueio novo
7. `cockpit/config/sidebar.ts` — entrada no menu
8. `cockpit/scripts/verify.ts` — casos novos

`git diff --stat` tem que listar exatamente estes oito.

## NÃO MEXER

Ver `.claude/skills/dupla/SKILL.md`. Em especial: `cockpit/supabase/**` (SQL já
aplicado, **não alterar**), `copa/**`, `core/**`, `cockpit/components/inst/**`
(os primitivos são para usar, não para editar), `cockpit/app/copa/**`.

**Não instalar dependência.** `MediaRecorder` e `FileReader` são do navegador;
o Supabase Storage vem no client que já existe.

**Regra de conformidade:** o sistema **armazena e exibe** a imagem. Nunca lê,
nunca analisa, nunca extrai preço dela. Parsing de gráfico seria detecção de
setup — proibido.

---

## 1. `cockpit/lib/storage.ts` (novo)

```ts
const BUCKET = "copa-prints";

/** Sobe um print. Caminho: <uid>/<YYYY-MM-DD>/<nome>. Devolve o path. */
export async function subirPrint(file: File, data: string, nome: string): Promise<string>;

/** URL assinada para exibir. O bucket é privado; URL pública não funciona. */
export async function urlDoPrint(path: string, segundos?: number): Promise<string | null>;
```

Regras:

- `uid` vem de `supabase.auth.getUser()`. Sem sessão, lança erro — **não** grava
  em pasta anônima.
- Aceita só `image/png`, `image/jpeg`, `image/webp`. Outro tipo, erro claro.
- Máximo 10 MB. Acima, erro dizendo o tamanho do arquivo.
- `upsert: true` — refazer o print do dia substitui, não acumula lixo.
- `urlDoPrint` com validade padrão de 3600 s. Erro devolve `null`; a tela mostra
  um estado de imagem indisponível, **não quebra**.

## 2. `cockpit/lib/copa-db.ts`

Acrescentar, sem alterar o que já existe:

```ts
export interface PreSessao {
  id: string | null;
  data: string;
  phase_id: string | null;
  bias_d1: "COMPRA" | "VENDA" | "INDEFINIDO";
  bias_h1: "COMPRA" | "VENDA" | "INDEFINIDO";
  contexto: "TENDENCIA" | "RANGE" | "INDEFINIDO";
  niveis: Array<{ label: string; preco: string }>;
  agenda: Array<{ evento: string; horario: string; impacto: "ALTO" | "MEDIO" | "BAIXO" }>;
  sono: number; tilt: number; pressao: number;
  setup_do_dia: "reversao_htf" | "continuidade_tendencia" | "NENHUM" | null;
  contratos_declarados: number | null;
  screenshot_path: string | null;
  fechada_em: string | null;
  notas: string;
}

export async function getPreSessaoDeHoje(): Promise<PreSessao>;
export async function salvarPreSessao(p: Partial<PreSessao>): Promise<string>;
export async function fecharPreSessao(): Promise<void>;
export async function reabrirPreSessao(motivo: string): Promise<void>;

/** O que falta para poder fechar. Vazio = pode. */
export function pendenciasDaPreSessao(p: PreSessao): string[];
```

### `pendenciasDaPreSessao` — espelha o CHECK do banco

Devolve uma linha por pendência, em português, na ordem do ritual:

| Condição | Texto |
|---|---|
| `!screenshot_path` | `"print do grafico HTF nao anexado"` |
| `bias_h1 === "INDEFINIDO"` | `"bias H1 nao definido"` |
| `contexto === "INDEFINIDO"` | `"contexto nao definido"` |
| `niveis.length < 2` | `"marque ao menos 2 niveis de liquidez ou array"` |
| `!setup_do_dia` | `"setup do dia nao escolhido"` |
| `setup_do_dia !== "NENHUM" && !contratos_declarados` | `"tamanho nao declarado"` |

**O banco tem o mesmo CHECK.** Esta função existe para dar mensagem boa, não
para substituir a trava. Se `fecharPreSessao` for chamada com pendência, o banco
recusa e o erro real aparece na tela.

### `reabrirPreSessao`

Zera `fechada_em` e **acrescenta ao `notas`** uma linha
`[REABERTA HH:MM] <motivo>`. Reabrir é permitido — mas fica registrado, porque
trocar setup no meio do pregão é exatamente o que o ritual existe para
desencorajar.

### `getOuCriarSessaoDoDia`

Passa a **não criar mais** sessão implicitamente. Se não existe sessão fechada
do dia, `registrarTrade` falha com
`"pre-sessao do dia nao foi fechada"`. Criar sessão é ato do ritual, não efeito
colateral de registrar trade.

## 3. `cockpit/components/copa/print-upload.tsx` (novo)

```tsx
<PrintUpload path={string | null} data={string} nome={string}
             onChange={(path: string) => void} obrigatorio?: boolean />
```

- Área tracejada (`InstEmpty`) quando vazio: *"Cole com Ctrl+V ou clique para escolher"*
- **Colar da área de transferência** via `onPaste`, lendo `e.clipboardData.files`.
  É o caminho principal: `Win+Shift+S` e colar são dois segundos.
- Clique abre seletor de arquivo
- Com print: miniatura clicável que abre em tamanho cheio
- Durante o upload, estado de carregando; erro em vermelho com a mensagem real

O container precisa de `tabIndex={0}` para receber o evento de colar.

## 4. `cockpit/app/pre-sessao/page.tsx` (novo)

O ritual, **na ordem**, usando os primitivos de `components/inst`.

### Cabeçalho

`InstPage` com eyebrow = data por extenso e a fase da Copa, título
*"Pré-sessão"*. À direita, `InstBadge`: `ABERTA` (tom `now`) ou `FECHADA`
(tom `ok`).

### Os passos

**1 · Print do gráfico HTF** — `PrintUpload`, obrigatório.
Ajuda: *"60m e 15m com liquidez e arrays marcados, antes das 09:00."*

**2 · Liquidez e arrays** — lista com adicionar/remover linha, cada uma com
rótulo e preço. Contador visível: *"N marcados — mínimo 2"*.

**3 · Contexto** — três botões: `TENDÊNCIA`, `RANGE`, `INDEFINIDO`.
`INDEFINIDO` é selecionável mas aparece como pendência.

**4 · Bias** — D1 e H1, cada um com `COMPRA` / `VENDA` / `INDEFINIDO`.

**5 · Setup do dia** — três botões grandes, lado a lado:
`REVERSÃO HTF` · `CONTINUIDADE DE TENDÊNCIA` · `NENHUM`.

> `NENHUM` tem o mesmo peso visual dos outros dois. Decidir de manhã que hoje
> não tem setup é decisão válida e é a mais barata que existe.

Ao escolher, mostrar a `descricao` da estratégia abaixo.

**6 · Tamanho declarado** — campo de contratos. Escondido quando o setup é
`NENHUM`. Ajuda: *"Declarado agora, frio. Trava durante o pregão."*

**7 · Agenda** — lista de eventos: evento, horário, impacto.

**8 · Estado** — sono, tilt, pressão, 0 a 5 em botões (não slider).

### Rodapé — fechar

`InstBand` com o que falta:

- pendências > 0 → tom `block`, título `PRÉ-SESSÃO INCOMPLETA`, todas as
  pendências listadas, botão **FECHAR PRÉ-SESSÃO** visível e travado
- pendências vazias → tom `ok`, título `PRONTA PARA FECHAR`, botão ativo

Depois de fechada: campos **somente leitura**, e um botão discreto
`REABRIR` que pede o motivo num prompt e chama `reabrirPreSessao`.

Salvar é automático (debounce ~800 ms) a cada mudança. Indicador discreto de
*salvo / salvando*. Perder a pré-sessão por não ter clicado em salvar às 08:55
seria o pior bug possível aqui.

## 5. `cockpit/app/checklist/page.tsx`

### 5a. Sem pré-sessão fechada, a tela não opera

Se `fechada_em` é nulo: renderizar **apenas** um `InstBand` tom `block` —
*"Pré-sessão do dia não foi fechada"* — com as pendências e um botão grande
para `/pre-sessao`. Nada de checklist, nada de formulário.

### 5b. Setup travado

O seletor de estratégia some. No lugar, uma linha:

> `SETUP DO DIA` · **Reversão HTF** · *declarado às 08:42*

Se `setup_do_dia === "NENHUM"`: `InstBand` tom `lock`, *"Hoje é dia de não
operar. Decidido na pré-sessão."* e o checklist não aparece.

### 5c. Tamanho travado

`contratos` vem preenchido com `contratos_declarados` e fica **desabilitado**.
Abaixo: *"Declarado na pré-sessão. Alterar exige reabrir."*

### 5d. Print obrigatório no trade

`PrintUpload` no formulário, acima do botão. Sem print, o gate não libera,
com o motivo `"print do trade nao anexado"`.

> No registro, não no fechamento: o print tem que ser do que você viu **antes**
> do resultado. Depois, já está contaminado pelo desfecho.

Caminho: `<uid>/<data>/trade-<timestamp>.png`, gravado em
`copa_trades.screenshot_path`.

## 6. `cockpit/lib/gate.ts`

`avaliarGate` ganha dois parâmetros opcionais ao final:
`preSessaoFechada?: boolean` e `temPrint?: boolean`.

Motivos novos, acumulados como os outros:

| Condição | Motivo |
|---|---|
| `preSessaoFechada === false` | `"pre-sessao do dia nao foi fechada"` |
| `temPrint === false` | `"print do trade nao anexado"` |

**Chamadas existentes sem esses parâmetros continuam funcionando.** Os 31 casos
atuais não podem mudar de resultado.

## 7. `cockpit/config/sidebar.ts`

No grupo **Trading**, acrescentar `Pré-Sessão` em `/pre-sessao`, **antes** de
`Checklist Pregão`. A ordem no menu é a ordem do dia.

Não mexer em mais nada.

## 8. `cockpit/scripts/verify.ts`

Manter os 31 casos. Acrescentar, para `pendenciasDaPreSessao`:

1. objeto vazio → 6 pendências, começando pelo print
2. tudo preenchido, setup `reversao_htf`, 2 contratos → **0 pendências**
3. tudo preenchido menos o print → 1 pendência, cita o print
4. tudo menos o tamanho, setup `reversao_htf` → 1 pendência, cita tamanho
5. tudo menos o tamanho, setup `NENHUM` → **0 pendências** (NENHUM dispensa tamanho)
6. 1 nível marcado → pendência cita o mínimo de 2

E para o gate:

7. tudo certo, `preSessaoFechada: false` → bloqueado citando a pré-sessão
8. tudo certo, `temPrint: false` → bloqueado citando o print
9. tudo certo, ambos verdadeiros → liberado

Total: **31 + 9 = 40 casos**.

---

## Critério de aceite

```bash
cd cockpit && npx tsc --noEmit
cd .. && npx tsx cockpit/scripts/verify.ts
cd cockpit && npm run build
cd .. && git diff --stat
```

1. `tsc` limpo
2. `verify.ts` 40 casos OK, exit 0
3. build compila, rota `/pre-sessao` gerada
4. `git diff --stat` lista exatamente os 8 arquivos

**Teste manual, obrigatório:**

1. `/checklist` sem pré-sessão → só o bloqueio, sem formulário
2. `/pre-sessao` → colar um print com Ctrl+V, preencher tudo, fechar
3. No SQL Editor:
   ```sql
   select data, setup_do_dia, contratos_declarados,
          screenshot_path is not null as tem_print, fechada_em
     from copa_sessions order by data desc limit 1;
   ```
   → `fechada_em` preenchido, `tem_print` true
4. Voltar ao `/checklist` → setup travado no declarado, contratos travado
5. Tentar registrar sem print → botão travado citando o print
6. Com print → registra, e `select screenshot_path from copa_trades order by
   created_at desc limit 1;` devolve um caminho
7. Escolher `NENHUM` na pré-sessão → `/checklist` mostra o dia de não operar

Colar a saída dos passos 3 e 6.

---

## Armadilhas desta task

**Criar sessão implicitamente.** `registrarTrade` não pode mais criar a sessão
do dia. Se puder, a pré-sessão deixa de ser obrigatória na prática e a task
inteira não serviu para nada.

**Perder a pré-sessão por falta de salvar.** Salvamento automático com debounce.
Às 08:55 ninguém lembra de clicar em salvar.

**URL pública do print.** O bucket é privado. `getPublicUrl` devolve uma URL que
não funciona, e silenciosamente — a imagem só aparece quebrada. Usar
`createSignedUrl`.

**Colar sem foco.** O `onPaste` só dispara se o elemento puder receber foco.
Sem `tabIndex`, colar não funciona e não dá erro nenhum.

**Data pelo navegador.** `America/Sao_Paulo`, sempre. Já existe
`getDataSaoPaulo` em `copa-db.ts` — usar essa, não criar outra.
