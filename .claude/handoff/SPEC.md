# SPEC — Redesenho do /checklist: trilha travada, direção "instrumento de precisão"

## Objetivo

O `/checklist` já tem a lógica certa (7 KILL, 8 PONTO, gate de janela nobre —
commit `0af5acb`). O que falta é a interface fazer o modelo ser **sentido**.

Hoje os 7 obrigatórios são uma lista de caixas: dá para marcar o passo 6 antes
do passo 1. Mas o modelo do operador é uma **sequência real** —

`Array HTF` → `liquidez varrida` → `preço chegou na região` → `MSS no LTF` →
`FVG do displacement` → `reteste` → `risco definido`

— e marcar fora de ordem é exatamente o erro que o sistema existe para impedir
("não persigo preço"). Esta task trava a sequência na interface: **só o próximo
passo aceita clique.**

Junto vem a direção visual nova: escuro, denso, tipografia técnica, números
tabulares, e **cor só onde significa estado**.

**A referência visual é o artboard `design/Main.dc.html`.** Leia esse arquivo
antes de escrever qualquer linha: ele tem o layout, as cores exatas, os tamanhos
e a interação já resolvidos. Copie os valores de lá — não arredonde para grade
de 4/8px, não invente tom.

---

## Arquivos (só estes)

1. `cockpit/app/layout.tsx` — trocar a fonte
2. `cockpit/app/globals.css` — adicionar os tokens de estado
3. `cockpit/lib/gate.ts` — adicionar as regras de sequência
4. `cockpit/app/checklist/page.tsx` — reconstruir a interface
5. `cockpit/scripts/verify.ts` — casos novos para a sequência

`git diff --stat` tem que listar exatamente estes cinco.

## NÃO MEXER

Ver `.claude/skills/dupla/SKILL.md`. Nesta task, em especial:
`copa/**`, `core/**`, `strategies/**`, `cockpit/lib/trading-db.ts`,
`cockpit/data/strategies.ts`, `cockpit/app/copa/**`, `cockpit/supabase/**`,
`design/**` (é referência, leitura apenas).

**Não instalar dependência.** `next/font/google` já vem com o Next.

**Regra de conformidade da Copa vale integralmente** — sem cotação, sem dado de
mercado, sem detecção de setup, sem integração com plataforma.

**Não mudar a lógica de gate existente.** `classificarJanela`,
`scoreMinimoEfetivo` e `avaliarGate` já estão corretos e testados. Esta task
ACRESCENTA funções; não reescreve as que existem.

---

## 1. `cockpit/app/layout.tsx` — tipografia

Hoje: `Inter` via `next/font/google` em `--font-sans`.

Trocar por duas famílias, mantendo o mesmo padrão `next/font/google` e as mesmas
variáveis CSS que o resto do app já consome:

```ts
import { Archivo, IBM_Plex_Mono } from "next/font/google";

const archivo = Archivo({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});
```

Aplicar as duas variáveis na tag `<html>` (hoje aplica só `inter.variable`).
Não remover `dark h-full antialiased`.

**Motivo:** Inter é a fonte padrão de todo template — é parte do que faz o app
não parecer instrumento. Archivo é industrial e tem peso; IBM Plex Mono carrega
todo número com `tabular-nums`, para coluna de preço não dançar quando o dígito
muda.

## 2. `cockpit/app/globals.css` — tokens de estado

**Acrescentar** um bloco novo ao final do arquivo. Não editar nem remover
nenhum token existente — o resto do app depende deles.

```css
/* Tokens do instrumento. Cor aqui NUNCA é decoração: cada uma significa
   um estado. Ver design/Main.dc.html. */
:root {
  --inst-bg:        #0C0E10;
  --inst-panel:     #0F1215;
  --inst-panel-2:   #101416;
  --inst-line:      #1E2327;
  --inst-line-2:    #262B30;

  --inst-text:      #E8ECEF;
  --inst-text-2:    #A8B2B9;
  --inst-dim:       #8A949C;
  --inst-faint:     #5A646C;
  --inst-ghost:     #4A535A;

  --inst-ok:        #3FB27F;  /* cumprido, liberado */
  --inst-now:       #E0B44E;  /* agora, atenção */
  --inst-block:     #E0574A;  /* bloqueado, desvio */
  --inst-lock:      #394148;  /* travado */

  --inst-ok-bg:     #101614;
  --inst-now-bg:    #15140E;
  --inst-block-bg:  #150F0E;
  --inst-ok-line:   #1E3A2E;
  --inst-now-line:  #3A3020;
  --inst-block-line:#3A1F1C;
}
```

