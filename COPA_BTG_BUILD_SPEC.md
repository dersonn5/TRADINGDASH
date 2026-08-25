# BUILD-SPEC — Cockpit Copa BTG

**Executor:** Gemini CLI
**Revisor:** Claude (lê o `git diff`, não o relatório)
**Base:** `COPA_BTG_PRD.md` — ler antes de cada fase
**Raiz do projeto:** `E:\AUTOMAÇÃO IA\TRADING AI`

---

## REGRAS PARA O EXECUTOR — ler antes de tocar em qualquer arquivo

1. **Uma task por vez, na ordem.** Termina, roda o Verify, marca `[x]`, só então
   passa pra próxima.
2. **Só criar/editar os arquivos listados em `Files`.** Se achar que precisa de
   outro arquivo, PARE e escreva o motivo no fim deste doc, seção "Bloqueios".
3. **Não instalar dependência que não esteja listada na task.** Não trocar de
   stack, não introduzir ORM, não trocar SQLite por outra coisa.
4. **Não inventar endpoint, campo ou nome.** Os contratos deste doc são
   literais — nome de rota, nome de campo JSON e enum são exatamente como
   escritos aqui.
5. **Não mexer em nada fora de `copa/` e `cockpit/`**, exceto as duas linhas
   autorizadas na TASK-004 (`cockpit_api.py`) e TASK-014 (`config/sidebar.ts`).
   `strategies/`, `core/`, `live_daemon_*.py`, `backtesting/` são **read-only**.
6. **REGRA DE CONFORMIDADE — acima de todas as outras.** O regulamento da Copa
   BTG prevê desclassificação por "automações não autorizadas, robôs, scripts,
   ferramentas externas". Este software só é legítimo enquanto for um diário de
   bordo. Portanto, **é proibido**, em qualquer task, sob qualquer justificativa:
   - integrar com Profit Pro / Ultra / Scalper Pro / Nelogica / BTG — inclusive
     ler tela, arquivo, DLL, log ou clipboard dessas plataformas;
   - buscar cotação, candle ou qualquer dado de mercado, de qualquer fonte;
   - detectar setup, sugerir entrada, ou gerar sinal;
   - enviar ordem ou simular envio;
   - fazer qualquer chamada de rede para fora de `localhost`.

   Se uma task parecer pedir qualquer um desses itens, **você leu errado** —
   pare e registre em "Bloqueios". Ver PRD §13.
7. **Verify é obrigatório.** Se o comando não rodou, a task não está feita. Não
   escrever "deve funcionar".
8. Todo texto de interface em **português do Brasil**.
9. O tema é **dark** (o `<html>` já tem `className="dark"`). Não criar toggle.

---

## Convenções técnicas

- **Backend:** Python 3, FastAPI, SQLite via `sqlite3` da stdlib. Sem ORM.
- **Front:** Next 16 App Router, React 19, TypeScript strict, Tailwind 4, shadcn
  (base-ui). Alias de import: `@/*` → raiz de `cockpit/`.
- **Datas:** sempre `YYYY-MM-DD` (string). Horas: `HH:MM` 24h. Timezone: local
  do PC (America/Sao_Paulo). Nada de UTC na interface.
- **Dinheiro:** float em reais, 2 casas. **Pontos:** float.
- **Enums** (string, maiúsculas, exatamente assim):
  - `direcao`: `COMPRA` | `VENDA`
  - `contexto`: `TENDENCIA` | `RANGE` | `INDEFINIDO`
  - `bias`: `COMPRA` | `VENDA` | `INDEFINIDO`
  - `impacto`: `ALTO` | `MEDIO` | `BAIXO`
  - `modo`: `NORMAL` | `DEFENSIVO`
  - `tipo` de item: `KILL` | `PONTO`
  - `status` de trade: `ABERTO` | `FECHADO`
  - `motivo_saida`: `ALVO` | `STOP` | `MANUAL`
  - `desfecho_plano`: `BATEU_ALVO` | `BATEU_STOP` | `NAO_SEI`
  - `ambiente`: `FAVORAVEL` | `NEUTRA` | `DESFAVORAVEL`
  - `mercado`: `WIN` | `WDO`
- **Valor do ponto:** `WIN` = 0.20 R$/ponto, `WDO` = 10.00 R$/ponto. Constante
  em `copa/db.py`, não hardcoded espalhado.

---

# Phase 0 — Fundação

**Goal:** banco, config de estratégia e scoring existem e são testáveis por CLI,
sem nenhuma UI.
**Ler antes:** PRD §5 (modelo de dados), §7 (estratégias).

