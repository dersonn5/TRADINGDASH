from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Dict, Optional
import pandas as pd
from strategies.base import Strategy, Signal, Position
from backtesting.metrics import PerformanceMetrics
from core.risk_manager import RiskManager

@dataclass
class BacktestConfig:
    initial_balance: float = 10000.0
    slippage_ticks: int = 1         # quantidade de ticks de slippage na execução
    spread_ticks: int = 1           # spread em ticks
    commission_usd: float = 2.0     # comissão flat por trade round-trip
    commission_pct: float = 0.0     # comissão % por LADO sobre o nocional (OKX taker ~0.0005). Round-trip = 2x.
    tick_size: float = 0.25         # tamanho do tick padrão (0.25 para NQ, 0.01 para XAU)
    point_value: float = 20.0       # valor do ponto inteiro (20 para NQ, 100 para XAU)
    enable_break_even: bool = False
    break_even_trigger_rr: float = 1.0  # R:R em que o SL é movido para o preço de entrada (BE)
    # Gestão durante o trade: trailing após X R para travar lucro (regra: não devolver +4R)
    enable_trailing: bool = False
    trail_trigger_rr: float = 4.0       # começa a trilhar após atingir este R favorável
    trail_distance_rr: float = 1.5      # mantém o stop a este R atrás do pico (MFE)
    # Trailing ESTRUTURAL: em vez de distância fixa em R, stop segue o último swing 5m
    # a favor (abaixo do swing-low p/ BUY, acima do swing-high p/ SELL) + buffer.
    trail_mode: str = "rr"              # "rr" = distância fixa | "structure" = swing 5m
    trail_swing_bars: int = 3           # fractal: vela com N vizinhas maiores/menores de cada lado
    trail_struct_buffer_atr: float = 0.25  # buffer além do swing (fração do ATR 5m)
    # Parciais: realiza parte do lote em partial_rr e deixa o resto correr (SL p/ BE no resto)
    enable_partials: bool = False
    partial_rr: float = 2.0             # R em que tira a parcial
    partial_pct: float = 0.5            # fração do lote realizada na parcial
    # Funding de perpétuo (cripto): taxa por janela de 8h sobre o nocional. ~0.01%/8h típico.
    funding_rate_8h: float = 0.0001     # 0.01% a cada 8h (3x/dia)

