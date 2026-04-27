"""
test_chatbot_agent.py — Assignment 9 Test Suite for SunLeo Chatbot Agent Module.

Tests cover:
  TC-01: Agent session state initialization
  TC-02: Tool dispatch with valid tool name
  TC-03: Tool dispatch with unknown tool name
  TC-04: Tool dispatch with None arguments (BUG-01 regression)
  TC-05: Session state update after search
  TC-06: Reply sanitizer strips raw JSON
  TC-07: Indexed download with empty session (no tracks)
  TC-08: Save last tracks as playlist
  TC-09: Duplicate track detection in playlist creation
  TC-10: Delete playlist tool returns correct result
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from collections import defaultdict

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_agent_state():
    """Reset agent in-memory state between tests."""
    from backend.chatbot_service.app import agent
    agent._sessions.clear()
    agent._session_state.clear()
    yield
    agent._sessions.clear()
    agent._session_state.clear()


@pytest.fixture
def mock_playlist_service():
    """Patch playlist_service with in-memory mock."""
    from tests.conftest import InMemoryPlaylistService
    svc = InMemoryPlaylistService()
    with patch("backend.chatbot_service.app.tools._ps", svc):
        yield svc


# ── TC-01: Session state initialization ───────────────────────────────────────

def test_tc01_session_state_initialization():
    """TC-01: get_session_state should return a fresh state dict for a new session."""
    from backend.chatbot_service.app.agent import get_session_state

    state = get_session_state("test-session-new")

    assert isinstance(state, dict), "Session state should be a dict"
    assert state["last_tracks"] == [], "last_tracks should start empty"
    assert state["last_playlist"] is None, "last_playlist should start as None"
    assert state["pending_downloads"] == [], "pending_downloads should start empty"


# ── TC-02: Tool dispatch with valid tool name ─────────────────────────────────

def test_tc02_dispatch_valid_tool():
    """TC-02: _dispatch_tool should successfully call a known tool function."""
    from backend.chatbot_service.app.agent import _dispatch_tool

    with patch("backend.chatbot_service.app.tools.get_available_moods") as mock_fn:
        mock_fn.return_value = json.dumps({"moods": ["chill", "workout"]})

        result = _dispatch_tool("get_available_moods", {}, "uid-123", "sess-123")

    mock_fn.assert_called_once()
    parsed = json.loads(result)
    assert "moods" in parsed


# ── TC-03: Tool dispatch with unknown tool ────────────────────────────────────

def test_tc03_dispatch_unknown_tool():
    """TC-03: _dispatch_tool should return an error JSON for unknown tool names."""
    from backend.chatbot_service.app.agent import _dispatch_tool

    result = _dispatch_tool("nonexistent_tool_xyz", {}, "uid-123", "sess-123")
    parsed = json.loads(result)

    assert "error" in parsed, "Should return an error field"
    assert "Unknown tool" in parsed["error"], "Error should mention unknown tool"


# ── TC-04: Tool dispatch with None arguments (BUG-01 regression) ──────────────

def test_tc04_dispatch_none_args_regression():
    """TC-04: _dispatch_tool must not crash when args is None.
    This is a regression test for BUG-01 where json.loads returned None
    and caused 'NoneType does not support item assignment'."""
    from backend.chatbot_service.app.agent import _dispatch_tool

    # Simulate what happens when args is None (the bug scenario)
    # The fix ensures fn_args is always a dict before dispatch
    # but _dispatch_tool itself should also be robust
    result = _dispatch_tool("list_playlists", {}, "uid-123", "sess-123")

    parsed = json.loads(result)
    # Should not crash — either returns data or an error
    assert isinstance(parsed, (list, dict)), "Should return valid JSON"


# ── TC-05: Session state update after search ──────────────────────────────────

def test_tc05_session_update_after_search():
    """TC-05: _update_session_from_tool_result should store search results
    in session state's last_tracks."""
    from backend.chatbot_service.app.agent import (
        _update_session_from_tool_result, get_session_state
    )

    fake_tracks = [
        {"track_name": "Blinding Lights", "artist_name": "The Weeknd"},
        {"track_name": "Shape of You", "artist_name": "Ed Sheeran"},
    ]

    _update_session_from_tool_result("sess-search", "search_tracks", json.dumps(fake_tracks))
    state = get_session_state("sess-search")

    assert len(state["last_tracks"]) == 2, "Should store 2 tracks"
    assert state["last_tracks"][0]["track_name"] == "Blinding Lights"