- [x] **TASK-001 — Schema SQLite + acesso**
  - **Files:** `copa/__init__.py`, `copa/db.py`
  - **Notes:**
    - `copa/db.py` expõe: `DB_PATH` (= `copa/data/copa.db`), `get_conn()`
      (retorna `sqlite3.Connection` com `row_factory = sqlite3.Row` e
      `PRAGMA foreign_keys=ON`), `init_db()` (cria as tabelas se não existirem,
      idempotente), `VALOR_PONTO = {"WIN": 0.20, "WDO": 10.00}`.
    - Criar o diretório `copa/data/` se não existir.
    - Tabelas:

    ```sql
    CREATE TABLE IF NOT EXISTS session_day (
      data              TEXT PRIMARY KEY,          -- YYYY-MM-DD
      bias_d1           TEXT NOT NULL,
      bias_h1           TEXT NOT NULL,
      contexto          TEXT NOT NULL,
      niveis            TEXT NOT NULL DEFAULT '[]',   -- JSON [{label,preco}]
      agenda            TEXT NOT NULL DEFAULT '[]',   -- JSON [{evento,horario,impacto}]
      sono              INTEGER NOT NULL DEFAULT 3,
      tilt              INTEGER NOT NULL DEFAULT 0,
      pressao           INTEGER NOT NULL DEFAULT 0,
      meta_dia          REAL NOT NULL DEFAULT 0,
      limite_perda_dia  REAL NOT NULL DEFAULT 0,
      max_trades_dia    INTEGER NOT NULL DEFAULT 3,
      modo              TEXT NOT NULL DEFAULT 'NORMAL',
      notas             TEXT NOT NULL DEFAULT '',
      criado_em         TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS trade (
      id                INTEGER PRIMARY KEY AUTOINCREMENT,
      data              TEXT NOT NULL REFERENCES session_day(data),
      strategy_id       TEXT NOT NULL,
      mercado           TEXT NOT NULL,
      direcao           TEXT NOT NULL,
      checklist         TEXT NOT NULL,             -- JSON {item_id: bool}
      score             REAL NOT NULL,
      grade             TEXT NOT NULL,
      entrada           REAL NOT NULL,
      stop              REAL NOT NULL,
      alvo              REAL NOT NULL,
      contratos         INTEGER NOT NULL,
      rr_planejado      REAL NOT NULL,
      status            TEXT NOT NULL DEFAULT 'ABERTO',
      saida             REAL,
      motivo_saida      TEXT,
      desfecho_plano    TEXT,
      pnl_real          REAL,
      pnl_plano         REAL,
      pontos_real       REAL,
      respeitou_plano   INTEGER,
      antecipou_stop    INTEGER,
      parcial_emocional INTEGER,
      mudou_alvo        INTEGER,
      notas             TEXT NOT NULL DEFAULT '',
      screenshot_path   TEXT,
      criado_em         TEXT NOT NULL,
      fechado_em        TEXT
    );

    CREATE TABLE IF NOT EXISTS copa_config (
      chave TEXT PRIMARY KEY,
      valor TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_trade_data ON trade(data);
    CREATE INDEX IF NOT EXISTS idx_trade_status ON trade(status);
    ```

    - Tabela adicional para o módulo de torneio (FR-015 a FR-019):

    ```sql
    CREATE TABLE IF NOT EXISTS fase (
      id            TEXT PRIMARY KEY,     -- 'etapa1','etapa2','repescagem','semifinal','final'
      nome          TEXT NOT NULL,
      data_inicio   TEXT NOT NULL,
      data_fim      TEXT NOT NULL,
      dias          INTEGER NOT NULL,
      tem_descarte  INTEGER NOT NULL DEFAULT 1,
      ordem         INTEGER NOT NULL
    );
    ```

    `session_day` ganha a coluna `fase_id TEXT REFERENCES fase(id)` (pode ser
    NULL para dias de treino fora da Copa).

    - `init_db()` insere as fases oficiais se a tabela estiver vazia
      (datas do regulamento, PRD §12):

    | id | nome | início | fim | dias | descarte |
    |---|---|---|---|---|---|
    | `etapa1` | Classificatória Etapa 1 | 2026-09-14 | 2026-09-17 | 4 | sim |
    | `etapa2` | Classificatória Etapa 2 | 2026-09-21 | 2026-09-24 | 4 | sim |
    | `repescagem` | Repescagem | 2026-09-28 | 2026-09-30 | 3 | sim |
    | `semifinal` | Semifinal | 2026-10-13 | 2026-10-16 | 4 | sim |
    | `final` | Final presencial | 2026-10-29 | 2026-10-29 | 1 | não |

    - `init_db()` também insere os defaults de `copa_config` se a tabela estiver
      vazia (chave/valor, valor sempre string JSON):
      `banca_inicial=0` · `meta_dia_padrao=0` · `limite_perda_dia=300` ·
      `max_trades_dia=3` · `max_perdas_seguidas=2` · `cooldown_min=60` ·
      `bloquear_apos_meta=false` ·
      `horarios_validos=[{"inicio":"09:00","fim":"12:00"}]` ·
      `exposicao_maxima_contratos=0` (0 = não informada pelo BTG ainda) ·
      `fator_perda_pos_descarte=0.5`.

    **Nota de regulamento:** o ranking da Copa é performance em **R$ absoluto**,
    não percentual, e o saldo zera a cada fase. Por isso `banca_inicial` é
    meramente informativo — a curva de capital do módulo de torneio é sempre
    **por fase, começando em zero**. Não usar `banca_inicial` em nenhum cálculo
    de ranking.
  - **Verify:** `python -c "from copa.db import init_db,get_conn; init_db(); c=get_conn(); print([r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')])"`
    → imprime as 3 tabelas. Rodar duas vezes seguidas sem erro (idempotência).

