import streamlit as st
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

st.set_page_config(page_title="Sun Leo — Discovery", page_icon="🔍", layout="wide")

# Apply shared design system
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from _styles import inject_styles, section_label
inject_styles()

# ──────────────── AUTH GATE ────────────────
if not st.session_state.get("firebase_user"):
    st.markdown(
        "<div style='text-align:center; padding:4rem 0;'>"
        "<div style='font-size:3rem; margin-bottom:1rem;'>🔒</div>"
        "<h2 style='color:#f1f5f9;'>Sign in to Discover Music</h2>"
        "<p style='color:#94a3b8; max-width:400px; margin:0.5rem auto;'>"
        "Search millions of songs, explore by mood, and download instantly. "
        "Sign in from the Home page to get started."
        "</p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ──────────────── CONFIG ────────────────
RECOMMENDATION_API_URL = os.getenv("RECOMMENDATION_API_URL", "http://localhost:8001")
YTCONVERTER_API_URL    = os.getenv("API_GATEWAY_URL",        "http://127.0.0.1:8000")

# Session state
if "discovery_jobs"  not in st.session_state: st.session_state.discovery_jobs  = []
if "search_results"  not in st.session_state: st.session_state.search_results  = []
if "mood_results"    not in st.session_state: st.session_state.mood_results    = []


# ═══════════════════════════════════════════════════════
#  DOWNLOAD HELPER  — defined HERE (before tabs) to avoid
#  forward-reference NameError when a button is clicked.
# ═══════════════════════════════════════════════════════
def _trigger_download(track: dict, idx: int, source: str):
    """
    Delegates the full YouTube-search → download pipeline to the
    Discovery backend service (/resolve-and-queue), so the frontend
    stays thin and error-resilient.
    """
    track_name  = track.get("track_name",  "Unknown")
    artist_name = track.get("artist_name", "Unknown")
    search_query = track.get("search_query", f"{track_name} {artist_name} audio")

    with st.spinner(f"Finding & queuing \"{track_name}\" by {artist_name}…"):
        try:
            resp = requests.post(
                f"{RECOMMENDATION_API_URL}/resolve-and-queue",
                json={
                    "track_name":   track_name,
                    "artist_name":  artist_name,
                    "search_query": search_query,
                },
                timeout=30,   # yt-dlp fallback can take a few seconds
            )
        except requests.exceptions.ConnectionError:
            st.error(
                "⚠️ Discovery service is offline. "
                "Make sure the recommendation backend is running on port 8001."
            )
            return
        except requests.exceptions.Timeout:
            st.error("⏱️ The request timed out while searching YouTube. Please try again.")
            return
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return

    # ── Handle response codes ────────────────────────────────
    if resp.status_code == 200:
        data   = resp.json()
        job_id = data.get("job_id", "")
        st.success(f"✅ Download queued: **{track_name}**")
        st.session_state.discovery_jobs.append({
            "job_id": job_id,
            "url":    data.get("youtube_url", ""),
            "title":  track_name,
        })
        if "library" not in st.session_state:
            st.session_state.library = []

    elif resp.status_code == 404:
        st.warning(
            f"🔍 Could not find **{track_name}** on YouTube. "
            "You can try downloading it manually from the Home page."
        )

    elif resp.status_code == 503:
        st.error(
            "🚫 The download service (ytconverter) is offline. "
            "Make sure it is running on port 8000."
        )

    elif resp.status_code == 429:
        st.warning(
            "⏳ YouTube search quota reached for today. "
            "The system will automatically retry with yt-dlp. Try again shortly."
        )

    else:
        # Surface the backend error message for any unexpected status
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        st.error(f"Download error ({resp.status_code}): {detail}")


# ──────────────── HEADER ────────────────
st.markdown(
    "<div style='margin-bottom:0.5rem;'>"
    "<div class='hero-title' style='font-size:2.2rem;'>🔍 Discover Music</div>"
    "<div class='hero-subtitle'>Search millions of songs or explore by mood. "
    "One click to download.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)


# ──────────────── TAB LAYOUT ────────────────
tab_search, tab_mood = st.tabs(["🔎 Search Songs", "🎭 Discover by Mood"])


# ═══════════════════════════════════════════════
#  TAB 1: SEARCH BY NAME / ARTIST
# ═══════════════════════════════════════════════
with tab_search:
    search_col, btn_col = st.columns([5, 1])
    with search_col:
        search_query = st.text_input(
            "Search",
            placeholder="Search for any song, artist, or album…",
            label_visibility="collapsed",
            key="search_input",
        )
    with btn_col:
        search_clicked = st.button("🔍 Search", use_container_width=True, key="search_btn")

    # Execute search
    if search_clicked and search_query:
        with st.spinner("Searching iTunes catalog…"):
            try:
                res = requests.get(
                    f"{RECOMMENDATION_API_URL}/search",
                    params={"q": search_query, "limit": 15},
                    timeout=10,
                )
                if res.status_code == 200:
                    st.session_state.search_results = res.json()
                elif res.status_code == 503:
                    st.error("Discovery service returned an error. Check your API keys.")
                    st.session_state.search_results = []
                else:
                    st.error(f"Search error: {res.text}")
                    st.session_state.search_results = []

            except requests.exceptions.ConnectionError:
                # Graceful fallback: call iTunes directly from frontend
                st.caption("ℹ️ Discovery service offline — falling back to direct iTunes search.")
                try:
                    res = requests.get(
                        "https://itunes.apple.com/search",
                        params={"term": search_query, "media": "music", "entity": "song", "limit": 15},
                        timeout=10,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.search_results = [
                            {
                                "track_name":   item.get("trackName",      "Unknown"),
                                "artist_name":  item.get("artistName",     "Unknown"),
                                "album_name":   item.get("collectionName", ""),
                                "artwork_url":  item.get("artworkUrl100",  "").replace("100x100bb", "600x600bb"),
                                "preview_url":  item.get("previewUrl",     ""),
                                "duration_ms":  item.get("trackTimeMillis", 0),
                                "genre":        item.get("primaryGenreName", ""),
                                "search_query": f"{item.get('trackName','')} {item.get('artistName','')} audio",
                            }
                            for item in data.get("results", [])
                        ]
                    else:
                        st.error("iTunes search failed.")
                        st.session_state.search_results = []
                except Exception as e:
                    st.error(f"Could not reach iTunes: {e}")
                    st.session_state.search_results = []

            except Exception as e:
                st.error(f"Search failed: {e}")
                st.session_state.search_results = []

    elif search_clicked and not search_query:
        st.warning("Please enter a search term.")

    # ── Render results ──
    results = st.session_state.search_results
    if results:
        st.markdown(
            f"<div style='color:#94a3b8; font-size:0.85rem; margin:0.8rem 0;'>"
            f"Found {len(results)} results</div>",
            unsafe_allow_html=True,
        )

        for idx, track in enumerate(results):
            with st.container():
                col_art, col_info, col_action = st.columns([1, 4, 1.5])

                with col_art:
                    artwork = track.get("artwork_url", "")
                    if artwork:
                        st.image(artwork, width=80)
                    else:
                        st.markdown(
                            "<div style='width:80px;height:80px;background:rgba(124,58,237,0.15);"
                            "border-radius:10px;display:flex;align-items:center;justify-content:center;"
                            "font-size:2rem;'>🎵</div>",
                            unsafe_allow_html=True,
                        )

                with col_info:
                    name        = track.get("track_name",  "Unknown")
                    artist      = track.get("artist_name", "Unknown")
                    album       = track.get("album_name",  "")
                    genre       = track.get("genre",       "")
                    duration_ms = track.get("duration_ms", 0)
                    duration_str = ""
                    if duration_ms:
                        mins = duration_ms // 60000
                        secs = (duration_ms % 60000) // 1000
                        duration_str = f"{mins}:{secs:02d}"

                    st.markdown(
                        f"<div style='margin-top:4px;'>"
                        f"<div style='font-size:1rem; font-weight:600; color:#f1f5f9;'>{name}</div>"
                        f"<div style='font-size:0.85rem; color:#94a3b8;'>{artist}"
                        f"{' · ' + album if album else ''}"
                        f"{' · ' + duration_str if duration_str else ''}"
                        f"</div>"
                        f"<div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>{genre}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    preview = track.get("preview_url", "")
                    if preview:
                        st.audio(preview, format="audio/mp4")

                with col_action:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    if st.button("⬇ Download", key=f"dl_search_{idx}", use_container_width=True):
                        _trigger_download(track, idx, "search")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    "<hr style='margin:0.5rem 0; border-color:rgba(255,255,255,0.04);'>",
                    unsafe_allow_html=True,
                )

    elif search_query and search_clicked:
        st.info("No results found. Try a different search term.")


# ═══════════════════════════════════════════════
#  TAB 2: DISCOVER BY MOOD
# ═══════════════════════════════════════════════
with tab_mood:
    st.markdown(section_label("PICK A VIBE"), unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94a3b8; font-size:0.9rem; margin-bottom:1rem;'>"
        "Select a mood to discover top tracks. Powered by Last.fm · Artwork via iTunes.</p>",
        unsafe_allow_html=True,
    )

    mood_options = [
        ("😌 Chill",      "chill"),
        ("🏋️ Workout",   "workout"),
        ("😢 Sad",        "sad"),
        ("😄 Happy",      "happy"),
        ("🎯 Focus",      "focus"),
        ("🎉 Party",      "party"),
        ("💤 Sleep",      "sleep"),
        ("🚗 Road Trip",  "road trip"),
        ("📚 Study",      "study"),
        ("🎸 Indie",      "indie"),
        ("🎹 Lo-fi",      "lo-fi"),
        ("🎷 Jazz",       "jazz"),
    ]

    cols = st.columns(6)
    selected_mood = None
    for i, (label, tag) in enumerate(mood_options):
        with cols[i % 6]:
            if st.button(label, key=f"mood_{tag}", use_container_width=True):
                selected_mood = tag

    if selected_mood:
        with st.spinner(f"Finding {selected_mood} tracks + artwork…"):
            try:
                res = requests.get(
                    f"{RECOMMENDATION_API_URL}/mood",
                    params={"tag": selected_mood, "limit": 20},
                    timeout=20,   # iTunes artwork enrichment adds a few seconds
                )
                if res.status_code == 200:
                    st.session_state.mood_results = res.json()
                elif res.status_code == 503:
                    st.warning(
                        "Last.fm API key not configured. "
                        "Add LASTFM_API_KEY to your .env file to enable mood discovery."
                    )
                    st.session_state.mood_results = []
                else:
                    st.error(f"Error: {res.text}")
                    st.session_state.mood_results = []
            except requests.exceptions.ConnectionError:
                st.error(
                    "⚠️ Could not connect to the Discovery service. "
                    "Make sure it is running on port 8001 (launch via Start-SunLeo.bat)."
                )
                st.session_state.mood_results = []
            except Exception as e:
                st.error(f"Mood discovery failed: {e}")
                st.session_state.mood_results = []

    # ── Render mood results ──
    mood_tracks = st.session_state.mood_results
    if mood_tracks:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:#a78bfa; font-size:0.9rem; font-weight:600; "
            f"margin-bottom:0.8rem;'>Found {len(mood_tracks)} tracks</div>",
            unsafe_allow_html=True,
        )

        for idx, track in enumerate(mood_tracks):
            with st.container():
                col_art, col_info, col_action = st.columns([1, 4, 1.5])

                with col_art:
                    artwork = track.get("artwork_url", "")
                    if artwork:
                        st.image(artwork, width=80)
                    else:
                        st.markdown(
                            "<div style='width:80px;height:80px;background:rgba(124,58,237,0.15);"
                            "border-radius:10px;display:flex;align-items:center;justify-content:center;"
                            "font-size:2rem;'>🎵</div>",
                            unsafe_allow_html=True,
                        )

                with col_info:
                    name   = track.get("track_name",  "Unknown")
                    artist = track.get("artist_name", "Unknown")
                    st.markdown(
                        f"<div style='margin-top:14px;'>"
                        f"<div style='font-size:1rem; font-weight:600; color:#f1f5f9;'>{name}</div>"
                        f"<div style='font-size:0.85rem; color:#94a3b8;'>{artist}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with col_action:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    if st.button("⬇ Download", key=f"dl_mood_{idx}", use_container_width=True):
                        _trigger_download(track, idx, "mood")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    "<hr style='margin:0.5rem 0; border-color:rgba(255,255,255,0.04);'>",
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════
#  DOWNLOAD STATUS SECTION
# ═══════════════════════════════════════════════
if st.session_state.discovery_jobs:
    import time

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(section_label("DOWNLOAD STATUS"), unsafe_allow_html=True)
    st.markdown(
        "<h3 style='margin-top:4px; font-size:1.1rem;'>📡 Active Downloads</h3>",
        unsafe_allow_html=True,
    )

    all_completed = True
    newly_added    = False   # tracks whether this run appended anything to the library

    for job in st.session_state.discovery_jobs:
        job_id = job.get("job_id", "")
        if not job_id:
            continue
        try:
            status_resp = requests.get(
                f"{YTCONVERTER_API_URL}/status/{job_id}", timeout=5
            )
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                status = s_data.get("status", "unknown")
                title  = s_data.get("title") or job.get("title") or job.get("url", "Unknown")

                color = "#a78bfa"
                if status == "completed": color = "#34d399"
                elif status == "failed":  color = "#f87171"

                st.markdown(
                    f"<div style='display:flex; align-items:center; gap:8px; "
                    f"padding:8px 14px; background:rgba(255,255,255,0.03); "
                    f"border-radius:10px; border:1px solid rgba(255,255,255,0.06); "
                    f"margin-bottom:6px;'>"
                    f"<span style='width:8px;height:8px;border-radius:50%; "
                    f"background:{color};display:inline-block;'></span>"
                    f"<span style='font-size:0.9rem; font-weight:500;'>{title}</span>"
                    f"<span style='margin-left:auto; font-size:0.75rem; color:{color}; "
                    f"font-weight:600; text-transform:uppercase;'>{status}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if status == "completed":
                    full_url = f"{YTCONVERTER_API_URL}{s_data.get('download_url', '')}"
                    metadata = s_data.get("metadata", {})
                    if "library" not in st.session_state:
                        st.session_state.library = []
                    if not any(s["url"] == full_url for s in st.session_state.library):
                        st.session_state.library.append(
                            {"url": full_url, "title": title, "metadata": metadata}
                        )
                        newly_added = True   # flag so we rerun once more to surface it
                elif status not in ("completed", "failed"):
                    all_completed = False

                if status == "failed":
                    err = s_data.get("error", "Unknown error")
                    st.caption(f"⚠️ Failed: {err}")

        except requests.exceptions.ConnectionError:
            st.warning("⚠️ Cannot reach ytconverter to check download status.")
        except Exception:
            pass  # silently skip bad status checks

    if not all_completed:
        time.sleep(3)
        st.rerun()
    elif newly_added:
        # All jobs done AND we just added new tracks to the library —
        # fire one final rerun so the sidebar player reflects them immediately.
        st.rerun()
