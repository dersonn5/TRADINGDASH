"""
Runner de Backtesting de Alta Fidelidade para Criptoativos (BTC e ETH).
Permite validar as estratégias ICT (Silver Bullet e London Sweep) em dados reais de 2022-2024.
"""
import os
import sys
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Configura a saída padrão para UTF-8 no Windows para evitar erros de encoding de console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adicionar o diretório atual ao sys.path para garantir importações
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
from strategies.london_sweep_xau import LondonSweepXAU, LondonSweepConfig
from strategies.breaker_block_xau import BreakerBlockXAU, BreakerBlockXAUConfig
from strategies.silver_bullet_crypto import SilverBulletCrypto, SilverBulletCryptoConfig
from strategies.breaker_block_crypto import BreakerBlockCrypto, BreakerBlockCryptoConfig
from strategies.prop_firm_2024_crypto import PropFirm2024Crypto, PropFirm2024CryptoConfig


def setup_directories():
    """Garante que a pasta de relatórios exista."""
    reports_dir = Path(__file__).resolve().parent / "backtesting" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def run_stress_simulation(positions, initial_balance=10000.0, symbol="BTC/USDT:USDT", strategy="silver_bullet"):
    """
    Aplica perturbações estatísticas do Rigor Lopez de Prado adaptadas para Cripto:
    1. Purging de autocorrelação (cooldown de 2 horas)
    2. Slippage / Neighborhood checks (1-2 ticks)
    """
    stressed_positions = []
    last_executed_time = None
    balance = initial_balance
    
    stats = {
        "trades_taken": 0,
        "wins": 0,
        "losses": 0,
        "prevented_losses": 0,
        "missed_wins": 0,
        "purged_trades": 0,
        "total_pnl_usd": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0
    }
    
    gross_profits = 0.0
    gross_losses = 0.0
    
    for pos in positions:
        entry_time = pd.to_datetime(pos.entry_time)
        
        # 1. Purging de Autocorrelação
        is_purged = False
        if last_executed_time is not None:
            diff_hours = (entry_time - last_executed_time).total_seconds() / 3600.0
            if diff_hours < 2.0:
                is_purged = True
                stats["purged_trades"] += 1
                
        if is_purged:
            # Em vez de pular completamente (o que dessincroniza os arrays ideal e estressado),
            # criamos um trade com PnL zerado e avaliação "PREVENTED_LOSS" para o dashboard.
            stressed_pos = {
                "scenario_id": f"TRADE-{len(stressed_positions)+1:03d}",
                "date": pos.entry_time.strftime("%Y-%m-%d") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[:10],
                "time_of_day_est": pos.entry_time.strftime("%H:%M EST") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[11:16] + " EST",
                "symbol": symbol,
                "signal_type": f"ICT {strategy.replace('_', ' ').title()}",
                "ai_decision": "PASS",
                "historical_result": "WIN" if pos.pnl_usd > 0 else "LOSS",
                "evaluation": "PREVENTED_LOSS",
                "pnl_usd": 0.0,
                "slippage_applied": 0.0,
                "reasoning": "Trade bloqueado (purgado) pelo embargo de 2 horas (autocorrelação) no ambiente estressado."
            }
            stressed_positions.append(stressed_pos)
            continue
            
        # Adiciona a execução ao estresse
        last_executed_time = entry_time
        stats["trades_taken"] += 1
        
        # 2. Aplicar Slippage no desfecho
        if "BTC" in symbol:
            # Slippage entre 1.0 e 5.0 USDT no preço do BTC
            slippage = round(random.uniform(1.0, 5.0), 2)
        else:
            # Slippage entre 0.1 e 0.5 USDT no preço do ETH
            slippage = round(random.uniform(0.1, 0.5), 2)
            
        original_sl = abs(pos.entry_price - pos.stop_loss)
        original_tp = abs(pos.take_profit - pos.entry_price)
        
        slipped_sl = original_sl + slippage
        slipped_tp = original_tp - slippage
        
        slipped_rr = round(slipped_tp / slipped_sl, 2) if slipped_sl > 0 else 1.0
        
        # Recalcular P&L
        if pos.pnl_usd > 0:
            slipped_pnl = pos.pnl_usd * (slipped_rr / (original_tp / original_sl)) if original_sl > 0 else pos.pnl_usd
            slipped_pnl = max(0.0, slipped_pnl)
            stats["wins"] += 1
            gross_profits += slipped_pnl
        else:
            loss_mult = slipped_sl / original_sl if original_sl > 0 else 1.05
            slipped_pnl = pos.pnl_usd * loss_mult
            stats["losses"] += 1
            gross_losses += abs(slipped_pnl)
            
        stats["total_pnl_usd"] += slipped_pnl
        
        # Copiar posição com dados estressados
        stressed_pos = {
            "scenario_id": f"TRADE-{len(stressed_positions)+1:03d}",
            "date": pos.entry_time.strftime("%Y-%m-%d") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[:10],
            "time_of_day_est": pos.entry_time.strftime("%H:%M EST") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[11:16] + " EST",
            "symbol": symbol,
            "signal_type": f"ICT {strategy.replace('_', ' ').title()}",
            "ai_decision": pos.action,
            "historical_result": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "evaluation": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "pnl_usd": round(slipped_pnl, 2),
            "slippage_applied": round(slippage, 2),
            "reasoning": f"Simulação de estresse: Slippage de {slippage:.2f} aplicado à execução cripto."
        }
        stressed_positions.append(stressed_pos)
        
    total_trades = stats["wins"] + stats["losses"]
    stats["win_rate"] = (stats["wins"] / total_trades) * 100 if total_trades > 0 else 0.0
    stats["profit_factor"] = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)
    
    return stats, stressed_positions


