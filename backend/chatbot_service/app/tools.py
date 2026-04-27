"""
SunLeo Chatbot Agent — Tool implementations.
Each tool wraps a SunLeo service endpoint or the internal playlist service.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import requests

from . import playlist_service as _ps

RECOMMENDATION_API = os.getenv("RECOMMENDATION_API_URL", "http://127.0.0.1:8001")
CONVERTER_API = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:8000")


# ── Music discovery tools ─────────────────────────────────────────────────────

def search_tracks(query: str, limit: int = 10) -> str:
    """Search for tracks by song name or artist. Returns a JSON list of results."""
    try:
        resp = requests.get(
            f"{RECOMMENDATION_API}/search",
            params={"q": query, "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def get_mood_tracks(mood: str, limit: int = 10) -> str:
    """Get track recommendations for a given mood or activity."""
    try:
        resp = requests.get(
            f"{RECOMMENDATION_API}/mood",
            params={"tag": mood, "limit": limit, "page": 0},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def download_track(track_name: str, artist_name: str) -> str:
    """
    Resolve a track to a YouTube URL and queue it for MP3 download.
    Returns a JSON dict with job_id and youtube_url.
    """
    if not track_name or not artist_name:
        return json.dumps({"error": "track_name and artist_name are required"})
    try:
        resp = requests.post(
            f"{RECOMMENDATION_API}/resolve-and-queue",
            json={"track_name": track_name, "artist_name": artist_name},
            timeout=20,
        )
        resp.raise_for_status()
        return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def check_download_status(job_ids: list[str] = None) -> str:
    """Check download status for a list of job IDs. Returns a JSON list of status objects."""
    if not job_ids:
        return json.dumps({"error": "job_ids list is required"})
    try:
        results = []
        for job_id in job_ids:
            resp = requests.get(f"{CONVERTER_API}/status/{job_id}", timeout=5)
            if resp.status_code == 200:
                results.append(resp.json())
            else:
                results.append({"job_id": job_id, "status": "unknown"})
        return json.dumps(results)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Session-aware tools ───────────────────────────────────────────────────────

def download_tracks_by_index(session_id: str, indexes: list[int] = None) -> str:
    """Download tracks by their 1-based index from the last shown track list."""
    from .agent import get_session_state
    state = get_session_state(session_id)
    last_tracks = state.get("last_tracks", [])

    if not last_tracks:
        return json.dumps({"error": "No recent track list found. Please search for tracks first."})
    if not indexes:
        return json.dumps({"error": "Please specify which track numbers to download (e.g. [1, 3, 5])."})

    results = []
    for idx in indexes:
        if idx < 1 or idx > len(last_tracks):
            results.append({"index": idx, "error": f"Track #{idx} is out of range (1-{len(last_tracks)})"})
            continue
        track = last_tracks[idx - 1]
        dl_result = json.loads(download_track(track.get("track_name", ""), track.get("artist_name", "")))
        dl_result["index"] = idx
        dl_result["track_name"] = track.get("track_name")
        dl_result["artist_name"] = track.get("artist_name")
        results.append(dl_result)

    return json.dumps(results)


def save_last_tracks_as_playlist(user_uid: str, session_id: str, name: str, indexes: list[int] = None) -> str:
    """Create a playlist from the last shown tracks. Optionally specify indexes to include only certain tracks."""
    from .agent import get_session_state
    state = get_session_state(session_id)
    last_tracks = state.get("last_tracks", [])

    if not last_tracks:
        return json.dumps({"error": "No recent track list found. Please search for tracks first."})

    if indexes:
        selected = []
        for idx in indexes:
            if 1 <= idx <= len(last_tracks):
                selected.append(last_tracks[idx - 1])
        tracks = selected
    else:
        tracks = list(last_tracks)

    if not tracks:
        return json.dumps({"error": "No valid tracks selected."})

    # Normalise tracks to playlist format
    playlist_tracks = [
        {"track_name": t.get("track_name", ""), "artist_name": t.get("artist_name", ""),
         "artwork_url": t.get("artwork_url", ""), "search_query": t.get("search_query", "")}
        for t in tracks
    ]

    try:
        result = _ps.create_playlist(user_uid, name, playlist_tracks)
        return json.dumps(_serialise(result))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def add_last_tracks_to_playlist(user_uid: str, session_id: str, playlist_id: str, indexes: list[int] = None) -> str:
    """Add tracks from the last shown list to an existing playlist. Optionally specify indexes."""
    from .agent import get_session_state
    state = get_session_state(session_id)
    last_tracks = state.get("last_tracks", [])

    if not last_tracks:
        return json.dumps({"error": "No recent track list found. Please search first."})

    if indexes:
        selected = [last_tracks[i - 1] for i in indexes if 1 <= i <= len(last_tracks)]
    else:
        selected = list(last_tracks)

    if not selected:
        return json.dumps({"error": "No valid tracks selected."})

    playlist_tracks = [
        {"track_name": t.get("track_name", ""), "artist_name": t.get("artist_name", ""),
         "artwork_url": t.get("artwork_url", ""), "search_query": t.get("search_query", "")}
        for t in selected
    ]

    try:
        result = _ps.add_tracks(user_uid, playlist_id, playlist_tracks)
        return json.dumps(_serialise(result))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Playlist tools ────────────────────────────────────────────────────────────

def create_playlist(user_uid: str, name: str, tracks: list[dict] = None) -> str:
    """Create a named playlist in Firestore for the given user."""
    if tracks is None:
        tracks = []
    try:
        result = _ps.create_playlist(user_uid, name, tracks)
        return json.dumps(_serialise(result))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def add_to_playlist(user_uid: str, playlist_id: str, tracks: list[dict] = None) -> str:
    """Append tracks to an existing playlist."""
    if not tracks:
        return json.dumps({"error": "tracks list is required"})
    try:
        result = _ps.add_tracks(user_uid, playlist_id, tracks)
        return json.dumps(_serialise(result))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def list_playlists(user_uid: str) -> str:
    """Return all playlists owned by the user as a JSON array."""
    try:
        playlists = _ps.get_playlists(user_uid)
        return json.dumps([_serialise(p) for p in playlists])
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def get_playlist_details(user_uid: str, playlist_id: str) -> str:
    """Get full details of a specific playlist including all tracks."""
    try:
        result = _ps.get_playlist(user_uid, playlist_id)
        if result is None:
            return json.dumps({"error": f"Playlist {playlist_id} not found."})
        return json.dumps(_serialise(result))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def delete_playlist(user_uid: str, playlist_id: str) -> str:
    """Delete a playlist by its ID."""
    if not playlist_id:
        return json.dumps({"error": "playlist_id is required"})
    try:
        success = _ps.delete_playlist(user_uid, playlist_id)
        if success:
            return json.dumps({"success": True, "message": f"Playlist {playlist_id} deleted."})
        else:
            return json.dumps({"error": f"Playlist {playlist_id} not found."})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def remove_track_from_playlist(user_uid: str, playlist_id: str, track_index: int) -> str:
    """Remove a track from a playlist by its 0-based index."""
    try:
        result = _ps.remove_track(user_uid, playlist_id, track_index)
        return json.dumps(_serialise(result))
    except (ValueError, IndexError) as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def bulk_download_playlist(user_uid: str, playlist_id: str) -> str:
    """Queue all tracks in a playlist for MP3 download."""
    try:
        results = _ps.bulk_download_playlist(user_uid, playlist_id)
        return json.dumps(results)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Feedback tool ─────────────────────────────────────────────────────────────

def send_feedback(user_name: str, user_email: str, category: str, message: str, rating: int = 5) -> str:
    """Send user feedback via EmailJS. Categories: Bug Report, Feature Request, General Feedback, Other."""
    service_id = os.getenv("EMAILJS_SERVICE_ID", "")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID", "")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY", "")

    if not service_id or not template_id or not public_key:
        return json.dumps({"error": "EmailJS is not configured. Feedback logged locally.",
                           "logged": True, "name": user_name, "email": user_email,
                           "category": category, "message": message, "rating": rating})

    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "template_params": {
            "from_name": user_name,
            "reply_to": user_email,
            "category": category,
            "rating": f"{rating}/5",
            "message": f"[Via SunLeo DJ Chatbot]\n{message}",
        },
    }

    try:
        resp = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload, timeout=15,
        )
        if resp.status_code == 200:
            return json.dumps({"success": True, "message": "Feedback sent successfully!"})
        return json.dumps({"error": f"EmailJS error {resp.status_code}: {resp.text}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Utility tools ─────────────────────────────────────────────────────────────

def get_available_moods() -> str:
    """Return the list of available mood/genre tags for discovery."""
    try:
        resp = requests.get(f"{RECOMMENDATION_API}/moods", timeout=5)
        resp.raise_for_status()
        return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"moods": ["chill", "workout", "sad", "happy", "focus",
                                      "party", "sleep", "road trip", "study",
                                      "indie", "lo-fi", "jazz"]})


def check_pending_downloads(session_id: str) -> str:
    """Check status of all pending downloads from this session."""
    from .agent import get_session_state
    state = get_session_state(session_id)
    pending = state.get("pending_downloads", [])

    if not pending:
        return json.dumps({"message": "No pending downloads.", "downloads": []})

    job_ids = [d.get("job_id") for d in pending if d.get("job_id")]
    if not job_ids:
        return json.dumps({"message": "No pending downloads.", "downloads": []})

    return check_download_status(job_ids)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _serialise(obj):
    """Recursively convert datetime objects to ISO strings for JSON export."""
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj
