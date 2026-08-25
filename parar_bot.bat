@echo off
title Trading AI - Parar Bot
cd /d "%~dp0"
echo =======================================================
echo   ENCERRANDO INSTANCIAS DO LIVE DAEMON EM EXECUCAO
echo =======================================================
echo.
wmic process where "commandline like '%%live_daemon%%'" delete
echo.
echo =======================================================
echo   [SUCESSO] Instancias do bot encerradas com sucesso!
echo =======================================================
echo === BOT ENCERRADO EM %date% %time% === >> logs_daemon.txt
pause
