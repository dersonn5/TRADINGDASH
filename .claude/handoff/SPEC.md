# SPEC — Gate de janela nobre e checklist único em /checklist

## Objetivo

O Anderson opera a Copa BTG Trader a partir de **14/09** (4 dias). A tela que ele
vai abrir no pregão é `/checklist`, publicada no Vercel com Supabase.

Hoje essa tela renderiza um checklist genérico de 7 itens (`c1`…`c7`) que **não é
o modelo dele**, não distingue item obrigatório de item de confluência, e não tem
gate nenhum — `risk_approved` é um booleano que o próprio operador marca.

O modelo real está em `cockpit/data/strategies.ts` (`PLAYBOOK_ANDERSON`): máquina
de duas camadas, **7 itens KILL** (obrigatórios, bloqueiam) e **8 itens PONTO**
(confluência, somam 100).

Esta task faz `/checklist` renderizar o modelo real, com gate de verdade, e
aplica a regra de janela de horário que o Anderson definiu:

- **10:00–11:00 é a janela nobre.** Abertura do mercado à vista (10:00) e
  abertura americana (10:30). Volatilidade e manipulação. Score mínimo **65**.
- **09:00–12:00 fora da janela nobre**: permitido, mas exige score mínimo **80**.
  Pode operar, só que apenas setup melhor.
- **Fora de 09:00–12:00**: bloqueado.

Sem isso, dia 14 ele opera com o checklist errado.

---

## Arquivos (só estes)

1. `cockpit/lib/gate.ts` — **novo**
2. `cockpit/lib/trading-db.ts` — editar tipos e `getDefaultChecklist`
3. `cockpit/data/strategies.ts` — editar `calibracao` e o bloco `checklist`
4. `cockpit/app/checklist/page.tsx` — reescrever a renderização
5. `cockpit/scripts/verify.ts` — **novo**, é a prova de aceite
6. `copa/strategies/playbook_anderson.json` — **só** o bloco `checklist` e
   `calibracao`, para espelhar o item 3

Nenhum outro arquivo. `git diff --stat` tem que listar exatamente estes seis.

## NÃO MEXER

Ver `.claude/skills/dupla/SKILL.md` deste projeto — a lista completa com motivo.
Em especial, nesta task: `copa/risk.py`, `core/entry_quality.py`, `strategies/**`,
`cockpit/supabase/schema.sql`, `cockpit/app/copa/**`, `cockpit/lib/copa-api.ts`.

**Não instalar dependência.** `npx tsx` é permitido porque roda avulso e não
altera `package.json`.

**Regra de conformidade da Copa vale integralmente** — sem cotação, sem dado de
mercado, sem detecção de setup, sem integração com plataforma. Ver SKILL.md.

---

## 1. `cockpit/lib/gate.ts` (novo)

Módulo puro, sem React, sem import de Supabase. Precisa ser importável por script
Node.

```ts
export type Janela = "PRIME" | "VALIDA" | "FORA";

export interface ItemAvaliado {
  id: string;
  tipo: "KILL" | "PONTO";
  label: string;
  checked: boolean;
  peso: number;
}

export interface GateResult {
  liberado: boolean;
  janela: Janela;
  score: number;
  scoreMinimo: number;
  killsFaltando: string[];   // labels dos KILL não marcados
  motivos: string[];         // todos os motivos de bloqueio, em português
  avisos: string[];
}

export const SCORE_MINIMO_PRIME = 65;
export const BONUS_FORA_DA_PRIME = 15;   // VALIDA exige 65 + 15 = 80

export function classificarJanela(agora: Date): Janela;
export function scoreMinimoEfetivo(janela: Janela, base: number): number;
export function avaliarGate(
  itens: ItemAvaliado[],
  bias: string,
  agora: Date,
  scoreMinimoBase?: number
): GateResult;
```

### `classificarJanela`

Converte `agora` para **America/Sao_Paulo** — não usar a hora local do navegador,
porque a tela pode ser aberta de outro fuso. Usar
`Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", hour12: false })`
e comparar em minutos desde a meia-noite.

- `PRIME` — de 10:00 (inclusive) a 11:00 (exclusive)
- `VALIDA` — de 09:00 (inclusive) a 12:00 (exclusive), fora do PRIME
- `FORA` — o resto

### `scoreMinimoEfetivo`

- `PRIME` → `base`
- `VALIDA` → `base + BONUS_FORA_DA_PRIME`
- `FORA` → `Number.POSITIVE_INFINITY`

### `avaliarGate`

`score` = soma dos `peso` dos itens **PONTO marcados**. Itens KILL não somam.

Bloqueia, acumulando **todos** os motivos aplicáveis (nunca parar no primeiro):

| Condição | Motivo (texto exato) |
|---|---|
| `bias === "NAO_OPERAR"` | `"bias do dia marcado como NAO_OPERAR"` |
| `janela === "FORA"` | `"fora da janela de operação 09:00–12:00"` |
| algum KILL não marcado | `"falta obrigatório: <label>"` (um motivo por item) |
| `score < scoreMinimo` e janela ≠ FORA | `"score <score> abaixo do mínimo <scoreMinimo>"` |

