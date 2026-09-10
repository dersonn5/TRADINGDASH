-- ==============================================================================
-- SCHEMA TRADING COGNITIVO ICT & SEGUNDO CÉREBRO
-- Executar no Supabase SQL Editor: https://supabase.com/dashboard/project/jirgsqhhnfqglxadqeap/sql/new
-- ==============================================================================

-- 1. TABELA DE NOTAS / SEGUNDO CÉREBRO (Camadas 1 a 5)
CREATE TABLE IF NOT EXISTS trading_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    camada INTEGER NOT NULL CHECK (camada BETWEEN 1 AND 5), -- 1=conceito, 2=regra, 3=modelo, 4=sistema, 5=sabedoria
    categoria TEXT NOT NULL DEFAULT 'ICT',
    status TEXT NOT NULL DEFAULT 'validado',
    tags TEXT[] DEFAULT '{}',
    linked_notes TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. TABELA DO BANCO DE TRADES
CREATE TABLE IF NOT EXISTS trading_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    strategy TEXT NOT NULL,
    session TEXT,
    contracts NUMERIC DEFAULT 1,
    entry_price NUMERIC NOT NULL,
    exit_price NUMERIC,
    stop_loss NUMERIC NOT NULL,
    take_profit NUMERIC,
    pnl NUMERIC DEFAULT 0,
    result TEXT NOT NULL DEFAULT 'OPEN' CHECK (result IN ('WIN', 'LOSS', 'BE', 'OPEN')),
    rr_achieved NUMERIC,
    confluence_score NUMERIC,
    screenshot_url TEXT,
    notes TEXT,
    mistakes_learnings TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. TABELA DO CHECKLIST AO VIVO NO PREGÃO
CREATE TABLE IF NOT EXISTS trading_live_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_date DATE NOT NULL DEFAULT CURRENT_DATE,
    session_name TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'B3 WIN',
    bias TEXT NOT NULL DEFAULT 'NEUTRO' CHECK (bias IN ('BULLISH', 'BEARISH', 'NEUTRO', 'NAO_OPERAR')),
    items JSONB NOT NULL DEFAULT '[]',
    score NUMERIC NOT NULL DEFAULT 0,
    risk_approved BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Habilitar RLS e criar políticas públicas
ALTER TABLE trading_notes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "trading_notes_public_access" ON trading_notes;
CREATE POLICY "trading_notes_public_access" ON trading_notes FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE trading_trades ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "trading_trades_public_access" ON trading_trades;
CREATE POLICY "trading_trades_public_access" ON trading_trades FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE trading_live_checklist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "trading_live_checklist_public_access" ON trading_live_checklist;
CREATE POLICY "trading_live_checklist_public_access" ON trading_live_checklist FOR ALL USING (true) WITH CHECK (true);

-- Índices para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_trading_notes_camada ON trading_notes(camada);
CREATE INDEX IF NOT EXISTS idx_trading_trades_date ON trading_trades(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_trading_trades_symbol ON trading_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_live_checklist_date ON trading_live_checklist(session_date DESC);
