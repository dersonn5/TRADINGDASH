Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  INICIALIZANDO TRADINGVIEW COM PORTA DE DEPURACAO (9222)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Localizar o aplicativo TradingView
Write-Host "[1/3] Localizando pasta do app no Windows Apps..." -ForegroundColor Yellow
$pkg = Get-AppxPackage -Name "TradingView*"
if (-not $pkg) {
    Write-Host "[ERRO] TradingView Desktop nao foi encontrado no sistema." -ForegroundColor Red
    Exit
}

$installPath = $pkg.InstallLocation
$exePath = Join-Path $installPath "TradingView.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "[ERRO] Executavel nao encontrado em: $exePath" -ForegroundColor Red
    Exit
}

Write-Host "[OK] Encontrado em: $exePath" -ForegroundColor Green
Write-Host ""

# 2. Fechar instancias existentes
Write-Host "[2/3] Encerrando instancias abertas do TradingView..." -ForegroundColor Yellow
$procs = Get-Process -Name "TradingView" -ErrorAction SilentlyContinue
if ($procs) {
    Stop-Process -Name "TradingView" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 3. Iniciar com a porta de depuracao
Write-Host "[3/3] Iniciando TradingView com porta de depuracao remota (CDP 9222)..." -ForegroundColor Yellow
Start-Process -FilePath $exePath -ArgumentList "--remote-debugging-port=9222"

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "  [SUCESSO] TRADINGVIEW INICIADO COM DEPURACAO NA PORTA 9222" -ForegroundColor Green
Write-Host "  Agora a IA pode ver e interagir com seus graficos!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
