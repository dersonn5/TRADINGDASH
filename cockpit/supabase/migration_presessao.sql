-- =============================================================================
-- MIGRACAO — RITUAL DE PRE-SESSAO
-- =============================================================================
-- Fecha tres lacunas de controle, todas do mesmo tipo: decisao tomada DURANTE
-- o pregao que deveria ter sido tomada ANTES dele.
--
--   1. pre-sessao nao era obrigatoria  -> dava para operar sem mapear nada
--   2. setup escolhido no calor        -> agora e escolhido frio e trava
--   3. tamanho digitado na hora        -> agora e declarado frio e trava
--
-- Mais a evidencia: print do grafico marcado antes da abertura, e print por
-- trade.
--
-- CONFORMIDADE: o sistema ARMAZENA e EXIBE a imagem. Nunca le, nunca analisa,
-- nunca extrai preco dela. Print anexado pelo operador e diario de bordo, igual
-- a foto. Parsing de grafico seria deteccao de setup, que e proibido.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. COLUNAS NOVAS EM copa_sessions
-- -----------------------------------------------------------------------------

ALTER TABLE copa_sessions
  -- Print do grafico HTF marcado, tirado antes das 09:00.
  ADD COLUMN IF NOT EXISTS screenshot_path TEXT,

  -- Setup escolhido para o dia. NENHUM e decisao valida e e a mais barata.
  -- Escolhido frio, trava durante o pregao.
  ADD COLUMN IF NOT EXISTS setup_do_dia TEXT
      CHECK (setup_do_dia IN ('reversao_htf', 'continuidade_tendencia', 'NENHUM')),

  -- Tamanho declarado frio. E o unico canal por onde a ganancia entrava sem
  -- passar por trava nenhuma.
  ADD COLUMN IF NOT EXISTS contratos_declarados SMALLINT
      CHECK (contratos_declarados > 0),

  -- Marca o momento em que a pre-sessao foi dada por completa. Enquanto for
  -- NULL, o gate nao libera trade nenhum.
  ADD COLUMN IF NOT EXISTS fechada_em TIMESTAMPTZ;


-- Uma pre-sessao so pode ser fechada com tudo preenchido. O banco recusa
-- fechar pela metade, entao a regra nao depende da tela.
ALTER TABLE copa_sessions DROP CONSTRAINT IF EXISTS chk_presessao_completa;
ALTER TABLE copa_sessions ADD CONSTRAINT chk_presessao_completa CHECK (
    fechada_em IS NULL
    OR (
        setup_do_dia IS NOT NULL
        AND screenshot_path IS NOT NULL
        AND bias_h1 <> 'INDEFINIDO'
        AND contexto <> 'INDEFINIDO'
        AND jsonb_array_length(niveis) >= 2
        AND (setup_do_dia = 'NENHUM' OR contratos_declarados IS NOT NULL)
    )
);


-- -----------------------------------------------------------------------------
-- 2. PRINT POR TRADE
-- -----------------------------------------------------------------------------
-- copa_trades.screenshot_url ja existe. Renomeado para _path por coerencia:
-- guardamos o caminho no storage, nao uma URL assinada (que expira).

ALTER TABLE copa_trades RENAME COLUMN screenshot_url TO screenshot_path;


-- -----------------------------------------------------------------------------
-- 3. STORAGE
-- -----------------------------------------------------------------------------
-- Bucket privado. Imagem de journal nao vai para link publico.

-- O bucket NAO se cria por SQL. O Supabase bloqueia INSERT direto em
-- storage.buckets, e a instrucao falha em silencio: o script roda inteiro, diz
-- sucesso, e o bucket nao existe. So aparece na primeira tentativa de upload,
-- como "Bucket not found".
--
-- Criar pelo painel: Storage > New bucket
--   nome: copa-prints
--   public: OFF
--   file size limit: 10 MB
--   allowed MIME types: image/png, image/jpeg, image/webp
--
-- Ou pela API de storage com a service key:
--   POST <SUPABASE_URL>/storage/v1/bucket
--   { "id": "copa-prints", "name": "copa-prints", "public": false,
--     "file_size_limit": 10485760,
--     "allowed_mime_types": ["image/png","image/jpeg","image/webp"] }
--
-- As politicas abaixo, sim, sao SQL e funcionam — mas so depois que o bucket
-- existir.


-- Cada usuario so enxerga e escreve na propria pasta: copa-prints/<uid>/...
DROP POLICY IF EXISTS prints_select_own ON storage.objects;
CREATE POLICY prints_select_own ON storage.objects
    FOR SELECT TO authenticated
    USING (bucket_id = 'copa-prints' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS prints_insert_own ON storage.objects;
CREATE POLICY prints_insert_own ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'copa-prints' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS prints_delete_own ON storage.objects;
CREATE POLICY prints_delete_own ON storage.objects
    FOR DELETE TO authenticated
    USING (bucket_id = 'copa-prints' AND (storage.foldername(name))[1] = auth.uid()::text);


-- -----------------------------------------------------------------------------
-- 4. VIEW — ADESAO AO PROCESSO
-- -----------------------------------------------------------------------------
-- Mede processo, nao resultado. E o numero que responde "eu segui o protocolo?"
-- independente de ter dado dinheiro.

DROP VIEW IF EXISTS v_copa_adesao;

CREATE VIEW v_copa_adesao AS
WITH dias AS (
    SELECT s.user_id,
           s.data,
           s.phase_id,
           (s.fechada_em IS NOT NULL)                                    AS presessao_feita,
           s.setup_do_dia,
           count(t.id) FILTER (WHERE t.id IS NOT NULL)                   AS n_trades,
           -- Trade fora do setup declarado do dia.
           count(t.id) FILTER (
               WHERE t.id IS NOT NULL
                 AND s.setup_do_dia IS NOT NULL
                 AND v.strategy_id <> s.setup_do_dia)                    AS trades_fora_do_setup,
           -- Trade com tamanho diferente do declarado.
           count(t.id) FILTER (
               WHERE t.id IS NOT NULL
                 AND s.contratos_declarados IS NOT NULL
                 AND t.contratos <> s.contratos_declarados)              AS trades_fora_do_tamanho,
           count(t.id) FILTER (WHERE t.screenshot_path IS NULL)          AS trades_sem_print,
           count(t.id) FILTER (WHERE t.notas LIKE '[EXEC:A]%')           AS exec_a,
           count(t.id) FILTER (WHERE t.notas LIKE '[EXEC:B]%')           AS exec_b,
           count(t.id) FILTER (WHERE t.notas LIKE '[EXEC:C]%')           AS exec_c
      FROM copa_sessions s
      LEFT JOIN copa_trades t ON t.session_id = s.id
      LEFT JOIN copa_strategy_versions v ON v.id = t.version_id
     GROUP BY s.user_id, s.data, s.phase_id, s.fechada_em, s.setup_do_dia, s.contratos_declarados
)
SELECT
    user_id,
    data,
    phase_id,
    presessao_feita,
    setup_do_dia,
    n_trades,
    trades_fora_do_setup,
    trades_fora_do_tamanho,
    trades_sem_print,
    exec_a, exec_b, exec_c,
    -- Dia limpo: pre-sessao feita, nenhum trade fora do setup, nenhum fora do
    -- tamanho, nenhum sem print, e nenhuma execucao C.
    (presessao_feita
       AND trades_fora_do_setup = 0
       AND trades_fora_do_tamanho = 0
       AND trades_sem_print = 0
       AND exec_c = 0)                                                   AS dia_limpo
  FROM dias;
