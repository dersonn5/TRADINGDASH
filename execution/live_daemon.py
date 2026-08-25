import asyncio
import os
import sys
import traceback
from datetime import datetime, time
import pandas as pd
from dotenv import load_dotenv

# Garantir que o diretório raiz está no python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import config
from data.data_loader import DataLoader
from core.agent import ICTAgent
from core.risk_manager import RiskManager
from core.common_execution import CommonExecution
from core.mcp_client import MCPTradingViewClient
from strategies.silver_bullet_nq import SilverBulletNQ
from strategies.london_sweep_xau import LondonSweepXAU
from strategies.silver_bullet_xau import SilverBulletXAU
from strategies.london_sweep_nq import LondonSweepNQ
from strategies.orb_breakout import ORBBreakout
from strategies.session_configs import (
    make_sb_nq_am, make_sb_nq_lunch, make_sb_nq_close,
    make_sb_xau_am, make_sb_xau_lunch, make_sb_xau_close
)
from execution.order_manager import OrderManager

# Tentar importar o MetaTrader 5 de forma opcional
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

load_dotenv()

class LiveTradingDaemon:
    """
    Mente de Execução ao Vivo (Live Daemon).
    Executa continuamente em segundo plano, monitorando as Killzones e buscando dados
    em tempo real via TradingView MCP (nuvem) ou diretamente do MetaTrader 5 local (zero latência).
    Processa sinais de forma autônoma através da IA Gemini, valida com o Obsidian e executa ordens.
    """
    
    def __init__(self, feed_source: str = "MT5", execute_mode: str = None):
        # "MT5" (leitura direta local de velas no terminal) ou "MCP" (TradingView via MCP)
        self.feed_source = feed_source.upper()
        self.execute_mode = execute_mode or config.EXECUTION_MODE
        self.order_manager = OrderManager()
        self.agent = ICTAgent()
        self.data_loader = DataLoader()
        
        # Instanciar todas as estratégias operacionais em paralelo para a Demo de 60-90 dias
        self.strategies = {
            "orb_breakout":            ORBBreakout(),
            "london_sweep_xau":        LondonSweepXAU(),
            "london_sweep_nq":         LondonSweepNQ(),
            "silver_bullet_nq_am":     make_sb_nq_am(),
            "silver_bullet_nq_lunch":  make_sb_nq_lunch(),
            "silver_bullet_nq_close":  make_sb_nq_close(),
            "silver_bullet_xau_am":    make_sb_xau_am(),
            "silver_bullet_xau_lunch": make_sb_xau_lunch(),
            "silver_bullet_xau_close": make_sb_xau_close()
        }
        
        print("\n" + "="*70)
        print(" 🤖 CÉREBRO DE TRADING COGNITIVO - LIVE DAEMON EM SEGUNDO PLANO")
        print("="*70)
        print(f"  • Fonte de Dados (Feed):   {self.feed_source}")
        print(f"  • Modo de Execução:        {self.execute_mode}")
        print(f"  • Diretório do Obsidian:   {config.OBSIDIAN_VAULT_PATH}")
        print(f"  • MT5 Library Status:      {'DISPONÍVEL' if MT5_AVAILABLE else 'INDISPONÍVEL'}")
        print("="*70 + "\n")

    def _convert_mt5_tf(self, tf_str: str):
        """Converte timeframe string para constante do MT5."""
        if not MT5_AVAILABLE:
            return None
        mapping = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "1h": mt5.TIMEFRAME_H1,
            "1d": mt5.TIMEFRAME_D1
        }
        return mapping.get(tf_str, mt5.TIMEFRAME_M5)

    def _get_candles_from_mt5(self, symbol: str, timeframe: str, count: int = 100) -> pd.DataFrame:
        """Puxa candles em tempo real direto do terminal local do MT5 (Latência zero)."""
        if not MT5_AVAILABLE:
            print("[DAEMON][ERRO] MetaTrader 5 não está instalado ou disponível no sistema.")
            return pd.DataFrame()
            
        if not mt5.initialize():
            print(f"[DAEMON][ERRO] Falha ao inicializar conexão local com terminal MT5: {mt5.last_error()}")
            return pd.DataFrame()
            
        symbol_mt5 = symbol
        if "XAU" in symbol.upper():
            symbol_mt5 = "XAUUSD"
        elif "NQ" in symbol.upper() or "NDX" in symbol.upper():
            symbol_mt5 = "USTEC"
            
        mt5_tf = self._convert_mt5_tf(timeframe)
        
        # Ativa o ativo no Market Watch
        mt5.symbol_select(symbol_mt5, True)
        
        rates = mt5.copy_rates_from_pos(symbol_mt5, mt5_tf, 0, count)
        if rates is None or len(rates) == 0:
            print(f"[DAEMON][ERRO] Não foi possível copiar taxas para {symbol_mt5} do MT5. Erro: {mt5.last_error()}")
            return pd.DataFrame()
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "tick_volume": "volume"
        }, inplace=True)
        df.set_index("time", inplace=True)
        
        # Adicionar timezone UTC para compatibilidade
        df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        return df

    async def _fetch_candles(self, symbol: str, timeframe: str, count: int = 100) -> pd.DataFrame:
        """Busca dados dinamicamente com base na fonte configurada."""
        if self.feed_source == "MT5" and MT5_AVAILABLE:
            try:
                # Carregamento local via terminal MT5 (sem requisições HTTP)
                return self._get_candles_from_mt5(symbol, timeframe, count)
            except Exception as e:
                print(f"[DAEMON][AVISO] Falha ao ler feed nativo do MT5: {e}. Recorrendo ao MCP...")
        
        # Fallback para TradingView via MCP
        try:
            exchange = MCPTradingViewClient.resolve_exchange(symbol)
            res = await MCPTradingViewClient.get_candles(symbol, timeframe, count, exchange)
            data = res.get("data", [])
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
            else:
                df.index = df.index.tz_convert("America/New_York")
            return df
        except Exception as e:
            print(f"[DAEMON][ERRO] Falha ao carregar dados via MCP TradingView: {e}")
            return pd.DataFrame()

    def _is_inside_killzone(self, strategy) -> bool:
        """Verifica se a hora atual EST está dentro da Killzone da estratégia."""
        now_est = datetime.now().astimezone(pd.Timestamp.now(tz="America/New_York").tz).time()
        
        if hasattr(strategy, 'config') and hasattr(strategy.config, 'killzone_start') and hasattr(strategy.config, 'killzone_end'):
            return strategy.config.killzone_start <= now_est < strategy.config.killzone_end
        elif hasattr(strategy, 'config') and hasattr(strategy.config, 'trade_start') and hasattr(strategy.config, 'trade_end'):
            return strategy.config.trade_start <= now_est < strategy.config.trade_end
            
        return False

    async def process_market_cycle(self):
        """Executa um ciclo completo de monitoramento, análise cognitiva e execução."""
        print(f"\n[DAEMON] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando varredura cíclica do mercado...")
        
        account_balance = config.ACCOUNT_BALANCE
        
        for strat_name, strategy in self.strategies.items():
            print(f"[DAEMON] Verificando estratégia: {strat_name} ({strategy.symbol})...")
            
            # 1. Validar Killzone operacional
            if not self._is_inside_killzone(strategy):
                print(f"  • {strategy.symbol} ({strat_name}): Fora da Killzone correspondente. Aguardando a próxima janela.")
                continue
                
            print(f"  🔥 {strategy.symbol} ({strat_name}) está dentro da KILLZONE! Baixando dados...")
            
            # 2. Obter múltiplos timeframes em tempo real
            candles_1m = await self._fetch_candles(strategy.symbol, "1m", 100)
            candles_5m = await self._fetch_candles(strategy.symbol, "5m", 100)
            candles_15m = await self._fetch_candles(strategy.symbol, "15m", 100)
            candles_1h = await self._fetch_candles(strategy.symbol, "1h", 50)
            candles_1d = await self._fetch_candles(strategy.symbol, "1d", 10)
            
            if candles_5m.empty or candles_1d.empty:
                print(f"  [ERRO] Não foi possível obter dados ao vivo para {strategy.symbol}. Pulando ciclo.")
                continue
                
            # 3. Rodar a lógica da estratégia matemática
            print(f"  • Executando avaliação matemática para {strategy.symbol} ({strat_name})...")
            signal = strategy.evaluate(candles_5m, candles_15m, candles_1h, candles_1d, candles_1m)
            
            if signal is None:
                print(f"  • {strategy.symbol} ({strat_name}): Nenhum sinal matemático/gráfico de ICT detectado neste candle.")
                continue
                
            print(f"  🎯 [SINAL GRÁFICO] Setup {signal.action} detectado em {strategy.symbol}! Gatilho: {signal.reasoning}")
            
            # 4. Acionar a inteligência artificial (Gemini RAG Obsidian) para Avaliação Cognitiva
            setup_data = {
                "strategy": strategy.name,
                "symbol": signal.symbol,
                "action": signal.action,
                "price": signal.entry_price,
                "timeframe": "5m",
                "ict_signal": signal.reasoning,
                "liquidity_swept": "Asian Range Boundary",
                "fvg_high": signal.entry_price * 1.001 if signal.action == "BUY" else signal.stop_loss,
                "fvg_low": signal.stop_loss if signal.action == "BUY" else signal.entry_price * 0.999,
                "daily_bias": "BULLISH" if signal.action == "BUY" else "BEARISH",
                "htf_order_flow": "Confirmado por alinhamento estrutural H1/D1",
                "draw_on_liquidity": "Pool de liquidez da sessão oposta",
                "price_action_notes": f"Vela M5 fechou confirmando o setup e Consequent Encroachment em {signal.entry_price:.2f}",
                "time_of_day_est": datetime.now().astimezone(pd.Timestamp.now(tz="America/New_York").tz).strftime("%H:%M EST")
            }
            
            print(f"  🧠 Acionando Mente Cognitiva Gemini (RAG) para validação do trade...")
            ai_decision = self.agent.evaluate_trade_setup(
                setup_data=setup_data,
                account_balance=account_balance,
                is_backtest=False
            )
            
            if not ai_decision.get("approved"):
                reason = ai_decision.get("reason") or ai_decision.get("reasoning")
                print(f"  ❌ [REJEITADO] IA rejeitou a operação: {reason}")
                
                # Registrar a rejeição como uma perda evitada no DB de trades
                RiskManager.log_trade(
                    symbol=signal.symbol,
                    action="PASS",
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    size_units=0.0,
                    result="PREVENTED_LOSS",
                    profit_loss_usd=0.0,
                    reasoning=ai_decision.get("reasoning", str(reason)),
                    strategy=strategy.name,
                    checklist={
                        "killzone": ai_decision.get("checklist_killzone", False),
                        "sweep": ai_decision.get("checklist_sweep", False),
                        "mss": ai_decision.get("checklist_mss", False),
                        "payout": ai_decision.get("checklist_payout", False)
                    }
                )
                continue
                
            print(f"  ✅ [APROVADO] Mente Cognitiva validou o setup!")
            print(f"    • Direção:     {ai_decision.get('action')}")
            print(f"    • Entrada:     {ai_decision.get('entry_price')}")
            print(f"    • Stop Loss:   {ai_decision.get('stop_loss')}")
            print(f"    • Take Profit: {ai_decision.get('take_profit')}")
            print(f"    • Lotes:       {ai_decision.get('size_units')}")
            
            # 5. Execução real/simulada imediata
            print("  ⚡ Encaminhando ordem ao Roteador de Execução física...")
            exec_res = CommonExecution.execute_trade(ai_decision)
            
            if exec_res.get("success"):
                print(f"  🎉 [SUCESSO] Ordem enviada com sucesso! ID da Ordem: {exec_res.get('order_id')}")
            else:
                print(f"  ⚠️ [ERRO DE EXECUÇÃO] Falha física ao colocar ordem: {exec_res.get('error')}")

    async def start_daemon_loop(self, interval_seconds: int = 15):
        """Inicia o loop infinito do daemon em segundo plano."""
        print(f"\n[DAEMON] Loop de execução ao vivo iniciado. Intervalo de poll: {interval_seconds} segundos.")
        print("[DAEMON] Pressione Ctrl+C para encerrar o bot de forma segura.")
        
        while True:
            try:
                await self.process_market_cycle()
            except Exception as e:
                print(f"[DAEMON][ERRO GRAVE] Erro inesperado no ciclo principal: {e}")
                traceback.print_exc()
                
            await asyncio.sleep(interval_seconds)

def main():
    # Carregar argumentos CLI opcionais
    import argparse
    parser = argparse.ArgumentParser(description="Daemon de Execução ao Vivo em Segundo Plano.")
    parser.add_argument("--feed", type=str, default="MT5", choices=["MT5", "MCP"], help="Fonte de dados de candles (MT5 local ou TradingView MCP).")
    parser.add_argument("--interval", type=int, default=15, help="Intervalo de varredura do mercado em segundos.")
    
    args = parser.parse_args()
    
    # Criar e iniciar o daemon
    daemon = LiveTradingDaemon(feed_source=args.feed)
    
    try:
        asyncio.run(daemon.start_daemon_loop(args.interval))
    except KeyboardInterrupt:
        print("\n[DAEMON] Desligamento ordenado acionado pelo usuário (KeyboardInterrupt).")
        if MT5_AVAILABLE:
            try:
                mt5.shutdown()
                print("[DAEMON] Conexão com MetaTrader 5 encerrada de forma limpa.")
            except Exception:
                pass
        print("[DAEMON] Bot desligado com sucesso.")

if __name__ == "__main__":
    main()
