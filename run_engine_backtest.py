import os
import sys
import argparse
import json
import random
from datetime import datetime, timedelta
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
from backtesting.walk_forward import WalkForwardEngine
from backtesting.metrics import PerformanceMetrics
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
from strategies.london_sweep_xau import LondonSweepXAU, LondonSweepConfig
from strategies.silver_bullet_xau import SilverBulletXAU, SilverBulletXAUConfig
from strategies.london_sweep_nq import LondonSweepNQ, LondonSweepNQConfig
from strategies.orb_breakout import ORBBreakout, ORBConfig
from strategies.session_configs import (
    make_sb_nq_am, make_sb_nq_lunch, make_sb_nq_close,
    make_sb_xau_am, make_sb_xau_lunch, make_sb_xau_close
)

def setup_directories():
    """Garante que a pasta de relatórios exista."""
    reports_dir = Path(__file__).resolve().parent / "backtesting" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir

from pathlib import Path

def load_macro_filters(start_date, end_date):
    """Carrega dados macro de filtro (VIX, SPY, UUP) de forma resiliente."""
    loader = DataLoader()
    
    print("[FILTROS] Carregando dados para filtros macro (SPY, UUP, ^VIX)...")
    
    # 1. Carregar SPY (Index S&P500 proxy)
    try:
        spy_data = loader.load_data("SPY", "5m", start_date, end_date)
        if spy_data.empty:
            print("[FILTROS] [AVISO] Dados de SPY vazios. Filtro de SPY será desabilitado.")
            spy_data = None
    except Exception as e:
        print(f"[FILTROS] [AVISO] Falha ao carregar SPY: {e}. Filtro de SPY desabilitado.")
        spy_data = None
        
    # 2. Carregar UUP (Dollar index ETF)
    try:
        uup_data = loader.load_data("UUP", "5m", start_date, end_date)
        if uup_data.empty:
            print("[FILTROS] [AVISO] Dados de UUP vazios. Filtro de DXY será desabilitado.")
            uup_data = None
    except Exception as e:
        print(f"[FILTROS] [AVISO] Falha ao carregar UUP: {e}. Filtro de DXY desabilitado.")
        uup_data = None
        
    # 3. Carregar VIX (1d timeframe)
    try:
        vix_data = loader.load_data("^VIX", "1d", start_date, end_date)
        if vix_data.empty:
            print("[FILTROS] [AVISO] Dados de VIX vazios. Filtro de VIX será desabilitado.")
            vix_data = None
    except Exception as e:
        print(f"[FILTROS] [AVISO] Falha ao carregar VIX: {e}. Filtro de VIX desabilitado.")
        vix_data = None
        
    return spy_data, uup_data, vix_data

def generate_economic_news_events(start_date, end_date):
    """
    Simula um calendário econômico realista para o período do backtest.
    Gera notícias de alto impacto em horários canônicos (08:30 EST e 14:00 EST).
    """
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    news_events = []
    current = start_dt
    
    # Geramos notícias todas as semanas
    while current <= end_dt:
        # Apenas dias úteis (segunda a sexta)
        if current.weekday() < 5:
            # 1. CPI/NFP nas primeiras sextas ou quintas às 08:30 EST
            if current.weekday() == 4:  # Sexta-feira
                news_events.append({
                    "timestamp": current.replace(hour=8, minute=30).strftime("%Y-%m-%d %H:%M:%S"),
                    "impact": "HIGH",
                    "headline": "Non-Farm Payrolls (NFP) Employment Report"
                })
            elif current.weekday() == 3:  # Quinta-feira
                news_events.append({
                    "timestamp": current.replace(hour=8, minute=30).strftime("%Y-%m-%d %H:%M:%S"),
                    "impact": "HIGH",
                    "headline": "CPI Inflation Report / Initial Jobless Claims"
                })
            # 2. FOMC Decision em quartas-feiras alternadas às 14:00 EST
            elif current.weekday() == 2 and current.day % 2 == 0:  # Quarta-feira
                news_events.append({
                    "timestamp": current.replace(hour=14, minute=0).strftime("%Y-%m-%d %H:%M:%S"),
                    "impact": "HIGH",
                    "headline": "FOMC Interest Rate Decision & Statement"
                })
        current += timedelta(days=1)
        
    print(f"[NEWS] Geradas {len(news_events)} janelas de notícias econômicas de alto impacto simuladas.")
    return news_events

