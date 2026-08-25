import pandas as pd
import numpy as np
from typing import List, Dict
from strategies.base import Position

class PerformanceMetrics:
    @staticmethod
    def calculate(positions: List[Position], initial_balance: float) -> Dict:
        """
        Calcula as métricas estatísticas de performance do backtest com base nos trades executados.
        """
        if not positions:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown_percent": 0.0,
                "expectancy_usd": 0.0,
                "total_pnl_usd": 0.0,
                "final_balance": initial_balance,
                "consecutive_losses_streak": 0
            }

        df_trades = pd.DataFrame([{
            "pnl": p.pnl_usd,
            "entry_time": p.entry_time,
            "exit_time": p.exit_time,
            "status": p.status,
            "result": "WIN" if p.pnl_usd > 0 else "LOSS"
        } for p in positions])

        # Métricas Básicas
        total_trades = len(df_trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]
        
        total_pnl = df_trades['pnl'].sum()
        final_balance = initial_balance + total_pnl
        
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0.0
        
        gross_profit = wins['pnl'].sum()
        gross_loss = abs(losses['pnl'].sum())
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
        
        # Expectativa Matemática (Expectancy)
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0.0
        expectancy = (win_rate / 100.0 * avg_win) - ((1.0 - win_rate / 100.0) * avg_loss)

        # Cálculo da curva de capital e Drawdown
        balance_curve = [initial_balance]
        current_balance = initial_balance
        for pnl in df_trades['pnl']:
            current_balance += pnl
            balance_curve.append(current_balance)
            
        balance_series = pd.Series(balance_curve)
        peak = balance_series.cummax()
        drawdowns = (balance_series - peak) / peak * 100
        max_drawdown = abs(drawdowns.min())

        # Sharpe & Sortino (assumindo retornos por trade)
        trade_returns = df_trades['pnl'] / initial_balance
        avg_return = trade_returns.mean()
        std_return = trade_returns.std()
        
        sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0
        
        # Downside Deviation para o Sortino
        downside_returns = trade_returns[trade_returns < 0]
        downside_std = downside_returns.std()
        sortino = (avg_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0

        # Streak de perdas consecutivas
        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in df_trades['pnl']:
            if pnl <= 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "max_drawdown_percent": round(max_drawdown, 2),
            "expectancy_usd": round(expectancy, 2),
            "total_pnl_usd": round(total_pnl, 2),
            "final_balance": round(final_balance, 2),
            "consecutive_losses_streak": max_consecutive_losses
        }
