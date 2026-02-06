from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .converter import convert_youtube_to_mp3
from .models import ConvertRequest, ConvertResponse, JobRecord, JobStatus, StatusResponse
from .queue import InMemoryJobQueue
from .utils import extract_video_id, validate_youtube_url

BASE_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = BASE_DIR / "downloads"

jobs: Dict[str, JobRecord] = {}
queue = InMemoryJobQueue()


async def _process_job(job_id: str) -> None:
    job = jobs[job_id]
    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)

    try:
        output_path, title, video_id = await asyncio.to_thread(
            convert_youtube_to_mp3, job.url, DOWNLOAD_DIR
        )
        job.file_path = str(output_path)
        job.title = title
        job.video_id = video_id
        job.status = JobStatus.completed
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = str(exc)
    finally:
        job.finished_at = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    queue.start(_process_job)
    yield
    await queue.stop()


app = FastAPI(title="ytconverter", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    if not validate_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    job_id = uuid4().hex
    video_id = extract_video_id(request.youtube_url) or "unknown"
    jobs[job_id] = JobRecord(job_id=job_id, url=request.youtube_url, video_id=video_id)
    await queue.enqueue(job_id)

    return ConvertResponse(job_id=job_id, status=JobStatus.queued)


@app.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    download_url = None
    if job.status == JobStatus.completed:
        download_url = f"/download/{job_id}"

    return StatusResponse(
        job_id=job.job_id,
        status=job.status,
        title=job.title,
        error=job.error,
        download_url=download_url,
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.completed or not job.file_path:
        raise HTTPException(status_code=409, detail="File not ready")

    filename = f"{job.title or job.video_id}.mp3"
    return FileResponse(path=job.file_path, filename=filename, media_type="audio/mpeg")
