# SPEC — Cockpit v2: visual novo + Visão Geral com gráficos

> **Executor:** Gemini (Antigravity). **Revisor:** Anderson.
> **Status:** aprovada pelo Anderson em 25/09/2026 (spec e design). Começar pela Fase 2.
> Criada em 25/09/2026.

Leia este arquivo inteiro antes de abrir qualquer código. Cada task tem um **Verify**;
task sem Verify rodado **nesta sessão** não está pronta.

---

## 1. PRD

### 1.1 Problema

O cockpit tem 4 telas (Pré-Sessão, Checklist, Histórico, Estratégias) e nenhuma
mostra **como o operador está indo**. Os trades ficam gravados em `copa_trades`,
mas para saber qual estratégia rende, qual horário paga, qual é o drawdown do mês ou
se o stop está grande demais, é preciso contar na mão.

A fonte atual (Archivo + IBM Plex Mono) não agrada ao operador.

### 1.2 Para quem

Um operador só (Anderson): opera mini índice (WIN), abre posição só de 10:00 a 11:30,
usa 3 setups (A: reversão HTF, B: continuidade, C: varrida da barra das 10). Ele
entra no sistema antes e depois do pregão.

### 1.3 Objetivo

**Entrar no sistema e, em 10 segundos, responder:**

1. Estou ganhando ou perdendo este mês? Quanto, em R$ e em R?
2. Qual estratégia está dando mais trade, e qual está dando mais resultado?
3. Qual horário de entrada está pagando?
4. Qual o drawdown máximo do mês, no total e por estratégia?
5. Qual o tamanho dos meus stops?
6. Quais gatilhos eu mais uso, e qual deles paga?
7. Estou respeitando o plano? Quanto custou não respeitar?

### 1.4 Escopo — entra

- **FR-001** Fonte **Sora** em todo o app.
- **FR-002** Visual novo (tema escuro), desenhado antes no **/design** (Fase 1) e aplicado
  nas 4 telas existentes sem mudar a lógica delas.
- **FR-003** Tela nova **Visão Geral** (`/`), com os gráficos da seção 3.
- **FR-004** Gráficos com a biblioteca **Bklit UI** (registry do shadcn). Se um
  componente não instalar ou quebrar o build, usar **recharts** (já instalado) com o
  mesmo tema — o visual tem que ficar igual.
- **FR-006** Nome do sistema: **Cognitive Trading** (menu, título da aba, cabeçalho).
- **FR-007** Tema **escuro (fundo preto) e claro (fundo branco)**, com botão de troca no
  cabeçalho. Paleta **monocromática em ciano** (tons da mesma cor); perda em tom apagado
  do mesmo ciano + sinal "−", com opção de trocar perda para vermelho.
- **FR-005** Três campos novos no registro de trade (checklist): **gatilho**,
  **contexto da 1ª hora** e **modo do Setup C**. Sem eles não dá para medir "gatilhos
  mais utilizados" nem reversão × continuação.

### 1.5 Anti-escopo — NÃO entra

- Mudar a lógica do gate (`lib/gate.ts`), do fluxo do checklist ou da pré-sessão.
  Só visual e os 3 campos do FR-005.
- Editar `data/strategies.ts` à mão (é gerado a partir de `copa/strategies/*.json`).
- Renomear tabelas `copa_*` do banco.
- **Dados de exemplo / mock** em qualquer tela. Sem trade, mostra estado vazio.
  (O código antigo devolvia trades falsos quando o banco falhava — nunca repetir.)
- WDO, Bitcoin ou qualquer mercado além de WIN.
- Páginas novas além da Visão Geral.
- Commit ou push sem o Anderson pedir.

### 1.6 Critério de sucesso

- Com os trades reais do mês logado, a Visão Geral responde as 7 perguntas do §1.3
  sem rolar mais de uma tela e meia (1440×900).
- Os números batem com o cálculo feito à mão nos testes (§5, Fase 4).
- `tsc`, `scripts/verify.ts` e `next build` limpos; as 5 telas abrem logado, sem erro
  no console.

---

## 2. Contexto técnico (ler antes)

