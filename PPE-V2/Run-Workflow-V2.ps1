$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created PPE-V2/.env from .env.example. Update your API key before running."
    }
}

if (-not (Test-Path "..\ppe\.venv\Scripts\python.exe")) {
    throw "Expected virtual environment at ..\ppe\.venv. Please create it first."
}

& "..\ppe\.venv\Scripts\python.exe" -m pip install -r "requirements.txt"
& "..\ppe\.venv\Scripts\python.exe" "main.py"
