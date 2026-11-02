-- =============================================================================
-- MIGRACAO - NOTA DA EXECUCAO (A / B / C) COMO COLUNA (02/11/2026)
-- =============================================================================
-- Rodar inteiro no SQL Editor do Supabase. Idempotente.
-- Trade System §7: A = fiz exatamente o que devia; B = executei com ruido (hesitei, entrei
-- torto, saí cedo); C = forcei (entortei a regra, antecipei sem confirmacao, quis recuperar).
-- Ate aqui a nota ia so como prefixo [EXEC:X] nas notas; agora vira coluna para as metricas.

ALTER TABLE copa_trades
  ADD COLUMN IF NOT EXISTS execucao TEXT CHECK (execucao IS NULL OR execucao IN ('A', 'B', 'C'));

-- Backfill: le o prefixo [EXEC:X] das notas dos trades antigos
UPDATE copa_trades
   SET execucao = substring(notas from '\[EXEC:([ABC])\]')
 WHERE execucao IS NULL
   AND notas ~ '\[EXEC:[ABC]\]';

-- Conferencia: quantos trades por nota (NULL = sem nota ainda)
SELECT execucao, count(*) FROM copa_trades GROUP BY execucao ORDER BY execucao NULLS LAST;
