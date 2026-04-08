"""
SunLeo Chatbot Agent — Tool definitions for the ReAct agent.
Each tool wraps an existing SunLeo API endpoint.
"""
from __future__ import annotations

import os
import requests
from typing import Optional

RECOMMENDATION_API = os.getenv("RECOMMENDATION_API_URL", "http://127.0.0.1:8001")
CONVERTER_API = os.getenv("CONVERTER_API_URL", "http://127.0.0.1:8000")


def search_tracks(query: str, limit: int = 10) -> list[dict]:
    """Search for tracks by name or artist."""
    resp = requests.get(f"{RECOMMENDATION_API}/search", params={"q": query, "limit": limit}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_recommendations(
    genres: list[str],
    energy: Optional[float] = None,
    valence: Optional[float] = None,
    danceability: Optional[float] = None,
    tempo: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    """Get music recommendations based on genre and mood parameters."""
    payload = {"seed_genres": genres, "limit": limit}
    if energy is not None:
        payload["target_energy"] = energy
    if valence is not None:
        payload["target_valence"] = valence
    if danceability is not None:
        payload["target_danceability"] = danceability
    if tempo is not None:
        payload["target_tempo"] = tempo

    resp = requests.post(f"{RECOMMENDATION_API}/recommend", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def download_tracks(youtube_urls: list[str]) -> list[dict]:
    """Submit a batch of YouTube URLs for MP3 conversion."""
    resp = requests.post(f"{CONVERTER_API}/convert/batch", json={"urls": youtube_urls}, timeout=10)
    resp.raise_for_status()
    return resp.json().get("jobs", [])


def check_download_status(job_ids: list[str]) -> list[dict]:
    """Check the download status of one or more jobs."""
    results = []
    for job_id in job_ids:
        resp = requests.get(f"{CONVERTER_API}/status/{job_id}", timeout=5)
        if resp.status_code == 200:
            results.append(resp.json())
        else:
            results.append({"job_id": job_id, "status": "unknown", "error": "Failed to fetch status"})
    return results


def create_playlist(name: str, tracks: list[dict]) -> dict:
    """Create a named playlist from a list of tracks (in-memory for now)."""
    return {
        "playlist_name": name,
        "track_count": len(tracks),
        "tracks": tracks,
        "message": f"Playlist '{name}' created with {len(tracks)} tracks!"
    }
