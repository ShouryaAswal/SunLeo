"""
SunLeo Chatbot Service — FastAPI app.
Exposes:
  - /chat             POST  — AI chatbot (LangChain + Groq)
  - /playlists/{uid}  GET   — list user playlists
  - /playlists/{uid}  POST  — create playlist
  - /playlists/{uid}/{pid}           GET    — get single playlist
  - /playlists/{uid}/{pid}           DELETE — delete playlist
  - /playlists/{uid}/{pid}/tracks    POST   — add tracks
  - /playlists/{uid}/{pid}/tracks/{idx} DELETE — remove track
  - /playlists/{uid}/{pid}/download  POST   — bulk download
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Load root .env (works locally; in Docker, env vars come from compose env_file)
try:
    _ROOT_ENV = Path(__file__).parents[3] / ".env"
    load_dotenv(_ROOT_ENV)
except (IndexError, OSError):
    pass
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import run_agent
from . import playlist_service as ps

app = FastAPI(title="SunLeo Chatbot Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_uid: str = ""          # Firebase UID — needed for playlist operations


class ChatResponse(BaseModel):
    reply: str
    actions: list[dict] = []


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "chatbot"}


@app.get("/llm-status/{session_id}")
async def llm_status(session_id: str):
    from .llm_client import get_session_provider
    return {
        "session_id": session_id,
        "active_provider": get_session_provider(session_id),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await run_agent(request.message, request.session_id, request.user_uid)
        return ChatResponse(reply=result["reply"], actions=result.get("actions", []))
    except Exception as exc:
        import traceback
        print(f"[SunLeo Chat ERROR] Unhandled exception in /chat: {exc}")
        traceback.print_exc()
        return ChatResponse(
            reply="🎵 Oops! Something went wrong on my end. Please try again in a moment.",
            actions=[],
        )


# ── Playlist models ───────────────────────────────────────────────────────────

class CreatePlaylistRequest(BaseModel):
    name: str
    tracks: list[dict[str, Any]] = []


class AddTracksRequest(BaseModel):
    tracks: list[dict[str, Any]]


# ── Playlist endpoints ────────────────────────────────────────────────────────

@app.get("/playlists/{uid}")
async def list_playlists(uid: str):
    try:
        return ps.get_playlists(uid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/playlists/{uid}", status_code=201)
async def create_playlist(uid: str, body: CreatePlaylistRequest):
    try:
        result = ps.create_playlist(uid, body.name, body.tracks)
        return _serialise(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/playlists/{uid}/{pid}")
async def get_playlist(uid: str, pid: str):
    result = ps.get_playlist(uid, pid)
    if result is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return _serialise(result)


@app.delete("/playlists/{uid}/{pid}", status_code=204)
async def delete_playlist(uid: str, pid: str):
    if not ps.delete_playlist(uid, pid):
        raise HTTPException(status_code=404, detail="Playlist not found")


@app.post("/playlists/{uid}/{pid}/tracks", status_code=200)
async def add_tracks(uid: str, pid: str, body: AddTracksRequest):
    try:
        result = ps.add_tracks(uid, pid, body.tracks)
        return _serialise(result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/playlists/{uid}/{pid}/tracks/{idx}", status_code=200)
async def remove_track(uid: str, pid: str, idx: int):
    try:
        result = ps.remove_track(uid, pid, idx)
        return _serialise(result)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/playlists/{uid}/{pid}/download")
async def bulk_download(uid: str, pid: str):
    try:
        results = ps.bulk_download_playlist(uid, pid)
        return {"jobs": results}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialise(obj):
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj

