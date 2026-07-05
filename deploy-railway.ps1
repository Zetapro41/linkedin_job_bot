# Despliegue del LinkedIn Job Bot en Railway (24/7)
# Uso: .\deploy-railway.ps1

$ErrorActionPreference = "Stop"
$Railway = "npx --yes @railway/cli@latest"

Write-Host "=== LinkedIn Job Bot PRO - Deploy Railway ===" -ForegroundColor Cyan

& $Railway whoami 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No estas logueado en Railway. Ejecuta:" -ForegroundColor Yellow
    Write-Host "  npx @railway/cli login" -ForegroundColor White
    exit 1
}

if (-not (Test-Path ".railway")) {
    Write-Host "Vinculando proyecto en Railway..." -ForegroundColor Green
    & $Railway link
}

if (Test-Path ".env") {
    Write-Host "Configurando variables de entorno..." -ForegroundColor Green
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim()
            if ($key -and $val) {
                & $Railway variables set "$key=$val" 2>$null
            }
        }
    }
    & $Railway variables set "DATABASE_PATH=/data/linkedin_bot.db"
} else {
    Write-Host "AVISO: No hay .env. Copia .env.example a .env y configura BOT_TOKEN." -ForegroundColor Yellow
    Write-Host "O configura las variables manualmente en railway.app" -ForegroundColor Yellow
}

Write-Host "Desplegando a Railway..." -ForegroundColor Green
& $Railway up --detach

Write-Host ""
Write-Host "Deploy enviado. Pasos en railway.app:" -ForegroundColor Cyan
Write-Host "  1. Service -> Settings -> Add Volume montado en /data" -ForegroundColor White
Write-Host "  2. Settings -> Connect Repo (GitHub) para deploy automatico en cada push" -ForegroundColor White
Write-Host "  3. Verifica logs: npx @railway/cli logs" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE: Solo una instancia del bot debe estar activa (evita error 409 de Telegram)." -ForegroundColor Yellow