def run_stress_simulation(positions, initial_balance=10000.0, symbol="NQ"):
    """
    Aplica perturbações estatísticas do Rigor Lopez de Prado:
    1. Purging de autocorrelação (cooldown de 2 horas)
    2. Slippage / Neighborhood checks (2-5 ticks para Ouro, 6-12 ticks para NQ)
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
            continue
            
        # Adiciona a execução ao estresse
        last_executed_time = entry_time
        stats["trades_taken"] += 1
        
        # 2. Aplicar Slippage no desfecho
        if symbol == "XAUUSD":
            # Slippage entre 0.20 e 0.50 USD
            slippage = round(random.uniform(0.20, 0.50), 2)
            original_sl = abs(pos.entry_price - pos.stop_loss)
            original_tp = abs(pos.take_profit - pos.entry_price)
            
            slipped_sl = original_sl + slippage
            slipped_tp = original_tp - slippage
        else:
            # Slippage entre 1.50 e 3.00 pontos (CME NQ ticks)
            slippage = round(random.uniform(1.50, 3.00), 2)
            original_sl = abs(pos.entry_price - pos.stop_loss)
            original_tp = abs(pos.take_profit - pos.entry_price)
            
            slipped_sl = original_sl + slippage
            slipped_tp = original_tp - slippage
            
        slipped_rr = round(slipped_tp / slipped_sl, 2) if slipped_sl > 0 else 1.0
        
        # Recalcular P&L
        if pos.pnl_usd > 0:
            # Venceu, mas com ganho reduzido por slippage
            slipped_pnl = pos.pnl_usd * (slipped_rr / (original_tp / original_sl)) if original_sl > 0 else pos.pnl_usd
            slipped_pnl = max(0.0, slipped_pnl)
            stats["wins"] += 1
            gross_profits += slipped_pnl
        else:
            # Perdeu, e com perda aumentada por slippage
            loss_mult = slipped_sl / original_sl if original_sl > 0 else 1.1
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
            "signal_type": "High Fidelity Candle Signal",
            "ai_decision": pos.action,
            "historical_result": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "evaluation": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "pnl_usd": round(slipped_pnl, 2),
            "slippage_applied": round(slippage, 2),
            "reasoning": f"Simulação de estresse: Slippage de {slippage:.2f} aplicado à execução operacional."
        }
        stressed_positions.append(stressed_pos)
        
    total_trades = stats["wins"] + stats["losses"]
    stats["win_rate"] = stats["wins"] / total_trades if total_trades > 0 else 0.0
    stats["profit_factor"] = gross_profits / gross_losses if gross_losses > 0 else (gross_profits if gross_profits > 0 else 1.0)
    
    return stats, stressed_positions

def save_to_database(positions, stats_ideal, stats_stressed, stressed_trades, symbol):
    """Salva os resultados em backtest_database.json para que o dashboard Fast API os leia."""
    database_path = Path(__file__).resolve().parent / "backtest_database.json"
    
    ideal_trades = []
    for idx, pos in enumerate(positions):
        ideal_trades.append({
            "scenario_id": f"TRADE-{idx+1:03d}",
            "date": pos.entry_time.strftime("%Y-%m-%d") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[:10],
            "time_of_day_est": pos.entry_time.strftime("%H:%M EST") if isinstance(pos.entry_time, datetime) else str(pos.entry_time)[11:16] + " EST",
            "symbol": symbol,
            "signal_type": "High Fidelity Candle Signal",
            "daily_bias": "BULLISH" if pos.action == "BUY" else "BEARISH",
            "ai_decision": pos.action,
            "historical_result": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "evaluation": "WIN" if pos.pnl_usd > 0 else "LOSS",
            "pnl_usd": round(pos.pnl_usd, 2),
            "reasoning": f"Ordem executada a {pos.entry_price:.2f} com Stop Loss a {pos.stop_loss:.2f} e Take Profit a {pos.take_profit:.2f}."
        })
        
    db_data = {
        "timestamp": datetime.now().isoformat(),
        "ideal": {
            "statistics": {
                "total_scenarios": len(ideal_trades),
                "trades_taken": len(ideal_trades),
                "wins": stats_ideal.get("wins", 0),
                "losses": stats_ideal.get("losses", 0),
                "prevented_losses": stats_ideal.get("prevented_losses", 0),
                "missed_wins": stats_ideal.get("missed_wins", 0),
                "total_pnl_usd": round(stats_ideal.get("total_pnl_usd", 0.0), 2),
                "win_rate": round(stats_ideal.get("win_rate", 0.0), 2),
                "profit_factor": round(stats_ideal.get("profit_factor", 1.0), 2)
            },
            "trades": ideal_trades
        },
        "stressed": {
            "statistics": {
                "total_scenarios": len(stressed_trades),
                "trades_taken": len(stressed_trades),
                "wins": stats_stressed.get("wins", 0),
                "losses": stats_stressed.get("losses", 0),
                "prevented_losses": stats_stressed.get("prevented_losses", 0),
                "missed_wins": stats_stressed.get("missed_wins", 0),
                "purged_trades": stats_stressed.get("purged_trades", 0),
                "total_pnl_usd": round(stats_stressed.get("total_pnl_usd", 0.0), 2),
                "win_rate": round(stats_stressed.get("win_rate", 0.0), 2),
                "profit_factor": round(stats_stressed.get("profit_factor", 1.0), 2)
            },
            "trades": stressed_trades
        }
    }
    
    with open(database_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)
    print(f"[DATABASE] Resultados salvos com sucesso em {database_path}.")

def generate_plotly_report(positions, stats_ideal, stats_stressed, strategy_name, reports_dir):
    """Gera o relatório gráfico Plotly HTML."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        balance_ideal = [10000.0]
        balance_stressed = [10000.0]
        timestamps = [datetime.now() - timedelta(days=365)] # Fallback
        
        if positions:
            timestamps = [pos.entry_time for pos in positions]
            cur_ideal = 10000.0
            for pos in positions:
                cur_ideal += pos.pnl_usd
                balance_ideal.append(cur_ideal)
            
            cur_stressed = 10000.0
            # Simular curva de estresse
            for pos in positions:
                # Simplificação da curva estressada cronologicamente
                if pos.pnl_usd > 0:
                    cur_stressed += pos.pnl_usd * 0.8
                else:
                    cur_stressed += pos.pnl_usd * 1.15
                balance_stressed.append(cur_stressed)
                
            balance_ideal = balance_ideal[1:]
            balance_stressed = balance_stressed[1:]
        else:
            balance_ideal = [10000.0]
            balance_stressed = [10000.0]
            timestamps = [datetime.now()]
            
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.1,
                           subplot_titles=("Curva de Crescimento Patrimonial", "Drawdown Relativo %"))
        
        # Curva Ideal
        fig.add_trace(go.Scatter(x=timestamps, y=balance_ideal, mode='lines', name='Curva Ideal',
                                 line=dict(color='#06b6d4', width=3),
                                 fill='tozeroy', fillcolor='rgba(6, 182, 212, 0.1)'),
                      row=1, col=1)
                      
        # Curva Estressada
        fig.add_trace(go.Scatter(x=timestamps, y=balance_stressed, mode='lines', name='Curva Estressada',
                                 line=dict(color='#a855f7', width=3, dash='dash'),
                                 fill='tozeroy', fillcolor='rgba(168, 85, 247, 0.1)'),
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
                      
        fig.update_layout(title_text=f"Relatório de Alta Fidelidade - {strategy_name.upper()}",
                          template="plotly_dark",
                          paper_bgcolor="#080b11",
                          plot_bgcolor="#080b11",
                          height=700)
                          
        html_path = reports_dir / f"{strategy_name}_backtest.html"
        fig.write_html(str(html_path))
        print(f"[RELATÓRIO] Relatório gráfico Plotly HTML salvo em: {html_path}")
    except Exception as e:
        print(f"[RELATÓRIO] [AVISO] Falha ao gerar relatório Plotly: {e}")

def generate_markdown_report(positions, stats_ideal, stats_stressed, strategy_name, reports_dir):
    """Gera o relatório descritivo final em Markdown sob backtesting/reports/."""
    md_path = reports_dir / f"{strategy_name}_backtest.md"
    
    trade_rows = []
    for idx, pos in enumerate(positions):
        pnl_str = f"**+${pos.pnl_usd:.2f}**" if pos.pnl_usd > 0 else f"-${abs(pos.pnl_usd):.2f}"
        action_emoji = "🟢 BUY" if pos.action == "BUY" else "🔴 SELL"
        trade_rows.append(
            f"| {idx+1:03d} | {pos.entry_time} | {action_emoji} | {pos.entry_price:.2f} | {pos.stop_loss:.2f} | {pos.take_profit:.2f} | {pnl_str} |"
        )
        
    trades_table = "\n".join(trade_rows)
    
    content = f"""# 📊 Relatório Final de Backtest de Alta Fidelidade - {strategy_name.upper()}
Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## ⚡ Sumário Executivo de Performance

| Métrica | 📈 AMBIENTE IDEAL | 🛡️ AMBIENTE REALISTA (Com Estresse) |
| :--- | :--- | :--- |
| **PnL Líquido Acumulado** | **${stats_ideal.get('total_pnl_usd', 0.0):+.2f} USD** | **${stats_stressed.get('total_pnl_usd', 0.0):+.2f} USD** |
| **Taxa de Acerto (Win Rate)** | **{stats_ideal.get('win_rate', 0.0) * 100:.1f}%** | **{stats_stressed.get('win_rate', 0.0) * 100:.1f}%** |
| **Fator de Lucro (Profit Factor)** | **{stats_ideal.get('profit_factor', 1.0):.2f}** | **{stats_stressed.get('profit_factor', 1.0):.2f}** |
| **Total de Trades** | {stats_ideal.get('wins', 0) + stats_ideal.get('losses', 0)} | {stats_stressed.get('wins', 0) + stats_stressed.get('losses', 0)} |
| **Vitórias / Derrotas** | {stats_ideal.get('wins', 0)} / {stats_ideal.get('losses', 0)} | {stats_stressed.get('wins', 0)} / {stats_stressed.get('losses', 0)} |
| **Perdas Evitadas** | {stats_ideal.get('prevented_losses', 0)} | {stats_stressed.get('prevented_losses', 0)} |
| **Trades Purgados (Embargo)** | 0 | {stats_stressed.get('purged_trades', 0)} |

---

## 🔬 Metodologia de Estresse (Rigor Lopez de Prado)
1. **Neighborhood Slippage**: Perturbação aleatória e desfavorável de 2 a 5 ticks no preço de execução física.
2. **Purging de Cooldown**: Bloqueio de sinais redundantes que ocorrem num intervalo inferior a **2 horas** após uma execução bem-sucedida ou stop-out, limpando a autocorrelação serial dos dados.

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

def run_standard_backtest(args, reports_dir):
    """Executa o backtest candle-by-candle regular com ou sem filtros."""
    print("\n===========================================================")
    print(f"  INICIANDO BACKTEST COGNITIVO HIGH-FIDELITY: {args.strategy.upper()}")
    print("===========================================================\n")
    
    loader = DataLoader()
    
    # 1. Mapear e carregar dados
    if args.strategy == "silver_bullet_nq" or args.strategy == "silver_bullet_nq_am":
        symbol = "I:NDX"  # Nasdaq continuous proxy
        strategy = make_sb_nq_am()
    elif args.strategy == "silver_bullet_nq_lunch":
        symbol = "I:NDX"
        strategy = make_sb_nq_lunch()
    elif args.strategy == "silver_bullet_nq_close":
        symbol = "I:NDX"
        strategy = make_sb_nq_close()
    elif args.strategy == "silver_bullet_xau" or args.strategy == "silver_bullet_xau_am":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_am()
    elif args.strategy == "silver_bullet_xau_lunch":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_lunch()
    elif args.strategy == "silver_bullet_xau_close":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_close()
    elif args.strategy == "london_sweep_nq":
        symbol = "I:NDX"
        strategy = LondonSweepNQ()
    elif args.strategy == "orb_breakout":
        symbol = "I:NDX"
        strategy = ORBBreakout()
    elif args.strategy == "london_sweep_xau":
        symbol = "C:XAUUSD"
        strategy = LondonSweepXAU()
    else:
        raise ValueError(f"Estratégia desconhecida: {args.strategy}")
        
    print(f"[CARREGADOR] Carregando séries temporais M1, M5, M15, H1, D1 para {symbol}...")
    try:
        candles_1m = loader.load_data(symbol, "1m", args.start, args.end)
    except Exception as e:
        print(f"[CARREGADOR] [AVISO] Opcional M1 não disponível ({e}). Usando fallback M5 CE.")
        candles_1m = pd.DataFrame()
    candles_5m = loader.load_data(symbol, "5m", args.start, args.end)
    candles_15m = loader.load_data(symbol, "15m", args.start, args.end)
    candles_1h = loader.load_data(symbol, "1h", args.start, args.end)
    candles_1d = loader.load_data(symbol, "1d", args.start, args.end)
    
    if candles_5m.empty:
        print("[ERRO] Não foi possível carregar dados de entrada para o backtest.")
        return
        
    print(f"[CARREGADOR] Sucesso! {len(candles_5m)} velas operacionais M5 carregadas.")
    
    # 2. Carregar dados de filtros macro e notícias se filtros ativos
    use_filters = args.filters == "all"
    spy_data, uup_data, vix_data = None, None, None
    news_events = None
    
    if use_filters:
        spy_data, uup_data, vix_data = load_macro_filters(args.start, args.end)
        news_events = generate_economic_news_events(args.start, args.end)
        
    # 3. Executar o Motor de Backtesting
    engine = BacktestEngine(BacktestConfig(initial_balance=10000.0))
    result = engine.run(
        strategy=strategy,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        candles_1h=candles_1h,
        candles_1d=candles_1d,
        candles_1m=candles_1m,
        use_filters=use_filters,
        vix_data=vix_data,
        es_data=spy_data,
        dxy_data=uup_data,
        news_events=news_events
    )
    
    positions = result["positions"]
    metrics_ideal = result["metrics"]
    
    print(f"\n[BACKTEST] Simulação ideal concluída. {len(positions)} trades tomados.")
    
    # 4. Raciocinar estresse realista (Lopez de Prado)
    metrics_stressed, stressed_trades = run_stress_simulation(
        positions=positions, 
        initial_balance=10000.0, 
        symbol=strategy.symbol
    )
    
    # 5. Salvar base de dados e relatórios
    save_to_database(positions, metrics_ideal, metrics_stressed, stressed_trades, strategy.symbol)
    generate_plotly_report(positions, metrics_ideal, metrics_stressed, args.strategy, reports_dir)
    generate_markdown_report(positions, metrics_ideal, metrics_stressed, args.strategy, reports_dir)
    
    # 6. Painel de Output no console
    print("\n===========================================================")
    print("⚡ RESULTADOS CONSOLIDADOS CONTRAPARTIDA COGNITIVA ⚡")
    print("-----------------------------------------------------------")
    print(f"  MÉTRICA            |  AMBIENTE IDEAL    |  ESTRESSADO")
    print("-----------------------------------------------------------")
    print(f"  PnL Líquido USD    |  ${metrics_ideal['total_pnl_usd']:+12.2f}    |  ${metrics_stressed['total_pnl_usd']:+12.2f}")
    print(f"  Taxa de Acerto     |  {metrics_ideal['win_rate']*100:11.1f}%    |  {metrics_stressed['win_rate']*100:11.1f}%")
    print(f"  Fator de Lucro     |  {metrics_ideal['profit_factor']:12.2f}    |  {metrics_stressed['profit_factor']:12.2f}")
    print(f"  Trades Executados  |  {len(positions):12d}    |  {metrics_stressed['trades_taken']:12d}")
    print(f"  Drawdown Máximo %  |  {metrics_ideal['max_drawdown_percent']:11.1f}%    |  -")
    print("===========================================================\n")

def run_walk_forward_validation(args, reports_dir):
    """Executa a validação cruzada walk-forward."""
    print("\n===========================================================")
    print(f"  INICIANDO VALIDAÇÃO WALK-FORWARD: {args.strategy.upper()}")
    print(f"  SPLITS: {args.splits} | EMBARGO TEMPORAL: 2 dias")
    print("===========================================================\n")
    
    loader = DataLoader()
    
    if args.strategy == "silver_bullet_nq" or args.strategy == "silver_bullet_nq_am":
        symbol = "I:NDX"
        strategy = make_sb_nq_am()
    elif args.strategy == "silver_bullet_nq_lunch":
        symbol = "I:NDX"
        strategy = make_sb_nq_lunch()
    elif args.strategy == "silver_bullet_nq_close":
        symbol = "I:NDX"
        strategy = make_sb_nq_close()
    elif args.strategy == "silver_bullet_xau" or args.strategy == "silver_bullet_xau_am":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_am()
    elif args.strategy == "silver_bullet_xau_lunch":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_lunch()
    elif args.strategy == "silver_bullet_xau_close":
        symbol = "C:XAUUSD"
        strategy = make_sb_xau_close()
    elif args.strategy == "london_sweep_nq":
        symbol = "I:NDX"
        strategy = LondonSweepNQ()
    elif args.strategy == "orb_breakout":
        symbol = "I:NDX"
        strategy = ORBBreakout()
    elif args.strategy == "london_sweep_xau":
        symbol = "C:XAUUSD"
        strategy = LondonSweepXAU()
    else:
        raise ValueError(f"Estratégia desconhecida: {args.strategy}")
        
    try:
        candles_1m = loader.load_data(symbol, "1m", args.start, args.end)
    except Exception as e:
        print(f"[CARREGADOR] [AVISO] Opcional M1 não disponível ({e}). Usando fallback M5 CE.")
        candles_1m = pd.DataFrame()
    candles_5m = loader.load_data(symbol, "5m", args.start, args.end)
    candles_15m = loader.load_data(symbol, "15m", args.start, args.end)
    candles_1h = loader.load_data(symbol, "1h", args.start, args.end)
    candles_1d = loader.load_data(symbol, "1d", args.start, args.end)
    
    if candles_5m.empty:
        print("[ERRO] Dados não encontrados para a validação walk-forward.")
        return
        
    use_filters = args.filters == "all"
    spy_data, uup_data, vix_data = None, None, None
    news_events = None
    
    if use_filters:
        spy_data, uup_data, vix_data = load_macro_filters(args.start, args.end)
        news_events = generate_economic_news_events(args.start, args.end)
        
    # Inicializar Walk Forward Engine
    wf_engine = WalkForwardEngine()
    result = wf_engine.run(
        strategy=strategy,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        candles_1h=candles_1h,
        candles_1d=candles_1d,
        candles_1m=candles_1m,
        n_splits=args.splits,
        embargo_days=2,
        use_filters=use_filters,
        vix_data=vix_data,
        es_data=spy_data,
        dxy_data=uup_data,
        news_events=news_events
    )
    
    # Gerar Relatório HTML de Walk-Forward
    html_path = reports_dir / f"{args.strategy}_walkforward.html"
    
    splits_rows = []
    for r in result["splits"]:
        splits_rows.append(
            f"<tr><td>Split {r['split']}</td><td>{r['start']} a {r['end']}</td><td>{r['positions_count']}</td>"
            f"<td>${r['metrics']['total_pnl_usd']:+.2f}</td><td>{r['metrics']['win_rate']*100:.1f}%</td>"
            f"<td>{r['metrics']['profit_factor']:.2f}</td></tr>"
        )
    splits_table_content = "\n".join(splits_rows)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Validação Walk-Forward - {args.strategy.upper()}</title>
        <style>
            body {{ font-family: sans-serif; background-color: #080b11; color: #f3f4f6; margin: 40px; }}
            h1 {{ color: #a855f7; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }}
            th {{ background-color: rgba(168, 85, 247, 0.2); color: #a855f7; }}
            .card {{ background: rgba(17, 24, 39, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>📊 Relatório de Validação Cruzada Walk-Forward</h1>
        <div class="card">
            <h2>Estratégia: {args.strategy.upper()}</h2>
            <p><strong>P&L Acumulado Agregado Out-of-Sample:</strong> ${result['aggregate']['total_pnl_usd']:+.2f} USD</p>
            <p><strong>Win Rate Médio:</strong> {result['aggregate']['avg_win_rate']*100:.1f}%</p>
            <p><strong>Sharpe Ratio Médio:</strong> {result['aggregate']['avg_sharpe']:.2f}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Split</th>
                    <th>Período de Teste</th>
                    <th>Trades</th>
                    <th>PnL USD</th>
                    <th>Win Rate</th>
                    <th>Fator de Lucro</th>
                </tr>
            </thead>
            <tbody>
                {splits_table_content}
            </tbody>
        </table>
    </body>
    </html>
    """
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"\n[WALK-FORWARD] Relatório HTML de Walk-Forward salvo em: {html_path}")

