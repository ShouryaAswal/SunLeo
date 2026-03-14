import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="Sun Leo", layout="wide")

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🎵 Sun Leo")

    if st.session_state.logged_in:
        st.success("Logged in")

        feature = st.radio(
            "Features",
            ["Player", "Chatbot", "Create Playlist"]
        )

        if feature == "Player":
            st.subheader("Music Player")

            if "last_downloaded_url" in st.session_state:
                file_url = st.session_state["last_downloaded_url"]
                st.audio(file_url)
            elif "last_downloaded" in st.session_state:
                # legacy local file logic
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

# ---------------- HEADER ----------------
col1, col2 = st.columns([8, 1])

with col1:
    st.markdown("<h1>Welcome to Sun Leo</h1>", unsafe_allow_html=True)
    st.markdown("Find the melody that moves you")

with col2:
    if not st.session_state.logged_in:
        if st.button("Login"):
            st.session_state.logged_in = True
            st.rerun()
    else:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

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
            unsafe_allow_html=True
        )

st.write("---")

# ---------------- YOUTUBE DOWNLOAD WITH MP3 CONVERSION ----------------
st.subheader("Batch Download from YouTube (MP3)")

urls_text = st.text_area("Paste YouTube Links (one per line, up to 10)")

API_BASE_URL = os.getenv("API_GATEWAY_URL", "http://127.0.0.1:8000")

if st.button("Download MP3s"):
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
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
                    timeout=10
                )
                if response.status_code != 200:
                    st.error(f"Error from service: {response.text}")
                else:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    st.success(f"Successfully queued {len(jobs)} jobs!")
                    
                    # Store jobs in session state to poll them
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
        
        # Poll status
        try:
            status_resp = requests.get(f"{API_BASE_URL}/status/{job_id}", timeout=5)
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                status = s_data["status"]
                title = s_data.get("title") or job.get("url")
                
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{title}** - Status: `{status}`")
                
                if status == "completed":
                    # Update feature player state if it's the first completed
                    if "last_downloaded_url" not in st.session_state:
                         st.session_state["last_downloaded_url"] = f"{API_BASE_URL}{s_data['download_url']}"
                         
                    col2.markdown(f"[Download MP3]({API_BASE_URL}{s_data['download_url']})")
                elif status == "failed":
                    col2.error("Failed")
                else:
                    col2.info("Processing...")
                    all_completed = False
            else:
                st.error(f"Failed to get status for {job_id}")
        except Exception:
            st.error(f"Cannot reach backend to check {job_id}")
            
    if not all_completed:
        time.sleep(3)
        st.rerun()
