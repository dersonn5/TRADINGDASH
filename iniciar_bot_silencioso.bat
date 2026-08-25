@echo off
cd /d "%~dp0"
echo === BOT INICIADO EM MODO SILENCIOSO EM %date% %time% === >> logs_daemon.txt
python -X utf8 -m execution.live_daemon --feed MCP --interval 15 >> logs_daemon.txt 2>&1
