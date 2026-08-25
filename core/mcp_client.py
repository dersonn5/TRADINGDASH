import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import config


class MCPTradingViewClient:
    """
    Cliente MCP para servidor TradingView (compatível com bidouilles/mcp-tradingview-server).
    Conecta via stdio (default) ou HTTP.

    Ferramentas usadas:
      - get_historical_data(symbol, exchange, timeframe, max_records) -> OHLCV
      - get_indicators(symbol, exchange, timeframe, all_indicators)   -> snapshot indicadores
      - get_specific_indicators(symbol, indicators, exchange, timeframe)

    Uso assíncrono (recomendado em FastAPI):
        snapshot = await MCPTradingViewClient.get_candles("XAUUSD", "15m", 100)
    """

    SYMBOL_EXCHANGE_MAP = [
        ("XAUUSD", "OANDA"),
        ("XAU", "OANDA"),
        ("MNQ", "CME_MINI"),
        ("MES", "CME_MINI"),
        ("NQ", "CME_MINI"),
        ("ES", "CME_MINI"),
        ("BTCUSDT", "BINANCE"),
        ("ETHUSDT", "BINANCE"),
    ]

    @classmethod
    def resolve_exchange(cls, symbol: str) -> str:
        sym = symbol.upper()
        for key, exch in cls.SYMBOL_EXCHANGE_MAP:
            if key in sym:
                return exch
        return getattr(config, "MCP_DEFAULT_EXCHANGE", "BINANCE")

    @classmethod
    @asynccontextmanager
    async def _session(cls):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=config.MCP_SERVER_COMMAND,
            args=list(config.MCP_SERVER_ARGS),
            env=os.environ.copy(),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as sess:
                await sess.initialize()
                yield sess

    @classmethod
    async def _call(cls, tool_name: str, args: dict) -> dict:
        async with cls._session() as sess:
            result = await sess.call_tool(tool_name, args)
            return cls._parse_result(result)

    @staticmethod
    def _parse_result(result) -> dict:
        if not getattr(result, "content", None):
            return {}
        first = result.content[0]
        text = first.text if hasattr(first, "text") else str(first)
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    @classmethod
    async def get_candles(
        cls,
        symbol: str,
        timeframe: str = "15m",
        max_records: int = 100,
        exchange: Optional[str] = None,
    ) -> dict:
        return await cls._call("get_historical_data", {
            "symbol": symbol,
            "exchange": exchange or cls.resolve_exchange(symbol),
            "timeframe": timeframe,
            "max_records": max_records,
        })

    @classmethod
    async def get_indicators(
        cls,
        symbol: str,
        timeframe: str = "15m",
        exchange: Optional[str] = None,
    ) -> dict:
        return await cls._call("get_indicators", {
            "symbol": symbol,
            "exchange": exchange or cls.resolve_exchange(symbol),
            "timeframe": timeframe,
            "all_indicators": True,
        })

    @classmethod
    async def get_specific_indicators(
        cls,
        symbol: str,
        indicators: list[str],
        timeframe: str = "15m",
        exchange: Optional[str] = None,
    ) -> dict:
        return await cls._call("get_specific_indicators", {
            "symbol": symbol,
            "indicators": indicators,
            "exchange": exchange or cls.resolve_exchange(symbol),
            "timeframe": timeframe,
        })

    @classmethod
    async def market_snapshot(
        cls,
        symbol: str,
        timeframe: str = "15m",
        candles: int = 100,
        exchange: Optional[str] = None,
    ) -> dict:
        exch = exchange or cls.resolve_exchange(symbol)
        candles_task = cls.get_candles(symbol, timeframe, candles, exch)
        indicators_task = cls.get_specific_indicators(
            symbol,
            indicators=["RSI", "MACD", "EMA20", "EMA50", "EMA200", "ATR"],
            timeframe=timeframe,
            exchange=exch,
        )
        candles_res, indicators_res = await asyncio.gather(candles_task, indicators_task)
        return {
            "symbol": symbol,
            "exchange": exch,
            "timeframe": timeframe,
            "candles": candles_res,
            "indicators": indicators_res,
        }
