from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple, List
import pandas as pd
from strategies.base import Strategy, Signal

@dataclass
class PropFirm2024CryptoConfig:
    killzone_macros: List[Tuple[time, time]] = None
    killzone_end: time = time(17, 0)      # Fim do ciclo de cancelamento de ordens pendentes
    min_rr: float = 2.0
    sl_buffer_percent: float = 0.001     # 0.1% buffer
    require_daily_bias: bool = False     # Falso por padrão, permitindo alinhar com 1h EMA 200 se neutro
    cooldown_minutes: int = 60
    min_sl_distance_percent: float = 0.005 # 0.5%
    atr_multiplier: float = 1.0          # Displacement para Breaker
    breaker_lookback: int = 50
    range_lookback_5m: int = 288        # 24h range em M5
    enable_ifvg: bool = False            # Habilita o setup Inversion FVG
    require_ema200: bool = True          # Exige alinhamento com a EMA 200 de 5m
    require_smt: bool = False             # Exige confluência SMT Divergência (ETH/BTC)
    require_htf_orderflow: bool = True   # Exige alinhamento com 1h EMA 200 e 15m EMA 50
    require_liquidity_sweep: bool = True # Exige varredura de PDH/PDL ou EQH/EQL
    lookback_sweep: int = 24            # Lookback em candles M5 (2 horas) para o sweep
    displacement_atr_mult: float = 1.5   # Corpo do candle do MSS deve ser >= 1.5 * ATR(14)
    max_sl_percent: float = 0.015        # Rejeitar se SL estrutural for > 1.5%

    def __post_init__(self):
        if self.killzone_macros is None:
            # Janelas de volume institucionais (Londres + Nova York AM)
            self.killzone_macros = [
                (time(2, 0), time(5, 0)),     # London Open
                (time(8, 30), time(11, 30))   # NY AM Session
            ]