Adicionar também um utilitário para números:

```css
.tabular { font-family: var(--font-mono), ui-monospace, monospace; font-variant-numeric: tabular-nums; }
```

## 3. `cockpit/lib/gate.ts` — regras de sequência

Acrescentar ao módulo (sem tocar no que já existe):

```ts
/**
 * Quantos KILL consecutivos, a partir do primeiro, estão marcados.
 * É o número de passos cumpridos da trilha.
 */
export function passosCumpridos(itens: ItemAvaliado[]): number;

/**
 * Estado de cada KILL, na ordem do array:
 * "CUMPRIDO" — já marcado
 * "AGORA"    — o próximo, único clicável
 * "TRAVADO"  — ainda não liberado
 */
export function estadoDosPassos(itens: ItemAvaliado[]): Array<"CUMPRIDO" | "AGORA" | "TRAVADO">;

/**
 * Aplica um clique num KILL e devolve a lista nova.
 * - clicar no passo AGORA: marca ele
 * - clicar num passo CUMPRIDO de índice n: desmarca ele E TODOS OS SEGUINTES
 * - clicar num passo TRAVADO: não faz nada (devolve a lista inalterada)
 */
export function alternarPasso(itens: ItemAvaliado[], id: string): ItemAvaliado[];
```

**A regra de desmarcar em cascata não é detalhe.** Se o operador volta ao passo
3, os passos 4 a 7 descrevem uma estrutura que ele acabou de negar — deixá-los
marcados guarda um estado que não corresponde ao gráfico. Voltar limpa o que
vinha depois.

Itens PONTO não têm ordem: continuam livres, alternados como hoje.

`passosCumpridos` conta apenas KILL, na ordem em que aparecem no array, parando
no primeiro não marcado.

## 4. `cockpit/app/checklist/page.tsx` — a interface

Reconstruir seguindo `design/Main.dc.html`. Comportamento de carregar, salvar e
resetar continua igual; `risk_approved` segue derivado de `gate.liberado`.

### 4a. Barra de estado (topo, largura cheia)

Células separadas por borda vertical: **PREGÃO** (relógio de São Paulo, segundos,
atualizado a cada segundo), **JANELA** (ponto colorido + `PRIME · 10:00–11:00` /
`FORA DA NOBRE` / `FORA DA JANELA` + a nota explicativa), **PERDA DIA**,
**TRADES**, **MULLIGAN**.

As três últimas ainda não têm fonte de dados — renderizar com traço (`—`) e o
rótulo, **nunca com número inventado**. Elas ganham dado quando as tabelas do
`schema_v2` existirem.

### 4b. Trilha (coluna principal)

Um cartão por KILL, na ordem, com `grid-template-columns: 40px 1fr auto`:

| Estado | Marca | Fundo | Borda esquerda | Texto | Tag |
|---|---|---|---|---|---|
| CUMPRIDO | `--inst-ok`, símbolo `✓` | `--inst-panel-2` | 3px `--inst-ok` | `--inst-text-2` | `CUMPRIDO` |
| AGORA | `--inst-now`, número | `--inst-now-bg` | 3px `--inst-now` | `--inst-text` | `AGORA` |
| TRAVADO | `--inst-lock`, número | `#0D1013` | 3px `--inst-lock` | `--inst-ghost` | `TRAVADO` |

Cada cartão mostra o `label` e, abaixo, o `ajuda` — mais legível no AGORA, apagado
nos outros.

**Clique na linha inteira**, não só no ícone. CUMPRIDO e AGORA são clicáveis
(`cursor: pointer`, hover claro); TRAVADO não responde e não tem cursor de
ponteiro.

Contador `{cumpridos} / 7` no cabeçalho, âmbar enquanto incompleto, verde em 7.

Abaixo da trilha, uma linha de orientação: qual passo está liberado e quantos
faltam; em 7, "Sequência completa. O trade agora termina no alvo ou no stop."

