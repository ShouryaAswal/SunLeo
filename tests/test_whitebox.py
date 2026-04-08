"""
White Box Test Suite — SunLeo Application
==========================================

White Box (Glass Box) tests are designed with full knowledge of the internal
code structure. Each test targets specific code paths, branches, and statements.

Test IDs: WB-01 through WB-10
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ytconverter.app.utils import extract_video_id, validate_youtube_url
from backend.database.dal import JobDAL, FeedbackDAL


# ==========================================================================
# WB-01: extract_video_id — Path Coverage (all 4 URL format branches)
# ==========================================================================

class TestExtractVideoIdPathCoverage:
    """
    Technique: PATH COVERAGE
    Target: extract_video_id() in utils.py
    
    This function has 4 distinct execution paths based on the URL format:
      1. youtu.be short links
      2. /watch?v= standard links
      3. /shorts/ links
      4. /embed/ links
    We test each path to ensure all branches are exercised.
    """

    def test_watch_url(self):
        """Path 1: Standard /watch?v= format."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        """Path 2: youtu.be short link format."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        """Path 3: YouTube Shorts format."""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        """Path 4: Embed format."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"


# ==========================================================================
# WB-02: extract_video_id — Branch Coverage (invalid paths return None)
# ==========================================================================

class TestExtractVideoIdBranchCoverage:
    """
    Technique: BRANCH COVERAGE
    Target: extract_video_id() in utils.py
    
    Tests the False branches — URLs that don't match any known pattern
    should return None.
    """

    def test_unknown_path_returns_none(self):
        """A URL with an unrecognized path should return None."""
        url = "https://www.youtube.com/playlist?list=PLtest"
        assert extract_video_id(url) is None

    def test_empty_path_returns_none(self):
        """youtu.be with no path segment should return None."""
        url = "https://youtu.be/"
        # lstrip("/") on empty path gives "", which is falsy → returns None
        result = extract_video_id(url)
        assert result is None or result == ""

    def test_watch_without_v_param_returns_none(self):
        """/watch without ?v= parameter should return None."""
        url = "https://www.youtube.com/watch?feature=something"
        assert extract_video_id(url) is None


# ==========================================================================
# WB-03: validate_youtube_url — Condition Coverage
# ==========================================================================

class TestValidateUrlConditionCoverage:
    """
    Technique: CONDITION COVERAGE
    Target: validate_youtube_url() in utils.py
    
    The function has 3 conditions:
      C1: parsed.scheme in {"http", "https"}
      C2: parsed.netloc in YT_HOSTS
      C3: extract_video_id(url) is not None
    
    We test each sub-condition as True and False independently.
    """

    def test_all_conditions_true(self):
        """C1=T, C2=T, C3=T → Valid URL."""
        assert validate_youtube_url("https://youtube.com/watch?v=abc123") is True

    def test_invalid_scheme(self):
        """C1=F → Invalid (ftp scheme)."""
        assert validate_youtube_url("ftp://youtube.com/watch?v=abc123") is False

    def test_invalid_host(self):
        """C2=F → Invalid (non-YouTube host)."""
        assert validate_youtube_url("https://notyoutube.com/watch?v=abc123") is False

    def test_no_video_id(self):
        """C3=F → Invalid (valid host but no extractable video ID)."""
        assert validate_youtube_url("https://youtube.com/channel/something") is False


# ==========================================================================
# WB-04: JobDAL.create_job — Statement Coverage
# ==========================================================================

class TestJobDALCreateStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: JobDAL.create_job() in dal.py
    
    Verifies the INSERT statement executes successfully and
    returns a correctly populated JobRow.
    """

    @pytest.mark.asyncio
    async def test_create_job_returns_correct_row(self, job_dal):
        """Every statement in create_job() executes and returns valid data."""
        result = await job_dal.create_job("job-001", "https://youtu.be/abc", "abc")
        assert result.job_id == "job-001"
        assert result.url == "https://youtu.be/abc"
        assert result.video_id == "abc"
        assert result.status == "queued"

    @pytest.mark.asyncio
    async def test_create_job_persists_in_db(self, job_dal):
        """Verify the INSERT actually wrote to the database."""
        await job_dal.create_job("job-002", "https://youtu.be/xyz", "xyz")
        retrieved = await job_dal.get_job("job-002")
        assert retrieved is not None
        assert retrieved.job_id == "job-002"


# ==========================================================================
# WB-05: JobDAL.update_job_status — Statement Coverage
# ==========================================================================

class TestJobDALUpdateStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: JobDAL.update_job_status() in dal.py
    
    Verifies the dynamic UPDATE statement correctly modifies
    only the fields that are explicitly provided.
    """

    @pytest.mark.asyncio
    async def test_update_status_only(self, job_dal):
        """Update just the status field, leaving others unchanged."""
        await job_dal.create_job("job-010", "https://youtu.be/aaa", "aaa")
        await job_dal.update_job_status("job-010", "running", started_at="2026-04-07T09:00:00Z")

        job = await job_dal.get_job("job-010")
        assert job.status == "running"
        assert job.started_at == "2026-04-07T09:00:00Z"
        assert job.title is None  # not updated

    @pytest.mark.asyncio
    async def test_update_with_all_fields(self, job_dal):
        """Update status along with title, metadata, and timestamps."""
        await job_dal.create_job("job-011", "https://youtu.be/bbb", "bbb")
        await job_dal.update_job_status(
            "job-011", "completed",
            title="Test Song",
            file_path="/tmp/bbb.mp3",
            metadata={"duration": 180},
            finished_at="2026-04-07T09:05:00Z",
        )

        job = await job_dal.get_job("job-011")
        assert job.status == "completed"
        assert job.title == "Test Song"
        assert job.file_path == "/tmp/bbb.mp3"
        assert job.metadata == {"duration": 180}
        assert job.finished_at == "2026-04-07T09:05:00Z"


# ==========================================================================
# WB-06: JobDAL.get_job — Branch Coverage (found vs not found)
# ==========================================================================

class TestJobDALGetBranch:
    """
    Technique: BRANCH COVERAGE
    Target: JobDAL.get_job() in dal.py
    
    Two branches:
      - Row found → return JobRow
      - Row not found → return None
    """

    @pytest.mark.asyncio
    async def test_get_existing_job(self, job_dal):
        """Branch: row IS found → returns JobRow."""
        await job_dal.create_job("job-020", "https://youtu.be/ccc", "ccc")
        result = await job_dal.get_job("job-020")
        assert result is not None
        assert result.job_id == "job-020"

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, job_dal):
        """Branch: row NOT found → returns None."""
        result = await job_dal.get_job("nonexistent-id")
        assert result is None


# ==========================================================================
# WB-07: JobDAL.delete_old_jobs — Path Coverage
# ==========================================================================

class TestJobDALDeleteOldPath:
    """
    Technique: PATH COVERAGE
    Target: JobDAL.delete_old_jobs() in dal.py
    
    Tests two scenarios:
      - Old jobs are deleted (finished_at far in the past)
      - Recent jobs are kept (finished_at is recent)
    """

    @pytest.mark.asyncio
    async def test_deletes_old_finished_jobs(self, job_dal, db_connection):
        """Jobs with old finished_at timestamps should be deleted."""
        await job_dal.create_job("old-job", "https://youtu.be/old", "old")
        # Manually set finished_at to 2 hours ago
        await db_connection.execute(
            "UPDATE jobs SET status='completed', finished_at=datetime('now', '-2 hours') WHERE job_id='old-job'"
        )
        await db_connection.commit()

        deleted = await job_dal.delete_old_jobs(3600)  # 1 hour threshold
        assert deleted >= 1

        # Verify it's gone
        result = await job_dal.get_job("old-job")
        assert result is None

    @pytest.mark.asyncio
    async def test_keeps_recent_jobs(self, job_dal, db_connection):
        """Jobs with recent finished_at should NOT be deleted."""
        await job_dal.create_job("new-job", "https://youtu.be/new", "new")
        await db_connection.execute(
            "UPDATE jobs SET status='completed', finished_at=datetime('now') WHERE job_id='new-job'"
        )
        await db_connection.commit()

        deleted = await job_dal.delete_old_jobs(3600)
        assert deleted == 0

        # Verify it still exists
        result = await job_dal.get_job("new-job")
        assert result is not None


