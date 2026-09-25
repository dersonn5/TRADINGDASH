-- Migration: Dados novos no registro do trade (FR-005)
-- Adiciona colunas para gatilho, contexto da 1ª hora e modo do Setup C
-- Colunas aceitam NULL (trades antigos); a obrigatoriedade fica no app.

ALTER TABLE copa_trades
  ADD COLUMN IF NOT EXISTS gatilho TEXT
    CHECK (gatilho IN ('MSS_FVG','MSS_OB','BPR','RISK_ENTRY','FVG_POS_SWING')),
  ADD COLUMN IF NOT EXISTS contexto_1h TEXT
    CHECK (contexto_1h IN ('CONTINUACAO','REVERSAO','LATERAL')),
  ADD COLUMN IF NOT EXISTS setup_c_modo TEXT
    CHECK (setup_c_modo IN ('C1','C2'));

-- Verificação:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'copa_trades'
--   AND column_name IN ('gatilho', 'contexto_1h', 'setup_c_modo');
