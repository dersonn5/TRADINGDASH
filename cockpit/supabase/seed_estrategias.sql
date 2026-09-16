-- Seed do catalogo. GERADO de copa/strategies/*.json — nao editar a mao.
-- Substitui playbook_anderson pelas duas estrategias reais do trade system.

DELETE FROM copa_strategies WHERE id = 'playbook_anderson';

-- Continuidade de Tendencia
INSERT INTO copa_strategies (id, nome, descricao, mercados) VALUES
    ('continuidade_tendencia', 'Continuidade de Tendencia', 'Opera A FAVOR da tendencia, entrando na correcao. Em alta: espera o mercado criar um swing high e capturar o FUNDO desse swing, entra em FVG ou bloco de ordem. Em baixa: espera criar um swing low e capturar o ULTIMO TOPO, entra em bloco de ordem ou FVG. A captura do extremo oposto do swing e o mesmo mecanismo do sweep, em escala menor.', ARRAY['WIN', 'WDO'])
ON CONFLICT (id) DO UPDATE SET nome=EXCLUDED.nome, descricao=EXCLUDED.descricao, mercados=EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('continuidade_tendencia', 1, 65, 'NAO_CALIBRADO', 'Pesos e score minimo sao ESTIMADO. Nenhum medido em backtest de WIN. Definido pelo operador em 2026-09-15.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo=EXCLUDED.score_minimo, calibracao=EXCLUDED.calibracao, observacao=EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v, (VALUES
      ('k1', 'KILL', 0::numeric, 0, 'Tendencia CLARA no HTF (60m / 15m), com estrutura progressiva', 'Alta: topos e fundos mais altos. Baixa: topos e fundos mais baixos. Clara, nao suposta. HTF e 60m e 15m - nao e o diario.', 'ESTIMADO'),
      ('k2', 'KILL', 0::numeric, 1, 'Swing formado na direcao da tendencia', 'Em alta, um swing high. Em baixa, um swing low. E ele que cria a liquidez a ser capturada.', 'ESTIMADO'),
      ('k3', 'KILL', 0::numeric, 2, 'Preco CAPTUROU o extremo oposto desse swing', 'Em alta: capturou o FUNDO do swing high. Em baixa: capturou o ULTIMO TOPO. E o sweep em escala menor - pega quem entrou na correcao.', 'ESTIMADO'),
      ('k4', 'KILL', 0::numeric, 3, 'FVG ou bloco de ordem na regiao da captura, ou na retomada da proxima perna', 'E o ponto de entrada. Sem array nao ha onde entrar.', 'ESTIMADO'),
      ('k5', 'KILL', 0::numeric, 4, 'Entrada no RETESTE desse array', 'Nao perseguir preco. Espera o retorno na regiao.', 'ESTIMADO'),
      ('k6', 'KILL', 0::numeric, 5, 'Stop alem do extremo capturado · alvo em liquidez · RR >= 2', 'Se o preco volta alem do extremo que acabou de capturar, a ideia morreu. Alvo em liquidez identificada, nunca numero arbitrario.', 'ESTIMADO'),
      ('p1', 'PONTO', 20::numeric, 6, 'A captura foi por PAVIO - preco nao fechou alem do extremo', 'Fechamento alem do extremo capturado sugere quebra de estrutura, nao captura de liquidez.', 'ESTIMADO'),
      ('p2', 'PONTO', 20::numeric, 7, 'Retomada com barras GRANDES e CONSECUTIVAS', 'A perna que retoma a tendencia precisa ter conviccao. Retomada arrastada enfraquece.', 'ESTIMADO'),
      ('p3', 'PONTO', 15::numeric, 8, 'Confluencia de array: FVG + bloco de ordem sobrepostos', 'Duas razoes na mesma regiao valem mais que uma.', 'ESTIMADO'),
      ('p4', 'PONTO', 15::numeric, 9, 'Tendencia com pelo menos 2 pernas confirmadas antes desta', 'Primeira perna ainda nao e tendencia. Terceira ja pode ser exaustao - julgue.', 'ESTIMADO'),
      ('p5', 'PONTO', 15::numeric, 10, 'Array ainda nao mitigado (fresco)', 'Array virgem reage melhor que array ja trabalhado varias vezes.', 'ESTIMADO'),
      ('p6', 'PONTO', 15::numeric, 11, 'Entrada em discount da perna (compra) ou premium (venda)', 'Entrar na metade favoravel da correcao, nao no topo dela.', 'ESTIMADO')
  ) AS x(item_id, tipo, peso, ordem, label, ajuda, origem)
 WHERE v.strategy_id = 'continuidade_tendencia' AND v.versao = 1
ON CONFLICT (version_id, item_id) DO UPDATE SET
    tipo=EXCLUDED.tipo, peso=EXCLUDED.peso, ordem=EXCLUDED.ordem,
    label=EXCLUDED.label, ajuda=EXCLUDED.ajuda, origem=EXCLUDED.origem;

-- Reversao HTF
INSERT INTO copa_strategies (id, nome, descricao, mercados) VALUES
    ('reversao_htf', 'Reversao HTF', 'Opera CONTRA a perna que acabou de varrer liquidez HTF. Sequencia: liquidez HTF (60m/15m) mapeada, sweep dessa liquidez, PD array HTF como destino, desce ao 1m para ler a briga na regiao, encontra sinal de reversao, MSS no 1m, entrada no reteste do FVG ou BPR.', ARRAY['WIN', 'WDO'])
ON CONFLICT (id) DO UPDATE SET nome=EXCLUDED.nome, descricao=EXCLUDED.descricao, mercados=EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('reversao_htf', 1, 65, 'NAO_CALIBRADO', 'Pesos e score minimo sao ESTIMADO. Nenhum medido em backtest de WIN. Definido pelo operador em 2026-09-15.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo=EXCLUDED.score_minimo, calibracao=EXCLUDED.calibracao, observacao=EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v, (VALUES
      ('k1', 'KILL', 0::numeric, 0, 'Liquidez HTF mapeada (60m / 15m) e o preco foi ate ela', 'PDH/PDL, topos e fundos relevantes, EQH/EQL. HTF do indice e 60m e 15m - NAO e o diario.', 'ESTIMADO'),
      ('k2', 'KILL', 0::numeric, 1, 'SWEEP dessa liquidez HTF confirmado', 'Preco penetrou a regiao, rejeitou e voltou. Sem sweep nao existe este setup.', 'ESTIMADO'),
      ('k3', 'KILL', 0::numeric, 2, 'PD array HTF na regiao, como destino (FVG / OB / BPR, 60m ou 15m)', 'E para onde o preco esta sendo entregue. Marcar a regiao inteira, nao a linha.', 'ESTIMADO'),
      ('k4', 'KILL', 0::numeric, 3, 'No 1m: sinal de reversao presente na regiao', 'Um dos tres: (a) estrutura de rompimento induzindo players a comprar/vender o rompimento; (b) AMD revertendo o movimento; (c) swing deixado apos o sweep com reversao forte.', 'ESTIMADO'),
      ('k5', 'KILL', 0::numeric, 4, 'MSS no 1m em vela FECHADA', 'Contra a perna que varreu. Vela fechada, nao em formacao.', 'ESTIMADO'),
      ('k6', 'KILL', 0::numeric, 5, 'Entrada no RETESTE do FVG ou BPR deixado pela perna do MSS', 'Nao perseguir preco. Espera o retorno na regiao do array.', 'ESTIMADO'),
      ('k7', 'KILL', 0::numeric, 6, 'Stop alem do extremo do swing do MSS · alvo em liquidez · RR >= 2', 'Stop no extremo do swing que originou o MSS, NAO na barra do FVG. Alvo em liquidez identificada, nunca numero arbitrario.', 'ESTIMADO'),
      ('p1', 'PONTO', 20::numeric, 7, 'Reversao com barras GRANDES e CONSECUTIVAS', 'O criterio e este. Reversao arrastada nao conta.', 'ESTIMADO'),
      ('p2', 'PONTO', 20::numeric, 8, 'Estrutura de rompimento induzindo players, dentro da regiao de sweep', 'O rompimento existe para capturar quem entrou nele. Sem inducao, VOCE e a liquidez.', 'ESTIMADO'),
      ('p3', 'PONTO', 15::numeric, 9, 'AMD completo visivel dentro da regiao', 'Acumulacao, manipulacao e distribuicao revertendo o movimento apos o sweep.', 'ESTIMADO'),
      ('p4', 'PONTO', 15::numeric, 10, 'O sweep foi de liquidez do 60m', 'Liquidez de 60m pesa mais que a de 15m.', 'ESTIMADO'),
      ('p5', 'PONTO', 15::numeric, 11, 'Confluencia de array: FVG + OB, ou FVG + BPR sobrepostos', 'Duas razoes na mesma regiao valem mais que uma.', 'ESTIMADO'),
      ('p6', 'PONTO', 15::numeric, 12, 'Reteste limpo - preco nao fechou alem do array', 'Pavio entrando na regiao e aceitavel. Corpo fechando alem enfraquece a ideia.', 'ESTIMADO')
  ) AS x(item_id, tipo, peso, ordem, label, ajuda, origem)
 WHERE v.strategy_id = 'reversao_htf' AND v.versao = 1
ON CONFLICT (version_id, item_id) DO UPDATE SET
    tipo=EXCLUDED.tipo, peso=EXCLUDED.peso, ordem=EXCLUDED.ordem,
    label=EXCLUDED.label, ajuda=EXCLUDED.ajuda, origem=EXCLUDED.origem;

