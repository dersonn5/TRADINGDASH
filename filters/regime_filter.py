import pandas as pd
import numpy as np

class RegimeFilter:
    """
    Filtro de Regime de Mercado.
    Calcula a volatilidade relativa baseada no Average True Range (ATR) de 20 períodos
    para evitar operar em mercados sem liquidez (mortos) ou em volatilidade catastrófica de notícias.
    """
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcula o Average True Range (ATR) de forma clássica"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def is_volatility_acceptable(df_5m: pd.DataFrame, period_atr: int = 20) -> bool:
        """
        Calcula se o regime de volatilidade é aceitável (0.5 <= Ratio <= 2.0).
        """
        if len(df_5m) < period_atr * 2:
            return True
            
        atr = RegimeFilter.calculate_atr(df_5m, period=period_atr)
        current_atr = atr.iloc[-1]
        
        # Média móvel do ATR para normalizar
        mean_atr = atr.rolling(window=period_atr).mean().iloc[-1]
        
        if pd.isna(current_atr) or pd.isna(mean_atr) or mean_atr == 0:
            return True
            
        ratio = current_atr / mean_atr
        
        # Aceita se a volatilidade estiver na faixa aceitável
        return 0.5 <= ratio <= 2.0
