
Write-Host "Activating WMS System..." -ForegroundColor Cyan

# 1. 啟動後端 (新視窗)
Write-Host "Activating Backend API (Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run uvicorn app.main:app --reload"

# 等待幾秒讓後端跑起來
Start-Sleep -Seconds 3

# 2. 啟動前端 (新視窗)
Write-Host "Activating Frontend Web (Port 5000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run python app.py"

Write-Host "WMS System Activated!" -ForegroundColor Cyan
