-- =============================================================================
-- LIMPEZA - tira do banco o que era da Copa BTG e das telas antigas (25/09/2026)
-- =============================================================================
-- FICA (o cockpit usa todo dia):
--   copa_sessions, copa_trades, copa_trade_items          pre-sessao, checklist, historico
--   copa_strategies, copa_strategy_versions, copa_strategy_items   setups A, B e C
--   trading_live_checklist                                 estado do checklist ao vivo
--   views de analise (v_copa_item_performance, v_copa_janela_performance,
--   v_copa_disciplina, v_copa_dia_resultado, v_copa_adesao, v_copa_score_buckets)
--
-- SAI:
--   copa_phases + v_copa_fase_placar      fases e placar do torneio
--   copa_notas_voz, copa_nota_erros, copa_tipos_erro + v_copa_erro_custo
--                                         notas de voz (nenhuma tela usa)
--   trading_notes, trading_trades         Segundo Cerebro e Banco de Trades antigos
--
-- A coluna copa_sessions.phase_id fica (vazia): duas views de analise leem ela.
-- Sem CASCADE: se algo inesperado depender de uma tabela, o DROP falha e a
-- transacao inteira volta atras, sem apagar nada.


-- PASSO 1 - rode SO este SELECT primeiro e veja o que tem dentro.
SELECT 'copa_phases' AS tabela, count(*) AS linhas FROM copa_phases
UNION ALL SELECT 'copa_notas_voz', count(*) FROM copa_notas_voz
UNION ALL SELECT 'copa_nota_erros', count(*) FROM copa_nota_erros
UNION ALL SELECT 'copa_tipos_erro', count(*) FROM copa_tipos_erro
UNION ALL SELECT 'trading_notes', count(*) FROM trading_notes
UNION ALL SELECT 'trading_trades', count(*) FROM trading_trades;


-- PASSO 2 - apaga. Selecione daqui ate o COMMIT e rode.
BEGIN;

DROP VIEW IF EXISTS v_copa_fase_placar;
ALTER TABLE copa_sessions DROP CONSTRAINT IF EXISTS copa_sessions_phase_id_fkey;
UPDATE copa_sessions SET phase_id = NULL WHERE phase_id IS NOT NULL;
DROP TABLE IF EXISTS copa_phases;

DROP VIEW IF EXISTS v_copa_erro_custo;
DROP TABLE IF EXISTS copa_nota_erros;
DROP TABLE IF EXISTS copa_notas_voz;
DROP TABLE IF EXISTS copa_tipos_erro;

DROP TABLE IF EXISTS trading_notes;
DROP TABLE IF EXISTS trading_trades;

COMMIT;


-- PASSO 3 - conferencia: deve listar so as 7 tabelas que ficam.
SELECT table_name
  FROM information_schema.tables
 WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
   AND (table_name LIKE 'copa_%' OR table_name LIKE 'trading_%')
 ORDER BY table_name;
