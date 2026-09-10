-- Seed do catalogo. Gerado de copa/strategies/playbook_anderson.json
-- Nao editar a mao: regerar do JSON para as duas fontes nao divergirem.

INSERT INTO copa_strategies (id, nome, descricao, mercados) VALUES
    ('playbook_anderson', 'Playbook Anderson', 'Maquina de duas camadas. HTF define destino: array nao-mitigado (FVG/OB) para onde a liquidez varrida entrega o preco. LTF define gatilho: MSS dentro do array, displacement deixa FVG, entrada no reteste desse FVG. Alvo na liquidez oposta (PDL/PDH). O sweep nao e o setup, e o transporte.', ARRAY['WIN', 'WDO'])
ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome, descricao = EXCLUDED.descricao, mercados = EXCLUDED.mercados;

INSERT INTO copa_strategy_versions (strategy_id, versao, score_minimo, calibracao, observacao) VALUES
    ('playbook_anderson', 1, 65, 'NAO_CALIBRADO', 'Todos os pesos e o score mínimo são ESTIMADO. Nenhum foi medido em backtest de WIN. Ver COPA_BTG_PLAN_V2.md Fase 3.')
ON CONFLICT (strategy_id, versao) DO UPDATE SET score_minimo = EXCLUDED.score_minimo, calibracao = EXCLUDED.calibracao, observacao = EXCLUDED.observacao;

INSERT INTO copa_strategy_items (version_id, item_id, tipo, peso, ordem, label, ajuda, origem)
SELECT v.id, x.item_id, x.tipo, x.peso, x.ordem, x.label, x.ajuda, x.origem
  FROM copa_strategy_versions v,
       (VALUES
           ('k1', 'KILL', 0::numeric, 0, 'Array HTF nao-mitigado identificado como DESTINO', 'FVG ou OB de 60m ou maior, ainda nao trabalhado. Marcar a regiao inteira (topo, CE, fundo). E para onde o preco esta sendo entregue.', 'ESTIMADO'),
           ('k2', 'KILL', 0::numeric, 1, 'A liquidez que entrega o preco no array foi VARRIDA', 'BSL/SSL ou topo/fundo HTF. Preco penetrou a regiao, rejeitou e fechou de volta. O sweep e o transporte, nao o setup.', 'ESTIMADO'),
           ('k3', 'KILL', 0::numeric, 2, 'Preco alcancou a REGIAO do array, no lado certo', 'Premium para venda, discount para compra. Regiao, nao linha: nao precisa penetrar exatamente o CE nem um preco especifico.', 'ESTIMADO'),
           ('k4', 'KILL', 0::numeric, 3, 'MSS no LTF em vela FECHADA, dentro do array', 'Contra a perna que trouxe o preco ate aqui. Vela fechada, nao em formacao. E a virada de estrutura no timeframe de execucao.', 'ESTIMADO'),
           ('k5', 'KILL', 0::numeric, 4, 'O displacement do MSS deixou FVG no LTF', 'A perna que rompeu a estrutura precisa ter deixado desbalanco. Sem FVG nao ha ponto de entrada definido.', 'ESTIMADO'),
           ('k6', 'KILL', 0::numeric, 5, 'Entrada no RETESTE do FVG do LTF', 'Licao 4. Nao perseguir preco. Espera o retorno na regiao do FVG.', 'ESTIMADO'),
           ('k7', 'KILL', 0::numeric, 6, 'Alvo = liquidez oposta identificada · stop acima/abaixo do TOPO/FUNDO do swing · RR >= 2', 'Alvo em PDL/PDH ou liquidez clara, nunca numero arbitrario. Stop ancorado no extremo do swing que originou o MSS, NAO na barra do FVG.', 'ESTIMADO'),
           ('p1', 'PONTO', 14::numeric, 7, 'Corpos respeitaram o CE do array HTF', 'Referencia de forca, nao regra rigida. Corpos que nao fecham alem do 50% indicam que a regiao esta segurando.', 'ESTIMADO'),
           ('p2', 'PONTO', 14::numeric, 8, 'Confluencia de array - FVG e OB sobrepostos', 'Duas razoes na mesma regiao valem mais que uma.', 'ESTIMADO'),
           ('p3', 'PONTO', 14::numeric, 9, 'Displacement forte no MSS', 'Corpo grande em relacao a media. Rompimento convicto, nao arrastado.', 'ESTIMADO'),
           ('p4', 'PONTO', 14::numeric, 10, 'Inducao: micro-sweep no reteste antes da entrada', 'O pullback varreu um micro extremo antes de virar. Sem inducao, VOCE e a liquidez.', 'ESTIMADO'),
           ('p6', 'PONTO', 11::numeric, 11, 'Array fresco - deixado na sessao anterior e ainda nao tocado', 'Array virgem reage melhor que array ja trabalhado varias vezes.', 'ESTIMADO'),
           ('p7', 'PONTO', 11::numeric, 12, 'Caminho limpo ate o alvo - sem array oposto no meio', 'Um FVG ou OB contrario entre a entrada e o alvo trava o movimento.', 'ESTIMADO'),
           ('p8', 'PONTO', 11::numeric, 13, 'SMT - WIN e WDO contando a mesma historia', 'Divergencia entre os dois no momento do sweep reforca a leitura.', 'ESTIMADO'),
           ('p9', 'PONTO', 11::numeric, 14, 'Sem noticia de alto impacto nos proximos 30 min', 'Consultar a agenda preenchida na pre-sessao.', 'ESTIMADO')
       ) AS x(item_id, tipo, peso, ordem, label, ajuda, origem)
 WHERE v.strategy_id = 'playbook_anderson' AND v.versao = 1
ON CONFLICT (version_id, item_id) DO UPDATE SET
    tipo = EXCLUDED.tipo, peso = EXCLUDED.peso, ordem = EXCLUDED.ordem,
    label = EXCLUDED.label, ajuda = EXCLUDED.ajuda, origem = EXCLUDED.origem;
