# SPEC — Alertas de voz do pregão

> **Executor:** Gemini ou Claude. **Revisor:** Anderson.
> **Status:** aprovada e implementada em 25/09/2026 (Claude). Falta só a prova ao vivo (TASK-502).
> Criada em 25/09/2026.

Leia `CHECKPOINT.md` (raiz) e este arquivo inteiro antes de abrir código. Cada task
tem **Verify**; sem Verify rodado nesta sessão, a task não está pronta.

---

## 1. PRD

### 1.1 Problema
O operador opera das 09:00 às 12:00 com o Profit na frente. A rotina tem horários
fixos (abertura do mini índice, do à vista, de Nova York, fim da janela de entrada,
hora de fechar) e notícias que movem o índice (Payroll, CPI, Fed). Hoje ele depende
de olhar o relógio e de lembrar da agenda que ele mesmo escreveu na pré-sessão.

### 1.2 Objetivo
Uma **voz feminina em português** avisa, sem ele precisar olhar a tela:
1. os marcos da rotina do pregão;
2. as notícias relevantes do dia, alguns minutos antes e na hora.

### 1.3 Escopo — entra
- **FR-001** Alertas da rotina do pregão (tabela §3.1), só em dia útil de pregão.
- **FR-002** Alertas de notícia a partir da **agenda da pré-sessão** (a que já existe:
  evento, horário, impacto): impacto **Alto** avisa 5 min antes e na hora; **Médio**
  só na hora; **Baixo** não fala.
- **FR-003** Agenda preenchida **automaticamente** com os eventos dos **EUA** de impacto
  Alto e Médio do dia (fonte §4). O operador revisa, apaga ou acrescenta eventos do
  Brasil à mão, como já faz.
- **FR-004** Resumo falado às 09:00: quantas notícias de impacto alto hoje e a primeira.
- **FR-005** Controle na barra lateral: liga/desliga, volume, escolha da voz, quais
  grupos falam (rotina / notícias), botão **Testar** e a lista dos alertas de hoje com
  "ouvir" em cada um.
- **FR-006** Um alerta nunca fala por cima de outro (fila).

### 1.4 Anti-escopo — NÃO entra
- Voz paga / API de TTS (ElevenLabs, OpenAI, Google Cloud). Fica para depois, se a voz
  do navegador não agradar.
- Alerta com o navegador fechado ou no celular (push). A aba do cockpit precisa estar
  aberta — é a rotina do operador das 09:00 às 12:00.
- Mudar gate, checklist, registro de trade ou a lógica de fechar a pré-sessão.
- Eventos do Brasil automáticos (a fonte gratuita não tem BRL). Brasil continua manual.
- Commit ou push sem o Anderson pedir.

### 1.5 Critério de sucesso
- Num dia útil, com o cockpit aberto e a voz ativada, às 10:00 a voz diz a frase da
  abertura do à vista, no máximo **60 s** depois do horário.
- Uma notícia Alta das 10:30 na agenda gera a fala das 10:25 e a das 10:30.
- Sábado, domingo e feriado da B3: nenhuma fala.

---

## 2. Decisões técnicas