- [x] **TASK-002 — Estratégias como config**
  - **Files:** `copa/strategies_config.py`, `copa/strategies/playbook_anderson.json`
  - **Notes:**
    - `strategies_config.py` expõe `load_all() -> list[dict]` e
      `load_one(strategy_id) -> dict | None`. Lê todo `copa/strategies/*.json`,
      ordena por campo `ordem` (int) e valida: a soma dos `peso` dos itens
      `PONTO` **tem que dar 100** — se não der, levanta `ValueError` com o id da
      estratégia. Sem cache (o arquivo é editado à mão durante a Copa).
    - Schema do JSON de estratégia:

    ```json
    {
      "id": "playbook_anderson",
      "ordem": 1,
      "nome": "Playbook Anderson",
      "mercado": ["WIN", "WDO"],
      "descricao": "Liquidez -> Tendencia -> CHoCH -> Nova liquidez -> Execucao. O modelo das 5 licoes.",
      "score_minimo": 65,
      "ambiente_favoravel": [
        "Tendencia definida no D1/H1",
        "Liquidez clara marcada (PDH/PDL, EQH/EQL)",
        "Dia sem noticia de alto impacto na janela de operacao"
      ],
      "ambiente_desfavoravel": [
        "Mercado em range sem direcao",
        "Bias H1 indefinido",
        "Dia de Copom/payroll dentro da janela",
        "Operador em tilt"
      ],
      "horarios_validos": [{"inicio": "09:00", "fim": "12:00"}],
      "regras_ambiente": [
        {"campo": "contexto",  "op": "=",  "valor": "TENDENCIA",  "efeito": "FAVORAVEL",    "motivo": "modelo opera a favor da tendencia macro (licao 2)"},
        {"campo": "contexto",  "op": "=",  "valor": "RANGE",      "efeito": "DESFAVORAVEL", "motivo": "sem tendencia, o CHoCH vira falso sinal"},
        {"campo": "bias_h1",   "op": "=",  "valor": "INDEFINIDO", "efeito": "DESFAVORAVEL", "motivo": "licao 2 exige direcao H1 definida antes de procurar entrada"},
        {"campo": "tilt",      "op": ">=", "valor": 3,            "efeito": "DESFAVORAVEL", "motivo": "tilt alto: risco de romper o plano (licao 5)"},
        {"campo": "sono",      "op": "<=", "valor": 2,            "efeito": "DESFAVORAVEL", "motivo": "sono baixo degrada leitura"},
        {"campo": "tem_noticia_alta", "op": "=", "valor": true,   "efeito": "NEUTRA",       "motivo": "noticia de alto impacto no dia: reduzir exposicao"},
        {"campo": "niveis_marcados",  "op": ">=", "valor": 2,     "efeito": "FAVORAVEL",    "motivo": "liquidez-alvo ja mapeada"}
      ],
      "checklist": [
        {"id": "k1", "tipo": "KILL", "peso": 0,  "label": "Bias H1 definido e a operacao vai a favor dele", "ajuda": "Licao 2. Se o H1 e comprador, so compra."},
        {"id": "k2", "tipo": "KILL", "peso": 0,  "label": "Liquidez relevante foi VARRIDA (sweep confirmado)", "ajuda": "Licao 1. Preco rompeu topo/fundo relevante, rejeitou e fechou de volta. Sem sweep, e adivinhacao."},
        {"id": "k3", "tipo": "KILL", "peso": 0,  "label": "CHoCH confirmado em vela FECHADA", "ajuda": "Licao 3. Estrutura anterior rompida na direcao do bias. Vela fechada, nao em formacao."},
        {"id": "k4", "tipo": "KILL", "peso": 0,  "label": "Nova liquidez formou apos o CHoCH e o preco voltou para busca-la", "ajuda": "Licao 4. Nao perseguir preco. Espera o retorno."},
        {"id": "k5", "tipo": "KILL", "peso": 0,  "label": "Stop e alvo definidos ANTES da ordem, RR >= 2", "ajuda": "Licao 5. O trade termina no alvo ou no stop."},
        {"id": "k6", "tipo": "KILL", "peso": 0,  "label": "Dentro do horario permitido e sem breaker ativo", "ajuda": "Verificado pelo sistema, mas confirme."},
        {"id": "p1", "tipo": "PONTO", "peso": 15, "label": "Entrada dentro de PD array (FVG / OB / breaker)", "ajuda": ""},
        {"id": "p2", "tipo": "PONTO", "peso": 15, "label": "Premium/discount correto", "ajuda": "Venda no premium, compra no discount do range."},
        {"id": "p3", "tipo": "PONTO", "peso": 15, "label": "Liquidez varrida e de QUALIDADE (PDH/PDL, EQH/EQL, max/min semanal)", "ajuda": ""},
        {"id": "p4", "tipo": "PONTO", "peso": 10, "label": "Displacement forte no CHoCH, deixou FVG", "ajuda": ""},
        {"id": "p5", "tipo": "PONTO", "peso": 10, "label": "Inducao: o pullback varreu micro-topo/fundo antes da entrada", "ajuda": "Sem inducao, VOCE e a liquidez."},
        {"id": "p6", "tipo": "PONTO", "peso": 10, "label": "Killzone nobre: dentro de 09:00-12:00, de preferencia 09:00-10:30", "ajuda": "Janela definida pelo operador. Fora dela o breaker bloqueia."},
        {"id": "p7", "tipo": "PONTO", "peso": 10, "label": "Alvo e liquidez clara, nao numero arbitrario", "ajuda": ""},
        {"id": "p8", "tipo": "PONTO", "peso": 10, "label": "Sem noticia de alto impacto nos proximos 30 min", "ajuda": ""},
        {"id": "p9", "tipo": "PONTO", "peso": 5,  "label": "Confluencia WIN x WDO", "ajuda": "Os dois contando a mesma historia."}
      ]
    }
    ```
  - **Verify:** `python -c "from copa.strategies_config import load_all; s=load_all(); print(s[0]['id'], sum(i['peso'] for i in s[0]['checklist'] if i['tipo']=='PONTO'))"`
    → imprime `playbook_anderson 100`.

- [x] **TASK-003 — Scoring + ranking de ambiente**
  - **Files:** `copa/scoring.py`
  - **Notes:**
    - `score_checklist(strategy: dict, marcado: dict[str,bool]) -> dict` retorna
      `{"score": float, "grade": str, "kills_faltando": [item_id], "pontos_marcados": [item_id]}`.
      Score = soma dos pesos dos `PONTO` marcados. Grade: **importar
      `grade_for` de `core.entry_quality`** — não reimplementar a régua.
    - `avaliar_ambiente(strategy: dict, sessao: dict) -> dict` retorna
      `{"ambiente": "FAVORAVEL"|"NEUTRA"|"DESFAVORAVEL", "motivos": [str]}`.
      Avalia cada regra de `regras_ambiente` contra o dict da sessão. Campos
      derivados que o avaliador precisa calcular a partir da sessão:
      `tem_noticia_alta` (bool: existe item em `agenda` com `impacto == "ALTO"`),
      `niveis_marcados` (int: `len(niveis)`).
      Operadores suportados: `=`, `!=`, `>=`, `<=`, `>`, `<`.
      Resolução: se alguma regra que casou tem efeito `DESFAVORAVEL` → resultado
      `DESFAVORAVEL`. Senão, se alguma casou como `FAVORAVEL` → `FAVORAVEL`.
      Senão `NEUTRA`. `motivos` = motivos de todas as regras que casaram.
    - `sugerir_modo(sessao: dict) -> str`: `DEFENSIVO` se
      `tilt >= 3` ou `sono <= 2` ou `pressao >= 4` ou `tem_noticia_alta`.
      Senão `NORMAL`.
    - Em modo `DEFENSIVO`, quem consome (TASK-005) soma **+15** ao
      `score_minimo` e força `max_trades_dia = 1`. `scoring.py` só reporta.
  - **Verify:** `python -c "from copa.strategies_config import load_one; from copa.scoring import score_checklist, avaliar_ambiente; s=load_one('playbook_anderson'); print(score_checklist(s, {'p1':True,'p2':True,'p3':True,'k1':True})); print(avaliar_ambiente(s, {'contexto':'RANGE','bias_h1':'COMPRA','tilt':0,'sono':4,'pressao':0,'agenda':[],'niveis':[]}))"`
    → score 45 grade `C`, `kills_faltando` com 5 ids; ambiente `DESFAVORAVEL`.

