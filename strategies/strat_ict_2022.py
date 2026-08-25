import pandas as pd
from typing import Optional, List, Tuple
from datetime import time

from strategies.base import Signal
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig


class StratICT2022(ICTTopDownCrypto):
    name = "strat_ict_2022"

    def __init__(self, config=None):
        super().__init__(config or ICTTopDownConfig())
        self.config = self.config
        
    def _detect_fvg_1m(self, df: pd.DataFrame, lookback: int = 10) -> List[Tuple[str, float, float, int]]:
        """Detecta FVGs puros no 1M."""
        if len(df) < 4:
            return []
        n = len(df)
        start = max(2, n - lookback)
        fvgs = []
        for i in range(start, n - 1):
            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1] # Displacement candle
            c3 = df.iloc[i]     # Current candle (forming FVG)
            
            # Bullish FVG
            if c3["low"] > c1["high"]:
                fvgs.append(("BUY", float(c3["low"]), float(c1["high"]), i))
            # Bearish FVG
            elif c3["high"] < c1["low"]:
                fvgs.append(("SELL", float(c1["low"]), float(c3["high"]), i))
        return fvgs

    def generate_signal(self, candles_5m: pd.DataFrame, candles_15m: pd.DataFrame = None,
                        candles_1h: pd.DataFrame = None, candles_1d: pd.DataFrame = None,
                        candles_1m: pd.DataFrame = None) -> Optional[Signal]:
        
        if candles_1m is None or len(candles_1m) < 60:
            return None
            
        df1m = self._convert_to_est(candles_1m)
        df1h = self._convert_to_est(candles_1h)
        
        last_ts = df1m.index[-1]
        cur_time = last_ts.time()
        
        # 1. Gate de Horário (e.g., 9:30 - 11:30 EST)
        if not self._in_window(cur_time, time(9, 30), time(11, 30)):
            return None
            
        # 2. HTF Sweep (1H Liquidity)
        if df1h is None or len(df1h) < 10:
            return None
            
        h1_h = df1h["high"].values
        h1_l = df1h["low"].values
        n_1h = len(df1h)
        
        high_recent = float(df1m["high"].iloc[-30:].max())
        low_recent = float(df1m["low"].iloc[-30:].min())
        
        sh_1h, sl_1h = None, None
        
        # Buscar topos/fundos de 1H das últimas 5 horas
        for i in range(n_1h - 2, max(0, n_1h - 7), -1):
            if sh_1h is None and high_recent > h1_h[i]:
                sh_1h = float(h1_h[i])
            if sl_1h is None and low_recent < h1_l[i]:
                sl_1h = float(h1_l[i])
            if sh_1h is not None and sl_1h is not None:
                break
                
        bias = None
        sweep_extreme = None
        if sh_1h is not None and high_recent > sh_1h:
            bias = "SELL"
            sweep_extreme = high_recent
        elif sl_1h is not None and low_recent < sl_1h:
            bias = "BUY"
            sweep_extreme = low_recent
            
        if bias is None:
            return None
            
        # 3. MSS (Market Structure Shift) no 1M + FVG
        # O deslocamento reverso deve ocorrer APÓS a varredura
        
        fvgs = self._detect_fvg_1m(df1m, lookback=10)
        target_fvg = None
        
        for side, ftop, fbot, idx in reversed(fvgs):
            if side == bias:
                # Verifica se o FVG está fresco (não foi preenchido por completo)
                # Para uma ordem pendente, o preço atual deve estar fora do FVG
                curr_close = float(df1m["close"].iloc[-1])
                
                if side == "BUY" and curr_close > ftop:
                    target_fvg = (ftop, fbot)
                    break
                elif side == "SELL" and curr_close < fbot:
                    target_fvg = (ftop, fbot)
                    break
                    
        if target_fvg is None:
            return None
            
        ftop, fbot = target_fvg
        
        # 4. Ordem Pendente (Limit) na borda do FVG
        # Com Stop Loss no extremo do Sweep
        
        if bias == "BUY":
            entry_price = ftop
            stop_loss = sweep_extreme - 2.0 # buffer em pontos
            take_profit = entry_price + (entry_price - stop_loss) * 3.0 # Alvo 3:1
        else:
            entry_price = fbot
            stop_loss = sweep_extreme + 2.0
            take_profit = entry_price - (stop_loss - entry_price) * 3.0 # Alvo 3:1
            
        # Retorna o sinal limit
        return Signal(
            symbol=self.symbol or "NQ",
            action=bias,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence_score=0.95,
            timestamp=last_ts.to_pydatetime(),
            meta={
                "strategy": self.name,
                "ifvg_zone": (ftop, fbot),
                "swept_1h": sh_1h if bias == "SELL" else sl_1h,
                "sweep_extreme": sweep_extreme
            }
        )
