"""
4_Playlists.py — SunLeo Playlist Management page.
Lists the user's Firestore playlists, lets them create/delete/bulk-download.
"""
import os
import time
import requests
import streamlit as st

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="My Playlists — SunLeo",
    page_icon="📋",
    layout="wide",
)

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _styles import inject_styles
inject_styles()

CHATBOT_URL = os.getenv("CHATBOT_API_URL", "http://localhost:8002")
GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

# ── auth gate ────────────────────────────────────────────────────────────────
user = st.session_state.get("firebase_user")
if not user:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;">
        <div style="font-size:3rem;">📋</div>
        <h2 style="color:#f1f5f9;margin:1rem 0 0.5rem;">My Playlists</h2>
        <p style="color:#94a3b8;">Please sign in to view and manage your playlists.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

uid = user.get("localId", "anonymous")

# ── helpers ───────────────────────────────────────────────────────────────────

def fetch_playlists():
    try:
        r = requests.get(f"{CHATBOT_URL}/playlists/{uid}", timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return [], "⚠️ Chatbot service is offline. Start it on port 8002."
    except Exception as exc:
        return [], str(exc)


def create_playlist(name: str):
    r = requests.post(
        f"{CHATBOT_URL}/playlists/{uid}",
        json={"name": name, "tracks": []},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def delete_playlist(pid: str):
    r = requests.delete(f"{CHATBOT_URL}/playlists/{uid}/{pid}", timeout=10)
    r.raise_for_status()


def remove_track(pid: str, idx: int):
    r = requests.delete(f"{CHATBOT_URL}/playlists/{uid}/{pid}/tracks/{idx}", timeout=10)
    r.raise_for_status()


def bulk_download(pid: str):
    r = requests.post(f"{CHATBOT_URL}/playlists/{uid}/{pid}/download", timeout=30)
    r.raise_for_status()
    return r.json().get("jobs", [])


def poll_status(job_id: str):
    try:
        r = requests.get(f"{GATEWAY_URL}/status/{job_id}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "unknown"}

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1rem;">
    <span style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#2563eb);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">📋 My Playlists</span>
</div>
<p style="color:#94a3b8;font-size:0.9rem;margin:0 0 1.5rem;">
    Create playlists in the chatbot or here, then bulk-download all tracks as MP3.
</p>
""", unsafe_allow_html=True)

# ── create new playlist ───────────────────────────────────────────────────────
with st.expander("✨ Create New Playlist", expanded=False):
    with st.form("new_playlist_form"):
        name_input = st.text_input("Playlist name", placeholder='e.g. "Chill Vibes", "Workout Mix"')
        if st.form_submit_button("✨ Create Playlist"):
            if name_input.strip():
                try:
                    create_playlist(name_input.strip())
                    st.success(f"✅ Created **{name_input}**!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create playlist: {exc}")
            else:
                st.warning("Please enter a playlist name.")

st.markdown("---")

# ── load playlists ────────────────────────────────────────────────────────────
playlists, error = fetch_playlists()

if error:
    st.error(error)
    st.stop()

if not playlists:
    st.markdown("""
    <div style="text-align:center;padding:3rem;background:rgba(255,255,255,0.03);
         border:1px dashed rgba(255,255,255,0.1);border-radius:16px;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">🎵</div>
        <p style="color:#94a3b8;">No playlists yet.</p>
        <p style="color:#64748b;font-size:0.85rem;">
            Ask the <b>SunLeo DJ chatbot</b> to "save these as a playlist" or create one above.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── render each playlist ──────────────────────────────────────────────────────
for pl in playlists:
    pid = pl.get("id", "")
    pname = pl.get("name", "Unnamed")
    tracks = pl.get("tracks", [])
    track_count = len(tracks)

    with st.expander(f"🎵 **{pname}** — {track_count} track{'s' if track_count != 1 else ''}", expanded=False):
        # Track list
        if tracks:
            for i, track in enumerate(tracks):
                t_col, btn_col = st.columns([8, 1])
                with t_col:
                    st.markdown(
                        f"<div class='track-row'>"
                        f"<span style='color:#7c3aed;font-weight:600;'>{i+1}.</span>"
                        f"&nbsp;<b>{track.get('track_name','Unknown')}</b>"
                        f"&nbsp;<span style='color:#64748b;'>— {track.get('artist_name','')}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with btn_col:
                    if st.button("✕", key=f"rm_{pid}_{i}", help="Remove track"):
                        try:
                            remove_track(pid, i)
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
        else:
            st.markdown("<p style='color:#64748b;font-size:0.85rem;'>No tracks yet.</p>", unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Action buttons
        dl_col, del_col = st.columns(2)

        with dl_col:
            if st.button(f"⬇️ Download All ({track_count})", key=f"dl_{pid}", use_container_width=True):
                if not tracks:
                    st.warning("Playlist is empty — nothing to download.")
                else:
                    with st.spinner("Queuing downloads…"):
                        try:
                            jobs = bulk_download(pid)
                        except Exception as exc:
                            st.error(f"Failed to start downloads: {exc}")
                            jobs = []

                    if jobs:
                        st.success(f"✅ Queued {len(jobs)} tracks for download!")
                        # Poll progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        all_done = False
                        attempts = 0
                        while not all_done and attempts < 60:
                            done = 0
                            for job in jobs:
                                j_id = job.get("job_id")
                                if j_id:
                                    s = poll_status(j_id)
                                    if s.get("status") in ("completed", "failed"):
                                        done += 1
                                else:
                                    done += 1  # failed to queue; count as done
                            progress = done / len(jobs)
                            progress_bar.progress(progress)
                            status_text.markdown(f"<p style='color:#94a3b8;font-size:0.85rem;'>{done}/{len(jobs)} tracks ready</p>", unsafe_allow_html=True)
                            if done >= len(jobs):
                                all_done = True
                            else:
                                time.sleep(2)
                                attempts += 1

                        if all_done:
                            st.balloons()
                            st.success("🎉 All tracks downloaded! Check your downloads folder.")

        with del_col:
            if st.button(f"🗑️ Delete Playlist", key=f"del_{pid}", use_container_width=True):
                if st.session_state.get(f"confirm_del_{pid}"):
                    try:
                        delete_playlist(pid)
                        st.success(f"Deleted **{pname}**")
                        del st.session_state[f"confirm_del_{pid}"]
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                else:
                    st.session_state[f"confirm_del_{pid}"] = True
                    st.warning(f"Click **Delete Playlist** again to confirm deleting **{pname}**.")

st.markdown("---")
st.markdown(f"<p style='color:#64748b;font-size:0.8rem;text-align:center;'>{len(playlists)} playlist{'s' if len(playlists) != 1 else ''} · Stored in Firestore</p>", unsafe_allow_html=True)
