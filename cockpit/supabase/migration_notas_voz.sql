-- =============================================================================
-- MIGRACAO — NOTAS DE VOZ E CUSTO POR TIPO DE ERRO
-- =============================================================================
-- Depois de um trade ruim, digitar e a ultima coisa que o operador vai fazer.
-- Falar e natural. Entao a nota e por audio, e um agente transcreve, organiza
-- por topicos e CLASSIFICA o erro numa taxonomia fechada.
--
-- A taxonomia fechada e o que torna o resto possivel. Texto livre nao agrega:
-- "operei mal hoje" nao vira numero. "ANTECIPOU_STOP" vira.
--
-- Com a classificacao, o sistema responde a pergunta que muda comportamento:
-- "esse erro especifico ja te custou R$ X em N trades."
--
-- CONFORMIDADE: o agente organiza o que o OPERADOR disse sobre a propria
-- execucao. Nunca analisa mercado, nunca sugere trade, nunca le grafico. Se ele
-- opinar sobre o mercado, saiu do escopo e virou assessoria — proibido.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. TAXONOMIA DE ERROS
-- -----------------------------------------------------------------------------
-- Fechada de proposito. Categoria nova entra por migracao, com motivo, nao por
-- digitacao livre no calor.

CREATE TABLE IF NOT EXISTS copa_tipos_erro (
    id          TEXT PRIMARY KEY,
    nome        TEXT NOT NULL,
    descricao   TEXT NOT NULL,
    -- Onde o erro nasce: antes, durante ou depois da ordem.
    momento     TEXT NOT NULL CHECK (momento IN ('PRE', 'ENTRADA', 'CONDUCAO', 'POS')),
    ordem       INTEGER NOT NULL DEFAULT 0
);

INSERT INTO copa_tipos_erro (id, nome, descricao, momento, ordem) VALUES
 ('SEM_PRESESSAO',     'Operou sem pre-sessao',      'Abriu o pregao sem mapear liquidez, arrays e escolher o setup.', 'PRE', 1),
 ('FORA_DO_SETUP',     'Fora do setup declarado',    'Operou um setup diferente do que escolheu de manha, frio.', 'PRE', 2),
 ('FORA_DA_JANELA',    'Fora da janela',             'Operou fora de 09:00-12:00.', 'PRE', 3),
 ('RUIDO_EXTERNO',     'Ruido externo',              'Decisao influenciada por opiniao de terceiro, sala ou video.', 'PRE', 4),
 ('PRESSAO_FINANCEIRA','Pressao financeira',         'Operou precisando do dinheiro, e isso mudou a decisao.', 'PRE', 5),

 ('SEM_CONFIRMACAO',   'Antecipou sem confirmacao',  'Entrou antes do gatilho confirmar. Adivinhou em vez de esperar.', 'ENTRADA', 10),
 ('PERSEGUIU_PRECO',   'Perseguiu o preco',          'Entrou correndo atras em vez de esperar o reteste.', 'ENTRADA', 11),
 ('FORA_DO_TAMANHO',   'Fora do tamanho declarado',  'Usou mais ou menos contratos do que declarou de manha.', 'ENTRADA', 12),
 ('MELHOR_PRECO',      'Cacando preco melhor',       'Deixou de entrar no ponto do plano querendo preco melhor para carregar mais.', 'ENTRADA', 13),
 ('EXCESSO_TRADES',    'Trades demais',              'Passou do numero de operacoes que o plano permite.', 'ENTRADA', 14),
 ('REVANCHE',          'Revanche',                   'Operou para recuperar a perda anterior.', 'ENTRADA', 15),

 ('ANTECIPOU_STOP',    'Antecipou o stop',           'Saiu antes do stop ser atingido.', 'CONDUCAO', 20),
 ('PARCIAL_EMOCIONAL', 'Parcial emocional',          'Realizou parcial por medo, fora do plano.', 'CONDUCAO', 21),
 ('MUDOU_ALVO',        'Mudou o alvo',               'Alterou o alvo com a posicao aberta.', 'CONDUCAO', 22),
 ('AUMENTOU_POSICAO',  'Aumentou posicao contra',    'Acrescentou contratos numa posicao perdedora.', 'CONDUCAO', 23),

 ('SEM_REGISTRO',      'Nao registrou',              'Operou sem passar pelo checklist ou sem anexar print.', 'POS', 30),
 ('SEM_REVISAO',       'Nao revisou',                'Fechou o dia sem classificar a execucao nem anotar o que aconteceu.', 'POS', 31)
ON CONFLICT (id) DO UPDATE
   SET nome = EXCLUDED.nome, descricao = EXCLUDED.descricao,
       momento = EXCLUDED.momento, ordem = EXCLUDED.ordem;


