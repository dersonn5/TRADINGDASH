-- =============================================================================
-- MIGRACAO - SETUP C: VARRIDA DA BARRA DAS 10 (em teste desde 2026-09-23)
-- =============================================================================
-- Rodar inteiro no SQL Editor do Supabase. Idempotente: pode rodar mais de uma vez.
-- Espelho de copa/strategies/varrida_barra_10.json.

-- 1. Pre-sessao passa a aceitar o Setup C como setup do dia.
ALTER TABLE copa_sessions DROP CONSTRAINT IF EXISTS copa_sessions_setup_do_dia_check;
ALTER TABLE copa_sessions ADD CONSTRAINT copa_sessions_setup_do_dia_check
    CHECK (setup_do_dia IN ('reversao_htf', 'continuidade_tendencia', 'varrida_barra_10', 'NENHUM'));

-- 2. Estrategia, versao 1 e checklist.
INSERT INTO copa_strategies (id, nome, descricao, mercados) VALUES
    ('varrida_barra_10', 'Varrida da Barra das 10', 'A abertura do a vista cria liquidez nos dois lados da barra de 15 min das 10:00. Entre 10:15 e 11:14, uma barra de 15 min passa da maxima ou da minima dela e FECHA de volta dentro: topo varrido -> venda, fundo varrido -> compra. No 1m, MSS no sentido da reversao, entrada no reteste do FVG, stop alem do extremo da varrida, alvo no proximo BSL/SSL com trailing. Fechou fora e ficou fora = rompimento, sem trade.', ARRAY['WIN'])
ON CONFLICT (id) DO UPDATE SET nome=EXCLUDED.nome, descricao=EXCLUDED.descricao, mercados=EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('varrida_barra_10', 1, 65, 'EM_CALIBRACAO', 'Estrutura medida em 5 anos de 15 min (varrida em ~2/3 dos dias; volta ao outro lado 52% x 44% da barra das 11, z=3,7). Com o gatilho de 1m: 64 trades, +0,39R/trade (t=2,5), abr-set/2026. Pesos dos PONTOS sao ESTIMADO. Teste prospectivo desde 2026-09-23: 20-30 trades; negativo apos 30 -> sai.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo=EXCLUDED.score_minimo, calibracao=EXCLUDED.calibracao, observacao=EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v, (VALUES
      ('k1', 'KILL', 0::numeric, 0, 'Barra das 10 (15 min) marcada: maxima e minima', 'As linhas douradas do indicador. O nivel so fica fixo depois das 10:15.', 'ESTIMADO'),
      ('k2', 'KILL', 0::numeric, 1, 'VARRIDA confirmada: barra de 15 min passou da linha e FECHOU de volta dentro (10:15-11:14)', 'Esperar o fechamento da barra. Fechou fora e ficou fora e rompimento - sem trade.', 'ESTIMADO'),
      ('k3', 'KILL', 0::numeric, 2, 'Direcao CONTRA o lado varrido: topo varrido = venda, fundo varrido = compra', 'A direcao da 1a hora nao muda a regra - o lado varrido define a direcao.', 'ESTIMADO'),
      ('k4', 'KILL', 0::numeric, 3, 'MSS no 1m em vela FECHADA, no sentido da reversao, ate 45 min do inicio da barra que varreu', 'Sem MSS nao ha entrada. Entrar no fechamento do 15 min nao paga: stop de ~500 pts.', 'ESTIMADO'),
      ('k5', 'KILL', 0::numeric, 4, 'Entrada no RETESTE do FVG deixado pela perna do MSS', 'Nao perseguir preco. Espera o retorno na regiao do FVG.', 'ESTIMADO'),
      ('k6', 'KILL', 0::numeric, 5, 'Stop alem do extremo da varrida · alvo no proximo BSL/SSL', 'Trailing: zero a zero em 1R, depois atras dos swings de 1m. Tamanho calculado para o stop (mediana ~420 pts).', 'ESTIMADO'),
      ('k7', 'KILL', 0::numeric, 6, 'Primeiro trade do Setup C hoje', 'Um trade do Setup C por dia. Stopou, o setup acabou no dia.', 'ESTIMADO'),
      ('p1', 'PONTO', 25::numeric, 7, 'Varrida por pavio LONGO, com rejeicao clara', 'Pavio grande alem da linha e fechamento bem dentro da barra das 10.', 'ESTIMADO'),
      ('p2', 'PONTO', 25::numeric, 8, 'Reversao com barras GRANDES e CONSECUTIVAS no 1m', 'A perna do MSS precisa ter conviccao. Reversao arrastada enfraquece.', 'ESTIMADO'),
      ('p3', 'PONTO', 20::numeric, 9, 'FVG limpo e ainda nao mitigado', 'FVG virgem reage melhor.', 'ESTIMADO'),
      ('p4', 'PONTO', 15::numeric, 10, 'Alvo (BSL/SSL) a pelo menos 2R', 'Se a liquidez mais proxima esta perto demais, o trade paga pouco para o risco.', 'ESTIMADO'),
      ('p5', 'PONTO', 15::numeric, 11, 'A varrida coincide com outra liquidez (PDH/PDL ou max/min da 1a hora)', 'Duas liquidezes no mesmo lugar valem mais que uma.', 'ESTIMADO')
  ) AS x(item_id, tipo, peso, ordem, label, ajuda, origem)
 WHERE v.strategy_id = 'varrida_barra_10' AND v.versao = 1
ON CONFLICT (version_id, item_id) DO UPDATE SET
    tipo=EXCLUDED.tipo, peso=EXCLUDED.peso, ordem=EXCLUDED.ordem,
    label=EXCLUDED.label, ajuda=EXCLUDED.ajuda, origem=EXCLUDED.origem;

-- 3. Conferencia: deve listar 12 itens (7 KILL + 5 PONTO, pontos somando 100).
SELECT i.tipo, count(*), sum(i.peso)
  FROM copa_strategy_items i JOIN copa_strategy_versions v ON v.id = i.version_id
 WHERE v.strategy_id = 'varrida_barra_10' AND v.versao = 1
 GROUP BY i.tipo;
