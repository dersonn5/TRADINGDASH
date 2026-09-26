# SPEC — Voz Kokoro (pf_dora) nos alertas do pregão

> **Executor:** Gemini. **Revisor:** Anderson.
> **Status:** implementada pelo Claude em 26/09/2026 (ver CHECKPOINT.md, seção Voz Dora). Diferença da spec: o manifest é indexado pelo texto normalizado, não pelo SHA-1.
> Depende de `cockpit/SPEC_ALERTAS_VOZ.md` (já implementada — ler antes).

Leia `CHECKPOINT.md` (raiz), `cockpit/SPEC_ALERTAS_VOZ.md` e este arquivo antes de abrir
código. Cada task tem **Verify**; sem Verify rodado nesta sessão, não está pronta.

---

## 1. PRD

### 1.1 Problema
Os alertas de voz usam a voz do navegador (Web Speech API). O operador achou a voz feia.

### 1.2 Objetivo
Os alertas falam com a voz **Kokoro `pf_dora`** (feminina, português do Brasil, modelo de
código aberto `hexgrad/Kokoro-82M`), gerada **uma vez** na GPU do operador e guardada
como arquivos de áudio dentro do cockpit. No pregão o navegador só **toca** os arquivos:
sem servidor de voz, sem custo, funciona no site publicado.

### 1.3 Escopo — entra
- **FR-001** Script de geração (`tools/voz/gerar.py`) que cria todos os áudios.
- **FR-002** Os alertas passam a ter **segmentos** de fala; cada segmento vira um arquivo.
- **FR-003** Player no navegador que toca os segmentos em fila; segmento sem arquivo cai
  na voz do navegador (a de hoje), só aquele pedaço.
- **FR-004** No painel de alertas, a voz padrão passa a ser "Dora (Kokoro)"; as vozes do
  navegador continuam na lista como alternativa.
- **FR-005** Na pré-sessão, o campo "Evento" da agenda sugere os nomes que já têm áudio
  (`<datalist>`), para o operador escrever o nome que a voz conhece.

### 1.4 Anti-escopo — NÃO entra
- Rodar o Kokoro no servidor ou no navegador em tempo real.
- Clonar voz / outras vozes. Só `pf_dora`.
- Mudar horários, textos ou regras dos alertas (SPEC_ALERTAS_VOZ §3) — só como são falados.
- Commit ou push sem o Anderson pedir.

### 1.5 Critério de sucesso
- Todas as frases da rotina e as de notícia com nomes conhecidos tocam com a voz Dora.
- O teste de cobertura (TASK-302) passa: nenhuma frase fixa sem áudio.
- `?relogio=09:59:50&data=2026-09-25` em desenvolvimento toca o áudio da Dora às 10:00.

---

## 2. Decisões técnicas

| Decisão | Escolha | Por quê |
|---|---|---|
| Onde roda o Kokoro | só no PC do operador, na hora de gerar (RTX 3070) | o pregão não depende de servidor nem de internet para a voz |
| Ambiente Python | **`C:\Users\Pc\kokoro-voz`** (venv, Python 3.12, fora do projeto) | o caminho do projeto tem "Ç" ("AUTOMAÇÃO") e o eSpeak falha com acento no caminho. O venv pode já existir com o PyTorch cu124 instalado — conferir antes de recriar |
| Idioma | `KPipeline(lang_code="p", repo_id="hexgrad/Kokoro-82M")`, voz `pf_dora` | `p` = português do Brasil (usa eSpeak via `misaki`) |
| Formato | **OGG Vorbis**, 24 kHz mono (`soundfile.write(..., format="OGG", subtype="VORBIS")`) | ~10× menor que WAV; Edge e Chrome tocam |
| Onde ficam | `cockpit/public/voz/<id>.ogg` + `cockpit/public/voz/manifest.json` | servidos como arquivo estático, inclusive na Vercel |
| Chave de cada áudio | `id` = primeiros 12 caracteres do **SHA-1 do texto normalizado** (trim, espaços únicos) | o mesmo texto sempre gera o mesmo arquivo; regerar não duplica |
| Frase inteira × pedaços | **frase inteira** sempre que a frase é fixa ou o nome do evento é conhecido; **pedaços** só no resumo das 09:00 | frase inteira tem entonação natural; juntar pedaços soa picotado |
| Segurança | `torch.load(..., weights_only=True)` já é o que o Kokoro usa — não mudar | revisado pelo Claude em 26/09: sem código malicioso em kokoro/misaki |

