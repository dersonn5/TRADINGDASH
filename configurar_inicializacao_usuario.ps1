# =====================================================================
# CONFIGURAÇÃO DE INICIALIZAÇÃO VIA PASTA STARTUP (SEM REQUISITAR ADMIN)
# =====================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LauncherPath = Join-Path $ScriptDir "iniciar_bot_oculto.vbs"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO INICIALIZAÇÃO AUTOMÁTICA (MÉTODO USER LNK)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $LauncherPath)) {
    Write-Host "[ERRO] Arquivo launcher ($LauncherPath) não encontrado." -ForegroundColor Red
    Exit
}

# 1. Obter caminho da pasta Startup do Usuário
$StartupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$ShortcutPath = [System.IO.Path]::Combine($StartupFolder, "TradingAI_Live_Daemon.lnk")

Write-Host "Pasta de inicialização do usuário: $StartupFolder" -ForegroundColor Yellow
Write-Host "Destino do atalho: $ShortcutPath" -ForegroundColor Yellow
Write-Host ""

# 2. Criar o atalho via WScript.Shell
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $LauncherPath
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.Description = "Inicializa silenciosamente o Bot de Trading AI em segundo plano."
    $Shortcut.Save()
    
    Write-Host "===========================================================" -ForegroundColor Green
    Write-Host "  [SUCESSO] ATALHO DE INICIALIZAÇÃO CRIADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "  O bot iniciará de forma 100% silenciosa a cada login" -ForegroundColor Green
    Write-Host "  do usuário no Windows, sem precisar de privilégios admin!" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Green
} catch {
    Write-Host "[ERRO CRÍTICO] Falha ao criar o atalho de inicialização: $_" -ForegroundColor Red
}
