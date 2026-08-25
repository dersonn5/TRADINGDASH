"""
Cockpit API — backend do dashboard (FastAPI)
=============================================
Serve os dados que o frontend Next.js consome:
  /api/metrics   -> KPIs (PF, win, PnL, DD, trades, expectância)
  /api/equity    -> curva de capital
  /api/trades    -> histórico de trades (com cenário)
  /api/positions -> posições abertas (ao vivo)
  /api/lessons   -> lições aprendidas (Obsidian)
  /api/status    -> status do robô

Fonte: cockpit/data/portfolio.json (gerado por research/export_cockpit.py) +
Obsidian. Se não houver dados, devolve amostra para o front renderizar.

Rodar:  uvicorn cockpit_api:app --reload --port 8010
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from copa.api import router as copa_router
from copa.db import init_db

BASE = Path(__file__).resolve().parent
DATA = BASE / "cockpit" / "data" / "portfolio.json"
LESSONS_DIR = BASE / "Cerebro_Obsidian" / "Trading AI" / "C02 Licoes Aprendidas"

init_db()

app = FastAPI(title="ICT Cockpit API")
app.include_router(copa_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"], allow_headers=["*"],
)


def _load_portfolio() -> dict:
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _sample()


def _sample() -> dict:
    """Amostra para o front renderizar sem dados reais ainda."""
    import random
    random.seed(7)
    bal = 500.0
    eq = [{"t": f"2024-{m:02d}-01", "balance": round(bal := bal * (1 + random.uniform(-0.03, 0.06)), 2)}
          for m in range(1, 13)]
    trades = []
    for i in range(1, 13):
        win = random.random() < 0.4
        pnl = round(random.uniform(20, 90) if win else random.uniform(-40, -20), 2)
        trades.append({"id": i, "date": f"2024-{i:02d}-15 03:40", "symbol": "BTC/USDT",
                       "side": "BUY" if i % 2 else "SELL", "rr": round(random.uniform(1.8, 3.2), 1),
                       "result": "WIN" if win else "LOSS", "pnl": pnl,
                       "grade": random.choice(["A+", "A", "B"])})
    return {
        "metrics": {"profit_factor": 1.35, "win_rate": 40.9, "total_pnl": eq[-1]["balance"] - 500,
                    "max_drawdown": 6.8, "trades": 120, "expectancy": 21.5},
        "equity": eq, "trades": trades,
        "sample": True,
    }


@app.get("/api/status")
def status():
    return {"bot": "idle", "mode": "backtest", "last_scan": datetime.now(timezone.utc).isoformat(),
            "next_killzone": "London Open 02:00 ET"}


@app.get("/api/metrics")
def metrics():
    return _load_portfolio().get("metrics", {})


@app.get("/api/equity")
def equity():
    return _load_portfolio().get("equity", [])


@app.get("/api/trades")
def trades():
    return _load_portfolio().get("trades", [])


@app.get("/api/positions")
def positions():
    return _load_portfolio().get("positions", [])


@app.get("/api/lessons")
def lessons():
    out = []
    if LESSONS_DIR.exists():
        for md in sorted(LESSONS_DIR.glob("*.md")):
            try:
                txt = md.read_text(encoding="utf-8")
                body = re.sub(r"^---.*?---", "", txt, flags=re.DOTALL).strip()
                snippet = re.sub(r"[#>*`]", "", body)[:280].strip()
                out.append({"title": md.stem.replace("_", " "), "snippet": snippet})
            except Exception:
                continue
    return out


@app.get("/api/meta")
def meta():
    p = _load_portfolio()
    return {"sample": p.get("sample", False), "generated": p.get("generated")}