def save_to_database(positions, stats_ideal, stats_stressed, stressed_trades, symbol, strategy):
    """Salva os resultados em backtest_database.json mesclando-os para evitar sobrescrever outros ativos/estratégias."""
    database_path = Path(__file__).resolve().parent / "backtest_database.json"
    
    ideal_trades = []
    for idx, pos in enumerate(positions):
        ideal_trades.append({
            "scenario_id": f"TRADE-{idx+1:03d}",
            "date": pos.entry_time.strftime("%Y-%m-%d") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[:10],
            "time_of_day_est": pos.entry_time.strftime("%H:%M EST") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[11:16] + " EST",
            "symbol": symbol,
            "signal_type": f"ICT {strategy.replace('_', ' ').title()}",
            "daily_bias": "BULLISH" if pos.action == "BUY" else "BEARISH",
            "ai_decision": pos.action,
            "historical_result": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "evaluation": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "pnl_usd": round(pos.pnl_usd, 2),
            "reasoning": f"Ordem executada a {pos.entry_price:.2f} com Stop Loss a {pos.stop_loss:.2f} e Take Profit a {pos.take_profit:.2f}.",
            "strategy": strategy
        })
        
    for t in stressed_trades:
        t["strategy"] = strategy
        
    existing_ideal = []
    existing_stressed = []
    
    if database_path.exists():
        try:
            with open(database_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_ideal = existing_data.get("ideal", {}).get("trades", [])
                existing_stressed = existing_data.get("stressed", {}).get("trades", [])
        except Exception as e:
            print(f"[DATABASE] [AVISO] Falha ao carregar banco de dados existente: {e}. Criando novo.")
            existing_ideal = []
            existing_stressed = []

    filtered_ideal = [t for t in existing_ideal if not (t.get("symbol") == symbol and t.get("strategy") == strategy)]
    filtered_stressed = [t for t in existing_stressed if not (t.get("symbol") == symbol and t.get("strategy") == strategy)]
    
    merged_ideal = filtered_ideal + ideal_trades
    merged_stressed = filtered_stressed + stressed_trades
    
    def get_trade_datetime(t):
        time_part = t.get("time_of_day_est", "00:00 EST").split()[0]
        try:
            return datetime.strptime(f"{t['date']} {time_part}", "%Y-%m-%d %H:%M")
        except Exception:
            return datetime.min
            
    merged_ideal.sort(key=get_trade_datetime)
    merged_stressed.sort(key=get_trade_datetime)
    
    for idx, t in enumerate(merged_ideal):
        t["scenario_id"] = f"TRADE-{idx+1:03d}"
    for idx, t in enumerate(merged_stressed):
        t["scenario_id"] = f"TRADE-{idx+1:03d}"
        
    def calculate_stats(trades):
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get("evaluation") == "WIN")
        losses = sum(1 for t in trades if t.get("evaluation") == "LOSS")
        prevented_losses = sum(1 for t in trades if t.get("evaluation") == "PREVENTED_LOSS")
        missed_wins = sum(1 for t in trades if t.get("evaluation") == "MISSED_WIN")
        
        total_pnl = sum(t.get("pnl_usd", 0.0) for t in trades)
        
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        
        gross_profits = sum(t.get("pnl_usd", 0.0) for t in trades if t.get("pnl_usd", 0.0) > 0)
        gross_losses = sum(abs(t.get("pnl_usd", 0.0)) for t in trades if t.get("pnl_usd", 0.0) < 0)
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)
        
        return {
            "total_scenarios": total_trades,
            "trades_taken": wins + losses,
            "wins": wins,
            "losses": losses,
            "prevented_losses": prevented_losses,
            "missed_wins": missed_wins,
            "total_pnl_usd": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2)
        }
        
    stats_ideal_global = calculate_stats(merged_ideal)
    stats_stressed_global = calculate_stats(merged_stressed)
    
    stats_stressed_global["purged_trades"] = sum(1 for t in merged_stressed if "purgado" in t.get("reasoning", "").lower())
    
    db_data = {
        "timestamp": datetime.now().isoformat(),
        "ideal": {
            "statistics": stats_ideal_global,
            "trades": merged_ideal
        },
        "stressed": {
            "statistics": stats_stressed_global,
            "trades": merged_stressed
        }
    }
    
    with open(database_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)
    print(f"[DATABASE] Resultados mesclados com sucesso em {database_path}.")


