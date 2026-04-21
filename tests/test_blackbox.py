"""
Black Box Test Suite — SunLeo Application
==========================================

Black Box (Functional) tests are designed WITHOUT knowledge of internal code.
Tests are based purely on specifications, requirements, and expected I/O behavior.

Updated for Firebase Firestore DAL — playlist tests treat the service as a
black box, validating behavior against specifications without examining
internal Firestore calls.

Test IDs: BB-01 through BB-10
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ==========================================================================
# BB-01: POST /convert — Valid URL (Equivalence Partitioning)
# ==========================================================================

class TestConvertValidURL:
    """
    Technique: EQUIVALENCE PARTITIONING
    Partition: Valid YouTube URLs → should return 200 + job_id

    The tester does not know how URL validation works internally;
    they only know that valid YouTube URLs should be accepted.
    """

    @pytest.mark.asyncio
    async def test_valid_youtube_url_returns_200(self, async_client):
        """A well-formed YouTube URL should be accepted and return a job."""
        response = await async_client.post(
            "/convert",
            json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"


# ==========================================================================
# BB-02: POST /convert — Invalid URL (Equivalence Partitioning)
# ==========================================================================

class TestConvertInvalidURL:
    """
    Technique: EQUIVALENCE PARTITIONING
    Partition: Invalid URLs → should return 400 error
    """

    @pytest.mark.asyncio
    async def test_invalid_url_returns_400(self, async_client):
        """A non-YouTube URL should be rejected with a 400 status."""
        response = await async_client.post(
            "/convert",
            json={"youtube_url": "https://www.google.com/search?q=test"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_malformed_url_returns_400(self, async_client):
        """A completely malformed string should be rejected."""
        response = await async_client.post(
            "/convert",
            json={"youtube_url": "not-a-url-at-all"}
        )
        assert response.status_code == 400


# ==========================================================================
# BB-03: POST /convert/batch — Exactly 10 URLs (Boundary Value Analysis)
# ==========================================================================

class TestBatchBoundaryAt10:
    """
    Technique: BOUNDARY VALUE ANALYSIS
    Boundary: Maximum batch size = 10
    Test: Exactly AT the boundary (10 URLs)
    """

    @pytest.mark.asyncio
    async def test_exactly_10_urls_accepted(self, async_client):
        """Submitting exactly 10 valid URLs should succeed (at boundary)."""
        urls = [f"https://www.youtube.com/watch?v=test{i:04d}" for i in range(10)]
        response = await async_client.post("/convert/batch", json={"urls": urls})
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 10


# ==========================================================================
# BB-04: POST /convert/batch — 11 URLs (Boundary Value Analysis)
# ==========================================================================

class TestBatchBoundaryAbove10:
    """
    Technique: BOUNDARY VALUE ANALYSIS
    Boundary: Maximum batch size = 10
    Test: Just ABOVE the boundary (11 URLs) → should fail
    """

    @pytest.mark.asyncio
    async def test_11_urls_rejected(self, async_client):
        """Submitting 11 URLs (one above max) should be rejected.

        Note: FastAPI/Pydantic's model-level max_length=10 validation
        fires before the endpoint handler, returning 422 instead of 400.
        Both are client-error codes indicating the request was rejected.
        """
        urls = [f"https://www.youtube.com/watch?v=test{i:04d}" for i in range(11)]
        response = await async_client.post("/convert/batch", json={"urls": urls})
        assert response.status_code in (400, 422)


# ==========================================================================
# BB-05: POST /convert/batch — Empty list (Boundary Value Analysis)
# ==========================================================================

class TestBatchBoundaryEmpty:
    """
    Technique: BOUNDARY VALUE ANALYSIS
    Boundary: Minimum batch size = 1
    Test: Below minimum (0 URLs)
    """

    @pytest.mark.asyncio
    async def test_empty_batch_returns_200_with_no_jobs(self, async_client):
        """
        An empty URL list is technically valid at the schema level,
        but produces zero jobs. The endpoint should handle it gracefully.
        """
        response = await async_client.post("/convert/batch", json={"urls": []})
        # The endpoint returns 200 with empty jobs list (no validation on empty)
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 0


# ==========================================================================
# BB-06: GET /status/{job_id} — Existing Job (Equivalence Partitioning)
# ==========================================================================

class TestStatusExistingJob:
    """
    Technique: EQUIVALENCE PARTITIONING
    Partition: Existing job IDs → should return 200 + status info
    """

    @pytest.mark.asyncio
    async def test_existing_job_returns_200(self, async_client):
        """A previously created job should return its status."""
        # First create a job
        create_resp = await async_client.post(
            "/convert",
            json={"youtube_url": "https://www.youtube.com/watch?v=existtest"}
        )
        job_id = create_resp.json()["job_id"]

        # Then check its status
        status_resp = await async_client.get(f"/status/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert "status" in data


# ==========================================================================
# BB-07: GET /status/{job_id} — Non-existent Job (Equivalence Partitioning)
# ==========================================================================

class TestStatusNonexistentJob:
    """
    Technique: EQUIVALENCE PARTITIONING
    Partition: Non-existent job IDs → should return 404
    """

    @pytest.mark.asyncio
    async def test_nonexistent_job_returns_404(self, async_client):
        """Requesting status of a job that was never created should return 404."""
        response = await async_client.get("/status/this-job-does-not-exist")
        assert response.status_code == 404


# ==========================================================================
# BB-08: GET /download/{job_id} — Incomplete Job (Equivalence Partitioning)
# ==========================================================================

class TestDownloadIncompleteJob:
    """
    Technique: EQUIVALENCE PARTITIONING
    Partition: Jobs not yet completed → download should fail with 409
    """

    @pytest.mark.asyncio
    async def test_download_queued_job_returns_409(self, async_client):
        """Downloading a job that's still queued should return 409 Conflict."""
        create_resp = await async_client.post(
            "/convert",
            json={"youtube_url": "https://www.youtube.com/watch?v=dltest01"}
        )
        job_id = create_resp.json()["job_id"]

        download_resp = await async_client.get(f"/download/{job_id}")
        assert download_resp.status_code == 409


