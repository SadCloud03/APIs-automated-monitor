$ErrorActionPreference = "Stop"

Write-Host "Starting API Monitor project"

# Go to project root
Set-Location -Path $PSScriptRoot

# ---- PRECHECKS ----
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH"
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm (Node.js) not found in PATH"
    exit 1
}

# ---- VENV ----
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} 
else {
    Write-Host "Virtual environment already exists"
}

$venvPython = ".\venv\Scripts\python.exe"

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

# ---- PYTHON DEPS ----
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..."
    & $venvPython -m pip install -r requirements.txt
}
else {
    Write-Host "No requirements.txt found, installing minimal deps..."
    & $venvPython -m pip install fastapi uvicorn
}

# Ensure uvicorn exists
& $venvPython -m pip install uvicorn

# ---- FRONTEND DEPS ----
if (-not (Test-Path "dashboard\package.json")) {
    Write-Host "dashboard/package.json not found"
    exit 1
}

if (-not (Test-Path "dashboard\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location dashboard
    npm install
    Pop-Location
}
else {
    Write-Host "Frontend dependencies already installed"
}

# ---- START SERVICES ----
Write-Host "Starting services..."

# API Server
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot`"; . .\venv\Scripts\Activate.ps1; python -m uvicorn core.api_server:app --host 127.0.0.1 --port 8001"

Start-Sleep -Seconds 2

# Monitor
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot`"; . .\venv\Scripts\Activate.ps1; python main.py"

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot\dashboard`"; npm run dev"

Write-Host ""
Write-Host "ALL SERVICES STARTED"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8001"