class PropFirm2024Crypto(Strategy):
    name = "prop_firm_2024_crypto"
    
    def __init__(self, config: PropFirm2024CryptoConfig = None):
        self.config = config or PropFirm2024CryptoConfig()
        self._last_signal_ts: Optional[datetime] = None
        self.correlated_data: Optional[pd.DataFrame] = None # Injetado pelo engine
        self.correlated_symbol: str = "" # Definido no runner

    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None and str(df.index.tz) in ["America/New_York", "EST5EDT"]:
            return df
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        if df_copy.index.tz is None:
            df_copy.index = df_copy.index.tz_localize("UTC").tz_convert("America/New_York")
        else:
            df_copy.index = df_copy.index.tz_convert("America/New_York")
        return df_copy

    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        if len(candles_1d) < 2:
            return "NEUTRAL"
        last = candles_1d.iloc[-2]
        close = last["close"]
        open_val = last["open"]
        high = last["high"]
        low = last["low"]
        total_range = high - low if high > low else 1.0
        if close > open_val and (high - close) / total_range < 0.3:
            return "BULLISH"
        elif close < open_val and (close - low) / total_range < 0.3:
            return "BEARISH"
        return "NEUTRAL"

    def _check_smt_divergence(self, df_5m: pd.DataFrame, df_corr_5m: pd.DataFrame, direction: str) -> bool:
        """
        Verifica se há divergência SMT (Smart Money Technique) nos wicks recentes.
        BUY: Nosso ativo faz um lower low, mas o correlacionado faz um higher low.
        SELL: Nosso ativo faz um higher high, mas o correlacionado faz um lower high.
        """
        if df_corr_5m is None or len(df_corr_5m) < 10 or len(df_5m) < 10:
            return False

        recent_us = df_5m.iloc[-5:]
        recent_corr = df_corr_5m.iloc[-5:]

        if direction == "BUY":
            prev_us = df_5m.iloc[-10:-5]
            prev_corr = df_corr_5m.iloc[-10:-5]

            us_low1 = prev_us['low'].min()
            us_low2 = recent_us['low'].min()
            corr_low1 = prev_corr['low'].min()
            corr_low2 = recent_corr['low'].min()

            us_made_lower_low = us_low2 < us_low1
            corr_made_lower_low = corr_low2 < corr_low1

            if us_made_lower_low and not corr_made_lower_low:
                return True
            if not us_made_lower_low and corr_made_lower_low:
                return True
        else: # direction == "SELL"
            prev_us = df_5m.iloc[-10:-5]
            prev_corr = df_corr_5m.iloc[-10:-5]

            us_high1 = prev_us['high'].max()
            us_high2 = recent_us['high'].max()
            corr_high1 = prev_corr['high'].max()
            corr_high2 = recent_corr['high'].max()

            us_made_higher_high = us_high2 > us_high1
            corr_made_higher_high = corr_high2 > corr_high1

            if us_made_higher_high and not corr_made_higher_high:
                return True
            if not us_made_higher_high and corr_made_higher_high:
                return True

        return False

    def _in_macro(self, current_time_only: time) -> bool:
        for start, end in self.config.killzone_macros:
            if start <= current_time_only < end:
                return True
        return False

    def _get_24h_range(self, df_5m: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        lookback = self.config.range_lookback_5m
        if len(df_5m) < lookback + 1:
            return None, None
        recent = df_5m.iloc[-(lookback + 1):-1]
        return float(recent["high"].max()), float(recent["low"].min())

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula o ATR(14) de forma otimizada."""
        if len(df) < period + 1:
            return 0.0
        
        df_sliced = df.iloc[-(period + 5):] if len(df) > (period + 5) else df
        
        high = df_sliced['high']
        low = df_sliced['low']
        close = df_sliced['close']
        
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1])

    def _detect_bpr(self, df_5m: pd.DataFrame, idx_sweep: int, idx_mss: int, direction: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Detecta Balanced Price Range (BPR) entre o candle do sweep e o candle do MSS.
        BPR = sobreposição entre FVG bullish e FVG bearish contrárias.
        Retorna (bpr_top, bpr_bottom) ou (None, None).
        """
        if len(df_5m) < 4 or idx_sweep is None or idx_mss is None or idx_sweep > idx_mss:
            return None, None

        n = len(df_5m)
        highs = df_5m['high'].values
        lows = df_5m['low'].values

        bull_fvgs = []
        bear_fvgs = []

        if direction == "BUY":
            # Perna anterior à varredura (baixa): procurar FVG Bearish
            # Permite estender até idx_sweep + 1 para capturar FVG no próprio candle do sweep
            start_bear = max(2, idx_sweep - 15)
            end_bear = min(n, idx_sweep + 2)
            for i in range(start_bear, end_bear):
                if highs[i] < lows[i - 2]:
                    bear_fvgs.append((float(lows[i - 2]), float(highs[i])))

            # Perna de deslocamento subsequente (alta): procurar FVG Bullish
            start_bull = idx_sweep
            end_bull = min(n, idx_mss + 1)
            for i in range(start_bull, end_bull):
                if i >= 2 and lows[i] > highs[i - 2]:
                    bull_fvgs.append((float(lows[i]), float(highs[i - 2])))

            # Procurar sobreposição
            for (bear_top, bear_bot) in bear_fvgs:
                for (bull_top, bull_bot) in bull_fvgs:
                    overlap_top = min(bear_top, bull_top)
                    overlap_bot = max(bear_bot, bull_bot)
                    if overlap_top > overlap_bot:
                        return overlap_top, overlap_bot

        else: # direction == "SELL"
            # Perna anterior à varredura (alta): procurar FVG Bullish
            start_bull = max(2, idx_sweep - 15)
            end_bull = min(n, idx_sweep + 2)
            for i in range(start_bull, end_bull):
                if lows[i] > highs[i - 2]:
                    bull_fvgs.append((float(lows[i]), float(highs[i - 2])))

            # Perna de deslocamento subsequente (baixa): procurar FVG Bearish
            start_bear = idx_sweep
            end_bear = min(n, idx_mss + 1)
            for i in range(start_bear, end_bear):
                if i >= 2 and highs[i] < lows[i - 2]:
                    bear_fvgs.append((float(lows[i - 2]), float(highs[i])))

            # Procurar sobreposição
            for (bull_top, bull_bot) in bull_fvgs:
                for (bear_top, bear_bot) in bear_fvgs:
                    overlap_top = min(bull_top, bear_top)
                    overlap_bot = max(bear_bot, bull_bot)
                    if overlap_top > overlap_bot:
                        return overlap_top, overlap_bot

        return None, None

    def _detect_mss_and_swing(self, df_5m: pd.DataFrame, lookback: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """Detecta swing highs/lows estruturais recentes em 5m."""
        if len(df_5m) < 4:
            return None, None

        highs = df_5m['high'].values
        lows = df_5m['low'].values
        n = len(df_5m)
        start_idx = max(2, n - lookback - 1)

        recent_swing_high = None
        recent_swing_low = None

        for i in range(n - 2, start_idx, -1):
            if recent_swing_high is None:
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    recent_swing_high = float(highs[i])
            if recent_swing_low is None:
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    recent_swing_low = float(lows[i])
            if recent_swing_high is not None and recent_swing_low is not None:
                break

        return recent_swing_high, recent_swing_low

    def _detect_active_fvg(self, df_5m: pd.DataFrame, lookback: int = 15) -> List[Tuple[str, Tuple[float, float], int]]:
        """
        Retorna uma lista de FVGs ativos nos últimos `lookback` candles.
        Cada item da lista é: (fvg_direction, (fvg_top, fvg_bottom), index_of_fvg_candle)
        """
        if len(df_5m) < 4:
            return []
            
        n = len(df_5m)
        start = max(2, n - lookback)
        fvgs = []
        
        for i in range(n - 1, start, -1):
            c_curr = df_5m.iloc[i]
            c_prev2 = df_5m.iloc[i - 2]
            
            # FVG Bullish
            if c_curr['low'] > c_prev2['high']:
                fvg_top = float(c_curr['low'])
                fvg_bottom = float(c_prev2['high'])
                
                # Verificar se já foi totalmente mitigado
                mitigated = False
                for j in range(i + 1, n):
                    if df_5m.iloc[j]['close'] < fvg_bottom:
                        mitigated = True
                        break
                if not mitigated:
                    fvgs.append(("bullish", (fvg_top, fvg_bottom), i))
                    
            # FVG Bearish
            elif c_curr['high'] < c_prev2['low']:
                fvg_top = float(c_prev2['low'])
                fvg_bottom = float(c_curr['high'])
                
                mitigated = False
                for j in range(i + 1, n):
                    if df_5m.iloc[j]['close'] > fvg_top:
                        mitigated = True
                        break
                if not mitigated:
                    fvgs.append(("bearish", (fvg_top, fvg_bottom), i))
                    
        return fvgs

    def _detect_inversion_fvg(self, df_5m: pd.DataFrame, direction: str, lookback: int = 15) -> Optional[Tuple[float, float, float, float, str]]:
        if len(df_5m) < 6:
            return None
            
        n = len(df_5m)
        start = max(2, n - lookback)
        
        highs = df_5m['high'].values
        lows = df_5m['low'].values
        closes = df_5m['close'].values
        current_close = closes[-1]
        
        if direction == "bullish":
            for i in range(n - 3, start, -1):
                if highs[i] < lows[i-2]:
                    fvg_top = float(lows[i-2])
                    fvg_bottom = float(highs[i])
                    for j in range(i + 1, n):
                        if closes[j] > fvg_top:
                            if n - 1 - j <= 2:
                                entry = current_close
                                sl = min(lows[j], fvg_bottom) * (1.0 - self.config.sl_buffer_percent)
                                return entry, sl, fvg_top, fvg_bottom, f"Inversion FVG Bullish: FVG Bearish [{fvg_bottom:.2f}-{fvg_top:.2f}] rompida fresca."
                            break
        else:
            for i in range(n - 3, start, -1):
                if lows[i] > highs[i-2]:
                    fvg_top = float(lows[i])
                    fvg_bottom = float(highs[i-2])
                    for j in range(i + 1, n):
                        if closes[j] < fvg_bottom:
                            if n - 1 - j <= 2:
                                entry = current_close
                                sl = max(highs[j], fvg_top) * (1.0 + self.config.sl_buffer_percent)
                                return entry, sl, fvg_top, fvg_bottom, f"Inversion FVG Bearish: FVG Bullish [{fvg_bottom:.2f}-{fvg_top:.2f}] rompida fresca."
                            break
        return None

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
    ) -> Optional[Signal]:
        self._reset_gates()

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty),
                          None, "dados M5 ou D1 vazios"):
            return None

        df_5m = self._convert_to_est(candles_5m)
        df_1d = self._convert_to_est(candles_1d)
        current_time = df_5m.index[-1]
        current_time_only = current_time.time()
        current_close = float(df_5m.iloc[-1]["close"])

        # GATE 1 — Janelas temporais algorítmicas
        in_macro = self._in_macro(current_time_only)
        if not self._gate("in_algorithmic_macro", in_macro,
                          current_time_only.strftime("%H:%M"),
                          "fora das Macros algoritmicas de NY/Londres"):
            return None

        # GATE 1.5 — Cooldown
        if self._last_signal_ts is not None:
            elapsed = (current_time - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", elapsed >= self.config.cooldown_minutes,
                               f"{elapsed:.0f}min", "cooldown ativo"):
                return None

        # GATE 2 — Daily Bias (PO3)
        bias = self._get_daily_bias(df_1d)
        bias_ok = (not self.config.require_daily_bias) or (bias != "NEUTRAL")
        if not self._gate("bias_not_neutral", bias_ok, bias, "PO3 neutral"):
            return None

        # Calcular EMA 200 no timeframe de 5m
        closes_5m = df_5m['close']
        if len(closes_5m) >= 600:
            ema_200 = closes_5m.iloc[-600:].ewm(span=200, adjust=False).mean().iloc[-1]
        elif len(closes_5m) >= 200:
            ema_200 = closes_5m.ewm(span=200, adjust=False).mean().iloc[-1]
        else:
            ema_200 = closes_5m.mean()

        # Calcular EMA 200 de 1h
        closes_1h = candles_1h['close']
        if len(closes_1h) >= 200:
            ema_200_1h = closes_1h.ewm(span=200, adjust=False).mean().iloc[-1]
        elif len(closes_1h) > 0:
            ema_200_1h = closes_1h.mean()
        else:
            ema_200_1h = current_close

        # Calcular EMA 50 de 15m
        closes_15m = candles_15m['close']
        if len(closes_15m) >= 50:
            ema_50_15m = closes_15m.iloc[-50:].ewm(span=50, adjust=False).mean().iloc[-1]
        elif len(closes_15m) > 0:
            ema_50_15m = closes_15m.ewm(span=50, adjust=False).mean().iloc[-1]
        else:
            ema_50_15m = current_close

        # GATE 2.5 — Alinhamento de Orderflow HTF (EMA 200 1h + EMA 50 15m)
        if self.config.require_htf_orderflow:
            if current_close > ema_200_1h and current_close > ema_50_15m:
                action = "BUY"
            elif current_close < ema_200_1h and current_close < ema_50_15m:
                action = "SELL"
            else:
                if not self._gate("htf_orderflow_aligned", False, f"close={current_close:.2f} ema200_1h={ema_200_1h:.2f} ema50_15m={ema_50_15m:.2f}", "orderflow de 1h/15m não alinhado"):
                    return None
        else:
            if self.config.require_daily_bias and bias != "NEUTRAL":
                action = "BUY" if bias == "BULLISH" else "SELL"
            else:
                action = "BUY" if current_close > ema_200_1h else "SELL"

        # GATE 3 — Filtro de Tendência EMA 200 (5m)
        trend_aligned = (not self.config.require_ema200) or (action == "BUY" and current_close > ema_200) or (action == "SELL" and current_close < ema_200)
        if not self._gate("trend_aligned_ema200", trend_aligned, f"close={current_close:.2f} ema200={ema_200:.2f}", f"Sinal {action} contra a tendência da EMA 200"):
            return None

        # GATE 3.5 — SMT Divergência
        df_corr = self._convert_to_est(self.correlated_data) if self.correlated_data is not None else None
        smt_detected = self._check_smt_divergence(df_5m, df_corr, action)
        if not self._gate("smt_confluence", (not self.config.require_smt) or smt_detected,
                          f"smt={smt_detected}", f"sem divergência SMT com {self.correlated_symbol}"):
            return None

        # GATE 3.8 — Varredura de Liquidez de Alta Qualidade (PDH/PDL ou EQH/EQL)
        pdh, pdl = None, None
        if len(df_1d) >= 2:
            pdh = float(df_1d.iloc[-2]['high'])
            pdl = float(df_1d.iloc[-2]['low'])

        recent_candles = df_5m.iloc[-self.config.lookback_sweep:]
        lowest_low_recent = recent_candles['low'].min()
        highest_high_recent = recent_candles['high'].max()

        # Encontrar a posição do sweep
        if action == "BUY":
            idx_sweep_dt = recent_candles['low'].idxmin()
        else:
            idx_sweep_dt = recent_candles['high'].idxmax()
        idx_sweep_pos = df_5m.index.get_loc(idx_sweep_dt)

        pdl_swept = pdl is not None and lowest_low_recent < pdl and current_close > pdl
        pdh_swept = pdh is not None and highest_high_recent > pdh and current_close < pdh

        eql_swept = False
        eqh_swept = False

        if self.config.require_liquidity_sweep:
            eql_pivots = self._detect_eqh_eql(df_5m, "low", lookback=50)
            if eql_pivots:
                min_eql = min(p[1] for p in eql_pivots)
                eql_swept = lowest_low_recent < min_eql and current_close > min_eql

            eqh_pivots = self._detect_eqh_eql(df_5m, "high", lookback=50)
            if eqh_pivots:
                max_eqh = max(p[1] for p in eqh_pivots)
                eqh_swept = highest_high_recent > max_eqh and current_close < max_eqh

            sweep_ok = (action == "BUY" and (pdl_swept or eql_swept)) or (action == "SELL" and (pdh_swept or eqh_swept))
            if not self._gate("liquidity_sweep_confirmed", sweep_ok, f"action={action} pdl_swept={pdl_swept} eql_swept={eql_swept} pdh_swept={pdh_swept} eqh_swept={eqh_swept}", "sem varredura de liquidez de alta qualidade recente"):
                return None

        # GATE 4 — MSS e Deslocamento Consistente (Displacement)
        recent_swing_high, recent_swing_low = self._detect_mss_and_swing(df_5m, lookback=20)
        
        mss_confirmed = (action == "BUY" and recent_swing_high is not None and current_close > recent_swing_high) or \
                        (action == "SELL" and recent_swing_low is not None and current_close < recent_swing_low)
        
        if not self._gate("mss_confirmed", mss_confirmed, f"action={action} swing_high={recent_swing_high} swing_low={recent_swing_low}", "MSS não confirmado pelo preço atual"):
            return None

        atr = self._calculate_atr(df_5m, period=14)
        curr_candle = df_5m.iloc[-1]
        body_size = abs(curr_candle['close'] - curr_candle['open'])
        displacement_ok = body_size >= self.config.displacement_atr_mult * atr if atr > 0 else True
        
        if not self._gate("displacement_confirmed", displacement_ok, f"body={body_size:.2f} target_atr={self.config.displacement_atr_mult * atr:.2f}", "rompimento sem volume institucional suficiente (Displacement)"):
            return None

        # Fechamento perto do extremo
        if action == "BUY":
            close_near_extreme = (curr_candle['high'] - curr_candle['close']) / (curr_candle['high'] - curr_candle['low'] + 1e-6) < 0.25
        else:
            close_near_extreme = (curr_candle['close'] - curr_candle['low']) / (curr_candle['high'] - curr_candle['low'] + 1e-6) < 0.25
            
        if not self._gate("close_near_extreme", close_near_extreme, None, "fechamento do candle de rompimento deixou sombra contrária muito longa"):
            return None

        # GATE 5 — Gatilhos de Entrada (BPR -> Unicorn -> FVG -> IFVG)
        entry_price, sl_price, reason_str, setup_type = None, None, "", ""
        asian_range = self._get_asian_range(df_5m, current_time)
        range_24h = self._get_24h_range(df_5m)

        # 1. BPR Check
        bpr_top, bpr_bot = self._detect_bpr(df_5m, idx_sweep_pos, len(df_5m) - 1, action)
        if bpr_top is not None:
            entry_price = (bpr_top + bpr_bot) / 2.0
            if action == "BUY":
                sl_price = lowest_low_recent - (self.config.sl_buffer_percent * entry_price)
            else:
                sl_price = highest_high_recent + (self.config.sl_buffer_percent * entry_price)
            setup_type = "bpr"
            reason_str = f"BPR Setup {action} (BPR [{bpr_bot:.2f}-{bpr_top:.2f}] Overlap)."
        
        # 2. Unicorn Check (Fallback 1)
        if entry_price is None:
            breaker_dir = "bullish" if action == "BUY" else "bearish"
            bb = self._detect_breaker_block(df_5m, breaker_dir,
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier,
                                            asian_range=asian_range,
                                            range_24h=range_24h)
            if bb is not None:
                active_fvgs = self._detect_active_fvg(df_5m, lookback=15)
                for fvg_dir, (fvg_top, fvg_bot), fvg_idx in active_fvgs:
                    if fvg_dir == breaker_dir:
                        b_high, b_low = bb["zone_high"], bb["zone_low"]
                        overlap_top = min(fvg_top, b_high)
                        overlap_bot = max(fvg_bot, b_low)
                        if overlap_top > overlap_bot:
                            entry_price = (overlap_top + overlap_bot) / 2.0
                            if action == "BUY":
                                sl_price = bb.get("swing_low", b_low) * (1.0 - self.config.sl_buffer_percent)
                            else:
                                sl_price = bb.get("swing_high", b_high) * (1.0 + self.config.sl_buffer_percent)
                            setup_type = "unicorn"
                            reason_str = f"Unicorn Setup {action} (Breaker [{b_low:.2f}-{b_high:.2f}] + FVG overlap)."
                            break

        # 3. FVG Check (Fallback 2)
        if entry_price is None:
            active_fvgs = self._detect_active_fvg(df_5m, lookback=15)
            fvg_dir_target = "bullish" if action == "BUY" else "bearish"
            for fvg_dir, (fvg_top, fvg_bot), fvg_idx in active_fvgs:
                if fvg_dir == fvg_dir_target:
                    entry_price = (fvg_top + fvg_bot) / 2.0
                    if action == "BUY":
                        sl_price = lowest_low_recent - (self.config.sl_buffer_percent * entry_price)
                    else:
                        sl_price = highest_high_recent + (self.config.sl_buffer_percent * entry_price)
                    setup_type = "fvg"
                    reason_str = f"FVG Setup {action} (FVG CE [{(fvg_top + fvg_bot)/2.0:.2f}])."
                    break

        # 4. IFVG Check (Fallback 3)
        if entry_price is None and self.config.enable_ifvg:
            ifvg = self._detect_inversion_fvg(df_5m, "bullish" if action == "BUY" else "bearish", lookback=15)
            if ifvg is not None:
                entry_price, sl_price, fvg_top, fvg_bottom, ifvg_reason = ifvg
                setup_type = "ifvg"
                reason_str = ifvg_reason

        # Se nenhum setup de entrada foi qualificado
        if entry_price is None or sl_price is None:
            if not self._gate("setup_trigger_found", False, None, "nenhum gatilho de entrada (BPR, Unicorn, FVG, IFVG) qualificado"):
                return None

        # GATE 6 — Validação do Tamanho do Stop Loss (Max SL %)
        sl_dist = abs(entry_price - sl_price)
        sl_percent = sl_dist / entry_price
        if sl_percent > self.config.max_sl_percent:
            if not self._gate("max_sl_passed", False, f"sl_percent={sl_percent:.3f}", f"Stop Loss muito longo ({sl_percent*100:.2f}% > {self.config.max_sl_percent*100:.2f}%)"):
                return None

        # Validar distância mínima de SL
        min_sl = entry_price * self.config.min_sl_distance_percent
        if sl_dist < min_sl:
            if action == "BUY":
                sl_price = entry_price - min_sl
            else:
                sl_price = entry_price + min_sl
            sl_dist = min_sl

        # GATE 7 — Projeção do Take Profit (DOL) & Relação R:R
        if action == "BUY":
            dol = self._detect_dynamic_dol(candles_15m, "BUY", entry_price, lookback=50)
            min_tp = entry_price + sl_dist * self.config.min_rr
            take_profit = max(dol, min_tp) if (dol is not None and dol > entry_price) else min_tp
        else:
            dol = self._detect_dynamic_dol(candles_15m, "SELL", entry_price, lookback=50)
            min_tp = entry_price - sl_dist * self.config.min_rr
            take_profit = min(dol, min_tp) if (dol is not None and dol < entry_price) else min_tp

        rr = abs(take_profit - entry_price) / sl_dist if sl_dist > 0 else 0.0
        if not self._gate("min_rr_passed", rr >= self.config.min_rr, f"RR={rr:.2f}", f"R:R abaixo de {self.config.min_rr}"):
            return None

        self._gate("signal_generated", True, action, f"setup {setup_type} confirmado")
        self._last_signal_ts = current_time

        full_reason = f"{reason_str} MSS confirmado com displacement. HTF alinhado. DOL={take_profit:.2f} SL={sl_price:.2f} RR={rr:.2f}"

        return Signal(
            symbol=self.symbol,
            action=action,
            entry_price=round(entry_price, 2),
            stop_loss=round(sl_price, 2),
            take_profit=round(take_profit, 2),
            confidence_score=0.96,
            reasoning=full_reason,
            timestamp=current_time.to_pydatetime()
        )