---

## 3. O que precisa de áudio (lista gerada, não escrita à mão)

Um script TypeScript, **`cockpit/scripts/listar-frases-voz.ts`**, importa `lib/alertas.ts`
e `lib/calendario.ts` e escreve **`tools/voz/frases.json`** (`[{ id, texto }]`) com:

1. **Rotina**: todos os textos fixos de `alertasDoDia` (§3.1 da spec anterior), gerando
   para dois dias úteis — um com NY às 10:30 e outro com NY às 11:30 — e com pré-sessão
   aberta e fechada, para cobrir todos.
2. **Notícias com nome conhecido**: para cada nome em português de `NOMES` (`lib/calendario.ts`)
   e da lista de eventos do Brasil abaixo:
   - `Atenção: em cinco minutos, {nome}. Impacto alto.`
   - `Saindo agora: {nome}.`
3. **Resumo das 09:00 em pedaços**:
   - `Bom dia. O pregão abriu. Até as dez, só observar e marcar.`
   - `Hoje não tem notícia de impacto alto.`
   - `Hoje tem {uma|duas|…|seis} {notícia|notícias} de impacto alto.`
   - `A primeira é {nome},` para cada nome conhecido
   - `às {horaFalada}.` para cada horário de 08:00 a 18:00 de 5 em 5 minutos
4. **Eventos do Brasil** (nomes que entram na lista de sugestões da agenda):
   IPCA · IPCA-15 · decisão do Copom · ata do Copom · PIB brasileiro · Caged · IBC-Br ·
   produção industrial · vendas no varejo do Brasil · Relatório Focus · leilão do Tesouro ·
   fluxo cambial · IGP-M. Exportar essa lista como `EVENTOS_BRASIL` em `lib/calendario.ts`.

---

## 4. Roadmap

### Fase 0 — Ambiente e amostra (aprovação do Anderson)
- [x] **TASK-001** — Ambiente: conferir `C:\Users\Pc\kokoro-voz` (criar se não existir:
  `python -m venv C:\Users\Pc\kokoro-voz`), instalar
  `torch` (`--index-url https://download.pytorch.org/whl/cu124`), `kokoro`, `soundfile`.
  - Verify: `C:\Users\Pc\kokoro-voz\Scripts\python.exe -c "import torch, kokoro; print(torch.cuda.is_available())"` imprime `True`.
- [ ] **TASK-002** — Rodar `tools/voz/amostra.py` (já existe) e **parar**: o Anderson ouve
  `tools/voz/amostras/pf_dora_*.wav` e aprova a voz e a velocidade
  (`amostra.py pf_dora 0.95` para testar mais devagar).
  - Verify: Anderson aprovou; anotar a velocidade escolhida no CHECKPOINT.

### Fase 1 — Segmentos (lógica pura, com teste)
- [ ] **TASK-101** — `lib/alertas.ts`: `Alerta` ganha `segmentos: string[]`, cuja junção
  com espaço é igual a `texto`. Rotina e notícias: 1 segmento (a frase inteira). Resumo
  das 09:00: os pedaços do §3.3. `texto` continua existindo (é o que o painel mostra).
  - Files: `lib/alertas.ts`
  - Verify: teste em `scripts/verify.ts` — para os alertas de 2026-09-25 com a agenda do
    teste atual, `segmentos.join(" ") === texto` em todos; o resumo tem 5 segmentos.