| Decisão | Escolha | Por quê |
|---|---|---|
| Motor de voz | **Web Speech API** (`window.speechSynthesis`), `lang = "pt-BR"` | Grátis, sem chave, sem latência, funciona offline |
| Voz feminina | escolher na ordem: nome contém `Francisca` → `Thalita` → `Maria` → `Google português do Brasil` → qualquer `pt-BR` | Francisca/Thalita são as vozes neurais do **Edge** (as mais naturais); Maria é a do Windows; a do Google é a do Chrome. O operador pode trocar no controle |
| Desbloqueio | o navegador **não deixa falar sem um clique** do usuário na página. Ao abrir o cockpit com a voz ligada, mostrar um aviso "Clique para ativar a voz" até o primeiro clique | Política de autoplay do Chrome/Edge — sem isso a primeira fala falha em silêncio |
| Relógio | checagem a cada 1 s em `America/Sao_Paulo`; alerta dispara se `agora` estiver entre `hora` e `hora + 90 s` e ainda não disparou hoje | Aba em segundo plano tem timer limitado a ~1 por minuto pelo navegador; a janela de 90 s garante que não se perde o alerta |
| Registro do que já falou | `localStorage` com a chave do dia (`alertas-falados-AAAA-MM-DD`) | Recarregar a página não repete o alerta |
| Preferências | `localStorage` (`alertas-voz-config`) | São do aparelho, não do banco |
| Abertura de NY | **calcular** 09:30 em `America/New_York` e converter para São Paulo | NY abre 10:30 (horário de verão nos EUA, mar–nov) ou 11:30 (nov–mar). Nunca fixar 10:30 |

---

## 3. O que a voz fala

### 3.1 Rotina (horário de São Paulo, dia útil de pregão)

| Hora | Frase |
|---|---|
| 09:00 | "Bom dia. O pregão abriu. Até as dez, só observar e marcar." + resumo das notícias (FR-004) |
| 09:45 | "Faltam quinze minutos para a janela. A pré-sessão ainda não foi fechada." — **só se não foi fechada** |
| 09:55 | "Cinco minutos para a abertura do mercado à vista." |
| 10:00 | "Abertura do mercado à vista. Janela de entrada aberta." |
| NY − 5 min | "Cinco minutos para a abertura de Nova York." |
| NY | "Abertura de Nova York." |
| 11:00 | "Fim da janela nobre. A partir de agora, só com score oitenta." |
| 11:25 | "Cinco minutos para fechar a janela de entrada." |
| 11:30 | "Janela de entrada fechada. Agora é só gerenciar o que está aberto." |
| 11:55 | "Faltam cinco minutos. Ao meio-dia, feche o Profit." |
| 12:00 | "Fim do pregão do plano. Feche o Profit." |

Se o horário de NY coincidir com outro alerta (11:30 no horário de inverno dos EUA),
as duas frases saem em sequência, NY primeiro.

### 3.2 Notícias (da agenda da pré-sessão)

| Quando | Frase |
|---|---|
| 5 min antes (só Alto) | "Atenção: em cinco minutos, {evento}. Impacto alto." |
| Na hora (Alto e Médio) | "Saindo agora: {evento}." |
| Resumo das 09:00 | "Hoje tem {n} notícias de impacto alto. A primeira é {evento}, às {hora falada}." / "Hoje não tem notícia de impacto alto." |

Só alerta notícias entre **09:00 e 12:00**. Hora falada por extenso: 10:30 → "dez e
meia", 09:45 → "nove e quarenta e cinco".

### 3.3 Dias sem pregão
Sábado, domingo e feriados da B3 em `lib/alertas.ts` (lista 2026 abaixo, **conferir
com o calendário oficial da B3** antes de fechar a task):
01/01 · 16/02 · 17/02 · 03/04 · 21/04 · 01/05 · 04/06 · 07/09 · 12/10 · 02/11 · 20/11 ·
24/12 · 25/12 · 31/12.

---

## 4. Calendário automático (FR-003)

- **Fonte:** `https://nfs.faireconomy.media/ff_calendar_thisweek.json` (ForexFactory,
  gratuita, sem chave). Campos: `title`, `country`, `date` (ISO com fuso, ex.
  `2026-09-21T11:00:00-04:00`), `impact` (`High`/`Medium`/`Low`/`Holiday`),
  `forecast`, `previous`. Não tem Brasil.
