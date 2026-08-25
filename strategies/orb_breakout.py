from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
from strategies.base import Strategy, Signal

@dataclass
class ORBConfig:
    # Período para calcular a faixa de abertura (Opening Range)
    range_start: time = time(9, 30)   # 09:30 EST
    range_end: time = time(10, 0)     # 10:00 EST (30-min ORB)
    
    # Janela onde entradas são permitidas
    trade_start: time = time(10, 0)   # 10:00 EST
    trade_end: time = time(11, 30)    # 11:30 EST
    
    # Parâmetros de risco
    min_rr: float = 2.5               # Relação Risco/Retorno mínima
    use_half_range_sl: bool = True    # Se True, coloca o SL no meio do range (melhor R:R), se False, no extremo oposto
    max_trades_per_day: int = 1       # Limite de 1 operação por dia para evitar overtrading
    tick_size: float = 0.25           # Tamanho do tick (NQ)
    require_daily_bias: bool = False  # Opcional: Alinhamento com a tendência diária

class ORBBreakout(Strategy):
    """
    Estratégia Opening Range Breakout (ORB) - Plano B
    Identifica a máxima e a mínima dos primeiros 30 minutos da sessão de Nova York (09:30 - 10:00 EST),
    e entra na direção da quebra de estrutura (Breakout) com Stop Loss inteligente e alvo simétrico.
    """
    name = "orb_breakout"
    symbol = "NQ"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: ORBConfig = None):
        self.config = config or ORBConfig()

    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        """Garante que o índice do DataFrame esteja em fuso EST/EDT (America/New_York)"""
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        if df_copy.index.tz is None:
            df_copy.index = df_copy.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df_copy.index = df_copy.index.tz_convert('America/New_York')
        return df_copy

    def _get_opening_range(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """Calcula a máxima e a mínima do Opening Range para o dia atual."""
        day_str = current_time.strftime("%Y-%m-%d")
        
        # Filtra as velas do dia atual entre 09:30 e 10:00 EST
        start_dt = pd.to_datetime(f"{day_str} {self.config.range_start}").tz_localize('America/New_York')
        end_dt = pd.to_datetime(f"{day_str} {self.config.range_end}").tz_localize('America/New_York')
        
        range_candles = df_5m[(df_5m.index >= start_dt) & (df_5m.index < end_dt)]
        if range_candles.empty:
            return None, None
            
        return range_candles['high'].max(), range_candles['low'].min()

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
    ) -> Optional[Signal]:
        """
        Avalia se ocorreu breakout da faixa de abertura e gera o sinal de entrada.
        """
        if candles_5m.empty:
            return None
            
        # 1. Converter para EST
        df_5m = self._convert_to_est(candles_5m)
        current_time = df_5m.index[-1]
        current_time_only = current_time.time()
        
        # 2. Verificar se estamos dentro da janela operacional de trade (10:00 - 11:30 EST)
        if not (self.config.trade_start <= current_time_only <= self.config.trade_end):
            return None
            
        # 3. Obter a máxima e a mínima do range de abertura (09:30 - 10:00)
        range_high, range_low = self._get_opening_range(df_5m, current_time)
        if range_high is None or range_low is None:
            return None
            
        range_size = range_high - range_low
        if range_size <= 0:
            return None
            
        # 4. Avaliar breakout com base na vela fechada anterior
        c3 = df_5m.iloc[-1]  # Vela M5 atual
        
        # BUY: Fechamento acima da máxima do range
        if c3['close'] > range_high:
            entry_price = c3['close']
            
            # SL: Meio do range ou extremo inferior
            if self.config.use_half_range_sl:
                stop_loss = range_high - (range_size / 2.0)
            else:
                stop_loss = range_low
                
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * self.config.min_rr)
            
            reason = (f"ORB 30m BULLISH Breakout detectado. Fechamento ({c3['close']:.2f}) "
                      f"acima da máxima do range ({range_high:.2f}). Range size: {range_size:.2f} pontos. "
                      f"SL ajustado para {stop_loss:.2f} e TP para {take_profit:.2f} (RR {self.config.min_rr}).")
                      
            return Signal(
                symbol=self.symbol,
                action="BUY",
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2),
                confidence_score=0.85,
                reasoning=reason,
                timestamp=current_time.to_pydatetime()
            )
            
        # SELL: Fechamento abaixo da mínima do range
        elif c3['close'] < range_low:
            entry_price = c3['close']
            
            # SL: Meio do range ou extremo superior
            if self.config.use_half_range_sl:
                stop_loss = range_low + (range_size / 2.0)
            else:
                stop_loss = range_high
                
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * self.config.min_rr)
            
            reason = (f"ORB 30m BEARISH Breakout detectado. Fechamento ({c3['close']:.2f}) "
                      f"abaixo da mínima do range ({range_low:.2f}). Range size: {range_size:.2f} pontos. "
                      f"SL ajustado para {stop_loss:.2f} e TP para {take_profit:.2f} (RR {self.config.min_rr}).")
                      
            return Signal(
                symbol=self.symbol,
                action="SELL",
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2),
                confidence_score=0.85,
                reasoning=reason,
                timestamp=current_time.to_pydatetime()
            )
            
        return None
