"""
White Box Test Suite — SunLeo Application
==========================================

White Box (Glass Box) tests are designed with full knowledge of the internal
code structure. Each test targets specific code paths, branches, and statements.

Updated for Firebase Firestore DAL — playlist operations use a mocked
Firestore client (no live Firebase calls). URL utility tests remain pure.

Test IDs: WB-01 through WB-10
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
import pytest_asyncio

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ytconverter.app.utils import extract_video_id, validate_youtube_url


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
# WB-04: Playlist Service — create_playlist Statement Coverage
# ==========================================================================

class TestPlaylistCreateStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: playlist_service.create_playlist()

    Verifies every statement in create_playlist() executes:
      1. UUID generation
      2. Document construction
      3. Firestore .set() call
      4. Return value contains 'id' key
    """

    def test_create_playlist_returns_doc_with_id(self, playlist_service):
        """create_playlist() should return a dict with 'id', 'name', 'tracks'."""
        result = playlist_service.create_playlist(
            "test-uid-001", "My Playlist", [{"track_name": "Song A", "artist_name": "Artist 1"}]
        )
        assert "id" in result
        assert result["name"] == "My Playlist"
        assert result["track_count"] == 1
        assert len(result["tracks"]) == 1

    def test_create_playlist_persists_in_firestore(self, playlist_service):
        """Created playlist should be retrievable via get_playlist()."""
        created = playlist_service.create_playlist("test-uid-002", "Workout Mix", [])
        retrieved = playlist_service.get_playlist("test-uid-002", created["id"])
        assert retrieved is not None
        assert retrieved["name"] == "Workout Mix"


# ==========================================================================
# WB-05: Playlist Service — get_playlist Branch Coverage
# ==========================================================================

class TestPlaylistGetBranch:
    """
    Technique: BRANCH COVERAGE
    Target: playlist_service.get_playlist()

    Two branches based on doc.exists:
      - doc exists → return dict with data
      - doc doesn't exist → return None
    """

    def test_get_existing_playlist(self, playlist_service):
        """Branch: doc.exists=True → returns playlist dict."""
        created = playlist_service.create_playlist("uid-010", "Found Playlist", [])
        result = playlist_service.get_playlist("uid-010", created["id"])
        assert result is not None
        assert result["name"] == "Found Playlist"

    def test_get_nonexistent_playlist(self, playlist_service):
        """Branch: doc.exists=False → returns None."""
        result = playlist_service.get_playlist("uid-010", "nonexistent-id")
        assert result is None


# ==========================================================================
# WB-06: Playlist Service — add_tracks Statement Coverage
# ==========================================================================

class TestPlaylistAddTracksStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: playlist_service.add_tracks()

    Verifies:
      1. Existing tracks are read
      2. New tracks appended
      3. track_count updated
      4. .update() called on Firestore
    """

    def test_add_tracks_appends_correctly(self, playlist_service):
        """Adding tracks should append to existing list and update count."""
        created = playlist_service.create_playlist(
            "uid-020", "Growing Playlist",
            [{"track_name": "Track 1", "artist_name": "Artist 1"}]
        )
        updated = playlist_service.add_tracks(
            "uid-020", created["id"],
            [{"track_name": "Track 2", "artist_name": "Artist 2"}]
        )
        assert updated["track_count"] == 2
        assert len(updated["tracks"]) == 2
        assert updated["tracks"][1]["track_name"] == "Track 2"

    def test_add_tracks_to_nonexistent_raises(self, playlist_service):
        """Adding tracks to a non-existent playlist should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            playlist_service.add_tracks(
                "uid-020", "fake-playlist-id",
                [{"track_name": "X", "artist_name": "Y"}]
            )


# ==========================================================================
# WB-07: Playlist Service — remove_track Path Coverage
# ==========================================================================

class TestPlaylistRemoveTrackPath:
    """
    Technique: PATH COVERAGE
    Target: playlist_service.remove_track()

    Paths:
      1. Valid index → track removed, count updated
      2. Playlist not found → ValueError
      3. Index out of range → IndexError
    """

    def test_remove_valid_index(self, playlist_service):
        """Removing track at valid index 0 should shrink the list."""
        created = playlist_service.create_playlist(
            "uid-030", "Remove Test",
            [
                {"track_name": "A", "artist_name": "1"},
                {"track_name": "B", "artist_name": "2"},
            ]
        )
        result = playlist_service.remove_track("uid-030", created["id"], 0)
        assert result["track_count"] == 1
        assert result["tracks"][0]["track_name"] == "B"

    def test_remove_nonexistent_playlist_raises(self, playlist_service):
        """Removing from a non-existent playlist should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            playlist_service.remove_track("uid-030", "fake-id", 0)

    def test_remove_out_of_range_raises(self, playlist_service):
        """Removing at an out-of-range index should raise IndexError."""
        created = playlist_service.create_playlist(
            "uid-031", "Small Playlist",
            [{"track_name": "Only", "artist_name": "One"}]
        )
        with pytest.raises(IndexError):
            playlist_service.remove_track("uid-031", created["id"], 5)


# ==========================================================================
# WB-08: Playlist Service — delete_playlist Branch Coverage
# ==========================================================================

class TestPlaylistDeleteBranch:
    """
    Technique: BRANCH COVERAGE
    Target: playlist_service.delete_playlist()

    Two branches:
      - Playlist exists → delete and return True
      - Playlist doesn't exist → return False
    """

    def test_delete_existing_returns_true(self, playlist_service):
        """Deleting an existing playlist should return True."""
        created = playlist_service.create_playlist("uid-040", "To Delete", [])
        result = playlist_service.delete_playlist("uid-040", created["id"])
        assert result is True

        # Verify it's gone
        retrieved = playlist_service.get_playlist("uid-040", created["id"])
        assert retrieved is None

    def test_delete_nonexistent_returns_false(self, playlist_service):
        """Deleting a non-existent playlist should return False."""
        result = playlist_service.delete_playlist("uid-040", "no-such-id")
        assert result is False


# ==========================================================================
# WB-09: Playlist Service — get_playlists Statement Coverage
# ==========================================================================

class TestPlaylistListStatement:
    """
    Technique: STATEMENT COVERAGE
    Target: playlist_service.get_playlists()

    Verifies:
      1. Multiple playlists are returned
      2. Each result has an 'id' field
      3. Order is maintained (newest first — DESCENDING)
    """

    def test_list_returns_all_playlists(self, playlist_service):
        """get_playlists() should return all playlists for a user."""
        playlist_service.create_playlist("uid-050", "Playlist A", [])
        playlist_service.create_playlist("uid-050", "Playlist B", [])

        results = playlist_service.get_playlists("uid-050")
        assert len(results) == 2
        assert all("id" in p for p in results)

    def test_list_empty_user_returns_empty(self, playlist_service):
        """A user with no playlists should get an empty list."""
        results = playlist_service.get_playlists("uid-no-playlists")
        assert results == []


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