class BacktestEngine:
    """
    Engine de Backtesting de Alta Fidelidade.
    Simula cronologicamente candle-by-candle (M5) o mercado, evitando look-ahead bias,
    incorporando slippage, spread, comissão e simulação realista de stop-loss e take-profit.
    """
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()

    def run(
        self,
        strategy: Strategy,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
        use_filters: bool = True,
        vix_data: pd.DataFrame = None,
        es_data: pd.DataFrame = None,
        dxy_data: pd.DataFrame = None,
        news_events: List[Dict] = None,
        candles_5m_corr: pd.DataFrame = None
    ) -> Dict:
        """
        Executa a simulação candle-by-candle.
        """
        print(f"\n[BACKTEST] Iniciando simulação para {strategy.symbol}...")
        
        # 1. Garantir fusos horários EST
        df_5m = strategy._convert_to_est(candles_5m)
        df_15m = strategy._convert_to_est(candles_15m)
        df_1h = strategy._convert_to_est(candles_1h)
        df_1d = strategy._convert_to_est(candles_1d)
        df_1m = strategy._convert_to_est(candles_1m) if (candles_1m is not None and not candles_1m.empty) else None
        df_corr = strategy._convert_to_est(candles_5m_corr) if (candles_5m_corr is not None and not candles_5m_corr.empty) else None
        
        balance = self.config.initial_balance
        positions: List[Position] = []
        active_position: Optional[Position] = None
        pending_signal: Optional[Signal] = None
        
        trades_today = 0
        current_day = None
        
        # Loop candle-by-candle no timeframe operacional (M5)
        # Começamos no candle 50 para ter dados de histórico mínimos
        for i in range(50, len(df_5m)):
            current_time = df_5m.index[i]
            candle = df_5m.iloc[i]
            
            # Controle diário de quantidade de operações
            day_str = current_time.strftime("%Y-%m-%d")
            if current_day != day_str:
                current_day = day_str
                trades_today = 0
                pending_signal = None  # Cancela pendentes do dia anterior
            
            # --- 1. Atualizar Posição Ativa (SL / TP Touch) ---
            if active_position is not None:
                high = candle['high']
                low = candle['low']
                close = candle['close']
                
                # ── Gestão durante o trade (Parcial + BE + Trailing) ──
                if self.config.enable_break_even or self.config.enable_trailing or self.config.enable_partials:
                    entry = active_position.entry_price
                    # risco INICIAL (fixo) e pico favorável (MFE), guardados na posição
                    if not hasattr(active_position, "_init_risk"):
                        active_position._init_risk = abs(entry - active_position.stop_loss)
                        active_position._mfe = entry
                        active_position._realized_partial_pnl = 0.0
                        active_position._partial_taken = False
                    risk = active_position._init_risk
                    if risk > 0:
                        is_buy = active_position.action == "BUY"
                        # overrides por-trade (estratégia pode passar gatilhos estruturais no meta)
                        _m = getattr(active_position, "meta", None) or {}
                        _partial_rr = _m.get("partial_rr_override", self.config.partial_rr)
                        _be_rr = _m.get("be_trigger_rr_override", self.config.break_even_trigger_rr)
                        if is_buy:
                            active_position._mfe = max(active_position._mfe, high)
                            r_now = (active_position._mfe - entry) / risk
                        else:
                            active_position._mfe = min(active_position._mfe, low)
                            r_now = (entry - active_position._mfe) / risk

                        # Parcial: realiza partial_pct do lote em partial_rr e move SL p/ BE no resto
                        if self.config.enable_partials and not active_position._partial_taken \
                                and r_now >= _partial_rr:
                            part_price = entry + risk * _partial_rr if is_buy \
                                else entry - risk * _partial_rr
                            part_size = active_position.size_units * self.config.partial_pct
                            part_pnl = ((part_price - entry) if is_buy else (entry - part_price)) \
                                * part_size * self.config.point_value
                            active_position._realized_partial_pnl += part_pnl
                            balance += part_pnl
                            active_position.size_units -= part_size       # resto continua
                            active_position._partial_taken = True
                            if (is_buy and active_position.stop_loss < entry) or \
                               (not is_buy and active_position.stop_loss > entry):
                                active_position.stop_loss = entry         # BE no restante

                        # Break-even
                        if self.config.enable_break_even and r_now >= _be_rr:
                            if is_buy and active_position.stop_loss < entry:
                                active_position.stop_loss = entry
                            elif not is_buy and active_position.stop_loss > entry:
                                active_position.stop_loss = entry
                        # Trailing após trigger
                        if self.config.enable_trailing and r_now >= self.config.trail_trigger_rr:
                            if self.config.trail_mode == "structure":
                                # ESTRUTURAL: stop segue o último swing 5m confirmado a favor
                                # (fractal N/N; só velas FECHADAS até i — sem look-ahead)
                                nb = self.config.trail_swing_bars
                                win = df_5m.iloc[max(0, i - 40):i + 1]
                                atr5 = float((win["high"] - win["low"]).tail(14).mean())
                                sbuf = atr5 * self.config.trail_struct_buffer_atr
                                lows, highs = win["low"].values, win["high"].values
                                locked = None
                                if is_buy:
                                    for j in range(len(lows) - nb - 1, nb - 1, -1):
                                        if lows[j] == min(lows[j - nb:j + nb + 1]):
                                            locked = float(lows[j]) - sbuf
                                            break
                                    if locked is not None and locked > active_position.stop_loss:
                                        active_position.stop_loss = locked
                                else:
                                    for j in range(len(highs) - nb - 1, nb - 1, -1):
                                        if highs[j] == max(highs[j - nb:j + nb + 1]):
                                            locked = float(highs[j]) + sbuf
                                            break
                                    if locked is not None and locked < active_position.stop_loss:
                                        active_position.stop_loss = locked
                            else:
                                if is_buy:
                                    locked = active_position._mfe - risk * self.config.trail_distance_rr
                                    if locked > active_position.stop_loss:
                                        active_position.stop_loss = locked
                                else:
                                    locked = active_position._mfe + risk * self.config.trail_distance_rr
                                    if locked < active_position.stop_loss:
                                        active_position.stop_loss = locked
                
                sl_hit = False
                tp_hit = False
                exit_reason = None
                
                # Simulação para BUY
                if active_position.action == "BUY":
                    if low <= active_position.stop_loss:
                        sl_hit = True
                    if high >= active_position.take_profit:
                        tp_hit = True
                        
                    if sl_hit and tp_hit:
                        # Stop Hunt: se ambos forem tocados na mesma vela de 5m, assume o pior (Stop Loss)
                        exit_price = active_position.stop_loss
                        exit_reason = "STOP_LOSS (STOP HUNT SIMULATED)"
                        tp_hit = False
                    elif sl_hit:
                        # Aplica slippage negativa no SL
                        exit_price = active_position.stop_loss - (self.config.slippage_ticks * self.config.tick_size)
                        exit_reason = "STOP_LOSS"
                    elif tp_hit:
                        exit_price = active_position.take_profit
                        exit_reason = "TAKE_PROFIT"
                        
                # Simulação para SELL
                else:
                    if high >= active_position.stop_loss:
                        sl_hit = True
                    if low <= active_position.take_profit:
                        tp_hit = True
                        
                    if sl_hit and tp_hit:
                        exit_price = active_position.stop_loss
                        exit_reason = "STOP_LOSS (STOP HUNT SIMULATED)"
                        tp_hit = False
                    elif sl_hit:
                        # Aplica slippage no SL
                        exit_price = active_position.stop_loss + (self.config.slippage_ticks * self.config.tick_size)
                        exit_reason = "STOP_LOSS"
                    elif tp_hit:
                        exit_price = active_position.take_profit
                        exit_reason = "TAKE_PROFIT"
                
                # Fechamento forçado no fim da killzone (invalidação de tempo) - desabilitado para Cripto 24/7
                # e para estratégias multi-dia (allow_overnight_hold=True, ex.: momentum/trend-following
                # que precisa segurar posição por dias/semanas — day-trade ICT nunca segura overnight).
                is_crypto = "USDT" in strategy.symbol
                allow_overnight = bool(getattr(getattr(strategy, "config", None), "allow_overnight_hold", False))
                if not is_crypto and not allow_overnight:
                    if hasattr(strategy, 'config') and hasattr(strategy.config, 'killzone_end'):
                        killzone_end = strategy.config.killzone_end
                    elif hasattr(strategy, 'config') and hasattr(strategy.config, 'trade_end'):
                        killzone_end = strategy.config.trade_end
                    else:
                        killzone_end = time(11, 0) if strategy.symbol == "NQ" else time(5, 0)
                    
                    if current_time.time() >= killzone_end:
                        sl_hit = False
                        tp_hit = False
                        exit_price = close
                        exit_reason = "TIME_INVALIDATION"
                    
                if sl_hit or tp_hit or exit_reason == "TIME_INVALIDATION":
                    # Calcular P&L Financeiro
                    # PnL = (Preço_Saída - Preço_Entrada) * Lote * Valor_Ponto
                    if active_position.action == "BUY":
                        gross_pnl = (exit_price - active_position.entry_price) * active_position.size_units * self.config.point_value
                    else:
                        gross_pnl = (active_position.entry_price - exit_price) * active_position.size_units * self.config.point_value
                        
                    # Funding de perpétuo: taxa proporcional ao tempo segurado, sobre o nocional.
                    funding_cost = 0.0
                    if self.config.funding_rate_8h > 0 and active_position.exit_time is not None:
                        held_h = (active_position.exit_time - active_position.entry_time).total_seconds() / 3600.0
                        notional = active_position.entry_price * active_position.size_units * self.config.point_value
                        funding_cost = abs(notional) * self.config.funding_rate_8h * (held_h / 8.0)

                    # Comissão % sobre o nocional (round-trip: entrada + saída), modelo OKX real.
                    comm_pct_cost = 0.0
                    if self.config.commission_pct > 0:
                        entry_notional = active_position.entry_price * active_position.size_units * self.config.point_value
                        exit_notional = exit_price * active_position.size_units * self.config.point_value
                        comm_pct_cost = (abs(entry_notional) + abs(exit_notional)) * self.config.commission_pct

                    # A parcial já foi creditada no balance quando realizada; aqui só o restante.
                    remainder_net = gross_pnl - self.config.commission_usd - funding_cost - comm_pct_cost
                    balance += remainder_net
                    # pnl_usd (para métricas) = restante + parcial já realizada
                    net_pnl = remainder_net + getattr(active_position, "_realized_partial_pnl", 0.0)

                    active_position.status = "CLOSED"
                    active_position.exit_price = exit_price
                    active_position.exit_time = current_time
                    active_position.pnl_usd = net_pnl
                    active_position.reason = exit_reason
                    
                    positions.append(active_position)
                    active_position = None
                    pending_signal = None
                    continue  # Pula para a próxima iteração
            
            # --- 2. Verificar Preenchimento de Sinal Pendente (Limit Order) ---
            if pending_signal is not None and active_position is None:
                # Cancelamento de ordem limite pendente após 3 velas (15 minutos para M5) para cripto
                is_crypto = "USDT" in strategy.symbol
                if is_crypto:
                    time_diff = (current_time - pending_signal.timestamp).total_seconds() / 60.0
                    if time_diff > 15.0:
                        pending_signal = None
                        continue
                else:
                    # Verifica invalidação por tempo do limite normal
                    if hasattr(strategy, 'config') and hasattr(strategy.config, 'killzone_end'):
                        killzone_end = strategy.config.killzone_end
                    elif hasattr(strategy, 'config') and hasattr(strategy.config, 'trade_end'):
                        killzone_end = strategy.config.trade_end
                    else:
                        killzone_end = time(11, 0) if strategy.symbol == "NQ" else time(5, 0)
                    
                    if current_time.time() >= killzone_end:
                        pending_signal = None
                        continue
                
                low = candle['low']
                high = candle['high']
                
                filled = False
                if pending_signal.action == "BUY" and low <= pending_signal.entry_price:
                    # Preenche com slippage/spread realista
                    fill_price = pending_signal.entry_price + (self.config.spread_ticks * self.config.tick_size)
                    filled = True
                elif pending_signal.action == "SELL" and high >= pending_signal.entry_price:
                    fill_price = pending_signal.entry_price - (self.config.spread_ticks * self.config.tick_size)
                    filled = True
                    
                if filled:
                    # Calcular tamanho do lote usando o RiskManager dinâmico do projeto
                    size = RiskManager.calculate_position_size(
                        symbol=strategy.symbol,
                        entry_price=fill_price,
                        stop_loss=pending_signal.stop_loss,
                        account_balance=balance
                    )
                    
                    if size > 0:
                        active_position = Position(
                            symbol=strategy.symbol,
                            action=pending_signal.action,
                            entry_price=fill_price,
                            stop_loss=pending_signal.stop_loss,
                            take_profit=pending_signal.take_profit,
                            size_units=size,
                            entry_time=current_time,
                            status="OPEN",
                            meta=getattr(pending_signal, "meta", {}) or {}
                        )
                        trades_today += 1
                        pending_signal = None
                    else:
                        # Capital insuficiente para respeitar o gerenciamento de risco
                        pending_signal = None
            
            # --- 3. Chamar Avaliação de Estratégia sem Look-Ahead Bias ---
            if active_position is None and pending_signal is None and trades_today < 2:
                # Verificação rápida de horário operacional antes do fatiamento caro
                current_time_only = current_time.time()
                in_operational_hours = True
                
                if hasattr(strategy, "get_operational_hours"):
                    kz_start, kz_end = strategy.get_operational_hours()
                    in_operational_hours = kz_start <= current_time_only < kz_end
                elif hasattr(strategy, "config"):
                    if hasattr(strategy.config, "killzone_start") and hasattr(strategy.config, "killzone_end"):
                        in_operational_hours = strategy.config.killzone_start <= current_time_only < strategy.config.killzone_end
                    elif hasattr(strategy.config, "killzone_macros") and strategy.config.killzone_macros is not None:
                        in_operational_hours = any(start <= current_time_only < end for start, end in strategy.config.killzone_macros)
                    elif hasattr(strategy.config, "trade_start") and hasattr(strategy.config, "trade_end"):
                        in_operational_hours = strategy.config.trade_start <= current_time_only <= strategy.config.trade_end
                
                if in_operational_hours:
                    # Filtramos todos os datasets históricos exatamente até o timestamp atual de forma hiper otimizada via busca binária
                    history_5m = df_5m.iloc[:i+1]
                    
                    idx_15m = df_15m.index.searchsorted(current_time, side='right')
                    history_15m = df_15m.iloc[:idx_15m]
                    
                    # HTF: só vela FECHADA (rótulo = abertura → fechada se abertura + duração <= agora).
                    # Sem isso, a vela 1h/1d "em formação" entra com OHLC completo = vaza futuro.
                    idx_1h = df_1h.index.searchsorted(current_time - pd.Timedelta(hours=1), side='right')
                    history_1h = df_1h.iloc[:idx_1h]

                    idx_1d = df_1d.index.searchsorted(current_time - pd.Timedelta(days=1), side='right')
                    history_1d = df_1d.iloc[:idx_1d]
                    
                    if df_1m is not None:
                        idx_1m = df_1m.index.searchsorted(current_time, side='right')
                        history_1m = df_1m.iloc[max(0, idx_1m - 100):idx_1m]
                    else:
                        history_1m = None
                    
                    # Sincroniza dados correlacionados se fornecidos para confluência SMT
                    if df_corr is not None:
                        idx_corr = df_corr.index.searchsorted(current_time, side='right')
                        strategy.correlated_data = df_corr.iloc[:idx_corr]
                    else:
                        strategy.correlated_data = None
                        
                    # 3.1 Aplicar Filtro de Regime (Volatilidade) se habilitado
                    if use_filters:
                        from filters.regime_filter import RegimeFilter
                        if not RegimeFilter.is_volatility_acceptable(history_5m):
                            continue
                            
                        # 3.2 Aplicar Filtro de Notícias se habilitado
                        from filters.news_filter import NewsFilter
                        nf = NewsFilter()
                        if news_events:
                            nf.load_simulated_news(news_events)
                        if nf.is_news_time(current_time):
                            continue
                    
                    if hasattr(strategy, "generate_signal") and callable(getattr(strategy, "generate_signal")):
                        signal = strategy.generate_signal(history_5m, history_15m, history_1h, history_1d, history_1m)
                    else:
                        signal = strategy.evaluate(history_5m, history_15m, history_1h, history_1d, history_1m)
                    
                    # 3.3 Aplicar Filtro Macro Cross-Asset se habilitado e houver sinal
                    if use_filters and signal is not None and signal.action in ["BUY", "SELL"]:
                        from filters.macro_filter import MacroFilter
                        
                        # Filtro do VIX
                        if vix_data is not None:
                            current_vix = vix_data[vix_data.index <= current_time]
                            if not current_vix.empty:
                                vix_price = current_vix.iloc[-1]['close']
                                if not MacroFilter.is_vix_safe(vix_price):
                                    signal = None
                                    
                        # Filtro do ES (para Nasdaq/NQ)
                        if signal is not None and strategy.symbol == "NQ" and es_data is not None:
                            es_history = es_data[es_data.index <= current_time]
                            if not MacroFilter.is_es_aligned(signal.action, es_history):
                                signal = None
                                
                        # Filtro do DXY (para Gold/XAUUSD)
                        if signal is not None and strategy.symbol == "XAUUSD" and dxy_data is not None:
                            dxy_history = dxy_data[dxy_data.index <= current_time]
                            if not MacroFilter.is_dxy_aligned(signal.action, dxy_history):
                                signal = None

                    if signal is not None and signal.action in ["BUY", "SELL"]:
                        # Validar relação risco-retorno mínima
                        risk = abs(signal.entry_price - signal.stop_loss)
                        reward = abs(signal.take_profit - signal.entry_price)
                        if risk > 0 and (reward / risk) >= 2.0:
                            pending_signal = signal
                        
        # Compilar resultados finais
        metrics = PerformanceMetrics.calculate(positions, self.config.initial_balance)
        return {
            "positions": positions,
            "metrics": metrics
        }
