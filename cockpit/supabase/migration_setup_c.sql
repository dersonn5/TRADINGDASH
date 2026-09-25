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
    ('varrida_barra_10', 'Varrida da Barra das 10', 'A abertura do a vista (barra de 15 min das 10:00) e o momento da manipulacao, em dois modos. C1 - a barra das 10 E MANIPULADA: entre 10:15 e 11:14 o preco passa da maxima ou da minima dela (sweep). C2 - a barra das 10 MANIPULA: ela mesma varre o topo ou o fundo de uma barra de 15 min anterior e devolve (nao precisa romper). Cenarios: continuacao (1a hora em tendencia, varre a maxima/minima contra a tendencia) ou reversao (varre BSL/SSL e devolve). Nos dois: operar CONTRA o lado varrido; NAO esperar o 15 min fechar - o sweep libera olhar o 1m; MSS no sentido da operacao, entrada no reteste do FVG, stop no extremo da pernada do MSS, alvo no proximo BSL/SSL com trailing. Registrar C1 ou C2 nas notas.', ARRAY['WIN'])
ON CONFLICT (id) DO UPDATE SET nome=EXCLUDED.nome, descricao=EXCLUDED.descricao, mercados=EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('varrida_barra_10', 1, 65, 'EM_CALIBRACAO', '1 min, 5 meses, sweep -> MSS + FVG de reversao sem esperar o 15 min fechar: C1 86 trades +0,21R (t=1,8), C2 95 trades +0,20R (t=1,8); base (todo gatilho 10:00-11:14) +0,11R. Melhor recorte: C1 contra a tendencia da 1a hora, 36 trades +0,43R (visto depois dos dados). Numeros antigos (+0,35R/+0,39R) tinham erro, corrigidos 25/09. Pesos dos PONTOS ESTIMADO. C1 e C2 medidos separados.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo=EXCLUDED.score_minimo, calibracao=EXCLUDED.calibracao, observacao=EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v, (VALUES
      ('k1', 'KILL', 0::numeric, 0, 'Barra das 10 (15 min) marcada: maxima e minima', 'As linhas douradas do indicador. O nivel so fica fixo depois das 10:15.', 'ESTIMADO'),
      ('k2', 'KILL', 0::numeric, 1, 'SWEEP do a vista: C1 (entre 10:15 e 11:14 o preco passou da maxima/minima da barra das 10) ou C2 (a barra das 10 passou do topo/fundo de uma barra de 15 min anterior)', 'Nao esperar a barra de 15 min fechar: o sweep ja libera olhar o 1 min. Anotar C1 ou C2 e o contexto da 1a hora (a favor, contra ou lateral).', 'ESTIMADO'),
      ('k3', 'KILL', 0::numeric, 2, 'Direcao CONTRA o lado varrido: topo varrido = venda, fundo varrido = compra', 'Vale para C1 e C2. Anotar o contexto: no teste, a reversao CONTRA a tendencia da 1a hora foi o melhor recorte do C1.', 'ESTIMADO'),
      ('k4', 'KILL', 0::numeric, 3, 'MSS no 1m em vela FECHADA, no sentido da operacao, em ate 30 min depois do sweep e ate 11:14', 'Sem MSS nao ha entrada. Se o preco segue alem do sweep sem virar, nao e setup.', 'ESTIMADO'),
      ('k5', 'KILL', 0::numeric, 4, 'Entrada no RETESTE do FVG ou do BLOCO DE ORDEM deixado pela perna do MSS', 'Nao perseguir preco. OB = ultimo candle contrario antes da pernada; entrada na abertura dele. OB: stop ~metade (~205 pts), menos entradas, mais 5R. Teste de 5 meses: no C1, OB igual ao FVG (+0,23R x +0,21R); no C2, OB pior (+0,01R x +0,20R) - no C2 preferir FVG.', 'ESTIMADO'),
      ('k6', 'KILL', 0::numeric, 5, 'Stop no extremo da pernada do MSS · alvo no proximo BSL/SSL', 'Nao usar o extremo da barra das 10 como stop no C2 - fica largo demais. Trailing: zero a zero em 1R, depois atras dos swings de 1m.', 'ESTIMADO'),
      ('k7', 'KILL', 0::numeric, 6, 'Primeiro trade do Setup C hoje', 'Um trade do Setup C por dia. Stopou, o setup acabou no dia.', 'ESTIMADO'),
      ('p1', 'PONTO', 25::numeric, 7, 'Sweep com rejeicao clara no 1m (pavio longo alem do nivel)', 'O preco passa do nivel e volta rapido. Aceitacao alem do nivel enfraquece.', 'ESTIMADO'),
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