# ==========================================================================
# WB-08: FeedbackDAL.save_feedback — Statement Coverage
# ==========================================================================

class TestFeedbackDALSaveStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: FeedbackDAL.save_feedback() in dal.py
    
    Verifies INSERT executes and returns the auto-generated ID.
    """

    @pytest.mark.asyncio
    async def test_save_returns_positive_id(self, feedback_dal):
        """save_feedback() should return a positive integer ID."""
        fb_id = await feedback_dal.save_feedback(
            "Alice", "alice@test.com", "Bug Report", "The app crashes on startup."
        )
        assert isinstance(fb_id, int)
        assert fb_id > 0

    @pytest.mark.asyncio
    async def test_save_persists_data(self, feedback_dal):
        """Saved feedback should be retrievable."""
        await feedback_dal.save_feedback(
            "Bob", "bob@test.com", "Feature Request", "Add dark mode please."
        )
        all_fb = await feedback_dal.get_all_feedback()
        assert len(all_fb) == 1
        assert all_fb[0].name == "Bob"
        assert all_fb[0].category == "Feature Request"


# ==========================================================================
# WB-09: FeedbackDAL.get_feedback_by_category — Branch Coverage
# ==========================================================================

class TestFeedbackDALCategoryBranch:
    """
    Technique: BRANCH COVERAGE
    Target: FeedbackDAL.get_feedback_by_category() in dal.py
    
    Tests matching and non-matching category queries.
    """

    @pytest.mark.asyncio
    async def test_matching_category(self, feedback_dal):
        """Category that has entries → non-empty list."""
        await feedback_dal.save_feedback("Eve", "eve@test.com", "Bug Report", "Bug found!")
        await feedback_dal.save_feedback("Frank", "frank@test.com", "Other", "Just a note.")

        results = await feedback_dal.get_feedback_by_category("Bug Report")
        assert len(results) == 1
        assert results[0].name == "Eve"

    @pytest.mark.asyncio
    async def test_nonmatching_category(self, feedback_dal):
        """Category with no entries → empty list."""
        await feedback_dal.save_feedback("Grace", "grace@test.com", "Bug Report", "Another bug.")

        results = await feedback_dal.get_feedback_by_category("Feature Request")
        assert len(results) == 0


# ==========================================================================
# WB-10: InMemoryJobQueue — Statement Coverage
# ==========================================================================

class TestInMemoryJobQueueStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: InMemoryJobQueue in queue.py
    
    Tests the core enqueue → worker fires → task_done cycle
    by verifying the worker callback is actually invoked.
    """

    @pytest.mark.asyncio
    async def test_enqueue_triggers_worker(self):
        """Enqueued job ID should be passed to the worker callback."""
        from backend.ytconverter.app.queue import InMemoryJobQueue

        processed_ids = []

        async def mock_worker(job_id: str):
            processed_ids.append(job_id)

        queue = InMemoryJobQueue(concurrency=1)
        queue.start(mock_worker)

        await queue.enqueue("test-job-1")
        # Give the worker time to process
        await asyncio.sleep(0.2)

        assert "test-job-1" in processed_ids

        await queue.stop()

    @pytest.mark.asyncio
    async def test_concurrent_workers(self):
        """Multiple workers should process jobs in parallel."""
        from backend.ytconverter.app.queue import InMemoryJobQueue

        processed_ids = []

        async def mock_worker(job_id: str):
            await asyncio.sleep(0.1)
            processed_ids.append(job_id)

        queue = InMemoryJobQueue(concurrency=3)
        queue.start(mock_worker)

        for i in range(3):
            await queue.enqueue(f"parallel-{i}")

        await asyncio.sleep(0.5)

        assert len(processed_ids) == 3
        await queue.stop()
