import httpx
from datetime import datetime
import config

class TradovateClient:
    """
    Cliente de Execução de Futuros para a API Tradovate.
    Lida com autenticação via OAuth, obtenção de tokens de acesso e envio
    de ordens de contratos (NQ, ES) com brackets de SL e TP automáticos.
    """
    
    BASE_URL_DEMO = "https://demo.tradovateapi.com/v1"
    BASE_URL_LIVE = "https://live.tradovateapi.com/v1"

    @classmethod
    def _get_base_url(cls) -> str:
        """Retorna o endpoint correto de acordo com a configuração de Demo/Live."""
        return cls.BASE_URL_DEMO if config.TRADOVATE_DEMO else cls.BASE_URL_LIVE

    @classmethod
    def get_access_token(cls) -> str:
        """Autentica na API da Tradovate e retorna o accessToken."""
        # Se não houver chaves de usuário configuradas, retorna Vazio
        if not config.TRADOVATE_USER or not config.TRADOVATE_PASSWORD:
            return ""

        url = f"{cls._get_base_url()}/auth/accesstoken"
        payload = {
            "name": config.TRADOVATE_USER,
            "password": config.TRADOVATE_PASSWORD,
            "appId": config.TRADOVATE_APP_ID,
            "appVersion": config.TRADOVATE_APP_VERSION,
            "cid": config.TRADOVATE_CID
        }

        try:
            response = httpx.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("accessToken", "")
            else:
                print(f"[TRADOVATE][ERRO] Autenticação falhou. Status: {response.status_code} | Resposta: {response.text}")
                return ""
        except Exception as e:
            print(f"[TRADOVATE][ERRO] Exceção na autenticação: {str(e)}")
            return ""

    @classmethod
    def place_order(cls, symbol: str, action: str, entry_price: float, stop_loss: float, take_profit: float, size_units: float) -> dict:
        """
        Envia ordem de compra ou venda de contrato de futuros no Tradovate.
        Envia uma ordem principal com SL e TP aninhados (Bracket Orders).
        """
        token = cls.get_access_token()
        if not token:
            print("[TRADOVATE][AVISO] Credenciais Tradovate ausentes ou inválidas. Simulando execução...")
            # Fallback seguro para simulação se as chaves da Tradovate não estiverem no .env
            from core.common_execution import CommonExecution
            return CommonExecution._execute_simulator(symbol, action, entry_price, stop_loss, take_profit, size_units)

        # Tradovate exige IDs de ativo específicos. Faremos um mapeamento simplificado do ativo
        tradovate_symbol = cls._normalize_symbol(symbol)
        
        # Obter ID da conta
        account_id = cls._get_account_id(token)
        if not account_id:
            return {"success": False, "error": "Falha ao recuperar ID da conta Tradovate"}

        url = f"{cls._get_base_url()}/order/placeorder"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Payload para ordem de mercado com brackets OCO de SL/TP
        payload = {
            "accountSpec": config.TRADOVATE_USER,
            "accountId": account_id,
            "action": "Buy" if action == "BUY" else "Sell",
            "symbol": tradovate_symbol,
            "orderQty": int(size_units),
            "orderType": "Market",
            "isAutomated": True,
            # Bracket de SL e TP (Tradovate aceita ordens acopladas OCO)
            "brackets": [
                {
                    "qty": int(size_units),
                    "action": "Sell" if action == "BUY" else "Buy",
                    "orderType": "Stop",
                    "stopPrice": stop_loss,
                    "isAutomated": True
                },
                {
                    "qty": int(size_units),
                    "action": "Sell" if action == "BUY" else "Buy",
                    "orderType": "Limit",
                    "price": take_profit,
                    "isAutomated": True
                }
            ]
        }

        print(f"[TRADOVATE] Enviando ordem de futuros: {action} {tradovate_symbol} | Contratos: {int(size_units)} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("orderId", f"TV-{int(datetime.now().timestamp())}")
                print(f"[TRADOVATE] Sucesso! Ordem colocada. Order ID: {order_id}")
                
                # Registrar no banco local como PENDING
                from core.risk_manager import RiskManager
                RiskManager.log_trade(
                    symbol=tradovate_symbol,
                    action=action,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    size_units=size_units,
                    result="PENDING",
                    profit_loss_usd=0.0
                )
                
                return {
                    "success": True,
                    "order_id": str(order_id),
                    "result": "PENDING",
                    "profit_loss_usd": 0.0
                }
            else:
                print(f"[TRADOVATE][ERRO] Erro ao enviar ordem. Status: {response.status_code} | Resposta: {response.text}")
                return {"success": False, "error": f"Erro Tradovate API: {response.text}"}
                
        except Exception as e:
            print(f"[TRADOVATE][ERRO] Exceção ao enviar ordem: {str(e)}")
            return {"success": False, "error": f"Exceção Tradovate API: {str(e)}"}

    @classmethod
    def _get_account_id(cls, token: str) -> int:
        """Puxa a conta padrão do usuário logado na Tradovate."""
        url = f"{cls._get_base_url()}/account/list"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = httpx.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                accounts = response.json()
                if accounts:
                    # Retorna o ID da primeira conta listada
                    return accounts[0].get("id", 0)
            return 0
        except Exception:
            return 0

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Traduz símbolos para o formato aceito pela Tradovate (ex: NQM6 para Nasdaq Junho, ou genéricos)."""
        symbol_upper = symbol.upper()
        # Mapeamento simplificado. Em futuros reais, exige o ticker exato do contrato atual.
        # Exemplo: NQM6 (Nasdaq Junho 26) ou ticker contínuo se a corretora permitir.
        if "NQ" in symbol_upper:
            return "NQ" # Símbolo base contínuo Tradovate
        elif "ES" in symbol_upper:
            return "ES"
        return symbol
