# ytconverter (in-memory queue, zero-cost)

A minimal YouTube → MP3 converter with a **single in-memory queue** (no DB, no S3). It downloads and converts on the server, then lets the client download the MP3.

## What this does

- Accepts a YouTube URL
- Enqueues a conversion job (1 worker)
- Converts to MP3 using `yt-dlp` + `ffmpeg`
- Stores MP3 locally in the downloads folder and serves it back

## Where the MP3 is saved

Files are saved on the server at:

- backend/ytconverter/downloads

## Requirements

- Python 3.11+
- ffmpeg installed and on PATH

## Step-by-step test guide (Windows PowerShell)

### 1) Go to the module folder

```powershell
Set-Location c:\Users\shour\Desktop\SunLeo\backend\ytconverter
```

### 2) Create & activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```powershell
pip install -r requirements.txt
```

### 4) Run the API

```powershell
uvicorn app.main:app --reload
```

### 5) Send a conversion request

```powershell
$body = @{ youtube_url = "https://www.youtube.com/watch?v=VIDEO_ID" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/convert" -Method Post -ContentType "application/json" -Body $body
```

### 6) Check job status

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/status/JOB_ID" -Method Get
```

### 7) Download the MP3 when ready

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/download/JOB_ID" -OutFile "downloaded.mp3"
```

## Notes

- The queue is **in-memory** and resets if the server restarts.
- If multiple users submit at once, jobs are processed sequentially (1 at a time).
- For demos, this keeps the app stable with zero cost.
