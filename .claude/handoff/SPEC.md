# SPEC — Duas estratégias, persistência e o gate que impede operar demais

## Objetivo

O operador definiu o trade system dele por escrito pela primeira vez. A fonte
canônica é `Cerebro_Obsidian/Trading AI/B05 Trade System/Trade_System_Anderson.md`.
**Leia esse arquivo antes de escrever qualquer linha.**

Três mudanças decorrem disso:

**1. São duas estratégias, não uma.** Reversão HTF e Continuidade de Tendência
têm gatilhos diferentes e checklists diferentes. Os JSONs já estão escritos em
`copa/strategies/`. O app só conhece uma.

**2. A persistência nunca subiu.** O app não sabe quantos trades foram feitos
hoje — o campo `TRADES` renderiza `—`. Por isso nenhum limite bloqueia nada, e o
operador vem operando solto no meio da Copa. Este é o problema central.

**3. Os limites são os do Profit Chart.** A plataforma trava em **3 perdas** ou
**5 operações**. O sistema usa exatamente esses números. Regra que contradiz a
plataforma vira regra ignorada.

---

## Arquivos (só estes)

1. `cockpit/lib/supabase.ts` — persistir sessão de auth
2. `cockpit/app/login/page.tsx` — **novo**
3. `cockpit/components/auth-gate.tsx` — **novo**
4. `cockpit/app/layout.tsx` — envolver com o auth gate
5. `cockpit/data/strategies.ts` — as duas estratégias
6. `cockpit/lib/copa-db.ts` — **novo**, camada de dados `copa_*`
7. `cockpit/lib/gate.ts` — limites reais no gate
8. `cockpit/app/checklist/page.tsx` — seleção de estratégia, formulário, ligação
9. `cockpit/lib/trading-db.ts` — derivar itens da estratégia escolhida
10. `cockpit/scripts/verify.ts` — casos novos

`git diff --stat` tem que listar exatamente estes dez.

## NÃO MEXER

Ver `.claude/skills/dupla/SKILL.md`. Nesta task, em especial: `copa/**` (os JSONs
das estratégias são **fonte, leitura apenas** — não editar), `core/**`,
`strategies/**`, `cockpit/supabase/**` (SQL já aplicado), `cockpit/app/copa/**`.

**Não instalar dependência.** `@supabase/supabase-js` já está no projeto.

**Regra de conformidade da Copa vale integralmente** — sem cotação, sem dado de
mercado, sem detecção de setup.

---

## 1. Autenticação

### 1a. `cockpit/lib/supabase.ts`

```ts
createClient(url, anonKey, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
})
```

### 1b. `cockpit/app/login/page.tsx`

Tela mínima, estética instrumento (tokens `--inst-*`): e-mail, senha, botão
ENTRAR. `supabase.auth.signInWithPassword`. Erro em vermelho com a mensagem real
do Supabase, **não** texto genérico. Sem cadastro, sem recuperação, sem OAuth.

### 1c. `cockpit/components/auth-gate.tsx`

Client component. `getSession()` + `onAuthStateChange`. Três estados: carregando
(fundo `--inst-bg`, sem flash), sem sessão (redireciona para `/login`), com
sessão (renderiza children). `/login` não passa pelo gate.

### 1d. `cockpit/app/layout.tsx`

Envolver com `<AuthGate>`. Não mexer nas fontes nem no `dark`.

---

## 2. `cockpit/data/strategies.ts` — as duas estratégias

Substituir `PLAYBOOK_ANDERSON` por duas constantes, **transcritas fielmente** de
`copa/strategies/reversao_htf.json` e `copa/strategies/continuidade_tendencia.json`.

```ts
export const REVERSAO_HTF: Strategy = { /* de reversao_htf.json */ };
export const CONTINUIDADE_TENDENCIA: Strategy = { /* de continuidade_tendencia.json */ };
export const DEFAULT_STRATEGIES: Strategy[] = [REVERSAO_HTF, CONTINUIDADE_TENDENCIA];
```

Campo a campo, sem reescrever texto, sem "melhorar" label ou ajuda. O `verify.ts`
compara os dois lados e falha se divergirem.

`REVERSAO_HTF` tem 7 KILL e 6 PONTO. `CONTINUIDADE_TENDENCIA` tem 6 KILL e
6 PONTO. Os dois somam 100 em PONTO.

---

## 3. `cockpit/lib/copa-db.ts` (novo)

Camada de dados. Só isto, nada de UI.