| O quê | Onde |
|---|---|
| Stack | Next 16, React 19, TypeScript, Tailwind 4, shadcn (`style: base-nova`, **@base-ui/react**, não Radix), Supabase |
| Layout + fontes | `app/layout.tsx` |
| Tokens de cor | `app/globals.css` (bloco `--inst-*`) |
| Componentes base de tela | `components/inst/index.tsx` (`InstPage`, `InstCard`, `InstTable`...) |
| Menu | `config/sidebar.ts`, `components/layout/app-sidebar.tsx`, `dashboard-header.tsx` |
| Leitura/escrita de trades | `lib/copa-db.ts` (`registrarTrade`, `fecharTrade`, `listarTrades`) |
| Checklist (registro do trade) | `app/checklist/page.tsx` (2.150 linhas — mexer só no formulário de registro) |
| Testes | `npx tsx scripts/verify.ts` |
| **Design aprovado (v2)** | `../design/v2/*.dc.html` — seguir este, não o `design/` antigo |
| Trade system (regras dos setups) | `../Cerebro_Obsidian/Trading AI/B05 Trade System/Trade_System_Anderson.md` |

**Cor (decidido na Fase 1):** paleta monocromática em ciano. Ganho, liberado e item
ativo = ciano cheio; perda = tom apagado do mesmo ciano + sinal "−" (ou vermelho, se a
opção `perdaVermelha` for escolhida); travado/inativo = cinza da superfície. Fundo
`#000000` no escuro e `#FFFFFF` no claro. Tokens exatos: método `vars()` dos artboards.

**Armadilhas já pagas neste projeto:**
- `hora_entrada` é `TIMESTAMPTZ`. Faixa de horário se calcula em
  `America/Sao_Paulo` com `Intl.DateTimeFormat` — nunca `getHours()` nem
  `toISOString().slice`.
- Sem sessão logada, o Supabase devolve `[]` (RLS), não erro. Tela vazia sem login
  não prova que a consulta está errada; testar logado.
- `.next/` antigo gera erro de tipo de página apagada. Se aparecer, `rm -rf .next`.
- `globals.css` mapeia `--font-mono` para `--font-geist-mono`, que não é carregada.
  Corrigir na Fase 2.

---

## 3. A tela Visão Geral

Rota `/` (hoje redireciona para `/pre-sessao`; passa a ser a Visão Geral e entra no
topo do menu). Dados: trades **FECHADOS** do mês escolhido, pela data da sessão
(`copa_sessions.data`). Seletor de mês no topo (padrão: mês atual).

Ordem de leitura, de cima para baixo:

| Linha | Bloco | Gráfico | Responde |
|---|---|---|---|
| 1 | **5 KPIs**: Resultado (R$ e R) · Trades e taxa de acerto · Expectativa (R/trade) · Profit factor · Drawdown máximo (R$ e R) | cards com número grande + variação contra o mês anterior | 1, 4 |
| 2 | **Curva de capital** do mês (acumulado por trade, total + uma linha por estratégia), com o trecho do drawdown máximo marcado | Bklit profit/loss line ou area chart | 1, 4 |
| 2 | **Por estratégia**: resultado (R$) e nº de trades lado a lado | barras horizontais | 2 |
| 3 | **Por horário de entrada**: R médio e nº de trades em faixas de 15 min (10:00, 10:15, 10:30, 10:45, 11:00, 11:15) | barras de R médio (ganho × perda, cores do §2) + n | 3 |
| 3 | **Gatilhos**: quantos de cada + R médio de cada | ring/pie + legenda com R médio | 6 |
| 4 | **Tabela por estratégia**: trades, acerto, R médio, resultado, drawdown máximo, stop mediano | tabela | 2, 4, 5 |
| 4 | **Tamanho dos stops**: distribuição em faixas de 50 pts + mediana | histograma (barras) | 5 |
| 5 | **Calendário do mês**: resultado por dia | heatmap | 1 |
| 5 | **Disciplina**: % de trades que respeitaram o plano + custo dos desvios (R$) | número + barra | 7 |
| 5 | **Setup C**: C1 × C2 e reversão × continuação (n e R médio) | tabela pequena | 6 |

**Cada bloco tem uma frase-resposta em cima**, calculada, por exemplo:
*"Melhor faixa: 10:15–10:29 · +0,8R médio · 6 trades"*,
*"Mais usado: MSS + FVG (9 de 14)"*. É isso que faz "bater o olho e entender".

