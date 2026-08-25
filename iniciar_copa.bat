@echo off
title Cockpit Copa BTG - Inicializador
echo ===================================================
echo INICIANDO COCKPIT COPA BTG (Backend + Frontend)
echo ===================================================

cd /d "%~dp0"

echo [1/3] Inicializando Backend FastAPI (Porta 8010)...
start "Cockpit Copa API (8010)" cmd /k "python -m uvicorn cockpit_api:app --port 8010 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Inicializando Frontend Next.js (Porta 3000)...
start "Cockpit Front Next.js (3000)" cmd /k "cd cockpit && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Abrindo painel no navegador...
start http://localhost:3000/copa

echo.
echo Tudo pronto! O Cockpit Copa BTG esta ativo.
echo Pressione qualquer tecla para fechar este inicializador.
pause >nul
