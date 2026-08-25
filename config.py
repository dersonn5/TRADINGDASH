import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar arquivo .env se ele existir
load_dotenv()

# ==========================================
# 1. DIRETÓRIOS E INTEGRAÇÃO OBSIDIAN
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
OBSIDIAN_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", str(BASE_DIR / "Cerebro_Obsidian" / "Trading AI")))

ICT_RULES_DIR = OBSIDIAN_VAULT_PATH / "B03 Regras ICT"
LESSONS_LEARNED_DIR = OBSIDIAN_VAULT_PATH / "C02 Licoes Aprendidas"
TRADE_JOURNAL_DIR = OBSIDIAN_VAULT_PATH / "A04 Diario de Trades"
BACKTEST_JOURNAL_DIR = OBSIDIAN_VAULT_PATH / "B04 Backtests" / "Logs de Trades"

# Estrutura Organizacional TRADE SYSTEM (Segundo Cérebro)
TRADE_SYSTEM_DIR = OBSIDIAN_VAULT_PATH / "B05 Trade System"
VALIDATED_STRATEGIES_DIR = TRADE_SYSTEM_DIR / "Estrategias Validadas"
VALIDATED_RISK_DIR = TRADE_SYSTEM_DIR / "Gerenciamento Validado"
TRADE_CONDUCT_DIR = TRADE_SYSTEM_DIR / "Conducao de Trade"
PRE_TRADE_MIND_DIR = TRADE_SYSTEM_DIR / "Mentalidade Pre-Trade"
DURING_TRADE_DIR = TRADE_SYSTEM_DIR / "Durante o Trade"
POST_TRADE_DIR = TRADE_SYSTEM_DIR / "Pos-Trade"

# Garantir que as pastas existam
ICT_RULES_DIR.mkdir(parents=True, exist_ok=True)
LESSONS_LEARNED_DIR.mkdir(parents=True, exist_ok=True)
TRADE_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
BACKTEST_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

TRADE_SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
VALIDATED_STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
VALIDATED_RISK_DIR.mkdir(parents=True, exist_ok=True)
TRADE_CONDUCT_DIR.mkdir(parents=True, exist_ok=True)
PRE_TRADE_MIND_DIR.mkdir(parents=True, exist_ok=True)
DURING_TRADE_DIR.mkdir(parents=True, exist_ok=True)
POST_TRADE_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. CHAVES DE API E CREDENCIAIS
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "super_secret_ict_key_123")

# Credenciais MT5
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")

# Credenciais Tradovate
TRADOVATE_USER = os.getenv("TRADOVATE_USER", "")
TRADOVATE_PASSWORD = os.getenv("TRADOVATE_PASSWORD", "")
TRADOVATE_APP_ID = os.getenv("TRADOVATE_APP_ID", "")
TRADOVATE_APP_VERSION = os.getenv("TRADOVATE_APP_VERSION", "1.0.0")
TRADOVATE_CID = int(os.getenv("TRADOVATE_CID", "0"))
TRADOVATE_DEMO = os.getenv("TRADOVATE_DEMO", "true").lower() == "true"

# ==========================================
# 3. GESTÃO DE RISCO E FILTROS QUANTITATIVOS
# ==========================================
# 'SIMULATOR' (Paper Trading), 'MT5' (Corretora CFD) ou 'TRADOVATE' (Futuros NQ/ES)
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "SIMULATOR").upper()
ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000.0"))

# Risco rígido de 1% por padrão
RISK_PER_TRADE_PERCENT = float(os.getenv("RISK_PER_TRADE_PERCENT", "1.0"))
# Risco máximo absoluto em dólares (caso a conta seja muito grande ou pequena)
MAX_TRADE_SIZE_USD = float(os.getenv("MAX_TRADE_SIZE_USD", "100.0"))

