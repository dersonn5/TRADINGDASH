import os
import sys
from datetime import datetime
import config

# Adicionar pasta atual ao Path
sys.path.append(str(config.BASE_DIR))

from core.agent import ICTAgent
from core.common_execution import CommonExecution
from core.rag import ObsidianRAG

def run_simulation():
    print("═══════════════════════════════════════════════════════════")
    print("  SIMULAÇÃO DE DISPARO - SUPER AGENTE ICT AI")
    print("═══════════════════════════════════════════════════════════\n")
    
    # 1. Verificar se a chave do Gemini está configurada
    if not config.GEMINI_API_KEY:
        print("❌ ERRO: GEMINI_API_KEY não encontrada no ambiente!")
        print("Por favor, configure sua chave do Gemini antes de rodar o teste.")
        return
        
    print(f"[TEST] Diretório do Vault do Obsidian: {config.OBSIDIAN_VAULT_PATH}")
    print(f"[TEST] Modo de Execução:              {config.EXECUTION_MODE}\n")

    # 2. Mock do Payload do TradingView
    # Simula um setup clássico de alta em Ouro (XAUUSD):
    # - Varredura de liquidez de baixa (SSL)
    # - Quebra de estrutura de alta (MSS) no NY Open (Killzone)
    # - Entrada na FVG formada de alta
    mock_tv_signal = {
        "secret": config.WEBHOOK_SECRET,
        "symbol": "XAUUSD",
        "action": "BUY",
        "price": 2342.50, # Preço atual de mercado (toque na FVG)
        "timeframe": "15m",
        "ict_signal": "Liquidity Sweep + MSS + FVG Touch",
        "liquidity_swept": "Sell-side Liquidity (SSL)",
        "fvg_high": 2343.80,
        "fvg_low": 2340.50
    }

    # Saldo de testes de $10,000
    account_balance = 10000.0

    print("[TEST] Disparando sinal de teste simulado...")
    print(f"       Ativo: {mock_tv_signal['symbol']} | Ação: {mock_tv_signal['action']} | Preço: ${mock_tv_signal['price']}")
    print(f"       Sinal: {mock_tv_signal['ict_signal']}\n")

    # 3. Inicializar o Agente de IA e rodar a avaliação cognitiva
    agent = ICTAgent()
    ai_decision = agent.evaluate_trade_setup(mock_tv_signal, account_balance)

    print("\n═══════════════════════════════════════════════════════════")
    print("  RESULTADO DA AVALIAÇÃO COGNITIVA DA IA")
    print("═══════════════════════════════════════════════════════════")
    print(f"Decisão da IA: {ai_decision.get('action')}")
    print(f"Aprovado:      {ai_decision.get('approved')}")
    print(f"Confiança:     {ai_decision.get('confidence_score') * 100:.1f}%")
    print(f"Preço Entrada: {ai_decision.get('entry_price')}")
    print(f"Stop Loss:     {ai_decision.get('stop_loss')}")
    print(f"Take Profit:   {ai_decision.get('take_profit')}")
    print(f"Lote/Tamanho:  {ai_decision.get('size_units')} unidades (Lotes)")
    print(f"Risco:Retorno: 1:{ai_decision.get('risk_reward_ratio')}")
    print("-----------------------------------------------------------")
    print("Raciocínio Chain-of-Thought:")
    print(ai_decision.get("reasoning"))
    print("═══════════════════════════════════════════════════════════\n")

    # 4. Executar se for aprovado
    if ai_decision.get("approved") and ai_decision.get("action") in ["BUY", "SELL"]:
        exec_result = CommonExecution.execute_trade(ai_decision)
        print(f"[TEST] Ordem enviada para execução física. Resultado: {exec_result}\n")
    else:
        print("[TEST] Setup não qualificado para execução real/papel.\n")
        
    print("[TEST] Verifique o seu Obsidian! Um relatório completo em markdown")
    print("       acaba de ser gravado na pasta 'Diario_Trades' do seu cofre!")
    print("═══════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    run_simulation()
