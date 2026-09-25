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