- **Rota de servidor** `app/api/calendario/route.ts` (o navegador não pode chamar a
  fonte direto por CORS): busca o JSON com cache de **1 hora** (a fonte pede para não
  ser chamada toda hora), filtra `country === "USD"`, `impact` High ou Medium, data de
  **hoje em São Paulo**, e devolve
  `[{ evento, horario: "HH:MM" (São Paulo), impacto: "ALTO" | "MEDIO", titulo_original }]`.
  Em erro da fonte, devolve `{ erro }` com status 502 — nunca lista inventada.
- **Nome em português** para os eventos comuns (o resto fica com o título original):

  | Título | Fala |
  |---|---|
  | Non-Farm Employment Change | Payroll |
  | Unemployment Rate | taxa de desemprego americana |
  | CPI m/m / Core CPI m/m | CPI, inflação ao consumidor / núcleo do CPI |
  | PPI m/m / Core PPI m/m | PPI, inflação ao produtor / núcleo do PPI |
  | Core PCE Price Index m/m | núcleo do PCE |
  | Retail Sales m/m / Core Retail Sales m/m | vendas no varejo / núcleo das vendas no varejo |
  | Unemployment Claims | pedidos de seguro-desemprego |
  | Advance GDP q/q / Prelim GDP q/q / Final GDP q/q | PIB americano |
  | ISM Manufacturing PMI / ISM Services PMI | ISM da indústria / ISM de serviços |
  | JOLTS Job Openings | JOLTS, vagas de emprego |
  | ADP Non-Farm Employment Change | ADP, emprego privado |
  | Federal Funds Rate / FOMC Statement | decisão de juros do Fed |
  | FOMC Press Conference | entrevista do Powell |
  | Fed Chair Powell Speaks | fala do Powell |
  | Prelim UoM Consumer Sentiment | confiança do consumidor de Michigan |
  | Crude Oil Inventories | estoques de petróleo |

- **Na pré-sessão:** ao carregar, se a pré-sessão **não está fechada** e a agenda está
  **vazia**, preenche a agenda com a rota (auto-save normal). Botão "Importar dos EUA"
  no card Agenda para repetir à mão (acrescenta só o que ainda não está na agenda).
  Pré-sessão fechada: não mexe na agenda.

---

## 5. Roadmap

### Fase 1 — Motor (lógica pura, com teste)
- [x] **TASK-101** — `lib/alertas.ts`: `ehDiaDePregao(dataISO)`, `aberturaNY(dataISO)`
  (09:30 NY → "HH:MM" São Paulo), `horaFalada("10:30") → "dez e meia"`,
  `alertasDoDia(dataISO, agenda, preSessaoFechada) → Alerta[]`
  (`{ id, hora, texto, grupo: "rotina" | "noticia" }`, ordenados) e
  `alertasParaDisparar(alertas, agora, jaFalados) → Alerta[]` (janela de 90 s).
  - Files: `lib/alertas.ts`
  - Verify: TASK-102.
- [x] **TASK-102** — Testes em `scripts/verify.ts`:
  - `aberturaNY("2026-09-25") === "10:30"` e `aberturaNY("2026-01-15") === "11:30"`;
  - sábado `2026-09-26` e feriado `2026-09-07` → `alertasDoDia` vazio;
  - agenda `[{ evento: "Payroll", horario: "10:30", impacto: "ALTO" }]` gera 10:25 e 10:30;
    Médio gera só a da hora; Baixo não gera;
  - o alerta das 09:45 só existe com `preSessaoFechada = false`;
  - `alertasParaDisparar` às 10:00:30 devolve o das 10:00; às 10:01:31 não devolve;
    com o id em `jaFalados`, não devolve;
  - `horaFalada("09:45") === "nove e quarenta e cinco"`.
  - Verify: `npx tsx scripts/verify.ts` passa.
  - Feito em 25/09/2026: 11 testes novos (alertas, voz, calendário) passando.

