# =====================================================================
# CONFIGURAÇÃO AUTOMÁTICA DE INICIALIZAÇÃO NO AGENDADOR DE TAREFAS
# =====================================================================

$TaskName = "TradingAI_Live_Daemon"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LauncherPath = Join-Path $ScriptDir "iniciar_bot_oculto.vbs"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO INICIALIZAÇÃO AUTOMÁTICA DO BOT (WINDOWS)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Caminho do script a registrar: $LauncherPath" -ForegroundColor Yellow

# Verificar se o arquivo VBS existe
if (-not (Test-Path $LauncherPath)) {
    Write-Host "[ERRO] Arquivo launcher ($LauncherPath) nao encontrado." -ForegroundColor Red
    Exit
}

# 1. Configurar ação da tarefa (Executar o script VBS silenciosamente)
# Como é um arquivo VBS, chamamos o interpretador de script padrão wscript.exe
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$LauncherPath`""

# 2. Configurar o gatilho (Ao inicializar o sistema / Windows Startup)
# Ou ao fazer logon do usuário (recomendado para interagir com o ambiente gráfico se necessário, embora o MCP funcione em segundo plano)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# 3. Configurar definições da tarefa (Reiniciar se falhar, rodar sob demanda, etc)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)

# 4. Registrar a tarefa no Windows
Write-Host "[1/2] Registrando tarefa no Windows Task Scheduler..." -ForegroundColor Yellow

# Remover se já existir
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Super Agente de Trading IA - Monitoramento de Killzones e Execução Cognitiva." -Force

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "  [SUCESSO] BOT AGENDADO E AUTOMATIZADO COM SUCESSO!" -ForegroundColor Green
Write-Host "  O robô iniciará silenciosamente toda vez que você ligar" -ForegroundColor Green
Write-Host "  e logar no computador, operando em background nas Killzones." -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
