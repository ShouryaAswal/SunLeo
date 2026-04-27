from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .converter import convert_youtube_to_mp3
from .models import BatchConvertRequest, BatchConvertResponse, ConvertRequest, ConvertResponse, JobRecord, JobStatus, StatusResponse
from .queue import InMemoryJobQueue
from .utils import extract_video_id, validate_youtube_url

BASE_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = BASE_DIR / "downloads"

jobs: Dict[str, JobRecord] = {}
queue = InMemoryJobQueue(concurrency=3)


async def _process_job(job_id: str) -> None:
    job = jobs[job_id]
    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)

    try:
        output_path, title, video_id, metadata = await asyncio.to_thread(
            convert_youtube_to_mp3, job.url, DOWNLOAD_DIR
        )
        job.file_path = str(output_path)
        job.title = title
        job.video_id = video_id
        job.metadata = metadata
        job.status = JobStatus.completed
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = str(exc)
    finally:
        job.finished_at = datetime.now(timezone.utc)


async def _cleanup_old_files_task():
    """Background task to delete MP3 files older than 1 hour (3600 seconds)"""
    while True:
        try:
            now = time.time()
            for file_path in DOWNLOAD_DIR.glob("*.mp3"):
                if file_path.is_file():
                    file_age = now - file_path.stat().st_mtime
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
            
            # Additional cleanup of in-memory job status tracker to prevent memory leaks over time
            job_ids_to_remove = []
            for j_id, jobr in jobs.items():
                if jobr.finished_at and (datetime.now(timezone.utc) - jobr.finished_at).total_seconds() > 3600:
                    job_ids_to_remove.append(j_id)
            for j_id in job_ids_to_remove:
                del jobs[j_id]
                
        except Exception:
            pass
        await asyncio.sleep(600)  # run cleanup check every 10 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    queue.start(_process_job)
    cleanup_task = asyncio.create_task(_cleanup_old_files_task())
    yield
    cleanup_task.cancel()
    await queue.stop()


app = FastAPI(title="ytconverter", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    return ConvertResponse(job_id=job_id, status=JobStatus.queued, url=request.youtube_url)


@app.post("/convert/batch", response_model=BatchConvertResponse)
async def convert_batch(request: BatchConvertRequest):
    if len(request.urls) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 URLs allowed per batch")
        
    responses = []
    for url in request.urls:
        if not validate_youtube_url(url):
            raise HTTPException(status_code=400, detail=f"Invalid YouTube URL: {url}")
            
        job_id = uuid4().hex
        video_id = extract_video_id(url) or "unknown"
        jobs[job_id] = JobRecord(job_id=job_id, url=url, video_id=video_id)
        await queue.enqueue(job_id)
        responses.append(ConvertResponse(job_id=job_id, status=JobStatus.queued, url=url))

    return BatchConvertResponse(jobs=responses)


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
        metadata=job.metadata,
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.completed or not job.file_path:
        raise HTTPException(status_code=409, detail="File not ready")

    filename = f"{job.title or job.video_id}.mp3"
    return FileResponse(
        path=job.file_path, 
        filename=filename, 
        media_type="audio/mpeg",
        content_disposition_type="inline"
    )


# ── Audio Editor endpoints ────────────────────────────────────────────────────

from fastapi import File, UploadFile, Form
from fastapi.responses import Response
from .audio_editor import EditParams, process_audio, estimate_sizes


@app.post("/audio/edit")
async def audio_edit(
    file: UploadFile = File(...),
    trim_start_ms: int = Form(0),
    trim_end_ms: int = Form(-1),
    fade_in_ms: int = Form(0),
    fade_out_ms: int = Form(0),
    bass_boost_db: float = Form(0.0),
    treble_boost_db: float = Form(0.0),
    volume_change_db: float = Form(0.0),
    speed_factor: float = Form(1.0),
    output_format: str = Form("mp3"),
    output_quality: str = Form("192"),
):
    """Process an audio file with the given edit parameters."""
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(file_bytes) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")

    params = EditParams(
        trim_start_ms=trim_start_ms,
        trim_end_ms=trim_end_ms if trim_end_ms >= 0 else None,
        fade_in_ms=fade_in_ms,
        fade_out_ms=fade_out_ms,
        bass_boost_db=bass_boost_db,
        treble_boost_db=treble_boost_db,
        volume_change_db=volume_change_db,
        speed_factor=speed_factor,
        output_format=output_format,
        output_quality=output_quality,
    )

    try:
        result_bytes, ext, mime = await asyncio.to_thread(process_audio, file_bytes, params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")

    filename = f"sunleo_edited.{ext}"
    return Response(
        content=result_bytes,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(result_bytes)),
        },
    )


@app.post("/audio/estimate")
async def audio_estimate(file: UploadFile = File(...)):
    """Estimate output file sizes for all format/quality combinations."""
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = await asyncio.to_thread(estimate_sizes, file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {exc}")

    return result