-- -----------------------------------------------------------------------------
-- 2. NOTAS DE VOZ
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS copa_notas_voz (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id     UUID REFERENCES copa_sessions(id) ON DELETE CASCADE,
    -- Nota pode ser sobre um trade especifico ou sobre o dia inteiro.
    trade_id       UUID REFERENCES copa_trades(id) ON DELETE SET NULL,

    audio_path     TEXT NOT NULL,
    duracao_seg    INTEGER,

    -- PENDENTE -> o audio subiu, o agente ainda nao rodou
    -- PRONTO    -> transcrito e classificado
    -- ERRO      -> falhou; motivo em erro_msg. NUNCA apagar o audio por falha.
    status         TEXT NOT NULL DEFAULT 'PENDENTE'
                   CHECK (status IN ('PENDENTE', 'PRONTO', 'ERRO')),
    erro_msg       TEXT,

    transcricao    TEXT,
    -- [{ "topico": "...", "texto": "..." }]
    topicos        JSONB NOT NULL DEFAULT '[]',
    resumo         TEXT,

    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    processado_em  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notas_voz_data ON copa_notas_voz(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_notas_voz_status ON copa_notas_voz(status);


-- Erros identificados numa nota. Uma nota pode carregar varios.
-- Tabela separada, nao array: e o que permite agregar custo por tipo.
CREATE TABLE IF NOT EXISTS copa_nota_erros (
    nota_id     UUID NOT NULL REFERENCES copa_notas_voz(id) ON DELETE CASCADE,
    tipo_erro   TEXT NOT NULL REFERENCES copa_tipos_erro(id),
    -- Trecho da transcricao que sustenta a classificacao. Sem evidencia, o
    -- agente esta adivinhando.
    evidencia   TEXT,
    -- Confirmado pelo operador. O agente classifica; quem decide e ele.
    confirmado  BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (nota_id, tipo_erro)
);

CREATE INDEX IF NOT EXISTS idx_nota_erros_tipo ON copa_nota_erros(tipo_erro);


-- -----------------------------------------------------------------------------
-- 3. RLS
-- -----------------------------------------------------------------------------

ALTER TABLE copa_notas_voz  ENABLE ROW LEVEL SECURITY;
ALTER TABLE copa_nota_erros ENABLE ROW LEVEL SECURITY;
ALTER TABLE copa_tipos_erro ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS notas_voz_own ON copa_notas_voz;
CREATE POLICY notas_voz_own ON copa_notas_voz
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS nota_erros_own ON copa_nota_erros;
CREATE POLICY nota_erros_own ON copa_nota_erros
    FOR ALL USING (
        EXISTS (SELECT 1 FROM copa_notas_voz n WHERE n.id = nota_id AND n.user_id = auth.uid())
    ) WITH CHECK (
        EXISTS (SELECT 1 FROM copa_notas_voz n WHERE n.id = nota_id AND n.user_id = auth.uid())
    );

DROP POLICY IF EXISTS tipos_erro_read ON copa_tipos_erro;
CREATE POLICY tipos_erro_read ON copa_tipos_erro
    FOR SELECT TO authenticated USING (true);


-- -----------------------------------------------------------------------------
-- 4. A VIEW QUE MUDA COMPORTAMENTO
-- -----------------------------------------------------------------------------
-- "Esse erro ja te custou R$ X."
--
-- Custo so existe quando a nota esta amarrada a um trade fechado. Nota do dia,
-- sem trade, conta ocorrencia mas nao custo — e correto: nem todo erro tem
-- preco isolavel.

DROP VIEW IF EXISTS v_copa_erro_custo;

CREATE VIEW v_copa_erro_custo AS
SELECT
    n.user_id,
    e.tipo_erro,
    te.nome,
    te.momento,
    count(*)                                                        AS ocorrencias,
    count(DISTINCT n.trade_id) FILTER (WHERE n.trade_id IS NOT NULL) AS trades_afetados,
    -- Quanto o plano teria dado a mais nos trades marcados com este erro.
    round(sum(COALESCE(t.pnl_plano, t.pnl_real) - t.pnl_real)
          FILTER (WHERE t.id IS NOT NULL), 2)                       AS custo_total,
    round(sum(t.pnl_real) FILTER (WHERE t.id IS NOT NULL), 2)       AS pnl_dos_trades,
    max(n.criado_em)                                                AS ultima_vez
  FROM copa_nota_erros e
  JOIN copa_notas_voz n  ON n.id = e.nota_id
  JOIN copa_tipos_erro te ON te.id = e.tipo_erro
  LEFT JOIN copa_trades t ON t.id = n.trade_id AND t.status = 'FECHADO'
 WHERE e.confirmado
 GROUP BY n.user_id, e.tipo_erro, te.nome, te.momento
 ORDER BY custo_total DESC NULLS LAST;
