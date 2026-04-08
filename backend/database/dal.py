"""
Data Access Layer (DAL) for SunLeo.

Contains repository classes that encapsulate all SQL operations.
These are the ONLY modules in the application that execute SQL queries.

Classes:
    JobDAL      — CRUD operations for the `jobs` table
    FeedbackDAL — CRUD operations for the `feedback` table
"""
from __future__ import annotations

import json
from typing import Optional

import aiosqlite

from .models import JobRow, FeedbackRow


class JobDAL:
    """
    Data Access Layer for conversion job records.

    Implements the Repository Pattern — provides a collection-like
    interface over the `jobs` table, hiding all SQL details.
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def create_job(self, job_id: str, url: str, video_id: str) -> JobRow:
        """
        Insert a new job record with status 'queued'.

        Args:
            job_id:   Unique identifier (UUID hex).
            url:      Original YouTube URL.
            video_id: Extracted YouTube video ID.

        Returns:
            The newly created JobRow.
        """
        await self._db.execute(
            """
            INSERT INTO jobs (job_id, url, video_id, status)
            VALUES (?, ?, ?, 'queued')
            """,
            (job_id, url, video_id),
        )
        await self._db.commit()
        return JobRow(job_id=job_id, url=url, video_id=video_id, status="queued")

    async def get_job(self, job_id: str) -> Optional[JobRow]:
        """
        Retrieve a single job by its ID.

        Returns:
            JobRow if found, None otherwise.
        """
        cursor = await self._db.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return JobRow.from_row(row)

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        *,
        title: Optional[str] = None,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> None:
        """
        Update the status and optional fields of a job.

        This method dynamically builds the SET clause to only update
        fields that are explicitly provided (not None).
        """
        fields = {"status": status}
        if title is not None:
            fields["title"] = title
        if file_path is not None:
            fields["file_path"] = file_path
        if error is not None:
            fields["error"] = error
        if metadata is not None:
            fields["metadata"] = json.dumps(metadata)
        if started_at is not None:
            fields["started_at"] = started_at
        if finished_at is not None:
            fields["finished_at"] = finished_at

        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [job_id]

        await self._db.execute(
            f"UPDATE jobs SET {set_clause} WHERE job_id = ?",
            values,
        )
        await self._db.commit()

    async def list_jobs(self, limit: int = 50) -> list[JobRow]:
        """
        Retrieve the most recent jobs, ordered by creation time (newest first).
        """
        cursor = await self._db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [JobRow.from_row(r) for r in rows]

    async def delete_old_jobs(self, age_seconds: int = 3600) -> int:
        """
        Delete jobs whose finished_at timestamp is older than `age_seconds`.

        Returns:
            Number of rows deleted.
        """
        cursor = await self._db.execute(
            """
            DELETE FROM jobs
            WHERE finished_at IS NOT NULL
              AND (julianday('now') - julianday(finished_at)) * 86400 > ?
            """,
            (age_seconds,),
        )
        await self._db.commit()
        return cursor.rowcount


class FeedbackDAL:
    """
    Data Access Layer for user feedback records.

    Replaces the previous flat-file JSON storage with structured
    SQLite storage, enabling filtering and querying.
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def save_feedback(
        self, name: str, email: str, category: str, message: str
    ) -> int:
        """
        Insert a new feedback record.

        Returns:
            The auto-generated ID of the new feedback row.
        """
        cursor = await self._db.execute(
            """
            INSERT INTO feedback (name, email, category, message)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, category, message),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_all_feedback(self) -> list[FeedbackRow]:
        """Retrieve all feedback records, newest first."""
        cursor = await self._db.execute(
            "SELECT * FROM feedback ORDER BY timestamp DESC"
        )
        rows = await cursor.fetchall()
        return [FeedbackRow.from_row(r) for r in rows]

    async def get_feedback_by_category(self, category: str) -> list[FeedbackRow]:
        """
        Retrieve feedback filtered by category.

        Args:
            category: One of 'Bug Report', 'Feature Request',
                      'General Feedback', or 'Other'.
        """
        cursor = await self._db.execute(
            "SELECT * FROM feedback WHERE category = ? ORDER BY timestamp DESC",
            (category,),
        )
        rows = await cursor.fetchall()
        return [FeedbackRow.from_row(r) for r in rows]
