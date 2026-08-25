import time
from datetime import datetime
import config

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class MT5Client:
    """
    Cliente de Execução Nativa para MetaTrader 5 (Windows).
    Conecta ao terminal aberto, envia ordens a mercado com Stop Loss e Take Profit
    calculados e acompanha posições para NQ, ES e XAUUSD.
    """

    @classmethod
    def initialize_mt5(cls) -> bool:
        """Inicializa a conexão com o terminal do MetaTrader 5."""
        if not MT5_AVAILABLE:
            print("[MT5][AVISO] Biblioteca 'MetaTrader5' não instalada ou indisponível (requer Windows).")
            return False

        # Conectar ao terminal
        if not mt5.initialize():
            print(f"[MT5][ERRO] Falha ao inicializar o MT5. Código de erro: {mt5.last_error()}")
            return False

        # Se houver credenciais definidas no config, realizar login
        if config.MT5_LOGIN > 0 and config.MT5_PASSWORD:
            print(f"[MT5] Efetuando login na conta {config.MT5_LOGIN}...")
            login_success = mt5.login(
                login=config.MT5_LOGIN,
                password=config.MT5_PASSWORD,
                server=config.MT5_SERVER
            )
            if not login_success:
                print(f"[MT5][ERRO] Login falhou no servidor {config.MT5_SERVER}. Código: {mt5.last_error()}")
                return False
                
        print("[MT5] Conectado com sucesso ao terminal MetaTrader 5!")
        return True

    @classmethod
    def place_order(cls, symbol: str, action: str, entry_price: float, stop_loss: float, take_profit: float, size_units: float) -> dict:
        """
        Envia uma ordem de compra ou venda a mercado no MT5.
        Insere automaticamente SL e TP rígidos.
        """
        # Tentar inicializar o terminal
        if not cls.initialize_mt5():
            print("[MT5][AVISO] MT5 indisponível. Simulando execução no MT5...")
            # Fallback seguro para simulação se o terminal não estiver ativo no computador do usuário
            from core.common_execution import CommonExecution
            return CommonExecution._execute_simulator(symbol, action, entry_price, stop_loss, take_profit, size_units)

        # Selecionar ativo
        symbol_mt5 = cls._normalize_symbol(symbol)
        if not mt5.symbol_select(symbol_mt5, True):
            print(f"[MT5][ERRO] Ativo {symbol_mt5} não pôde ser selecionado no terminal.")
            mt5.shutdown()
            return {"success": False, "error": f"Ativo {symbol_mt5} inválido no MT5"}

        # Obter dados do ativo
        symbol_info = mt5.symbol_info(symbol_mt5)
        if symbol_info is None:
            print(f"[MT5][ERRO] Falha ao obter informações do ativo {symbol_mt5}.")
            mt5.shutdown()
            return {"success": False, "error": "Falha ao obter info do ativo"}

        # Mapeamento do tipo de ordem e preço de disparo (Ask/Bid)
        if action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol_mt5).ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol_mt5).bid

        # Montagem do payload de requisição do MT5
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_mt5,
            "volume": size_units,
            "type": order_type,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": 20,
            "magic": 123456,  # Identificador mágico do nosso Super Agente IA
            "comment": "Super Agente IA - Mente ICT",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,  # Enche ou cancela
        }

        print(f"[MT5] Enviando ticket de ordem: {action} {symbol_mt5} | Volume: {size_units} | Preço: {price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
        
        # Enviar transação
        result = mt5.order_send(request)
        
        if result is None:
            err = mt5.last_error()
            print(f"[MT5][ERRO CRÍTICO] Falha catastrófica ao enviar ordem. Erro: {err}")
            mt5.shutdown()
            return {"success": False, "error": f"Erro MT5 order_send: {err}"}
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[MT5][ERRO] Ordem rejeitada pela corretora. Retcode: {result.retcode} | Mensagem: {result.comment}")
            mt5.shutdown()
            return {"success": False, "error": f"Ordem rejeitada: {result.comment} (retcode: {result.retcode})"}

        print(f"[MT5] Sucesso! Ordem executada. Ticket ID: {result.order}")
        
        # Registrar o trade no banco local
        # Como o trade está aberto no MT5, registramos como 'PENDING'
        from core.risk_manager import RiskManager
        RiskManager.log_trade(
            symbol=symbol_mt5,
            action=action,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size_units=size_units,
            result="PENDING",
            profit_loss_usd=0.0
        )

        mt5.shutdown()
        return {
            "success": True,
            "order_id": str(result.order),
            "result": "PENDING",
            "profit_loss_usd": 0.0
        }

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Adapta o símbolo recebido do TradingView para o padrão do MT5 (ex: XAUUSD, NQ1!, etc)."""
        symbol_upper = symbol.upper()
        if "XAU" in symbol_upper:
            return "XAUUSD"
        elif "NAS" in symbol_upper or "NQ" in symbol_upper:
            # Algumas corretoras usam USTEC, NAS100, NQ100, etc.
            return "USTEC"
        elif "SPX" in symbol_upper or "ES" in symbol_upper or "S&P" in symbol_upper:
            return "US500"
        return symbol
