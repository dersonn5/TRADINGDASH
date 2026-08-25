from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from strategies.base import Strategy, Signal

@dataclass
class SilverBulletCryptoConfig:
    killzone_start: time = time(10, 0)     # classic ICT SB NY AM (10:00-11:00 EST)
    killzone_end: time = time(11, 0)
    min_rr: float = 2.0
    sl_buffer_percent: float = 0.001     # 0.1% buffer
    require_daily_bias: bool = True
    require_premium_discount: bool = True
    require_smt: bool = True             # SMT Divergência obrigatória (ETH/BTC)
    cooldown_minutes: int = 60
    min_sl_distance_percent: float = 0.005 # 0.5%
    atr_multiplier: float = 1.0          # Displacement para FVG

class SilverBulletCrypto(Strategy):
    name = "silver_bullet_crypto"
    
    def __init__(self, config: SilverBulletCryptoConfig = None):
        self.config = config or SilverBulletCryptoConfig()
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

    def _detect_active_fvg(self, df_5m: pd.DataFrame, lookback: int = 6) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        if len(df_5m) < 4:
            return None, None
        n = len(df_5m)
        start = max(2, n - lookback)
        for i in range(n - 1, start, -1):
            c_curr = df_5m.iloc[i]
            c_prev2 = df_5m.iloc[i - 2]
            
            # FVG Bullish
            if c_curr['low'] > c_prev2['high']:
                fvg_top = float(c_curr['low'])
                fvg_bottom = float(c_prev2['high'])
                # Verifica se ja foi mitigada (fechou abaixo da minima do FVG)
                mitigated = False
                for j in range(i + 1, n):
                    if df_5m.iloc[j]['close'] < fvg_bottom:
                        mitigated = True
                        break
                if not mitigated:
                    return "bullish", (fvg_top, fvg_bottom)
                    
            # FVG Bearish
            if c_curr['high'] < c_prev2['low']:
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

    def _check_smt_divergence(self, df_5m: pd.DataFrame, df_corr_5m: pd.DataFrame, direction: str) -> bool:
        """
        Verifica se há divergência SMT (Smart Money Technique) nos wicks recentes.
        BUY: Nosso ativo faz um lower low, mas o correlacionado faz um higher low.
        SELL: Nosso ativo faz um higher high, mas o correlacionado faz um lower high.
        """
        if df_corr_5m is None or len(df_corr_5m) < 10 or len(df_5m) < 10:
            return False

        # Compara as mínimas/máximas dos últimos 5 candles
        recent_us = df_5m.iloc[-5:]
        recent_corr = df_corr_5m.iloc[-5:]

        if direction == "BUY":
            # Nosso ativo fez nova mínima nos últimos 5 candles em relação aos 5 anteriores?
            prev_us = df_5m.iloc[-10:-5]
            prev_corr = df_corr_5m.iloc[-10:-5]

            us_low1 = prev_us['low'].min()
            us_low2 = recent_us['low'].min()
            corr_low1 = prev_corr['low'].min()
            corr_low2 = recent_corr['low'].min()

            us_made_lower_low = us_low2 < us_low1
            corr_made_lower_low = corr_low2 < corr_low1

            # Divergência SMT: um fez nova mínima, o outro não
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
            corr_made_higher_high = corr_corr2 = corr_high2 > corr_high1

            # Divergência SMT: um fez nova máxima, o outro não
            if us_made_higher_high and not corr_made_higher_high:
                return True
            if not us_made_higher_high and corr_made_higher_high:
                return True

        return False

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
        current_close = float(df_5m.iloc[-1]["close"])

        # GATE 0.5 — Killzone Active
        current_time_only = current_time.time()
        in_killzone = self.config.killzone_start <= current_time_only < self.config.killzone_end
        if not self._gate("killzone_active", in_killzone,
                          current_time_only.strftime("%H:%M"),
                          f"fora da killzone {self.config.killzone_start}-{self.config.killzone_end}"):
            return None

        # GATE 1 — Cooldown
        if self._last_signal_ts is not None:
            elapsed = (current_time - self._last_signal_ts).total_seconds() / 60.0
            if not self._gate("cooldown_passed", elapsed >= self.config.cooldown_minutes,
                               f"{elapsed:.0f}min", "cooldown ativo"):
                return None

        # GATE 2 — Daily Bias
        bias = self._get_daily_bias(df_1d)
        bias_ok = (not self.config.require_daily_bias) or (bias != "NEUTRAL")
        if not self._gate("bias_not_neutral", bias_ok, bias, "PO3 neutral"):
            return None

        # GATE 3 — FVG Ativa
        fvg_direction, fvg_bounds = self._detect_active_fvg(df_5m, lookback=6)
        if not self._gate("fvg_present", fvg_direction is not None, fvg_direction if fvg_direction else "none", "sem FVG ativa nos últimos 6 candles"):
            return None

        fvg_top, fvg_bot = fvg_bounds
        fvg_ce = (fvg_top + fvg_bot) / 2.0

        # Calcular EMA 200 no timeframe de 5m (usando as últimas 600 velas para otimizar memória e CPU)
        closes_5m = df_5m['close']
        if len(closes_5m) >= 600:
            ema_200 = closes_5m.iloc[-600:].ewm(span=200, adjust=False).mean().iloc[-1]
        elif len(closes_5m) >= 200:
            ema_200 = closes_5m.ewm(span=200, adjust=False).mean().iloc[-1]
        else:
            ema_200 = closes_5m.mean()

        # Alinhamento de viés com a direção da FVG
        fvg_aligned = (
            (fvg_direction == "bullish" and bias == "BULLISH") or
            (fvg_direction == "bearish" and bias == "BEARISH")
        )
        if not self._gate("fvg_aligned_with_bias", fvg_aligned, f"fvg={fvg_direction} bias={bias}", "FVG contrária ao bias"):
            return None

        action = "BUY" if fvg_direction == "bullish" else "SELL"

        # GATE 3.8 — Filtro de Tendência EMA 200 (5m)
        trend_aligned = (action == "BUY" and current_close > ema_200) or (action == "SELL" and current_close < ema_200)
        if not self._gate("trend_aligned_ema200", trend_aligned, f"close={current_close:.2f} ema200={ema_200:.2f}", f"Sinal {action} contra a tendência da EMA 200 (5m)"):
            return None

        # GATE 4 — Confluência SMT Divergência (Cruzando com BTC/ETH)
        df_corr = self._convert_to_est(self.correlated_data) if self.correlated_data is not None else None
        smt_detected = self._check_smt_divergence(df_5m, df_corr, action)
        if not self._gate("smt_confluence", (not self.config.require_smt) or smt_detected,
                          f"smt={smt_detected}", f"sem divergência SMT com {self.correlated_symbol}"):
            return None

        # Calcular limites operacionais
        entry_price = current_close

        if action == "BUY":
            # SL abaixo da FVG com buffer
            sl_price = fvg_bot * (1.0 - self.config.sl_buffer_percent)
            sl_dist = abs(entry_price - sl_price)
            min_sl = entry_price * self.config.min_sl_distance_percent
            if sl_dist < min_sl:
                sl_price = entry_price - min_sl
                sl_dist = min_sl
            
            # DOL dinâmico
            dol_target = self._detect_dynamic_dol(candles_15m, "BUY", entry_price, lookback=50)
            if dol_target is not None and dol_target > entry_price:
                take_profit = dol_target
            else:
                take_profit = entry_price + sl_dist * self.config.min_rr
        else:
            # SL acima da FVG com buffer
            sl_price = fvg_top * (1.0 + self.config.sl_buffer_percent)
            sl_dist = abs(sl_price - entry_price)
            min_sl = entry_price * self.config.min_sl_distance_percent
            if sl_dist < min_sl:
                sl_price = entry_price + min_sl
                sl_dist = min_sl
            
            # DOL dinâmico
            dol_target = self._detect_dynamic_dol(candles_15m, "SELL", entry_price, lookback=50)
            if dol_target is not None and dol_target < entry_price:
                take_profit = dol_target
            else:
                take_profit = entry_price - sl_dist * self.config.min_rr

        # Validar R:R final
        rr = abs(take_profit - entry_price) / sl_dist if sl_dist > 0 else 0.0
        if not self._gate("min_rr_passed", rr >= self.config.min_rr, f"RR={rr:.2f}", f"R:R abaixo de {self.config.min_rr}"):
            return None

        self._gate("signal_generated", True, action, "todas as condicoes passadas")
        self._last_signal_ts = current_time

        reason = (
            f"Silver Bullet Crypto {action} — FVG={fvg_bot:.2f}-{fvg_top:.2f}. SMT Divergência confirmada. "
            f"DOL={take_profit:.2f} SL={sl_price:.2f} RR={rr:.2f}"
        )

        return Signal(
            symbol=self.symbol,
            action=action,
            entry_price=round(entry_price, 2),
            stop_loss=round(sl_price, 2),
            take_profit=round(take_profit, 2),
            confidence_score=0.92,
            reasoning=reason,
            timestamp=current_time.to_pydatetime()
        )