### 4c. Painel lateral — confluência e gate

Largura fixa ~452px, fundo `--inst-panel`, borda esquerda.

**Score**: número grande, `/ mínimo` ao lado, barra 0–100 com um traço vertical
na marca do mínimo efetivo (65 ou 80). Verde quando atinge, âmbar quando não.
Abaixo, a nota do regime: `MÍNIMO 65 NA JANELA NOBRE` / `MÍNIMO 80 FORA DA
JANELA NOBRE` / `BLOQUEADO PELO HORÁRIO`.

**Itens PONTO**: linha compacta com caixa, label, badge `ESTIMADO` e o peso à
direita. Marcado ganha fundo `--inst-ok-bg` e peso verde.

**Gate** (rodapé do painel, fundo e borda conforme o estado):
`LIBERADO` verde ou `BLOQUEADO` vermelho, seguido de **todos** os `motivos`, um
por linha, sem truncar e sem tooltip. `avisos` em âmbar, bloco separado.

**Botão ABRIR ORDEM**: sempre visível. Travado, é contorno cinza com texto
apagado; liberado, fundo `--inst-ok` com texto escuro. Nunca escondido — o
bloqueio precisa ser visto.

### 4d. Relógio

`setInterval` de 1 s para o relógio e a reavaliação da janela. `clearInterval` no
unmount. Sempre `America/Sao_Paulo`, nunca a hora local do navegador.

## 5. `cockpit/scripts/verify.ts` — casos novos

Manter os 13 casos existentes. Acrescentar, para uma lista dos 7 KILL:

1. Nenhum marcado → `passosCumpridos` = 0; estados = `["AGORA", "TRAVADO" × 6]`
2. k1–k3 marcados → `passosCumpridos` = 3; estado do k4 = `AGORA`, k5 = `TRAVADO`
3. `alternarPasso` no k4 quando k1–k3 estão marcados → k4 marcado, cumpridos = 4
4. `alternarPasso` no k6 quando só k1–k3 estão marcados → **lista inalterada**
   (travado não responde)
5. k1–k7 todos marcados, `alternarPasso` no k3 → k3, k4, k5, k6, k7 desmarcados,
   k1 e k2 intactos, cumpridos = 2
6. Marcar KILL fora de ordem direto no array (k1 e k5 marcados, k2–k4 não) →
   `passosCumpridos` = 1 (conta só os consecutivos do começo)

O caso 6 protege contra linha antiga do banco com estado incoerente.

---

## Critério de aceite

```bash
cd cockpit && npx tsc --noEmit
cd .. && npx tsx cockpit/scripts/verify.ts
cd cockpit && npm run build
cd .. && git diff --stat
grep -c "Inter" cockpit/app/layout.tsx || echo "0 ocorrencias - OK"
```

Esperado:
1. `tsc` sem erro
2. `verify.ts` com todos os casos OK e exit 0 (13 antigos + 6 novos)
3. `npm run build` compila
4. `git diff --stat` lista exatamente os 5 arquivos
5. `Inter` → 0 ocorrências em `layout.tsx`

`tsc` e build limpos **não provam tela**. O aceite inclui rodar `npm run dev`,
abrir `/checklist` e conferir: só o próximo passo responde ao clique; clicar num
passo cumprido volta e limpa os seguintes; o relógio mostra hora de São Paulo; o
botão ABRIR ORDEM está visível e travado.

## Armadilhas desta task

**Trocar a fonte quebra outras telas.** `--font-sans` é consumido pelo app
inteiro. Trocar a família é intencional; **mudar o nome da variável não é**.

**Cascata ao voltar.** Desmarcar só o passo clicado, deixando os seguintes
marcados, é o bug mais provável aqui — e ele guarda um estado que contradiz o
gráfico. O caso 5 do verify existe por isso.

**Cor fora do sistema.** Se um tom não é `--inst-ok`, `--inst-now`,
`--inst-block` ou `--inst-lock`, ele não significa estado e não deve existir.
Nada de gradiente, nada de cor de marca.

**Números inventados.** Perda do dia, trades e mulligan ainda não têm fonte.
Renderizar `—`. Preencher com valor plausível é o erro mais caro deste projeto.
