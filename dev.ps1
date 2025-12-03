# Simple dev server launcher - runs both backend and frontend
Write-Host "🎯 Starting Darts Fantasy Auction Dev Servers..." -ForegroundColor Green

# Start backend in background
Write-Host "`nStarting backend on port 8001..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\User\Workspace\file_import_manager\darts-fantasy-auction\backend"
    & .\.venv\Scripts\python.exe darts_server.py
}

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend in foreground (so you see the output)
Write-Host "Starting frontend on port 3000..." -ForegroundColor Cyan
Write-Host "`n✅ Backend running in background (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "✅ Frontend starting in foreground..." -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop both servers`n" -ForegroundColor Yellow

Set-Location "C:\Users\User\Workspace\file_import_manager\darts-fantasy-auction\frontend"
npm start

# When frontend stops (Ctrl+C), clean up backend
Write-Host "`nStopping backend server..." -ForegroundColor Yellow
Stop-Job -Job $backendJob
Remove-Job -Job $backendJob
Write-Host "✅ All servers stopped" -ForegroundColor Green
