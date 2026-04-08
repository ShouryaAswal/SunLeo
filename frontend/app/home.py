import streamlit as st
import os
from pathlib import Path

# ------------ LOAD .env FROM PROJECT ROOT ------------
# home.py lives at frontend/app/home.py → project root is 2 levels up
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

st.set_page_config(page_title="Sun Leo", layout="wide")

# ---------------- FIREBASE CONFIG ----------------
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}

# ---------------- SESSION STATE ----------------
if "library" not in st.session_state:
    st.session_state.library = []

if "auto_refresh_trigger" not in st.session_state:
    st.session_state.auto_refresh_trigger = False

if "firebase_user" not in st.session_state:
    st.session_state.firebase_user = None


def is_logged_in():
    return st.session_state.firebase_user is not None


# ---------------- STYLING ----------------
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top left, #0f1626, #0b0f19 70%);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

section[data-testid="stSidebar"] {
    background-color: #0f1626;
    border-right: 1px solid #1f6feb;
}

section[data-testid="stSidebar"]:hover {
    width: 300px !important;
}

.stButton > button {
    background: linear-gradient(90deg, #1f6feb, #3b82f6);
    border-radius: 10px;
    color: white;
    border: none;
}

div[data-baseweb="input"] > div {
    background-color: #111827 !important;
    border: 2px solid #1f6feb !important;
    border-radius: 10px !important;
}

div[data-baseweb="input"] input {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
#  FIREBASE AUTHENTICATION  (streamlit-firebase-auth package)
# ============================================================
def _init_firebase_auth():
    """Initialise Firebase Auth and check session.
    Returns the authenticated user dict or None."""
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

# Sync to session state so pages can check auth
if session_user and isinstance(session_user, dict) and session_user.get("email"):
    st.session_state.firebase_user = session_user
elif session_user is None:
    st.session_state.firebase_user = None


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🎵 Sun Leo")

    # --- Auth controls in sidebar ---
    if is_logged_in():
        user = st.session_state.firebase_user
        st.success(
            f"Logged in as {user.get('displayName', user.get('email', 'User'))}"
        )
        if auth_obj:
            auth_obj.logout_form()

        feature = st.radio(
            "Features", ["Player", "Chatbot", "Create Playlist"]
        )

        if feature == "Player":
            st.subheader("Music Player")

            if st.session_state.library:
                song_titles = [song["title"] for song in st.session_state.library]
                selected_title = st.selectbox("Select a song to play:", song_titles)

                selected_song = next(
                    song
                    for song in st.session_state.library
                    if song["title"] == selected_title
                )

                file_url = selected_song["url"]
                metadata = selected_song.get("metadata", {})

                st.markdown(f"**Now Playing:** {selected_song['title']}")
                if metadata:
                    st.caption(
                        f"👤 {metadata.get('uploader', 'Unknown')} | "
                        f"👁️ {metadata.get('view_count', 0):,} views"
                    )

                try:
                    import requests

                    response = requests.get(file_url, stream=True)
                    if response.status_code == 200:
                        st.audio(response.content, format="audio/mp3")
                        st.download_button(
                            label="📥 Download to PC",
                            data=response.content,
                            file_name=f"{selected_song['title']}.mp3",
                            mime="audio/mpeg",
                        )
                    else:
                        st.error("Failed to load audio from server.")
                except Exception as e:
                    st.error(f"Cannot play audio: {e}")

            elif "last_downloaded" in st.session_state:
                file_path = st.session_state["last_downloaded"]
                if os.path.exists(file_path):
                    st.audio(file_path)
                else:
                    st.warning("Downloaded file not found.")
            else:
                st.info("Download a song first to play it here.")

        elif feature == "Chatbot":
            st.subheader("Playlist Chatbot")
            user_input = st.text_input("Ask for recommendations")
            if user_input:
                st.write("Sun Leo Bot:", "Try Night Vibes 🌙 or Upbeat Mix ⚡")

        elif feature == "Create Playlist":
            st.subheader("Create Playlist")
            playlist_name = st.text_input("Playlist Name")
            if st.button("Create Playlist"):
                st.success(f"{playlist_name} created successfully!")

    else:
        st.warning("Login to unlock features")
        st.info("👆 Use the login form on the main page to sign in.")


# ---------------- HEADER ----------------
col1, col2 = st.columns([8, 1])

with col1:
    st.markdown("<h1>Welcome to Sun Leo</h1>", unsafe_allow_html=True)
    st.markdown("Find the melody that moves you")

with col2:
    if is_logged_in():
        if st.button("Logout"):
            st.session_state.firebase_user = None
            st.rerun()

st.write("---")

# ----------- LOGIN SECTION (shown when not logged in) -----------
if not is_logged_in() and auth_obj:
    st.subheader("🔐 Sign in to Sun Leo")
    st.markdown(
        "Sign in with your Google account or email to unlock "
        "the player, chatbot, and playlist features."
    )
    auth_obj.login_form()
    st.write("---")

# ---------------- TRENDING PLAYLISTS ----------------
st.subheader("Trending Playlists")

playlists = [
    ("Top Hits", "https://images.unsplash.com/photo-1511376777868-611b54f68947?w=600"),
    ("Night Vibes", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600"),
    ("Upbeat Mix", "https://images.unsplash.com/photo-1492724441997-5dc865305da7?w=600"),
    ("Jazz Essentials", "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600"),
]

cols = st.columns(4)

for col, (name, img_url) in zip(cols, playlists):
    with col:
        st.image(img_url, use_container_width=True)
        st.markdown(
            f"<div style='text-align:center; margin-top:8px;'>{name}</div>",
            unsafe_allow_html=True,
        )

st.write("---")

# ---------------- YOUTUBE DOWNLOAD WITH MP3 CONVERSION ----------------
st.subheader("Batch Download from YouTube (MP3)")

urls_text = st.text_area("Paste YouTube Links (one per line, up to 10)")

API_BASE_URL = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:8000")

if st.button("Download MP3s"):
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

# Poll and Display Job Status
if "active_jobs" in st.session_state and st.session_state["active_jobs"]:
    st.write("### Download Status:")
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

                c1, c2 = st.columns([3, 1])
                c1.write(f"**{title}** - Status: `{status}`")

                if status == "completed":
                    full_url = f"{API_BASE_URL}{s_data['download_url']}"
                    metadata = s_data.get("metadata", {})

                    if not any(
                        song["url"] == full_url
                        for song in st.session_state.library
                    ):
                        st.session_state.library.append(
                            {
                                "url": full_url,
                                "title": title,
                                "metadata": metadata,
                            }
                        )
                        st.session_state.auto_refresh_trigger = True

                    c2.success("Ready in Player!")
                elif status == "failed":
                    c2.error("Failed")
                else:
                    c2.info("Processing...")
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