`liberado` = `motivos.length === 0`.

Aviso (não bloqueia): quando `janela === "VALIDA"`, adicionar em `avisos`
`"fora da janela nobre 10:00–11:00 — exige score 80"`.

---

## 2. `cockpit/data/strategies.ts`

### 2a. Corrigir a declaração de calibração

Hoje diz `status: "EM_VALIDACAO"` com observação `"Baseado nos conceitos ICT
clássicos calibrados para índice e dólar B3"`. **Isso é falso** — nenhum peso foi
medido em backtest. Trocar por:

```ts
calibracao: {
  status: "NAO_CALIBRADO",
  observacao:
    "Todos os pesos e o score mínimo são ESTIMADO. Nenhum foi medido em backtest de WIN. Ver COPA_BTG_PLAN_V2.md Fase 3.",
  atualizado_em: "2026-09-10",
},
```

### 2b. Remover o item `p5` e redistribuir os pesos

`p5` era `"Killzone nobre"`. A janela nobre agora é **regra de gate** (score
mínimo 65 dentro, 80 fora). Mantê-lo como ponto seria contagem dupla: o score
subiria justo quando a barra já está mais baixa.

**Apagar o item `p5`.** Manter os ids restantes inalterados. Novos pesos, somando
exatamente 100:

| id | peso novo |
|---|---|
| `p1` | 14 |
| `p2` | 14 |
| `p3` | 14 |
| `p4` | 14 |
| `p6` | 11 |
| `p7` | 11 |
| `p8` | 11 |
| `p9` | 11 |

Resultado: **7 KILL + 8 PONTO**, PONTO somando 100. Todos os PONTO continuam com
`origem: "ESTIMADO"`.

---

## 3. `copa/strategies/playbook_anderson.json`

Espelhar **exatamente** a mudança do item 2: remover `p5`, aplicar os mesmos
pesos, mesmo bloco `calibracao` (`NAO_CALIBRADO`, mesma observação, mesma data).

Não tocar em mais nada deste arquivo. `copa/strategies_config.py` valida que a
soma dos PONTO é 100 e **levanta `ValueError`** se não for — se essa validação
quebrar, a mudança está errada.

---

## 4. `cockpit/lib/trading-db.ts`

### 4a. Estender `ChecklistItem`

```ts
export interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  weight: number;
  tipo: "KILL" | "PONTO";          // novo
  ajuda?: string;                   // novo
  origem?: "MEDIDO" | "ESTIMADO";   // novo
  category?: "pre_market" | "bias" | "technical" | "risk" | "emotional";
}
```

`category` passa a ser opcional — o modelo novo não usa essas categorias, usa
`tipo`. Não remover o campo: linhas antigas no Supabase ainda o têm.

### 4b. Reescrever `getDefaultChecklist`

**Apagar a lista `c1`…`c7` inteira.** Os itens passam a ser derivados de
`PLAYBOOK_ANDERSON.checklist` (importar de `@/data/strategies`), preservando a
ordem do array: KILL primeiro, depois PONTO.

Mapeamento por item: `id` → `id`, `label` → `label`, `ajuda` → `ajuda`,
`tipo` → `tipo`, `peso` → `weight`, `origem` → `origem`, `checked: false`.

Manter `session_name`, `market: "B3 WIN"`, `bias: "NEUTRO"`, `score: 0`,
`risk_approved: false`, `notes: ""`.

### 4c. Robustez de linha antiga

`fetchTodayChecklist` pode trazer uma linha salva antes desta mudança, com os
itens `c1`…`c7` e sem `tipo`. Nesse caso, **descartar os itens salvos e devolver
o default novo**, preservando `bias` e `notes` da linha. Critério de detecção:
algum item sem `tipo`, ou conjunto de ids diferente do default.

Sem isso o operador abre dia 14 com o checklist velho vindo do banco, que é
exatamente o bug que esta task existe para corrigir.

---

## 5. `cockpit/app/checklist/page.tsx`

Reescrever a renderização. Comportamento existente de carregar/salvar/resetar
continua.

### 5a. Faixa de gate no topo

Acima de tudo, sempre visível:

- **Verde `LIBERADO`** quando `gate.liberado`
- **Vermelho `BLOQUEADO`** caso contrário, listando **todos** os `motivos`, um
  por linha. Não esconder motivo atrás de tooltip nem truncar a lista.
- `avisos` em âmbar, num bloco separado dos motivos.

### 5b. Indicador de janela

Mostrar a hora corrente de São Paulo e a janela:

| Janela | Texto |
|---|---|
| `PRIME` | `JANELA NOBRE · 10:00–11:00 · score mínimo 65` (verde) |
| `VALIDA` | `Fora da janela nobre · score mínimo 80` (âmbar) |
| `FORA` | `Fora da janela de operação 09:00–12:00` (vermelho) |