```ts
export interface TradeInput {
  strategy_id: string;
  mercado: "WIN" | "WDO";
  direcao: "COMPRA" | "VENDA";
  janela: "PRIME" | "VALIDA" | "FORA";
  score: number;
  score_minimo: number;
  grade: string;
  entrada: number;
  stop: number;
  alvo: number;
  contratos: number;
  rr_planejado: number;
  itens: Array<{ item_id: string; tipo: "KILL" | "PONTO"; checked: boolean; peso_no_momento: number }>;
  notas?: string;
}

export interface ResumoDoDia {
  session_id: string | null;
  trades_fechados: number;
  trades_abertos: number;
  operacoes_hoje: number;        // fechados + abertos
  perdas_hoje: number;
  pnl_dia: number;
  ultimo_loss_em: Date | null;
  trade_aberto_id: string | null;
}

export interface FechamentoInput {
  saida: number;
  motivo_saida: "ALVO" | "STOP" | "MANUAL";
  desfecho_plano?: "BATEU_ALVO" | "BATEU_STOP" | "NAO_SEI";
  execucao: "A" | "B" | "C";
  respeitou_plano: boolean;
  antecipou_stop: boolean;
  parcial_emocional: boolean;
  mudou_alvo: boolean;
  notas?: string;
}

export async function getVersaoVigente(strategyId: string): Promise<string | null>;
export async function getOuCriarSessaoDoDia(): Promise<string>;
export async function getResumoDoDia(): Promise<ResumoDoDia>;
export async function registrarTrade(input: TradeInput): Promise<string>;
export async function fecharTrade(id: string, f: FechamentoInput): Promise<void>;
```

### Regras

**`getVersaoVigente`** — maior `versao` do `strategy_id` em
`copa_strategy_versions`. Amarra o trade aos pesos que valiam na entrada.

**`getOuCriarSessaoDoDia`** — data de hoje em **America/Sao_Paulo**, nunca
`toISOString()` do navegador (depois das 21h dá o dia seguinte). Procura em
`copa_sessions` por `data`; se não existir, cria com os defaults do schema e
`phase_id` resolvido por `copa_phases` (a fase cujo intervalo contém a data, ou
null). `user_id` vem do `DEFAULT auth.uid()` — **não enviar**.

**`registrarTrade`** — duas etapas, sem transação no client:
1. insere em `copa_trades`, pega o `id`
2. insere **todos** os itens em `copa_trade_items` numa chamada só

Se o passo 2 falhar, **apagar o trade do passo 1** e propagar o erro. Trade sem
snapshot mente na estatística para sempre.

**`fecharTrade`** — calcula:
- `pontos_real` = (saída − entrada) × sinal · sinal = +1 COMPRA, −1 VENDA
- `pnl_real` = `pontos_real` × contratos × valor_ponto (WIN 0,20 · WDO 10,00)
- `pnl_plano`: ALVO ou STOP → igual a `pnl_real`. MANUAL com BATEU_ALVO → como se
  tivesse saído no alvo; BATEU_STOP → como se no stop; NAO_SEI → igual ao real.
- `notas` gravado com o prefixo `[EXEC:A]`, `[EXEC:B]` ou `[EXEC:C]` seguido das
  notas livres. **Não alterar o schema** — a coluna já existe.
- `hora_saida` = agora · `status` = `FECHADO`

**Erros nunca são engolidos.** Toda função propaga a mensagem do Supabase. Trade
que silenciosamente não gravou é o pior resultado possível desta task.

---

## 4. `cockpit/lib/gate.ts` — os limites reais

Acrescentar, **sem alterar** `classificarJanela`, `scoreMinimoEfetivo`,
`avaliarGate`, `passosCumpridos`, `estadoDosPassos` ou `alternarPasso`.

```ts
/** Limites espelhados do Profit Chart, que trava nestes números. */
export const MAX_PERDAS_DIA = 3;
export const MAX_OPERACOES_DIA = 5;
export const COOLDOWN_APOS_LOSS_MIN = 30;

export interface LimitesDia {
  bloqueado: boolean;
  motivos: string[];
}

export function avaliarLimitesDia(
  perdasHoje: number,
  operacoesHoje: number,
  ultimoLossEm: Date | null,
  agora: Date
): LimitesDia;

/** Minutos que faltam do cooldown, ou 0. */
export function cooldownRestante(ultimoLossEm: Date | null, agora: Date): number;
```

Regras:

| Condição | Motivo |
|---|---|
| `perdasHoje >= 3` | `"3 perdas no dia: pregao encerrado"` |
| `operacoesHoje >= 5` | `"5 operacoes no dia: limite atingido"` |
| `cooldownRestante > 0` | `"cooldown apos loss: faltam N min"` |

