# correr con .\run-all.ps1
$ErrorActionPreference = "Stop"

Write-Host "Starting API Monitor project"

# ------------------------------------------------------------------
# Go to project root
# ------------------------------------------------------------------
Set-Location -Path $PSScriptRoot

# ------------------------------------------------------------------
# PRECHECKS
# ------------------------------------------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH"
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm (Node.js) not found in PATH"
    exit 1
}

# ------------------------------------------------------------------
# LOAD .env
# ------------------------------------------------------------------
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Write-Host "Loading .env..."
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $key, $val = $line.Split("=", 2)
            $key = $key.Trim()
            $val = $val.Trim().Trim('"').Trim("'")
            if ($key) {
                Set-Item -Path "Env:$key" -Value $val
            }
        }
    }
}

# ------------------------------------------------------------------
# VENV
# ------------------------------------------------------------------
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists"
}

$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$activateVenv = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

# ------------------------------------------------------------------
# PYTHON DEPENDENCIES
# ------------------------------------------------------------------
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..."
    & $venvPython -m pip install -r requirements.txt
} else {
    Write-Host "No requirements.txt found, installing minimal deps..."
    & $venvPython -m pip install fastapi uvicorn requests
}

& $venvPython -m pip install uvicorn

# ------------------------------------------------------------------
# FRONTEND DEPENDENCIES
# ------------------------------------------------------------------
if (-not (Test-Path "dashboard\package.json")) {
    Write-Host "dashboard/package.json not found"
    exit 1
}

if (-not (Test-Path "dashboard\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location dashboard
    npm install
    Pop-Location
} else {
    Write-Host "Frontend dependencies already installed"
}

# ------------------------------------------------------------------
# START SERVICES
# ------------------------------------------------------------------
Write-Host "Starting services..."

# API Server
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot`"; . `"$activateVenv`"; python -m uvicorn core.api_server:app --host 127.0.0.1 --port 8001"

Start-Sleep -Seconds 2

# Monitor
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot`"; . `"$activateVenv`"; python main.py"

Start-Sleep -Seconds 2

# Telegram Bot
if (Test-Path "telegram_bot.py") {
    if ($env:TELEGRAM_BOT_TOKEN) {
        Start-Process powershell -ArgumentList `
            "-NoExit",
            "-Command",
            "cd `"$PSScriptRoot`"; . `"$activateVenv`"; python telegram_bot.py"
        Write-Host "Telegram bot started"
    } else {
        Write-Host "telegram_bot.py found but TELEGRAM_BOT_TOKEN is not set"
    }
} else {
    Write-Host "telegram_bot.py not found, skipping Telegram bot"
}

Start-Sleep -Seconds 2

# Demo API (optional)
if (Test-Path "demo_api.py") {
    Start-Process powershell -ArgumentList `
        "-NoExit",
        "-Command",
        "cd `"$PSScriptRoot`"; . `"$activateVenv`"; python demo_api.py"
    Write-Host "Demo API started"
} else {
    Write-Host "demo_api.py not found (optional)"
}

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "cd `"$PSScriptRoot\dashboard`"; npm run dev"

# ------------------------------------------------------------------
# DONE
# ------------------------------------------------------------------
Write-Host ""
Write-Host "ALL SERVICES STARTED"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8001"
Write-Host "Telegram: send /start to the bot"
Write-Host "Demo API: http://127.0.0.1:8000"
