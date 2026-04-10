import streamlit as st
import os
from pathlib import Path

# ------------ LOAD .env FROM PROJECT ROOT ------------
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="Sun Leo — Free Music Downloader",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────── DESIGN SYSTEM ────────────────
from _styles import inject_styles, hero_block, section_label, feature_comparison_table

inject_styles()

# ──────────────── FIREBASE CONFIG ────────────────
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}

# ──────────────── SESSION STATE ────────────────
if "library" not in st.session_state:
    st.session_state.library = []
if "auto_refresh_trigger" not in st.session_state:
    st.session_state.auto_refresh_trigger = False
if "firebase_user" not in st.session_state:
    st.session_state.firebase_user = None


def is_logged_in():
    return st.session_state.firebase_user is not None


# ──────────────── FIREBASE AUTH INIT ────────────────
def _init_firebase_auth():
    """Initialise Firebase Auth and check session."""
    try:
        from streamlit_firebase_auth import FirebaseAuth

        auth = FirebaseAuth(firebase_config=FIREBASE_CONFIG)
        user = auth.check_session()
        return auth, user
    except ImportError:
        st.error(
            "Firebase auth package not installed. "
            "Run: `pip install streamlit-firebase-auth`"
        )
        return None, None
    except Exception as e:
        st.error(f"Firebase initialisation error: {e}")
        return None, None


auth_obj, session_user = _init_firebase_auth()

# Sync to session state
if session_user and isinstance(session_user, dict) and session_user.get("email"):
    st.session_state.firebase_user = session_user
elif session_user is None:
    st.session_state.firebase_user = None


# ──────────────── LOGIN DIALOG (MODAL) ────────────────
@st.dialog("Sign in to Sun Leo", width="small")
def login_dialog():
    """Renders the Firebase login form inside a centered modal dialog."""
    st.markdown(
        "<p style='color: #94a3b8; font-size: 0.92rem; margin-bottom: 1rem;'>"
        "Sign in with Google to unlock Discovery, Playlists, and the Chatbot DJ."
        "</p>",
        unsafe_allow_html=True,
    )
    if auth_obj:
        auth_obj.login_form()
    else:
        st.error("Firebase is not configured. Check your .env file.")


# ═══════════════════════════════════════════════════════
#  HEADER — logo left · user chip / Sign-In right
# ═══════════════════════════════════════════════════════
header_left, header_right = st.columns([7, 3])

with header_left:
    st.markdown(
        "<div style='display:flex; align-items:center; gap:10px;'>"
        "<span style='font-size:1.6rem;'>🎵</span>"
        "<span style='font-size:1.3rem; font-weight:700; "
        "background:linear-gradient(135deg,#7c3aed,#2563eb); "
        "-webkit-background-clip:text; -webkit-text-fill-color:transparent;'>"
        "Sun Leo</span>"
        "</div>",
        unsafe_allow_html=True,
    )

