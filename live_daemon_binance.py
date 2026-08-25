"""
Daemon Binance Futures: multi-ativo, multi-estratégia, WebSocket-driven via CCXT Pro.
Avalia estratégias a cada candle M5 fechado. Testnet ativa (paper trading).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import asyncio
import os
from datetime import time, datetime, timedelta
from dotenv import load_dotenv
from execution.binance_client import BinanceConfig
from data.binance_data_provider import BinanceDataProvider
from execution.binance_executor import BinanceExecutor
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig

load_dotenv()

# 3 sessões Silver Bullet × 5 ativos = 15 combinações de oportunidade
def _sb(kz_start: time, kz_end: time, min_sl: float, session: str) -> SilverBulletNQ:
    return SilverBulletNQ(SilverBulletConfig(
        killzone_start=kz_start,
        killzone_end=kz_end,
        min_sl_distance_pts=min_sl,
        min_rr=3.0,
        require_daily_bias=True,
        require_premium_discount=True,
        session_name=session,
    ))

NY_AM    = (time(10, 0), time(11, 0))
NY_LUNCH = (time(13, 0), time(14, 0))
NY_CLOSE = (time(15, 0), time(16, 0))

STRATEGY_MAP = {
    "ETH/USDT:USDT": [
        _sb(*NY_AM,    20.0, "eth_ny_am"),
        _sb(*NY_LUNCH, 20.0, "eth_ny_lunch"),
        _sb(*NY_CLOSE, 20.0, "eth_ny_close"),
    ],
    "SOL/USDT:USDT": [
        _sb(*NY_AM,    2.0, "sol_ny_am"),
        _sb(*NY_LUNCH, 2.0, "sol_ny_lunch"),
        _sb(*NY_CLOSE, 2.0, "sol_ny_close"),
    ],
    "BNB/USDT:USDT": [
        _sb(*NY_AM,    5.0, "bnb_ny_am"),
        _sb(*NY_LUNCH, 5.0, "bnb_ny_lunch"),
    ],
    "XRP/USDT:USDT": [
        _sb(*NY_AM,    0.03, "xrp_ny_am"),
        _sb(*NY_LUNCH, 0.03, "xrp_ny_lunch"),
        _sb(*NY_CLOSE, 0.03, "xrp_ny_close"),
    ],
    "DOGE/USDT:USDT": [
        _sb(*NY_AM,    0.004, "doge_ny_am"),
    ],
}

SYMBOLS = list(STRATEGY_MAP.keys())
TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"]

# Variáveis globais de controle de risco
trades_today = 0
daily_losses = 0
consecutive_losses = 0
daily_pnl = 0.0
pause_until = None
executor = None


def log_to_file(message: str):
    log_path = "logs_daemon_binance.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")
    print(formatted_msg)


async def has_open_position(symbol: str) -> bool:
    """Verifica se já existe uma posição aberta para o símbolo na Binance."""
    try:
        positions = await executor._execute_with_retry(executor.exchange.fetch_positions, [symbol])
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = abs(float(pos.get('contracts', 0) or pos.get('positionAmt', 0) or 0))
                if contracts > 0:
                    return True
    except Exception as e:
        log_to_file(f"[Daemon Risk Check ERROR] Falha ao verificar posições abertas para {symbol}: {e}")
    return False


def check_risk_gate(symbol: str) -> bool:
    """Aplica o filtro de gestão de risco rígido antes de permitir o trade."""
    global trades_today, daily_pnl, consecutive_losses, pause_until
    
    # 1. Verificar pausa por derrotas consecutivas
    if pause_until and datetime.now() < pause_until:
        log_to_file(f"[Risk Gate] Ignorando sinal: Bot em pausa de 24h até {pause_until} devido a perdas consecutivas.")
        return False
        
    # 2. Verificar limite diário de trades
    import config as app_config
    max_trades = getattr(app_config, "MAX_TRADES_PER_DAY", 2)
    if trades_today >= max_trades:
        log_to_file(f"[Risk Gate] Ignorando sinal: Limite diário de trades atingido ({trades_today}/{max_trades}).")
        return False
        
    # 3. Verificar drawdown diário
    max_drawdown = getattr(app_config, "MAX_DAILY_DRAWDOWN_PERCENT", 3.0) / 100.0
    drawdown_limit = - (executor.balance * max_drawdown)
    if daily_pnl <= drawdown_limit:
        log_to_file(f"[Risk Gate] Ignorando sinal: Drawdown diário atingido ({daily_pnl:.2f} USD <= {drawdown_limit:.2f} USD). Bot bloqueado!")
        return False
        
    return True


async def monitor_position(symbol: str, fill_price: float, amount: float, side: str, sl_order_id: str, tp_order_id: str):
    """Monitora a posição em background até atingir SL, TP ou ser fechada externamente."""
    global daily_pnl, consecutive_losses, daily_losses, pause_until
    log_to_file(f"[Monitor] Iniciando monitoramento da posição de {symbol} (Lote: {amount} @ {fill_price})...")
    
    while True:
        await asyncio.sleep(10)
        try:
            # 1. Verificar se SL ou TP foi acionado
            sl_order = await executor._execute_with_retry(executor.exchange.fetch_order, sl_order_id, symbol)
            tp_order = await executor._execute_with_retry(executor.exchange.fetch_order, tp_order_id, symbol)
            
            sl_status = sl_order['status']
            tp_status = tp_order['status']
            
            if sl_status == 'closed' or tp_status == 'closed':
                closed_by = "STOP_LOSS" if sl_status == 'closed' else "TAKE_PROFIT"
                exit_order = sl_order if closed_by == "STOP_LOSS" else tp_order
                exit_price = exit_order.get('price') or exit_order.get('average') or exit_order.get('stopPrice')
                
                # Cancela a outra ordem do bracket
                other_order_id = tp_order_id if closed_by == "STOP_LOSS" else sl_order_id
                try:
                    await executor._execute_with_retry(executor.exchange.cancel_order, other_order_id, symbol)
                    log_to_file(f"[Monitor] Ordem oposta {other_order_id} cancelada com sucesso.")
                except Exception as ex:
                    log_to_file(f"[Monitor WARNING] Falha ao cancelar ordem oposta {other_order_id}: {ex}")
                    
                # Calcular P&L final
                pnl = 0.0
                price_diff = exit_price - fill_price
                if side == "buy":
                    pnl = price_diff * amount
                else:
                    pnl = -price_diff * amount
                    
                # Taxa Binance Futures (0.04% maker/taker)
                commission = (fill_price * amount + exit_price * amount) * 0.0004
                net_pnl = pnl - commission
                
                daily_pnl += net_pnl
                
                if net_pnl < 0:
                    consecutive_losses += 1
                    daily_losses += 1
                    log_to_file(f"[Monitor] POSIÇÃO FECHADA por {closed_by}! P&L: {net_pnl:.2f} USD (Loss). Derrotas consecutivas: {consecutive_losses}")
                    if consecutive_losses >= 5:
                        pause_until = datetime.now() + timedelta(hours=24)
                        log_to_file(f"[Monitor CRITICAL] 5 derrotas consecutivas atingidas! Bot pausado por 24 horas.")
                else:
                    consecutive_losses = 0
                    log_to_file(f"[Monitor] POSIÇÃO FECHADA por {closed_by}! P&L: {net_pnl:.2f} USD (Win!).")
                break
                
            # 2. Verificar se a posição foi zerada externamente
            positions = await executor._execute_with_retry(executor.exchange.fetch_positions, [symbol])
            position_size = 0.0
            for pos in positions:
                if pos['symbol'] == symbol:
                    position_size = abs(float(pos.get('contracts', 0) or pos.get('positionAmt', 0) or 0))
                    break
                    
            if position_size == 0:
                log_to_file(f"[Monitor] Posição de {symbol} foi zerada ou fechada externamente. Cancelando ordens do bracket...")
                for o_id in [sl_order_id, tp_order_id]:
                    try:
                        await executor._execute_with_retry(executor.exchange.cancel_order, o_id, symbol)
                    except Exception:
                        pass
                break
                
        except Exception as e:
            log_to_file(f"[Monitor ERROR] Erro no loop de monitoramento: {e}")


async def refresh_higher_timeframes(provider: BinanceDataProvider):
    """Atualiza periodicamente (a cada 5m) os candles maiores (15m, 1h, 1d) via REST."""
    while True:
        try:
            await asyncio.sleep(300)  # A cada 5 minutos
            log_to_file("[Daemon] Iniciando atualização periódica de timeframes superiores...")
            for symbol in SYMBOLS:
                for tf in ["15m", "1h", "1d"]:
                    await provider.refresh_timeframe(symbol, tf)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log_to_file(f"[Daemon Refresh ERROR]: {e}")


async def health_heartbeat():
    """Imprime e grava o status de saúde do daemon a cada 5 minutos."""
    while True:
        await asyncio.sleep(300)
        try:
            positions_summary = []
            for symbol in SYMBOLS:
                positions = await executor._execute_with_retry(executor.exchange.fetch_positions, [symbol])
                for pos in positions:
                    if pos['symbol'] == symbol:
                        contracts = float(pos.get('contracts', 0) or pos.get('positionAmt', 0) or 0)
                        if contracts != 0:
                            positions_summary.append(f"{symbol}: {contracts:.4f} @ {pos.get('entryPrice')}")
            
            active_pos_str = ", ".join(positions_summary) if positions_summary else "Nenhuma"
            log_to_file(f"[HEARTBEAT] Status: ATIVO | P&L Diário: {daily_pnl:.2f} USD | "
                        f"Trades Hoje: {trades_today} | "
                        f"Posições Ativas: {active_pos_str}")
        except Exception as e:
            log_to_file(f"[HEARTBEAT ERROR] {e}")


async def main():
    global executor, trades_today
    
    import config as app_config
    api_key = getattr(app_config, "BINANCE_TESTNET_API_KEY", "")
    api_secret = getattr(app_config, "BINANCE_TESTNET_SECRET", "")
    balance = getattr(app_config, "ACCOUNT_BALANCE", 10000.0)
    risk_pct = getattr(app_config, "RISK_PER_TRADE_PERCENT", 1.0) / 100.0
    
    config = BinanceConfig(
        api_key=api_key,
        api_secret=api_secret,
        paper_trading=True,
    )
    
    provider = BinanceDataProvider(config, max_candles=300)
    executor = BinanceExecutor(config, balance_usd=balance, risk_pct=risk_pct)

    log_to_file("[BINANCE INIT] Bootstrap histórico via REST...")
    await provider.bootstrap(SYMBOLS, TIMEFRAMES)
    log_to_file("[BINANCE INIT] Bootstrap completo. Iniciando WebSocket...")

    # Tarefas auxiliares em background
    refresh_task = asyncio.create_task(refresh_higher_timeframes(provider))
    heartbeat_task = asyncio.create_task(health_heartbeat())

    async def on_closed_candle(symbol: str, tf: str, candle: list):
        global trades_today
        if tf != "5m":
            return
        if not provider.is_ready(symbol, "5m"):
            return

        df_1m  = provider.get_dataframe(symbol, "1m")
        df_5m  = provider.get_dataframe(symbol, "5m")
        df_15m = provider.get_dataframe(symbol, "15m")
        df_1h  = provider.get_dataframe(symbol, "1h")
        df_1d  = provider.get_dataframe(symbol, "1d")

        for strategy in STRATEGY_MAP.get(symbol, []):
            try:
                signal = strategy.evaluate(df_5m, df_15m, df_1h, df_1d, df_1m)
                if signal and signal.action in ["BUY", "SELL"]:
                    log_to_file(f"[BINANCE SIGNAL] {symbol} {strategy.__class__.__name__}: "
                                f"{signal.action} @ {signal.entry_price} "
                                f"SL={signal.stop_loss} TP={signal.take_profit}")
                    
                    # 1. Gestão de Risco Gate
                    if not check_risk_gate(symbol):
                        continue
                        
                    # 2. Verificar se já está posicionado
                    if await has_open_position(symbol):
                        log_to_file(f"[Risk Gate] Ignorando sinal: Posição já aberta para {symbol}.")
                        continue
                        
                    # 3. Execução Bracket
                    trades_today += 1
                    result = await executor.execute(signal, symbol)
                    
                    if result.get("status") == "FILLED":
                        log_to_file(f"[BINANCE ORDER FILLED] {symbol} preenchido. ID: {result['entry_order_id']}")
                        # Iniciar monitoramento da posição aberta em background
                        asyncio.create_task(monitor_position(
                            symbol=symbol,
                            fill_price=result['fill_price'],
                            amount=result['amount'],
                            side="buy" if signal.action == "BUY" else "sell",
                            sl_order_id=result['sl_order_id'],
                            tp_order_id=result['tp_order_id']
                        ))
                    else:
                        trades_today = max(0, trades_today - 1)  # Estorna se falhou
                        log_to_file(f"[BINANCE ORDER FAILED] Falha na execução: {result.get('reason', 'Unknown error')}")
                        
            except Exception as e:
                log_to_file(f"[BINANCE ERRO] {strategy.__class__.__name__} @ {symbol}: {e}")

    # Escuta WebSocket para M1 e M5 em todos os símbolos simultaneamente
    watchers = [
        provider.watch_symbol_timeframe(sym, tf, on_closed_candle)
        for sym in SYMBOLS
        for tf in ["1m", "5m"]
    ]
    
    try:
        await asyncio.gather(*watchers, refresh_task, heartbeat_task)
    except asyncio.CancelledError:
        pass
    finally:
        log_to_file("[Shutdown] Sinal de parada detectado. Cancelando ordens pendentes e fechando conexões...")
        refresh_task.cancel()
        heartbeat_task.cancel()
        
        # Cancela todas as ordens abertas na exchange de forma limpa
        try:
            for symbol in SYMBOLS:
                log_to_file(f"[Shutdown] Cancelando ordens abertas para {symbol}...")
                await executor._execute_with_retry(executor.exchange.cancel_all_orders, symbol)
        except Exception as e:
            log_to_file(f"[Shutdown WARNING] Falha ao cancelar ordens: {e}")
            
        await provider.close()
        log_to_file(f"[Shutdown] Encerramento concluído. Trades Hoje: {trades_today} | P&L Diário Final: {daily_pnl:.2f} USD")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_to_file("\n[Daemon] Bot encerrado manualmente via KeyboardInterrupt.")
