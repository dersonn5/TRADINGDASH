# Checkpoint — Cognitive Trading (cockpit v2)

Atualizado: 25/09/2026 · Claude (retomou depois do Gemini parar por limite)

## Onde estamos
Spec `cockpit/SPEC_FRONT_V2.md` (visual novo + Visão Geral) com todas as fases de
código feitas. Falta a conferência visual logada pelo Anderson e o commit.

## Pronto e verificado
- Fases 2–5 (Gemini): Sora, tokens escuro/claro, campos gatilho/contexto/modo,
  `lib/metricas.ts`, Visão Geral — prova: `npx tsx scripts/verify.ts` passa (inclui o
  conjunto de 4 trades da TASK-402); `tsc --noEmit` limpo.
- Fase 6 (Claude): Histórico, Estratégias, Checklist e Pré-Sessão no visual v2 —
  prova: `npm run build` limpo com as 7 rotas; dev server responde 200 em `/`,
  `/pre-sessao`, `/checklist`, `/trades`, `/estrategias`, `/login`.
- Migrations rodadas no Supabase: `migration_setup_c.sql`, `migration_gatilho.sql`
  (o Gemini gravou e apagou um trade de teste com os 3 campos).

## Em andamento
Conferência visual logada, nos dois temas, das 5 telas (o Claude não consegue logar).

## Próximo
- [ ] Anderson abre as 5 telas logado (escuro e claro) e aponta o que destoa do
      `design/v2/`.
- [ ] Commit (tudo desde 25/09 está sem commit — limpeza da Copa, Setup C, v2).
- [ ] Renomear tabelas `copa_*` → `ct_*` (combinado para depois da v2).
- [ ] Rodar a limpeza do banco se ainda não rodou: `cockpit/supabase/migration_limpeza_copa.sql`
      e o DROP das views `v_copa_*`.

## Fidelidade ao design (25/09, segunda rodada)
- Moldura nova em `components/layout/shell.tsx` (barra lateral do design, tema e sair
  no rodapé); o shadcn sidebar e o cabeçalho com busca/"bot idle" foram removidos.
- Visão Geral, Pré-Sessão, Checklist e Estratégias reescritas a partir de
  `design/v2/*.dc.html`; estilos comuns em `components/v2/estilos.ts`; cálculo da Visão
  Geral em `lib/visao-geral.ts` (testado com os 16 trades de `scripts/fixture-design.ts`).
- Textos das estratégias: fonte em `copa/strategies/*.json`, gerados por
  `python copa/strategies/gerar_ts.py`. O banco (copa_strategy_items) ainda tem os
  textos antigos sem acento — o app não lê de lá.
- Como conferir o visual sem login: não há mais atalho no código. Para tirar print,
  recriar temporariamente o desvio no AuthGate e remover antes do commit.

## Alertas de voz (25/09) — `cockpit/SPEC_ALERTAS_VOZ.md`
- Motor puro em `lib/alertas.ts`, voz em `lib/voz.ts` (Web Speech API), calendário em
  `lib/calendario.ts` + `app/api/calendario/route.ts` (ForexFactory, só EUA, cache 1 h).
- Componente `components/layout/alertas-voz.tsx` na barra lateral (botão alto-falante).
- Teste sem esperar o horário (só em dev): `?relogio=09:59:50&data=2026-09-25`.
- Falta: prova ao vivo num dia útil (TASK-502) e conferir os feriados da B3 de 2026.

## Decisões que não se recuperam lendo o código
- Paleta monocromática ciano; perda = ciano apagado + sinal "−" (classe
  `perda-vermelha` troca para vermelho) — pedido do operador por "tons da mesma cor".
- Tudo em Sora; `.mono`/`.tabular` viraram só `tabular-nums` — o operador não
  gostou da fonte mono.
- Gráficos em SVG puro, sem Bklit — o `shadcn add @bklit/...` falhou com
  `ECOMPROMISED` (lock do npm). Visual igual ao artboard.
- Checklist e Pré-Sessão ganharam o visual pelos componentes `components/inst/*`
  (restilizados) e por troca de estilo pontual — a lógica de 2.150 linhas do
  checklist não foi reescrita de propósito.
- Views `v_copa_*` devem ser apagadas: rodam sem RLS e expõem os trades à chave anon.

## Armadilhas já pagas
- O navegador não fala sem um clique na página (autoplay). Por isso o aviso no painel
  e o ponto no botão de alto-falante até o primeiro clique.
- Abertura de NY não é fixa: 10:30 no horário de verão dos EUA, 11:30 de nov a mar.
- Rota de API que usa "hoje" não pode ser estática: a data vem por `?data=` (deixa a rota
  dinâmica) e o feed fica no cache de fetch (`next.revalidate`).
- O relatório do Gemini disse "tsc limpo" e "anotado no CHECKPOINT" — nenhum dos
  dois era verdade (Histórico com erro de tipo, arquivo inexistente). Conferir o
  `git diff`, nunca o relatório.
- Apagar `.next/` com o dev server rodando deixa tudo em 500. Pare o servidor
  (porta 3000) antes, ou reinicie depois.
- `→` escrito como texto JSX (fora de string) aparece literal na tela.
- Seletor de mês da Visão Geral tem que ser ancorado no mês de hoje; ancorado no
  mês escolhido, o mês atual some da lista.
- Backtests do Setup C com gatilho de 1 min deixavam entrar antes da barra de 15 min
  fechar (olhar o futuro). Detalhes: `Cerebro_Obsidian/.../Estudo_Barra_das_10.md` itens 6–9.

## Aberto / bloqueado
- Chave `service_role` do Supabase vazou no histórico do GitHub
  (`cockpit/lib/supabase-admin.ts`, commit ccdcc8b) e dá acesso a outros sistemas
  do mesmo projeto (`trena_*`, `wilerk_*`). Precisa ser trocada no painel.