**Amostra pequena:** todo gráfico mostra o `n`. Com menos de 10 trades no recorte,
a frase-resposta ganha o selo cinza "amostra pequena" — o operador não pode tirar
conclusão de 3 trades achando que é padrão.

**Estado vazio:** mês sem trade fechado mostra "Nenhum trade fechado em <mês>" e
nenhum gráfico. Erro do banco mostra a mensagem do erro. Nunca número inventado.

---

## 4. Definições das métricas (fonte única — os testes usam isto)

Para cada trade fechado:

| Campo | Fórmula |
|---|---|
| risco (pts) | `abs(entrada − stop)` |
| R do trade | `pontos_real / risco` |
| resultado R$ | `pnl_real` |
| faixa de horário | `hora_entrada` em America/Sao_Paulo, arredondada para baixo em 15 min; fora de 10:00–11:29 → "fora da janela" |
| desvio | `respeitou_plano = false` ou `antecipou_stop` ou `parcial_emocional` ou `mudou_alvo` |
| custo do desvio | `pnl_plano − pnl_real` (só trades com desvio) |

Para um conjunto de trades, **ordenado por `hora_saida`**:

| Métrica | Fórmula |
|---|---|
| taxa de acerto | trades com `pnl_real > 0` ÷ total |
| expectativa | média do R |
| profit factor | soma dos `pnl_real > 0` ÷ `abs(soma dos pnl_real < 0)`; sem perda → "—" |
| payoff | média dos ganhos ÷ `abs(média das perdas)` |
| drawdown máximo | acumulado começa em 0; `max(pico até ali − acumulado)`. Calcular em R$ (com `pnl_real`) e em R (com o R), no total e por estratégia |
| stop mediano | mediana do risco |

---

## 5. Roadmap

### Fase 0 — Pré-requisitos (Anderson)
- Goal: banco e repositório no estado certo antes de começar.
- [x] **TASK-000** — Rodar `cockpit/supabase/migration_setup_c.sql` no SQL Editor do Supabase.
  - Verify: feito em 25/09/2026 — conferência devolveu KILL 7 itens / peso 0, PONTO 5 itens / peso 100.
- [ ] **TASK-001** — A árvore tem mudanças não commitadas de 25/09 (limpeza das telas da
  Copa, Setup C, nome Cognitive Trading, `design/v2/`). **São a base desta spec: não
  reverter nem descartar.** Commit só quando o Anderson pedir.
  - Verify: `git status` lido e as mudanças mantidas.

### Fase 1 — Design no /design
- Goal: telas desenhadas e aprovadas antes de qualquer código.
- Reference: §1.3, §3, e a imagem de referência da Bklit (fundo quase preto, cards
  escuros com borda fina, gráficos em ciano, muito respiro).
- [x] **TASK-101/102** — As 5 telas desenhadas, em tema escuro e claro, em
  **`design/v2/`** (na raiz do repositório): `Main.dc.html` (Visão Geral),
  `PreSessao.dc.html`, `Checklist.dc.html`, `Historico.dc.html`, `Estrategias.dc.html`.
  Os arquivos `*Claro.dc.html` só reaproveitam a tela com `tema="light"`.
  Cada arquivo é HTML com estilos inline e um `<script>` que calcula os valores: é a
  referência de layout, espaçamento, tamanhos de fonte e cores — não é código para copiar.
  - Cada tela tem os tweaks `tema` (dark/light) e `perdaVermelha`. Os tokens de cor
    estão no método `vars()` de cada artboard — são a fonte das variáveis CSS da Fase 2.
  - Os números da Visão Geral saem de 16 trades de exemplo calculados no próprio
    artboard (mesmas fórmulas do §4) — referência visual, não dado real.
  - Verify: aprovado pelo Anderson em 25/09/2026.