---

# Phase 1 — Backend

**Goal:** toda a lógica de gate, risco e estatística responde por HTTP. Testável
com `curl`, sem UI.
**Ler antes:** PRD §6 (FR-001 a FR-014).

- [x] **TASK-004 — Risco e circuit breakers**
  - **Files:** `copa/risk.py`
  - **Notes:**
    - `avaliar_gate(data: str, agora: str | None = None) -> dict` retorna:

    ```json
    {
      "liberado": false,
      "motivos": ["pre-sessao do dia nao preenchida"],
      "avisos": ["meta do dia ja batida"],
      "breakers": {
        "pre_sessao_ok": false,
        "dentro_horario": true,
        "pnl_dia": -120.0,
        "limite_perda_dia": 300.0,
        "trades_dia": 1,
        "max_trades_dia": 3,
        "perdas_seguidas": 0,
        "max_perdas_seguidas": 2,
        "cooldown_ate": null,
        "trade_aberto_id": null,
        "modo": "NORMAL",
        "bonus_score_defensivo": 0
      }
    }
    ```

    - Regras que **bloqueiam** (cada uma adiciona uma string em `motivos`):
      1. Sem linha em `session_day` para a data → `"pre-sessao do dia nao preenchida"`
      2. `pnl_dia <= -limite_perda_dia` → `"limite de perda do dia atingido (R$ X de R$ Y)"`
      3. `trades_dia >= max_trades_dia` → `"limite de trades do dia atingido (X/Y)"`
      4. `perdas_seguidas >= max_perdas_seguidas` e `agora < cooldown_ate` →
         `"cooldown apos X perdas seguidas ate HH:MM"`
      5. `agora` fora de todas as janelas de `horarios_validos` →
         `"fora do horario permitido"`
      6. Existe trade com `status='ABERTO'` → `"ja existe trade aberto (#id)"`
    - Regra que só **avisa**: `pnl_dia >= meta_dia` e `meta_dia > 0` →
      aviso `"meta do dia batida"`. Vira bloqueio se
      `copa_config.bloquear_apos_meta == true`.
    - `perdas_seguidas`: conta trades FECHADOS do dia, do mais recente pra trás,
      até achar um com `pnl_real > 0`. `cooldown_ate` = `fechado_em` do último
      trade perdedor + `cooldown_min` minutos.
    - `pnl_dia` = soma de `pnl_real` dos trades FECHADOS da data.
    - `bonus_score_defensivo` = 15 se `modo == 'DEFENSIVO'`, senão 0. O gate é
      por dia e não conhece a estratégia, então ele reporta só o acréscimo; quem
      soma ao `score_minimo` da estratégia é o POST de trade (TASK-005).
      Em modo `DEFENSIVO`, `max_trades_dia` é forçado a 1 no cálculo do breaker,
      independente do valor gravado na sessão.
    - `calcular_pnl(mercado, direcao, entrada, saida, contratos) -> (pontos, reais)`
      usando `VALOR_PONTO` de `copa/db.py`. COMPRA: `saida - entrada`. VENDA:
      `entrada - saida`.
  - **Verify:** `python -c "from copa.db import init_db; init_db(); from copa.risk import avaliar_gate; print(avaliar_gate('2026-08-25'))"`
    → `liberado: false` com motivo de pré-sessão faltando.

