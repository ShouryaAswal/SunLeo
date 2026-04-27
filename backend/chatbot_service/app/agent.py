"""
SunLeo DJ Agent — multi-provider LLM agent with Groq → Gemini fallback.

Uses the `openai` SDK via llm_client.py for both providers.
No LangChain, no LangGraph — just clean, reliable code.
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections import defaultdict

from . import tools as T
from .llm_client import chat_completion

log = logging.getLogger("sunleo.agent")

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are SunLeo DJ 🎵, a friendly and enthusiastic AI music assistant.

Your capabilities:
1. SEARCH — Find songs by name, artist, or album using search_tracks
2. DISCOVER — Suggest songs by mood/activity using get_mood_tracks
3. DOWNLOAD — Download songs as MP3. ALWAYS confirm with the user before downloading!
4. PLAYLISTS — Create, view, update, and manage playlists (create, add tracks, remove tracks, delete)
5. BULK DOWNLOAD — Download all songs in a playlist using bulk_download_playlist
6. FEEDBACK — Send feedback on behalf of the user using send_feedback
7. CHECK STATUS — Check download progress using check_pending_downloads

Behaviour rules:
- Always present song options BEFORE downloading. Never auto-download.
- Format track suggestions as numbered lists: "1. Song Name — Artist Name"
- Be conversational, use music emojis 🎵🎶🎸🥁🎤, keep responses concise.
- If user wants a playlist, ask for a name if not provided.
- For bulk downloads, confirm playlist name + track count before downloading.
- NEVER show raw JSON, tool call data, or internal errors to the user.
- If a tool fails, apologize and explain in simple terms.

INDEXED SELECTION (important):
- When you show tracks, always number them 1, 2, 3, etc.
- When the user says "download #3", "download 1, 3, 5", or "download all", use the download_tracks_by_index tool. Do NOT try to recall track names from memory.
- When the user says "save these as <name>", use save_last_tracks_as_playlist.
- When the user says "add these to <playlist>", use add_last_tracks_to_playlist. First call list_playlists to get the playlist_id.
- "download all" means pass indexes [1, 2, 3, ..., N] where N is the number of tracks shown.

PLAYLIST MANAGEMENT:
- To delete, remove tracks, or get details: first call list_playlists to find the playlist_id.
- To remove a track: call remove_track_from_playlist with the 0-based track_index. First call get_playlist_details to see tracks.
- Always confirm destructive actions (delete, remove) before executing.

FEEDBACK:
- If the user wants to send feedback or report a bug, use send_feedback. Ask for missing details: name, email, category, message.
- Categories: "Bug Report", "Feature Request", "General Feedback", "Other"

Mood mapping:
  Chill/Relax/Unwind → chill | Gym/Workout/Run → workout
  Sad/Heartbreak → sad | Happy/Joy → happy | Study/Focus → study/focus
  Party/Dance/Hype → party | Sleep/Night/Calm → sleep | Drive → road trip"""

