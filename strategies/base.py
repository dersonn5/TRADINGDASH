from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import pandas as pd

@dataclass
class Signal:
    symbol: str
    action: str  # 'BUY', 'SELL', 'PASS'
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence_score: float = 0.0
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    meta: dict = field(default_factory=dict)  # marcações do cenário (sweep, FVG, HTF array...)

@dataclass
class Position:
    symbol: str
    action: str  # 'BUY', 'SELL'
    entry_price: float
    stop_loss: float
    take_profit: float
    size_units: float
    entry_time: datetime
    status: str = "OPEN"  # 'OPEN', 'CLOSED'
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_usd: float = 0.0
    reason: str = ""
    meta: dict = field(default_factory=dict)  # cenário que originou a entrada (para visualização)

@dataclass
class TradeRecord:
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    size_units: float
    entry_time: datetime
    exit_time: datetime
    pnl_usd: float
    result: str  # 'WIN', 'LOSS', 'PASS', 'FORCE_CLOSE'
    reasoning: str = ""

class Strategy:
    name: str = "base_strategy"
    symbol: str = "GENERIC"
    timeframe_entry: str = "5m"
    timeframe_structure: str = "15m"
    timeframe_bias: str = "1h"

    # Sistema de diagnóstico (opt-in): quando habilitado, cada gate registrado
    # em self.last_gates. Permite analisar qual filtro mata mais sinais.
    diagnostic_enabled: bool = False
    last_gates: List[dict] = None

    def _gate(self, name: str, passed: bool, value=None, reason: str = "") -> bool:
        """Registra resultado de um gate (filtro) durante a avaliação.
        Retorna o próprio `passed` para uso direto em if statements."""
        if self.diagnostic_enabled:
            if self.last_gates is None:
                self.last_gates = []
            self.last_gates.append({
                "name": name,
                "passed": bool(passed),
                "value": value,
                "reason": reason,
            })
        return passed

    def _reset_gates(self):
        """Limpa o log de gates da última avaliação."""
        self.last_gates = []

    def _get_asian_range(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """
        Retorna a máxima e a mínima do Asian Range (20:00 EST do dia anterior às 02:00 EST do dia atual).
        """
        if df_5m.empty:
            return None, None
            
        current_date = current_time.date()
        if current_time.hour >= 20:
            start_dt = pd.to_datetime(f"{current_date} 20:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
            end_dt = pd.to_datetime(f"{(current_time + timedelta(days=1)).date()} 02:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
        else:
            prev_date = (current_time - timedelta(days=1)).date()
            start_dt = pd.to_datetime(f"{prev_date} 20:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
            end_dt = pd.to_datetime(f"{current_date} 02:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
            
        # Alinha os fusos horários
        if df_5m.index.tz is not None:
            start_dt = start_dt.tz_convert(df_5m.index.tz)
            end_dt = end_dt.tz_convert(df_5m.index.tz)
        else:
            start_dt = start_dt.tz_localize(None)
            end_dt = end_dt.tz_localize(None)
            
        # OTIMIZAÇÃO: Filtrar apenas nos candles recentes para evitar varrer todo o DataFrame histórico de 300k+ itens
        recent_candles = df_5m.iloc[-600:]
        asian_candles = recent_candles[(recent_candles.index >= start_dt) & (recent_candles.index <= end_dt)]
        if asian_candles.empty:
            return None, None
            
        return float(asian_candles['high'].max()), float(asian_candles['low'].min())

    def _detect_london_manipulation(
        self,
        df_5m: pd.DataFrame,
        asian_high: Optional[float],
        asian_low: Optional[float],
        current_time: datetime
    ) -> str:
        """
        Verifica se a sessão de Londres manipulou (varreu) o Asian Range (02:00 às 09:30 EST).
        Retorna 'BULLISH', 'BEARISH' ou 'NONE'.
        """
        if df_5m.empty or asian_high is None or asian_low is None:
            return "NONE"
            
        current_date = current_time.date()
        # Janela de Londres: 02:00 EST às 09:30 EST do dia atual
        london_start = pd.to_datetime(f"{current_date} 02:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
        london_end = pd.to_datetime(f"{current_date} 09:30:00").tz_localize('America/New_York', nonexistent='shift_forward')
        
        # Alinha fusos horários
        if df_5m.index.tz is not None:
            london_start = london_start.tz_convert(df_5m.index.tz)
            london_end = london_end.tz_convert(df_5m.index.tz)
        else:
            london_start = london_start.tz_localize(None)
            london_end = london_end.tz_localize(None)
            
        # Filtra candles da janela de Londres
        london_candles = df_5m[(df_5m.index >= london_start) & (df_5m.index <= london_end)]
        if london_candles.empty:
            return "NONE"
            
        london_high = london_candles['high'].max()
        london_low = london_candles['low'].min()
        
        swept_low = london_low < asian_low
        swept_high = london_high > asian_high
        
        if swept_low and not swept_high:
            return "BULLISH"
        elif swept_high and not swept_low:
            return "BEARISH"
        else:
            return "NONE"

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
    ) -> Optional[Signal]:
        """
        Avalia os dados históricos e retorna um Signal se as regras forem atendidas.
        Deve ser implementada por classes filhas.
        """
        raise NotImplementedError("Método evaluate() deve ser implementado pela estratégia filha.")

    def _detect_bpr_m1(self, df_1m: pd.DataFrame, lookback: int = 20):
        """
        Detecta Balanced Price Range (BPR) nos últimos `lookback` candles M1.
        BPR = sobreposição entre FVG bullish e FVG bearish.
        Retorna (bpr_top, bpr_bottom) ou (None, None).
        """
        if df_1m is None or len(df_1m) < 4:
            return None, None

        n = len(df_1m)
        start = max(2, n - lookback)
        bull_fvgs = []
        bear_fvgs = []

        for i in range(start, n):
            c_curr = df_1m.iloc[i]
            c_prev2 = df_1m.iloc[i - 2]
            if c_curr['low'] > c_prev2['high']:
                bull_fvgs.append((float(c_curr['low']), float(c_prev2['high'])))  # (top, bottom)
            if c_curr['high'] < c_prev2['low']:
                bear_fvgs.append((float(c_prev2['low']), float(c_curr['high'])))  # (top, bottom)

        # Procurar sobreposição entre qualquer par bull+bear
        for (bull_top, bull_bot) in bull_fvgs:
            for (bear_top, bear_bot) in bear_fvgs:
                overlap_top = min(bull_top, bear_top)
                overlap_bot = max(bull_bot, bear_bot)
                if overlap_top > overlap_bot:  # Sobreposição existe
                    return overlap_top, overlap_bot

        return None, None

    def _confirm_m1_entry(
        self,
        df_1m: pd.DataFrame,
        fvg_zone_top: float,
        fvg_zone_bottom: float,
        direction: str,  # "bullish" ou "bearish"
        lookback_m1: int = 30,
    ):
        """
        Dentro da zona do FVG M5, verifica no M1:
        1. Liquidity sweep: wick além da fronteira da zona
        2. MSS M1: quebra de swing structure na direção do trade
        3. FVG M1 ou BPR M1 formado após o MSS

        Retorna dict com:
            confirmed (bool)
            entry_price (float) — CE do FVG M1 ou midpoint do BPR
            sl_price (float) — extremo do swing M1 + buffer
            reason (str)
        Ou None se não confirmado.
        """
        if df_1m is None or len(df_1m) < 6:
            return None

        n = len(df_1m)
        start = max(0, n - lookback_m1)
        window = df_1m.iloc[start:]

        if direction == "bullish":
            # Procurar sweep de low + MSS bullish no M1
            highs = window['high'].values
            lows = window['low'].values
            closes = window['close'].values
            w_n = len(window)

            # Encontrar swing low recente dentro/abaixo da zona
            swing_low = None
            swing_low_idx = None
            for i in range(w_n - 2, 0, -1):
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    swing_low = lows[i]
                    swing_low_idx = i
                    break

            if swing_low is None:
                return None

            # Verificar se houve sweep: algum candle com low < swing_low
            sweep_idx = None
            for i in range(swing_low_idx + 1, w_n):
                if lows[i] < swing_low:
                    sweep_idx = i
                    break

            if sweep_idx is None:
                return None

            # MSS: após o sweep, fechamento acima do swing_low = estrutura quebrou bullish
            mss_confirmed = False
            mss_idx = None
            for i in range(sweep_idx, w_n):
                if closes[i] > swing_low:
                    mss_confirmed = True
                    mss_idx = i
                    break

            if not mss_confirmed:
                return None

            # Após MSS, procurar FVG bullish M1
            for i in range(mss_idx + 1, w_n):
                if i >= 2:
                    c_curr = window.iloc[i]
                    c_prev2 = window.iloc[i - 2]
                    if c_curr['low'] > c_prev2['high']:
                        fvg_top = float(c_curr['low'])
                        fvg_bot = float(c_prev2['high'])
                        entry = (fvg_top + fvg_bot) / 2.0
                        sl = lows[sweep_idx] - (fvg_top - fvg_bot) * 0.5  # abaixo do sweep
                        return {
                            "confirmed": True,
                            "entry_price": round(entry, 2),
                            "sl_price": round(sl, 2),
                            "reason": f"M1 MSS bullish confirmado. FVG M1 [{fvg_bot:.2f}-{fvg_top:.2f}]. Entry CE {entry:.2f}.",
                            "type": "fvg_m1"
                        }

            # Sem FVG M1, tentar BPR
            bpr_top, bpr_bot = self._detect_bpr_m1(window.iloc[mss_idx:], lookback=10)
            if bpr_top is not None:
                entry = (bpr_top + bpr_bot) / 2.0
                sl = lows[sweep_idx] - (bpr_top - bpr_bot) * 0.5
                return {
                    "confirmed": True,
                    "entry_price": round(entry, 2),
                    "sl_price": round(sl, 2),
                    "reason": f"M1 MSS bullish + BPR [{bpr_bot:.2f}-{bpr_top:.2f}]. Entry midpoint {entry:.2f}.",
                    "type": "bpr_m1"
                }

            return None

        else:  # bearish
            highs = window['high'].values
            lows = window['low'].values
            closes = window['close'].values
            w_n = len(window)

            # Swing high recente
            swing_high = None
            swing_high_idx = None
            for i in range(w_n - 2, 0, -1):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    swing_high = highs[i]
                    swing_high_idx = i
                    break

            if swing_high is None:
                return None

            # Sweep: wick acima do swing_high
            sweep_idx = None
            for i in range(swing_high_idx + 1, w_n):
                if highs[i] > swing_high:
                    sweep_idx = i
                    break

            if sweep_idx is None:
                return None

            # MSS: fechamento abaixo do swing_high
            mss_confirmed = False
            mss_idx = None
            for i in range(sweep_idx, w_n):
                if closes[i] < swing_high:
                    mss_confirmed = True
                    mss_idx = i
                    break

            if not mss_confirmed:
                return None

            # FVG bearish M1 após MSS
            for i in range(mss_idx + 1, w_n):
                if i >= 2:
                    c_curr = window.iloc[i]
                    c_prev2 = window.iloc[i - 2]
                    if c_curr['high'] < c_prev2['low']:
                        fvg_top = float(c_prev2['low'])
                        fvg_bot = float(c_curr['high'])
                        entry = (fvg_top + fvg_bot) / 2.0
                        sl = highs[sweep_idx] + (fvg_top - fvg_bot) * 0.5
                        return {
                            "confirmed": True,
                            "entry_price": round(entry, 2),
                            "sl_price": round(sl, 2),
                            "reason": f"M1 MSS bearish confirmado. FVG M1 [{fvg_bot:.2f}-{fvg_top:.2f}]. Entry CE {entry:.2f}.",
                            "type": "fvg_m1"
                        }

            # BPR fallback
            bpr_top, bpr_bot = self._detect_bpr_m1(window.iloc[mss_idx:], lookback=10)
            if bpr_top is not None:
                entry = (bpr_top + bpr_bot) / 2.0
                sl = highs[sweep_idx] + (bpr_top - bpr_bot) * 0.5
                return {
                    "confirmed": True,
                    "entry_price": round(entry, 2),
                    "sl_price": round(sl, 2),
                    "reason": f"M1 MSS bearish + BPR [{bpr_bot:.2f}-{bpr_top:.2f}]. Entry midpoint {entry:.2f}.",
                    "type": "bpr_m1"
                }

            return None

    def _detect_eqh_eql(
        self,
        df: pd.DataFrame,
        direction: str,  # "high" ou "low"
        lookback: int = 50,
        tolerance_pct: float = 0.0005
    ) -> list:
        """
        Detecta topos duplos/triplos próximos (EQH) ou fundos duplos/triplos próximos (EQL)
        nos últimos `lookback` candles.
        Retorna uma lista de tuplas (idx, preço) que compõem o EQH/EQL.
        """
        if df is None or len(df) < 10:
            return []
            
        # OTIMIZAÇÃO CRÍTICA: Fatiar para evitar cópia de arrays de 300k+ elementos
        if len(df) > lookback:
            df = df.iloc[-lookback:]
            
        n = len(df)
        start = max(1, n - lookback)
        highs = df['high'].values
        lows = df['low'].values
        
        pivots = []
        if direction == "high":
            for i in range(start, n - 1):
                if highs[i] >= highs[i-1] and highs[i] >= highs[i+1]:
                    pivots.append((i, highs[i]))
            
            for idx1, price1 in pivots:
                for idx2, price2 in pivots:
                    if idx1 != idx2 and abs(price1 - price2) / price1 <= tolerance_pct:
                        return [(idx1, price1), (idx2, price2)]
        else: # low
            for i in range(start, n - 1):
                if lows[i] <= lows[i-1] and lows[i] <= lows[i+1]:
                    pivots.append((i, lows[i]))
                    
            for idx1, price1 in pivots:
                for idx2, price2 in pivots:
                    if idx1 != idx2 and abs(price1 - price2) / price1 <= tolerance_pct:
                        return [(idx1, price1), (idx2, price2)]
                        
        return []

    def _detect_breaker_block(
        self,
        df: pd.DataFrame,
        direction: str,  # "bullish" ou "bearish"
        lookback: int = 30,
        atr_multiplier: float = 1.2,
        asian_range: Tuple[Optional[float], Optional[float]] = (None, None),
        range_24h: Tuple[Optional[float], Optional[float]] = (None, None)
    ):
        """
        Detecta Breaker Block canônico com Liquidity Sweep de relevância institucional (24h Range, Asian Range, EQH/EQL ou Extremos) e MSS.
        """
        if df is None or len(df) < 10:
            return None

        # OTIMIZAÇÃO CRÍTICA: Fatiar para evitar cópia de arrays de 300k+ elementos.
        # A profundidade máxima de busca no histórico para swings/displacement/invalidates é lookback + 50.
        max_needed = lookback + 50
        if len(df) > max_needed:
            df = df.iloc[-max_needed:]

        n = len(df)
        start = max(3, n - lookback)

        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        closes = df['close'].values

        # Calcular ATR(14)
        atr_val = 0.0
        if n >= 15:
            tr_list = []
            for i in range(n - 14, n):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1])
                )
                tr_list.append(tr)
            atr_val = sum(tr_list) / len(tr_list) if tr_list else 0.0

        current_price = closes[-1]

        # Encontrar swings de 1 candle de cada lado
        swings_high = []
        swings_low = []
        for i in range(start, n - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                swings_high.append((i, highs[i]))
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                swings_low.append((i, lows[i]))

        # Otimização: precalcular EQH/EQL antes de qualquer loop
        eq_high_pivots = self._detect_eqh_eql(df, "high", lookback=lookback) if direction == "bearish" else []
        eq_low_pivots = self._detect_eqh_eql(df, "low", lookback=lookback) if direction == "bullish" else []

        if direction == "bearish":
            for idx_sweep, price_sweep in reversed(swings_high):
                if idx_sweep >= n - 2:
                    continue

                for idx_sh1, price_sh1 in reversed(swings_high):
                    if idx_sh1 >= idx_sweep:
                        continue
                    if price_sweep > price_sh1:
                        # Validação de relevância institucional do sweep para evitar over-filtering mas manter qualidade
                        is_institutional_sweep = False
                        
                        # 1. EQH Check
                        if eq_high_pivots:
                            max_eq = max(p[1] for p in eq_high_pivots)
                            if price_sweep >= max_eq:
                                is_institutional_sweep = True
                                
                        # 2. Asian Session High Check
                        asian_high, _ = asian_range
                        if asian_high is not None and price_sweep >= asian_high:
                            is_institutional_sweep = True
                            
                        # 3. 24h High Check
                        range_high, _ = range_24h
                        if range_high is not None and price_sweep >= range_high:
                            is_institutional_sweep = True
                            
                        # 4. Extremidade de Curto Prazo (Highest High nos últimos 24 candles)
                        recent_window = df.iloc[max(0, idx_sweep - 24):idx_sweep]
                        if not recent_window.empty:
                            recent_high = recent_window['high'].max()
                            if price_sweep >= recent_high:
                                is_institutional_sweep = True

                        if not is_institutional_sweep:
                            continue

                        # Encontrar o Swing Low estrutural entre idx_sh1 e idx_sweep
                        between_lows = df.iloc[idx_sh1 + 1 : idx_sweep]
                        if between_lows.empty:
                            continue
                        
                        swing_low_idx = between_lows['low'].idxmin()
                        swing_low_idx = df.index.get_loc(swing_low_idx)
                        swing_low_val = lows[swing_low_idx]

                        # Verificar se houve MSS: preço fechou abaixo de swing_low_val após idx_sweep
                        mss_found = False
                        mss_idx = None
                        for j in range(idx_sweep + 1, n):
                            if closes[j] < swing_low_val:
                                mss_found = True
                                mss_idx = j
                                break

                        if not mss_found:
                            continue

                        # Displacement
                        body = abs(closes[mss_idx] - opens[mss_idx])
                        if atr_val > 0.0 and body < atr_multiplier * atr_val:
                            continue

                        # O Breaker Block zone é a última vela de alta no Swing High 1
                        ob_high, ob_low = highs[idx_sh1], lows[idx_sh1]
                        for k in range(max(start, idx_sh1 - 2), min(n, idx_sh1 + 3)):
                            if closes[k] > opens[k]:
                                ob_high, ob_low = float(highs[k]), float(lows[k])
                                break

                        # Invalidação: fechamento acima da máxima da zona
                        invalidated = False
                        for j in range(mss_idx, n):
                            if closes[j] > ob_high:
                                invalidated = True
                                break

                        if invalidated:
                            continue

                        # Reteste
                        price_in_breaker = (current_price <= ob_high * 1.002) and (current_price >= ob_low * 0.998)
                        if price_in_breaker:
                            entry = (ob_high + ob_low) / 2.0
                            sl = ob_high + (ob_high - ob_low) * 0.5
                            return {
                                "zone_high": round(ob_high, 2),
                                "zone_low": round(ob_low, 2),
                                "entry_price": round(entry, 2),
                                "sl_price": round(sl, 2),
                                "breaker_type": "bearish",
                                "swing_high": round(price_sweep, 2),
                                "reason": (
                                    f"Bearish Breaker canônico: Swing High [{price_sh1:.2f}] varrido por "
                                    f"[{price_sweep:.2f}]. Quebrou Swing Low estrutural [{swing_low_val:.2f}] com displacement. "
                                    f"Preço retornou à zona do Breaker [{ob_low:.2f}-{ob_high:.2f}]."
                                )
                            }
                            
        else: # bullish
            for idx_sweep, price_sweep in reversed(swings_low):
                if idx_sweep >= n - 2:
                    continue

                for idx_sl1, price_sl1 in reversed(swings_low):
                    if idx_sl1 >= idx_sweep:
                        continue
                    if price_sweep < price_sl1:
                        # Validação de relevância institucional do sweep para evitar over-filtering mas manter qualidade
                        is_institutional_sweep = False
                        
                        # 1. EQL Check
                        if eq_low_pivots:
                            min_eq = min(p[1] for p in eq_low_pivots)
                            if price_sweep <= min_eq:
                                is_institutional_sweep = True
                                
                        # 2. Asian Session Low Check
                        _, asian_low = asian_range
                        if asian_low is not None and price_sweep <= asian_low:
                            is_institutional_sweep = True
                            
                        # 3. 24h Low Check
                        _, range_low = range_24h
                        if range_low is not None and price_sweep <= range_low:
                            is_institutional_sweep = True
                            
                        # 4. Extremidade de Curto Prazo (Lowest Low nos últimos 24 candles)
                        recent_window = df.iloc[max(0, idx_sweep - 24):idx_sweep]
                        if not recent_window.empty:
                            recent_low = recent_window['low'].min()
                            if price_sweep <= recent_low:
                                is_institutional_sweep = True

                        if not is_institutional_sweep:
                            continue

                        # Encontrar o Swing High estrutural entre idx_sl1 e idx_sweep
                        between_highs = df.iloc[idx_sl1 + 1 : idx_sweep]
                        if between_highs.empty:
                            continue
                        
                        swing_high_idx = between_highs['high'].idxmax()
                        swing_high_idx = df.index.get_loc(swing_high_idx)
                        swing_high_val = highs[swing_high_idx]

                        # Verificar se houve MSS: preço fechou acima de swing_high_val após idx_sweep
                        mss_found = False
                        mss_idx = None
                        for j in range(idx_sweep + 1, n):
                            if closes[j] > swing_high_val:
                                mss_found = True
                                mss_idx = j
                                break

                        if not mss_found:
                            continue

                        # Displacement
                        body = abs(closes[mss_idx] - opens[mss_idx])
                        if atr_val > 0.0 and body < atr_multiplier * atr_val:
                            continue

                        # O Breaker Block zone é a última vela de baixa no Swing Low 1
                        ob_high, ob_low = highs[idx_sl1], lows[idx_sl1]
                        for k in range(max(start, idx_sl1 - 2), min(n, idx_sl1 + 3)):
                            if closes[k] < opens[k]:
                                ob_high, ob_low = float(highs[k]), float(lows[k])
                                break

                        # Invalidação: fechamento abaixo da mínima da zona
                        invalidated = False
                        for j in range(mss_idx, n):
                            if closes[j] < ob_low:
                                invalidated = True
                                break

                        if invalidated:
                            continue

                        # Reteste
                        price_in_breaker = (current_price >= ob_low * 0.998) and (current_price <= ob_high * 1.002)
                        if price_in_breaker:
                            entry = (ob_high + ob_low) / 2.0
                            sl = ob_low - (ob_high - ob_low) * 0.5
                            return {
                                "zone_high": round(ob_high, 2),
                                "zone_low": round(ob_low, 2),
                                "entry_price": round(entry, 2),
                                "sl_price": round(sl, 2),
                                "breaker_type": "bullish",
                                "swing_low": round(price_sweep, 2),
                                "reason": (
                                    f"Bullish Breaker canônico: Swing Low [{price_sl1:.2f}] varrido por "
                                    f"[{price_sweep:.2f}]. Quebrou Swing High estrutural [{swing_high_val:.2f}] com displacement. "
                                    f"Preço retornou à zona do Breaker [{ob_low:.2f}-{ob_high:.2f}]."
                                )
                            }
        return None

    def _detect_dynamic_dol(self, df_structure: pd.DataFrame, direction: str, current_price: float, lookback: int = 50) -> Optional[float]:
        """
        Detecta o Draw on Liquidity (DOL) dinâmico nos últimos `lookback` candles do timeframe estrutural.
        Para BUY: encontra a liquidez de compra (Buy-Side Liquidity - BSL) mais próxima acima do preço atual.
        Para SELL: encontra a liquidez de venda (Sell-Side Liquidity - SSL) mais próxima abaixo do preço atual.
        Retorna o preço do alvo ou None.
        """
        if df_structure is None or df_structure.empty or len(df_structure) < 10:
            return None

        n = len(df_structure)
        start = max(0, n - lookback)
        window = df_structure.iloc[start:]

        highs = window['high'].values
        lows = window['low'].values

        # Encontrar pivots de swing estruturais (2/2) na janela
        swings = []
        if direction == "BUY":
            for i in range(2, len(window) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    if highs[i] > current_price:
                        swings.append((i, highs[i]))
            if not swings:
                for i in range(1, len(window) - 1):
                    if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > current_price:
                        swings.append((i, highs[i]))
            
            if swings:
                swings.sort(key=lambda x: x[1], reverse=True) # maior high primeiro (BSL maior)
                return float(swings[0][1])

        else: # SELL
            for i in range(2, len(window) - 2):
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    if lows[i] < current_price:
                        swings.append((i, lows[i]))
            if not swings:
                for i in range(1, len(window) - 1):
                    if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < current_price:
                        swings.append((i, lows[i]))
            
            if swings:
                swings.sort(key=lambda x: x[1]) # menor low primeiro (SSL menor)
                return float(swings[0][1])

        return None

