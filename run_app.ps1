$ErrorActionPreference = 'SilentlyContinue'

Write-Host "=================================="
Write-Host "       SunLeo App Launcher        "
Write-Host "=================================="
Write-Host ""
Write-Host "1. Cleaning up old processes (Freeing ports 8000, 8001 & 8501)..."

# Function to safely kill processes on a specific port
function Clear-Port($port) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        # Select unique process IDs
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $pids) {
            Write-Host "   [!] Found process ($pid) using port $port. Terminating..."
            taskkill /PID $pid /F /T 2>&1 | Out-Null
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "   [ok] Port $port is free."
    }
}

Clear-Port 8000
Clear-Port 8001
Clear-Port 8501

Write-Host "Waiting briefly for ports to be fully released..."
Start-Sleep -Seconds 2

$baseDir = Get-Location

Write-Host "2. Upgrading yt-dlp to latest version..."
& ".venv\Scripts\pip.exe" install --upgrade yt-dlp --quiet 2>&1 | Out-Null
Write-Host "   -> yt-dlp upgraded."

Write-Host "3. Starting YTConverter Backend (port 8000) in a new window..."
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$baseDir'; & '.\\.venv\\Scripts\\Activate.ps1'; cd backend/ytconverter; uvicorn app.main:app --port 8000`""
Write-Host "   -> YTConverter launched."

Start-Sleep -Seconds 2

Write-Host "4. Starting Discovery/Recommendation Service (port 8001) in a new window..."
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$baseDir'; & '.\\.venv\\Scripts\\Activate.ps1'; cd backend/recommendation_service; uvicorn app.main:app --port 8001`""
Write-Host "   -> Discovery Service launched."

# Wait for both backends to be ready before starting frontend
Start-Sleep -Seconds 4

Write-Host "5. Starting Frontend (Streamlit) on port 8501 in a new window..."
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$baseDir'; & '.\\.venv\\Scripts\\Activate.ps1'; cd frontend; streamlit run app/home.py --server.port 8501`""
Write-Host "   -> Frontend launched."

Write-Host ""
Write-Host "=================================="
Write-Host "        Startup Complete!         "
Write-Host "=================================="
Write-Host ""
Write-Host "  Backend (YTConverter):  http://localhost:8000"
Write-Host "  Backend (Discovery):    http://localhost:8001"
Write-Host "  Frontend (Streamlit):   http://localhost:8501"
Write-Host ""
Write-Host "You can close this window now. The apps are running in separate windows."
Start-Sleep -Seconds 3
