import sys
import asyncio
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv

load_dotenv()

def print_result(check_name: str, success: bool, details: str = ""):
    status = "SUCCESS" if success else "FAILED"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] {check_name}: {details}")

async def main():
    print("====================================================")
    print("      BINANCE TESTNET PRE-FLIGHT VALIDATION GATES   ")
    print("====================================================\n")
    
    # Check 1: Python environment & dependencies
    try:
        import ccxt
        import ccxt.pro as ccxtpro
        import pandas as pd
        import numpy as np
        print_result("1. Libraries Check", True, f"ccxt v{ccxt.__version__}, ccxt.pro, pandas v{pd.__version__} installed.")
    except Exception as e:
        print_result("1. Libraries Check", False, f"Missing dependencies: {e}")
        sys.exit(1)
        
    # Check 2: API Keys configuration
    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
    api_secret = os.getenv("BINANCE_TESTNET_SECRET", "")
    
    if not api_key or not api_secret:
        print_result("2. API Keys Check", False, "BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_SECRET must be set in your .env file.")
        print("\nTo set up:")
        print("1. Go to https://testnet.binancefuture.com")
        print("2. Login with your GitHub account")
        print("3. Generate API Key + Secret")
        print("4. Paste them into .env in e:\\AUTOMAÇÃO IA\\TRADING AI\\.env")
        print("\nFor testing without keys, we can bypass, but live trading daemon requires them.")
        sys.exit(1)
    else:
        print_result("2. API Keys Check", True, "API Key and Secret found in environment.")
        
    # Check 3: Connectivity & API credentials authentication (via direct HTTP — CCXT load_markets
    # tenta endpoints spot que rejeitam keys demo)
    import urllib.request, urllib.error, hashlib, hmac, time as _time, json as _json
    BASE = "https://demo-fapi.binance.com"

    def _signed_get(path: str) -> dict:
        srv_r = urllib.request.urlopen(f"{BASE}/fapi/v1/time", timeout=10)
        ts = _json.loads(srv_r.read())["serverTime"]
        params = f"timestamp={ts}&recvWindow=10000"
        sig = hmac.new(api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        url = f"{BASE}{path}?{params}&signature={sig}"
        req = urllib.request.Request(url, headers={"X-MBX-APIKEY": api_key})
        return _json.loads(urllib.request.urlopen(req, timeout=10).read())

    try:
        ping_r = urllib.request.urlopen(f"{BASE}/fapi/v1/ping", timeout=10)
        print_result("3. API Connectivity Check", ping_r.status == 200, f"demo-fapi.binance.com ping OK ({ping_r.status})")
    except Exception as e:
        print_result("3. API Connectivity Check", False, f"Ping falhou: {e}")
        sys.exit(1)

    # Check 4: Fetch OHLCV (publico, sem auth)
    symbol_raw = "ETHUSDT"
    try:
        url = f"{BASE}/fapi/v1/klines?symbol={symbol_raw}&interval=5m&limit=5"
        r = urllib.request.urlopen(url, timeout=10)
        klines = _json.loads(r.read())
        if klines:
            last_close = float(klines[-1][4])
            print_result("4. Fetch Market Data", True, f"Fetched {len(klines)} M5 candles ETH/USDT. Last close: {last_close}")
        else:
            print_result("4. Fetch Market Data", False, "Lista vazia")
    except Exception as e:
        print_result("4. Fetch Market Data", False, f"Erro: {e}")

    # Check 5: Account balance (autenticado)
    try:
        data = await asyncio.to_thread(_signed_get, "/fapi/v2/account")
        usdt = next(
            (float(a.get("walletBalance", 0)) for a in data.get("assets", []) if a["asset"] == "USDT"),
            0.0
        )
        print_result("5. Balance & Margins Check", True, f"USDT demo balance: {usdt:.2f} USDT")
    except Exception as e:
        print_result("5. Balance & Margins Check", False, f"Erro: {e}")

    # Check 6: Strategy loading validation
    try:
        import io, contextlib
        from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            strategy = SilverBulletNQ(SilverBulletConfig())
        print_result("6. Strategy Load Check", True, "SilverBulletNQ loaded successfully with all components.")
    except Exception as e:
        print_result("6. Strategy Load Check", False, f"Failed to load strategy: {e}")
        
    print("\n====================================================")
    print("             PRE-FLIGHT VALIDATION COMPLETE         ")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(main())
