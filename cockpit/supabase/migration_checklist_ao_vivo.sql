-- =============================================================================
-- CHECKLIST AO VIVO — guarda o progresso da trilha durante o pregao (26/09/2026)
-- =============================================================================
-- O botao "Salvar progresso" do checklist gravava numa tabela que nunca foi criada.
-- Esta versao e por usuario: cada um so le e grava o proprio checklist (a versao
-- antiga do schema.sql deixava qualquer pessoa ler e gravar).
-- Rodar inteiro no SQL Editor do Supabase. Idempotente.

CREATE TABLE IF NOT EXISTS trading_live_checklist (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    session_date   DATE NOT NULL,
    strategy_id    TEXT,
    session_name   TEXT NOT NULL DEFAULT '',
    market         TEXT NOT NULL DEFAULT 'B3 WIN',
    bias           TEXT NOT NULL DEFAULT 'NEUTRO' CHECK (bias IN ('BULLISH', 'BEARISH', 'NEUTRO', 'NAO_OPERAR')),
    items          JSONB NOT NULL DEFAULT '[]',
    score          NUMERIC NOT NULL DEFAULT 0,
    risk_approved  BOOLEAN NOT NULL DEFAULT false,
    notes          TEXT NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- um checklist por usuario por dia: e o alvo do upsert do app
    CONSTRAINT trading_live_checklist_usuario_dia UNIQUE (user_id, session_date)
);

ALTER TABLE trading_live_checklist ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS live_checklist_own ON trading_live_checklist;
CREATE POLICY live_checklist_own ON trading_live_checklist
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Conferencia: a tabela existe, com RLS ligado e a politica por usuario
SELECT c.relname AS tabela, c.relrowsecurity AS rls_ligado,
       (SELECT count(*) FROM pg_policies p WHERE p.tablename = c.relname) AS politicas
  FROM pg_class c
 WHERE c.relname = 'trading_live_checklist';