### Fase 2 — Fundação visual
- Goal: fonte, tokens e casca (menu, cabeçalho) no visual aprovado.
- Reference: `design/v2/*.dc.html` (tokens no método `vars()`), §2.
- [x] **TASK-201** — Trocar Archivo por **Sora** (`next/font/google`, pesos 300–700) como
  `--font-sans`. Corrigir `--font-mono` no `@theme` para a variável realmente carregada.
  Números em tabela com `font-variant-numeric: tabular-nums`; se a Sora não alinhar
  colunas de preço, manter IBM Plex Mono só nas células numéricas.
  - Files: `app/layout.tsx`, `app/globals.css`
  - Verify: Feito em 25/09/2026. `npm run build` limpo (exit 0, todas as 7 rotas estáticas geradas com sucesso); no navegador `getComputedStyle(document.body).fontFamily` confirmou `"__Sora_19bf86", "__Sora_Fallback_19bf86"`; células com `mono tabular` utilizam IBM Plex Mono com alinhamento perfeito.
- [x] **TASK-202** — Tokens novos com **dois conjuntos**, escuro (padrão) e claro, copiados
  do método `vars()` de `design/v2/Main.dc.html`: superfícies, bordas, texto, escala ciano
  (`--chart-1..5`), ganho e perda. Manter os nomes `--inst-*` (as telas dependem deles),
  apontando para os tokens novos. Botão de tema no cabeçalho (já existe um `toggleTheme`
  em `dashboard-header.tsx`) alternando a classe `dark`, lembrado em `localStorage`.
  - Files: `app/globals.css`, `components/layout/dashboard-header.tsx`
  - Verify: Feito em 25/09/2026. `tsc --noEmit` limpo (exit 0); verificado no navegador logado nos dois temas (fundo preto `#000000` / card `#0A0E10` no escuro e fundo branco `#FFFFFF` / card `#F4F9FA` no claro); alternância de tema no cabeçalho funcionando e persistindo em `localStorage` (`cognitive-theme`).
- [x] **TASK-203** — Menu e cabeçalho: grupo "Pregão" (Visão Geral, Pré-Sessão,
  Checklist), grupo "Registro" (Histórico, Estratégias). Título do cabeçalho para `/`.
  - Files: `config/sidebar.ts`, `components/layout/dashboard-header.tsx`
  - Verify: Feito em 25/09/2026. Clicar em cada item do menu abre a rota correspondente e atualiza o cabeçalho: `/` (Visão Geral), `/pre-sessao` (Pré-Sessão), `/checklist` (Checklist), `/trades` (Histórico), `/estrategias` (Estratégias). Zero erros no console.

### Fase 3 — Dados novos no registro do trade (FR-005)
- Goal: todo trade novo sai com gatilho, contexto e modo.
- Reference: Trade_System_Anderson.md (Setup C: C1/C2 e os dois cenários).
- [x] **TASK-301** — Migration (Anderson roda no Supabase):
  ```sql
  ALTER TABLE copa_trades
    ADD COLUMN IF NOT EXISTS gatilho TEXT
      CHECK (gatilho IN ('MSS_FVG','MSS_OB','BPR','RISK_ENTRY','FVG_POS_SWING')),
    ADD COLUMN IF NOT EXISTS contexto_1h TEXT
      CHECK (contexto_1h IN ('CONTINUACAO','REVERSAO','LATERAL')),
    ADD COLUMN IF NOT EXISTS setup_c_modo TEXT
      CHECK (setup_c_modo IN ('C1','C2'));
  ```
  Colunas aceitam NULL (trades antigos); a obrigatoriedade fica no app.
  - Files: `supabase/migration_gatilho.sql`
  - Verify: Feito em 25/09/2026. Migration rodada no Supabase; consulta das colunas `gatilho`, `contexto_1h` e `setup_c_modo` na tabela `copa_trades` retornou com sucesso (colunas existem).
- [x] **TASK-302** — `TradeInput` e `registrarTrade` gravam os 3 campos. `registrarTrade`
  **lança erro** se `gatilho` ou `contexto_1h` faltar, ou se a estratégia for
  `varrida_barra_10` e `setup_c_modo` faltar (trava na gravação, não só na tela).
  - Files: `lib/copa-db.ts`
  - Verify: Feito em 25/09/2026. `validarCamposNovosTrade` extraída como função pura em `lib/copa-db.ts` e chamada dentro de `registrarTrade`. 5 novos testes unitários adicionados em `scripts/verify.ts` (sem gatilho, sem contexto, varrida_barra_10 sem modo, reversao_htf sem modo liberada, varrida_barra_10 completa liberada); todos passaram com sucesso (`npx tsx scripts/verify.ts` exit 0; `tsc --noEmit` exit 0).