def main():
    parser = argparse.ArgumentParser(description="Runner de Backtesting e Validação Walk-Forward.")
    parser.add_argument(
        "--strategy", type=str, default="silver_bullet_nq_am",
        choices=[
            "silver_bullet_nq", "silver_bullet_nq_am", "silver_bullet_nq_lunch", "silver_bullet_nq_close",
            "silver_bullet_xau", "silver_bullet_xau_am", "silver_bullet_xau_lunch", "silver_bullet_xau_close",
            "london_sweep_nq", "london_sweep_xau", "orb_breakout"
        ],
        help="Estratégia a executar."
    )
    parser.add_argument("--start", type=str, default="2023-01-01", help="Data de início (YYYY-MM-DD).")
    parser.add_argument("--end", type=str, default="2025-04-30", help="Data de término (YYYY-MM-DD).")
    parser.add_argument("--filters", type=str, default="all", choices=["all", "none"], help="Habilitar ou desabilitar filtros macro e regime.")
    parser.add_argument("--walk-forward", action="store_true", help="Executar validação walk-forward.")
    parser.add_argument("--splits", type=int, default=6, help="Número de splits temporais para o walk-forward.")
    
    args = parser.parse_args()
    
    reports_dir = setup_directories()
    
    if args.walk_forward:
        run_walk_forward_validation(args, reports_dir)
    else:
        run_standard_backtest(args, reports_dir)

if __name__ == "__main__":
    main()
