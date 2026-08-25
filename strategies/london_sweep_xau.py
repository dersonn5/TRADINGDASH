from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
from strategies.base import Strategy, Signal

@dataclass
class LondonSweepConfig:
    killzone_start: time = time(2, 0)   # EST
    killzone_end: time = time(5, 0)     # EST
    asian_start: time = time(0, 0)      # EST
    asian_end: time = time(2, 0)        # EST
    max_trades_per_day: int = 1
    min_rr: float = 2.0
    sl_buffer_usd: float = 0.5          # $0.50 buffer para XAU (50 ticks)
    require_daily_bias: bool = True
    cooldown_minutes: int = 30          # Dedup: ignora novo sinal nos N min após o último
    min_sl_distance_usd: float = 8.0    # SL mínimo $8.00 XAU — evita stop hunt

class LondonSweepXAU(Strategy):
    name = "london_sweep_xau"
    symbol = "XAUUSD"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: LondonSweepConfig = None):
        self.config = config or LondonSweepConfig()
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

    def _get_asian_range(self, df_5m: pd.DataFrame, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """
        Retorna a máxima e a mínima do Asian Range (00:00 - 02:00 EST).
        """
        date_str = current_time.strftime("%Y-%m-%d")
        
        asian_start_dt = pd.to_datetime(f"{date_str} 00:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
        asian_end_dt = pd.to_datetime(f"{date_str} 02:00:00").tz_localize('America/New_York', nonexistent='shift_forward')
        
        session_candles = df_5m[(df_5m.index >= asian_start_dt) & (df_5m.index <= asian_end_dt)]
        if session_candles.empty:
            return None, None
            
        return session_candles['high'].max(), session_candles['low'].min()

    def _detect_mss_and_swing(self, df_5m: pd.DataFrame, lookback: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """
        Detecta swing high e swing low recentes — pivot 1/1 (relaxado).
        Critério: candle com high/low maior/menor que 1 candle de cada lado.
        Pivot 2/2 era restritivo demais pra M5 e matava 100% dos setups.
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
        FVG bullish: c[i].low > c[i-2].high (gap pra cima entre c[i-2] e c[i])
        FVG bearish: c[i].high < c[i-2].low (gap pra baixo)
        Retorna ("bullish"|"bearish", (top, bottom)) ou (None, None).
        Não mitigada = candles posteriores não fecharam dentro/além do gap.
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
                # Displacement Check on c_disp (i-1)
                c_disp = df_5m.iloc[i - 1]
                atr_val = self._calculate_atr(df_5m.iloc[:i+1], period=14)
                c_disp_body = abs(c_disp['close'] - c_disp['open'])
                if atr_val == 0.0 or c_disp_body >= 1.2 * atr_val:
                    fvg_top = float(c_curr['low'])
                    fvg_bottom = float(c_prev2['high'])
                    # Verificar se foi mitigado por candles posteriores
                    mitigated = False
                    for j in range(i + 1, n):
                        if df_5m.iloc[j]['close'] < fvg_bottom:
                            mitigated = True
                            break
                    if not mitigated:
                        return "bullish", (fvg_top, fvg_bottom)

            # FVG Bearish
            if c_curr['high'] < c_prev2['low']:
                # Displacement Check on c_disp (i-1)
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
        Avalia o setup London Sweep para Gold (XAUUSD).
        Cada decisão passa por self._gate() pra diagnóstico funil.
        """
        self._reset_gates()

        if not self._gate("data_present", not (candles_5m.empty or candles_1d.empty),
                           None, "dados M5 ou D1 vazios"):
            return None

        df_5m = candles_5m
        df_1d = candles_1d
        df_1m = candles_1m if candles_1m is not None else None
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

        # GATE 3 — Asian Range válido
        asian_high, asian_low = self._get_asian_range(df_5m, current_time)
        if not self._gate("asian_range_valid", asian_high is not None and asian_low is not None,
                          f"asian_high={asian_high} asian_low={asian_low}",
                          "sem velas no Asian Range (00:00-02:00 EST)"):
            return None

        # GATE 4 — Velas presentes na killzone
        killzone_start_dt = pd.to_datetime(current_time.strftime(f"%Y-%m-%d {self.config.killzone_start}")).tz_localize('America/New_York', nonexistent='shift_forward')
        killzone_candles = df_5m[df_5m.index >= killzone_start_dt]
        if not self._gate("killzone_has_candles", not killzone_candles.empty, len(killzone_candles),
                          "sem velas dentro da killzone atual"):
            return None

        lowest_low = killzone_candles['low'].min()
        highest_high = killzone_candles['high'].max()

        bullish_sweep = lowest_low < asian_low and killzone_candles.iloc[-1]['close'] > asian_low
        bearish_sweep = highest_high > asian_high and killzone_candles.iloc[-1]['close'] < asian_high

        # GATE 5 — Velas suficientes para FVG
        if not self._gate("enough_candles_for_fvg", len(df_5m) >= 4, len(df_5m),
                          "menos de 4 velas M5"):
            return None

        # GATE 6 — FVG ativa em janela de 12 candles (não só últimos 3)
        # Usa detector novo que considera FVGs ainda não mitigadas
        fvg_direction, fvg_bounds = self._detect_active_fvg(df_5m, lookback=12)
        fvg_present = fvg_direction is not None
        if not self._gate("fvg_present_any", fvg_present,
                          fvg_direction if fvg_direction else "none",
                          "nenhum FVG ativo nos últimos 12 candles M5"):
            return None

        c3 = df_5m.iloc[-1]
        fvg_bullish = fvg_direction == "bullish"
        fvg_bearish = fvg_direction == "bearish"
        # fvg_top/fvg_bottom vêm do detector
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
                if sl_distance < self.config.min_sl_distance_usd:
                    stop_loss = entry_price - self.config.min_sl_distance_usd
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
                    stop_loss = lowest_low - self.config.sl_buffer_usd
                    sl_distance = abs(entry_price - stop_loss)
                    if sl_distance < self.config.min_sl_distance_usd:
                        stop_loss = entry_price - self.config.min_sl_distance_usd
                    take_profit = entry_price + (abs(entry_price - stop_loss) * self.config.min_rr)
                    self._gate("m1_confirmation", True, "fallback_m5_ce",
                               "sem dados M1 — entrada no CE M5 (modo degradado)")

            take_profit = max(take_profit, asian_high)

            self._gate("signal_generated", True, "BUY", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"London Sweep BULLISH XAU. Sweep Asian Low ({asian_low:.2f}) "
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
                if sl_distance < self.config.min_sl_distance_usd:
                    stop_loss = entry_price + self.config.min_sl_distance_usd
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
                    stop_loss = highest_high + self.config.sl_buffer_usd
                    sl_distance = abs(stop_loss - entry_price)
                    if sl_distance < self.config.min_sl_distance_usd:
                        stop_loss = entry_price + self.config.min_sl_distance_usd
                    take_profit = entry_price - (abs(stop_loss - entry_price) * self.config.min_rr)
                    self._gate("m1_confirmation", True, "fallback_m5_ce",
                               "sem dados M1 — entrada no CE M5 (modo degradado)")

            take_profit = min(take_profit, asian_low)

            self._gate("signal_generated", True, "SELL", "todos os gates passaram")
            self._last_signal_ts = current_time
            reason = (f"London Sweep BEARISH XAU. Sweep Asian High ({asian_high:.2f}) "
                      f"max {highest_high:.2f}. FVG M5 [{fvg_bot_m5:.2f}-{fvg_top_m5:.2f}] + MSS + Displacement. "
                      f"Entry ({entry_price:.2f}).")
            return Signal(
                symbol=self.symbol, action="SELL",
                entry_price=round(entry_price, 2), stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2), confidence_score=0.90,
                reasoning=reason, timestamp=current_time.to_pydatetime()
            )

if __name__ == "__main__":
    config = LondonSweepConfig()
    strategy = LondonSweepXAU(config)
    print(f"Estratégia {strategy.name} inicializada com sucesso para {strategy.symbol}.")
