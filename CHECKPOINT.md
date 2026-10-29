# Checkpoint — Cognitive Trading (cockpit v2)

Atualizado: 20/10/2026 · Claude

## Onde estamos
Plano por hora em operação. **Dia 1 do cockpit: 19/10/2026** — o operador pediu para apagar tudo antes
dessa data (SQL entregue em 20/10; ele roda no Supabase). 19/10: RPP +R$ 360 e 3 RHT fora do plano
(5 contratos, cota da 1ª hora estourada), dia +R$ 60. O diário de 07/10 fica só no Cerebro.

## Pronto e verificado
- Visual v2 fiel a `design/v2/*.dc.html` nas 5 telas; telas zeradas sem dados — prova:
  prints headless (playwright-core no scratchpad, Chromium de `~/AppData/Local/ms-playwright`).
- Alertas de voz com a Dora — prova: `npx tsx scripts/verify.ts` (cobertura: toda frase
  fixa e todo nome conhecido têm áudio); no navegador, "Testar a voz" pediu
  `/voz/manifest.json` e o `.ogg` certo; a Dora é a opção padrão do painel.
- Modo demonstração — prova: prints de Visão Geral, Histórico e Estratégias com
  `?demo=1` (jul–set/2026, 63 trades, 51% de acerto).
- `migration_plano_por_hora.sql` rodada no Supabase em 03/10 — prova: copa_strategies com RPP, MAV e CSI.
- `migration_primeira_perna.sql` rodada no Supabase em 01/10 — prova: KILL 6, PONTO 3 (soma 100).
- `trading_live_checklist` com RLS por usuário: SQL em
  `cockpit/supabase/migration_checklist_ao_vivo.sql`.
- Calendário de resultados (`/calendario`) — prova: `npx tsx scripts/verify.ts` (outubro/2026 com 5 semanas, feriado 12/10, dias com trade somando pnl e R, semana e total batendo, PF/WR nulos em zero trades/perdas, total de setembro demo idêntico à Visão Geral); verificação no navegador em `/calendario?demo=1` com navegação de mês, clique para detalhar trades do dia (03/09 com +R$ 910 batendo com a célula), responsivo sem rolagem horizontal em 1440px e 900px, temas claro/escuro e barra lateral retrátil; `npm run build` limpo (exit 0).

## Próximo
- [ ] "Fechar o dia" (importar CSV do Profit + completar com a agenda): spec em
      `cockpit/SPEC_FECHAMENTO.md`, para o Gemini. Bloqueado na Fase 2 até o Anderson salvar o CSV
      real em `cockpit/.local/profit-2026-10-28.csv`. Trades de 27–28/10 lançados por SQL (alguns com
      stop/alvo nominais, a migração da spec limpa).
- [ ] Testar o Setup V como trade nos 5 meses (entrada após o extremo, stop além da perna, alvo nos 75%).
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
- Plano por hora (03/10/2026, depois da semana 28/09–02/10): 09h Setup V (1 trade, alvo 75% da perna) · 10h setup das 10 ou continuidade (até 3) · 11h só continuidade (2, era 1 até 28/10). Contratos: até 3 na entrada; desde 29/10, escalonar a favor com stop no zero/lucro até 6 (`MAX_CONTRATOS_ESCALONADO`, coluna `escalonado`). 3 stops SEGUIDOS encerram (um gain zera; `contarPerdasSeguidas`, desde 29/10); 5 trades; 2–3 contratos. RHT (Reversão HTF) em qualquer hora, dentro da cota. Siglas: RPP, MAV, CSI, RHT (lib/metricas SIGLAS). Regras em `lib/gate.ts` (REGRAS_DA_HORA) e Trade_System_Anderson.md §1–2.
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
