import os
import sys
import config

# Configura a saída padrão para UTF-8 no Windows para evitar erros de encoding de console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.backtester import CognitiveBacktester

def main():
    print("===========================================================")
    print("  INICIALIZANDO MOTOR DE BACKTEST COGNITIVO ICT MULTI-ATIVOS")
    print("===========================================================\n")
    
    # Verificar a chave API do Gemini antes de rodar
    if not config.GEMINI_API_KEY:
        print("[ERRO] GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
        print("Por favor, cole sua API Key no arquivo .env antes de rodar o backtest.")
        sys.exit(1)
        
    scenarios_gold = config.BASE_DIR / "backtest_scenarios" / "scenarios_xauusd.json"
    scenarios_nq = config.BASE_DIR / "backtest_scenarios" / "scenarios_nq.json"
    
    # 1. Executar Backtest do Ouro (XAUUSD)
    print("\n[SUITE] >>> INICIANDO BACKTEST DE ELITE - GOLD (XAUUSD) <<<")
    backtester_gold = CognitiveBacktester(scenarios_gold)
    stats_gold = backtester_gold.run_backtest()
    
    # 2. Executar Backtest da Nasdaq (NQ/MNQ)
    print("\n[SUITE] >>> INICIANDO BACKTEST DE ELITE - NASDAQ MINI (NQ) <<<")
    backtester_nq = CognitiveBacktester(scenarios_nq)
    stats_nq = backtester_nq.run_backtest()
    
    if stats_gold and stats_nq:
        print("\n===========================================================")
        print("⚡ [SUITE COMPLETA] SUPER BACKTEST CONCLUÍDO COM SUCESSO!")
        print("-----------------------------------------------------------")
        print(f"🥇 GOLD (XAUUSD): PnL: ${stats_gold['total_pnl_usd']:+.2f} | Win Rate: {stats_gold['win_rate']*100:.1f}% | Fator de Lucro: {stats_gold['profit_factor']:.2f}")
        print(f"🗽 NASDAQ (NQ):   PnL: ${stats_nq['total_pnl_usd']:+.2f} | Win Rate: {stats_nq['win_rate']*100:.1f}% | Fator de Lucro: {stats_nq['profit_factor']:.2f}")
        print("-----------------------------------------------------------")
        print("Os diários isolados de cada operação foram gravados na pasta:")
        print("  - 'Backtests/Logs_Trades/'")
        print("Os relatórios consolidados dinâmicos de curadoria foram gravados em:")
        print("  - 'Backtests/Relatorio_Curadoria_XAUUSD.md'")
        print("  - 'Backtests/Relatorio_Curadoria_NQ.md'")
        print("===========================================================")
    else:
        print("[ERRO] Falha ao rodar a suite de backtest.")

if __name__ == "__main__":
    main()