with header_right:
    if is_logged_in():
        user = st.session_state.firebase_user
        display_name = user.get("displayName", user.get("email", "User"))
        initial = display_name[0].upper()

        # User chip + Logout button in a row
        chip_col, logout_col = st.columns([3, 1])
        with chip_col:
            st.markdown(
                f"<div class='user-chip'>"
                f"<div class='user-avatar'>{initial}</div>"
                f"<span>{display_name}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with logout_col:
            if st.button("Logout", key="header_logout", type="secondary"):
                st.session_state.firebase_user = None
                st.rerun()
    else:
        # Sign In pill button (triggers the modal dialog)
        if st.button("✨ Sign In", key="header_signin"):
            login_dialog()

st.markdown("<hr style='margin:0.8rem 0 1.5rem 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  HERO SECTION
# ═══════════════════════════════════════════════════════
st.markdown(
    hero_block(
        "Find the melody<br>that moves you",
        "Download any song for free. Sign in to unlock playlists, "
        "AI discovery, and your personal DJ.",
    ),
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════
#  FREE DOWNLOAD SECTION — available to ALL users
# ═══════════════════════════════════════════════════════
st.markdown(section_label("FREE — NO ACCOUNT NEEDED"), unsafe_allow_html=True)
st.markdown(
    "<h2 style='margin-top:4px; font-size:1.5rem;'>⬇ Download from YouTube</h2>",
    unsafe_allow_html=True,
)

# --- Glassmorphic download card ---
st.markdown(
    '<div class="download-card">',
    unsafe_allow_html=True,
)

urls_text = st.text_area(
    "Paste YouTube links (one per line, up to 10)",
    placeholder="https://youtube.com/watch?v=...\nhttps://youtube.com/watch?v=...",
    height=120,
    label_visibility="collapsed",
)

API_BASE_URL = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:8000")

if st.button("🚀 Download MP3s", key="download_btn", use_container_width=True):
    urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
    if not urls:
        st.warning("Please paste at least one valid YouTube link.")
    elif len(urls) > 10:
        st.warning("Maximum 10 URLs are allowed per batch.")
    else:
        import requests
        import time

        with st.spinner("Submitting batch request to Conversion Service..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/convert/batch",
                    json={"urls": urls},
                    timeout=10,
                )
                if response.status_code != 200:
                    st.error(f"Error from service: {response.text}")
                else:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    st.success(f"Successfully queued {len(jobs)} jobs!")
                    st.session_state["active_jobs"] = jobs
            except Exception as e:
                st.error(f"Failed to connect to backend: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# ---- Poll and Display Job Status ----
if "active_jobs" in st.session_state and st.session_state["active_jobs"]:
    st.markdown(
        "<h3 style='margin-top:1.5rem; font-size:1.1rem;'>📡 Download Status</h3>",
        unsafe_allow_html=True,
    )
    import requests
    import time

    jobs = st.session_state["active_jobs"]
    all_completed = True

    for idx, job in enumerate(jobs):
        job_id = job["job_id"]
        try:
            status_resp = requests.get(
                f"{API_BASE_URL}/status/{job_id}", timeout=5
            )
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                status = s_data["status"]
                title = s_data.get("title") or job.get("url")

                c1, c2 = st.columns([4, 1])
                with c1:
                    # Status indicator
                    color = "#a78bfa"
                    if status == "completed":
                        color = "#34d399"
                    elif status == "failed":
                        color = "#f87171"

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
                    full_url = f"{API_BASE_URL}{s_data['download_url']}"
                    metadata = s_data.get("metadata", {})
                    if not any(
                        song["url"] == full_url
                        for song in st.session_state.library
                    ):
                        st.session_state.library.append(
                            {"url": full_url, "title": title, "metadata": metadata}
                        )
                        st.session_state.auto_refresh_trigger = True
                elif status == "failed":
                    pass  # already shown via color
                else:
                    all_completed = False
            else:
                st.error(f"Failed to get status for {job_id}")
        except Exception:
            st.error(f"Cannot reach backend to check {job_id}")

    if not all_completed:
        time.sleep(3)
        st.rerun()
    elif st.session_state.auto_refresh_trigger:
        st.session_state.auto_refresh_trigger = False
        st.rerun()


st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  FREEMIUM FEATURE TABLE
# ═══════════════════════════════════════════════════════
if not is_logged_in():
    st.markdown(section_label("WHY SIGN IN?"), unsafe_allow_html=True)
    st.markdown(
        "<h2 style='margin-top:4px; font-size:1.4rem;'>🔓 Unlock Premium Features</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(feature_comparison_table(), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✨ Create Free Account", key="cta_signin", use_container_width=True):
        login_dialog()

    st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  TRENDING PLAYLISTS (decorative)
# ═══════════════════════════════════════════════════════
st.markdown(section_label("TRENDING"), unsafe_allow_html=True)
st.markdown(
    "<h2 style='margin-top:4px; font-size:1.4rem;'>🔥 Popular Playlists</h2>",
    unsafe_allow_html=True,
)

playlists = [
    ("Top Hits", "https://images.unsplash.com/photo-1511376777868-611b54f68947?w=400"),
    ("Night Vibes", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400"),
    ("Upbeat Mix", "https://images.unsplash.com/photo-1492724441997-5dc865305da7?w=400"),
    ("Jazz Essentials", "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400"),
]

cols = st.columns(4, gap="medium")
for col, (name, img_url) in zip(cols, playlists):
    with col:
        st.markdown(
            f"<div class='playlist-card'>"
            f"<img src='{img_url}' alt='{name}'/>"
            f"<div class='title'>{name}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


st.markdown("<hr>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  SIDEBAR — Navigation Only (no auth widgets)
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='padding:0.5rem 0 1rem 0;'>"
        "<span style='font-size:1.4rem;'>🎵</span> "
        "<span style='font-size:1.1rem; font-weight:700; "
        "background:linear-gradient(135deg,#7c3aed,#2563eb); "
        "-webkit-background-clip:text; -webkit-text-fill-color:transparent;'>"
        "Sun Leo</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if is_logged_in():
        # ---- Music Player ----
        st.markdown(
            "<div class='section-label' style='margin-top:0.5rem;'>PLAYER</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.library:
            song_titles = [song["title"] for song in st.session_state.library]
            selected_title = st.selectbox(
                "Select a song",
                song_titles,
                label_visibility="collapsed",
            )

            selected_song = next(
                song
                for song in st.session_state.library
                if song["title"] == selected_title
            )

            file_url = selected_song["url"]
            metadata = selected_song.get("metadata", {})

            st.markdown(
                f"<p style='font-size:0.9rem; font-weight:600; margin:6px 0 2px 0;'>"
                f"🎶 {selected_song['title']}</p>",
                unsafe_allow_html=True,
            )
            if metadata:
                st.caption(
                    f"👤 {metadata.get('uploader', 'Unknown')} · "
                    f"👁️ {metadata.get('view_count', 0):,} views"
                )

            try:
                import requests as _req

                response = _req.get(file_url, stream=True)
                if response.status_code == 200:
                    st.audio(response.content, format="audio/mp3")
                    st.download_button(
                        label="📥 Save to Device",
                        data=response.content,
                        file_name=f"{selected_song['title']}.mp3",
                        mime="audio/mpeg",
                    )
                else:
                    st.error("Failed to load audio from server.")
            except Exception as e:
                st.error(f"Cannot play audio: {e}")
        else:
            st.info("Download a song to start playing.")

    else:
        st.markdown(
            "<div style='padding:1.5rem 0; text-align:center;'>"
            "<p style='color:#64748b; font-size:0.9rem;'>"
            "🔒 Sign in to unlock the full player, playlists, and AI features."
            "</p></div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════
st.markdown(
    "<div style='text-align:center; padding:2rem 0 1rem 0; color:#64748b; "
    "font-size:0.78rem;'>"
    "Built with ♥ by Sun Leo · "
    "<a href='#' style='color:#7c3aed; text-decoration:none;'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
