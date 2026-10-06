param(
    [string]$LauncherPath
)

$ErrorActionPreference = "Stop"

Write-Host "Iniciando o Revisor Livro..." -ForegroundColor Cyan
Write-Host ""

if (-not $LauncherPath) {
    throw "LauncherPath nao informado."
}

$projectWinDir = [System.IO.Path]::GetDirectoryName($LauncherPath)
$projectWslDir = $null
$distro = $null

if ($projectWinDir -match '^\\\\wsl\.localhost\\([^\\]+)\\(.+)$') {
    $distro = $matches[1]
    $projectWslDir = "/" + ($matches[2] -replace '\\', '/')
} else {
    $projectWslDir = (wsl.exe wslpath -a -u $projectWinDir).Trim()
}

if (-not $projectWslDir) {
    throw "Nao foi possivel localizar a pasta do projeto dentro do WSL."
}

Write-Host "Projeto Windows: $projectWinDir"
Write-Host "Projeto WSL: $projectWslDir"
if ($distro) {
    Write-Host "Distribuicao WSL: $distro"
}
Write-Host ""

if ($distro) {
    & wsl.exe -d $distro bash -lc "cd '$projectWslDir' && ./scripts/launch-author-mode.sh"
} else {
    & wsl.exe bash -lc "cd '$projectWslDir' && ./scripts/launch-author-mode.sh"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "O launcher encontrou um erro ao iniciar o revisor." -ForegroundColor Red
}