- [x] **TASK-005 — Router FastAPI da Copa**
  - **Files:** `copa/api.py`, `cockpit_api.py` *(só as 2 linhas de include)*
  - **Notes:**
    - `copa/api.py` define `router = APIRouter(prefix="/api/copa", tags=["copa"])`.
    - Em `cockpit_api.py`, adicionar **apenas**:
      `from copa.api import router as copa_router` e
      `app.include_router(copa_router)`. Chamar `init_db()` no startup.
      **Nada mais nesse arquivo pode mudar.**
    - Endpoints (contrato literal):

    | Método | Rota | Corpo / Query | Resposta |
    |---|---|---|---|
    | GET | `/api/copa/config` | — | dict de `copa_config` com valores já desserializados |
    | PUT | `/api/copa/config` | dict parcial | config completa atualizada |
    | GET | `/api/copa/strategies` | — | `list[strategy]` (JSON completo do TASK-002) |
    | GET | `/api/copa/session/{data}` | — | SessionDay ou `null` (200, não 404) |
    | PUT | `/api/copa/session/{data}` | SessionDay sem `criado_em` | SessionDay salva (upsert) |
    | GET | `/api/copa/gate` | `?data=YYYY-MM-DD` | saída de `avaliar_gate` |
    | GET | `/api/copa/ranking` | `?data=YYYY-MM-DD` | `[{strategy_id, nome, ambiente, motivos[]}]` |
    | POST | `/api/copa/trades` | ver abaixo | trade criado (com `score`, `grade`, `rr_planejado`, `id`) |
    | GET | `/api/copa/trades` | `?status=&data=` (ambos opcionais) | `list[trade]`, mais recente primeiro |
    | PATCH | `/api/copa/trades/{id}/fechar` | ver abaixo | trade fechado |
    | DELETE | `/api/copa/trades/{id}` | — | `{"ok": true}` — só se `status == 'ABERTO'` |
    | GET | `/api/copa/stats` | — | ver TASK-006 |
    | GET | `/api/copa/export` | — | `FileResponse` do `copa.db` |

    - **POST /api/copa/trades** — corpo:
      `{data, strategy_id, mercado, direcao, checklist: {id: bool}, entrada, stop, alvo, contratos, notas}`.
      O servidor **recalcula** score/grade/rr e é a fonte da verdade.
      Rejeita com **HTTP 409** e `{"detail": "<motivo>"}` se:
      gate não liberado · algum KILL faltando · `score < score_minimo` da
      estratégia (+15 se modo DEFENSIVO) · `rr_planejado < 2`.
      `rr_planejado = abs(alvo - entrada) / abs(entrada - stop)`, arredondado a
      2 casas. Se `entrada == stop` → HTTP 422.
      Validar coerência da direção: COMPRA exige `stop < entrada < alvo`;
      VENDA exige `alvo < entrada < stop`. Senão HTTP 422.
    - **PATCH /api/copa/trades/{id}/fechar** — corpo:
      `{saida, motivo_saida, desfecho_plano, respeitou_plano, antecipou_stop, parcial_emocional, mudou_alvo, notas}`.
      Calcula `pontos_real` e `pnl_real` via `calcular_pnl`.
      `pnl_plano`: se `motivo_saida` é `ALVO` ou `STOP` → igual a `pnl_real`.
      Se `MANUAL`: `BATEU_ALVO` → pnl como se tivesse saído no `alvo`;
      `BATEU_STOP` → pnl como se tivesse saído no `stop`; `NAO_SEI` → igual a
      `pnl_real`. Grava `fechado_em` = agora ISO.
      HTTP 409 se o trade já estiver `FECHADO`.
  - **Verify:** subir `uvicorn cockpit_api:app --port 8010` e rodar:
    `curl -s localhost:8010/api/copa/strategies | python -m json.tool | head -20`
    e `curl -s "localhost:8010/api/copa/gate?data=2026-08-25"`.
    Colar as duas saídas no relatório.

- [x] **TASK-006 — Estatística**
  - **Files:** `copa/stats.py`
  - **Notes:**
    - `calcular() -> dict` sobre todos os trades `FECHADOS`. Formato exato:

    ```json
    {
      "geral": {"trades": 0, "winrate": 0.0, "profit_factor": 0.0, "expectancia": 0.0,
                "pnl_total": 0.0, "max_drawdown": 0.0, "banca_atual": 10000.0,
                "meta_copa": 0.0, "falta_para_meta": 0.0},
      "equity": [{"t": "2026-08-25", "balance": 10000.0}],
      "por_estrategia": [{"strategy_id": "", "nome": "", "n": 0, "winrate": 0.0, "expectancia": 0.0, "pnl": 0.0}],
      "por_grade":      [{"grade": "A+", "n": 0, "winrate": 0.0, "expectancia": 0.0, "pnl": 0.0}],
      "por_item":       [{"strategy_id": "", "item_id": "", "label": "", "tipo": "PONTO",
                          "n_marcado": 0, "winrate_marcado": 0.0, "exp_marcado": 0.0,
                          "n_nao": 0, "winrate_nao": 0.0, "exp_nao": 0.0,
                          "delta_winrate": 0.0, "amostra_baixa": true}],
      "por_hora":       [{"hora": "09", "n": 0, "winrate": 0.0, "pnl": 0.0}],
      "por_dia_semana": [{"dia": "seg", "n": 0, "winrate": 0.0, "pnl": 0.0}],
      "disciplina": {"trades_com_desvio": 0, "custo_total": 0.0,
                     "por_flag": [{"flag": "antecipou_stop", "n": 0, "custo": 0.0}]}
    }
    ```

    - `winrate` em % (0-100), 1 casa. `expectancia` = PnL médio por trade em R$.
    - `profit_factor` = soma dos ganhos / |soma das perdas|. Se não houve perda,
      devolver `0.0` e **não** dividir por zero.
    - `amostra_baixa` = `n_marcado < 20 or n_nao < 20`. A UI usa isso pra avisar.
    - `delta_winrate` = `winrate_marcado - winrate_nao`. É a resposta do FR-009.
    - `custo_total` = soma de `(pnl_plano - pnl_real)` nos trades onde qualquer
      flag de desvio é verdadeira. Positivo = a indisciplina custou dinheiro.
    - `max_drawdown` em % do pico da curva de capital.
    - Usar apenas stdlib + `pandas` (já é dependência do projeto). Com zero
      trades, devolver a estrutura completa com zeros — **nunca** `null` nem
      lista ausente. A UI não trata caso faltante.
  - **Verify:** inserir 3 trades fechados de teste via `curl` (2 win, 1 loss) e
    rodar `curl -s localhost:8010/api/copa/stats | python -m json.tool`.
    Conferir na mão: winrate 66.7, e `por_item` com o delta do item marcado.

---

# Phase 1B — Módulo Torneio

**Goal:** o software entende que a Copa é disputada em fases com descarte do pior
dia, e aperta o risco sozinho quando o descarte já foi consumido.
**Ler antes:** PRD §12 (regras oficiais) e FR-015 a FR-019.

**Por que isso existe:** numa fase de 4 dias com descarte do pior dia, você tem
exatamente **um** dia ruim de graça. Depois que ele é gasto, todo dia negativo
seguinte entra direto no placar. O regulamento também desempata por **menor
número de contratos operados** — eficiência é critério oficial, não vaidade.

