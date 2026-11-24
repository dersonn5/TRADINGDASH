# PRD curto — Contas (prova da mesa e conta real)

Status: **aprovado pelo Anderson em 11/11/2026; Fases 1 a 4 escritas em 12/11** · Claude
Falta: rodar `supabase/migration_contas.sql` e conferir com dados reais (critérios 1 a 3 do §6).
Plano da prova (10 contratos, corte do dia, recuo, saída): Trade System §2.2 e `lib/prova.ts`.

## 1. Problema

O cockpit trata tudo como uma conta só. O Anderson comprou a prova da Zero7 (plano Pleno,
WIN/WDO) e vai operar a prova e a conta real. Misturadas, as estatísticas não respondem a
nenhuma das duas perguntas: "quanto falta para passar na prova?" e "como está a conta real?".
E os limites são diferentes: o gate hoje tem 3 contratos e R$ 160 por trade fixos no código.

## 2. Objetivo

Cada trade pertence a uma conta. Todas as telas mostram uma conta por vez, e o gate aplica
os limites daquela conta. Na prova, a Visão Geral mostra em uma olhada a distância da meta e
a distância de cada regra que elimina ou trava.

## 3. Escopo

**Entra:**
- Cadastro de contas (por SQL, sem tela): `REAL` e `PROVA`, cada uma com seus limites.
- Seletor de conta na barra lateral; a escolha vale para todas as telas.
- Gate, pré-sessão, checklist e fechamento usando os limites da conta ativa.
- Card da prova na Visão Geral.
- Trades já registrados ficam na conta real.

**Não entra (anti-escopo):**
- Replicar ordem entre contas ou qualquer automação de envio: a mesa proíbe ("somente
  ordens orgânicas, enviadas manualmente").
- Integração com a Área do Trader da Zero7: o número oficial é o deles; o cockpit é o espelho.
- Visão somada das duas contas (pode vir depois, se fizer falta).
- Fase de incubadora: entra quando a prova for aprovada e as regras dela estiverem confirmadas.

## 4. Modelo de dados

```sql
copa_contas (
  id uuid pk, user_id uuid, nome text, tipo text check (tipo in ('REAL','PROVA')),
  status text check (status in ('ATIVA','APROVADA','ELIMINADA','ENCERRADA')) default 'ATIVA',
  max_contratos int, max_risco_trade_rs numeric,
  max_perdas_seguidas int, max_operacoes_dia int,
  limite_perda_diaria_rs numeric null,   -- da mesa; null na conta real
  limite_perda_total_rs numeric null,    -- da mesa; null na conta real
  meta_rs numeric null, min_pregoes int null,
  teto_dia_pct numeric null,             -- 0.5 = um pregão conta no máximo 50% da meta
  pts_minimos_validos int null,          -- 10 = operação com 10 pts ou menos não conta
  criada_em timestamptz
)
copa_sessions.conta_id uuid references copa_contas  -- unique (user_id, data, conta_id)
```

Os trades herdam a conta pela sessão (sem coluna nova em `copa_trades`).

## 5. Requisitos funcionais

- **FR-001** Migração: cria `copa_contas`, cria a conta `REAL` do usuário, preenche
  `conta_id` das sessões existentes com ela e troca o unique de `(user_id, data)` para
  `(user_id, data, conta_id)`.
- **FR-002** Seletor de conta na barra lateral (nome + etiqueta PROVA/REAL). A escolha fica
  em `localStorage`; sem escolha, abre na conta real.
- **FR-003** Todas as listagens (`listarTrades`, `listarTradesDoMes`, `listarTradesFechados`,
  sessão do dia) filtram pela conta ativa.
- **FR-004** `lib/gate.ts` recebe os limites da conta em vez de ler as constantes
  `MAX_CONTRATOS`, `MAX_RISCO_TRADE_RS`, `MAX_PERDAS_DIA`, `MAX_OPERACOES_DIA`. As cotas por
  hora eram iguais nas duas contas (1 · 3 · 2). **Desde 16/11/2026 a prova tem as dela;** desde
  23/11, só a hora das 10:00 e só o setup das 10 (MAV), 2 trades (0 · 2 · 0), e 2 stops
  encerram (`REGRAS_DA_HORA_PROVA` em `lib/prova.ts` + `supabase/migration_prova_plano.sql`). A mão da
  prova é de 5 contratos até o fim, com risco de R$ 265 por trade (`max_contratos` e
  `max_risco_trade_rs` da conta, na mesma migração); o recuo de `lib/prova.ts` só muda a mão
  de uma conta com mais de 5 contratos.
- **FR-005** Na prova, o gate bloqueia a entrada se o risco do trade levar a perda do dia
  além de `limite_perda_diaria_rs` ou a perda total além de `limite_perda_total_rs`.
- **FR-006** Card "Prova" na Visão Geral (só em conta `PROVA`): resultado contra a meta;
  perda total usada; perda de hoje contra o limite diário; pregões operados contra o mínimo;
  maior pregão contra o teto de 50% (o excedente aparece como "não conta"); trades com
  `pts_minimos_validos` ou menos marcados como "não conta para a mesa".
- **FR-007** O card da meta de fim de ano aparece só na conta real.
- **FR-008** O modo demonstração ganha uma conta de prova fictícia para ver o card.

## 6. Critério de sucesso

1. Trocar de conta muda Visão Geral, Histórico, Calendário e Checklist, sem trade de uma
   conta aparecer na outra.
2. O resultado da prova no cockpit bate com a Área do Trader da Zero7 (diferença só de
   custos, se houver).
3. O gate recusa na prova o que a mesa puniria (acima do limite diário ou total) e recusa
   na real o que o plano de fim de ano não permite.

## 7. Roadmap (vira build-spec depois do PRD aprovado)

- **Fase 1 — Banco:** migração `migration_contas.sql` + SQL de conferência. Verify: as
  sessões antigas todas com `conta_id` da conta real; contagem de trades igual à de antes.
- **Fase 2 — Lib:** conta ativa, listagens filtradas, gate por conta. Verify: `tsc` limpo e
  testes novos em `scripts/verify.ts` (gate com limites da prova e da real).
- **Fase 3 — Telas:** seletor na barra lateral e telas lendo a conta ativa. Verify: print
  das duas contas no modo demonstração e conferência com os dados reais.
- **Fase 4 — Card da prova:** FR-006. Verify: teste do cálculo (teto de 50%, pregões
  mínimos, trades de 10 pts) e print.

## 8. Aberto (depende da Zero7 responder)

- A perda total é fixa sobre o saldo inicial ou sobe junto com o lucro? Conta posição
  aberta? Isso muda a conta do FR-005 e do card.
- A perda diária conta posição aberta e custos?
- Perda total do plano comprado: R$ 6.500 (tela da compra) ou R$ 4.997 (regulamento)?
- O custo de R$ 0,37 por contrato de WIN é por ordem ou por operação fechada?