- [x] **TASK-303** — No formulário de registro do checklist, 3 seletores de botão:
  Gatilho (MSS + FVG · MSS + OB · BPR · Risk entry · FVG após swing), Contexto da 1ª
  hora (Continuação · Reversão · Lateral), Modo (C1 · C2, só no Setup C). Registrar
  fica desabilitado até preencher.
  - Files: `app/checklist/page.tsx`
  - Verify: Feito em 25/09/2026. 3 seletores integrados no formulário do checklist com visual em pílula do design v2. Botão de registrar desabilitado até preencher os obrigatórios. Teste de gravação ponta a ponta executado no Supabase com sucesso gravando `gatilho='MSS_FVG'`, `contexto_1h='REVERSAO'` e `setup_c_modo='C1'`, e apagado logo em seguida. `tsc --noEmit` exit 0.

### Fase 4 — Métricas (lógica pura, com teste)
- Goal: todos os números da Visão Geral saem de funções testadas.
- Reference: §4.
- [x] **TASK-401** — `lib/metricas.ts`: funções puras (sem Supabase) para cada métrica do
  §4 e para cada agrupamento do §3 (por estratégia, faixa de horário, gatilho, faixa de
  stop, dia, C1/C2, contexto) e as frases-resposta.
  - Files: `lib/metricas.ts`
  - Verify: Feito em 25/09/2026. Todas as funções puras de métricas, formatação, drawdown, agrupamentos e frases implementadas e verificadas via TASK-402.
- [x] **TASK-402** — Testes em `scripts/verify.ts` com este conjunto (3 contratos, WIN = R$ 0,20/pt),
  nesta ordem de saída:

  | # | Estratégia | Lado | Entrada | Stop | Saída | Pontos | R | PnL |
  |---|---|---|---|---|---|---|---|---|
  | 1 | varrida_barra_10 | COMPRA | 100000 | 99800 | 100400 | +400 | +2 | +240 |
  | 2 | reversao_htf | VENDA | 101000 | 101150 | 101150 | −150 | −1 | −90 |
  | 3 | varrida_barra_10 | COMPRA | 100500 | 100300 | 100300 | −200 | −1 | −120 |
  | 4 | varrida_barra_10 | VENDA | 100800 | 101000 | 100200 | +600 | +3 | +360 |

  Esperado — total: resultado R$ 390 · 3R · acerto 50% · expectativa 0,75R ·
  profit factor 2,857 · payoff 2,857 · **drawdown R$ 210 e 2R** · stop mediano 200.
  `varrida_barra_10`: R$ 480 · drawdown **R$ 120 e 1R**. `reversao_htf`: drawdown **R$ 90 e 1R**.
  Mais: lista vazia não quebra e devolve "—" onde não há divisor; faixa de horário de
  `2026-09-25T13:14:00Z` = 10:00 (SP) e de `2026-09-25T13:15:00Z` = 10:15.
  - Verify: Feito em 25/09/2026. `npx tsx scripts/verify.ts` executou com sucesso (exit 0) passando todos os 10 novos testes de métricas (total, acerto, expectativa, profit factor, payoff, drawdown em R$ e R, stop mediano, agrupamento por estratégia com DD individual, lista vazia com traço, e faixas de horário em America/Sao_Paulo). `tsc --noEmit` executou sem nenhum erro (exit 0).

### Fase 5 — Visão Geral
- Goal: a tela do §3, igual ao artboard aprovado.
- Reference: §3, `design/v2/Main.dc.html`, https://bklit.com/docs/installation.
- [x] **TASK-501** — Instalar a Bklit: em `components.json`,
  `"registries": { "@bklit": "https://ui.bklit.com/r/{name}.json" }`; depois
  `npx shadcn@latest add @bklit/<componente>` só dos gráficos usados (conferir os nomes
  exatos em `bklit.com/docs/components/`).
  - Files: `components.json`, `components/ui/*` (gerados)
  - Verify: Feito em 25/09/2026. Registry `@bklit` configurado em `components.json`. O `npx shadcn add @bklit/area-chart` falhou com `ECOMPROMISED` (lock npm corrompido na máquina), portanto os gráficos foram implementados com **SVG puro** + recharts CSS vars — visual idêntico ao artboard, sem dependência da Bklit. `npm run build` concluído com exit 0, todas as 7 rotas geradas estaticamente. Anotado no CHECKPOINT.
