param(
    [string]$Python = "python",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Frontend = Join-Path $ProjectRoot "frontend"
$BuildEnv = Join-Path $ProjectRoot ".desktop-build"
$Release = Join-Path $ProjectRoot "release"

Write-Host "Building AUnitedAI web interface..."
Push-Location $Frontend
try {
    & node "node_modules\vite\bin\vite.js" build
} finally {
    Pop-Location
}

if (-not $SkipInstall) {
    if (-not (Test-Path (Join-Path $BuildEnv "Scripts\python.exe"))) {
        & $Python -m venv $BuildEnv
    }
    $BuildPython = Join-Path $BuildEnv "Scripts\python.exe"
    & $BuildPython -m pip install --upgrade pip
    & $BuildPython -m pip install -e "$ProjectRoot[desktop]"
} else {
    $BuildPython = Join-Path $BuildEnv "Scripts\python.exe"
}

if (-not (Test-Path $BuildPython)) {
    throw "Desktop build environment is missing. Run without -SkipInstall first."
}

Write-Host "Packaging Windows application..."
& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name AUnitedAI `
    --icon (Join-Path $Frontend "public\aunitedai-logo.png") `
    --distpath $Release `
    --workpath (Join-Path $ProjectRoot "build\desktop") `
    --specpath (Join-Path $ProjectRoot "build") `
    --add-data "$(Join-Path $Frontend 'dist');frontend_dist" `
    --add-data "$(Join-Path $Frontend 'public\aunitedai-logo.png');." `
    --add-data "$(Join-Path $ProjectRoot 'worker_config.json');." `
    --collect-all chromadb `
    --collect-all langchain `
    --collect-all langgraph `
    --collect-all webview `
    (Join-Path $ProjectRoot "desktop_launcher.py")

$Exe = Join-Path $Release "AUnitedAI\AUnitedAI.exe"
if (-not (Test-Path $Exe)) { throw "Packaging finished without producing $Exe" }
Write-Host "AUnitedAI desktop app created at: $Exe"