- [x] **TASK-019 — Placar de fase e estado do mulligan**
  - **Files:** `copa/torneio.py`, `copa/risk.py` *(integração do aperto automático)*,
    `copa/api.py` *(1 endpoint novo)*
  - **Notes:**
    - `fase_atual(data) -> dict | None`: a fase cujo intervalo contém a data.
    - `placar_fase(fase_id) -> dict`:

    ```json
    {
      "fase": {"id": "etapa1", "nome": "Classificatoria Etapa 1",
               "data_inicio": "2026-09-14", "data_fim": "2026-09-17",
               "dias": 4, "tem_descarte": true},
      "dias": [{"data": "2026-09-14", "pnl": 250.0, "trades": 2, "contratos": 4, "descartado": false}],
      "dias_operados": 1,
      "dias_restantes": 3,
      "placar_bruto": 250.0,
      "placar_efetivo": 250.0,
      "pior_dia": {"data": "2026-09-14", "pnl": 250.0},
      "mulligan": {"disponivel": true, "consumido_por": null, "motivo": "nenhum dia negativo ainda"},
      "contratos_total": 4,
      "reais_por_contrato": 62.5
    }
    ```

    - **`placar_efetivo`**: soma dos PnL diários da fase **menos** o pior dia,
      mas só quando `tem_descarte` e `dias_operados >= 2`. Com 0 ou 1 dia
      operado, `placar_efetivo == placar_bruto` e `descartado` é `false` em
      todos os dias.
    - **`mulligan.disponivel`**: `false` quando já existe pelo menos um dia
      **negativo** na fase (esse dia é o candidato natural ao descarte).
      `consumido_por` = a data desse dia. Se há mais de um dia negativo, o
      mulligan aponta para o **pior** deles e os demais já estão pesando no
      placar — nesse caso `motivo` = `"2+ dias negativos: os excedentes ja pesam no placar"`.
    - **`reais_por_contrato`** = `placar_bruto / contratos_total`. Com
      `contratos_total == 0`, devolver `0.0` — não dividir por zero.
    - **Integração em `copa/risk.py`** (FR-017): quando `mulligan.disponivel`
      é `false` e ainda restam dias na fase, o gate passa a aplicar:
      `limite_perda_dia_efetivo = limite_perda_dia * fator_perda_pos_descarte`
      (default 0.5) e força `modo = 'DEFENSIVO'` independente do que a sessão
      gravou. Adicionar ao dict `breakers`:
      `"mulligan_disponivel": bool`, `"limite_perda_dia_efetivo": float`,
      `"modo_forcado_por_mulligan": bool`.
      O motivo de bloqueio por perda passa a citar o limite **efetivo**.
    - Endpoint novo: `GET /api/copa/fase?data=YYYY-MM-DD` → saída de
      `placar_fase` da fase que contém a data. Se a data não cai em nenhuma fase,
      devolver `{"fase": null}` (200, não 404) — dias de treino são válidos.
    - `PUT /api/copa/session/{data}` passa a preencher `fase_id`
      automaticamente a partir da data. Não pedir ao operador.
  - **Verify:** criar 3 dias de teste numa fase (`+250`, `-400`, `+180`) via
    `curl` e rodar `curl -s "localhost:8010/api/copa/fase?data=2026-09-16"`.
    Conferir na mão: `placar_bruto = 30`, `placar_efetivo = 430` (descarta o
    `-400`), `mulligan.disponivel = false`, `consumido_por = "2026-09-15"`.
    Depois `curl -s "localhost:8010/api/copa/gate?data=2026-09-16"` e conferir
    `limite_perda_dia_efetivo = 150` e `modo_forcado_por_mulligan = true`.
    Colar as duas saídas.

---

# Phase 2 — Pré-sessão e gate na tela

**Goal:** abrir o app, preencher o dia, ver o que está liberado e quais
estratégias estão favoráveis.
**Ler antes:** PRD §8.

- [x] **TASK-007 — Componentes shadcn que faltam**
  - **Files:** `cockpit/components/ui/*` (novos), `cockpit/package.json`
  - **Notes:** faltam `checkbox`, `label`, `select`, `textarea`, `tabs`,
    `progress`, `dialog`, `switch`, `radio-group`, `alert`.
    Tentar `npx shadcn@latest add checkbox label select textarea tabs progress dialog switch radio-group alert`.
    Se o CLI falhar (o projeto usa `@base-ui/react`, não radix), escrever os
    componentes à mão em Tailwind puro, mesma API de props dos existentes em
    `cockpit/components/ui/card.tsx`. **Não instalar radix.**
  - **Verify:** `cd cockpit && npx tsc --noEmit` sem erro.

- [x] **TASK-008 — Cliente de API + tipos**
  - **Files:** `cockpit/lib/copa-api.ts`
  - **Notes:** mesmo padrão de `cockpit/lib/api.ts` (fetch com `cache: "no-store"`,
    `BASE` de `NEXT_PUBLIC_API_BASE`). Tipos TS espelhando **exatamente** os
    contratos do TASK-005 e TASK-006. Exportar `copaApi` com um método por
    endpoint. Erros HTTP 409/422 devem propagar a string de `detail` —
    **não engolir com fallback silencioso**, ao contrário de `api.ts`. Criar
    `class CopaError extends Error` com `status`.
  - **Verify:** `cd cockpit && npx tsc --noEmit`.

- [x] **TASK-009 — Tela de pré-sessão**
  - **Files:** `cockpit/app/copa/pre-sessao/page.tsx`, `cockpit/components/copa/pre-sessao-form.tsx`
  - **Notes:** client component. Campos do `SessionDay` (PRD §5). Níveis e agenda
    são listas com botão de adicionar/remover linha. `sono`/`tilt`/`pressao` são
    0-5 (botões, não slider). Ao salvar, mostra o modo sugerido por
    `sugerir_modo` (vem no ranking/gate) e deixa o operador confirmar `NORMAL`
    ou `DEFENSIVO`. Data default = hoje. Se já existe sessão do dia, carrega
    para edição.
  - **Verify:** `cd cockpit && npm run build`, depois abrir
    `localhost:3000/copa/pre-sessao`, salvar um dia, e conferir com
    `curl -s "localhost:8010/api/copa/session/<hoje>"` que os campos gravaram.
    Colar a saída do curl.

