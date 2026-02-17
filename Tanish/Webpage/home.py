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
            st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")

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
col1, col2 = st.columns([8,1])

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
        st.markdown(f"<div style='text-align:center; margin-top:8px;'>{name}</div>", unsafe_allow_html=True)

st.write("---")

# ---------------- YOUTUBE DOWNLOAD WITH MP3 CONVERSION ----------------
st.subheader("Download from YouTube (MP3)")

youtube_url = st.text_input("Paste YouTube Link")

if st.button("Download MP3"):
    if youtube_url:
        with st.spinner("Downloading and converting to MP3..."):

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    title = info.get("title", "audio")
                    filename = f"{title}.mp3"

                st.success("MP3 Download Complete!")

                with open(filename, "rb") as f:
                    st.download_button(
                        label="Click to Download MP3",
                        data=f,
                        file_name=filename,
                        mime="audio/mpeg"
                    )

            except Exception as e:
                st.error(f"Error: {e}")

    else:
        st.warning("Please paste a valid YouTube link.")
