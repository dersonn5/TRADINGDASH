-- =============================================================================
-- MIGRACAO - TRADE CONTRA A PRIMEIRA PERNA + REGRAS DE 01/10/2026
-- =============================================================================
-- Rodar inteiro no SQL Editor do Supabase. Idempotente: pode rodar mais de uma vez.
-- Espelho de copa/strategies/primeira_perna.json.
--
-- Regras do operador (01/10/2026): antes das 10:00 so UM trade, contra a primeira perna
-- do dia (800+ pts a partir das 09:00), stop alem do extremo da perna, alvo nos 75% da
-- perna. Entradas normais 10:00-11:59. Limites: 6 operacoes, 4 stops, sem pausa. Ate 3
-- contratos. Os limites e a janela ficam no app (lib/gate.ts); aqui so o que o banco trava.

-- 1. A janela do trade passa a aceitar ABERTURA (09:00-09:59).
ALTER TABLE copa_trades DROP CONSTRAINT IF EXISTS copa_trades_janela_check;
ALTER TABLE copa_trades ADD CONSTRAINT copa_trades_janela_check
    CHECK (janela IN ('ABERTURA', 'PRIME', 'VALIDA', 'FORA'));

-- 2. Gatilho iFVG (o operador entra muito por iFVG).
ALTER TABLE copa_trades DROP CONSTRAINT IF EXISTS copa_trades_gatilho_check;
ALTER TABLE copa_trades ADD CONSTRAINT copa_trades_gatilho_check
    CHECK (gatilho IN ('MSS_FVG', 'MSS_OB', 'BPR', 'IFVG', 'RISK_ENTRY', 'FVG_POS_SWING'));

-- 3. Estrategia, versao 1 e checklist.
INSERT INTO copa_strategies (id, nome, descricao, mercados) VALUES
    ('primeira_perna', 'Contra a Primeira Perna', 'O unico trade antes das 10:00. A abertura das 09:00 faz uma perna forte (800 pts ou mais) e, em 2026, volta 75% dela em ~3 de cada 4 dias (o V das 09:00). Operar contra a perna depois do extremo, stop alem do topo/fundo da perna, alvo fixo nos 75% da perna. Um trade por dia.', ARRAY['WIN'])
ON CONFLICT (id) DO UPDATE SET nome=EXCLUDED.nome, descricao=EXCLUDED.descricao, mercados=EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('primeira_perna', 1, 65, 'EM_CALIBRACAO', 'Padrao medido (Estudo_Reversao_Abertura_Vista, itens 7 e 9): perna de 800 pts e volta de 75% ate 12:00 em 75% dos dias de 2026 (1 min) e 74% (15 min); 45-72% por ano de 2021 a 2025 com o tamanho em %. Perna rapida (800 pts ate 09:29) volta mais em todos os anos. A entrada com stop no extremo ainda nao foi testada como trade. Pesos dos PONTOS estimados.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo=EXCLUDED.score_minimo, calibracao=EXCLUDED.calibracao, observacao=EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v, (VALUES
      ('k1', 'KILL', 0::numeric, 0, 'A primeira perna andou 800 pts ou mais a partir da abertura das 09:00', 'Anotar a abertura das 09:00 e o extremo da perna. Menos de 800 pts nao e este setup.', 'ESTIMADO'),
      ('k2', 'KILL', 0::numeric, 1, 'Nivel dos 75% da perna marcado (o alvo)', 'Alvo = extremo - 75% x (extremo - abertura).', 'ESTIMADO'),
      ('k3', 'KILL', 0::numeric, 2, 'Direcao contra a perna: perna de alta = venda, perna de baixa = compra', 'So depois que o preco parar de fazer extremo novo.', 'ESTIMADO'),
      ('k4', 'KILL', 0::numeric, 3, 'Gatilho de reversao no 1 min (MSS + FVG, BPR, iFVG ou risk entry)', 'Perdeu a entrada, perdeu o trade.', 'ESTIMADO'),
      ('k5', 'KILL', 0::numeric, 4, 'Stop alem do topo/fundo da perna, alvo fixo nos 75%', 'Stop no extremo da perna + 1 tick. Sair no alvo dos 75%, sempre.', 'ESTIMADO'),
      ('k6', 'KILL', 0::numeric, 5, 'Antes das 10:00 e primeiro trade do dia', 'Um trade antes das 10:00, so este.', 'ESTIMADO'),
      ('p1', 'PONTO', 40::numeric, 6, 'A perna chegou aos 800 pts ate 09:29', 'No estudo, a perna rapida volta mais em todos os anos.', 'ESTIMADO'),
      ('p2', 'PONTO', 30::numeric, 7, 'Extremo com rejeicao clara no 1 min (pavio longo, candle de forca contra)', 'O preco tenta continuar e volta rapido.', 'ESTIMADO'),
      ('p3', 'PONTO', 30::numeric, 8, 'O alvo dos 75% esta a pelo menos 2R', 'Com o stop no extremo, o alvo precisa pagar o risco.', 'ESTIMADO')
  ) AS x(item_id, tipo, peso, ordem, label, ajuda, origem)
 WHERE v.strategy_id = 'primeira_perna' AND v.versao = 1
ON CONFLICT (version_id, item_id) DO UPDATE SET
    tipo=EXCLUDED.tipo, peso=EXCLUDED.peso, ordem=EXCLUDED.ordem,
    label=EXCLUDED.label, ajuda=EXCLUDED.ajuda, origem=EXCLUDED.origem;

-- 4. Conferencia: deve listar 6 KILL e 3 PONTO (pontos somando 100), e a janela nova.
SELECT i.tipo, count(*), sum(i.peso)
  FROM copa_strategy_items i JOIN copa_strategy_versions v ON v.id = i.version_id
 WHERE v.strategy_id = 'primeira_perna' AND v.versao = 1
 GROUP BY i.tipo;
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN ('copa_trades_janela_check', 'copa_trades_gatilho_check');
