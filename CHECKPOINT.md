# Checkpoint — Cognitive Trading (cockpit v2)

Atualizado: 16/11/2026 · Claude

## Onde estamos
**Prova da mesa Zero7 (plano Pleno), comprada em 11/11/2026: só a prova é operada, a conta real
está parada** e o plano de fim de ano, suspenso. O cockpit tem dois perfis, Real e Prova
(`SPEC_CONTAS.md`), com a `migration_contas.sql` já rodada.
**A prova está em −R$ 3.552 bruto (−R$ 3.703,70 líquido na mesa) depois de 16 trades em 3 pregões
(12, 13 e 16/11); a perda total é R$ 6.500.** Em 16/11 o operador mudou o plano da prova: sem 1ª
hora, 2 trades às 10h, 1 a partir das 11:30, 2 stops encerram, 5 contratos (Trade System §2.2).
Os 16 trades ainda **não estão no banco**: sem eles o cockpit acha a prova zerada e libera 10
contratos.
Dia 1 do cockpit: 19/10/2026 (o operador pediu para apagar tudo antes dessa data).

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

- Contas, prova e real (12/11) — prova: `npx tsc --noEmit` limpo; `npx tsx scripts/verify.ts` com 16
  testes novos (teto de 50% por pregão, trades de 10 pts, recuo, corte do dia, saída, risco do trade,
  card); no demo, seletor Real/Prova trocando Visão Geral, Histórico, Calendário e Estratégias, com a
  escolha mantida ao recarregar. **Não provado com dados reais:** filtro por conta no banco, faixa da
  prova no Checklist e bloqueios do gate na prova. Dependem da migração e do login do operador.
- Plano da prova de 16/11 no gate — prova: `npx tsc --noEmit` limpo e `npx tsx scripts/verify.ts`
  com 149 testes (7 casos de hora da prova, cotas 0 · 2 · 1, risco de R$ 265 no recuo e os 16
  trades reais dando −R$ 3.552 e mão de 5). **Não conferido na tela nem com dados reais.**
- Filtro "Tudo" na Visão Geral (03/11) — prova: teste no verify.ts e print no demo.

## Próximo
- [ ] Anderson roda `cockpit/supabase/migration_prova_plano.sql` (2 stops, 3 trades) e o SQL dos
      16 trades da prova (entregue no chat em 16/11; conferência: 16 trades, −3.552).
- [ ] Depois disso, conferir logado na conta Prova: card com perda total usada de R$ 3.552, mão de
      5 contratos, Checklist bloqueando antes das 10:00 e entre 11:00 e 11:29.
- [ ] Trades da prova: faltam setup, gatilho, stop planejado e nota de cada um (lançados com
      "setup a confirmar" e horário aproximado ao minuto).
- [ ] Perguntar à Zero7 por escrito: incubadora de 10 dias (promoção) ou ciclo de 30 dias com margem
      de R$ 4.997 (regulamento); limites de contratos e de perda na conta real; se a margem é o capital.
- [ ] Trades de 03/11: faltam setup e gatilho dos 3 da 1ª hora, gatilhos dos das 10h e nota A/B/C.
- [ ] Detector de estrutura (`cockpit/SPEC_DETECTOR.md`): PRD aguardando o operador; Fase 0 é fechar
      as definições do §4 com prints.
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
- Prova Zero7 (11/11/2026, Trade System §2.2): 10 contratos fixos, não 5 nem 15. Simulação: o
  operador quer aprovar em até 8 pregões; 5 contratos dão ~18 pregões; acima de 10 a perda diária
  da mesa (R$ 1.247) corta o dia depois de 2 stops, então a prova não acelera e a eliminação dobra.
  Perda total tratada como R$ 6.500 **fixos** (palavra do operador e tela da compra; o regulamento
  traz R$ 4.997 e não diz se é fixa). Cockpit soma sem custos: a saída é em R$ 5.100, não em R$ 4.997.
