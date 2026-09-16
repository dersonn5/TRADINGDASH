# SPEC — Unificar o front na estética instrumento

## Objetivo

A tela `/checklist` foi redesenhada na direção **instrumento de precisão**:
escuro, denso, tipografia técnica, números tabulares, e cor só onde significa
estado. Todas as outras 10 páginas continuam com a aparência antiga do shadcn.

O operador: *"o front do menu Checklist Pregão está diferente de todos os
outros, precisamos deixar todos com a mesma cara."*

Esta task faz isso. Mas **não restilizando página por página** — isso é o que
produziu a divergência atual e a produziria de novo em duas semanas.

**Primeiro extrai os primitivos visuais do `/checklist` em componentes. Depois
as páginas consomem os componentes.** A partir daí, mudar a estética é mudar um
arquivo, não onze.

**Leia `cockpit/app/checklist/page.tsx` antes de escrever qualquer linha.** Ela é
a referência viva: os valores saem de lá, não de invenção.

---

## Arquivos (só estes)

**Fase 1 — primitivos**
1. `cockpit/components/inst/index.tsx` — **novo**, os componentes
2. `cockpit/app/globals.css` — classes utilitárias que faltarem

**Fase 2 — páginas, nesta ordem**
3. `cockpit/app/page.tsx` (113 linhas)
4. `cockpit/app/copa/fase/page.tsx` (64)
5. `cockpit/app/copa/page.tsx` (312)
6. `cockpit/app/copa/trades/page.tsx` (353)
7. `cockpit/app/copa/stats/page.tsx` (429)
8. `cockpit/app/copa/estrategias/page.tsx` (226)
9. `cockpit/app/copa/config/page.tsx` (380)
10. `cockpit/app/estrategias/page.tsx` (230)
11. `cockpit/app/trades/page.tsx` (506)
12. `cockpit/app/cerebro/page.tsx` (357)

**Fase 3 — menu**
13. `cockpit/config/sidebar.ts`

`git diff --stat` tem que listar exatamente estes treze.

> A ordem importa. Se faltar tempo, **pare no fim de uma página inteira** e
> reporte onde parou. Página pela metade é pior que página não tocada.

## NÃO MEXER

Ver `.claude/skills/dupla/SKILL.md`. Nesta task, em especial:
`cockpit/app/checklist/page.tsx` (**é a referência, leitura apenas**),
`cockpit/app/login/page.tsx` (já está na estética),
`cockpit/lib/**`, `cockpit/data/**`, `cockpit/supabase/**`, `copa/**`, `core/**`.

**Esta task é só apresentação.** Nenhuma chamada de dados muda, nenhuma lógica
muda, nenhum contrato muda. Se você precisou editar algo em `lib/`, leu errado.

**Não instalar dependência.**

---

## 1. `cockpit/components/inst/index.tsx` — os primitivos

Componentes client-safe, sem estado, sem fetch. Estilo inline com os tokens
`--inst-*` que já existem em `globals.css`.

Tom compartilhado por todos:

```ts
export type Tom = "ok" | "now" | "block" | "lock" | "neutro";
```

Mapa de cores — **usar exatamente estes tokens**, sem inventar cor:

| Tom | Texto | Fundo | Borda |
|---|---|---|---|
| `ok` | `--inst-ok` | `--inst-ok-bg` | `--inst-ok-line` |
| `now` | `--inst-now` | `--inst-now-bg` | `--inst-now-line` |
| `block` | `--inst-block` | `--inst-block-bg` | `--inst-block-line` |
| `lock` | `--inst-lock` | transparente | `--inst-line` |
| `neutro` | `--inst-text` | `--inst-panel` | `--inst-line` |

### Componentes

**`<InstLabel>`** — o rótulo mono que aparece 35 vezes no checklist.
Fonte mono, `10px`, `letterSpacing: "0.16em"`, `textTransform: "uppercase"`,
cor `--inst-faint`.

**`<InstPage eyebrow title right?>`** — casca da página.
Cabeçalho com `InstLabel` no eyebrow, título 23px peso 600
`letterSpacing: "-0.015em"`, slot `right` opcional, `borderBottom: 1px solid
var(--inst-line-2)` e `paddingBottom: 18px`. Conteúdo abaixo com `gap: 20px`.

**`<InstBar>`** e **`<InstBarCell label value tom? sub?>`** — a barra de estado
do topo. Células separadas por `borderRight: 1px solid var(--inst-line-2)`,
padding `14px 24px`, label em `InstLabel` e valor em mono tabular 15px.

**`<InstCard label? children>`** — painel.
`border: 1px solid var(--inst-line)`, `background: var(--inst-panel)`,
`borderRadius: 3px`, padding `20px 22px`.

**`<InstNum value tom? size?>`** — número.
Sempre `className="tabular"`. `size`: `sm` 13px · `md` 16px · `lg` 25px ·
`xl` 34px, peso 600 nos dois maiores.

**`<InstBadge tom children>`** — pílula.
Mono `9px`, `letterSpacing: "0.1em"`, uppercase, `padding: "3px 9px"`,
`borderRadius: 2px`, borda e cor do tom.

**`<InstBand tom titulo linhas? acao?>`** — a faixa de status.
`borderLeft: "3px solid"` na cor do tom, fundo do tom, `borderRadius: 3px`,
padding `17px 22px`. Título mono 17px peso 600. `linhas` renderiza cada item
com um travessão na cor do tom — **todas, sem truncar e sem tooltip**.

