"""
Módulo de Banco de Dados SQLite — Cockpit Copa BTG
===================================================
Gerencia conexão, schema e dados iniciais (fases oficiais e configurações padrão).
"""
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "copa.db"

VALOR_PONTO = {
    "WIN": 0.20,
    "WDO": 10.00,
}

FASES_OFICIAIS = [
    {
        "id": "etapa1",
        "nome": "Classificatória Etapa 1",
        "data_inicio": "2026-09-14",
        "data_fim": "2026-09-17",
        "dias": 4,
        "tem_descarte": 1,
        "ordem": 1,
    },
    {
        "id": "etapa2",
        "nome": "Classificatória Etapa 2",
        "data_inicio": "2026-09-21",
        "data_fim": "2026-09-24",
        "dias": 4,
        "tem_descarte": 1,
        "ordem": 2,
    },
    {
        "id": "repescagem",
        "nome": "Repescagem",
        "data_inicio": "2026-09-28",
        "data_fim": "2026-09-30",
        "dias": 3,
        "tem_descarte": 1,
        "ordem": 3,
    },
    {
        "id": "semifinal",
        "nome": "Semifinal",
        "data_inicio": "2026-10-13",
        "data_fim": "2026-10-16",
        "dias": 4,
        "tem_descarte": 1,
        "ordem": 4,
    },
    {
        "id": "final",
        "nome": "Final presencial",
        "data_inicio": "2026-10-29",
        "data_fim": "2026-10-29",
        "dias": 1,
        "tem_descarte": 0,
        "ordem": 5,
    },
]

CONFIG_DEFAULTS = {
    "banca_inicial": json.dumps(0),
    "meta_dia_padrao": json.dumps(0),
    "limite_perda_dia": json.dumps(300),
    "max_trades_dia": json.dumps(3),
    "max_perdas_seguidas": json.dumps(2),
    "cooldown_min": json.dumps(60),
    "bloquear_apos_meta": json.dumps(False),
    "horarios_validos": json.dumps([{"inicio": "09:00", "fim": "12:00"}]),
    "exposicao_maxima_contratos": json.dumps(0),
    "fator_perda_pos_descarte": json.dumps(0.5),
}


def get_conn() -> sqlite3.Connection:
    """Retorna uma conexão SQLite com suporte a Row, timeout ampliado e Foreign Keys ativadas."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Inicializa as tabelas, índices e dados padrão se não existirem."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS fase (
          id            TEXT PRIMARY KEY,
          nome          TEXT NOT NULL,
          data_inicio   TEXT NOT NULL,
          data_fim      TEXT NOT NULL,
          dias          INTEGER NOT NULL,
          tem_descarte  INTEGER NOT NULL DEFAULT 1,
          ordem         INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS session_day (
          data              TEXT PRIMARY KEY,
          bias_d1           TEXT NOT NULL,
          bias_h1           TEXT NOT NULL,
          contexto          TEXT NOT NULL,
          niveis            TEXT NOT NULL DEFAULT '[]',
          agenda            TEXT NOT NULL DEFAULT '[]',
          sono              INTEGER NOT NULL DEFAULT 3,
          tilt              INTEGER NOT NULL DEFAULT 0,
          pressao           INTEGER NOT NULL DEFAULT 0,
          meta_dia          REAL NOT NULL DEFAULT 0,
          limite_perda_dia  REAL NOT NULL DEFAULT 0,
          max_trades_dia    INTEGER NOT NULL DEFAULT 3,
          modo              TEXT NOT NULL DEFAULT 'NORMAL',
          notas             TEXT NOT NULL DEFAULT '',
          criado_em         TEXT NOT NULL,
          fase_id           TEXT REFERENCES fase(id)
        );

        CREATE TABLE IF NOT EXISTS trade (
          id                INTEGER PRIMARY KEY AUTOINCREMENT,
          data              TEXT NOT NULL REFERENCES session_day(data),
          strategy_id       TEXT NOT NULL,
          mercado           TEXT NOT NULL,
          direcao           TEXT NOT NULL,
          checklist         TEXT NOT NULL,
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
        """)

        # Inserir fases oficiais se tabela vazia
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fase")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """
                INSERT INTO fase (id, nome, data_inicio, data_fim, dias, tem_descarte, ordem)
                VALUES (:id, :nome, :data_inicio, :data_fim, :dias, :tem_descarte, :ordem)
                """,
                FASES_OFICIAIS,
            )

        # Inserir configurações padrão se tabela vazia
        cursor.execute("SELECT COUNT(*) FROM copa_config")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """
                INSERT INTO copa_config (chave, valor)
                VALUES (?, ?)
                """,
                CONFIG_DEFAULTS.items(),
            )
    conn.close()
