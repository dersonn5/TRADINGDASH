@echo off
title Trading AI - Live Daemon Launcher
cd /d "%~dp0"
echo =======================================================
echo   INICIANDO SUPER BOT DE TRADING COGNITIVO ICT
echo =======================================================
echo   * Modo de Feed: MCP (TradingView)
echo   * logs gravando em tempo real...
echo =======================================================
python -X utf8 -m execution.live_daemon --feed MCP --interval 15
pause
