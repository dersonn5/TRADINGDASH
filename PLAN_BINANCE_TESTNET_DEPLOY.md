# Deploy ETH/USDT Silver Bullet to Binance Testnet (Fase 5)

Deploy the validated ETH/USDT Silver Bullet strategy (PF 1.68, WR 63.6%, 3-year backtest) to Binance Futures Testnet for live forward testing. The execution infrastructure exists but has critical gaps that must be fixed before going live.

## User Review Required

> [!IMPORTANT]
> **Binance Testnet API Keys Required.** You need to:
> 1. Go to https://testnet.binancefuture.com
> 2. Login with your GitHub account (no KYC needed)
> 3. Generate API Key + Secret
> 4. Provide them so I can add to `.env`
>
> Without these keys, we cannot connect to the testnet. The testnet provides ~15,000 USDT mock funds automatically.

> [!WARNING]
> **Risk Parameters.** The plan uses conservative defaults for testnet:
> - **Risk per trade:** 1% ($100 on $10K account)
> - **Max trades per day:** 2
> - **Max daily drawdown:** 3% (hard stop)
> - **Leverage:** 5x (cross margin)
> - **Kill switch:** Ctrl+C graceful shutdown + 5 consecutive losses = 24h auto-pause
>
> Do you agree with these, or want to adjust?

> [!IMPORTANT]
> **Strategy Selection.** Only deploying **ETH/USDT Silver Bullet** (the one validated strategy with PF > 1.5). London Sweep and Breaker Block are NOT being deployed — they didn't meet the go/no-go criteria. Confirm this is what you want.

## Open Questions

> [!IMPORTANT]
> 1. **Gemini AI Validation Gate:** The current Binance daemon skips AI validation entirely (unlike the NQ/XAU daemon which routes through Gemini). Should we add Gemini as a final confirmation gate before placing orders, or keep it purely mechanical?
> 2. **Obsidian Trade Journal:** Should the Binance daemon write trade results to Obsidian (like the NQ/XAU daemon does), or is a simple log file + database sufficient for testnet phase?

---

## Proposed Changes

### Component 1: Binance Executor — SL/TP + Leverage + Margin

The current executor only places entry limit orders with NO stop loss or take profit. This means positions ride unprotected. This is the most critical fix.

#### [MODIFY] [binance_executor.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/execution/binance_executor.py)

- Add `set_leverage()` and `set_margin_mode('cross')` calls on first trade per symbol
- Replace bare `create_order()` with a 3-order bracket: **Entry + SL (stop-market) + TP (take-profit-market)**
- Add retry logic (3 attempts with exponential backoff) for transient exchange errors
- Add market order fallback if limit order doesn't fill within 60 seconds
- Fix bug: `0.001` safety minimum for BTC is $100 at current prices — use market's `limits.amount.min` instead
- Add proper logging for every order placed/filled/failed

---

### Component 2: Live Daemon — Production-Grade Binance Daemon

The current `live_daemon_binance.py` is a functional skeleton but lacks risk management, error handling, multi-timeframe refresh, and graceful shutdown.

#### [MODIFY] [live_daemon_binance.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/live_daemon_binance.py)

- **Fix Bug:** Balance hardcoded to $10K — read from `config.ACCOUNT_BALANCE`
- **Strategy:** Keep ONLY `ETH/USDT:USDT` → `SilverBulletNQ` (validated strategy). Remove BTC until validated.
- **Multi-TF Refresh:** Add periodic REST refresh for 15m, 1h, 1d candles (every 15m/1h/1d respectively) — current code only watches 1m/5m via WebSocket, so higher TFs go stale
- **Risk Management Gate:** Before every trade, check:
  - Daily trade count < max (2)
  - Daily PnL drawdown < 3%
  - 5 consecutive losses → 24h auto-pause
  - Position already open for this symbol → skip
- **Graceful Shutdown:** `KeyboardInterrupt` handler that:
  - Closes all WebSocket connections
  - Cancels all pending orders
  - Logs final session summary
- **Trade Logging:** Log every signal/trade/fill/exit to `logs_daemon_binance.txt` with full details
- **Health Heartbeat:** Print status every 5 minutes (connection state, open positions, daily PnL, trades today)

---

### Component 3: Order Manager — Crypto-Compatible PnL

#### [MODIFY] [order_manager.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/execution/order_manager.py)

