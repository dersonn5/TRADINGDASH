-- =============================================================================
-- MIGRACAO - PLANO POR HORA (03/10/2026)
-- =============================================================================
-- Rodar inteiro no SQL Editor do Supabase. Idempotente: pode rodar mais de uma vez.
--
-- Regras do operador depois da semana de 28/09 a 02/10:
--   1a hora (09:00-09:59): contra a primeira perna, 1 trade
--   2a hora (10:00-10:59): setup das 10 ou continuidade, ate 3 trades
--   3a hora (11:00-11:59): so continuidade, 1 trade
--   3 stops encerram o dia; 2 a 3 contratos. Reversao HTF sai do sistema ativo.
-- As cotas ficam no app (lib/gate.ts); aqui so o que o banco trava.

-- 1. A pre-sessao passa a aceitar o plano por hora (o setup vem da hora, nao do dia).
--    Sessoes antigas com setup do dia continuam validas.
ALTER TABLE copa_sessions DROP CONSTRAINT IF EXISTS copa_sessions_setup_do_dia_check;
ALTER TABLE copa_sessions ADD CONSTRAINT copa_sessions_setup_do_dia_check
    CHECK (setup_do_dia IN ('POR_HORA', 'reversao_htf', 'continuidade_tendencia', 'varrida_barra_10', 'NENHUM'));

-- 2. Setup C: ate 3 trades na 2a hora (antes: 1 por dia).
UPDATE copa_strategy_items i
   SET label = 'Dentro da cota da 2a hora (ate 3 trades, somando setup das 10 e continuidade)',
       ajuda = '10:00-10:59: ate 3 trades. A abertura de NY (10:30) entra na conta. Bateu 3 stops no dia, acabou.'
  FROM copa_strategy_versions v
 WHERE i.version_id = v.id AND v.strategy_id = 'varrida_barra_10' AND v.versao = 1 AND i.item_id = 'k7';

-- 3. Conferencia: a constraint nova e o item atualizado.
SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'copa_sessions_setup_do_dia_check';
SELECT i.item_id, i.label
  FROM copa_strategy_items i JOIN copa_strategy_versions v ON v.id = i.version_id
 WHERE v.strategy_id = 'varrida_barra_10' AND v.versao = 1 AND i.item_id = 'k7';
