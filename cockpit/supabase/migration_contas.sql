-- Contas: prova da mesa (Zero7, plano Pleno) e conta real. Ver SPEC_CONTAS.md.
--
-- ORDEM: se o SQL de 03/11 ainda nao rodou, rode ele ANTES desta migracao: ele usa
-- ON CONFLICT (user_id, data), e esta migracao troca esse unique por (user_id, data, conta_id).
--
-- O que faz:
--   1. cria copa_contas (uma linha por conta, com os limites dela);
--   2. cria a conta REAL (para quem ja tem sessao e para trader@copa.btg) e a PROVA;
--   3. liga cada sessao a uma conta (as antigas ficam na REAL) e troca o unique;
--   4. confere: a REAL com todos os trades de antes, a PROVA zerada.
-- Pode rodar de novo: nada duplica.

CREATE TABLE IF NOT EXISTS copa_contas (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    nome                    TEXT NOT NULL,
    tipo                    TEXT NOT NULL CHECK (tipo IN ('REAL', 'PROVA')),
    status                  TEXT NOT NULL DEFAULT 'ATIVA'
                            CHECK (status IN ('ATIVA', 'APROVADA', 'ELIMINADA', 'ENCERRADA')),
    max_contratos           INT     NOT NULL,
    max_risco_trade_rs      NUMERIC NOT NULL,
    max_perdas_seguidas     INT     NOT NULL DEFAULT 3,
    max_operacoes_dia       INT     NOT NULL DEFAULT 5,
    -- regras da mesa: NULL na conta real
    limite_perda_diaria_rs  NUMERIC,
    limite_perda_total_rs   NUMERIC,
    meta_rs                 NUMERIC,
    min_pregoes             INT,
    teto_dia_pct            NUMERIC,   -- 0.5 = um pregao conta no maximo 50% da meta
    pts_minimos_validos     INT,       -- 10 = operacao de 10 pts ou menos nao conta
    criada_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, nome)
);

ALTER TABLE copa_contas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contas_own ON copa_contas;
CREATE POLICY contas_own ON copa_contas
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Conta real: os limites que o gate ja usava (3 contratos, R$ 160 por trade, 3 stops, 5 trades)
INSERT INTO copa_contas (user_id, nome, tipo, max_contratos, max_risco_trade_rs, max_perdas_seguidas, max_operacoes_dia)
SELECT DISTINCT q.user_id, 'Conta real', 'REAL', 3, 160, 3, 5
  FROM (SELECT id AS user_id FROM auth.users WHERE email = 'trader@copa.btg'
        UNION
        SELECT user_id FROM copa_sessions) q
ON CONFLICT (user_id, nome) DO NOTHING;

-- Prova Zero7, plano Pleno (regulamento de 14/10/2026 + tela da compra):
-- 10 contratos, risco maximo de R$ 530 por trade (265 pts), perda diaria R$ 1.247,
-- perda total R$ 6.500 (valor da compra; o regulamento traz R$ 4.997), meta R$ 4.997,
-- minimo de 5 pregoes, um pregao conta ate 50% da meta, 10 pts ou menos nao contam.
INSERT INTO copa_contas (user_id, nome, tipo, max_contratos, max_risco_trade_rs, max_perdas_seguidas, max_operacoes_dia,
                         limite_perda_diaria_rs, limite_perda_total_rs, meta_rs, min_pregoes, teto_dia_pct, pts_minimos_validos)
SELECT id, 'Prova Zero7 (Pleno)', 'PROVA', 10, 530, 2, 3, 1247, 6500, 4997, 5, 0.5, 10
  FROM auth.users WHERE email = 'trader@copa.btg'
ON CONFLICT (user_id, nome) DO NOTHING;

-- Sessoes: cada uma pertence a uma conta. As que ja existem ficam na conta real.
ALTER TABLE copa_sessions ADD COLUMN IF NOT EXISTS conta_id UUID REFERENCES copa_contas(id);

UPDATE copa_sessions s
   SET conta_id = c.id
  FROM copa_contas c
 WHERE s.conta_id IS NULL AND c.user_id = s.user_id AND c.tipo = 'REAL';

ALTER TABLE copa_sessions ALTER COLUMN conta_id SET NOT NULL;

-- O unique (user_id, data) deixa de valer: o mesmo dia pode ter uma sessao por conta
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT conname FROM pg_constraint
            WHERE conrelid = 'copa_sessions'::regclass AND contype = 'u'
              AND pg_get_constraintdef(oid) = 'UNIQUE (user_id, data)'
  LOOP
    EXECUTE format('ALTER TABLE copa_sessions DROP CONSTRAINT %I', r.conname);
  END LOOP;
END $$;

ALTER TABLE copa_sessions DROP CONSTRAINT IF EXISTS copa_sessions_user_data_conta_key;
ALTER TABLE copa_sessions ADD CONSTRAINT copa_sessions_user_data_conta_key UNIQUE (user_id, data, conta_id);

-- Conferencia: a conta real com as sessoes e os trades de antes, a prova zerada
SELECT c.nome, c.tipo, c.status,
       count(DISTINCT s.id)                 AS sessoes,
       count(t.id)                          AS trades,
       coalesce(sum(t.pnl_real), 0)         AS pnl
  FROM copa_contas c
  LEFT JOIN copa_sessions s ON s.conta_id = c.id
  LEFT JOIN copa_trades t   ON t.session_id = s.id
 GROUP BY c.nome, c.tipo, c.status
 ORDER BY c.tipo DESC;