- Fix hardcoded `point_value = 20.0 if "NQ"` — for crypto, PnL = `price_diff × quantity` (point_value = 1.0)
- Add symbol detection: if symbol contains `/` (CCXT format), use crypto PnL calculation
- Add commission handling for Binance futures (0.02% maker, 0.04% taker)

---

### Component 4: Data Provider — Async Fix + Higher TF Support

#### [MODIFY] [binance_data_provider.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/data/binance_data_provider.py)

- Fix sync `fetch_ohlcv` inside async method — use `await exchange.fetch_ohlcv()` or `asyncio.to_thread()`
- Add `refresh_timeframe(symbol, tf)` method for periodic REST refresh of 15m/1h/1d
- Add proper `close()` method for clean WebSocket shutdown

---

### Component 5: Configuration — Add BINANCE Mode

#### [MODIFY] [config.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/config.py)

- Add `EXECUTION_MODE = "BINANCE"` as a valid option
- Add Binance-specific config: `BINANCE_LEVERAGE`, `BINANCE_MARGIN_MODE`, `BINANCE_SYMBOLS`
- Load `BINANCE_TESTNET_API_KEY` and `BINANCE_TESTNET_SECRET` from `.env`

#### [MODIFY] [.env](file:///e:/AUTOMAÇÃO IA/TRADING AI/.env)

- Set `EXECUTION_MODE=BINANCE`
- Fill `BINANCE_TESTNET_API_KEY` and `BINANCE_TESTNET_SECRET` (user provides)
- Add `BINANCE_LEVERAGE=5`
- Add `BINANCE_MARGIN_MODE=cross`

---

### Component 6: Startup Script + Validation

#### [NEW] [start_binance_testnet.bat](file:///e:/AUTOMAÇÃO IA/TRADING AI/start_binance_testnet.bat)

- Simple startup script that:
  1. Validates Python environment + dependencies (`ccxt[pro]`)
  2. Tests Binance testnet connectivity (fetch balance)
  3. Launches `live_daemon_binance.py` with proper logging

#### [NEW] [validate_binance_setup.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/validate_binance_setup.py)

- Pre-flight check script that validates:
  - API keys present and valid
  - Testnet connectivity
  - `ccxt[pro]` installed correctly
  - Can fetch OHLCV for ETH/USDT:USDT
  - Can read account balance
  - Strategy loads without errors
  - Prints go/no-go status

---

## File Change Summary

| File | Action | Priority | Description |
|---|---|---|---|
| [binance_executor.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/execution/binance_executor.py) | MODIFY | 🔴 Critical | Add SL/TP bracket orders, leverage, retry logic |
| [live_daemon_binance.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/live_daemon_binance.py) | MODIFY | 🔴 Critical | Risk mgmt, multi-TF refresh, graceful shutdown |
| [order_manager.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/execution/order_manager.py) | MODIFY | 🟡 Important | Crypto-compatible PnL calculation |
| [binance_data_provider.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/data/binance_data_provider.py) | MODIFY | 🟡 Important | Async fix, higher TF refresh, clean shutdown |
| [config.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/config.py) | MODIFY | 🟡 Important | Add BINANCE execution mode + configs |
| [.env](file:///e:/AUTOMAÇÃO IA/TRADING AI/.env) | MODIFY | 🟡 Important | Add Binance testnet config |
| [validate_binance_setup.py](file:///e:/AUTOMAÇÃO IA/TRADING AI/validate_binance_setup.py) | NEW | 🟢 Nice | Pre-flight validation script |
| [start_binance_testnet.bat](file:///e:/AUTOMAÇÃO IA/TRADING AI/start_binance_testnet.bat) | NEW | 🟢 Nice | One-click startup |

---

## Verification Plan

### Automated Tests
1. Run `python validate_binance_setup.py` — confirms testnet connectivity, API keys, market access
2. Run `python -c "from execution.binance_executor import BinanceExecutor; print('OK')"` — confirms imports
3. Start `live_daemon_binance.py` and let it run for 10 minutes to confirm:
   - WebSocket connects and receives candles
   - Strategy evaluates without errors
   - Health heartbeat prints correctly
   - Graceful shutdown works (Ctrl+C)

### Manual Verification
1. **User must provide Binance testnet API keys** and paste them into `.env`
2. After daemon starts, check Binance testnet web UI to confirm:
   - Orders appear in open orders
   - SL/TP bracket orders are visible
   - Positions show correct leverage/margin
3. Wait for first ETH/USDT Silver Bullet signal during 10:00-11:00 EST killzone
4. Verify trade log in `logs_daemon_binance.txt`
