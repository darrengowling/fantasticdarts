# Darts Fantasy Auction - Startup Script
# Starts both backend and frontend servers

Write-Host "Starting Darts Fantasy Auction..." -ForegroundColor Green

# Check if backend virtual environment exists
if (-not (Test-Path "backend\.venv")) {
    Write-Host "Virtual environment not found. Please run setup first." -ForegroundColor Red
    exit 1
}

# Start Backend Server
Write-Host "`nStarting backend server on port 8001..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\.venv\Scripts\activate.bat; python darts_server.py"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "Starting frontend server on port 3000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm start"

Write-Host "`n✅ Servers starting..." -ForegroundColor Green
Write-Host "Backend:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