**O cooldown depois de QUALQUER loss** — não só depois de vários. Motivo, nas
palavras de quem opera: *"a maior parte dos dias eu começo no loss, e quando
começo no loss é como se minha cabeça voltasse pro passado"* · *"cometi um erro
que já desencadeou um monte de merda, e é sempre assim"*. O gatilho da cascata é
o primeiro loss.

`avaliarGate` ganha três parâmetros opcionais ao final —
`limites?: LimitesDia`, `tradeAbertoId?: string | null` — e acrescenta aos
`motivos`:

- todos os `motivos` de `limites`, quando bloqueado
- `"ja existe trade aberto"` quando `tradeAbertoId` não é nulo

**Chamadas existentes sem os parâmetros novos continuam funcionando.** Os 19
casos atuais do verify não podem quebrar.

---

## 5. `cockpit/lib/trading-db.ts`

`getDefaultChecklist` passa a receber a estratégia:

```ts
export function getDefaultChecklist(date: string, strategy: Strategy): LiveChecklist;
```

Deriva os itens de `strategy.checklist`, preservando a ordem: KILL primeiro,
PONTO depois. Mapeamento igual ao de hoje, mais o `strategy_id` guardado em
`LiveChecklist` (campo novo, opcional na interface para não quebrar linhas
antigas).

`fetchTodayChecklist(strategy)` — a regra de descarte de linha antiga continua, e
ganha um critério: se o `strategy_id` salvo for diferente do escolhido, devolve o
default novo preservando `bias` e `notes`.

---

## 6. `cockpit/app/checklist/page.tsx`

### 6a. Seletor de estratégia — no topo, acima de tudo

Dois botões grandes, lado a lado: **REVERSÃO HTF** e **CONTINUIDADE DE TENDÊNCIA**.
O escolhido fica destacado; o outro apagado.

Abaixo do seletor, uma linha com a `descricao` da estratégia escolhida.

Trocar de estratégia **reseta o checklist** (os itens são outros). Confirmar
antes se houver item marcado — perder marcação por clique errado no meio do
pregão é caro.

> Motivo de existir: são dois setups com gatilhos diferentes, e misturar os dois
> é o erro. A escolha é feita na pré-sessão, com a cabeça fria, e a tela só
> registra qual foi.

### 6b. Barra de estado com dado real

| Campo | Fonte |
|---|---|
| `PREGÃO` | relógio de São Paulo, atualizado a cada segundo |
| `JANELA` | `classificarJanela` |
| `OPERAÇÕES` | `operacoes_hoje / 5` — normal até 3, âmbar em 4, vermelho em 5 |
| `PERDAS` | `perdas_hoje / 3` — normal em 0, âmbar em 1–2, vermelho em 3 |
| `PNL DIA` | `pnl_dia` |

Tudo de `getResumoDoDia`, carregado no mount e recarregado após cada registro ou
fechamento. **Nada de número inventado** — enquanto carrega, `—`.

### 6c. Formulário de trade

Abaixo do painel de confluência: mercado, direção, entrada, stop, alvo,
contratos. RR e risco em reais ao vivo enquanto digita
(`risco = |entrada − stop| × contratos × valor_ponto`).

Validação local: COMPRA exige `stop < entrada < alvo`; VENDA exige
`alvo < entrada < stop`. O banco tem `CHECK` — a validação local existe para dar
mensagem melhor, não para substituir.

### 6d. ABRIR ORDEM

Registra de verdade, com o snapshot completo — **todos** os itens, marcados e não
marcados. Item não marcado é o lado "sem" da comparação em
`v_copa_item_performance`; sem ele a estatística não existe.

Sucesso: limpa o checklist, recarrega o resumo, confirma na tela.
Falha: vermelho com o erro real do Supabase, **checklist preservado**.

O botão continua visível e travado quando o gate bloqueia, com todos os motivos
listados abaixo.

### 6e. Trade aberto

Faixa com os dados do trade aberto e botão FECHAR. Registro de novo trade
bloqueado enquanto houver um aberto.

---

## 7. Fechamento

Diálogo: preço de saída, `motivo_saida`. Se MANUAL, `desfecho_plano` obrigatório.

Depois, **a pergunta mais importante da tela**:

> **Como foi a EXECUÇÃO?** (não o resultado)
>
> - **A** — fiz exatamente o que devia. Sem hesitar, sem perseguir, sem antecipar
> - **B** — executei, mas com ruído. Hesitei, entrei torto, saí cedo
> - **C** — forcei. Entortei a regra, antecipei sem confirmação, quis recuperar