- [x] **TASK-010 — Home da Copa**
  - **Files:** `cockpit/app/copa/page.tsx`, `cockpit/components/copa/gate-banner.tsx`,
    `cockpit/components/copa/ranking-estrategias.tsx`
  - **Notes:**
    - `gate-banner`: faixa grande no topo. Verde `LIBERADO` ou vermelho
      `BLOQUEADO`, com **todos** os motivos listados. Não esconder motivo atrás
      de tooltip. Avisos em âmbar, separados dos bloqueios.
    - KPIs do dia: PnL do dia, trades usados / máx, perdas seguidas, distância
      pro limite de perda, modo.
    - `ranking-estrategias`: card por estratégia, cor por ambiente
      (FAVORAVEL verde / NEUTRA cinza / DESFAVORAVEL vermelho), com os motivos
      escritos. Clicar leva a `/copa/novo?strategy=<id>`.
    - Se não há pré-sessão do dia, a home mostra só um CTA grande para
      `/copa/pre-sessao` e nada mais.
  - **Verify:** `npm run build` + print/observação da tela em dois estados:
    (a) sem pré-sessão, (b) com pré-sessão em RANGE → Playbook Anderson tem que
    aparecer DESFAVORAVEL com o motivo do CHoCH.

---

# Phase 3 — Checklist e registro

**Goal:** o gate físico funciona. Não dá pra registrar trade fora do modelo.

- [x] **TASK-011 — Checklist com score ao vivo**
  - **Files:** `cockpit/components/copa/checklist-form.tsx`, `cockpit/components/copa/score-meter.tsx`
  - **Notes:**
    - KILL e PONTO em blocos visualmente separados. KILL primeiro, com rótulo
      "OBRIGATÓRIO — sem isso não entra".
    - `score-meter`: barra 0-100 + grade grande + a marca do `score_minimo` na
      barra. Recalcula a cada clique, no cliente, com a mesma fórmula do
      servidor (soma dos pesos PONTO).
    - Painel de status sempre visível listando o que falta: KILLs não marcados,
      quanto falta de score, RR atual. Texto direto: "falta marcar: CHoCH
      confirmado".
    - Toda a marcação em 1 clique na linha inteira (não só no quadradinho). Meta
      declarada no PRD: preencher em menos de 30s.
  - **Verify:** `npx tsc --noEmit` + marcar itens na tela e conferir que o score
    bate com a soma dos pesos do JSON.

- [x] **TASK-012 — Novo trade + gate de registro**
  - **Files:** `cockpit/app/copa/novo/page.tsx`, `cockpit/components/copa/trade-form.tsx`
  - **Notes:**
    - Fluxo numa tela só: escolher estratégia → checklist → preço (entrada,
      stop, alvo, contratos, mercado, direção) → botão.
    - RR e risco em R$ calculados ao vivo enquanto digita
      (`risco = |entrada-stop| * contratos * valor_ponto`).
    - Botão **LIBERAR E REGISTRAR ENTRADA** desabilitado enquanto qualquer
      condição falhar, com o motivo abaixo do botão. Nunca esconder o botão —
      ele fica visível e travado, o bloqueio precisa ser sentido.
    - HTTP 409 do servidor vira alerta vermelho com o `detail`. O cliente
      **não** é a autoridade do gate; o servidor é.
    - Se a estratégia está `DESFAVORAVEL` hoje, mostrar aviso âmbar acima do
      checklist com os motivos — mas **não** bloquear (o operador decide).
  - **Verify:** tentar registrar (a) com KILL faltando → botão travado;
    (b) com RR 1.2 → recusa; (c) trade válido → aparece em
    `curl -s "localhost:8010/api/copa/trades?status=ABERTO"`. Colar a saída.

---

# Phase 4 — Journal e fechamento

- [x] **TASK-013 — Trades e auditoria de disciplina**
  - **Files:** `cockpit/app/copa/trades/page.tsx`, `cockpit/components/copa/fechar-trade-dialog.tsx`
  - **Notes:**
    - Topo: trades ABERTOS com botão FECHAR. Abaixo: histórico em tabela
      (data, estratégia, direção, grade, RR, resultado, PnL, flags de desvio).
    - Dialog de fechamento: preço de saída, `motivo_saida`. Se `MANUAL`, exigir
      `desfecho_plano` (o que o preço fez depois). Depois, as 4 perguntas de
      disciplina — **obrigatórias**, sem default marcado:
      "Respeitei o plano?" · "Antecipei o stop?" · "Fiz parcial emocional?" ·
      "Mudei o alvo no meio do trade?"
    - Linha do histórico com qualquer flag de desvio ganha marcador vermelho na
      lateral.
  - **Verify:** fechar um trade real de teste pela UI e conferir
    `curl -s "localhost:8010/api/copa/trades?status=FECHADO"` — `pnl_real`,
    `pnl_plano` e as 4 flags gravados. Colar a saída.

- [x] **TASK-014 — Sidebar**
  - **Files:** `cockpit/config/sidebar.ts` *(só adicionar um grupo)*
  - **Notes:** grupo novo **"Copa BTG"** no topo, acima de "Dashboard", com:
    Painel `/copa`, Pré-sessão `/copa/pre-sessao`, Novo Trade `/copa/novo`,
    Trades `/copa/trades`, **Fase `/copa/fase`**, Estatística `/copa/stats`,
    Estratégias `/copa/estrategias`, Config `/copa/config`. Ícones do
    `lucide-react` já instalado. **Não remover nem renomear nenhum item
    existente.**
  - **Verify:** `npm run build` + os itens antigos continuam na sidebar.

---

# Phase 5 — Probabilidade

