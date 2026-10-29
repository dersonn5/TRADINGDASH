-- =============================================================================
-- MIGRACAO — ESCALONAMENTO A FAVOR (29/10/2026)
-- =============================================================================
-- Regra nova do plano: entrada com ate 3 contratos; aumentar a mao so a favor do
-- movimento e com o stop ja no zero a zero ou no lucro, ate 6 no total
-- (lib/gate.ts: MAX_CONTRATOS, MAX_CONTRATOS_ESCALONADO).
--
-- O Profit so mostra o total de contratos do trade. Quem diz se os contratos acima
-- de 3 vieram de escalonamento a favor e o operador (agenda), por isso a coluna.
-- Executado por: Anderson no SQL Editor do Supabase.
-- =============================================================================

-- risco_inicial_rs: no trade escalonado a "entrada" gravada e o preco medio de todos os
-- contratos, entao pontos / (entrada - stop) erra o R. O R passa a ser
-- pnl_real / risco_inicial_rs (stop em pts x contratos da entrada x R$ 0,20 no WIN).
-- lib/metricas.ts rDoTrade usa esta coluna quando ela existe.
ALTER TABLE copa_trades
  ADD COLUMN IF NOT EXISTS escalonado BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS risco_inicial_rs NUMERIC CHECK (risco_inicial_rs IS NULL OR risco_inicial_rs > 0);

-- 29/10, MAV das 10:04: entrou com 3, stop de 170 pts (170 x 3 x 0,20 = R$ 102),
-- escalonou a favor ate 6. Com a regra nova, o trade fica dentro do plano.
-- O preco do stop fica vazio: o preco da primeira entrada nao foi anotado.
UPDATE copa_trades
   SET escalonado = true,
       risco_inicial_rs = 102,
       respeitou_plano = true,
       erro_tipo = NULL,
       notas = REPLACE(
                 REPLACE(notas, '[FORA DO PLANO: 6 contratos (máximo 3)] ', '[ESCALONADO 3 → 6] '),
                 'Stop inicial não anotado.', 'Stop inicial de 170 pts com 3 contratos (risco R$ 102).')
 WHERE hora_entrada = TIMESTAMPTZ '2026-10-29 10:04:00-03'
   AND user_id = (SELECT id FROM auth.users WHERE email = 'trader@copa.btg');

-- Conferencia: o trade das 10:04 com escalonado = true e no plano.
SELECT to_char(hora_entrada AT TIME ZONE 'America/Sao_Paulo', 'DD/MM HH24:MI') AS trade,
       contratos, escalonado, risco_inicial_rs,
       round(pnl_real / NULLIF(risco_inicial_rs, 0), 2) AS r,
       respeitou_plano, erro_tipo, left(notas, 70) AS notas
  FROM copa_trades
 WHERE hora_entrada::date = DATE '2026-10-29'
 ORDER BY hora_entrada;
