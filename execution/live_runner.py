import os
from datetime import datetime, timedelta
import pandas as pd
from data.data_loader import DataLoader
from strategies.silver_bullet_nq import SilverBulletNQ
from strategies.london_sweep_xau import LondonSweepXAU
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.walk_forward import WalkForwardEngine

class LiveRunner:
    """
    Orquestrador de Execução e Validação.
    Carrega dados históricos reais de NQ e XAUUSD, executa o motor de backtest candle-by-candle,
    aplica validação walk-forward out-of-sample e gera relatórios premium.
    """
    def __init__(self):
        self.data_loader = DataLoader()
        self.backtest_engine = BacktestEngine()
        self.walk_forward_engine = WalkForwardEngine(self.backtest_engine)

    def run_validation_pipeline(self):
        """
        Executa a validação completa dos dois setups (NQ e XAUUSD) usando dados reais de 2 anos (ou limite do fallback).
        """
        # Se temos POLYGON_API_KEY no .env, usamos 365 dias. Caso contrário, usamos 30 dias devido a limites do yfinance fallback para intraday 5m/15m.
        has_polygon_key = bool(os.getenv("POLYGON_API_KEY"))
        days_to_fetch = 365 if has_polygon_key else 30
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime("%Y-%m-%d")
        
        print("="*60)
        print("     INICIANDO PIPELINE DE VALIDAÇÃO QUANTITATIVA - PATH A     ")
        print("="*60)
        print(f"Período: {start_date} a {end_date}\n")
        
        # ----------------------------------------------------
        # 1. SETUP #1: Silver Bullet NY AM (NQ)
        # ----------------------------------------------------
        print("\n" + "-"*50)
        print("  VALIDANDO SETUP #1: SILVER BULLET NY AM (NQ)  ")
        print("-"*50)
        
        # NQ front month or Index Proxy (yfinance fallback mapping handles it)
        symbol_nq = "I:NDX"  # Nasdaq 100 Index como excelente proxy quantitativo de liquidez
        
        # Baixar dados
        candles_nq_5m = self.data_loader.load_data(symbol_nq, "5m", start_date, end_date)
        candles_nq_15m = self.data_loader.load_data(symbol_nq, "15m", start_date, end_date)
        candles_nq_1h = self.data_loader.load_data(symbol_nq, "1h", start_date, end_date)
        candles_nq_1d = self.data_loader.load_data(symbol_nq, "1d", start_date, end_date)
        
        if not candles_nq_5m.empty:
            strategy_nq = SilverBulletNQ()
            # Configuração de Custos Operacionais NQ ( ticks/ponto realistas )
            config_nq = BacktestConfig(
                initial_balance=10000.0,
                slippage_ticks=1,      # 0.25 pt
                spread_ticks=1,        # 0.25 pt
                commission_usd=2.0,    # $2 por trade
                tick_size=0.25,
                point_value=20.0       # NQ Mini $20/ponto
            )
            self.backtest_engine.config = config_nq
            
            # Backtest Principal
            result_nq = self.backtest_engine.run(
                strategy_nq, candles_nq_5m, candles_nq_15m, candles_nq_1h, candles_nq_1d
            )
            
            # Imprimir Métricas NQ
            m_nq = result_nq["metrics"]
            print("\n>>> RESULTADOS BACKTEST COMPLETO (NQ):")
            print(f"  Total de Trades: {m_nq['total_trades']}")
            print(f"  Taxa de Acerto:  {m_nq['win_rate']}%")
            print(f"  Profit Factor:   {m_nq['profit_factor']}")
            print(f"  Sharpe Ratio:    {m_nq['sharpe_ratio']}")
            print(f"  Max Drawdown:    {m_nq['max_drawdown_percent']}%")
            print(f"  PnL Total USD:   ${m_nq['total_pnl_usd']:.2f}")
            print(f"  Saldo Final:     ${m_nq['final_balance']:.2f}")
            
            # Walk Forward NQ
            wf_nq = self.walk_forward_engine.run(
                strategy_nq, candles_nq_5m, candles_nq_15m, candles_nq_1h, candles_nq_1d, n_splits=6
            )
        else:
            print("[ERRO] Falha ao carregar dados históricos para NQ. Pulando.")
            
        # ----------------------------------------------------
        # 2. SETUP #2: London Sweep + FVG (XAUUSD)
        # ----------------------------------------------------
        print("\n" + "-"*50)
        print("  VALIDANDO SETUP #2: LONDON OPEN SWEEP (XAUUSD)  ")
        print("-"*50)
        
        symbol_xau = "C:XAUUSD"
        
        candles_xau_5m = self.data_loader.load_data(symbol_xau, "5m", start_date, end_date)
        candles_xau_15m = self.data_loader.load_data(symbol_xau, "15m", start_date, end_date)
        candles_xau_1h = self.data_loader.load_data(symbol_xau, "1h", start_date, end_date)
        candles_xau_1d = self.data_loader.load_data(symbol_xau, "1d", start_date, end_date)
        
        if not candles_xau_5m.empty:
            strategy_xau = LondonSweepXAU()
            # Configuração de Custos Operacionais XAU (ticks/ponto realistas)
            config_xau = BacktestConfig(
                initial_balance=10000.0,
                slippage_ticks=2,      # $0.02
                spread_ticks=3,        # $0.03
                commission_usd=5.0,    # comissão MT5 clássica
                tick_size=0.01,
                point_value=100.0      # Ouro $100/ponto
            )
            self.backtest_engine.config = config_xau
            
            # Backtest Principal
            result_xau = self.backtest_engine.run(
                strategy_xau, candles_xau_5m, candles_xau_15m, candles_xau_1h, candles_xau_1d
            )
            
            # Imprimir Métricas XAU
            m_xau = result_xau["metrics"]
            print("\n>>> RESULTADOS BACKTEST COMPLETO (XAUUSD):")
            print(f"  Total de Trades: {m_xau['total_trades']}")
            print(f"  Taxa de Acerto:  {m_xau['win_rate']}%")
            print(f"  Profit Factor:   {m_xau['profit_factor']}")
            print(f"  Sharpe Ratio:    {m_xau['sharpe_ratio']}")
            print(f"  Max Drawdown:    {m_xau['max_drawdown_percent']}%")
            print(f"  PnL Total USD:   ${m_xau['total_pnl_usd']:.2f}")
            print(f"  Saldo Final:     ${m_xau['final_balance']:.2f}")
            
            # Walk Forward XAU
            wf_xau = self.walk_forward_engine.run(
                strategy_xau, candles_xau_5m, candles_xau_15m, candles_xau_1h, candles_xau_1d, n_splits=6
            )
        else:
            print("[ERRO] Falha ao carregar dados históricos para XAUUSD. Pulando.")
            
        print("\n" + "="*60)
        print("     VALIDAÇÃO QUANTITATIVA COMPLETA E FINALIZADA     ")
        print("="*60)

if __name__ == "__main__":
    runner = LiveRunner()
    runner.run_validation_pipeline()
