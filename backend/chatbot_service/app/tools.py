"""
SunLeo Chatbot Agent — Tool definitions for the LangChain ReAct agent.
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
    """
    Get track recommendations for a given mood or activity.
    Mood can be: chill, workout, sad, happy, study, focus, party, sleep, road trip, etc.
    Returns a JSON list of results.
    """
    try:
        resp = requests.get(
            f"{RECOMMENDATION_API}/mood",
            params={"tag": mood, "limit": limit},
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
    IMPORTANT: Always confirm with the user before calling this tool.
    """
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


def check_download_status(job_ids_json: str) -> str:
    """
    Check download status for a list of job IDs (pass as a JSON array string).
    Returns a JSON list of status objects.
    """
    try:
        job_ids: list[str] = json.loads(job_ids_json)
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


# ── Playlist tools ────────────────────────────────────────────────────────────

def create_playlist(user_uid: str, name: str, tracks_json: str = "[]") -> str:
    """
    Create a named playlist in Firestore for the given user.
    tracks_json is a JSON array of track maps (can be empty).
    Returns the created playlist as JSON.
    """
    try:
        tracks: list[dict] = json.loads(tracks_json)
        result = _ps.create_playlist(user_uid, name, tracks)
        # Convert datetime fields for JSON serialisation
        result = _serialise(result)
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def add_to_playlist(user_uid: str, playlist_id: str, tracks_json: str) -> str:
    """
    Append tracks to an existing playlist.
    tracks_json is a JSON array of track maps.
    Returns the updated playlist as JSON.
    """
    try:
        tracks: list[dict] = json.loads(tracks_json)
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


def bulk_download_playlist(user_uid: str, playlist_id: str) -> str:
    """
    Queue all tracks in a playlist for MP3 download.
    Returns a JSON list of {track_name, artist_name, job_id} dicts.
    IMPORTANT: Always confirm with the user before calling this tool.
    """
    try:
        results = _ps.bulk_download_playlist(user_uid, playlist_id)
        return json.dumps(results)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


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