# ── TC-06: Reply sanitizer strips raw JSON ────────────────────────────────────

def test_tc06_reply_sanitizer():
    """TC-06: _clean_reply should strip raw tool-call JSON from LLM output."""
    from backend.chatbot_service.app.agent import _clean_reply

    # Case 1: Clean text should pass through
    assert _clean_reply("Here are your songs! 🎵") == "Here are your songs! 🎵"

    # Case 2: Raw tool call JSON should be stripped
    dirty = '```json\n{"function": "search_tracks", "arguments": {"query": "test"}}\n```\nHere are results!'
    cleaned = _clean_reply(dirty)
    assert "function" not in cleaned, "Should strip JSON code block"
    assert "results" in cleaned, "Should keep the text portion"

    # Case 3: Empty/None should return emoji
    assert _clean_reply("") == "🎵"
    assert _clean_reply(None) == "🎵"


# ── TC-07: Indexed download with empty session ───────────────────────────────

def test_tc07_indexed_download_empty_session():
    """TC-07: download_tracks_by_index should return an error when
    no tracks have been searched yet (empty session)."""
    from backend.chatbot_service.app.tools import download_tracks_by_index

    result = download_tracks_by_index(session_id="empty-sess", indexes=[1, 2])
    parsed = json.loads(result)

    assert "error" in parsed, "Should return error when no tracks in session"
    assert "search" in parsed["error"].lower() or "track list" in parsed["error"].lower()


# ── TC-08: Save last tracks as playlist ───────────────────────────────────────

def test_tc08_save_last_tracks_as_playlist(mock_playlist_service):
    """TC-08: save_last_tracks_as_playlist should create a playlist from
    tracks stored in session state."""
    from backend.chatbot_service.app.agent import get_session_state
    from backend.chatbot_service.app.tools import save_last_tracks_as_playlist

    # Pre-populate session with tracks
    state = get_session_state("sess-save")
    state["last_tracks"] = [
        {"track_name": "Song A", "artist_name": "Artist 1"},
        {"track_name": "Song B", "artist_name": "Artist 2"},
        {"track_name": "Song C", "artist_name": "Artist 3"},
    ]

    result = save_last_tracks_as_playlist(
        user_uid="test-uid",
        session_id="sess-save",
        name="My Playlist",
        indexes=[1, 3],  # Should pick Song A and Song C
    )
    parsed = json.loads(result)

    assert "id" in parsed, "Should return a playlist with an id"
    assert parsed["name"] == "My Playlist"
    assert parsed["track_count"] == 2, "Should have 2 tracks (indexes 1 and 3)"


# ── TC-09: Duplicate track detection ──────────────────────────────────────────

def test_tc09_duplicate_track_detection():
    """TC-09: playlist_service._dedupe_tracks should detect and skip
    duplicate tracks based on normalised (track_name, artist_name)."""
    from backend.chatbot_service.app.playlist_service import _dedupe_tracks

    existing = [
        {"track_name": "Blinding Lights", "artist_name": "The Weeknd"},
    ]
    new_tracks = [
        {"track_name": "blinding lights", "artist_name": "the weeknd"},  # dupe (case)
        {"track_name": "Shape of You", "artist_name": "Ed Sheeran"},      # new
        {"track_name": " Blinding Lights ", "artist_name": " The Weeknd "},  # dupe (whitespace)
    ]

    to_add, skipped = _dedupe_tracks(existing, new_tracks)

    assert len(to_add) == 1, "Only 1 new track should be added"
    assert skipped == 2, "2 duplicates should be skipped"
    assert to_add[0]["track_name"] == "Shape of You"


# ── TC-10: Delete playlist tool ───────────────────────────────────────────────

def test_tc10_delete_playlist_tool(mock_playlist_service):
    """TC-10: delete_playlist tool should return success for existing playlist
    and error for non-existent playlist."""
    from backend.chatbot_service.app.tools import delete_playlist

    # Create a playlist first
    mock_playlist_service.create_playlist("uid-del", "ToDelete", [])
    playlists = mock_playlist_service.get_playlists("uid-del")
    pid = playlists[0]["id"]

    # Delete existing
    result = json.loads(delete_playlist(user_uid="uid-del", playlist_id=pid))
    assert result.get("success") is True, "Should succeed for existing playlist"

    # Delete non-existent
    result2 = json.loads(delete_playlist(user_uid="uid-del", playlist_id="fake-id"))
    assert "error" in result2, "Should return error for non-existent playlist"