Recalcular a cada 30 s com `setInterval`, e limpar o intervalo no unmount.

### 5c. Dois blocos separados

**OBRIGATÓRIOS** primeiro, com o rótulo `sem isso, não entra`. Depois
**CONFLUÊNCIA**, com `soma 100 pontos`. Visualmente distintos — não pode parecer
uma lista só.

Cada item mostra o `ajuda` quando existir. Item PONTO mostra o peso e um badge
`ESTIMADO` quando `origem === "ESTIMADO"` — o operador precisa ver que aquele
peso é julgamento, não medição.

Clique na linha inteira alterna o item, não só na caixinha.

### 5d. Score

Barra de progresso 0–100 com a marca do `scoreMinimo` **efetivo** (65 ou 80,
conforme a janela). Número grande do score ao lado.

### 5e. `risk_approved`

Deixa de ser toggle manual. Passa a ser **derivado**: `risk_approved = gate.liberado`,
gravado no save. Remover o controle manual.

---

## 6. `cockpit/scripts/verify.ts` (novo) — a prova

Script Node, sem dependência nova, rodado com `npx tsx cockpit/scripts/verify.ts`.
Imprime `OK` ou `FALHOU` por caso e sai com código 1 se qualquer um falhar.

**Casos de janela** — construir a `Date` de forma que em São Paulo seja o horário
indicado:

| Hora (SP) | Janela esperada | Score mínimo esperado |
|---|---|---|
| 10:30 | `PRIME` | 65 |
| 10:00 | `PRIME` | 65 |
| 10:59 | `PRIME` | 65 |
| 11:00 | `VALIDA` | 80 |
| 09:30 | `VALIDA` | 80 |
| 11:59 | `VALIDA` | 80 |
| 08:59 | `FORA` | bloqueado |
| 13:00 | `FORA` | bloqueado |

**Casos de gate:**

1. Todos os 7 KILL marcados + PONTO somando 70, às 10:30 → `liberado === true`
2. Mesmo conjunto às 09:30 → `liberado === false`, motivo cita score 70 e mínimo 80
3. Todos os PONTO marcados (100) e **um** KILL faltando, às 10:30 →
   `liberado === false`, e o motivo nomeia o KILL que falta
4. `bias === "NAO_OPERAR"` com tudo marcado às 10:30 → `liberado === false`

**Caso de sincronia** — ler `copa/strategies/playbook_anderson.json` e comparar
com `PLAYBOOK_ANDERSON` de `cockpit/data/strategies.ts`: mesmo conjunto de ids,
mesmo `tipo` por id, mesmo `peso` por id. Divergência falha o script.

É o que impede as duas fontes de divergirem em silêncio de novo.

---

## Critério de aceite

Rodar e colar a saída de cada um:

```bash
cd cockpit && npx tsc --noEmit
npx tsx cockpit/scripts/verify.ts
cd "E:/AUTOMAÇÃO IA/TRADING AI" && python -c "from copa.strategies_config import load_one; s=load_one('playbook_anderson'); p=[i for i in s['checklist'] if i['tipo']=='PONTO']; k=[i for i in s['checklist'] if i['tipo']=='KILL']; print('KILL',len(k),'PONTO',len(p),'soma',sum(i['peso'] for i in p))"
git diff --stat
grep -c "Calendário Econômico" cockpit/lib/trading-db.ts || echo "0 ocorrencias - OK"
grep -c "EM_VALIDACAO" cockpit/data/strategies.ts || echo "0 ocorrencias - OK"
```

Esperado:
1. `tsc` sem erro
2. `verify.ts` com todos os casos `OK`, exit 0
3. Python imprime `KILL 7 PONTO 8 soma 100`
4. `git diff --stat` lista **exatamente** os 6 arquivos da seção "Arquivos"
5. `Calendário Econômico` → 0 ocorrências
6. `EM_VALIDACAO` → 0 ocorrências

`tsc` limpo não prova tela. O aceite final inclui abrir `/checklist` e conferir:
faixa de gate visível, dois blocos separados, badge `ESTIMADO` nos PONTO, e o
indicador de janela mostrando a hora de São Paulo.

---

## Armadilhas desta task

**Fuso.** Usar hora local do navegador em vez de America/Sao_Paulo faz o gate
liberar no horário errado. É o tipo de bug que só aparece no dia.

**Linha antiga do Supabase.** Se `fetchTodayChecklist` devolver os itens velhos
salvos hoje, a tela mostra o checklist antigo mesmo com o código novo. A regra
4c existe por isso.

**Comparação de horário como string.** `"09:30" < "10:00"` funciona por acidente
lexicográfico, mas quebra em outros casos. Converter para minutos desde a
meia-noite.

**Apagar comentário que explica invariante.** Reescrever arquivo inteiro em vez
de editar remove comentários em silêncio. `git diff -U0 | grep "^-.*//"` faz
parte da revisão.
