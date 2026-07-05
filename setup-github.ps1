# Conecta este proyecto a GitHub para deploy automatico en Railway
# Uso: .\setup-github.ps1 -RepoUrl https://github.com/TU_USUARIO/linkedin-job-bot.git

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Green
    git init
    git branch -M main
}

git add .
git commit -m "LinkedIn Job Bot PRO - listo para Railway" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Sin cambios nuevos para commitear (o ya existe el commit)." -ForegroundColor Yellow
}

$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add origin $RepoUrl
    Write-Host "Remote origin agregado: $RepoUrl" -ForegroundColor Green
} else {
    git remote set-url origin $RepoUrl
    Write-Host "Remote origin actualizado: $RepoUrl" -ForegroundColor Green
}

Write-Host "Subiendo a GitHub..." -ForegroundColor Green
git push -u origin main

Write-Host ""
Write-Host "Listo. Ahora en railway.app:" -ForegroundColor Cyan
Write-Host "  1. Abre tu proyecto -> Service -> Settings -> Source" -ForegroundColor White
Write-Host "  2. Connect Repo -> elige $RepoUrl" -ForegroundColor White
Write-Host "  3. Cada git push redeployara el bot automaticamente" -ForegroundColor White