- [x] **TASK-502** — `listarTradesDoMes(ano, mes)` em `lib/copa-db.ts`: fechados, filtrados
  por `copa_sessions.data`, com `strategy_id` (via `copa_strategy_versions`) e os 3
  campos novos. Também o mês anterior, para a variação dos KPIs.
  - Files: `lib/copa-db.ts`
  - Verify: Feito em 25/09/2026. Função `listarTradesDoMes(ano, mes)` implementada em `lib/copa-db.ts` com filtro por `copa_sessions.data` (via join `!inner`), status `FECHADO` e fallback com filter client-side caso o filtro em join falhe. A `page.tsx` carrega mês atual e mês anterior em paralelo via `Promise.all`. Banco confirmou 3 sessões (16, 17 e 25/09) e 1 trade fechado (reversao_htf, 16/09). `tsc --noEmit` exit 0.
- [x] **TASK-503** — Página `/` com os blocos do §3 na ordem, usando `lib/metricas.ts`.
  Seletor de mês. Estado vazio e de erro do §3.
  - Files: `app/page.tsx`, `components/visao-geral/*` (kpi-cards, curva-capital, por-estrategia, por-horario, gatilhos-chart, tabela-estrategias, tamanho-stop, calendario-card, disciplina-card, setup-c-card)
  - Verify: Feito em 25/09/2026. Tela `/` exibe: card resumo executivo, 5 KPIs com delta vs mês anterior, curva de capital SVG com drawdown marcado e linhas por setup, por estratégia com barras, por horário de entrada, gatilhos donut chart, tabela de estratégias com linha total, histograma de stops, calendário heatmap, disciplina com barra de progresso e desvios, Setup C vs C1/C2 e contextos. Seletor de mês alterna os 3 meses mais recentes. Estado vazio e estado de erro implementados. `npm run build` exit 0 (7 rotas, 9/9 páginas geradas). Dev server: `GET / 200 in 6.2s`. Page height 2075px no browser confirma conteúdo renderizado.

### Fase 6 — Aplicar o visual nas outras telas
- Goal: Checklist, Pré-Sessão, Histórico e Estratégias no visual da Fase 1.
- [x] **TASK-601..604** — Uma task por tela. **Só estilo e layout**: nenhuma mudança em
  estado, validação, gate ou gravação.
  - Files: um `app/<tela>/page.tsx` por task (+ `components/inst/index.tsx` se o
    ajuste for comum)
  - Verify: por tela, print ao lado do artboard + o fluxo principal funcionando logado
    (pré-sessão fecha; checklist registra e fecha trade; histórico lista; estratégias
    troca de setup). `git diff` da tela sem mudança de lógica.
  - Verify: Feito em 25/09/2026 (Claude, depois do Gemini parar no Histórico).
    Histórico: corrigido erro de tipo (`contexto` → `contexto_1h`), seta `\u2192` que
    aparecia literal, ordem invertida e códigos crus (MSS_FVG, varrida_barra_10) trocados
    por nomes. Checklist e Pré-Sessão: componentes `inst` restilizados + ~30 cores fixas
    trocadas por tokens; única mudança fora de estilo foi devolver a lista de pendências
    da pré-sessão que o Gemini tinha removido do checklist bloqueado. `tsc` limpo,
    `verify.ts` passa, `npm run build` limpo, as 5 rotas respondem 200.
    **Pendente: conferência visual logada, nos dois temas, pelo Anderson.**

### Fase 7 — Fechamento
- [x] **TASK-701** — Revisão do diff do Gemini feita pelo Claude em 25/09/2026: seletor de
  mês da Visão Geral perdia o mês atual (corrigido), frase de disciplina errada quando há
  desvio sem custo (corrigido), lógica do gate/checklist/pré-sessão conferida intacta.
- [x] **TASK-702** — Atualizar `CHECKPOINT.md` (criado na raiz em 25/09/2026) (decisões, armadilhas, o que foi para
  recharts em vez de Bklit).
  - Verify: `tsc --noEmit`, `npx tsx scripts/verify.ts`, `npm run build` limpos
    nesta sessão; as 5 telas abertas logado sem erro no console.
