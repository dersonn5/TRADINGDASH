# SPEC — Calendário de resultados

> **Executor:** Gemini. **Revisor:** Claude (lê o `git diff`, não o relatório). **Aprovação:** Anderson.
> Escrita em 19/10/2026. Referência visual: calendário mensal com o resultado de cada dia e,
> à direita, o acumulado de cada semana (prints enviados pelo Anderson).

Antes de abrir código, ler: `CHECKPOINT.md` (raiz), `cockpit/AGENTS.md` (Next 16: ler
`node_modules/next/dist/docs` antes de usar API do Next), `lib/visao-geral.ts` (o cartão
"Calendário" que já existe na Visão Geral usa a mesma lógica de semanas), `components/v2/estilos.ts`
e `components/layout/shell.tsx`. Cada task tem **Verify**; sem o Verify rodado nesta sessão,
a task não está pronta.

---

## 1. PRD

### 1.1 Problema
A Visão Geral tem um calendário pequeno (só a cor e o R$ do dia). O operador quer ver o mês
inteiro como um diário de resultados: quantos trades, quanto ganhou ou perdeu, quantos ganhos e
perdas em cada dia, e **o acumulado de cada semana ao lado**, para saber quantas semanas fecha
no positivo.

### 1.2 Objetivo
Uma tela **Calendário** que mostra, para o mês escolhido:
- cada dia de pregão com o resultado do dia;
- uma coluna à direita com o resultado de cada semana;
- o total do mês no topo.

### 1.3 Escopo — entra
- **FR-001** Página nova `/calendario`, no menu lateral no grupo **Registro**, entre
  "Histórico" e "Estratégias". Ícone de calendário no mesmo estilo dos outros (`svgProps`).
- **FR-002** Cabeçalho: rótulo pequeno "Calendário · resultado por dia", título com o mês
  ("Outubro 2026"), setas ‹ › para mês anterior/seguinte (não passa do mês atual) e um resumo:
  `R$ +1.234 no mês · 10 ganhos · 12 perdas · 3 de 4 semanas positivas`.
- **FR-003** Grade de **segunda a sexta** (5 colunas; a B3 não abre no fim de semana — difere do
  print, que mostra sábado com R$ 0). Uma linha por semana do mês. Cada célula de dia mostra:
  - número do dia (canto superior esquerdo);
  - selo "N trades" (canto superior direito), só se houve trade;
  - **resultado do dia em R$**, grande, com a cor do sinal (ver §2);
  - abaixo: **R do dia** (soma dos R dos trades, ex.: `+1,8R`) e `2W · 3L`.
  - **No lugar do % do print vai o R**: o cockpit não guarda o capital da conta, então % não
    existe aqui. Não inventar capital.
  - Dia sem trade: "R$ 0" apagado (`var(--tx3)`), sem selo.
  - Dia de outro mês (preenchendo a semana): número apagado, célula vazia, opacidade baixa.
  - Dia futuro: apagado. Feriado da B3 (`FERIADOS_B3` em `lib/alertas.ts`): texto "Feriado".
  - Hoje: borda `var(--ac)`.
- **FR-004** **Coluna de semanas** à direita da grade, um cartão por linha, alinhado com ela:
  - "Semana N" (N = 1, 2, 3… dentro do mês);
  - resultado da semana em R$ (cor do sinal) e R da semana;
  - `X trades` e um selo `WR 50% · PF 1,63` (WR = ganhos ÷ trades; PF = soma dos ganhos ÷
    soma das perdas, "—" sem perda; semana sem trade: "0 trades" e selo apagado `WR — · PF —`).
- **FR-005** Clicar num dia com trades abre, **abaixo da grade**, a lista dos trades daquele dia:
  hora de entrada, sigla do setup (`SIGLAS` de `lib/metricas.ts`), compra/venda, R, R$ e
  "No plano"/"Desvio" (`temDesvio`). Mesmo visual das linhas do Histórico (`app/trades/page.tsx`).
  Clicar de novo fecha.
- **FR-006** Rodapé do mês: `Total do mês: R$ +1.234 · +5,2R · 22 trades · WR 45% · PF 1,40`.
- **FR-007** Funciona no **modo demonstração** (`?demo=1`) sem mudança extra: os dados vêm de
  `listarTradesDoMes`, que já devolve trades fictícios no demo.

### 1.4 Anti-escopo — NÃO entra
- Mudança no banco, nova tabela ou migração.
- Percentual sobre capital (não existe o dado).
- Editar ou lançar trade por esta tela.
- Mexer no cartão "Calendário" da Visão Geral (continua como está).
- Sábado e domingo.
- Commit ou push sem o Anderson pedir.

### 1.5 Critério de sucesso
- Com `?demo=1`, setembro/2026 mostra os dias com trade, as semanas à direita batendo com a
  soma dos dias, e o total do mês igual ao da Visão Geral do mesmo mês.
- O teste do modelo (TASK-102) passa.
- Tela sem dados (mês vazio) mostra a grade inteira zerada, sem quebrar (o operador gosta das
  telas "zeradas" — ver CHECKPOINT).

---

## 2. Decisões técnicas