# ── Tool schemas (OpenAI function-calling format) ─────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_tracks",
            "description": "Search for tracks by song name or artist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (song name, artist, etc.)"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mood_tracks",
            "description": "Get track recommendations for a mood or activity. Moods: chill, workout, sad, happy, study, focus, party, sleep, road trip, indie, lo-fi, jazz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {"type": "string", "description": "Mood or activity keyword"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
                "required": ["mood"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_moods",
            "description": "Get the list of available mood/genre tags for discovery. No parameters needed.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "download_track",
            "description": "Download a single track by name and artist. ONLY call after user confirms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "track_name": {"type": "string"},
                    "artist_name": {"type": "string"},
                },
                "required": ["track_name", "artist_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "download_tracks_by_index",
            "description": "Download tracks by their number from the most recently shown list. Use when user says 'download #2', 'download 1,3,5', or 'download all'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indexes": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "1-based track numbers from the last shown list",
                    },
                },
                "required": ["indexes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_download_status",
            "description": "Check download status for specific job IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of job_id strings to check",
                    },
                },
                "required": ["job_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_pending_downloads",
            "description": "Check status of all pending downloads from this chat session. No arguments needed.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_playlist",
            "description": "Create a new empty playlist. Use save_last_tracks_as_playlist to create with tracks from a search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Playlist name"},
                    "tracks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Optional tracks with track_name and artist_name",
                        "default": [],
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_last_tracks_as_playlist",
            "description": "Create a playlist from the most recently shown track list. Use when user says 'save these as <name>'. Optionally specify track numbers to include only certain tracks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Playlist name"},
                    "indexes": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional 1-based track numbers to include. Omit to include all.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_playlist",
            "description": "Add specific tracks (by name/artist) to an existing playlist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string"},
                    "tracks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Array of track objects with track_name and artist_name",
                    },
                },
                "required": ["playlist_id", "tracks"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_last_tracks_to_playlist",
            "description": "Add tracks from the most recently shown list to an existing playlist. Use when user says 'add these to <playlist>'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "The playlist ID to add tracks to"},
                    "indexes": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional 1-based track numbers. Omit to add all.",
                    },
                },
                "required": ["playlist_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_playlists",
            "description": "List all playlists belonging to the current user.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_playlist_details",
            "description": "Get full details of a specific playlist including all its tracks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "The playlist ID"},
                },
                "required": ["playlist_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_playlist",
            "description": "Delete a user's playlist. ALWAYS confirm before deleting. Get playlist_id from list_playlists first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "The playlist ID to delete"},
                },
                "required": ["playlist_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_track_from_playlist",
            "description": "Remove a single track from a playlist by its 0-based index. Call get_playlist_details first to see track indexes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string"},
                    "track_index": {"type": "integer", "description": "0-based index of the track to remove"},
                },
                "required": ["playlist_id", "track_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bulk_download_playlist",
            "description": "Queue every track in a playlist for MP3 download. ONLY call after user confirms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string"},
                },
                "required": ["playlist_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_feedback",
            "description": "Send user feedback or bug report via email. Ask user for details if missing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {"type": "string", "description": "User's name"},
                    "user_email": {"type": "string", "description": "User's email address"},
                    "category": {"type": "string", "enum": ["Bug Report", "Feature Request", "General Feedback", "Other"]},
                    "message": {"type": "string", "description": "Feedback message"},
                    "rating": {"type": "integer", "description": "Rating 1-5", "default": 5},
                },
                "required": ["user_name", "user_email", "category", "message"],
            },
        },
    },
]

# ── Tool dispatcher ───────────────────────────────────────────────────────────

# Tools that need user_uid injected
_UID_TOOLS = {
    "create_playlist", "add_to_playlist", "add_last_tracks_to_playlist",
    "list_playlists", "get_playlist_details", "delete_playlist",
    "remove_track_from_playlist", "bulk_download_playlist",
    "save_last_tracks_as_playlist",
}
# Tools that need session_id injected
_SESSION_TOOLS = {
    "download_tracks_by_index", "save_last_tracks_as_playlist",
    "add_last_tracks_to_playlist", "check_pending_downloads",
}

def _dispatch_tool(name: str, args: dict, user_uid: str, session_id: str) -> str:
    """Call the matching tool function and return its JSON result."""
    if name in _UID_TOOLS:
        args["user_uid"] = user_uid
    if name in _SESSION_TOOLS:
        args["session_id"] = session_id

    fn = getattr(T, name, None)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        return fn(**args)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})

# ── Session state (in-process) ────────────────────────────────────────────────

_session_state: dict[str, dict] = defaultdict(lambda: {
    "last_tracks": [],
    "last_playlist": None,
    "pending_downloads": [],
})

def get_session_state(session_id: str) -> dict:
    """Get the session state for a given session (used by tools)."""
    return _session_state[session_id]

def _update_session_from_tool_result(session_id: str, tool_name: str, result_str: str):
    """Update session state based on tool results."""
    try:
        result = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return

    state = _session_state[session_id]

    # Store search/mood results as last_tracks
    if tool_name in ("search_tracks", "get_mood_tracks") and isinstance(result, list):
        state["last_tracks"] = result

    # Store created playlist context
    if tool_name in ("create_playlist", "save_last_tracks_as_playlist") and isinstance(result, dict) and "id" in result:
        state["last_playlist"] = {"id": result["id"], "name": result.get("name", "")}

    # Track download job IDs
    if tool_name == "download_track" and isinstance(result, dict) and result.get("job_id"):
        state["pending_downloads"].append(result)

    if tool_name == "download_tracks_by_index" and isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and r.get("job_id"):
                state["pending_downloads"].append(r)

    if tool_name == "bulk_download_playlist" and isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and r.get("job_id"):
                state["pending_downloads"].append(r)


# ── Conversation memory (in-process) ─────────────────────────────────────────

_sessions: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 20

def _get_messages(session_id: str) -> list[dict]:
    return _sessions[session_id]

def _add_message(session_id: str, msg: dict):
    history = _sessions[session_id]
    history.append(msg)
    if len(history) > MAX_HISTORY:
        _sessions[session_id] = history[-MAX_HISTORY:]

# ── Reply sanitizer ──────────────────────────────────────────────────────────