# Limite diário de perda (Drawdown Diário) - Para proteger seu capital!
MAX_DAILY_DRAWDOWN_PERCENT = float(os.getenv("MAX_DAILY_DRAWDOWN_PERCENT", "3.0"))
# Meta diária para encerrar o expediente (Take Profit do Dia)
DAILY_PROFIT_TARGET_PERCENT = float(os.getenv("DAILY_PROFIT_TARGET_PERCENT", "5.0"))

# Número máximo de operações por dia (evitar overtrading)
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "3"))

# Filtro matemático de Payout mínimo (Risco:Retorno)
MIN_RISK_REWARD_RATIO = float(os.getenv("MIN_RISK_REWARD_RATIO", "2.5"))

# ==========================================
# 3.1 INTEGRAÇÃO MCP (TradingView Market Data)
# ==========================================
# Cliente MCP para puxar candles/indicadores em tempo real do TradingView.
# Compatível com bidouilles/mcp-tradingview-server (stdio transport).
# Instalar separadamente: https://github.com/bidouilles/mcp-tradingview-server
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "uv")
MCP_SERVER_ARGS = tuple(os.getenv("MCP_SERVER_ARGS", "run,mcp-tradingview").split(","))
MCP_DEFAULT_EXCHANGE = os.getenv("MCP_DEFAULT_EXCHANGE", "BINANCE")

# ==========================================
# 4. HORÁRIOS DAS KILLZONES ICT (EST/Nova York)
# ==========================================
# O trading sistemático de ICT funciona em horários muito específicos de alta liquidez.
# Definimos os intervalos em formato (Hora_Inicio, Min_Inicio, Hora_Fim, Min_Fim)
ICT_KILLZONES = {
    "LONDON_OPEN": {"start": (2, 0), "end": (5, 0)},       # 02:00 - 05:00 EST
    "NEW_YORK_OPEN": {"start": (7, 0), "end": (10, 0)},    # 07:00 - 10:00 EST
    "LONDON_CLOSE": {"start": (10, 0), "end": (12, 0)},    # 10:00 - 12:00 EST
}

# ==========================================
# 5. CONFIGURAÇÕES BINANCE FUTURES (TESTNET)
# ==========================================
BINANCE_TESTNET_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY", "")
BINANCE_TESTNET_SECRET = os.getenv("BINANCE_TESTNET_SECRET", "")
BINANCE_LEVERAGE = int(os.getenv("BINANCE_LEVERAGE", "5"))
BINANCE_MARGIN_MODE = os.getenv("BINANCE_MARGIN_MODE", "cross").lower()
BINANCE_SYMBOLS = os.getenv("BINANCE_SYMBOLS", "ETH/USDT:USDT").split(",")

# ==========================================
# 6. GROQ — Fallback LLM para destilação ICT Brain
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ==========================================
# 7. OLLAMA — LLM LOCAL (motor principal do Distiller)
# ==========================================
# Roda na GPU local (RTX 3070). Sem rate-limit, sem custo. Cloud vira só fallback.
USE_LOCAL_LLM   = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
OLLAMA_HOST     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# Modelo rápido para os lotes (extração bruta) — cabe 100% na GPU.
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
# Modelo mais forte só para consolidação final (qualidade). Offload parcial OK.
OLLAMA_CONSOLIDATION_MODEL = os.getenv("OLLAMA_CONSOLIDATION_MODEL", "qwen2.5:14b-instruct")
# timeout por chamada (s) — geração local pode demorar em lotes grandes
OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "900"))

# ==========================================
# 8. BRAIN FILTER — provedor do filtro LLM (experimental)
# ==========================================
# "ollama" (local 7b) | "openai" (gpt-4o-mini etc, mais forte e barato)
BRAIN_PROVIDER     = os.getenv("BRAIN_PROVIDER", "ollama")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
OPENAI_BRAIN_MODEL = os.getenv("OPENAI_BRAIN_MODEL", "gpt-4o-mini")