| Decisão | Escolha | Por quê |
|---|---|---|
| Onde fica a lógica | **função pura** `montarCalendarioMes(trades, ano, mes, hojeIso)` em `lib/calendario-resultados.ts` | testável no `verify.ts`, como `montarVisaoGeral`. **Não** usar `lib/calendario.ts` (é o calendário econômico) |
| Dados | `listarTradesDoMes(ano, mes)` de `lib/copa-db.ts` (só FECHADOS) | já filtra por data da sessão e já tem o demo |
| R do trade | `calcularRTrade(pontos_real, calcularRiscoTrade(entrada, stop))` de `lib/metricas.ts` | mesma conta da Visão Geral e do Histórico |
| Semanas | segunda a sexta; a semana começa na segunda da semana do dia 1 (se o dia 1 cair no fim de semana, começa na segunda seguinte) | igual ao cartão da Visão Geral (`lib/visao-geral.ts`, bloco "Calendario") — copiar a regra |
| Cores | ganho: `var(--actx)` no texto, fundo `var(--acs)`; perda: `var(--negtx)`, fundo `color-mix` leve de `var(--neg)`; zero: `var(--tx3)` | paleta monocromática do cockpit: perda é ciano apagado + "−", nunca vermelho fixo (a classe `perda-vermelha` cuida disso) |
| Formatação | `formatarBRL`, `formatarR`, `formatarPct` de `lib/metricas.ts`; números com `tabular-nums` | consistência com as outras telas |
| Estilo | `CARD`, `LBL`, `H2`, `chip`, `BOTAO_SECUNDARIO` de `components/v2/estilos.ts`; fonte Sora (já global) | as telas v2 seguem o design de `design/v2/*.dc.html` |
| Largura | grade 5 colunas + coluna de semanas (~220 px). Abaixo de 1100 px, o cartão da semana vai para baixo da linha da semana | não pode ter rolagem horizontal |
| Fuso | datas sempre em America/Sao_Paulo (`getDataSaoPaulo` para "hoje") | `toISOString()` do navegador vira o dia seguinte depois das 21h |

Tipo de saída da função (sugestão — pode ajustar nomes, não a ideia):

```ts
interface DiaCal { iso: string; dia: number; doMes: boolean; futuro: boolean; feriado: boolean; hoje: boolean;
  trades: number; ganhos: number; perdas: number; pnl: number; r: number; }
interface SemanaCal { n: number; dias: DiaCal[]; trades: number; ganhos: number; perdas: number;
  pnl: number; r: number; wr: number | null; pf: number | null; }
interface CalendarioMes { semanas: SemanaCal[]; total: { trades: number; ganhos: number; perdas: number;
  pnl: number; r: number; wr: number | null; pf: number | null }; semanasPositivas: number; semanasComTrade: number; }
```
Ganho = trade com `pnl_real > 0`; perda = `pnl_real < 0`; zero a zero não conta em nenhum.

---

## 3. Roadmap

### Fase 1 — Modelo (lógica pura, com teste)
- [ ] **TASK-101** — `lib/calendario-resultados.ts` com `montarCalendarioMes`.
  - Files: `lib/calendario-resultados.ts`
  - Verify: `npx tsc --noEmit` limpo.
- [ ] **TASK-102** — Testes em `scripts/verify.ts` (bloco novo "Calendário de resultados"):
  - outubro/2026 começa na **quinta 01/10** → a 1ª semana tem seg 28/09, ter 29/09 e qua 30/09
    como `doMes: false`; o mês tem 5 semanas;
  - com 3 trades fictícios no mesmo dia (+100, −50, +30 R$), o dia soma `pnl 80`, `2W · 1L`, e a
    semana e o total batem;
  - PF de uma semana sem perda é `null`; WR de semana sem trade é `null`;
  - mês sem trade: semanas existem, tudo zerado, `semanasComTrade = 0`;
  - 12/10/2026 (feriado) vem com `feriado: true`.
  - Files: `scripts/verify.ts`
  - Verify: `npx tsx scripts/verify.ts` termina com "✅ Todos os testes passaram com sucesso!".

### Fase 2 — Tela
- [ ] **TASK-201** — `app/calendario/page.tsx`: carrega `listarTradesDoMes`, seletor de mês,
  cabeçalho (FR-002), grade + coluna de semanas (FR-003, FR-004), rodapé (FR-006). Estado de
  carregamento igual às outras páginas.
  - Files: `app/calendario/page.tsx` (e, se quiser separar, `components/v2/calendario-mes.tsx`)
  - Verify: `npx tsc --noEmit` limpo; `npm run dev` e abrir `/calendario?demo=1`.
- [ ] **TASK-202** — Detalhe do dia ao clicar (FR-005).
  - Files: os mesmos da TASK-201
  - Verify: no demo, clicar num dia com trade mostra a lista; a soma em R$ da lista = valor da célula.
- [ ] **TASK-203** — Item "Calendário" no menu lateral (FR-001).
  - Files: `components/layout/shell.tsx`
  - Verify: o item aparece no grupo Registro, fica ativo em `/calendario` e funciona com a barra
    recolhida (só o ícone, com `title`).

### Fase 3 — Fechamento
- [ ] **TASK-301** — `npx tsc --noEmit`, `npx tsx scripts/verify.ts` e `npm run build` limpos
  (parar o `npm run dev` antes do build). Conferência visual com `?demo=1`, nos temas escuro e
  claro, em 1440 px e em ~900 px de largura: sem rolagem horizontal, semanas alinhadas às linhas.
  O total de setembro/2026 no Calendário é igual ao da Visão Geral de setembro.
  - Para ver a tela sem login: desvio temporário no `components/auth-gate.tsx` e **remover antes
    de terminar** (o `git diff` desse arquivo tem de vir vazio).
- [ ] **TASK-302** — Atualizar `CHECKPOINT.md` (seção "Pronto e verificado": a tela e a prova).
  Não fazer commit nem push: o Anderson pede.