_TOOL_CALL_PATTERNS = [
    re.compile(r'```(?:json)?\s*\{[^`]*?(?:"function"|"tool_call"|"name").*?\}\s*```', re.DOTALL | re.IGNORECASE),
    re.compile(r'<tool_call>.*?</tool_call>', re.DOTALL | re.IGNORECASE),
    re.compile(r'<function=\w+.*?</function>', re.DOTALL | re.IGNORECASE),
    re.compile(r'^\s*\{\s*"(?:type|function|name|tool)"\s*:.*?\}\s*$', re.DOTALL | re.MULTILINE),
]

def _clean_reply(content: str) -> str:
    """Strip raw tool-call JSON / XML artefacts from the LLM reply."""
    if not content:
        return "🎵"
    for pattern in _TOOL_CALL_PATTERNS:
        content = pattern.sub("", content)
    return content.strip() or "🎵"


# ── Agent entry point ─────────────────────────────────────────────────────────

async def run_agent(message: str, session_id: str, user_uid: str = "") -> dict:
    """
    Run the SunLeo DJ agent.

    Flow:
    1. Send user message + tool schemas to LLM (Groq primary, Gemini fallback)
    2. If model returns tool_calls → execute them, feed results back
    3. Repeat until model returns a final text response (max 6 loops)
    4. Return {reply, actions}
    """
    # Build conversation
    history = _get_messages(session_id)
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
        _sessions[session_id] = history

    # Add user message
    user_msg = {"role": "user", "content": message}
    _add_message(session_id, user_msg)

    last_content = ""
    collected_actions: list[dict] = []

    # Tool-call loop (max 6 iterations to prevent runaway)
    for _ in range(6):
        try:
            response = await chat_completion(
                session_id=session_id,
                messages=_get_messages(session_id),
                tools=TOOL_SCHEMAS,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            error_str = str(exc)
            log.error("LLM call failed for session %s: %s", session_id, error_str)

            # tool_use_failed — strip broken messages and retry without tools
            if "tool_use_failed" in error_str or "failed_generation" in error_str:
                try:
                    cleaned = [m for m in _get_messages(session_id)
                               if not (m.get("role") == "assistant" and m.get("tool_calls"))]
                    _sessions[session_id] = cleaned

                    fallback = await chat_completion(
                        session_id=session_id,
                        messages=cleaned,
                        tools=None,  # no tools — force text response
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    fallback_content = fallback.choices[0].message.content or ""
                    if fallback_content:
                        _add_message(session_id, {"role": "assistant", "content": fallback_content})
                        return {"reply": _clean_reply(fallback_content), "actions": collected_actions}
                except Exception as fallback_exc:
                    log.error("Tool-use fallback also failed: %s", fallback_exc)

            return {
                "reply": "🎵 Sorry, I had a hiccup processing that request. Could you try again in a moment?",
                "actions": [],
            }

        choice = response.choices[0]
        assistant_msg = choice.message

        # Convert to dict for storage
        msg_dict: dict = {"role": "assistant", "content": assistant_msg.content or ""}
        if assistant_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ]
        _add_message(session_id, msg_dict)

        if assistant_msg.content:
            last_content = assistant_msg.content

        # If no tool calls, we have the final answer
        if not assistant_msg.tool_calls:
            return {"reply": _clean_reply(assistant_msg.content or last_content), "actions": collected_actions}

        # Execute each tool call and feed results back
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                fn_args = {}
            if not isinstance(fn_args, dict):
                fn_args = {}

            result = _dispatch_tool(fn_name, fn_args, user_uid, session_id)

            # Update session state from tool results
            _update_session_from_tool_result(session_id, fn_name, result)

            # Collect download actions for frontend
            if fn_name in ("download_track", "download_tracks_by_index", "bulk_download_playlist"):
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, list):
                        for r in parsed:
                            if isinstance(r, dict) and r.get("job_id"):
                                collected_actions.append({
                                    "type": "download_queued",
                                    "job_id": r["job_id"],
                                    "track_name": r.get("track_name", ""),
                                    "artist_name": r.get("artist_name", ""),
                                })
                    elif isinstance(parsed, dict) and parsed.get("job_id"):
                        collected_actions.append({
                            "type": "download_queued",
                            "job_id": parsed["job_id"],
                            "track_name": parsed.get("track_name", ""),
                            "artist_name": parsed.get("artist_name", ""),
                        })
                except (json.JSONDecodeError, TypeError):
                    pass

            tool_result_msg = {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            }
            _add_message(session_id, tool_result_msg)

    # If we exhausted iterations, return last content
    return {
        "reply": _clean_reply(last_content) or "🎵 I got a bit carried away! Could you try again?",
        "actions": collected_actions,
    }
