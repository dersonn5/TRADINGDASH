from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict
from strategies.base import Strategy
from backtesting.engine import BacktestEngine, BacktestConfig

class WalkForwardEngine:
    """
    Motor de Validação Walk-Forward.
    Divide os dados em janelas de teste Out-Of-Sample consecutivas com embargo temporal
    para garantir validação livre de overfitting e autocorrelação.
    """
    def __init__(self, engine: BacktestEngine = None):
        self.engine = engine or BacktestEngine()

    def run(
        self,
        strategy: Strategy,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
        n_splits: int = 6,
        margin_days: int = 2, # Note: using argument in fallback
        embargo_days: int = 2,
        use_filters: bool = True,
        vix_data: pd.DataFrame = None,
        es_data: pd.DataFrame = None,
        dxy_data: pd.DataFrame = None,
        news_events: List[Dict] = None
    ) -> Dict:
        print(f"\n[WALK-FORWARD] Iniciando validação cruzada walk-forward ({n_splits} splits)...")
        
        # 1. Garantir fusos horários EST
        df_5m = strategy._convert_to_est(candles_5m)
        df_15m = strategy._convert_to_est(candles_15m)
        df_1h = strategy._convert_to_est(candles_1h)
        df_1d = strategy._convert_to_est(candles_1d)
        df_1m = strategy._convert_to_est(candles_1m) if (candles_1m is not None and not candles_1m.empty) else None
        
        total_days = (df_5m.index[-1] - df_5m.index[0]).days
        if total_days < 90:
            print("[AVISO] Período total é inferior a 90 dias. Reduzindo splits para 3.")
            n_splits = 3
            
        # Calcular os limites temporais de cada split de teste out-of-sample
        start_time = df_5m.index[0]
        end_time = df_5m.index[-1]
        time_span = end_time - start_time
        
        split_duration = time_span / n_splits
        splits_results = []
        
        # Orquestrar janelas de teste Walk-Forward
        for split_idx in range(n_splits):
            test_start = start_time + (split_idx * split_duration)
            test_end = test_start + split_duration
            
            # Aplicar Embargo temporal se não for o primeiro split para limpar resquícios
            if split_idx > 0:
                test_start += timedelta(days=embargo_days)
                
            print(f"  -> Executando split {split_idx+1}/{n_splits} | Período: {test_start.strftime('%Y-%m-%d')} a {test_end.strftime('%Y-%m-%d')}...")
            
            # Filtrar DataFrames
            split_5m = df_5m[(df_5m.index >= test_start) & (df_5m.index <= test_end)]
            split_15m = df_15m[(df_15m.index >= test_start) & (df_15m.index <= test_end)]
            split_1h = df_1h[(df_1h.index >= test_start) & (df_1h.index <= test_end)]
            split_1d = df_1d[(df_1d.index >= test_start) & (df_1d.index <= test_end)]
            split_1m = df_1m[(df_1m.index >= test_start) & (df_1m.index <= test_end)] if df_1m is not None else None
            
            # Slicing macro filters
            split_vix = vix_data[(vix_data.index >= test_start) & (vix_data.index <= test_end)] if vix_data is not None else None
            split_es = es_data[(es_data.index >= test_start) & (es_data.index <= test_end)] if es_data is not None else None
            split_dxy = dxy_data[(dxy_data.index >= test_start) & (dxy_data.index <= test_end)] if dxy_data is not None else None
            
            # Slicing news
            split_news = None
            if news_events:
                split_news = []
                for n in news_events:
                    ts = pd.to_datetime(n.get("timestamp"))
                    if ts.tzinfo is None:
                        ts = ts.tz_localize("America/New_York")
                    else:
                        ts = ts.tz_convert("America/New_York")
                    if test_start <= ts <= test_end:
                        split_news.append(n)
            
            if len(split_5m) < 100:
                print(f"     [SPLIT {split_idx+1} VAZIO OR INSUFICIENTE] Ignorando.")
                continue
                
            # Executar backtest
            result = self.engine.run(
                strategy, split_5m, split_15m, split_1h, split_1d, split_1m,
                use_filters=use_filters, vix_data=split_vix, es_data=split_es, dxy_data=split_dxy, news_events=split_news
            )
            splits_results.append({
                "split": split_idx + 1,
                "start": test_start.strftime("%Y-%m-%d"),
                "end": test_end.strftime("%Y-%m-%d"),
                "metrics": result["metrics"],
                "positions_count": len(result["positions"])
            })
            
        # Compilar estatísticas agregadas
        total_pnl = sum(r["metrics"]["total_pnl_usd"] for r in splits_results)
        avg_win_rate = np.mean([r["metrics"]["win_rate"] for r in splits_results]) if splits_results else 0.0
        avg_sharpe = np.mean([r["metrics"]["sharpe_ratio"] for r in splits_results]) if splits_results else 0.0
        
        print(f"\n[WALK-FORWARD] Validação concluída. P&L Agregado: ${total_pnl:.2f} | Sharpe Médio: {avg_sharpe:.2f}")
        
        return {
            "splits": splits_results,
            "aggregate": {
                "total_pnl_usd": round(total_pnl, 2),
                "avg_win_rate": round(avg_win_rate, 2),
                "avg_sharpe": round(avg_sharpe, 2)
            }
        }
