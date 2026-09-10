-- =============================================================================
-- SCHEMA V2 — COCKPIT COPA BTG
-- =============================================================================
-- Princípio central: o checklist é capturado POR TRADE, não por dia, e
-- NORMALIZADO (uma linha por item por trade). É isso que transforma
-- "esse item do checklist paga?" em um GROUP BY em vez de arqueologia em JSONB.
--
-- Segundo princípio: peso de checklist muda com o tempo. O trade guarda a
-- VERSÃO da estratégia que valia no momento da entrada. Sem isso, recalibrar
-- os pesos reescreve o passado e invalida toda comparação histórica.
--
-- Executar no Supabase SQL Editor.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. AUTENTICAÇÃO
-- -----------------------------------------------------------------------------
-- O schema v1 usava `FOR ALL USING (true)`: qualquer pessoa com a chave anon
-- (que é pública, vai no bundle do navegador) podia ler, alterar e APAGAR todos
-- os trades. Com o app publicado no Vercel, isso é journal world-writable.
--
-- V2 amarra tudo a auth.uid(). Exige login no app.
-- -----------------------------------------------------------------------------


-- =============================================================================
-- 1. ESTRATÉGIA VERSIONADA
-- =============================================================================

CREATE TABLE IF NOT EXISTS strategies (
    id              TEXT PRIMARY KEY,              -- 'playbook_anderson'
    nome            TEXT NOT NULL,
    descricao       TEXT NOT NULL DEFAULT '',
    mercados        TEXT[] NOT NULL DEFAULT '{}',
    ativa           BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cada recalibração cria uma versão nova. Versão antiga nunca é editada:
-- é o que permite comparar trades de antes e depois da calibração.
CREATE TABLE IF NOT EXISTS strategy_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id     TEXT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    versao          INTEGER NOT NULL,
    score_minimo    NUMERIC NOT NULL,
    -- NAO_CALIBRADO | EM_CALIBRACAO | CALIBRADO
    calibracao      TEXT NOT NULL DEFAULT 'NAO_CALIBRADO',
    observacao      TEXT NOT NULL DEFAULT '',
    vigente_desde   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (strategy_id, versao)
);

CREATE TABLE IF NOT EXISTS strategy_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES strategy_versions(id) ON DELETE CASCADE,
    item_id         TEXT NOT NULL,                 -- 'k1', 'p3'
    tipo            TEXT NOT NULL CHECK (tipo IN ('KILL', 'PONTO')),
    peso            NUMERIC NOT NULL DEFAULT 0,
    ordem           INTEGER NOT NULL DEFAULT 0,
    label           TEXT NOT NULL,
    ajuda           TEXT NOT NULL DEFAULT '',
    -- MEDIDO exige n_amostra e periodo_medicao preenchidos. ESTIMADO é julgamento.
    -- A interface MOSTRA a diferença. Nunca promover sem medição.
    origem          TEXT NOT NULL DEFAULT 'ESTIMADO' CHECK (origem IN ('MEDIDO', 'ESTIMADO')),
    n_amostra       INTEGER,
    periodo_medicao TEXT,
    delta_expectancia NUMERIC,
    UNIQUE (version_id, item_id)
);

-- KILL tem peso 0; a soma dos PONTO de uma versão tem que dar 100.
CREATE OR REPLACE FUNCTION check_pesos_somam_100() RETURNS TRIGGER AS $$
DECLARE soma NUMERIC;
BEGIN
    SELECT COALESCE(SUM(peso), 0) INTO soma
      FROM strategy_items
     WHERE version_id = COALESCE(NEW.version_id, OLD.version_id)
       AND tipo = 'PONTO';
    IF soma <> 0 AND soma <> 100 THEN
        RAISE EXCEPTION 'Pesos PONTO da versão % somam %, esperado 100',
              COALESCE(NEW.version_id, OLD.version_id), soma;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pesos_100 ON strategy_items;
CREATE CONSTRAINT TRIGGER trg_pesos_100
    AFTER INSERT OR UPDATE OR DELETE ON strategy_items
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_pesos_somam_100();


-- =============================================================================
-- 2. FASES DA COPA
-- =============================================================================

CREATE TABLE IF NOT EXISTS copa_phases (
    id              TEXT PRIMARY KEY,              -- 'etapa1'
    nome            TEXT NOT NULL,
    data_inicio     DATE NOT NULL,
    data_fim        DATE NOT NULL,
    dias            INTEGER NOT NULL,
    tem_descarte    BOOLEAN NOT NULL DEFAULT true,
    ordem           INTEGER NOT NULL
);

