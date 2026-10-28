-- =============================================================================
-- MIGRACAO — FECHAR O DIA (IMPORTAR PROFIT + COMPLETAR COM AGENDA)
-- =============================================================================
-- Permite trades com stop e alvo vazios (quando nao anotados na agenda).
-- Registra origem (CHECKLIST, PROFIT, SQL), chave unica do Profit e tipo de erro.
-- Limpa trades antigos com valores nominais (200 pts / 2R presumido).
-- Executado por: Anderson no SQL Editor do Supabase.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- PARTE 1 — COLUNAS E INDICES
-- -----------------------------------------------------------------------------
ALTER TABLE copa_trades ALTER COLUMN stop DROP NOT NULL;
ALTER TABLE copa_trades ALTER COLUMN alvo DROP NOT NULL;
ALTER TABLE copa_trades ALTER COLUMN rr_planejado DROP NOT NULL;

-- Novos tipos de erro em copa_tipos_erro, SO se a tabela existir (ela vem de
-- migration_notas_voz.sql, que pode nao ter rodado). Sem o guarda, o INSERT
-- falha e o SQL Editor para o script inteiro aqui.
DO $$
BEGIN
  IF to_regclass('public.copa_tipos_erro') IS NOT NULL THEN
    INSERT INTO copa_tipos_erro (id, nome, descricao, momento, ordem) VALUES
      ('LEITURA_CONTRA_LIQUIDEZ', 'Operou contra liquidez', 'Operou a favor da liquidez ja tomada (ex.: comprou rompimento logo apos a captura do PWH).', 'ENTRADA', 16),
      ('ERRO_BOLETA',              'Erro de boleta',         'Ordem errada: lado, quantidade ou preco.', 'ENTRADA', 17)
    ON CONFLICT (id) DO UPDATE
      SET nome = EXCLUDED.nome, descricao = EXCLUDED.descricao, momento = EXCLUDED.momento, ordem = EXCLUDED.ordem;
  END IF;
END $$;

ALTER TABLE copa_trades
  ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'CHECKLIST'
      CHECK (origem IN ('CHECKLIST', 'PROFIT', 'SQL')),
  ADD COLUMN IF NOT EXISTS profit_chave TEXT,
  ADD COLUMN IF NOT EXISTS erro_tipo TEXT
      CHECK (erro_tipo IS NULL OR erro_tipo IN (
        'FORA_DO_SETUP', 'SEM_CONFIRMACAO', 'PERSEGUIU_PRECO', 'FORA_DO_TAMANHO',
        'MELHOR_PRECO', 'EXCESSO_TRADES', 'REVANCHE', 'ANTECIPOU_STOP',
        'PARCIAL_EMOCIONAL', 'MUDOU_ALVO', 'AUMENTOU_POSICAO',
        'LEITURA_CONTRA_LIQUIDEZ', 'ERRO_BOLETA'
      ));

CREATE UNIQUE INDEX IF NOT EXISTS uq_trades_profit_chave
  ON copa_trades(user_id, profit_chave) WHERE profit_chave IS NOT NULL;


-- -----------------------------------------------------------------------------
-- PARTE 2 — CONSTRAINT DE DIRECAO COERENTE (ACEITA NULL EM STOP E ALVO)
-- -----------------------------------------------------------------------------
ALTER TABLE copa_trades DROP CONSTRAINT IF EXISTS chk_direcao_coerente;
ALTER TABLE copa_trades ADD CONSTRAINT chk_direcao_coerente CHECK (
  (stop IS NULL OR (direcao = 'COMPRA' AND stop < entrada) OR (direcao = 'VENDA' AND stop > entrada))
  AND
  (alvo IS NULL OR (direcao = 'COMPRA' AND alvo > entrada) OR (direcao = 'VENDA' AND alvo < entrada))
);


-- -----------------------------------------------------------------------------
-- PARTE 3 — LIMPEZA DOS NOMINAIS
-- -----------------------------------------------------------------------------
-- Previa antes do update (mostra quantas linhas cada regra pega):
-- As notas dos lancamentos por SQL usam tres textos:
--   "(200 pts nominais)"          -> so o stop e nominal
--   "(200 pts e 2R nominais)"     -> stop E alvo nominais
--   "(2R presumido)"              -> so o alvo e nominal (o stop = preco de saida do loss)
SELECT
  COUNT(*) FILTER (WHERE notas LIKE '%[lançado depois]%') AS qtd_origem_sql,
  COUNT(*) FILTER (WHERE notas LIKE '%200 pts nominais%' OR notas LIKE '%200 pts e 2R nominais%') AS qtd_stop_nominal,
  COUNT(*) FILTER (WHERE notas LIKE '%2R presumido%' OR notas LIKE '%2R nominais%') AS qtd_alvo_nominal
FROM copa_trades;

-- 1. Marcar origem = 'SQL' nos trades lancados a posteriori
UPDATE copa_trades
SET origem = 'SQL'
WHERE notas LIKE '%[lançado depois]%'
  AND origem <> 'SQL';

-- 2a. Stop E alvo nominais (precisa vir antes do 2b e do 3: o texto contem os dois padroes)
UPDATE copa_trades
SET
  stop = NULL,
  alvo = NULL,
  rr_planejado = NULL,
  notas = REPLACE(notas, '200 pts e 2R nominais', 'stop e alvo não anotados')
WHERE notas LIKE '%200 pts e 2R nominais%';

-- 2b. So o stop nominal
UPDATE copa_trades
SET
  stop = NULL,
  rr_planejado = NULL,
  notas = REPLACE(notas, '200 pts nominais', 'stop não anotado')
WHERE notas LIKE '%200 pts nominais%';

-- 3. Limpar alvo presumido/nominal e atualizar notas
UPDATE copa_trades
SET
  alvo = NULL,
  rr_planejado = NULL,
  notas = REPLACE(REPLACE(notas, '2R presumido', 'alvo não anotado'), '2R nominais', 'alvo não anotado')
WHERE notas LIKE '%2R presumido%' OR notas LIKE '%2R nominais%';

-- 4. Saida manual sem stop ou sem alvo: o resultado "do plano" nao e medivel.
--    Os lancamentos por SQL gravaram pnl_plano = pnl_real, o que mostrava custo R$ 0
--    em vez de "nao medido" (SPEC_FECHAMENTO §2.8).
UPDATE copa_trades
SET pnl_plano = NULL
WHERE motivo_saida = 'MANUAL'
  AND (stop IS NULL OR alvo IS NULL)
  AND pnl_plano IS NOT NULL;


-- -----------------------------------------------------------------------------
-- PARTE 4 — CONFERENCIA FINAL
-- -----------------------------------------------------------------------------
SELECT
  origem,
  COUNT(*) AS total_trades,
  COUNT(*) FILTER (WHERE stop IS NULL) AS sem_stop,
  COUNT(*) FILTER (WHERE alvo IS NULL) AS sem_alvo,
  COUNT(*) FILTER (WHERE rr_planejado IS NULL) AS sem_rr
FROM copa_trades
GROUP BY origem
ORDER BY origem;
