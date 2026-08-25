import os
from datetime import datetime
import config
from core.risk_manager import RiskManager

class CommonExecution:
    """
    Roteador Central de Execução.
    Direciona as ordens aprovadas para o Simulador (Paper Trading),
    para o MetaTrader 5 (CFD/Ouro) ou para a API Tradovate (Futuros).
    """

    @classmethod
    def execute_trade(cls, ai_decision: dict) -> dict:
        """Roteia a execução com base nas configurações globais."""
        symbol = ai_decision.get("symbol")
        action = ai_decision.get("action")
        entry_price = ai_decision.get("entry_price")
        stop_loss = ai_decision.get("stop_loss")
        take_profit = ai_decision.get("take_profit")
        size_units = ai_decision.get("size_units")
        
        mode = config.EXECUTION_MODE
        print(f"\n[EXECUTION] Iniciando execução no modo: {mode} para {action} {symbol} ({size_units} unidades)...")
        
        if mode == "MT5":
            from core.mt5_client import MT5Client
            return MT5Client.place_order(symbol, action, entry_price, stop_loss, take_profit, size_units)
            
        elif mode == "TRADOVATE":
            from core.tradovate_client import TradovateClient
            return TradovateClient.place_order(symbol, action, entry_price, stop_loss, take_profit, size_units)
            
        else: # Padrão: SIMULATOR (Paper Trading)
            reasoning = ai_decision.get("reasoning", "")
            strategy = ai_decision.get("strategy", "ICT Strategy")
            checklist = {
                "killzone": ai_decision.get("checklist_killzone"),
                "sweep": ai_decision.get("checklist_sweep"),
                "mss": ai_decision.get("checklist_mss"),
                "payout": ai_decision.get("checklist_payout")
            }
            return cls._execute_simulator(symbol, action, entry_price, stop_loss, take_profit, size_units, reasoning, strategy, checklist)

    @classmethod
    def _execute_simulator(cls, symbol: str, action: str, entry_price: float, stop_loss: float, take_profit: float, size_units: float, reasoning: str = "", strategy: str = "", checklist: dict = None) -> dict:
        """Simula a execução e assume um resultado simulado para atualizar drawdown e diário."""
        print(f"[SIMULATOR] Ordem simulada colocada com sucesso!")
        
        # Em simulações de teste simples, para dar feedback dinâmico, simulamos que a operação
        # foi um sucesso parcial (WIN) para alimentar as estatísticas do Obsidian.
        # Risco de 1% - Lucro médio de 2.5% do capital (relação 1:2.5)
        # Vamos assumir um ganho ou perda com base em probabilidade aleatória de 55% win rate para os testes locais.
        import random
        is_win = random.choice([True, False, True]) # 66% de chance de WIN simulado nos testes rápidos
        
        # Cálculo de lucro/perda fictício para alimentar o cérebro
        risk_usd = size_units * abs(entry_price - stop_loss) * (20.0 if "NQ" in symbol.upper() else (50.0 if "ES" in symbol.upper() else 100.0))
        
        # Fallback de segurança se der 0
        if risk_usd == 0:
            risk_usd = 100.0 # Risco fixo hipotético se pontos falharem
            
        if is_win:
            profit_loss = risk_usd * 2.5
            result_str = "WIN"
        else:
            profit_loss = -risk_usd
            result_str = "LOSS"
            
        # Registrar trade no banco quantitativo local para controle diário
        RiskManager.log_trade(
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size_units=size_units,
            result=result_str,
            profit_loss_usd=profit_loss,
            reasoning=reasoning,
            strategy=strategy,
            checklist=checklist
        )
        
        # Atualizar a nota de diário no Obsidian com o resultado simulado final
        # (Em produção real de MT5/Tradovate, rodamos o monitoramento de ordens em segundo plano
        # para gravar o resultado final quando bater no TP/SL!)
        print(f"[SIMULATOR] Resultado do Trade: {result_str} | Financeiro: ${profit_loss:.2f} USD")
        
        return {
            "success": True,
            "order_id": f"SIM-{int(datetime.now().timestamp())}",
            "result": result_str,
            "profit_loss_usd": profit_loss
        }