INSERT INTO copa_phases (id, nome, data_inicio, data_fim, dias, tem_descarte, ordem) VALUES
    ('etapa1',     'Classificatória Etapa 1', '2026-09-14', '2026-09-17', 4, true,  1),
    ('etapa2',     'Classificatória Etapa 2', '2026-09-21', '2026-09-24', 4, true,  2),
    ('repescagem', 'Repescagem',              '2026-09-28', '2026-09-30', 3, true,  3),
    ('semifinal',  'Semifinal',               '2026-10-13', '2026-10-16', 4, true,  4),
    ('final',      'Final presencial',        '2026-10-29', '2026-10-29', 1, false, 5)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 3. SESSÃO DO DIA (pré-sessão)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    data              DATE NOT NULL,
    phase_id          TEXT REFERENCES copa_phases(id),   -- NULL = dia de treino

    bias_d1           TEXT NOT NULL DEFAULT 'INDEFINIDO' CHECK (bias_d1 IN ('COMPRA','VENDA','INDEFINIDO')),
    bias_h1           TEXT NOT NULL DEFAULT 'INDEFINIDO' CHECK (bias_h1 IN ('COMPRA','VENDA','INDEFINIDO')),
    contexto          TEXT NOT NULL DEFAULT 'INDEFINIDO' CHECK (contexto IN ('TENDENCIA','RANGE','INDEFINIDO')),

    -- [{label, preco}] — arrays HTF e pools de liquidez mapeados antes do pregão
    niveis            JSONB NOT NULL DEFAULT '[]',
    -- [{evento, horario, impacto}]
    agenda            JSONB NOT NULL DEFAULT '[]',

    sono              SMALLINT NOT NULL DEFAULT 3 CHECK (sono BETWEEN 0 AND 5),
    tilt              SMALLINT NOT NULL DEFAULT 0 CHECK (tilt BETWEEN 0 AND 5),
    pressao           SMALLINT NOT NULL DEFAULT 0 CHECK (pressao BETWEEN 0 AND 5),

    meta_dia          NUMERIC NOT NULL DEFAULT 0,
    limite_perda_dia  NUMERIC NOT NULL DEFAULT 300,
    max_trades_dia    SMALLINT NOT NULL DEFAULT 3,
    modo              TEXT NOT NULL DEFAULT 'NORMAL' CHECK (modo IN ('NORMAL','DEFENSIVO')),

    notas             TEXT NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, data)
);


-- =============================================================================
-- 4. TRADES
-- =============================================================================

