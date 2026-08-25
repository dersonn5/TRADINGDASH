"""
Daemon OKX: multi-ativo, multi-estratégia, WebSocket-driven via CCXT Pro.
Avalia estratégias a cada candle M5 fechado. Paper trading ativo.
"""
import asyncio
import os
from datetime import time
from dotenv import load_dotenv
from execution.okx_client import OKXConfig
from data.okx_data_provider import OKXDataProvider
from execution.okx_executor import OKXExecutor
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
from strategies.london_sweep_xau import LondonSweepXAU, LondonSweepConfig

load_dotenv()

# Símbolos CCXT OKX (perpetual swap):
# BTC/USDT:USDT  ETH/USDT:USDT  SOL/USDT:USDT

STRATEGY_MAP = {
    "BTC/USDT:USDT": [
        SilverBulletNQ(SilverBulletConfig(
            min_sl_distance_pts=50.0,   # BTC move $50+ facilmente
            min_rr=2.0,
        )),
        LondonSweepXAU(LondonSweepConfig(
            killzone_start=time(2, 0),
            killzone_end=time(5, 0),
            min_sl_distance_usd=50.0,
            min_rr=2.0,
        )),
    ],
    "ETH/USDT:USDT": [
        SilverBulletNQ(SilverBulletConfig(
            min_sl_distance_pts=20.0,   # ETH move $20+ na sessão NY
            min_rr=2.0,
        )),
    ],
}

SYMBOLS = list(STRATEGY_MAP.keys())
TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"]


async def main():
    config = OKXConfig(
        api_key=os.getenv("OKX_API_KEY", ""),
        api_secret=os.getenv("OKX_API_SECRET", ""),
        passphrase=os.getenv("OKX_PASSPHRASE", ""),
        paper_trading=True,  # SEMPRE True durante validação de edge
    )
    provider = OKXDataProvider(config, max_candles=300)
    executor = OKXExecutor(config, balance_usd=10_000, risk_pct=0.01)

    print("[INIT] Bootstrap histórico via REST...")
    await provider.bootstrap(SYMBOLS, TIMEFRAMES)
    print("[INIT] Bootstrap completo. Iniciando WebSocket...")

    async def on_closed_candle(symbol: str, tf: str, candle: list):
        if tf != "5m":
            return
        if not provider.is_ready(symbol, "5m"):
            return

        df_1m  = provider.get_dataframe(symbol, "1m")
        df_5m  = provider.get_dataframe(symbol, "5m")
        df_15m = provider.get_dataframe(symbol, "15m")
        df_1h  = provider.get_dataframe(symbol, "1h")
        df_1d  = provider.get_dataframe(symbol, "1d")

        for strategy in STRATEGY_MAP.get(symbol, []):
            try:
                signal = strategy.evaluate(df_5m, df_15m, df_1h, df_1d, df_1m)
                if signal:
                    print(f"[SIGNAL] {symbol} {strategy.__class__.__name__}: "
                          f"{signal.action} @ {signal.entry_price} "
                          f"SL={signal.stop_loss} TP={signal.take_profit}")
                    result = executor.execute(signal, symbol)
                    print(f"[ORDER] {result.get('id', result)}")
            except Exception as e:
                print(f"[ERRO] {strategy.__class__.__name__} @ {symbol}: {e}")

    # Escuta WebSocket para M1 e M5 em todos os símbolos simultaneamente
    watchers = [
        provider.watch_symbol_timeframe(sym, tf, on_closed_candle)
        for sym in SYMBOLS
        for tf in ["1m", "5m"]
    ]
    await asyncio.gather(*watchers)


if __name__ == "__main__":
    asyncio.run(main())