- [x] **TASK-015 — Tela de estatística**
  - **Files:** `cockpit/app/copa/stats/page.tsx`, `cockpit/components/copa/stats-por-item.tsx`
  - **Notes:**
    - Topo: KPIs gerais + curva de capital (reusar `recharts`, mesmo padrão de
      `cockpit/components/equity-chart.tsx`).
    - **Bloco principal — "O que está pagando"**: tabela por item de checklist,
      ordenada por `delta_winrate` decrescente. Colunas: item, N marcado,
      winrate marcado, N não, winrate não, delta. Delta positivo em verde,
      negativo em vermelho. Quando `amostra_baixa`, badge âmbar "N baixo" na
      linha — o número aparece, mas marcado como não confiável.
    - Bloco "Custo da indisciplina": número grande em R$ + quebra por flag.
    - Blocos por grade, por estratégia, por hora, por dia da semana.
    - Com zero trades: estado vazio explicando que os números aparecem depois
      dos primeiros trades fechados. Nada de gráfico quebrado.
  - **Verify:** `npm run build` + abrir a tela com os trades de teste e conferir
    que o delta bate com o cálculo manual de um item.

- [x] **TASK-020 — Tela da fase (placar do torneio)**
  - **Files:** `cockpit/app/copa/fase/page.tsx`, `cockpit/components/copa/placar-fase.tsx`
  - **Notes:**
    - Cabeçalho: nome da fase, datas, dias operados / total, dias restantes.
    - **Dois números grandes lado a lado:** `placar_bruto` e `placar_efetivo`
      (rotulado "com descarte do pior dia"). O efetivo é o que vale para o
      ranking — dar destaque maior a ele.
    - Linha do tempo dos dias da fase: um card por dia com PnL, trades e
      contratos. O dia descartado ganha tratamento visual de riscado/apagado com
      o rótulo "descartado".
    - **Semáforo do mulligan** — o elemento mais importante da tela:
      - verde `MULLIGAN DISPONÍVEL` — "um dia ruim ainda sai de graça"
      - vermelho `MULLIGAN CONSUMIDO` — mostra a data que o consumiu e o texto
        "a partir de agora todo dia negativo entra direto no placar. Limite de
        perda diária cortado para R$ X e modo defensivo forçado."
    - Bloco de eficiência: contratos no total e **R$ por contrato**, com a nota
      de que o desempate oficial da Copa é por menor número de contratos.
    - Se `fase == null` (dia de treino fora das datas da Copa), mostrar estado
      neutro dizendo isso — sem gráfico quebrado.
  - **Verify:** `npm run build` + abrir a tela com os 3 dias de teste da
    TASK-019 e conferir que o dia `-400` aparece riscado, `placar_efetivo`
    mostra `430` e o semáforo está vermelho.

- [x] **TASK-016 — Fichas das estratégias**
  - **Files:** `cockpit/app/copa/estrategias/page.tsx`
  - **Notes:** uma ficha por estratégia: descrição, ambiente favorável,
    ambiente desfavorável, horários, checklist completo (KILL e PONTO com
    pesos), score mínimo, e a estatística própria vinda de
    `stats.por_estrategia`. É a tela de estudo antes do pregão.
  - **Verify:** `npm run build` + a ficha do Playbook Anderson mostra os 6 KILL
    e os 9 PONTO somando 100.

---

# Phase 6 — Pregão-proof

- [x] **TASK-017 — Subir tudo com 1 clique + backup**
  - **Files:** `iniciar_copa.bat`, `cockpit/app/copa/config/page.tsx`
  - **Notes:**
    - `iniciar_copa.bat` (na raiz): sobe `uvicorn cockpit_api:app --port 8010` e
      `npm run dev` dentro de `cockpit/`, em duas janelas, e abre
      `http://localhost:3000/copa` no navegador.
    - Tela de config: editar `copa_config` (limite de perda, máx trades, máx
      perdas seguidas, cooldown, horários válidos, bloquear_apos_meta,
      **exposicao_maxima_contratos** — o BTG informa esse número antes de cada
      fase — e **fator_perda_pos_descarte**) + botão **Exportar banco** apontando
      pra `/api/copa/export`. Também listar as 5 fases da Copa com suas datas,
      somente leitura.
  - **Verify:** fechar tudo, rodar só o `.bat`, e a tela `/copa` carregar com
    dados. Baixar o export e conferir que o arquivo abre no SQLite.

- [x] **TASK-018 — Ensaio geral**
  - **Files:** nenhum (task de verificação)
  - **Notes:** rodar o fluxo inteiro do zero como se fosse um pregão:
    apagar `copa/data/copa.db` → `iniciar_copa.bat` → pré-sessão → ranking →
    novo trade (uma recusa e uma aceitação) → fechar com desvio de plano →
    conferir custo da indisciplina na tela de stats → simular um dia negativo e
    conferir que a tela `/copa/fase` marca o mulligan como consumido e que o
    gate do dia seguinte já vem com o limite de perda cortado pela metade.
  - **Verify:** relatar cada passo com a evidência (saída de comando ou o que
    apareceu na tela). Se qualquer passo travar, **não corrigir sozinho** —
    reportar em "Bloqueios".

---

## Bloqueios

*(o executor escreve aqui o que travou, com o erro literal. Não improvisar
solução fora do escopo da task.)*

---

## Checklist de revisão do Claude (não é tarefa do executor)

- [ ] **Conformidade:** `grep -riE "nelogica|profit|scalper|b3\.com|yfinance|ccxt|requests\.get|http://(?!localhost|127)" copa/ cockpit/app/copa cockpit/components/copa cockpit/lib/copa-api.ts` retorna vazio
- [ ] `git diff` lido arquivo por arquivo — relatório do agente não conta
- [ ] Nenhum arquivo fora de `copa/` e `cockpit/` alterado, exceto as 2 linhas
      do `cockpit_api.py` e o grupo novo em `config/sidebar.ts`
- [ ] `strategies/`, `core/`, `live_daemon_*.py` intactos
- [ ] Gate é validado no **servidor**, não só no botão do React
- [ ] `grade_for` importado de `core/entry_quality.py`, não reimplementado
- [ ] `stats` devolve estrutura completa com zero trades
- [ ] `npx tsc --noEmit` e `npm run build` rodados nesta sessão, saída colada
