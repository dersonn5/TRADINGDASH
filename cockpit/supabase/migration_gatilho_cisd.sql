-- =============================================================================
-- MIGRACAO - GATILHO CISD + OB (02/11/2026)
-- =============================================================================
-- Rodar inteiro no SQL Editor do Supabase. Idempotente.
-- O operador entra por CISD (change in state of delivery) + order block, que nao e o
-- mesmo que MSS + OB. Espelho de GatilhoTrade em lib/copa-db.ts.

ALTER TABLE copa_trades DROP CONSTRAINT IF EXISTS copa_trades_gatilho_check;
ALTER TABLE copa_trades ADD CONSTRAINT copa_trades_gatilho_check
    CHECK (gatilho IN ('MSS_FVG', 'MSS_OB', 'CISD_OB', 'BPR', 'IFVG', 'RISK_ENTRY', 'FVG_POS_SWING'));

SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'copa_trades_gatilho_check';
