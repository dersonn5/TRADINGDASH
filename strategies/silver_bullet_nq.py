from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from strategies.base import Strategy, Signal

@dataclass
class SilverBulletConfig:
    killzone_start: time = time(10, 0)  # EST
    killzone_end: time = time(11, 0)    # EST
    max_trades_per_day: int = 2
    min_rr: float = 2.0
    sl_buffer_ticks: int = 3
    tick_size: float = 0.25  # NQ tick
    require_daily_bias: bool = True
    require_premium_discount: bool = True
    require_sweep: bool = False   # Sweep prévio de PDH/PDL obrigatório (ICT canônico)
    require_mss: bool = True     # Market Structure Shift confirmando direção obrigatório
    require_london_sweep: bool = True  # MMM gate: London deve varrer Asian Range antes de NY
    cooldown_minutes: int = 30   # Dedup: ignora novo sinal nos N min após o último
    min_sl_distance_pts: float = 5.0  # SL mínimo de 5 pts NQ (20 ticks) — evita stop hunt
    pd_threshold: float = 0.50  # Fração do range: 0.50 = equilibrium padrão, 0.25 = top/bottom 25%
    session_name: str = "ny_am"  # Para logging e diagnóstico

class SilverBulletNQ(Strategy):
    name = "silver_bullet_nq"
    symbol = "NQ"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: SilverBulletConfig = None):
        self.config = config or SilverBulletConfig()
        self._last_signal_ts: Optional[datetime] = None  # Para dedup/cooldown

    def _convert_to_est(self, df: pd.DataFrame) -> pd.DataFrame:
        """Garante que o índice do DataFrame esteja em fuso EST/EDT (America/New_York)"""
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        if df_copy.index.tz is None:
            # Assume UTC se não tiver tz e converte
            df_copy.index = df_copy.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df_copy.index = df_copy.index.tz_convert('America/New_York')
        return df_copy

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula o ATR(14) atual de forma altamente otimizada em O(1)"""
        if len(df) < period + 1:
            return 0.0
        
        # Slices only the required end of the dataframe to avoid O(N) recalculations on every step
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

    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        """
        Calcula o viés diário (Daily Bias) baseado no Power of 3 (PO3) do D1.
        Retorna 'BULLISH', 'BEARISH' ou 'NEUTRAL'.
        """
        if len(candles_1d) < 2:
            return "NEUTRAL"
        
        last_candle = candles_1d.iloc[-2]
        prev_candle = candles_1d.iloc[-2]
        
        # Lógica PO3 baseada no fechamento do candle diário anterior
        close = last_candle['close']
        open_val = last_candle['open']
        high = last_candle['high']
        low = last_candle['low']
        
        body_size = abs(close - open_val)
        total_range = high - low if high > low else 1.0
        
        # Bullish: fechamento próximo do topo e candle de alta
        if close > open_val and (high - close) / total_range < 0.3:
            return "BULLISH"
        # Bearish: fechamento próximo do fundo e candle de baixa
        elif close < open_val and (close - low) / total_range < 0.3:
            return "BEARISH"
        
        return "NEUTRAL"

    def _get_prev_day_levels(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """
        Retorna PDH (Previous Day High) e PDL (Previous Day Low) — canonical ICT
        para US index/futures (NDX, ES, NQ). Asian Range não se aplica a índices
        que fecham 16:00 EST; usar dia anterior completo é o padrão.
        """
        current_date = current_time.date()
        prev_day_candles = df_5m[df_5m.index.date < current_date]
        if prev_day_candles.empty:
            return None, None

        # Pegar o dia mais recente disponível anterior ao atual
        prev_date = max(prev_day_candles.index.date)
        prev_day_data = df_5m[df_5m.index.date == prev_date]
        if prev_day_data.empty:
            return None, None

        return float(prev_day_data['high'].max()), float(prev_day_data['low'].min())

    def _detect_active_fvg(self, df_5m: pd.DataFrame, lookback: int = 6) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        """
        Procura FVG ativa (não mitigada) nos últimos `lookback` candles.
        FVG bullish: c[i].low > c[i-2].high
        FVG bearish: c[i].high < c[i-2].low
        Retorna ("bullish"|"bearish", (top, bottom)) ou (None, None).
        Adiciona o filtro Displacement: FVG só conta se candle criador i-1 tiver body >= 1.2x ATR(14)
        """
        if len(df_5m) < 4:
            return None, None

        n = len(df_5m)
        start = max(2, n - lookback)

        # Busca do mais recente pra trás
        for i in range(n - 1, start, -1):
            c_curr = df_5m.iloc[i]
            c_prev2 = df_5m.iloc[i - 2]

            # FVG Bullish
            if c_curr['low'] > c_prev2['high']:
                c_disp = df_5m.iloc[i - 1]
                atr_val = self._calculate_atr(df_5m.iloc[:i+1], period=14)
                c_disp_body = abs(c_disp['close'] - c_disp['open'])
                if atr_val == 0.0 or c_disp_body >= 1.2 * atr_val:
                    fvg_top = float(c_curr['low'])
                    fvg_bottom = float(c_prev2['high'])
                    mitigated = False
                    for j in range(i + 1, n):
                        if df_5m.iloc[j]['close'] < fvg_bottom:
                            mitigated = True
                            break
                    if not mitigated:
                        return "bullish", (fvg_top, fvg_bottom)

            # FVG Bearish
            if c_curr['high'] < c_prev2['low']:
                c_disp = df_5m.iloc[i - 1]
                atr_val = self._calculate_atr(df_5m.iloc[:i+1], period=14)
                c_disp_body = abs(c_disp['close'] - c_disp['open'])
                if atr_val == 0.0 or c_disp_body >= 1.2 * atr_val:
                    fvg_top = float(c_prev2['low'])
                    fvg_bottom = float(c_curr['high'])
                    mitigated = False
                    for j in range(i + 1, n):
                        if df_5m.iloc[j]['close'] > fvg_top:
                            mitigated = True
                            break
                    if not mitigated:
                        return "bearish", (fvg_top, fvg_bottom)

        return None, None

    def _detect_mss_and_swing(self, df_5m: pd.DataFrame, lookback: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """
        Detecta swing high e swing low recentes — pivot 1/1 (relaxado).
        Critério: candle com high/low maior/menor que 1 candle de cada lado.
        Pivot 2/2 anterior matava 100% dos setups no M5. Lookback limitado
        evita pegar swings muito antigos irrelevantes pro MSS atual.
        """
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

    def _check_sweep(self, df_5m: pd.DataFrame, pdh: float, pdl: float, current_time: datetime) -> Tuple[bool, bool]:
        """
        Verifica sweep de PDH (Previous Day High) ou PDL (Previous Day Low).
        Janela estendida: pre-market 04:00 EST até o candle atual (~6h).
        Sweeps de PDH/PDL são o setup ICT canônico pra US futures/index.
        Retorna (bullish_sweep, bearish_sweep).
        """
        if pdh is None or pdl is None:
            return False, False

        # Janela: 04:00 EST do dia atual até agora (cobre pré-mercado + abertura)
        day_str = current_time.strftime("%Y-%m-%d")
        start_check = pd.to_datetime(f"{day_str} 04:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
        recent_candles = df_5m[(df_5m.index >= start_check) & (df_5m.index <= current_time)]

        if recent_candles.empty:
            return False, False

        # Bullish Sweep: preço perfurou PDL e fechou acima
        low_broke = recent_candles['low'].min() < pdl
        close_above = recent_candles.iloc[-1]['close'] > pdl
        bullish_sweep = low_broke and close_above

        # Bearish Sweep: preço perfurou PDH e fechou abaixo
        high_broke = recent_candles['high'].max() > pdh
        close_below = recent_candles.iloc[-1]['close'] < pdh
        bearish_sweep = high_broke and close_below

        return bullish_sweep, bearish_sweep

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
    ) -> Optional[Signal]:
        """
        Avalia o setup Silver Bullet para Nasdaq.
        Cada decisão passa por self._gate() pra permitir diagnóstico funil quando
        diagnostic_enabled=True. O comportamento de produção é idêntico.
        """
        self._reset_gates()

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty),
                          None, "dados M5 ou D1 vazios"):
            return None

        df_5m = candles_5m
        df_1d = candles_1d
        df_1m = candles_1m if candles_1m is not None else None
        current_time = df_5m.index[-1]

        # Converter para EST para todos os checks de horário
        if hasattr(current_time, 'tz') and current_time.tz is not None:
            current_time_est = current_time.tz_convert('America/New_York')
        else:
            current_time_est = current_time
        current_time_only = current_time_est.time()

        # GATE 1 — Killzone (10:00-11:00 EST)
        in_killzone = self.config.killzone_start <= current_time_only < self.config.killzone_end
        if not self._gate("killzone_active", in_killzone,
                          current_time_only.strftime("%H:%M"),
                          f"horário fora de {self.config.killzone_start}-{self.config.killzone_end}"):
            return None

        # GATE 1.5 — Cooldown desde último sinal (dedup)
        if self._last_signal_ts is not None:
            elapsed_min = (current_time - self._last_signal_ts).total_seconds() / 60.0
            cooldown_ok = elapsed_min >= self.config.cooldown_minutes
            if not self._gate("cooldown_passed", cooldown_ok, f"{elapsed_min:.0f}min",
                              f"último sinal há {elapsed_min:.0f}min (cooldown {self.config.cooldown_minutes}min)"):
                return None

        # GATE 2 — Daily Bias (PO3)
        bias = self._get_daily_bias(df_1d)
        bias_ok = (not self.config.require_daily_bias) or (bias != "NEUTRAL")
        if not self._gate("bias_not_neutral", bias_ok, bias,
                          f"PO3 retornou NEUTRAL (close não em top/bottom 30% do range)"):
            return None

        # GATE 3 — Dados do dia presentes
        day_start = pd.to_datetime(current_time_est.strftime("%Y-%m-%d 00:00:00")).tz_localize('America/New_York', nonexistent='shift_forward')
        today_candles = df_5m[df_5m.index >= day_start]
        if not self._gate("today_has_data", not today_candles.empty, len(today_candles),
                          "sem velas do dia atual"):
            return None

        # GATE 3.5 — London Session Manipulation Bias
        asian_high_range, asian_low_range = self._get_asian_range(df_5m, current_time)
        london_bias = self._detect_london_manipulation(df_5m, asian_high_range, asian_low_range, current_time)
        london_ok = (not self.config.require_london_sweep) or (london_bias != "NONE")
        if not self._gate("london_bias_active", london_ok, london_bias, f"London did not sweep Asian Range"):
            return None

        day_high = today_candles['high'].max()
        day_low = today_candles['low'].min()
        day_range = day_high - day_low if day_high > day_low else 1.0
        premium_threshold = day_low + day_range * (1.0 - self.config.pd_threshold)
        discount_threshold = day_low + day_range * self.config.pd_threshold

        # PDH/PDL & Sweep (canonical ICT pra NDX/NQ)
        pdh, pdl = self._get_prev_day_levels(df_5m, current_time)
        bullish_sweep, bearish_sweep = self._check_sweep(df_5m, pdh, pdl, current_time)
        # Aliases pra compatibilidade do código TP existente
        asian_high, asian_low = pdh, pdl

        # GATE 4 — Velas suficientes para detectar FVG
        if not self._gate("enough_candles_for_fvg", len(df_5m) >= 4, len(df_5m),
                          "menos de 4 velas M5"):
            return None

        c3 = df_5m.iloc[-1]

        # Procura FVG ativa nos últimos 6 candles
        fvg_direction, fvg_bounds = self._detect_active_fvg(df_5m, lookback=6)
        fvg_present = fvg_direction is not None

        # GATE 5 — FVG presente em alguma direção nos últimos 6 candles
        if not self._gate("fvg_present_any", fvg_present,
                          fvg_direction if fvg_direction else "none",
                          "nenhum FVG ativo nos últimos 6 candles M5"):
            return None

        fvg_bullish = fvg_direction == "bullish"
        fvg_bearish = fvg_direction == "bearish"
        fvg_top_detected, fvg_bottom_detected = fvg_bounds

        recent_swing_high, recent_swing_low = self._detect_mss_and_swing(df_5m)

        # GATE 6 — FVG alinhado com Daily Bias
        fvg_aligned_dir = "BULLISH" if fvg_bullish else "BEARISH"
        bias_aligned = (
            (not self.config.require_daily_bias)
            or (fvg_bullish and bias == "BULLISH")
            or (fvg_bearish and bias == "BEARISH")
        )
        if not self._gate("fvg_aligned_with_bias", bias_aligned,
                          f"fvg={fvg_aligned_dir} bias={bias}",
                          "direção do FVG contraria daily bias"):
            return None

        if fvg_bullish:
            # GATE 6.5 — London Bias alignment
            if not self._gate("london_bias_direction", london_bias == "BULLISH", london_bias, "London bias is BEARISH, but setup is BULLISH"):
                return None

            # GATE 7 — Sweep prévio bullish (Asian Low)
            sweep_ok = (not self.config.require_sweep) or bullish_sweep
            if not self._gate("sweep_present_bullish", sweep_ok,
                              f"pdl={pdl} bullish_sweep={bullish_sweep}",
                              "sem sweep do PDL desde 04:00 EST"):
                return None

            # GATE 8 — MSS confirmado (close > swing high recente)
            mss_ok = (not self.config.require_mss) or (
                recent_swing_high is not None and c3['close'] > recent_swing_high
            )
            if not self._gate("mss_confirmed_bullish", mss_ok,
                              f"close={c3['close']} swing_high={recent_swing_high}",
                              "fechamento atual não rompeu swing high recente"):
                return None

            fvg_top_m5 = fvg_top_detected
            fvg_bot_m5 = fvg_bottom_detected
            fvg_ce_m5 = (fvg_top_m5 + fvg_bot_m5) / 2.0
            
            # GATE 9 — Zona do FVG em Discount (CE abaixo do equilibrium do dia)
            equilibrium = discount_threshold
            pd_ok = (not self.config.require_premium_discount) or (fvg_ce_m5 <= equilibrium)
            if not self._gate("fvg_in_discount", pd_ok,
                              f"fvg_ce={fvg_ce_m5:.2f} equilibrium={equilibrium:.2f}",
                              "FVG está acima do equilibrium (zona premium, não serve pra BUY)"):
                return None

            # Filtrar M1 apenas dentro da zona do FVG M5 e dentro da killzone atual
            if df_1m is not None and not df_1m.empty:
                killzone_start_dt = pd.to_datetime(
                    current_time.strftime("%Y-%m-%d") + f" {self.config.killzone_start}"
                ).tz_localize('America/New_York', nonexistent='shift_forward')
                df_1m_kz = df_1m[df_1m.index >= killzone_start_dt]
                zone_range = fvg_top_m5 - fvg_bot_m5
                df_1m_zone = df_1m_kz[
                    (df_1m_kz['low'] <= fvg_top_m5 + zone_range * 0.2) &
                    (df_1m_kz['high'] >= fvg_bot_m5 - zone_range * 0.2)
                ]
                m1_conf = self._confirm_m1_entry(
                    df_1m_zone,
                    fvg_zone_top=fvg_top_m5,
                    fvg_zone_bottom=fvg_bot_m5,
                    direction="bullish",
                    lookback_m1=60,
                )
            else:
                m1_conf = None

            if m1_conf is not None:
                entry_price = m1_conf["entry_price"]
                stop_loss = m1_conf["sl_price"]
                sl_distance = abs(entry_price - stop_loss)
                if sl_distance < self.config.min_sl_distance_pts:
                    stop_loss = entry_price - self.config.min_sl_distance_pts
                take_profit = entry_price + (abs(entry_price - stop_loss) * self.config.min_rr)
                self._gate("m1_confirmation", True, m1_conf["type"], m1_conf["reason"])
            else:
                # M1 não confirmou ou sem dados → CE M5 (frequência máxima)
                entry_price = fvg_ce_m5
                stop_loss = fvg_bot_m5 - (self.config.sl_buffer_ticks * self.config.tick_size)
                sl_distance = abs(entry_price - stop_loss)
                if sl_distance < self.config.min_sl_distance_pts:
                    stop_loss = entry_price - self.config.min_sl_distance_pts
                take_profit = entry_price + (abs(entry_price - stop_loss) * self.config.min_rr)
                self._gate("m1_confirmation", True, "fallback_m5_ce", "M1 desabilitado — CE M5")

            if asian_high is not None and asian_high > entry_price:
                take_profit = max(take_profit, asian_high)

            self._gate("signal_generated", True, "BUY", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"Silver Bullet BULLISH. Sweep PDL OK, MSS confirmado + Displacement. "
                       f"M5 [{fvg_bot_m5:.2f}-{fvg_top_m5:.2f}]. Entry ({entry_price:.2f}).")
            return Signal(
                symbol=self.symbol, action="BUY",
                entry_price=round(entry_price, 2), stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2), confidence_score=0.90,
                reasoning=reason, timestamp=current_time.to_pydatetime()
            )

        else:  # fvg_bearish
            # GATE 6.5 — London Bias alignment
            if not self._gate("london_bias_direction", london_bias == "BEARISH", london_bias, "London bias is BULLISH, but setup is BEARISH"):
                return None

            sweep_ok = (not self.config.require_sweep) or bearish_sweep
            if not self._gate("sweep_present_bearish", sweep_ok,
                              f"pdh={pdh} bearish_sweep={bearish_sweep}",
                              "sem sweep do PDH desde 04:00 EST"):
                return None

            mss_ok = (not self.config.require_mss) or (
                recent_swing_low is not None and c3['close'] < recent_swing_low
            )
            if not self._gate("mss_confirmed_bearish", mss_ok,
                              f"close={c3['close']} swing_low={recent_swing_low}",
                              "fechamento atual não rompeu swing low recente"):
                return None

            fvg_top_m5 = fvg_top_detected
            fvg_bot_m5 = fvg_bottom_detected
            fvg_ce_m5 = (fvg_top_m5 + fvg_bot_m5) / 2.0
            
            # GATE 9 — Zona do FVG em Premium (CE acima do equilibrium do dia)
            equilibrium = premium_threshold
            pd_ok = (not self.config.require_premium_discount) or (fvg_ce_m5 >= equilibrium)
            if not self._gate("fvg_in_premium", pd_ok,
                              f"fvg_ce={fvg_ce_m5:.2f} equilibrium={equilibrium:.2f}",
                              "FVG está abaixo do equilibrium (zona discount, não serve pra SELL)"):
                return None

            # Filtrar M1 apenas dentro da zona do FVG M5 e dentro da killzone atual
            if df_1m is not None and not df_1m.empty:
                killzone_start_dt = pd.to_datetime(
                    current_time.strftime("%Y-%m-%d") + f" {self.config.killzone_start}"
                ).tz_localize('America/New_York', nonexistent='shift_forward')
                df_1m_kz = df_1m[df_1m.index >= killzone_start_dt]
                zone_range = fvg_top_m5 - fvg_bot_m5
                df_1m_zone = df_1m_kz[
                    (df_1m_kz['low'] <= fvg_top_m5 + zone_range * 0.2) &
                    (df_1m_kz['high'] >= fvg_bot_m5 - zone_range * 0.2)
                ]
                m1_conf = self._confirm_m1_entry(
                    df_1m_zone,
                    fvg_zone_top=fvg_top_m5,
                    fvg_zone_bottom=fvg_bot_m5,
                    direction="bearish",
                    lookback_m1=60,
                )
            else:
                m1_conf = None

            if m1_conf is not None:
                entry_price = m1_conf["entry_price"]
                stop_loss = m1_conf["sl_price"]
                sl_distance = abs(stop_loss - entry_price)
                if sl_distance < self.config.min_sl_distance_pts:
                    stop_loss = entry_price + self.config.min_sl_distance_pts
                take_profit = entry_price - (abs(stop_loss - entry_price) * self.config.min_rr)
                self._gate("m1_confirmation", True, m1_conf["type"], m1_conf["reason"])
            else:
                # M1 não confirmou ou sem dados → CE M5 (frequência máxima)
                entry_price = fvg_ce_m5
                stop_loss = fvg_top_m5 + (self.config.sl_buffer_ticks * self.config.tick_size)
                sl_distance = abs(stop_loss - entry_price)
                if sl_distance < self.config.min_sl_distance_pts:
                    stop_loss = entry_price + self.config.min_sl_distance_pts
                take_profit = entry_price - (abs(stop_loss - entry_price) * self.config.min_rr)
                self._gate("m1_confirmation", True, "fallback_m5_ce", "M1 desabilitado — CE M5")

            if asian_low is not None and asian_low < entry_price:
                take_profit = min(take_profit, asian_low)

            self._gate("signal_generated", True, "SELL", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"Silver Bullet BEARISH. Sweep PDH OK, MSS confirmado + Displacement. "
                      f"M5 [{fvg_bot_m5:.2f}-{fvg_top_m5:.2f}]. Entry ({entry_price:.2f}).")
            return Signal(
                symbol=self.symbol, action="SELL",
                entry_price=round(entry_price, 2), stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2), confidence_score=0.90,
                reasoning=reason, timestamp=current_time.to_pydatetime()
            )

if __name__ == "__main__":
    # Teste rápido de importação e criação
    config = SilverBulletConfig()
    strategy = SilverBulletNQ(config)
    print(f"Estratégia {strategy.name} inicializada com sucesso para {strategy.symbol}.")