- Plano da prova de 16/11: as cotas por hora da prova ficam no código (`REGRAS_DA_HORA_PROVA`),
  não no banco, como o corte do dia e o recuo: são plano do operador, não regra da mesa. No banco
  só o que já era coluna (stops seguidos e trades do dia). O trade das 11:30 é a 3ª hora com
  início às 11:30 (`aPartirDeMin`), não uma janela nova.
- Contas: a conta ativa é estado de módulo em `lib/contas.ts`, definido pelo Shell antes de montar
  as telas; trocar de conta remonta a tela (key). Alternativa descartada: passar a conta por
  parâmetro em toda função do `copa-db.ts` (dezenas de chamadas). Sem a migração ou sem conta
  carregada o id é nulo e nada é filtrado; depois da migração, gravar sem conta falha no banco
  (`conta_id NOT NULL`), de propósito.
- Trade de 10 pts ou menos na prova: a perda conta, o ganho não. O regulamento só diz que a
  operação "não conta"; a leitura conservadora evita meta inflada no cockpit.
- Plano de fim de ano (02/11/2026, Trade System §2.1): novembro 3 contratos, meta R$ 6.000 (19 pregões); dezembro 5→7→10 contratos se novembro cumprir 4 requisitos (R$ 6 mil, disciplina 90%, 50 trades, positivo sem o maior trade); recuo de R$ 2 mil do pico desce um degrau, colchão de R$ 3 mil volta a 3. Card "Meta do mês" na Visão Geral (`lib/meta-fim-de-ano.ts`). **Em dezembro, `MAX_CONTRATOS` e `MAX_RISCO_TRADE_RS` em `lib/gate.ts` ainda estão fixos em 3 e R$ 160: ligar ao degrau antes de 01/12.**
- Plano por hora (03/10/2026, depois da semana 28/09–02/10): 09h Setup V (1 trade; foi 2 de 29/10 a 02/11, voltou a 1 porque a perna parou de reverter na 1ª hora depois das eleições; alvo 75% da perna) · 10h setup das 10 ou continuidade (até 3) · 11h só continuidade (2, era 1 até 28/10). Contratos: até 3 na entrada; desde 29/10, escalonar a favor com stop financeiro até 6 (`MAX_CONTRATOS_ESCALONADO`, coluna `escalonado`); perda máxima por trade R$ 160, todos os contratos (`MAX_RISCO_TRADE_RS`). 3 stops SEGUIDOS encerram (um gain zera; `contarPerdasSeguidas`, desde 29/10); 5 trades; 2–3 contratos. RHT (Reversão HTF) em qualquer hora, dentro da cota. Siglas: RPP, MAV, CSI, RHT (lib/metricas SIGLAS). Regras em `lib/gate.ts` (REGRAS_DA_HORA) e Trade_System_Anderson.md §1–2.
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
- Conferir visual sem login: desvio temporário no AuthGate, removido antes do commit. O desvio
  tem de olhar a URL (`demo=1`), não o `localStorage`: o demo só é ligado pelo Shell, que fica
  dentro do AuthGate. O desvio também gera erro de hidratação no console; some ao remover.
- Push não garante publicação: em 12/11 o build da Vercel falhou em 17 s ao buscar a fonte Sora
  (`next/font/google queries have exactly one entry`), com `tsc` e build local limpos, e o site
  ficou na versão antiga sem aviso. Depois de todo push: `vercel ls tradingdash` (site em
  `tradingdash-psi.vercel.app`). Falhou na fonte: `vercel redeploy <url do deploy>` resolveu.
- Banco checa `chk_direcao_coerente`: stop de compra abaixo da entrada. Saída no zero a zero com
  stop já movido não serve como stop do registro; gravar `NULL` (03/11).
- Backtests do Setup C com gatilho de 1 min olhavam o futuro. Ver
  `Cerebro_Obsidian/.../Estudo_Barra_das_10.md` itens 6–9.

## Aberto / bloqueado
- Chave `service_role` vazou no histórico do GitHub (commit ccdcc8b); repo privado.
  Trocar no painel do Supabase quando der.