Deixar explícito na tela que a pergunta é sobre execução e **não** sobre
resultado — **um trade vencedor pode ser C**.

> Por quê: *"se esse trade ganhar, ainda foi um trade ruim, porque está
> reforçando comportamento errado."* Vitória com processo C é o resultado mais
> perigoso que existe, e um journal que só grava win/loss registra ela como
> sucesso. A métrica que importa não é winrate — é frequência de C.

Depois, as quatro perguntas de disciplina, obrigatórias, sem default marcado:
respeitei o plano · antecipei o stop · fiz parcial emocional · mudei o alvo.

---

## 8. `cockpit/scripts/verify.ts`

Manter os 19 casos. Acrescentar:

**Sincronia das duas estratégias** (substitui o caso de sincronia atual): para
cada uma das duas, comparar `copa/strategies/<id>.json` com a constante em
`cockpit/data/strategies.ts` — mesmo conjunto de ids, mesmo tipo, mesmo peso,
mesmo label. Divergência falha.

**Soma dos pesos**: `reversao_htf` → 7 KILL, 6 PONTO, soma 100.
`continuidade_tendencia` → 6 KILL, 6 PONTO, soma 100.

**`avaliarLimitesDia`:**

1. 0 perdas, 0 operações, sem loss → liberado
2. 2 perdas, 3 operações, loss há 40 min → liberado
3. **3 perdas** → bloqueado, motivo cita pregão encerrado
4. **5 operações** → bloqueado, motivo cita limite de operações
5. 1 perda, loss há 10 min → bloqueado, motivo cita 20 min restantes
6. 1 perda, loss há 31 min → liberado
7. loss há exatamente 30 min → liberado (fronteira inclusiva)
8. 3 perdas **e** 5 operações → bloqueado com **os dois** motivos

**`avaliarGate` integrado:**

9. 7 KILL, 80 pontos, 10:30, limites liberados → liberado
10. mesmo caso com `tradeAbertoId` não nulo → bloqueado
11. mesmo caso com 3 perdas → bloqueado citando o pregão encerrado

Total esperado: **19 + 11 = 30 casos**.

---

## Critério de aceite

```bash
cd cockpit && npx tsc --noEmit
cd .. && npx tsx cockpit/scripts/verify.ts
cd cockpit && npm run build
cd .. && git diff --stat
cd .. && python -c "from copa.strategies_config import load_all; [print(s['id'], len([i for i in s['checklist'] if i['tipo']=='KILL']), sum(i['peso'] for i in s['checklist'] if i['tipo']=='PONTO')) for s in load_all()]"
```

1. `tsc` limpo
2. `verify.ts` 30 casos OK, exit 0
3. build compila
4. `git diff --stat` lista exatamente os 10 arquivos
5. Python imprime `reversao_htf 7 100` e `continuidade_tendencia 6 100`

**Teste manual, obrigatório — é o único que prova que grava:**

1. `npm run dev`, abrir `/checklist` → redireciona para `/login`
2. Entrar
3. Escolher REVERSÃO HTF, marcar os 7 KILL e PONTO suficientes, preencher o
   trade, ABRIR ORDEM
4. `select id, strategy_id, score, janela from copa_trades order by created_at desc limit 1;` → 1 linha com `reversao_htf`
5. `select count(*) from copa_trade_items where trade_id = '<id>';` → **13**
6. Trocar para CONTINUIDADE e conferir que o checklist mudou para 6 KILL
7. Fechar o trade com MANUAL / BATEU_ALVO / execução C → conferir que `pnl_plano`
   ficou diferente de `pnl_real` e que `notas` começa com `[EXEC:C]`

Colar a saída dos passos 4, 5 e 7.

---

## Armadilhas desta task

**Data do dia pelo navegador.** `toISOString().split("T")[0]` devolve o dia
seguinte depois das 21h no Brasil. A sessão iria para a data errada e o contador
zeraria no meio da noite. Sempre `America/Sao_Paulo`.

**Trade gravado sem os itens.** Se o insert dos itens falhar e o trade ficar, a
estatística mente para sempre. Apagar o trade e propagar.

**Erro engolido.** `catch` que só faz `console.error` e segue faz o operador achar
que gravou.

**Reescrever os textos das estratégias.** Os labels e ajudas vêm dos JSONs,
palavra por palavra. São as palavras do operador. "Melhorar" a redação quebra o
verify e apaga o sentido.

**Misturar os checklists das duas estratégias.** Cada uma tem os seus ids e
pesos; o snapshot tem que ser o da estratégia escolhida.

**Quebrar as chamadas existentes de `avaliarGate`.** Parâmetros novos são
opcionais e vão no fim.
