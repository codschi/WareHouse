Write-Host "Aggressive WMS Cleanup..."

# Kill ALL Python processes
Write-Host "Killing all Python processes..."
taskkill /F /IM python.exe 2>$null

# Kill ALL Uvicorn processes  
Write-Host "Killing all Uvicorn processes..."
taskkill /F /IM uvicorn.exe 2>$null

# Also kill by port as backup
$ports = @(5000, 8000)
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String ":$port" | Select-String "LISTENING"
    foreach ($conn in $connections) {
        $pid = ($conn -split '\s+')[-1]
        if ($pid -match '^\d+$') {
            Write-Host "Killing PID $pid on port $port"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Cleanup complete!"