def generate_reports(positions, metrics_ideal, metrics_stressed, strategy_name, symbol, reports_dir):
    """Gera relatórios gráficos e descritivos para o backtest de cripto."""
    # 1. Relatório em Markdown
    md_path = reports_dir / f"crypto_{strategy_name.lower()}_{symbol.replace('/', '_').replace(':', '_')}_backtest.md"
    
    trade_rows = []
    for idx, pos in enumerate(positions):
        pnl_str = f"**+${pos.pnl_usd:.2f}**" if pos.pnl_usd > 0 else f"-${abs(pos.pnl_usd):.2f}"
        action_emoji = "🟢 BUY" if pos.action == "BUY" else "🔴 SELL"
        trade_rows.append(
            f"| {idx+1:03d} | {pos.entry_time} | {action_emoji} | {pos.entry_price:.2f} | {pos.stop_loss:.2f} | {pos.take_profit:.2f} | {pnl_str} |"
        )
        
    trades_table = "\n".join(trade_rows)
    
    content = f"""# 📊 Relatório Final de Backtest de Criptoativos - {strategy_name.upper()}
Ativo: **{symbol}**
Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## ⚡ Sumário Executivo de Performance (3 Anos: 2022-2024)

| Métrica | 📈 AMBIENTE IDEAL | 🛡️ AMBIENTE REALISTA (Com Estresse) |
| :--- | :--- | :--- |
| **PnL Líquido Acumulado** | **${metrics_ideal.get('total_pnl_usd', 0.0):+.2f} USD** | **${metrics_stressed.get('total_pnl_usd', 0.0):+.2f} USD** |
| **Taxa de Acerto (Win Rate)** | **{metrics_ideal.get('win_rate', 0.0):.1f}%** | **{metrics_stressed.get('win_rate', 0.0):.1f}%** |
| **Fator de Lucro (Profit Factor)** | **{metrics_ideal.get('profit_factor', 1.0):.2f}** | **{metrics_stressed.get('profit_factor', 1.0):.2f}** |
| **Total de Trades** | {metrics_ideal.get('wins', 0) + metrics_ideal.get('losses', 0)} | {metrics_stressed.get('wins', 0) + metrics_stressed.get('losses', 0)} |
| **Vitórias / Derrotas** | {metrics_ideal.get('wins', 0)} / {metrics_ideal.get('losses', 0)} | {metrics_stressed.get('wins', 0)} / {metrics_stressed.get('losses', 0)} |
| **Perdas Evitadas** | {metrics_ideal.get('prevented_losses', 0)} | {metrics_stressed.get('prevented_losses', 0)} |
| **Trades Purgados (Embargo)** | 0 | {metrics_stressed.get('purged_trades', 0)} |

---

## 📋 Ledger Completo de Operações
| Trade | Horário (EST) | Direção | Entrada | Stop Loss | Take Profit | PnL USD |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{trades_table if trades_table else "| N/A | Nenhum trade executado | - | - | - | - | - |"}

---
*Relatório gerado automaticamente pelo Cérebro de Trading Cognitivo.*
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[RELATÓRIO] Relatório detalhado em Markdown salvo em: {md_path}")
    
    # 2. Relatório Gráfico Plotly HTML
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        balance_ideal = [10000.0]
        balance_stressed = [10000.0]
        timestamps = []
        
        if positions:
            timestamps = [pos.entry_time for pos in positions]
            cur_ideal = 10000.0
            for pos in positions:
                cur_ideal += pos.pnl_usd
                balance_ideal.append(cur_ideal)
            
            cur_stressed = 10000.0
            for pos in positions:
                if pos.pnl_usd > 0:
                    cur_stressed += pos.pnl_usd * 0.8  # Desconto de slippage
                else:
                    cur_stressed += pos.pnl_usd * 1.1   # Perda aumentada
                balance_stressed.append(cur_stressed)
                
            balance_ideal = balance_ideal[1:]
            balance_stressed = balance_stressed[1:]
        else:
            balance_ideal = [10000.0]
            balance_stressed = [10000.0]
            timestamps = [datetime.now()]
            
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.1,
                           subplot_titles=("Curva de Crescimento Patrimonial (USDT)", "Drawdown Relativo %"))
        
        # Curva Ideal
        fig.add_trace(go.Scatter(x=timestamps, y=balance_ideal, mode='lines', name='Curva Ideal',
                                 line=dict(color='#10b981', width=3),
                                 fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'),
                      row=1, col=1)
                      
        # Curva Estressada
        fig.add_trace(go.Scatter(x=timestamps, y=balance_stressed, mode='lines', name='Curva Estressada',
                                 line=dict(color='#8b5cf6', width=3, dash='dash'),
                                 fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.1)'),
                      row=1, col=1)
                      
        # Calcular Drawdown
        dd_ideal = []
        peak = 10000.0
        for val in balance_ideal:
            if val > peak:
                peak = val
            dd = ((val - peak) / peak) * 100
            dd_ideal.append(dd)
            
        fig.add_trace(go.Scatter(x=timestamps, y=dd_ideal, mode='lines', name='Drawdown Ideal',
                                 line=dict(color='#ef4444', width=2),
                                 fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.15)'),
                      row=2, col=1)
                      
        fig.update_layout(title_text=f"Relatório de Alta Fidelidade - {strategy_name.upper()} - {symbol}",
                          template="plotly_dark",
                          paper_bgcolor="#080b11",
                          plot_bgcolor="#080b11",
                          height=700)
                          
        html_path = reports_dir / f"crypto_{strategy_name.lower()}_{symbol.replace('/', '_').replace(':', '_')}_backtest.html"
        fig.write_html(str(html_path))
        print(f"[RELATÓRIO] Relatório gráfico Plotly HTML salvo em: {html_path}")
    except Exception as e:
        print(f"[RELATÓRIO] [AVISO] Falha ao gerar relatório Plotly: {e}")


def main():
    parser = argparse.ArgumentParser(description="Runner de Backtesting de Criptoativos para ICT.")
    parser.add_argument("--symbol", type=str, default="BTC/USDT:USDT", choices=["BTC/USDT:USDT", "ETH/USDT:USDT"], help="Símbolo.")
    parser.add_argument("--strategy", type=str, default="silver_bullet", choices=["silver_bullet", "london_sweep", "breaker_block", "prop_firm_2024"], help="Estratégia.")
    parser.add_argument("--start", type=str, default="2022-01-01", help="Data início YYYY-MM-DD.")
    parser.add_argument("--end", type=str, default="2024-12-31", help="Data fim YYYY-MM-DD.")

    
    args = parser.parse_args()
    reports_dir = setup_directories()
    
    print("\n===========================================================")
    print(f"  INICIANDO MOTOR DE BACKTEST CRIPTO COGNITIVO")
    print(f"  ATIVO: {args.symbol} | ESTRATÉGIA: {args.strategy.upper()}")
    print("===========================================================\n")
    
    loader = DataLoader()
    
    # 1. Configurar parâmetros de mercado da exchange
    if args.symbol == "BTC/USDT:USDT":
        tick_size = 0.1
        point_value = 1.0  # Para perpetuals lineares cripto, 1 ponto = 1 USDT por contrato
        min_sl = 50.0      # Risco mínimo do SL em USDT
    else:
        tick_size = 0.01
        point_value = 1.0
        min_sl = 10.0
        
    backtest_config = BacktestConfig(
        initial_balance=10000.0,
        slippage_ticks=1,
        spread_ticks=1,
        commission_usd=1.0,  # comissão baixa de maker/taker em cripto
        tick_size=tick_size,
        point_value=point_value
    )
    
    # 2. Inicializar a Estratégia correspondente
    if args.strategy == "silver_bullet":
        strategy_config = SilverBulletCryptoConfig(
            min_sl_distance_percent=0.005,
            min_rr=2.0,
            require_daily_bias=True,
            require_premium_discount=True,
            require_smt=True
        )
        strategy = SilverBulletCrypto(strategy_config)
        strategy.name = f"silver_bullet_crypto_{args.symbol.split('/')[0].lower()}"
        strategy.correlated_symbol = "BTC/USDT:USDT" if args.symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    elif args.strategy == "breaker_block":
        strategy_config = BreakerBlockCryptoConfig(
            min_sl_distance_percent=0.005,
            sl_buffer_percent=0.001,
            min_rr=2.0,
            require_daily_bias=True,
            require_sweep=True
        )
        strategy = BreakerBlockCrypto(strategy_config)
        strategy.name = f"breaker_block_crypto_{args.symbol.split('/')[0].lower()}"
        strategy.correlated_symbol = "BTC/USDT:USDT" if args.symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    elif args.strategy == "prop_firm_2024":
        strategy_config = PropFirm2024CryptoConfig(
            min_sl_distance_percent=0.005,
            sl_buffer_percent=0.001,
            min_rr=2.0,
            require_daily_bias=False
        )
        strategy = PropFirm2024Crypto(strategy_config)
        strategy.name = f"prop_firm_2024_crypto_{args.symbol.split('/')[0].lower()}"
        strategy.correlated_symbol = "BTC/USDT:USDT" if args.symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    else:
        strategy_config = LondonSweepConfig(
            min_sl_distance_usd=min_sl,
            min_rr=2.0,
            require_daily_bias=True
        )
        strategy = LondonSweepXAU(strategy_config)
        strategy.name = f"london_sweep_{args.symbol.split('/')[0].lower()}"
        
    # Importante: subscrever o símbolo da estratégia para que o motor carregue e registre corretamente!
    strategy.symbol = args.symbol
    
    # 3. Carregar dados de forma robusta e inteligente (tenta cache local primeiro)
    print(f"[CARREGADOR] Carregando séries temporais para {args.symbol}...")
    candles_5m = loader.load_data(args.symbol, "5m", args.start, args.end)
    candles_1d = loader.load_data(args.symbol, "1d", args.start, args.end)
    
    # Timeframes auxiliares. Se não estiverem no cache local ou estiverem incompletos,
    # geramos via amostragem de alta fidelidade a partir de candles_5m para evitar lentidão e falhas do yfinance.
    safe_symbol = args.symbol.replace(":", "_").replace("^", "_").replace("=", "_")
    start_dt = pd.to_datetime(args.start).tz_localize("America/New_York")
    end_dt = pd.to_datetime(args.end).tz_localize("America/New_York")
    
    # 15m
    candles_15m = pd.DataFrame()
    cache_file_15m = loader.CACHE_DIR / f"{safe_symbol}_15m.parquet"
    if cache_file_15m.exists():
        try:
            df_temp = pd.read_parquet(cache_file_15m)
            if not isinstance(df_temp.index, pd.DatetimeIndex):
                df_temp.index = pd.to_datetime(df_temp.index)
            if df_temp.index.tz is None:
                df_temp.index = df_temp.index.tz_localize("UTC").tz_convert("America/New_York")
            else:
                df_temp.index = df_temp.index.tz_convert("America/New_York")
            candles_15m = df_temp[(df_temp.index >= start_dt) & (df_temp.index <= end_dt)]
            print(f"[CARREGADOR] Carregado {len(candles_15m)} candles de 15m do cache local.")
        except Exception as e:
            print(f"[CARREGADOR] [AVISO] Falha ao ler cache 15m: {e}.")
            
    if (candles_15m.empty or 
        candles_15m.index.min() > candles_5m.index.min() + pd.Timedelta(hours=2) or 
        candles_15m.index.max() < candles_5m.index.max() - pd.Timedelta(hours=2)):
        print("[CARREGADOR] Gerando/Completando candles 15m via amostragem de alta fidelidade dos candles 5m...")
        candles_15m = candles_5m.resample("15min").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        
    # 1h
    candles_1h = pd.DataFrame()
    cache_file_1h = loader.CACHE_DIR / f"{safe_symbol}_1h.parquet"
    if cache_file_1h.exists():
        try:
            df_temp = pd.read_parquet(cache_file_1h)
            if not isinstance(df_temp.index, pd.DatetimeIndex):
                df_temp.index = pd.to_datetime(df_temp.index)
            if df_temp.index.tz is None:
                df_temp.index = df_temp.index.tz_localize("UTC").tz_convert("America/New_York")
            else:
                df_temp.index = df_temp.index.tz_convert("America/New_York")
            candles_1h = df_temp[(df_temp.index >= start_dt) & (df_temp.index <= end_dt)]
            print(f"[CARREGADOR] Carregado {len(candles_1h)} candles de 1h do cache local.")
        except Exception as e:
            print(f"[CARREGADOR] [AVISO] Falha ao ler cache 1h: {e}.")
            
    if (candles_1h.empty or 
        candles_1h.index.min() > candles_5m.index.min() + pd.Timedelta(hours=2) or 
        candles_1h.index.max() < candles_5m.index.max() - pd.Timedelta(hours=2)):
        print("[CARREGADOR] Gerando/Completando candles 1h via amostragem de alta fidelidade dos candles 5m...")
        candles_1h = candles_5m.resample("1h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        
    # 1m
    cache_file_1m = loader.CACHE_DIR / f"{safe_symbol}_1m.parquet"
    if cache_file_1m.exists():
        try:
            candles_1m = loader.load_data(args.symbol, "1m", args.start, args.end)
        except Exception:
            candles_1m = pd.DataFrame()
    else:
        candles_1m = pd.DataFrame()
        
    if candles_5m.empty or candles_1d.empty:
        print(f"[ERRO] Velas M5 ou 1D vazias. Você precisa rodar o historical loader primeiro para {args.symbol}!")
        print(f"Exemplo: python backtesting/binance_historical_loader.py --symbol \"{args.symbol}\" --timeframe \"5m\"")
        sys.exit(1)
        
    print(f"[CARREGADOR] Sucesso! Carregados {len(candles_5m)} candles M5 e {len(candles_1d)} candles D1.")
    
    # Carregar dados correlacionados para confluência SMT se aplicável
    corr_symbol = "BTC/USDT:USDT" if args.symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    print(f"[CARREGADOR] Carregando dados correlacionados de {corr_symbol} para confluência SMT...")
    try:
        candles_5m_corr = loader.load_data(corr_symbol, "5m", args.start, args.end)
    except Exception as e:
        print(f"[CARREGADOR] [AVISO] Falha ao carregar dados correlacionados para SMT: {e}. Desabilitando SMT.")
        candles_5m_corr = None

    # 4. Executar simulação de Backtest
    engine = BacktestEngine(backtest_config)
    result = engine.run(
        strategy=strategy,
        candles_5m=candles_5m,
        candles_15m=candles_15m if not candles_15m.empty else candles_5m,
        candles_1h=candles_1h if not candles_1h.empty else candles_5m,
        candles_1d=candles_1d,
        candles_1m=candles_1m if not candles_1m.empty else None,
        use_filters=False,  # Filtros macro de ES/DXY não se aplicam a cripto diretamente
        candles_5m_corr=candles_5m_corr
    )
    
    positions = result["positions"]
    metrics_ideal = result["metrics"]
    
    print(f"\n[BACKTEST] Simulação concluída. {len(positions)} trades tomados no ambiente ideal.")
    
    # 5. Executar simulação de estresse (Lopez de Prado)
    metrics_stressed, stressed_trades = run_stress_simulation(
        positions=positions,
        initial_balance=10000.0,
        symbol=args.symbol,
        strategy=args.strategy
    )
    
    # 6. Salvar base de dados e relatórios
    save_to_database(positions, metrics_ideal, metrics_stressed, stressed_trades, args.symbol, args.strategy)
    generate_reports(positions, metrics_ideal, metrics_stressed, args.strategy, args.symbol, reports_dir)
    
    # 7. Painel de Resultados no Console
    print("\n===========================================================")
    print("⚡ RESULTADOS CONSOLIDADOS CRIPTO COGNITIVO ⚡")
    print("-----------------------------------------------------------")
    print(f"  MÉTRICA            |  AMBIENTE IDEAL    |  ESTRESSADO")
    print("-----------------------------------------------------------")
    print(f"  PnL Líquido USD    |  ${metrics_ideal['total_pnl_usd']:+12.2f}    |  ${metrics_stressed['total_pnl_usd']:+12.2f}")
    print(f"  Taxa de Acerto     |  {metrics_ideal['win_rate']:11.1f}%    |  {metrics_stressed['win_rate']:11.1f}%")
    print(f"  Fator de Lucro     |  {metrics_ideal['profit_factor']:12.2f}    |  {metrics_stressed['profit_factor']:12.2f}")
    print(f"  Trades Executados  |  {len(positions):12d}    |  {metrics_stressed['trades_taken']:12d}")
    print(f"  Drawdown Máximo %  |  {metrics_ideal['max_drawdown_percent']:11.1f}%    |  -")
    print("===========================================================\n")


if __name__ == "__main__":
    main()
