import os
import sys
import json
import asyncio
import traceback
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# Configura a saída padrão para UTF-8 no Windows para evitar erros de encoding de console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Carregar variáveis de ambiente
load_dotenv()

# Configurar diretório raiz no Python Path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import config
from core.mt5_client import MT5Client
from core.risk_manager import RiskManager
from core.agent import ICTAgent
from core.common_execution import CommonExecution
from data.data_loader import DataLoader

# Tentar importar o MetaTrader 5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# Resiliência de Timezone
try:
    import pytz
    EST_TZ = pytz.timezone('America/New_York')
except ImportError:
    EST_TZ = timezone(timedelta(hours=-5)) # Fallback padrão EST

# Mapeamento de timeframes para o MT5
if MT5_AVAILABLE:
    TIMEFRAME_MAP = {
        "1m": mt5.TIMEFRAME_M1,
        "5m": mt5.TIMEFRAME_M5,
        "15m": mt5.TIMEFRAME_M15,
        "1h": mt5.TIMEFRAME_H1,
        "1d": mt5.TIMEFRAME_D1
    }
else:
    TIMEFRAME_MAP = {}

# ==========================================
# GESTÃO DE CONFIGURAÇÃO DINÂMICA
# ==========================================
CONFIG_PATH = ROOT_DIR / "core" / "dashboard_config.json"

def load_dashboard_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Configurações iniciais a partir do config.py
    return {
        "execution_mode": config.EXECUTION_MODE,
        "risk_pct": config.RISK_PER_TRADE_PERCENT,
        "max_trade_usd": config.MAX_TRADE_SIZE_USD,
        "max_daily_dd": config.MAX_DAILY_DRAWDOWN_PERCENT,
        "daily_target": config.DAILY_PROFIT_TARGET_PERCENT,
        "max_trades_day": config.MAX_TRADES_PER_DAY,
        "broker_tz_offset": 3,  # EET Padrão (IC Markets, etc)
        "is_paused": False
    }

def save_dashboard_config(cfg: dict):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[CONFIG] Erro ao salvar configurações: {e}")

def apply_config_to_modules(cfg: dict):
    config.EXECUTION_MODE = cfg.get("execution_mode", "SIMULATOR")
    config.RISK_PER_TRADE_PERCENT = float(cfg.get("risk_pct", 1.0))
    config.MAX_TRADE_SIZE_USD = float(cfg.get("max_trade_usd", 100.0))
    config.MAX_DAILY_DRAWDOWN_PERCENT = float(cfg.get("max_daily_dd", 3.0))
    config.DAILY_PROFIT_TARGET_PERCENT = float(cfg.get("daily_target", 5.0))
    config.MAX_TRADES_PER_DAY = int(cfg.get("max_trades_day", 3))

# ==========================================
# ESTADO GLOBAL DO DAEMON
# ==========================================
class DaemonState:
    def __init__(self):
        self.config = load_dashboard_config()
        apply_config_to_modules(self.config)
        
        self.is_running = True
        self.logs = []
        self.active_monitored_positions = {}
        self.funnel_logs = {}

state = DaemonState()

# ==========================================
# GERENCIAMENTO DE CONEXÕES WEBSOCKET
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

