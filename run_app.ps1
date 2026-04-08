$ErrorActionPreference = 'SilentlyContinue'

Write-Host "=================================="
Write-Host "       SunLeo App Launcher        "
Write-Host "=================================="
Write-Host ""
Write-Host "1. Cleaning up old processes (Freeing ports 8000 & 8501)..."

# Function to safely kill processes on a specific port
function Clear-Port($port) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        # Select unique process IDs
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $pids) {
            Write-Host "   [!] Found process ($pid) using port $port. Terminating..."
            # Use taskkill /T to kill process and children. We kill it multiple times if needed.
            taskkill /PID $pid /F /T 2>&1 | Out-Null
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "   [ok] Port $port is free."
    }
}

Clear-Port 8000
Clear-Port 8501

Write-Host "Waiting briefly for ports to be fully released..."
Start-Sleep -Seconds 2

$baseDir = Get-Location

Write-Host "2. Upgrading yt-dlp to latest version..."
& ".venv\Scripts\pip.exe" install --upgrade yt-dlp --quiet 2>&1 | Out-Null
Write-Host "   -> yt-dlp upgraded."

Write-Host "3. Starting Backend (Uvicorn) in a new window..."
# Starts backend in a new Powershell Window (no --reload to prevent killing ffmpeg mid-download)
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$baseDir'; & '.\.venv\Scripts\Activate.ps1'; cd backend/ytconverter; uvicorn app.main:app --port 8000`""
Write-Host "   -> Backend launched."

# Wait a few seconds to let the backend start up before starting the frontend
Start-Sleep -Seconds 3

Write-Host "4. Starting Frontend (Streamlit) in a new window..."
# Starts frontend in a new Powershell Window
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$baseDir'; & '.\.venv\Scripts\Activate.ps1'; cd frontend; streamlit run app/home.py --server.port 8501`""
Write-Host "   -> Frontend launched."

Write-Host ""
Write-Host "=================================="
Write-Host "        Startup Complete!         "
Write-Host "=================================="
Write-Host "You can close this window now. The apps are running in the new windows."
Start-Sleep -Seconds 3