# ==========================================================================
# BB-09: Playlist Service — CRUD Behavior (Decision Table)
# ==========================================================================

class TestPlaylistDecisionTable:
    """
    Technique: DECISION TABLE

    Tests playlist operations as a black box — we only know the specification:
    - create_playlist(uid, name, tracks) → returns playlist dict
    - get_playlists(uid) → returns list of playlists
    - delete_playlist(uid, pid) → returns True/False
    - add_tracks(uid, pid, tracks) → returns updated playlist

    We don't look at how Firestore documents are structured internally.
    """

    def test_create_and_retrieve_playlist(self, playlist_service):
        """Creating a playlist should make it retrievable."""
        result = playlist_service.create_playlist(
            uid="bb-user-001",
            name="My Favorites",
            tracks=[
                {"track_name": "Song A", "artist_name": "Artist 1"},
                {"track_name": "Song B", "artist_name": "Artist 2"},
            ]
        )
        assert result["name"] == "My Favorites"
        assert result["track_count"] == 2

        # Retrieve and verify
        all_playlists = playlist_service.get_playlists("bb-user-001")
        assert len(all_playlists) == 1
        assert all_playlists[0]["name"] == "My Favorites"

    def test_delete_removes_playlist(self, playlist_service):
        """Deleting a playlist should remove it from the user's list."""
        created = playlist_service.create_playlist("bb-user-002", "Temp Playlist", [])
        pid = created["id"]

        # Delete
        deleted = playlist_service.delete_playlist("bb-user-002", pid)
        assert deleted is True

        # Verify it's gone
        found = playlist_service.get_playlist("bb-user-002", pid)
        assert found is None

    def test_add_tracks_grows_playlist(self, playlist_service):
        """Adding tracks should increase the playlist's track list."""
        created = playlist_service.create_playlist("bb-user-003", "Growing", [])
        pid = created["id"]

        updated = playlist_service.add_tracks(
            "bb-user-003", pid,
            [{"track_name": "New Song", "artist_name": "New Artist"}]
        )
        assert updated["track_count"] == 1
        assert updated["tracks"][0]["track_name"] == "New Song"


# ==========================================================================
# BB-10: Playlist Service — Boundary Values (Boundary Value Analysis)
# ==========================================================================

class TestPlaylistBoundaryValues:
    """
    Technique: BOUNDARY VALUE ANALYSIS

    Tests edge cases for playlist data:
    - Empty playlist (0 tracks)
    - Playlist with many tracks
    - Track with special characters
    - Remove track at boundary indices
    """

    def test_empty_playlist_creation(self, playlist_service):
        """A playlist with zero tracks should be created successfully."""
        result = playlist_service.create_playlist("bb-user-010", "Empty", [])
        assert result["track_count"] == 0
        assert result["tracks"] == []

    def test_playlist_with_many_tracks(self, playlist_service):
        """A playlist with 50 tracks should handle all of them."""
        tracks = [
            {"track_name": f"Song {i}", "artist_name": f"Artist {i}"}
            for i in range(50)
        ]
        result = playlist_service.create_playlist("bb-user-011", "Big Playlist", tracks)
        assert result["track_count"] == 50
        assert len(result["tracks"]) == 50

    def test_special_characters_in_names(self, playlist_service):
        """Track names with unicode and special characters should be stored intact."""
        result = playlist_service.create_playlist(
            "bb-user-012", "Special 🎵 Chars",
            [{"track_name": "It's a 'Test' — \"Song\" <#1> & More 🎶", "artist_name": "O'Brien"}]
        )
        assert "🎵" in result["name"]
        assert "O'Brien" in result["tracks"][0]["artist_name"]
        assert "🎶" in result["tracks"][0]["track_name"]

    def test_remove_first_track(self, playlist_service):
        """Removing the first track (index 0) should work correctly."""
        created = playlist_service.create_playlist(
            "bb-user-013", "Three Songs",
            [
                {"track_name": "First", "artist_name": "A"},
                {"track_name": "Second", "artist_name": "B"},
                {"track_name": "Third", "artist_name": "C"},
            ]
        )
        result = playlist_service.remove_track("bb-user-013", created["id"], 0)
        assert result["track_count"] == 2
        assert result["tracks"][0]["track_name"] == "Second"

    def test_remove_last_track(self, playlist_service):
        """Removing the last track should work correctly."""
        created = playlist_service.create_playlist(
            "bb-user-014", "Two Songs",
            [
                {"track_name": "First", "artist_name": "A"},
                {"track_name": "Last", "artist_name": "B"},
            ]
        )
        result = playlist_service.remove_track("bb-user-014", created["id"], 1)
        assert result["track_count"] == 1
        assert result["tracks"][0]["track_name"] == "First"

    def test_remove_out_of_range_raises(self, playlist_service):
        """Removing at an out-of-range index should raise an error."""
        created = playlist_service.create_playlist(
            "bb-user-015", "One Song",
            [{"track_name": "Only", "artist_name": "One"}]
        )
        with pytest.raises(IndexError):
            playlist_service.remove_track("bb-user-015", created["id"], 5)