### Fase 2 — Voz
- [x] **TASK-201** — `lib/voz.ts`: `escolherVoz(vozes, preferida?)` (ordem do §2),
  `falar(texto, { voz, volume })` com **fila** (uma fala por vez), `pararTudo()`.
  Aguardar `voiceschanged` (a lista de vozes chega vazia no primeiro instante).
  - Files: `lib/voz.ts`
  - Verify: teste de `escolherVoz` em `verify.ts` com lista falsa (ordem de preferência
    e fallback para qualquer pt-BR; sem pt-BR → `null` e a UI avisa "sem voz em português").
  - Feito: teste "Voz: prefere Francisca…" passando.

### Fase 3 — Integração
- [x] **TASK-301** — `components/layout/alertas-voz.tsx` montado na `Shell`: timer de
  1 s, carrega a pré-sessão de hoje (agenda + fechada) ao montar e a cada 5 min,
  dispara `alertasParaDisparar`, grava em `localStorage` o que falou.
  - Files: `components/layout/alertas-voz.tsx`, `components/layout/shell.tsx`
  - Verify: com `?relogio=09:59:50` (**só em desenvolvimento**, ignorado em produção),
    a voz fala a frase das 10:00 em até 15 s; recarregar a página não repete.
  - Feito: Chrome sem janela em `?relogio=09:59:52&data=2026-09-25` registrou
    `[voz] 10:00 Abertura do mercado à vista. Janela de entrada aberta.` No modo dev, o
    relógio simulado conta como página liberada (sem clique). Não repetir ao recarregar
    está coberto pelo teste de `alertasParaDisparar` + `localStorage`.
- [x] **TASK-302** — Controle na barra lateral, ao lado do botão de tema: ícone de
  alto-falante (ligado/desligado) que abre um painel com voz, volume, rotina/notícias,
  **Testar** e a lista de hoje com "ouvir". Aviso "Clique para ativar a voz" enquanto o
  navegador não liberou. Visual: tokens e estilos de `components/v2/estilos.ts`.
  - Files: `components/layout/alertas-voz.tsx`
  - Verify: no navegador, Testar fala com voz feminina pt-BR; desligar para a fila;
    tema claro e escuro sem cor quebrada.
  - Feito: painel conferido por print (voz "Google português do Brasil" listada, volume,
    rotina/notícias, Testar, lista do dia). A voz audível e o tema claro precisam do
    Anderson logado.

### Fase 4 — Calendário automático
- [x] **TASK-401** — `app/api/calendario/route.ts` como no §4 (ler o guia de route
  handlers em `node_modules/next/dist/docs/` antes — o Next deste projeto é o 16).
  - Verify: `curl http://localhost:3000/api/calendario` num dia com evento dos EUA
    devolve a lista com horário em São Paulo; conferir 1 evento à mão contra o site
    do ForexFactory.
  - Feito: `?data=2026-09-24` devolveu "pedidos de seguro-desemprego" às 09:30
    (Unemployment Claims, 8:30 em NY = 09:30 em São Paulo).
- [x] **TASK-402** — Pré-sessão: importação automática (agenda vazia e aberta) e botão
  "Importar dos EUA" no card Agenda.
  - Files: `app/pre-sessao/page.tsx`
  - Verify: logado, pré-sessão aberta com agenda vazia → a agenda aparece preenchida e
    salva (recarregar mantém); pré-sessão fechada não muda.
  - Feito no código (importa uma vez com agenda vazia e aberta; botão "Importar dos EUA";
    mescla sem duplicar, testado). Conferência logada fica com o Anderson.

### Fase 5 — Fechamento
- [x] **TASK-501** — `tsc --noEmit`, `npx tsx scripts/verify.ts`, `npm run build` limpos;
  atualizar `CHECKPOINT.md`.
  - Feito: tsc, verify e build limpos (build lista `/api/calendario` como dinâmica).
- [ ] **TASK-502** — Prova ao vivo: num dia útil, cockpit aberto desde antes das 09:00 com
  a voz ativada; anotar a hora real de cada fala até as 12:00. Nenhuma pode passar de 60 s
  de atraso.
