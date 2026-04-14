"""
SunLeo DJ Agent — powered by Groq's native function-calling API.

Uses the `groq` SDK directly (OpenAI-compatible tool_call protocol).
No LangChain, no LangGraph — just clean, reliable code.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict

from groq import Groq

from . import tools as T

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are SunLeo DJ 🎵, a friendly and enthusiastic AI music assistant.

Your capabilities:
1. SEARCH — Find songs by name, artist, or album
2. DISCOVER — Suggest songs by mood/activity (chill, workout, sad, happy, study, party, sleep, road trip)
3. DOWNLOAD — Download songs as MP3 (always confirm with the user first!)
4. PLAYLISTS — Create, view, and manage playlists
5. BULK DOWNLOAD — Download all songs in a playlist at once

Behaviour rules:
- Always present song options BEFORE downloading. Never auto-download.
- Format track suggestions as numbered lists with artist names.
- When the user says "download #3" or "download all", execute the download.
- Map natural moods: "something for studying" → mood="study"
- Be conversational, use music emojis 🎵🎶🎸🥁🎤, keep responses concise.
- If user wants a playlist, ask for a name if not provided.
- For bulk downloads, confirm playlist name + track count before downloading.

Mood mapping:
  Chill/Relax/Unwind → chill | Gym/Workout/Run → workout
  Sad/Heartbreak → sad | Happy/Joy → happy | Study/Focus → study
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
            "description": "Get track recommendations for a mood or activity. Moods: chill, workout, sad, happy, study, focus, party, sleep, road trip.",
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
            "name": "download_track",
            "description": "Resolve a track to YouTube and queue MP3 download. ONLY call after user confirms.",
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
            "name": "check_download_status",
            "description": "Check download status for job IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_ids_json": {"type": "string", "description": "JSON array of job_id strings"},
                },
                "required": ["job_ids_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_playlist",
            "description": "Create a named playlist for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Playlist name"},
                    "tracks_json": {"type": "string", "description": "JSON array of track objects", "default": "[]"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_playlist",
            "description": "Add tracks to an existing playlist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string"},
                    "tracks_json": {"type": "string", "description": "JSON array of track objects"},
                },
                "required": ["playlist_id", "tracks_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_playlists",
            "description": "List all playlists belonging to the current user. No arguments needed.",
            "parameters": {"type": "object", "properties": {}},
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
]

# ── Tool dispatcher ───────────────────────────────────────────────────────────

# Tools that need user_uid injected
_UID_TOOLS = {"create_playlist", "add_to_playlist", "list_playlists", "bulk_download_playlist"}

def _dispatch_tool(name: str, args: dict, user_uid: str) -> str:
    """Call the matching tool function and return its JSON result."""
    # Inject user_uid for playlist tools
    if name in _UID_TOOLS:
        args["user_uid"] = user_uid

    fn = getattr(T, name, None)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        return fn(**args)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})

# ── Conversation memory (in-process) ─────────────────────────────────────────

_sessions: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 20  # keep last 20 messages per session

def _get_messages(session_id: str) -> list[dict]:
    return _sessions[session_id]

def _add_message(session_id: str, msg: dict):
    history = _sessions[session_id]
    history.append(msg)
    # Trim to keep memory bounded (always keep system prompt)
    if len(history) > MAX_HISTORY:
        _sessions[session_id] = history[-MAX_HISTORY:]

# ── Reply sanitizer ──────────────────────────────────────────────────────────

# Patterns that indicate raw tool-call artefacts leaking into the reply
_TOOL_CALL_PATTERNS = [
    # Markdown-fenced JSON block containing `function` or `name` key
    re.compile(r'```(?:json)?\s*\{[^`]*?(?:"function"|"tool_call"|"name").*?\}\s*```', re.DOTALL | re.IGNORECASE),
    # XML-style <tool_call>...</tool_call> tags
    re.compile(r'<tool_call>.*?</tool_call>', re.DOTALL | re.IGNORECASE),
    # Bare JSON objects on their own line that look like tool invocations
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
    1. Send user message + tool schemas to Groq
    2. If model returns tool_calls → execute them, feed results back
    3. Repeat until model returns a final text response (max 6 loops)
    4. Return {reply, actions}
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "reply": "⚠️ Groq API key is not configured. Set `GROQ_API_KEY` in your `.env` file.",
            "actions": [],
        }

    client = Groq(api_key=api_key)

    # Build conversation
    history = _get_messages(session_id)
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
        _sessions[session_id] = history

    # Add user message
    user_msg = {"role": "user", "content": message}
    _add_message(session_id, user_msg)

    last_content = ""

    # Tool-call loop (max 6 iterations to prevent runaway)
    for _ in range(6):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=_get_messages(session_id),
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            return {"reply": f"⚠️ Groq API error: {exc}", "actions": []}

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

        # Track last non-empty content for fallback
        if assistant_msg.content:
            last_content = assistant_msg.content

        # If no tool calls, we have the final answer
        if not assistant_msg.tool_calls:
            return {"reply": _clean_reply(assistant_msg.content or last_content), "actions": []}

        # Execute each tool call and feed results back
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            result = _dispatch_tool(fn_name, fn_args, user_uid)

            tool_result_msg = {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            }
            _add_message(session_id, tool_result_msg)

    # If we exhausted iterations, return last content
    return {
        "reply": _clean_reply(last_content) or "🎵 I got a bit carried away! Could you try again?",
        "actions": [],
    }
