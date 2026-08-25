import pandas as pd

class MacroFilter:
    """
    Filtro Macro Cross-Asset.
    Bloqueia trades com base no sentimento de risco sistêmico global (VIX),
    momentum oposto de correlação com S&P 500 (ES) e pressão contrária do Índice Dólar (DXY).
    """
    @staticmethod
    def is_vix_safe(vix_price: float) -> bool:
        """
        Bloqueia se o VIX estiver acima de 30, indicando pânico sistêmico
        onde modelos de price action clássicos sofrem rupturas estruturais.
        """
        return vix_price <= 30.0

    @staticmethod
    def is_es_aligned(nq_direction: str, es_candles_5m: pd.DataFrame) -> bool:
        """
        Garante que o S&P 500 (ES) não esteja indo na direção oposta ao trade de NQ.
        """
        if es_candles_5m.empty or len(es_candles_5m) < 3:
            return True
            
        # Calcular momentum do ES (fechamento atual vs fechamento de 3 velas atrás)
        es_momentum = es_candles_5m.iloc[-1]['close'] - es_candles_5m.iloc[-3]['close']
        
        if nq_direction == "BUY" and es_momentum < 0:
            return False  # ES caindo forte atua como âncora contra alta de NQ
        elif nq_direction == "SELL" and es_momentum > 0:
            return False  # ES subindo forte segura a queda de NQ
            
        return True

    @staticmethod
    def is_dxy_aligned(xau_direction: str, dxy_candles_5m: pd.DataFrame) -> bool:
        """
        Garante que a força do Dólar (DXY) não esteja em colisão frontal com o Ouro (XAU).
        Ouro e Dólar têm correlação fortemente negativa de longo prazo.
        """
        if dxy_candles_5m.empty or len(dxy_candles_5m) < 3:
            return True
            
        dxy_momentum = dxy_candles_5m.iloc[-1]['close'] - dxy_candles_5m.iloc[-3]['close']
        
        if xau_direction == "BUY" and dxy_momentum > 0:
            return False  # DXY subindo forte inviabiliza longs de XAU
        elif xau_direction == "SELL" and dxy_momentum < 0:
            return False  # DXY caindo forte inviabiliza shorts de XAU
            
        return True
