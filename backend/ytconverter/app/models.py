from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ConvertRequest(BaseModel):
    youtube_url: str = Field(..., description="YouTube URL")


class ConvertResponse(BaseModel):
    job_id: str
    status: JobStatus


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    title: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class JobRecord:
    job_id: str
    url: str
    video_id: str
    status: JobStatus = JobStatus.queued
    title: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