**`<InstTable colunas children>`** e **`<InstRow tom? children>`** — tabela densa.
Cabeçalho com `InstLabel`, fundo `--inst-bg`, `borderBottom: 1px solid
var(--inst-line)`. Linhas com `borderBottom: 1px solid #14181B` e padding
`12px 16px`. `InstRow` com tom desenha `borderLeft: 2px solid` na cor.

**`<InstEmpty children>`** — estado vazio.
Borda tracejada `1px dashed var(--inst-line-2)`, texto `--inst-faint`, centrado.

**`<InstDivider>`** — `height: 1px`, `background: var(--inst-line)`.

### Regra de cor

Cor **só** significa estado. Nenhum componente aceita cor arbitrária. Se um
elemento não é `ok`, `now`, `block` ou `lock`, ele é `neutro` e não tem cor.

Sem gradiente, sem cor de marca, sem accent decorativo.

---

## 2. `cockpit/app/globals.css`

Só acrescentar o que faltar. `.tabular` já existe. Se `.mono` não existir como
classe isolada, criar:

```css
.mono { font-family: var(--font-mono), ui-monospace, monospace; }
```

Não alterar nem remover token existente.

---

## 3. As dez páginas

Para cada uma, o trabalho é **o mesmo e é mecânico**:

1. Trocar `Card`/`CardHeader`/`CardTitle`/`CardContent` do shadcn por `InstCard`
2. Trocar `Badge` por `InstBadge`, escolhendo o tom pelo significado
3. Trocar `Table` do shadcn por `InstTable`/`InstRow`
4. Envolver o conteúdo em `InstPage` com eyebrow e título
5. Todo número passa a `InstNum` — nenhum número fora de mono tabular
6. Todo rótulo de campo vira `InstLabel`
7. Faixa de status (gate, aviso, alerta) vira `InstBand`
8. Estado vazio vira `InstEmpty`

**Preservar integralmente:**
- toda chamada de dados, hook, `useEffect`, fallback e tratamento de erro
- todo texto de conteúdo, palavra por palavra
- toda lógica condicional de renderização

Se a página hoje trata um caso de erro ou de lista vazia, ela continua tratando.
**Restilizar não é reescrever.**

### Escolha de tom por significado

| Significado | Tom |
|---|---|
| liberado, cumprido, positivo, lucro | `ok` |
| agora, atenção, aviso, aguardando | `now` |
| bloqueado, desvio, negativo, prejuízo | `block` |
| travado, indisponível, futuro | `lock` |
| tudo o mais | `neutro` |

Número positivo em `ok`, negativo em `block`. Zero é `neutro`, não verde.

### Nota sobre `/copa/*`

Essas páginas consomem o FastAPI local via `cockpit/lib/copa-api.ts` e têm
fallback quando ele não responde. **O fallback continua exatamente como está** —
elas precisam renderizar sem o backend no ar. Restilizar o estado de fallback
também: ele usa `InstEmpty` com o texto que já existe.

---

## 4. `cockpit/config/sidebar.ts`

Três itens do menu apontam para rotas que **não existem** e dão 404:
`/backtests`, `/pesquisa`, `/config`.

**Remover esses três itens.** Item de menu que quebra é pior que item ausente.

Isso esvazia o grupo "Sistema" inteiro — remover o grupo também.

**Não remover mais nada.** O grupo Copa BTG fica, decisão do operador.

---

## Critério de aceite

```bash
cd cockpit && npx tsc --noEmit
cd .. && npx tsx cockpit/scripts/verify.ts
cd cockpit && npm run build
cd .. && git diff --stat
```

1. `tsc` limpo
2. `verify.ts` 31 casos OK, exit 0 — **esta task não toca em lógica, então
   nenhum caso pode mudar de resultado**
3. build compila, todas as rotas geradas
4. `git diff --stat` lista exatamente os 13 arquivos

**Conferências mecânicas:**

```bash
grep -rc "from \"@/components/ui/card\"" cockpit/app/copa cockpit/app/trades cockpit/app/estrategias cockpit/app/cerebro cockpit/app/page.tsx
grep -rn "backtests\|pesquisa\|\"/config\"" cockpit/config/sidebar.ts
```

- O primeiro deve dar 0 em todas — nenhuma página ainda importando o Card antigo
- O segundo deve voltar vazio

**`tsc` e build limpos não provam tela.** O aceite inclui `npm run dev` e abrir
cada uma das dez, conferindo que renderiza, que os dados aparecem e que nenhuma
quebrou. Reportar qual você abriu.

---

## Armadilhas desta task

**Reescrever em vez de restilizar.** O modo de falhar aqui é apagar tratamento de
erro, fallback ou caso de lista vazia junto com o estilo. `git diff` de cada
página deve mostrar mudança de apresentação, não de comportamento.

**Apagar comentário.** `git diff -U0 | grep "^-.*//"` faz parte da revisão.

**Inventar cor.** Se o tom não é um dos cinco, o elemento é `neutro`. Verde e
vermelho significam resultado, não decoração.

**Número fora de tabular.** Coluna de preço que dança quando o dígito muda é
exatamente o que a estética existe para evitar. Todo número passa por `InstNum`.

**Mexer em `lib/`.** Esta task é presentação. Zero mudança de dados.
