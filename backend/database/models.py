"""
Data Transfer Objects (DTOs) for the SunLeo DAL.

These dataclasses represent rows from the database tables.
They serve as a type-safe boundary between the DAL and the
rest of the application — the app never touches raw SQL rows directly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobRow:
    """Represents a single row from the `jobs` table."""
    job_id: str
    url: str
    video_id: str
    status: str = "queued"
    title: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = field(default=None)
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> JobRow:
        """
        Factory method to create a JobRow from an aiosqlite.Row.
        Handles JSON deserialization of the metadata column.
        """
        metadata_raw = row["metadata"]
        metadata = json.loads(metadata_raw) if metadata_raw else None

        return cls(
            job_id=row["job_id"],
            url=row["url"],
            video_id=row["video_id"],
            status=row["status"],
            title=row["title"],
            file_path=row["file_path"],
            error=row["error"],
            metadata=metadata,
            created_at=row["created_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )


@dataclass
class FeedbackRow:
    """Represents a single row from the `feedback` table."""
    id: Optional[int]
    name: str
    email: str
    category: str
    message: str
    timestamp: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> FeedbackRow:
        """Factory method to create a FeedbackRow from an aiosqlite.Row."""
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            category=row["category"],
            message=row["message"],
            timestamp=row["timestamp"],
        )
