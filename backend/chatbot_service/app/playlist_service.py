"""
Playlist CRUD service for SunLeo.

All operations are scoped to a Firebase UID so that each user only ever
sees their own playlists.

Firestore schema:
    users/{uid}/playlists/{playlist_id}
        name:         str
        created_at:   timestamp
        updated_at:   timestamp
        track_count:  int
        tracks:       list[TrackMap]

TrackMap:
    track_name:   str
    artist_name:  str
    artwork_url:  str   (optional)
    search_query: str   (optional – used to resolve a YouTube URL later)
    youtube_url:  str   (optional – filled in after download)
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

import requests
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from .firestore_client import get_db

# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _playlist_ref(uid: str, playlist_id: str):
    return get_db().collection("users").document(uid).collection("playlists").document(playlist_id)


def _playlists_ref(uid: str):
    return get_db().collection("users").document(uid).collection("playlists")


def _track_key(track: dict) -> tuple[str, str]:
    """Normalised (track_name, artist_name) for deduplication."""
    return (
        track.get("track_name", "").strip().lower(),
        track.get("artist_name", "").strip().lower(),
    )


def _dedupe_tracks(existing: list[dict], new_tracks: list[dict]) -> tuple[list[dict], int]:
    """
    Return (tracks_to_add, skipped_count).
    Duplicates are identified by normalised (track_name, artist_name).
    """
    existing_keys = {_track_key(t) for t in existing}
    to_add: list[dict] = []
    skipped = 0
    for t in new_tracks:
        key = _track_key(t)
        if key in existing_keys:
            skipped += 1
        else:
            existing_keys.add(key)
            to_add.append(t)
    return to_add, skipped


# ── CRUD ─────────────────────────────────────────────────────────────────────

def create_playlist(uid: str, name: str, tracks: list[dict]) -> dict:
    """Create a new playlist and return its full document."""
    # Dedupe within the provided tracks themselves
    deduped, skipped = _dedupe_tracks([], tracks)

    playlist_id = str(uuid.uuid4())
    doc: dict[str, Any] = {
        "name": name,
        "created_at": _now(),
        "updated_at": _now(),
        "track_count": len(deduped),
        "tracks": deduped,
    }
    _playlist_ref(uid, playlist_id).set(doc)
    doc["id"] = playlist_id
    doc["added"] = len(deduped)
    doc["skipped_duplicates"] = skipped
    return doc


def get_playlists(uid: str) -> list[dict]:
    """Return all playlists for a user, ordered by creation time (newest first)."""
    docs = (
        _playlists_ref(uid)
        .order_by("created_at", direction="DESCENDING")
        .stream()
    )
    result = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        result.append(data)
    return result


def get_playlist(uid: str, playlist_id: str) -> dict | None:
    """Return a single playlist document, or None if not found."""
    doc = _playlist_ref(uid, playlist_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_tracks(uid: str, playlist_id: str, tracks: list[dict]) -> dict:
    """Append tracks to an existing playlist, skipping duplicates."""
    ref = _playlist_ref(uid, playlist_id)
    doc = ref.get()
    if not doc.exists:
        raise ValueError(f"Playlist {playlist_id} not found for user {uid}")

    current: list = doc.to_dict().get("tracks", [])
    to_add, skipped = _dedupe_tracks(current, tracks)
    updated = current + to_add
    ref.update({
        "tracks": updated,
        "track_count": len(updated),
        "updated_at": _now(),
    })
    data = ref.get().to_dict()
    data["id"] = playlist_id
    data["added"] = len(to_add)
    data["skipped_duplicates"] = skipped
    return data


def remove_track(uid: str, playlist_id: str, track_index: int) -> dict:
    """Remove a track by its zero-based index."""
    ref = _playlist_ref(uid, playlist_id)
    doc = ref.get()
    if not doc.exists:
        raise ValueError(f"Playlist {playlist_id} not found for user {uid}")

    tracks: list = doc.to_dict().get("tracks", [])
    if track_index < 0 or track_index >= len(tracks):
        raise IndexError(f"Track index {track_index} out of range (0–{len(tracks)-1})")

    tracks.pop(track_index)
    ref.update({
        "tracks": tracks,
        "track_count": len(tracks),
        "updated_at": _now(),
    })
    data = ref.get().to_dict()
    data["id"] = playlist_id
    return data


def delete_playlist(uid: str, playlist_id: str) -> bool:
    """Delete a playlist. Returns True if it existed, False if not found."""
    ref = _playlist_ref(uid, playlist_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True


def bulk_download_playlist(uid: str, playlist_id: str) -> list[dict]:
    """
    Queue every track in the playlist for download via the recommendation service.
    Returns a list of {track_name, artist_name, job_id, youtube_url} dicts.
    """
    playlist = get_playlist(uid, playlist_id)
    if playlist is None:
        raise ValueError(f"Playlist {playlist_id} not found for user {uid}")

    reco_url = os.getenv("RECOMMENDATION_API_URL", "http://localhost:8001")
    results: list[dict] = []

    for track in playlist.get("tracks", []):
        try:
            resp = requests.post(
                f"{reco_url}/resolve-and-queue",
                json={
                    "track_name": track.get("track_name", ""),
                    "artist_name": track.get("artist_name", ""),
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            results.append({
                "track_name": track.get("track_name"),
                "artist_name": track.get("artist_name"),
                "job_id": data.get("job_id"),
                "youtube_url": data.get("youtube_url"),
            })
        except Exception as exc:
            results.append({
                "track_name": track.get("track_name"),
                "artist_name": track.get("artist_name"),
                "job_id": None,
                "error": str(exc),
            })

    return results