async def log_and_broadcast(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    state.logs.append(formatted)
    if len(state.logs) > 1000:
        state.logs.pop(0)
        
    # Gravar em arquivo local de log
    log_path = ROOT_DIR / "logs_daemon_mt5.txt"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass
        
    await manager.broadcast({"type": "log", "message": formatted})

async def broadcast_state_update():
    try:
        metrics = RiskManager.get_todays_metrics(config.ACCOUNT_BALANCE)
    except Exception:
        metrics = {"trades_count": 0, "net_profit_loss_usd": 0.0, "net_percentage": 0.0}
        
    await manager.broadcast({
        "type": "state_update",
        "state": {
            "is_paused": state.config.get("is_paused", False),
            "trades_today": metrics.get("trades_count", 0),
            "daily_pnl": metrics.get("net_profit_loss_usd", 0.0),
            "daily_pnl_pct": metrics.get("net_percentage", 0.0),
            "active_positions_count": len(state.active_monitored_positions)
        }
    })

# ==========================================
# PROCESSAMENTO DE DADOS E HISTÓRICO
# ==========================================
def get_rates_dataframe(symbol_mt5: str, timeframe: str, count: int = 300, offset_hours: int = 3) -> pd.DataFrame:
    """Busca os candles no MT5 e ajusta a timezone para America/New_York (UTC offset do broker)."""
    if not MT5_AVAILABLE:
        return pd.DataFrame()
        
    mt5_tf = TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_M5)
    mt5.symbol_select(symbol_mt5, True)
    
    rates = mt5.copy_rates_from_pos(symbol_mt5, mt5_tf, 0, count)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'] - offset_hours * 3600, unit='s')
    df.rename(columns={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "tick_volume": "volume"
    }, inplace=True)
    df.set_index("time", inplace=True)
    df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
    return df

def update_logged_trade(symbol_mt5: str, exit_price: float, profit: float, reason: str):
    db_path = ROOT_DIR / "trades_database.json"
    if not db_path.exists():
        return
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
            
        updated = False
        for t in reversed(db.get("trades", [])):
            if t.get("symbol") == symbol_mt5 and t.get("result") == "PENDING":
                t["result"] = "WIN" if profit > 0 else "LOSS"
                t["profit_loss_usd"] = profit
                t["exit_price"] = exit_price
                t["exit_reason"] = reason
                t["timestamp_exit"] = datetime.now().isoformat()
                updated = True
                break
                
        if updated:
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=4, ensure_ascii=False)
            print(f"[DB] Registro atualizado para {symbol_mt5} no trades_database.json")
    except Exception as e:
        print(f"[ERRO DB] Falha ao atualizar trades_database: {e}")