- [ ] **TASK-102** — `lib/voz-clipes.ts`: `idDoTexto(texto)` (SHA-1, 12 caracteres, texto
  normalizado — usar `crypto.subtle` no navegador e `node:crypto` nos scripts; a função pura
  recebe o hash pronto ou existe uma versão síncrona testável) e
  `planoDeFala(segmentos, manifest) → Array<{ tipo: "arquivo", url } | { tipo: "navegador", texto }>`.
  - Verify: teste com manifest falso — segmento conhecido vira `arquivo`, desconhecido vira
    `navegador`, ordem mantida.

### Fase 2 — Geração
- [ ] **TASK-201** — `cockpit/scripts/listar-frases-voz.ts` (§3) → `tools/voz/frases.json`.
  - Verify: `npx tsx scripts/listar-frases-voz.ts` roda; o JSON tem as frases das quatro
    listas do §3 e nenhum `id` repetido.
- [ ] **TASK-202** — `tools/voz/gerar.py`: lê `frases.json`, gera só os `id` que ainda não
  existem em `cockpit/public/voz/`, grava OGG e reescreve `cockpit/public/voz/manifest.json`
  (`{ "voz": "pf_dora", "velocidade": x, "clipes": { "<id>": "<id>.ogg" } }`). Idempotente.
  **Antes de sintetizar, aplicar `para_fala()` de `tools/voz/pronuncia.py`** (dicionário de
  pronúncia dos termos em inglês e siglas — a voz lê tudo como português). O `id` continua
  vindo do texto ORIGINAL; só o áudio usa a pronúncia. Mudou o dicionário → apagar os
  áudios das frases afetadas e regerar.
  - Verify: rodar duas vezes; a segunda não gera nada novo. Tamanho total de
    `public/voz` anotado no CHECKPOINT (esperado: dezenas de MB, no máximo ~60 MB).

### Fase 3 — Player e integração
- [ ] **TASK-301** — `lib/voz.ts`: `tocarPlano(plano, { volume, vozNavegador })` — fila de
  `HTMLAudioElement` (um por vez, `onended` chama o próximo, ~120 ms de pausa entre
  segmentos); `tipo: "navegador"` usa o `falar()` atual. `pararTudo()` para os dois.
  Carregar `/voz/manifest.json` uma vez (se falhar, tudo cai na voz do navegador).
  - Files: `lib/voz.ts`
- [ ] **TASK-302** — `components/layout/alertas-voz.tsx`: disparo e "ouvir" usam
  `planoDeFala` + `tocarPlano`. No seletor de voz, primeira opção "Dora (Kokoro)" (padrão);
  as do navegador continuam abaixo. Teste de **cobertura** em `verify.ts`: todo texto fixo
  da rotina e toda frase de notícia com nome conhecido tem `id` no `manifest.json`.
  - Files: `components/layout/alertas-voz.tsx`, `scripts/verify.ts`
  - Verify: `?relogio=09:59:50&data=2026-09-25` (dev) → às 10:00 toca o arquivo da Dora
    (conferir na aba Network que `/voz/<id>.ogg` foi pedido). "Testar a voz" e "ouvir"
    tocam a Dora. Com a opção de voz do navegador escolhida, volta a falar pelo navegador.
- [ ] **TASK-303** — Pré-sessão: `<datalist>` no campo Evento com os nomes conhecidos
  (`NOMES` + `EVENTOS_BRASIL`).
  - Files: `app/pre-sessao/page.tsx`
  - Verify: ao digitar "IP" no Evento aparece "IPCA" e "IPCA-15".

### Fase 4 — Fechamento
- [ ] **TASK-401** — `tsc --noEmit`, `npx tsx scripts/verify.ts`, `npm run build` limpos;
  `CHECKPOINT.md` atualizado (como regerar os áudios: `listar-frases-voz.ts` → `gerar.py`;
  quando regerar: sempre que mudar um texto em `lib/alertas.ts` ou um nome em `lib/calendario.ts`).
- [ ] **TASK-402** — Anderson ouve os alertas do dia no painel ("ouvir" em cada um) e aprova.
