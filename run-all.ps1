# run-all.ps1  (ejecutar desde la raíz del proyecto)
#si windows bloquea scripts: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned como admin una sola vez
$ErrorActionPreference = "Stop"

# --- Helpers ---
function Ensure-Command($cmd, $help) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "❌ No se encontró '$cmd'. $help" -ForegroundColor Red
    exit 1
  }
}

# --- Prechecks ---
Ensure-Command python "Instalá Python y asegurate que esté en PATH."
Ensure-Command npm "Instalá Node.js (incluye npm) y reiniciá la terminal."

# --- Go to script directory (project root) ---
Set-Location -Path $PSScriptRoot

Write-Host "📁 Proyecto: $PSScriptRoot"

# --- 1) Create venv if missing ---
if (-not (Test-Path ".\venv")) {
  Write-Host "🐍 Creando entorno virtual (venv)..." -ForegroundColor Cyan
  python -m venv venv
} else {
  Write-Host "🐍 venv ya existe." -ForegroundColor Green
}

# --- 2) Activate venv for install steps ---
$venvPython = ".\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "❌ No encuentro $venvPython. Algo falló creando el venv." -ForegroundColor Red
  exit 1
}

Write-Host "📦 Actualizando pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip | Out-Host

# --- 3) Install Python deps ---
if (Test-Path ".\requirements.txt") {
  Write-Host "📦 Instalando dependencias Python (requirements.txt)..." -ForegroundColor Cyan
  & $venvPython -m pip install -r .\requirements.txt | Out-Host
} else {
  Write-Host "⚠️ No existe requirements.txt. Instalando mínimos (uvicorn + fastapi)..." -ForegroundColor Yellow
  & $venvPython -m pip install uvicorn fastapi | Out-Host
}

# Asegurar uvicorn (por si no vino en requirements)
Write-Host "📦 Asegurando uvicorn..." -ForegroundColor Cyan
& $venvPython -m pip install uvicorn | Out-Host

# --- 4) Install dashboard deps (npm) if missing ---
if (-not (Test-Path ".\dashboard\package.json")) {
  Write-Host "❌ No encuentro dashboard\package.json. ¿Estás en la raíz correcta del repo?" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path ".\dashboard\node_modules")) {
  Write-Host "📦 Instalando dependencias del dashboard (npm install)..." -ForegroundColor Cyan
  Push-Location .\dashboard
  npm install | Out-Host
  Pop-Location
} else {
  Write-Host "📦 dashboard\node_modules ya existe. Omitiendo npm install." -ForegroundColor Green
}

# --- 5) Start services in separate windows ---
Write-Host "🚀 Levantando servicios..." -ForegroundColor Cyan

# API Server (FastAPI)
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd `"$PSScriptRoot`"; .\venv\Scripts\Activate.ps1; python -m uvicorn core.api_server:app --host 127.0.0.1 --port 8001"
)

Start-Sleep -Seconds 2

# Monitor
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd `"$PSScriptRoot`"; .\venv\Scripts\Activate.ps1; python main.py"
)

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd `"$PSScriptRoot\dashboard`"; npm run dev"
)

Write-Host ""
Write-Host "✅ Listo. Abrí: http://localhost:5173" -ForegroundColor Green
Write-Host "   Backend: http://localhost:8001" -ForegroundColor Green