def update_obsidian_journal_trade_close(symbol: str, action: str, result: str, profit: float):
    symbol_clean = symbol.replace(":", "_").replace("/", "_").replace("\\", "_")
    target_dir = config.TRADE_JOURNAL_DIR
    pattern = f"*{symbol_clean}_{action}_PENDING.md"
    files = list(target_dir.glob(pattern))
    
    if files:
        filepath = files[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            status_emoji = "✅ WIN" if result == "WIN" else "❌ LOSS"
            content = content.replace("⏳ PENDING", status_emoji)
            content = content.replace("- **Take Profit**: ", f"- **P&L Realizado**: ${profit:.2f} USD\n- **Take Profit**: ")
            
            new_filename = filepath.name.replace("_PENDING.md", f"_{result}.md")
            new_filepath = target_dir / new_filename
            
            filepath.unlink()
            
            with open(new_filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"[OBSIDIAN] Diário de trade fechado atualizado: {new_filename}")
        except Exception as e:
            print(f"[ERRO OBSIDIAN] Falha ao fechar diário no Obsidian: {e}")

def get_live_trades_data() -> dict:
    db_path = ROOT_DIR / "trades_database.json"
    trades = []
    if db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                trades = data.get("trades", [])
        except Exception:
            pass
            
    ideal_trades = []
    stressed_trades = []
    
    ideal_pnl = 0.0
    stressed_pnl = 0.0
    wins = 0
    losses = 0
    prevented_losses = 0
    trades_taken = 0
    
    for idx, t in enumerate(trades):
        res = t.get("result", "PENDING")
        pnl = float(t.get("profit_loss_usd", 0.0))
        
        dt_str = t.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(dt_str)
            date_val = dt.strftime("%Y-%m-%d")
            time_val = dt.strftime("%H:%M EST")
        except Exception:
            date_val = datetime.now().strftime("%Y-%m-%d")
            time_val = datetime.now().strftime("%H:%M EST")
            
        action = t.get("action", "PASS")
        ai_dec = action if res != "BLOCKED_BY_RISK" else "PASS"
        
        eval_type = "LOSS"
        if res == "WIN":
            eval_type = "WIN"
            wins += 1
            trades_taken += 1
            ideal_pnl += pnl
            stressed_pnl += pnl
        elif res == "LOSS":
            eval_type = "LOSS"
            losses += 1
            trades_taken += 1
            ideal_pnl += pnl
            stressed_pnl += pnl
        elif res == "BLOCKED_BY_RISK":
            eval_type = "PREVENTED_LOSS"
            prevented_losses += 1
        else: # PENDING
            eval_type = "PENDING"
            trades_taken += 1
            
        ideal_trade = {
            "scenario_id": f"LIVE-{idx+1:03d}",
            "date": date_val,
            "time_of_day_est": time_val,
            "symbol": t.get("symbol", ""),
            "signal_type": t.get("strategy", "Silver Bullet"),
            "daily_bias": "ALIGNED",
            "ai_decision": ai_dec,
            "historical_result": res,
            "evaluation": eval_type,
            "pnl_usd": pnl,
            "reasoning": t.get("reasoning", ""),
            "checklist_killzone": t.get("checklist", {}).get("killzone", True),
            "checklist_sweep": t.get("checklist", {}).get("sweep", True),
            "checklist_mss": t.get("checklist", {}).get("mss", True),
            "checklist_payout": t.get("checklist", {}).get("payout", True)
        }
        
        stressed_trade = {
            "scenario_id": f"LIVE-{idx+1:03d}",
            "date": date_val,
            "time_of_day_est": time_val,
            "symbol": t.get("symbol", ""),
            "signal_type": t.get("strategy", "Silver Bullet"),
            "ai_decision": ai_dec,
            "historical_result": res,
            "evaluation": eval_type,
            "pnl_usd": pnl,
            "slippage_applied": 0.0,
            "reasoning": t.get("reasoning", "")
        }
        
        ideal_trades.append(ideal_trade)
        stressed_trades.append(stressed_trade)
        
    return {
        "ideal": {
            "statistics": {
                "total_scenarios": len(trades),
                "trades_taken": trades_taken,
                "wins": wins,
                "losses": losses,
                "prevented_losses": prevented_losses,
                "missed_wins": 0,
                "total_pnl_usd": ideal_pnl,
                "win_rate": (wins / trades_taken * 100) if trades_taken > 0 else 0.0,
                "profit_factor": 0.0
            },
            "trades": ideal_trades
        },
        "stressed": {
            "statistics": {
                "total_scenarios": len(trades),
                "trades_taken": trades_taken,
                "wins": wins,
                "losses": losses,
                "prevented_losses": prevented_losses,
                "missed_wins": 0,
                "total_pnl_usd": stressed_pnl,
                "win_rate": (wins / trades_taken * 100) if trades_taken > 0 else 0.0,
                "profit_factor": 0.0
            },
            "trades": stressed_trades
        }
    }

# ==========================================
# LOOP PRINCIPAL DO DAEMON DE TRADING
# ==========================================
async def run_live_trading_daemon():
    await asyncio.sleep(2)  # Delay inicial
    await log_and_broadcast("🤖 CÉREBRO DE TRADING COGNITIVO - LIVE DAEMON MT5 INICIADO")
    await log_and_broadcast(f"Modo de Execução: {config.EXECUTION_MODE} | Risco por Trade: {config.RISK_PER_TRADE_PERCENT}%")
    
    if not MT5_AVAILABLE:
        await log_and_broadcast("[AVISO] Biblioteca 'MetaTrader5' não disponível neste sistema. O daemon rodará em modo SIMULAÇÃO/DEMO com dados de fallback.")
    else:
        connected = await asyncio.to_thread(mt5.initialize)
        if connected:
            await log_and_broadcast("✅ Conexão inicial estabelecida com o terminal MetaTrader 5!")
            if config.MT5_LOGIN > 0 and config.MT5_PASSWORD:
                login_ok = await asyncio.to_thread(
                    mt5.login, login=config.MT5_LOGIN, password=config.MT5_PASSWORD, server=config.MT5_SERVER
                )
                if login_ok:
                    await log_and_broadcast(f"🔑 Logado com sucesso na conta MT5 {config.MT5_LOGIN} ({config.MT5_SERVER})")
                else:
                    await log_and_broadcast(f"❌ Erro de login no MT5: {mt5.last_error()}")
            
            # Restaurar posições ativas magic-number 123456
            try:
                positions = await asyncio.to_thread(mt5.positions_get)
                if positions:
                    for pos in positions:
                        if pos.magic == 123456:
                            symbol_mt5 = pos.symbol
                            state.active_monitored_positions[symbol_mt5] = {
                                "ticket": pos.ticket,
                                "entry_price": pos.price_open,
                                "size": pos.volume,
                                "side": "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                                "strategy": "Recuperada do Terminal"
                            }
                            await log_and_broadcast(f"Monitoramento recuperado para posição ativa de {symbol_mt5} (Ticket: {pos.ticket}, Lotes: {pos.volume})")
            except Exception as e:
                await log_and_broadcast(f"Falha ao checar posições ativas no terminal: {e}")
            
            await asyncio.to_thread(mt5.shutdown)
        else:
            await log_and_broadcast("❌ [MT5] Não foi possível conectar ao terminal local. Certifique-se de que o MT5 está aberto.")
            
    # Importar estratégias
    from strategies.session_configs import (
        make_sb_nq_am, make_sb_nq_lunch, make_sb_nq_close,
        make_sb_xau_am, make_sb_xau_lunch, make_sb_xau_close,
        make_bb_nq_lunch, make_bb_nq_close,
        make_bb_xau_lunch, make_bb_xau_close
    )
    from strategies.london_sweep_nq import LondonSweepNQ
    from strategies.london_sweep_xau import LondonSweepXAU

    # Criar listas de estratégias para os ativos Nasdaq e Ouro
    strategies_nq = [
        make_sb_nq_am(),
        make_sb_nq_lunch(),
        make_sb_nq_close(),
        make_bb_nq_lunch(),
        make_bb_nq_close(),
        LondonSweepNQ()
    ]
    
    strategies_xau = [
        make_sb_xau_am(),
        make_sb_xau_lunch(),
        make_sb_xau_close(),
        make_bb_xau_lunch(),
        make_bb_xau_close(),
        LondonSweepXAU()
    ]
    
    agent = ICTAgent()
    loop_interval = 10  # Verificar a cada 10 segundos
    
    while state.is_running:
        try:
            if state.config.get("is_paused", False):
                await asyncio.sleep(2)
                continue
                
            connected = False
            if MT5_AVAILABLE:
                connected = await asyncio.to_thread(mt5.initialize)
                if connected and config.MT5_LOGIN > 0 and config.MT5_PASSWORD:
                    connected = await asyncio.to_thread(
                        mt5.login, login=config.MT5_LOGIN, password=config.MT5_PASSWORD, server=config.MT5_SERVER
                    )
            
            # 1. Monitoramento de Posições Ativas
            if connected:
                for symbol_mt5, pos_info in list(state.active_monitored_positions.items()):
                    ticket = pos_info["ticket"]
                    positions = await asyncio.to_thread(mt5.positions_get, ticket=ticket)
                    
                    if not positions or len(positions) == 0:
                        # Posição fechada
                        await log_and_broadcast(f"Posição de {symbol_mt5} (Ticket {ticket}) fechada. Buscando histórico de execução...")
                        
                        # Pegar deals
                        deals = await asyncio.to_thread(mt5.history_deals_get, position=ticket)
                        exit_price = pos_info["entry_price"]
                        profit = 0.0
                        reason = "CLOSED"
                        
                        if deals:
                            for deal in deals:
                                if deal.entry == 1: # DEAL_ENTRY_OUT
                                    exit_price = deal.price
                                    profit = deal.profit
                                    comment = deal.comment.lower()
                                    if "sl" in comment or "stop" in comment:
                                        reason = "STOP_LOSS"
                                    elif "tp" in comment or "take" in comment:
                                        reason = "TAKE_PROFIT"
                                    else:
                                        reason = "MANUAL_CLOSE"
                                    break
                                    
                        await log_and_broadcast(f"🎉 [POSIÇÃO FECHADA] {symbol_mt5} (Ticket: {ticket}): {reason} | Lucro/Prejuízo: ${profit:.2f} USD")
                        
                        # Atualizar bancos e Obsidian
                        update_logged_trade(symbol_mt5, exit_price, profit, reason)
                        update_obsidian_journal_trade_close(symbol_mt5, pos_info["side"], "WIN" if profit > 0 else "LOSS", profit)
                        
                        del state.active_monitored_positions[symbol_mt5]
                        await broadcast_state_update()

            # 2. Avaliação de Sinais (NQ & XAUUSD)
            assets = [
                ("USTEC", strategies_nq, "NQ"),
                ("XAUUSD", strategies_xau, "XAUUSD")
            ]
            
            for symbol_mt5, strategies_list, standard_symbol in assets:
                if symbol_mt5 in state.active_monitored_positions:
                    continue
                    
                offset = state.config.get("broker_tz_offset", 3)
                df_1m = get_rates_dataframe(symbol_mt5, "1m", 100, offset) if MT5_AVAILABLE and connected else pd.DataFrame()
                df_5m = get_rates_dataframe(symbol_mt5, "5m", 300, offset) if MT5_AVAILABLE and connected else pd.DataFrame()
                df_15m = get_rates_dataframe(symbol_mt5, "15m", 300, offset) if MT5_AVAILABLE and connected else pd.DataFrame()
                df_1h = get_rates_dataframe(symbol_mt5, "1h", 100, offset) if MT5_AVAILABLE and connected else pd.DataFrame()
                df_1d = get_rates_dataframe(symbol_mt5, "1d", 30, offset) if MT5_AVAILABLE and connected else pd.DataFrame()
                
                # Fallback para dados históricos simulados se não houver MT5 ativo
                if (not MT5_AVAILABLE or not connected) and (df_5m.empty or df_1d.empty):
                    try:
                        loader = DataLoader()
                        end_date = datetime.now().strftime("%Y-%m-%d")
                        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                        df_1m = await asyncio.to_thread(loader.load_data, standard_symbol, "1m", start_date, end_date)
                        df_5m = await asyncio.to_thread(loader.load_data, standard_symbol, "5m", start_date, end_date)
                        df_15m = await asyncio.to_thread(loader.load_data, standard_symbol, "15m", start_date, end_date)
                        df_1h = await asyncio.to_thread(loader.load_data, standard_symbol, "1h", start_date, end_date)
                        df_1d = await asyncio.to_thread(loader.load_data, standard_symbol, "1d", start_date, end_date)
                    except Exception:
                        pass
                        
                if df_5m.empty or df_1d.empty:
                    continue
                    
                # Iterar estratégias
                for strategy in strategies_list:
                    strategy.diagnostic_enabled = True
                    signal = strategy.evaluate(df_5m, df_15m, df_1h, df_1d, df_1m)
                    
                    funnel_key = f"{symbol_mt5}_{strategy.name}"
                    state.funnel_logs[funnel_key] = getattr(strategy, "last_gates", [])
                    
                    if signal is not None and signal.action in ["BUY", "SELL"]:
                        await log_and_broadcast(f"🎯 [SINAL IDENTIFICADO] Estratégia '{strategy.name}' gerou gatilho de {signal.action} em {symbol_mt5} @ {signal.entry_price:.2f}")
                        
                        account_balance = config.ACCOUNT_BALANCE
                        if MT5_AVAILABLE and connected:
                            acc_info = await asyncio.to_thread(mt5.account_info)
                            if acc_info is not None:
                                account_balance = acc_info.balance
                                
                        # Rodar regras de risco antes de ir para a IA
                        risk_check = RiskManager.validate_pre_trade_filters(
                            symbol=symbol_mt5,
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            account_balance=account_balance
                        )
                        
                        if not risk_check["approved"]:
                            await log_and_broadcast(f"🛡️ [VETO DE RISCO] Sinal bloqueado pelo gerenciador de risco: {risk_check['reason']}")
                            # Gravar trade bloqueado
                            RiskManager.log_trade(
                                symbol=symbol_mt5,
                                action="PASS",
                                entry_price=signal.entry_price,
                                stop_loss=signal.stop_loss,
                                take_profit=signal.take_profit,
                                size_units=0.0,
                                result="BLOCKED_BY_RISK",
                                profit_loss_usd=0.0,
                                reasoning=f"Filtro quantitativo de Risco: {risk_check['reason']}",
                                strategy=strategy.name,
                                checklist={
                                    "killzone": "APROVADO",
                                    "sweep": "APROVADO",
                                    "mss": "APROVADO",
                                    "payout": "REJEITADO"
                                }
                            )
                            await broadcast_state_update()
                            continue
                            
                        # Acionar a mente da IA Gemini (RAG)
                        await log_and_broadcast("🧠 Enviando setup para avaliação e tomada de decisão cognitiva da IA...")
                        
                        # Formatar dados
                        setup_data = {
                            "strategy": strategy.name,
                            "symbol": standard_symbol,
                            "action": signal.action,
                            "price": signal.entry_price,
                            "timeframe": "5m",
                            "ict_signal": strategy.name,
                            "liquidity_swept": "PDH/PDL Sweep",
                            "fvg_high": signal.entry_price + 1.0,
                            "fvg_low": signal.entry_price - 1.0,
                            "daily_bias": "ALIGNED",
                            "htf_order_flow": "BULLISH" if signal.action == "BUY" else "BEARISH",
                            "draw_on_liquidity": "HTF High/Low Liquidity Pool",
                            "price_action_notes": signal.reasoning,
                            "time_of_day_est": datetime.now(EST_TZ).strftime('%H:%M EST')
                        }
                        
                        ai_decision = await asyncio.to_thread(
                            agent.evaluate_trade_setup,
                            setup_data=setup_data,
                            account_balance=account_balance,
                            is_backtest=False
                        )
                        
                        if not ai_decision.get("approved") or ai_decision.get("action") == "PASS":
                            reason = ai_decision.get("reason") or ai_decision.get("reasoning", "Filtro cognitivo ativo")
                            await log_and_broadcast(f"❌ [VETO COGNITIVO IA] IA abortou setup: {reason}")
                            await broadcast_state_update()
                            continue
                            
                        # APROVADO! Executar
                        await log_and_broadcast(f"✅ [SETUP APROVADO PELA IA] Enviando sinal operacional para execução física!")
                        await log_and_broadcast(f"Preço: {ai_decision.get('entry_price')} | SL: {ai_decision.get('stop_loss')} | TP: {ai_decision.get('take_profit')} | Lotes: {ai_decision.get('size_units')}")
                        
                        config.EXECUTION_MODE = state.config.get("execution_mode", "SIMULATOR")
                        
                        # Executar
                        exec_res = await asyncio.to_thread(CommonExecution.execute_trade, ai_decision)
                        
                        if exec_res.get("success"):
                            order_id = exec_res.get("order_id")
                            if config.EXECUTION_MODE == "MT5" and MT5_AVAILABLE:
                                try:
                                    ticket_id = int(order_id)
                                    state.active_monitored_positions[symbol_mt5] = {
                                        "ticket": ticket_id,
                                        "entry_price": ai_decision.get("entry_price"),
                                        "size": ai_decision.get("size_units"),
                                        "side": ai_decision.get("action"),
                                        "strategy": strategy.name
                                    }
                                except Exception:
                                    pass
                            await log_and_broadcast(f"🚀 [SUCESSO] Ordem enviada ao broker. ID/Ticket: {order_id}")
                        else:
                            err_reason = exec_res.get("error", "Erro físico de comunicação")
                            await log_and_broadcast(f"⚠️ [FALHA NA ORDEM] Erro na execução física da ordem: {err_reason}")
                            
                        await broadcast_state_update()
                        
            if MT5_AVAILABLE and connected:
                await asyncio.to_thread(mt5.shutdown)
                
        except Exception as e:
            await log_and_broadcast(f"[ERRO CRÍTICO DAEMON] {e}")
            traceback.print_exc()
            
        await asyncio.sleep(loop_interval)

# ==========================================
# APP FASTAPI E ENDPOINTS
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start trading daemon as a background task
    daemon_task = asyncio.create_task(run_live_trading_daemon())
    yield
    # Shutdown steps
    state.is_running = False
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    if MT5_AVAILABLE:
        try:
            mt5.shutdown()
        except Exception:
            pass

app = FastAPI(title="Cérebro de Trading Cognitivo ICT", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_path = ROOT_DIR / "templates" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard index.html not found!</h1>")

@app.get("/api/backtests")
async def get_backtests():
    backtest_db_path = ROOT_DIR / "backtest_database.json"
    if backtest_db_path.exists():
        try:
            with open(backtest_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "ideal": {"statistics": {"total_pnl_usd": 0.0}, "trades": []},
        "stressed": {"statistics": {"total_pnl_usd": 0.0}, "trades": []}
    }

@app.get("/api/live_trades")
async def get_live_trades():
    return get_live_trades_data()

@app.get("/api/config")
async def get_config():
    return state.config

@app.post("/api/config")
async def update_config(cfg: dict):
    state.config.update(cfg)
    save_dashboard_config(state.config)
    apply_config_to_modules(state.config)
    await log_and_broadcast(f"⚙️ Parâmetros atualizados via dashboard: Modo={config.EXECUTION_MODE}, Risco={config.RISK_PER_TRADE_PERCENT}%")
    return {"status": "success", "config": state.config}

@app.post("/api/killswitch")
async def toggle_killswitch():
    is_paused = not state.config.get("is_paused", False)
    state.config["is_paused"] = is_paused
    save_dashboard_config(state.config)
    status_msg = "SUSPENSO (PAUSA DE RISCO) 🔴" if is_paused else "ATIVADO (PRODUÇÃO) 🟢"
    await log_and_broadcast(f"🚨 PAINEL DE CONTROLE: Robô foi {status_msg} pelo usuário!")
    await broadcast_state_update()
    return {"status": "success", "is_paused": is_paused}

@app.get("/api/funnels")
async def get_funnels():
    return state.funnel_logs

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Enviar logs em cache
        for log in state.logs:
            await websocket.send_json({"type": "log", "message": log})
            
        # Enviar estado inicial das métricas
        metrics = {"trades_count": 0, "net_profit_loss_usd": 0.0, "net_percentage": 0.0}
        try:
            metrics = RiskManager.get_todays_metrics(config.ACCOUNT_BALANCE)
        except Exception:
            pass
            
        await websocket.send_json({
            "type": "state_update",
            "state": {
                "is_paused": state.config.get("is_paused", False),
                "trades_today": metrics.get("trades_count", 0),
                "daily_pnl": metrics.get("net_profit_loss_usd", 0.0),
                "daily_pnl_pct": metrics.get("net_percentage", 0.0),
                "active_positions_count": len(state.active_monitored_positions)
            }
        })
        
        while True:
            # Mantém a conexão aberta
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# ==========================================
# ENTRADA
# ==========================================
def main():
    print("[INIT] Iniciando servidor do Dashboard & Live Daemon na porta 8000...")
    uvicorn.run("live_daemon_mt5:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
