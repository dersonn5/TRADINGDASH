import subprocess
import time
import sys
import os

# Configura stdout/stderr para UTF-8 no Windows para evitar crashes com print
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_backtest(symbol, strategy):
    print("\n===========================================================")
    print(f"INICIANDO BACKTEST PARA {symbol} ({strategy.upper()})")
    print("===========================================================")
    
    cmd = [
        "python",
        "run_crypto_backtest.py",
        "--symbol", symbol,
        "--strategy", strategy
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.time() - start_time
    
    print(result.stdout)
    if result.stderr:
        print("ERROS / AVISOS:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        
    print(f"Concluido em {elapsed:.2f}s com codigo {result.returncode}")
    return result.returncode == 0

def main():
    print("CEREBRO DE TRADING - ORQUESTRADOR DE BACKTESTS CRIPTO")
    print("Iniciando execucao sequencial para preencher a base de dados mesclada...\n")
    
    setups = [
        ("BTC/USDT:USDT", "silver_bullet"),
        ("ETH/USDT:USDT", "silver_bullet"),
        ("BTC/USDT:USDT", "breaker_block"),
        ("ETH/USDT:USDT", "breaker_block"),
        ("BTC/USDT:USDT", "prop_firm_2024"),
        ("ETH/USDT:USDT", "prop_firm_2024")
    ]
    
    success_count = 0
    for symbol, strategy in setups:
        success = run_backtest(symbol, strategy)
        if success:
            success_count += 1
            
    print(f"\nExecucao de backtests concluida! {success_count}/{len(setups)} setups gerados e mesclados com sucesso.")

if __name__ == "__main__":
    main()
