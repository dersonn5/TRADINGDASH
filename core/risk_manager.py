import os
import json
from datetime import datetime
from pathlib import Path
import config

class RiskManager:
    """
    Gerenciador Quântico de Risco.
    Garante a consistência matemática bloqueando overtrading, drawdowns excessivos,
    calculando lotes ótimos e verificando a relação de Payout (Risco:Retorno) mínima.
    """
    
    DB_FILE = Path(__file__).resolve().parent.parent / "trades_database.json"

    @classmethod
    def _load_db(cls) -> dict:
        """Carrega a base local de trades para controle financeiro diário."""
        if not cls.DB_FILE.exists():
            return {"trades": []}
        try:
            with open(cls.DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"trades": []}

    @classmethod
    def _save_db(cls, data: dict):
        """Salva a base local de trades."""
        with open(cls.DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def log_trade(cls, symbol: str, action: str, entry_price: float, stop_loss: float, take_profit: float, size_units: float, result: str, profit_loss_usd: float = 0.0, reasoning: str = "", strategy: str = "", checklist: dict = None):
        """Registra um trade na base quantitativa local com metadados cognitivos."""
        db = cls._load_db()
        trade_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size_units": size_units,
            "result": result, # 'WIN', 'LOSS', 'PENDING'
            "profit_loss_usd": profit_loss_usd,
            "reasoning": reasoning,
            "strategy": strategy,
            "checklist": checklist or {}
        }
        db["trades"].append(trade_entry)
        cls._save_db(db)

    @classmethod
    def get_todays_metrics(cls, account_balance: float) -> dict:
        """Calcula o drawdown acumulado e lucro do dia atual."""
        db = cls._load_db()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        todays_trades = [
            t for t in db["trades"]
            if t["timestamp"].startswith(today_str)
        ]
        
        trades_count = len(todays_trades)
        net_profit_loss = sum(t["profit_loss_usd"] for t in todays_trades)
        net_percentage = (net_profit_loss / account_balance) * 100 if account_balance > 0 else 0.0
        
        return {
            "trades_count": trades_count,
            "net_profit_loss_usd": net_profit_loss,
            "net_percentage": net_percentage
        }

    @classmethod
    def validate_pre_trade_filters(cls, symbol: str, entry_price: float, stop_loss: float, take_profit: float, account_balance: float, bypass_daily_limits: bool = False) -> dict:
        """
        Valida se o trade atende TODOS os critérios rígidos matemáticos e de drawdown.
        Retorna um dicionário: {"approved": bool, "reason": str}
        """
        metrics = cls.get_todays_metrics(account_balance)
        
        if not bypass_daily_limits:
            # 1. Filtro de Overtrading
            if metrics["trades_count"] >= config.MAX_TRADES_PER_DAY:
                return {
                    "approved": False,
                    "reason": f"Limite máximo de operações diárias atingido: {metrics['trades_count']}/{config.MAX_TRADES_PER_DAY}"
                }
                
            # 2. Filtro de Drawdown Diário (Perda Limite)
            if metrics["net_percentage"] <= -config.MAX_DAILY_DRAWDOWN_PERCENT:
                return {
                    "approved": False,
                    "reason": f"Circuito de Proteção Ativado! Drawdown diário atingiu {metrics['net_percentage']:.2f}%. Limite: -{config.MAX_DAILY_DRAWDOWN_PERCENT}%"
                }
                
            # 3. Filtro de Meta Diária de Lucro
            if metrics["net_percentage"] >= config.DAILY_PROFIT_TARGET_PERCENT:
                return {
                    "approved": False,
                    "reason": f"Metas diárias alcançadas! Lucro acumulado hoje de {metrics['net_percentage']:.2f}%. Meta: {config.DAILY_PROFIT_TARGET_PERCENT}%"
                }
            
        # 4. Filtro Matemático de Payout (Risco:Retorno)
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return {"approved": False, "reason": "Stop Loss não pode ser igual ao preço de entrada (Risco zero calculado)."}
            
        rr_ratio = reward / risk
        if rr_ratio < config.MIN_RISK_REWARD_RATIO:
            return {
                "approved": False,
                "reason": f"Setup Rejeitado por Payout insuficiente. Relação R:R calculada de 1:{rr_ratio:.2f}. Mínimo exigido: 1:{config.MIN_RISK_REWARD_RATIO}"
            }
            
        return {
            "approved": True,
            "reason": f"Filtros de risco aprovados! Relação R:R de 1:{rr_ratio:.2f}. Drawdown de hoje: {metrics['net_percentage']:.2f}%"
        }

    @classmethod
    def calculate_position_size(cls, symbol: str, entry_price: float, stop_loss: float, account_balance: float) -> float:
        """
        Calcula dinamicamente o tamanho do lote/contrato com base no risco de 1%
        e na distância até o Stop Loss (em pontos/pips).
        """
        risk_amount_usd = account_balance * (config.RISK_PER_TRADE_PERCENT / 100.0)
        # Limitar o risco em dólares ao valor máximo definido no config
        risk_amount_usd = min(risk_amount_usd, config.MAX_TRADE_SIZE_USD)
        
        distance = abs(entry_price - stop_loss)
        if distance == 0:
            return 0.0
            
        # Ajuste de valor por ponto dependendo do ativo
        symbol_upper = symbol.upper()
        
        # 1. Nasdaq Mini (NQ) / Micro (MNQ)
        # NQ Mini: 1 ponto = $20. Micro NQ (MNQ): 1 ponto = $2
        if "NQ" in symbol_upper:
            # Assumimos que o padrão no simulador/Tradovate é o NQ Mini ($20/ponto)
            point_value = 20.0
            size = risk_amount_usd / (distance * point_value)
            return round(size, 2)
            
        # 2. S&P 500 Mini (ES) / Micro (MES)
        # ES Mini: 1 ponto = $50. Micro ES (MES): 1 ponto = $5
        elif "ES" in symbol_upper:
            point_value = 50.0
            size = risk_amount_usd / (distance * point_value)
            return round(size, 2)
            
        # 3. Ouro (XAUUSD)
        # CFD de Ouro: geralmente 1 lote padrão = $100 por ponto de oscilação do preço inteiro (ex: 2340 -> 2341 é $100 de oscilação por lote)
        # No MT5, 1 lote de XAUUSD representa 100 onças, logo 1 ponto de variação (ex: de 2300.00 para 2301.00) = $100 de variação
        elif "XAU" in symbol_upper or "GOLD" in symbol_upper:
            point_value = 100.0
            size = risk_amount_usd / (distance * point_value)
            # Limite mínimo de tamanho para MT5 é 0.01 lotes
            return max(0.01, round(size, 2))
            
        # Ativo genérico (1 ponto = 1 dólar por unidade)
        else:
            size = risk_amount_usd / distance
            return round(size, 2)
