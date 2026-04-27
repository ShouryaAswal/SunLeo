"""
SunLeo Recommendation / Discovery Service  v3.0
=================================================
Integrations:
  - iTunes Search API   — track search + artwork (free, no key)
  - Last.fm tag API     — mood/genre discovery (free key)
  - YouTube Data API v3 — find YouTube URL for a track (primary, free quota)
  - yt-dlp ytsearch     — YouTube URL fallback (no key, slower)
  - ytconverter svc     — downstream: actually downloads the MP3
"""
from __future__ import annotations

import asyncio
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Load root .env (works locally; in Docker, env vars come from compose env_file)
try:
    _ROOT_ENV = Path(__file__).parents[3] / ".env"
    load_dotenv(_ROOT_ENV)
except (IndexError, OSError):
    pass  # Inside Docker — env vars are injected by docker-compose

LASTFM_API_KEY    = os.getenv("LASTFM_API_KEY", "")
YOUTUBE_API_KEY   = os.getenv("YOUTUBE_API_KEY", "")
YTCONVERTER_URL   = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:8000")
CHATBOT_URL       = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8002")
LASTFM_BASE       = "https://ws.audioscrobbler.com/2.0/"
ITUNES_BASE       = "https://itunes.apple.com/search"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

app = FastAPI(title="SunLeo Discovery Service", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── Models ───────────────────────────

class TrackInfo(BaseModel):
    track_name:   str
    artist_name:  str
    album_name:   Optional[str] = None
    artwork_url:  Optional[str] = None
    preview_url:  Optional[str] = None   # 30-second iTunes preview
    duration_ms:  Optional[int] = None
    genre:        Optional[str] = None
    search_query: str                    # pre-built query string for YouTube search


class ResolveQueueRequest(BaseModel):
    track_name:   str
    artist_name:  str
    search_query: str = Field("", description="Override search string; auto-built if empty")


class ResolveQueueResponse(BaseModel):
    job_id:      str
    status:      str
    url:         str
    youtube_url: str


# ─────────────────────────── iTunes Search ───────────────────────────

@app.get("/search", response_model=List[TrackInfo])
async def search_tracks(
    q: str = Query(..., description="Song name, artist, etc."),
    limit: int = Query(15, ge=1, le=25),
):
    """Search the iTunes catalog. Free — no API key required."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                ITUNES_BASE,
                params={"term": q, "media": "music", "entity": "song", "limit": limit},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"iTunes API error: {e}")

    results = []
    for item in resp.json().get("results", []):
        artist = item.get("artistName", "Unknown")
        track  = item.get("trackName",  "Unknown")
        artwork = item.get("artworkUrl100", "")
        if artwork:
            artwork = artwork.replace("100x100bb", "600x600bb")

        results.append(TrackInfo(
            track_name=track,
            artist_name=artist,
            album_name=item.get("collectionName"),
            artwork_url=artwork or None,
            preview_url=item.get("previewUrl"),
            duration_ms=item.get("trackTimeMillis"),
            genre=item.get("primaryGenreName"),
            search_query=f"{track} {artist} audio",
        ))

    return results


# ─────────────────────────── Last.fm Mood Discovery ───────────────────────────

MOOD_TAGS = [
    "chill", "workout", "sad", "happy", "focus", "party",
    "romantic", "energetic", "sleep", "road trip", "study",
    "indie", "lo-fi", "acoustic", "electronic", "hip-hop",
    "rock", "pop", "jazz", "classical", "metal", "r&b",
]

# Cache of total pages per tag: {tag: (total_pages, timestamp)}
_tag_page_cache: Dict[str, Tuple[int, float]] = {}
_CACHE_TTL = 3600  # 1 hour


async def _get_total_pages(tag: str, client: httpx.AsyncClient) -> int:
    """Get total pages for a tag from cache or Last.fm API."""
    cached = _tag_page_cache.get(tag)
    if cached and (time.time() - cached[1]) < _CACHE_TTL:
        return cached[0]

    try:
        resp = await client.get(
            LASTFM_BASE,
            params={
                "method": "tag.getTopTracks",
                "tag": tag,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "limit": 20,
                "page": 1,
            },
        )
        if resp.status_code == 200:
            attrs = resp.json().get("tracks", {}).get("@attr", {})
            total = int(attrs.get("totalPages", 5))
            total = min(total, 10)  # Cap at 10 pages
            _tag_page_cache[tag] = (total, time.time())
            return total
    except Exception:
        pass
    return 5  # default fallback


@app.get("/moods")
async def get_available_moods():
    return {"moods": MOOD_TAGS}


async def _fetch_itunes_artwork(
    name: str,
    artist: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> Optional[str]:
    """Fetch iTunes artwork for a track (used to enrich Last.fm results)."""
    async with sem:
        try:
            resp = await client.get(
                ITUNES_BASE,
                params={
                    "term": f"{name} {artist}",
                    "media": "music",
                    "entity": "song",
                    "limit": 1,
                },
            )
            if resp.status_code == 200:
                items = resp.json().get("results", [])
                if items:
                    url = items[0].get("artworkUrl100", "")
                    return url.replace("100x100bb", "600x600bb") if url else None
        except Exception:
            pass
    return None


@app.get("/mood", response_model=List[TrackInfo])
async def get_mood_tracks(
    tag: str = Query(..., description="Mood or genre tag"),
    limit: int = Query(20, ge=1, le=50),
    page: int = Query(0, ge=0, description="Page number (0 = random page for fresh results)"),
):
    """Get top tracks for a mood/genre via Last.fm, enriched with iTunes artwork.
    Set page=0 for random results, or a specific page number for deterministic results."""
    if not LASTFM_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Last.fm API key not configured. Set LASTFM_API_KEY in .env",
        )

    # Step 1 — Determine which page to fetch
    async with httpx.AsyncClient(timeout=10) as lfm_client:
        if page == 0:
            total_pages = await _get_total_pages(tag, lfm_client)
            actual_page = random.randint(1, max(1, total_pages))
        else:
            actual_page = page

        # Step 2 — Last.fm: get track list for tag
        try:
            resp = await lfm_client.get(
                LASTFM_BASE,
                params={
                    "method": "tag.getTopTracks",
                    "tag": tag,
                    "api_key": LASTFM_API_KEY,
                    "format": "json",
                    "limit": limit,
                    "page": actual_page,
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Last.fm API error: {e}")

    tracks_raw = resp.json().get("tracks", {}).get("track", [])
    if not tracks_raw:
        return []

    # Step 3 — Shuffle for extra variety within the page
    random.shuffle(tracks_raw)

    # Step 4 — iTunes: fetch artwork concurrently (max 5 at a time)
    sem = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=5) as itunes_client:
        artwork_tasks = [
            _fetch_itunes_artwork(
                t.get("name", ""),
                t.get("artist", {}).get("name", ""),
                itunes_client,
                sem,
            )
            for t in tracks_raw
        ]
        artworks = await asyncio.gather(*artwork_tasks, return_exceptions=True)

    # Step 5 — Assemble results
    results = []
    for t, art in zip(tracks_raw, artworks):
        name   = t.get("name", "Unknown")
        artist = t.get("artist", {}).get("name", "Unknown")
        artwork_url = art if isinstance(art, str) else None

        results.append(TrackInfo(
            track_name=name,
            artist_name=artist,
            artwork_url=artwork_url,
            search_query=f"{name} {artist} audio",
        ))

    return results


# ─────────────────────────── Personalized Mood Endpoint ───────────────────────

@app.get("/mood/personalized", response_model=List[TrackInfo])
async def get_personalized_mood_tracks(
    tag: str = Query(..., description="Mood or genre tag"),
    user_uid: str = Query("", description="Firebase UID for personalization"),
    limit: int = Query(20, ge=1, le=50),
):
    """Personalized mood tracks: filters out songs the user already has in playlists,
    and enriches with similar-artist discovery based on their library."""

    # Step 1 — Get base mood tracks (random page for freshness)
    base_tracks = await get_mood_tracks(tag=tag, limit=limit + 10, page=0)

    if not user_uid:
        return base_tracks[:limit]

    # Step 2 — Fetch user's existing playlist tracks for filtering
    user_track_keys: set[tuple[str, str]] = set()
    user_artists: set[str] = set()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"{CHATBOT_URL}/playlists/{user_uid}")
            if resp.status_code == 200:
                playlists = resp.json()
                for pl in playlists:
                    for t in pl.get("tracks", []):
                        tn = t.get("track_name", "").strip().lower()
                        an = t.get("artist_name", "").strip().lower()
                        user_track_keys.add((tn, an))
                        if an:
                            user_artists.add(an)
    except Exception:
        pass  # If chatbot service is down, skip personalization

    # Step 3 — Filter out tracks user already has
    filtered = [
        t for t in base_tracks
        if (t.track_name.strip().lower(), t.artist_name.strip().lower()) not in user_track_keys
    ]

    # Step 4 — If user has artists, try to discover similar artists via Last.fm
    if user_artists and LASTFM_API_KEY and len(filtered) < limit:
        sample_artists = random.sample(list(user_artists), min(3, len(user_artists)))
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                for artist in sample_artists:
                    resp = await client.get(
                        LASTFM_BASE,
                        params={
                            "method": "artist.getTopTracks",
                            "artist": artist,
                            "api_key": LASTFM_API_KEY,
                            "format": "json",
                            "limit": 5,
                        },
                    )
                    if resp.status_code == 200:
                        artist_tracks = resp.json().get("toptracks", {}).get("track", [])
                        for at in artist_tracks:
                            name = at.get("name", "Unknown")
                            art_name = at.get("artist", {}).get("name", "Unknown")
                            key = (name.strip().lower(), art_name.strip().lower())
                            if key not in user_track_keys:
                                filtered.append(TrackInfo(
                                    track_name=name,
                                    artist_name=art_name,
                                    search_query=f"{name} {art_name} audio",
                                ))
                                user_track_keys.add(key)
                            if len(filtered) >= limit:
                                break
                    if len(filtered) >= limit:
                        break
        except Exception:
            pass

    random.shuffle(filtered)
    return filtered[:limit]


# ─────────────────────────── YouTube URL Resolution ───────────────────────────

async def _find_youtube_url_via_api(query: str) -> Optional[str]:
    """Primary: YouTube Data API v3 with music category filter."""
    if not YOUTUBE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                YOUTUBE_SEARCH_URL,
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "videoCategoryId": "10",  # Music
                    "maxResults": 1,
                    "key": YOUTUBE_API_KEY,
                },
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    video_id = items[0]["id"]["videoId"]
                    return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass
    return None


def _find_youtube_url_via_ytdlp(query: str) -> Optional[str]:
    """Fallback: yt-dlp ytsearch (no API key needed; slower ~3-5 s)."""
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "default_search": "ytsearch1",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries", []) if info else []
            if entries:
                vid_id = entries[0].get("id", "")
                if vid_id:
                    return f"https://www.youtube.com/watch?v={vid_id}"
    except Exception:
        pass
    return None


# ─────────────────────────── Resolve & Queue Endpoint ───────────────────────────

@app.post("/resolve-and-queue", response_model=ResolveQueueResponse)
async def resolve_and_queue(request: ResolveQueueRequest):
    """
    Full pipeline:
      1. Build search query from track + artist (or use override)
      2. Try YouTube Data API v3  (primary — fast, reliable)
      3. Try yt-dlp ytsearch      (fallback — no key needed)
      4. If still no URL → 404
      5. POST the YouTube URL to ytconverter → returns job_id
    """
    query = request.search_query.strip() or f"{request.track_name} {request.artist_name} audio"

    # Step 1 — YouTube Data API
    youtube_url = await _find_youtube_url_via_api(query)

    # Step 2 — yt-dlp fallback
    if not youtube_url:
        youtube_url = await asyncio.to_thread(_find_youtube_url_via_ytdlp, query)

    # Step 3 — Nothing found
    if not youtube_url:
        raise HTTPException(
            status_code=404,
            detail=f"No YouTube video found for \"{request.track_name}\" by {request.artist_name}. "
                   "Try downloading it manually from the Home page.",
        )

    # Step 4 — Forward to ytconverter
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            conv_resp = await client.post(
                f"{YTCONVERTER_URL}/convert",
                json={"youtube_url": youtube_url},
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Download service (ytconverter on port 8000) is unreachable. "
                   "Make sure it is running.",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Converter communication error: {e}")

    if conv_resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Converter rejected the request: {conv_resp.text}",
        )

    data = conv_resp.json()
    return ResolveQueueResponse(
        job_id=data["job_id"],
        status=data["status"],
        url=data["url"],
        youtube_url=youtube_url,
    )


# ─────────────────────────── Genres (backwards compat) ───────────────────────────

@app.get("/genres")
def get_available_genres():
    return {"genres": [
        "pop", "rock", "hip-hop", "acoustic", "electronic",
        "metal", "chill", "indie", "jazz", "classical",
        "r&b", "country", "latin", "dance", "ambient",
    ]}


# ─────────────────────────── Health Check ───────────────────────────

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "itunes":  True,
        "lastfm":  bool(LASTFM_API_KEY),
        "youtube_api": bool(YOUTUBE_API_KEY),
        "ytconverter": YTCONVERTER_URL,
    }
