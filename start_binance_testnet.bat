@echo off
title Binance Futures Testnet Trading Daemon
echo ========================================================
echo         STARTING BINANCE TESTNET TRADING DAEMON
echo ========================================================
echo.

echo [INFO] Running Pre-Flight Setup Validation...
python validate_binance_setup.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Pre-flight validation FAILED.
    echo Please fix the issues above before starting the daemon.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Pre-flight validation PASSED.
echo.
echo [INFO] Starting Live Binance Futures Daemon...
echo [INFO] Press Ctrl+C to stop trading gracefully at any time.
echo.

python live_daemon_binance.py

echo.
echo [INFO] Daemon has stopped.
echo.
pause
