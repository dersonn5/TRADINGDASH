from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional, Tuple
import pandas as pd
from strategies.base import Strategy, Signal

@dataclass
class BreakerBlockCryptoConfig:
    killzone_start: time = time(2, 0)     # Janela de Volume Cripto (Londres + NY)
    killzone_end: time = time(16, 0)      # 02:00 às 16:00 EST
    min_rr: float = 2.0
    sl_buffer_percent: float = 0.001     # 0.1% buffer do preço para SL
    require_daily_bias: bool = True
    require_sweep: bool = True           # Sweep do High/Low de 24h
    cooldown_minutes: int = 60
    min_sl_distance_percent: float = 0.005 # SL mínimo de 0.5% para evitar stop hunt
    atr_multiplier: float = 1.0         # Displacement
    breaker_lookback: int = 50          # Candles M5 para buscar o OB violado
    range_lookback_5m: int = 288        # 288 candles de 5m = 24 horas

class BreakerBlockCrypto(Strategy):
    name = "breaker_block_crypto"
    
    def __init__(self, config: BreakerBlockCryptoConfig = None):
        self.config = config or BreakerBlockCryptoConfig()
        self._last_signal_ts: Optional[datetime] = None

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

    def _get_24h_range(self, df_5m: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """Retorna a máxima e a mínima das últimas 24 horas (excluindo a vela atual)."""
        lookback = self.config.range_lookback_5m
        if len(df_5m) < lookback + 1:
            return None, None
        recent = df_5m.iloc[-(lookback + 1):-1]
        return float(recent["high"].max()), float(recent["low"].min())

    def _check_sweep(self, df_5m: pd.DataFrame, range_high: float, range_low: float) -> Tuple[bool, bool]:
        """Verifica se o candle atual ou recente varreu a máxima ou mínima das últimas 24h."""
        if range_high is None or range_low is None:
            return False, False
        # Consideramos as últimas 3 velas para ver se houve o sweep local
        recent_window = df_5m.iloc[-3:]
        low_swept = recent_window["low"].min() < range_low
        close_above_low = df_5m.iloc[-1]["close"] > range_low
        bullish_sweep = low_swept and close_above_low

        high_swept = recent_window["high"].max() > range_high
        close_below_high = df_5m.iloc[-1]["close"] < range_high
        bearish_sweep = high_swept and close_below_high

        return bullish_sweep, bearish_sweep

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

        # GATE 1 — Killzone (London Open: 02:00-05:00 EST, NY Open: 10:00-12:00 EST)
        in_killzone = (time(2, 0) <= current_time_only < time(5, 0)) or (time(10, 0) <= current_time_only < time(12, 0))
        if not self._gate("killzone_active", in_killzone,
                          current_time_only.strftime("%H:%M"),
                          "fora das janelas operacionais de volume"):
            return None

        # GATE 1.5 — Cooldown
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

        # Calcular EMA 200 no timeframe de 5m (usando as últimas 600 velas para otimizar memória e CPU)
        closes_5m = df_5m['close']
        if len(closes_5m) >= 600:
            ema_200 = closes_5m.iloc[-600:].ewm(span=200, adjust=False).mean().iloc[-1]
        elif len(closes_5m) >= 200:
            ema_200 = closes_5m.ewm(span=200, adjust=False).mean().iloc[-1]
        else:
            ema_200 = closes_5m.mean()

        # Obter Asian Range e 24h Range para validação de sweep
        asian_range = self._get_asian_range(df_5m, current_time)
        range_24h = self._get_24h_range(df_5m)

        # GATE 3 — Detectar Breaker com sweeps institucionais
        if bias == "BEARISH":
            bb = self._detect_breaker_block(df_5m, "bearish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier,
                                            asian_range=asian_range,
                                            range_24h=range_24h)
        elif bias == "BULLISH":
            bb = self._detect_breaker_block(df_5m, "bullish",
                                            lookback=self.config.breaker_lookback,
                                            atr_multiplier=self.config.atr_multiplier,
                                            asian_range=asian_range,
                                            range_24h=range_24h)
        else:
            bb = None

        if not self._gate("breaker_detected", bb is not None,
                          bb["breaker_type"] if bb else "none",
                          "sem Breaker Block M5 qualificado"):
            return None

        # Entrada a mercado
        entry_price = current_close
        action = "SELL" if bb["breaker_type"] == "bearish" else "BUY"

        # GATE 3.5 — Filtro de Tendência EMA 200 (5m)
        trend_aligned = (action == "BUY" and current_close > ema_200) or (action == "SELL" and current_close < ema_200)
        if not self._gate("trend_aligned_ema200", trend_aligned, f"close={current_close:.2f} ema200={ema_200:.2f}", f"Sinal {action} contra a tendência da EMA 200 (5m)"):
            return None

        # Calcular SL com buffer proporcional
        if action == "SELL":
            sl_price = bb["zone_high"] * (1.0 + self.config.sl_buffer_percent)
            sl_dist = abs(sl_price - entry_price)
            min_sl = entry_price * self.config.min_sl_distance_percent
            if sl_dist < min_sl:
                sl_price = entry_price + min_sl
                sl_dist = min_sl
            
            # Draw on Liquidity (DOL) dinâmico
            dol_target = self._detect_dynamic_dol(candles_15m, "SELL", entry_price, lookback=50)
            if dol_target is not None and dol_target < entry_price:
                take_profit = dol_target
            else:
                take_profit = entry_price - sl_dist * self.config.min_rr
        else:
            sl_price = bb["zone_low"] * (1.0 - self.config.sl_buffer_percent)
            sl_dist = abs(entry_price - sl_price)
            min_sl = entry_price * self.config.min_sl_distance_percent
            if sl_dist < min_sl:
                sl_price = entry_price - min_sl
                sl_dist = min_sl
                
            # Draw on Liquidity (DOL) dinâmico
            dol_target = self._detect_dynamic_dol(candles_15m, "BUY", entry_price, lookback=50)
            if dol_target is not None and dol_target > entry_price:
                take_profit = dol_target
            else:
                take_profit = entry_price + sl_dist * self.config.min_rr

        # Validar R:R final
        rr = abs(take_profit - entry_price) / sl_dist if sl_dist > 0 else 0.0
        if not self._gate("min_rr_passed", rr >= self.config.min_rr, f"RR={rr:.2f}", f"R:R abaixo de {self.config.min_rr}"):
            return None

        self._gate("signal_generated", True, action, "todas as condicoes passadas")
        self._last_signal_ts = current_time

        reason = (
            f"Breaker Block Crypto {action} — {bb['reason']} "
            f"DOL={take_profit:.2f} SL={sl_price:.2f} RR={rr:.2f}"
        )

        return Signal(
            symbol=self.symbol,
            action=action,
            entry_price=round(entry_price, 2),
            stop_loss=round(sl_price, 2),
            take_profit=round(take_profit, 2),
            confidence_score=0.90,
            reasoning=reason,
            timestamp=current_time.to_pydatetime()
        )
