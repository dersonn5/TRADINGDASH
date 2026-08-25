from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
from strategies.base import Strategy, Signal

@dataclass
class LondonSweepNQConfig:
    killzone_start: time = time(2, 0)   # EST
    killzone_end: time = time(5, 0)     # EST
    max_trades_per_day: int = 1
    min_rr: float = 2.0
    sl_buffer_ticks: int = 3            # 3 ticks = 0.75 pts NQ
    tick_size: float = 0.25             # NQ tick = 0.25
    require_daily_bias: bool = True
    cooldown_minutes: int = 30          # Dedup: ignora novo sinal nos N min após o último
    min_sl_distance_pts: float = 8.0    # SL mínimo 8 pts NQ — evita stop hunt

class LondonSweepNQ(Strategy):
    name = "london_sweep_nq"
    symbol = "NQ"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: LondonSweepNQConfig = None):
        self.config = config or LondonSweepNQConfig()
        self._last_signal_ts: Optional[datetime] = None  # Para dedup/cooldown

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

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcula o ATR(14) atual para fins de deslocamento (displacement)"""
        if len(df) < period + 1:
            return 0.0
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1])

    def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
        """
        Calcula o viés diário (Daily Bias) baseado no Power of 3 (PO3) do D1.
        """
        if len(candles_1d) < 2:
            return "NEUTRAL"
        
        last_candle = candles_1d.iloc[-2]
        close = last_candle['close']
        open_val = last_candle['open']
        high = last_candle['high']
        low = last_candle['low']
        
        total_range = high - low if high > low else 1.0
        
        # Bullish: fechamento próximo do topo e candle de alta
        if close > open_val and (high - close) / total_range < 0.35:
            return "BULLISH"
        # Bearish: fechamento próximo do fundo e candle de baixa
        elif close < open_val and (close - low) / total_range < 0.35:
            return "BEARISH"
        
        return "NEUTRAL"

    def _get_prev_day_levels(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """
        Retorna PDH (Previous Day High) e PDL (Previous Day Low) para NQ.
        """
        current_date = current_time.date()
        prev_day_candles = df_5m[df_5m.index.date < current_date]
        if prev_day_candles.empty:
            return None, None

        prev_date = max(prev_day_candles.index.date)
        prev_day_data = df_5m[df_5m.index.date == prev_date]
        if prev_day_data.empty:
            return None, None

        return float(prev_day_data['high'].max()), float(prev_day_data['low'].min())

    def _detect_mss_and_swing(self, df_5m: pd.DataFrame, lookback: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """
        Detecta swing high e swing low recentes — pivot 1/1 (relaxado).
        Critério: candle com high/low maior/menor que 1 candle de cada lado.
        Lookback limitado pra evitar pegar swings muito antigos.
        """
        if len(df_5m) < 4:
            return None, None

        highs = df_5m['high'].values
        lows = df_5m['low'].values
        n = len(df_5m)
        start_idx = max(2, n - lookback - 1)

        recent_swing_high = None
        recent_swing_low = None

        # Busca reversa do swing mais recente (pivot 1/1)
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

    def _detect_active_fvg(self, df_5m: pd.DataFrame, lookback: int = 12) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        """
        Procura FVG ativa (não mitigada) nos últimos `lookback` candles.
        FVG bullish: c[i].low > c[i-2].high
        FVG bearish: c[i].high < c[i-2].low
        Retorna ("bullish"|"bearish", (top, bottom)) ou (None, None).
        Adiciona o filtro Displacement: FVG só conta se candle criador i-1 tiver body >= 1.5x ATR(14)
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

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
        candles_1m: pd.DataFrame = None,
    ) -> Optional[Signal]:
        """
        Avalia o setup London Sweep para Nasdaq (NQ/NDX).
        """
        self._reset_gates()

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty),
                           None, "dados M5 ou D1 vazios"):
            return None

        df_5m = self._convert_to_est(candles_5m)
        df_1d = self._convert_to_est(candles_1d)
        df_1m = self._convert_to_est(candles_1m) if (candles_1m is not None and not candles_1m.empty) else None
        current_time = df_5m.index[-1]
        current_time_only = current_time.time()

        # GATE 1 — Killzone London Open (02:00-05:00 EST)
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
                          "PO3 retornou NEUTRAL (close não em top/bottom 35% do range)"):
            return None

        # GATE 3 — PDH e PDL válidos (NQ usa PDH/PDL em vez de Asian Range)
        pdh, pdl = self._get_prev_day_levels(df_5m, current_time)
        pdh_pdl_ok = pdh is not None and pdl is not None
        if not self._gate("pdh_pdl_valid", pdh_pdl_ok,
                          f"pdh={pdh} pdl={pdl}",
                          "sem níveis prévios do PDH/PDL detectados"):
            return None

        # GATE 4 — Velas presentes na killzone
        killzone_start_dt = pd.to_datetime(current_time.strftime(f"%Y-%m-%d {self.config.killzone_start}")).tz_localize('America/New_York')
        killzone_candles = df_5m[df_5m.index >= killzone_start_dt]
        if not self._gate("killzone_has_candles", not killzone_candles.empty, len(killzone_candles),
                          "sem velas dentro da killzone atual"):
            return None

        lowest_low = killzone_candles['low'].min()
        highest_high = killzone_candles['high'].max()

        bullish_sweep = lowest_low < pdl and killzone_candles.iloc[-1]['close'] > pdl
        bearish_sweep = highest_high > pdh and killzone_candles.iloc[-1]['close'] < pdh

        # GATE 5 — Velas suficientes para FVG
        if not self._gate("enough_candles_for_fvg", len(df_5m) >= 4, len(df_5m),
                          "menos de 4 velas M5"):
            return None

        # GATE 6 — FVG ativa em janela de 12 candles
        fvg_direction, fvg_bounds = self._detect_active_fvg(df_5m, lookback=12)
        fvg_present = fvg_direction is not None
        if not self._gate("fvg_present_any", fvg_present,
                          fvg_direction if fvg_direction else "none",
                          "nenhum FVG ativo nos últimos 12 candles M5"):
            return None

        c3 = df_5m.iloc[-1]
        fvg_bullish = fvg_direction == "bullish"
        fvg_bearish = fvg_direction == "bearish"
        fvg_top_detected, fvg_bottom_detected = fvg_bounds

        recent_swing_high, recent_swing_low = self._detect_mss_and_swing(df_5m)

        # GATE 7 — Sweep + FVG + Bias alinhados
        is_bullish_setup = bullish_sweep and fvg_bullish and (
            (not self.config.require_daily_bias) or bias == "BULLISH"
        )
        is_bearish_setup = bearish_sweep and fvg_bearish and (
            (not self.config.require_daily_bias) or bias == "BEARISH"
        )

        if not self._gate("setup_combo_valid", is_bullish_setup or is_bearish_setup,
                          f"sweep(bull={bullish_sweep},bear={bearish_sweep}) "
                          f"fvg(bull={fvg_bullish},bear={fvg_bearish}) bias={bias}",
                          "sweep + FVG + bias não alinharam na mesma direção"):
            return None

        if is_bullish_setup:
            mss_ok = recent_swing_high is not None and c3['close'] > recent_swing_high
            if not self._gate("mss_confirmed_bullish", mss_ok,
                              f"close={c3['close']} swing_high={recent_swing_high}",
                              "fechamento atual não rompeu swing high recente"):
                return None
            
            fvg_top_m5 = fvg_top_detected
            fvg_bot_m5 = fvg_bottom_detected
            fvg_ce_m5 = (fvg_top_m5 + fvg_bot_m5) / 2.0
            
            # Filtrar M1 apenas dentro da zona do FVG M5 e dentro da killzone atual
            if df_1m is not None and not df_1m.empty:
                killzone_start_dt = pd.to_datetime(
                    current_time.strftime("%Y-%m-%d") + f" {self.config.killzone_start}"
                ).tz_localize('America/New_York')
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
                m1_reason = m1_conf["reason"]
                self._gate("m1_confirmation", True, m1_conf["type"], m1_reason)
            else:
                if df_1m is not None:
                    self._gate("m1_confirmation", False, "none",
                               "M1 sem MSS+FVG/BPR confirmado na zona do FVG M5")
                    return None
                else:
                    entry_price = fvg_ce_m5
                    stop_loss = lowest_low - (self.config.sl_buffer_ticks * self.config.tick_size)
                    sl_distance = abs(entry_price - stop_loss)
                    if sl_distance < self.config.min_sl_distance_pts:
                        stop_loss = entry_price - self.config.min_sl_distance_pts
                    take_profit = entry_price + (abs(entry_price - stop_loss) * self.config.min_rr)
                    self._gate("m1_confirmation", True, "fallback_m5_ce",
                               "sem dados M1 — entrada no CE M5 (modo degradado)")

            take_profit = max(take_profit, pdh)

            self._gate("signal_generated", True, "BUY", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"London Sweep BULLISH NQ. Sweep PDL ({pdl:.2f}) "
                      f"min {lowest_low:.2f}. FVG M5 [{fvg_bot_m5:.2f}-{fvg_top_m5:.2f}] + MSS + Displacement. "
                      f"Entry ({entry_price:.2f}).")
            return Signal(
                symbol=self.symbol, action="BUY",
                entry_price=round(entry_price, 2), stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2), confidence_score=0.90,
                reasoning=reason, timestamp=current_time.to_pydatetime()
            )

        else:  # is_bearish_setup
            mss_ok = recent_swing_low is not None and c3['close'] < recent_swing_low
            if not self._gate("mss_confirmed_bearish", mss_ok,
                               f"close={c3['close']} swing_low={recent_swing_low}",
                               "fechamento atual não rompeu swing low recente"):
                return None
            
            fvg_top_m5 = fvg_top_detected
            fvg_bot_m5 = fvg_bottom_detected
            fvg_ce_m5 = (fvg_top_m5 + fvg_bot_m5) / 2.0
            
            # Filtrar M1 apenas dentro da zona do FVG M5 e dentro da killzone atual
            if df_1m is not None and not df_1m.empty:
                killzone_start_dt = pd.to_datetime(
                    current_time.strftime("%Y-%m-%d") + f" {self.config.killzone_start}"
                ).tz_localize('America/New_York')
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
                m1_reason = m1_conf["reason"]
                self._gate("m1_confirmation", True, m1_conf["type"], m1_reason)
            else:
                if df_1m is not None:
                    self._gate("m1_confirmation", False, "none",
                               "M1 sem MSS+FVG/BPR confirmado na zona do FVG M5")
                    return None
                else:
                    entry_price = fvg_ce_m5
                    stop_loss = highest_high + (self.config.sl_buffer_ticks * self.config.tick_size)
                    sl_distance = abs(stop_loss - entry_price)
                    if sl_distance < self.config.min_sl_distance_pts:
                        stop_loss = entry_price + self.config.min_sl_distance_pts
                    take_profit = entry_price - (abs(stop_loss - entry_price) * self.config.min_rr)
                    self._gate("m1_confirmation", True, "fallback_m5_ce",
                               "sem dados M1 — entrada no CE M5 (modo degradado)")

            take_profit = min(take_profit, pdl)

            self._gate("signal_generated", True, "SELL", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"London Sweep BEARISH NQ. Sweep PDH ({pdh:.2f}) "
                      f"max {highest_high:.2f}. FVG M5 [{fvg_bot_m5:.2f}-{fvg_top_m5:.2f}] + MSS + Displacement. "
                      f"Entry ({entry_price:.2f}).")
            return Signal(
                symbol=self.symbol, action="SELL",
                entry_price=round(entry_price, 2), stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2), confidence_score=0.90,
                reasoning=reason, timestamp=current_time.to_pydatetime()
            )

if __name__ == "__main__":
    config = LondonSweepNQConfig()
    strategy = LondonSweepNQ(config)
    print(f"Estratégia {strategy.name} inicializada com sucesso para {strategy.symbol}.")