CREATE TABLE IF NOT EXISTS trades (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id        UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    -- Versão da estratégia VIGENTE NA ENTRADA. Recalibrar não reescreve o passado.
    version_id        UUID NOT NULL REFERENCES strategy_versions(id),

    mercado           TEXT NOT NULL CHECK (mercado IN ('WIN','WDO')),
    direcao           TEXT NOT NULL CHECK (direcao IN ('COMPRA','VENDA')),

    -- Janela em que a entrada foi registrada. É o que permite medir se
    -- 10:00-11:00 realmente é o filé, em vez de acreditar que é.
    janela            TEXT NOT NULL CHECK (janela IN ('PRIME','VALIDA','FORA')),
    hora_entrada      TIMESTAMPTZ NOT NULL DEFAULT now(),

    score             NUMERIC NOT NULL,
    score_minimo      NUMERIC NOT NULL,       -- o efetivo no momento (65 ou 80)
    grade             TEXT NOT NULL,

    entrada           NUMERIC NOT NULL,
    stop              NUMERIC NOT NULL,
    alvo              NUMERIC NOT NULL,
    contratos         SMALLINT NOT NULL CHECK (contratos > 0),
    rr_planejado      NUMERIC NOT NULL,

    status            TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO','FECHADO')),
    saida             NUMERIC,
    hora_saida        TIMESTAMPTZ,
    motivo_saida      TEXT CHECK (motivo_saida IN ('ALVO','STOP','MANUAL')),
    -- Só quando motivo_saida = MANUAL: o que o preço fez DEPOIS da saída.
    -- É o que permite calcular custo da indisciplina sem feed de mercado.
    desfecho_plano    TEXT CHECK (desfecho_plano IN ('BATEU_ALVO','BATEU_STOP','NAO_SEI')),

    pontos_real       NUMERIC,
    pnl_real          NUMERIC,
    pnl_plano         NUMERIC,               -- resultado se tivesse ido a alvo/stop

    respeitou_plano   BOOLEAN,
    antecipou_stop    BOOLEAN,
    parcial_emocional BOOLEAN,
    mudou_alvo        BOOLEAN,

    screenshot_url    TEXT,
    notas             TEXT NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Coerência de direção: impede registrar stop/alvo do lado errado.
    CONSTRAINT chk_direcao_coerente CHECK (
        (direcao = 'COMPRA' AND stop < entrada AND alvo > entrada) OR
        (direcao = 'VENDA'  AND stop > entrada AND alvo < entrada)
    ),
    CONSTRAINT chk_fechado_completo CHECK (
        status = 'ABERTO' OR (saida IS NOT NULL AND motivo_saida IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_trades_session ON trades(session_id);
CREATE INDEX IF NOT EXISTS idx_trades_status  ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_hora    ON trades(hora_entrada DESC);


-- =============================================================================
-- 5. TRADE_ITEMS — a peça central
-- =============================================================================
-- Uma linha por item por trade. Snapshot imutável do que estava marcado no
-- momento da entrada, com o peso que valia então.
--
-- É isto que faz "esse item paga?" ser um GROUP BY.
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_items (
    trade_id        UUID NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    item_id         TEXT NOT NULL,
    tipo            TEXT NOT NULL CHECK (tipo IN ('KILL','PONTO')),
    checked         BOOLEAN NOT NULL,
    peso_no_momento NUMERIC NOT NULL DEFAULT 0,
    PRIMARY KEY (trade_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_trade_items_item ON trade_items(item_id, checked);


-- =============================================================================
-- 6. SEGUNDO CÉREBRO
-- =============================================================================

CREATE TABLE IF NOT EXISTS trading_notes (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    content       TEXT NOT NULL,
    camada        INTEGER NOT NULL CHECK (camada BETWEEN 1 AND 5),
    categoria     TEXT NOT NULL DEFAULT 'ICT',
    status        TEXT NOT NULL DEFAULT 'validado',
    tags          TEXT[] DEFAULT '{}',
    linked_notes  TEXT[] DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =============================================================================
-- 7. INTELIGÊNCIA — views
-- =============================================================================

-- 7.1 Desempenho por item: com marcado vs sem marcado.
-- Responde a pergunta que a Copa não dá amostra para responder ao vivo,
-- e que o backtest da Fase 3 vai alimentar.
CREATE OR REPLACE VIEW v_item_performance AS
WITH base AS (
    SELECT ti.item_id, ti.tipo, ti.checked, t.pnl_real, t.user_id
      FROM trade_items ti
      JOIN trades t ON t.id = ti.trade_id
     WHERE t.status = 'FECHADO' AND t.pnl_real IS NOT NULL
)
SELECT
    user_id,
    item_id,
    tipo,
    count(*) FILTER (WHERE checked)                                    AS n_marcado,
    round(100.0 * count(*) FILTER (WHERE checked AND pnl_real > 0)
          / NULLIF(count(*) FILTER (WHERE checked), 0), 1)             AS winrate_marcado,
    round(avg(pnl_real) FILTER (WHERE checked), 2)                     AS exp_marcado,
    count(*) FILTER (WHERE NOT checked)                                AS n_nao,
    round(100.0 * count(*) FILTER (WHERE NOT checked AND pnl_real > 0)
          / NULLIF(count(*) FILTER (WHERE NOT checked), 0), 1)         AS winrate_nao,
    round(avg(pnl_real) FILTER (WHERE NOT checked), 2)                 AS exp_nao,
    (count(*) FILTER (WHERE checked) < 20
     OR count(*) FILTER (WHERE NOT checked) < 20)                      AS amostra_baixa
  FROM base
 GROUP BY user_id, item_id, tipo;

-- 7.2 O score prevê alguma coisa?
-- Se as faixas altas não performarem melhor que as baixas, o score é decorativo
-- e os pesos precisam mudar. É o teste de honestidade do sistema inteiro.
CREATE OR REPLACE VIEW v_score_buckets AS
SELECT
    user_id,
    width_bucket(score, 0, 100, 5) * 20 - 20                          AS faixa_min,
    count(*)                                                          AS n,
    round(100.0 * count(*) FILTER (WHERE pnl_real > 0) / count(*), 1)  AS winrate,
    round(avg(pnl_real), 2)                                           AS expectancia,
    round(sum(pnl_real), 2)                                           AS pnl
  FROM trades
 WHERE status = 'FECHADO' AND pnl_real IS NOT NULL
 GROUP BY user_id, 2
 ORDER BY 2;

-- 7.3 A janela nobre é mesmo o filé?
CREATE OR REPLACE VIEW v_janela_performance AS
SELECT
    user_id,
    janela,
    count(*)                                                          AS n,
    round(100.0 * count(*) FILTER (WHERE pnl_real > 0) / count(*), 1)  AS winrate,
    round(avg(pnl_real), 2)                                           AS expectancia,
    round(sum(pnl_real), 2)                                           AS pnl,
    round(avg(rr_planejado), 2)                                       AS rr_medio
  FROM trades
 WHERE status = 'FECHADO' AND pnl_real IS NOT NULL
 GROUP BY user_id, janela;

-- 7.4 Custo da indisciplina, em reais.
CREATE OR REPLACE VIEW v_disciplina AS
SELECT
    user_id,
    count(*) FILTER (WHERE NOT COALESCE(respeitou_plano, true)
                        OR COALESCE(antecipou_stop, false)
                        OR COALESCE(parcial_emocional, false)
                        OR COALESCE(mudou_alvo, false))               AS trades_com_desvio,
    round(sum(COALESCE(pnl_plano, pnl_real) - pnl_real)
          FILTER (WHERE NOT COALESCE(respeitou_plano, true)
                     OR COALESCE(antecipou_stop, false)
                     OR COALESCE(parcial_emocional, false)
                     OR COALESCE(mudou_alvo, false)), 2)              AS custo_total,
    count(*) FILTER (WHERE COALESCE(antecipou_stop, false))           AS n_antecipou_stop,
    count(*) FILTER (WHERE COALESCE(parcial_emocional, false))        AS n_parcial_emocional,
    count(*) FILTER (WHERE COALESCE(mudou_alvo, false))               AS n_mudou_alvo
  FROM trades
 WHERE status = 'FECHADO' AND pnl_real IS NOT NULL
 GROUP BY user_id;

-- 7.5 Resultado por dia, com marcação do pior dia de cada fase.
-- O regulamento descarta o pior dia. Depois que ele é consumido, todo dia
-- negativo seguinte entra direto no placar.
CREATE OR REPLACE VIEW v_dia_resultado AS
SELECT
    s.user_id,
    s.data,
    s.phase_id,
    round(sum(t.pnl_real), 2)                                         AS pnl_dia,
    count(t.id)                                                       AS n_trades,
    sum(t.contratos)                                                  AS contratos_dia,
    (sum(t.pnl_real) = min(sum(t.pnl_real)) OVER (
        PARTITION BY s.user_id, s.phase_id))                          AS eh_pior_dia
  FROM sessions s
  JOIN trades t ON t.session_id = s.id
 WHERE t.status = 'FECHADO' AND t.pnl_real IS NOT NULL
 GROUP BY s.user_id, s.data, s.phase_id;

-- 7.6 Placar da fase: bruto, efetivo (com descarte) e eficiência.
-- reais_por_contrato importa porque o desempate oficial da Copa é
-- "vencerá aquele que operar o menor número de contratos".
CREATE OR REPLACE VIEW v_fase_placar AS
SELECT
    d.user_id,
    d.phase_id,
    p.nome,
    count(*)                                                          AS dias_operados,
    round(sum(d.pnl_dia), 2)                                          AS placar_bruto,
    round(sum(d.pnl_dia) - CASE WHEN p.tem_descarte AND count(*) >= 2
                                THEN min(d.pnl_dia) ELSE 0 END, 2)    AS placar_efetivo,
    round(min(d.pnl_dia), 2)                                          AS pior_dia,
    (min(d.pnl_dia) < 0)                                              AS mulligan_consumido,
    sum(d.contratos_dia)                                              AS contratos_total,
    round(sum(d.pnl_dia) / NULLIF(sum(d.contratos_dia), 0), 2)        AS reais_por_contrato
  FROM v_dia_resultado d
  JOIN copa_phases p ON p.id = d.phase_id
 GROUP BY d.user_id, d.phase_id, p.nome, p.tem_descarte;


-- =============================================================================
-- 8. RLS — cada usuário enxerga só o que é dele
-- =============================================================================

ALTER TABLE sessions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades        ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_items   ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sessions_own ON sessions;
CREATE POLICY sessions_own ON sessions
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS trades_own ON trades;
CREATE POLICY trades_own ON trades
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS notes_own ON trading_notes;
CREATE POLICY notes_own ON trading_notes
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- trade_items não tem user_id: herda o dono pelo trade.
DROP POLICY IF EXISTS trade_items_own ON trade_items;
CREATE POLICY trade_items_own ON trade_items
    FOR ALL USING (
        EXISTS (SELECT 1 FROM trades t WHERE t.id = trade_id AND t.user_id = auth.uid())
    ) WITH CHECK (
        EXISTS (SELECT 1 FROM trades t WHERE t.id = trade_id AND t.user_id = auth.uid())
    );

-- Catálogo é leitura pública para usuário autenticado, escrita só por service_role.
ALTER TABLE strategies        ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategy_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategy_items    ENABLE ROW LEVEL SECURITY;
ALTER TABLE copa_phases       ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS strategies_read ON strategies;
CREATE POLICY strategies_read ON strategies
    FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS versions_read ON strategy_versions;
CREATE POLICY versions_read ON strategy_versions
    FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS items_read ON strategy_items;
CREATE POLICY items_read ON strategy_items
    FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS phases_read ON copa_phases;
CREATE POLICY phases_read ON copa_phases
    FOR SELECT TO authenticated USING (true);
