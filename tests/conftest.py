"""
Shared pytest fixtures for SunLeo test suites.

Provides:
- Standalone mock playlist service (no Firebase imports at all)
- FastAPI test client for endpoint testing
- Pure-function fixtures (URL utils, job queue) — no mocking needed

Strategy: Rather than importing the real playlist_service module (which
would trigger imports of firebase_admin, google.cloud.firestore, etc.),
we re-implement the playlist logic against an in-memory store.  This
lets tests run on any machine without Firebase SDK dependencies.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Add project root to sys.path so we can import backend modules directly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# In-memory Playlist Service — mirrors playlist_service.py logic exactly,
# but stores data in a plain Python dict instead of Firestore.
# ---------------------------------------------------------------------------

class InMemoryPlaylistService:
    """
    Drop-in replacement for backend.chatbot_service.app.playlist_service
    that stores everything in a Python dict.  The API surface is identical
    to the real module so tests exercise the same contract.

    Internal store layout:
        _store[uid][playlist_id] = { name, tracks, track_count, created_at, updated_at }
    """

    def __init__(self):
        self._store: dict[str, dict[str, dict[str, Any]]] = {}

    # -- helpers --

    def _user_playlists(self, uid: str) -> dict[str, dict]:
        return self._store.setdefault(uid, {})

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    # -- CRUD --

    def create_playlist(self, uid: str, name: str, tracks: list[dict]) -> dict:
        playlist_id = str(uuid.uuid4())
        doc = {
            "name": name,
            "created_at": self._now(),
            "updated_at": self._now(),
            "track_count": len(tracks),
            "tracks": list(tracks),
        }
        self._user_playlists(uid)[playlist_id] = doc
        result = dict(doc)
        result["id"] = playlist_id
        return result

    def get_playlists(self, uid: str) -> list[dict]:
        playlists = self._user_playlists(uid)
        result = []
        for pid, data in sorted(
            playlists.items(),
            key=lambda x: x[1].get("created_at", ""),
            reverse=True,
        ):
            entry = dict(data)
            entry["id"] = pid
            result.append(entry)
        return result

    def get_playlist(self, uid: str, playlist_id: str) -> dict | None:
        playlists = self._user_playlists(uid)
        if playlist_id not in playlists:
            return None
        data = dict(playlists[playlist_id])
        data["id"] = playlist_id
        return data

    def add_tracks(self, uid: str, playlist_id: str, tracks: list[dict]) -> dict:
        playlists = self._user_playlists(uid)
        if playlist_id not in playlists:
            raise ValueError(f"Playlist {playlist_id} not found for user {uid}")
        doc = playlists[playlist_id]
        current = doc.get("tracks", [])
        updated = current + tracks
        doc["tracks"] = updated
        doc["track_count"] = len(updated)
        doc["updated_at"] = self._now()
        result = dict(doc)
        result["id"] = playlist_id
        return result

    def remove_track(self, uid: str, playlist_id: str, track_index: int) -> dict:
        playlists = self._user_playlists(uid)
        if playlist_id not in playlists:
            raise ValueError(f"Playlist {playlist_id} not found for user {uid}")
        doc = playlists[playlist_id]
        tracks = doc.get("tracks", [])
        if track_index < 0 or track_index >= len(tracks):
            raise IndexError(f"Track index {track_index} out of range (0–{len(tracks)-1})")
        tracks.pop(track_index)
        doc["tracks"] = tracks
        doc["track_count"] = len(tracks)
        doc["updated_at"] = self._now()
        result = dict(doc)
        result["id"] = playlist_id
        return result

    def delete_playlist(self, uid: str, playlist_id: str) -> bool:
        playlists = self._user_playlists(uid)
        if playlist_id not in playlists:
            return False
        del playlists[playlist_id]
        return True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def playlist_service():
    """
    Yield a fresh InMemoryPlaylistService for each test.
    This mirrors the exact same API as the real playlist_service module,
    but requires zero Firebase dependencies.
    """
    return InMemoryPlaylistService()


# ---------------------------------------------------------------------------
# FastAPI test client fixture (for black box endpoint testing)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_client():
    """
    Create a synchronous TestClient for the ytconverter FastAPI app.
    Uses httpx for ASGI transport.
    """
    from httpx import ASGITransport, AsyncClient
    from backend.ytconverter.app.main import app

    transport = ASGITransport(app=app)
    return transport


@pytest_asyncio.fixture
async def async_client():
    """
    Create an async httpx client mounted on the ytconverter FastAPI app.
    """
    from httpx import ASGITransport, AsyncClient
    from backend.ytconverter.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
