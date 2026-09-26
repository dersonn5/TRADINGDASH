# Checkpoint — Cognitive Trading (cockpit v2)

Atualizado: 26/09/2026 · Claude

## Onde estamos
Cockpit v2 no ar e commitado. Voz Dora (Kokoro) integrada nos alertas. Modo
demonstração com trades fictícios. O Anderson começa a operar de verdade na segunda (28/09).

## Pronto e verificado
- Visual v2 fiel a `design/v2/*.dc.html` nas 5 telas; telas zeradas sem dados — prova:
  prints headless (playwright-core no scratchpad, Chromium de `~/AppData/Local/ms-playwright`).
- Alertas de voz com a Dora — prova: `npx tsx scripts/verify.ts` (cobertura: toda frase
  fixa e todo nome conhecido têm áudio); no navegador, "Testar a voz" pediu
  `/voz/manifest.json` e o `.ogg` certo; a Dora é a opção padrão do painel.
- Modo demonstração — prova: prints de Visão Geral, Histórico e Estratégias com
  `?demo=1` (jul–set/2026, 63 trades, 51% de acerto).
- `trading_live_checklist` com RLS por usuário: SQL em
  `cockpit/supabase/migration_checklist_ao_vivo.sql`.

## Próximo
- [ ] Anderson roda `migration_checklist_ao_vivo.sql` no Supabase e testa "Salvar progresso".
- [ ] Limpeza Passo 2 (apagar os 3 dias e o trade de teste) e DROP das views `v_copa_*`,
      se ainda não rodou.
- [ ] Prova ao vivo dos alertas num dia útil (TASK-502) e conferir feriados B3 2026.
- [ ] Renomear tabelas `copa_*` → `ct_*`.

## Voz Dora — como regerar
1. `npx tsx scripts/listar-frases-voz.ts` (em `cockpit/`) grava `tools/voz/frases.json`.
2. `C:/Users/Pc/kokoro-voz/Scripts/python.exe tools/voz/gerar.py` gera só o que falta em
   `cockpit/public/voz/` e reescreve o `manifest.json` (287 frases, 4,8 MB).
- Regerar sempre que mudar um texto em `lib/alertas.ts` ou um nome em `lib/calendario.ts`
  (o teste de cobertura do verify.ts falha até regerar).
- Pronúncia de inglês/siglas: `tools/voz/pronuncia.py`. Mudou o dicionário: apagar os
  `.ogg` afetados e regerar.
- O que não tem áudio (nome de evento digitado à mão) sai pela voz do navegador, só
  aquele pedaço. Por isso o campo Evento da pré-sessão sugere os nomes gravados.

## Decisões que não se recuperam lendo o código
- Voz: áudios pré-gerados na GPU do operador, tocados como arquivo estático. Sem
  servidor de voz. O manifest é indexado pelo texto normalizado (o hash só dá nome ao
  arquivo), então o navegador não precisa calcular SHA-1.
- Modo demonstração só no front (`lib/demo.ts`, interceptado em `listarTrades` e
  `listarTradesDoMes`): nada vai para o Supabase. Liga com `?demo=1`, sai pelo aviso.
  Semente fixa escolhida para parecer um trader real.
- Paleta monocromática ciano; perda = ciano apagado + "−". Tudo em Sora.
- Gráficos em SVG puro (Bklit falhou com `ECOMPROMISED`).
- Views `v_copa_*` rodam sem RLS e expõem os trades à chave anon: apagar.

## Armadilhas já pagas
- `position: sticky` cria contexto de empilhamento: o painel de alertas (fixed, dentro
  da barra lateral) ficava atrás do conteúdo. A barra lateral precisa de `zIndex`.
- O overlay de dev do Next (`nextjs-portal`) cobre o botão de alto-falante nos testes
  headless: esconder com CSS ou `click({ force: true })`.
- Kokoro deu `CUDA error: out of memory` uma vez com a GPU quase livre; rodar de novo passou.
- O navegador não fala sem um clique (autoplay). Abertura de NY: 10:30 no verão dos
  EUA, 11:30 de nov a mar.
- Relatório do Gemini disse "tsc limpo" sem ser verdade. Conferir o `git diff`.
- Apagar `.next/` com o dev server rodando deixa tudo em 500.
- Conferir visual sem login: desvio temporário no AuthGate, removido antes do commit.
- Backtests do Setup C com gatilho de 1 min olhavam o futuro. Ver
  `Cerebro_Obsidian/.../Estudo_Barra_das_10.md` itens 6–9.

## Aberto / bloqueado
- Chave `service_role` vazou no histórico do GitHub (commit ccdcc8b); repo privado.
  Trocar no painel do Supabase quando der.
