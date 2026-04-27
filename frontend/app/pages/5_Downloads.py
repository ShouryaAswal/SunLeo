"""
5_Downloads.py — SunLeo Downloads Dashboard.
Shows all session downloads (from Discovery, Chatbot, and Playlist bulk downloads)
with real-time status polling, play/save buttons for completed files.
"""
import os
import time
import requests
import streamlit as st

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Downloads — SunLeo",
    page_icon="⬇️",
    layout="wide",
)

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _styles import inject_styles, section_label
inject_styles()

GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

# ── auth gate ────────────────────────────────────────────────────────────────
user = st.session_state.get("firebase_user")
if not user:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;">
        <div style="font-size:3rem;">⬇️</div>
        <h2 style="color:#f1f5f9;margin:1rem 0 0.5rem;">Downloads</h2>
        <p style="color:#94a3b8;">Please sign in to view your downloads.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1rem;">
    <span style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#2563eb);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">⬇️ Downloads</span>
</div>
<p style="color:#94a3b8;font-size:0.9rem;margin:0 0 1.5rem;">
    All your session downloads in one place. Files are available for 1 hour after completion.
</p>
""", unsafe_allow_html=True)

# ── collect all download jobs from session state ──────────────────────────────
discovery_jobs = st.session_state.get("discovery_jobs", [])
chatbot_downloads = st.session_state.get("chatbot_downloads", [])

all_jobs = []
# Add discovery/playlist jobs
for job in discovery_jobs:
    if job.get("job_id"):
        j = dict(job)
        j.setdefault("source", "discovery")
        all_jobs.append(j)

# Add chatbot jobs
for job in chatbot_downloads:
    if job.get("job_id"):
        j = dict(job)
        j["source"] = "chatbot"
        all_jobs.append(j)

# Dedupe by job_id
seen_ids = set()
unique_jobs = []
for j in all_jobs:
    jid = j.get("job_id")
    if jid and jid not in seen_ids:
        seen_ids.add(jid)
        unique_jobs.append(j)

if not unique_jobs:
    st.markdown("""
    <div style="text-align:center;padding:3rem;background:rgba(255,255,255,0.03);
         border:1px dashed rgba(255,255,255,0.1);border-radius:16px;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
        <p style="color:#94a3b8;">No downloads yet this session.</p>
        <p style="color:#64748b;font-size:0.85rem;">
            Download songs from <b>Discovery</b>, the <b>Chatbot</b>, or <b>Playlists</b> to see them here.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── poll status and render ────────────────────────────────────────────────────
st.markdown("---")

# Group by source
sources = {"home": "🏠 From Home Page", "discovery": "🔍 From Discovery", "chatbot": "🤖 From Chatbot", "playlist": "📋 From Playlists"}
grouped: dict[str, list] = {}
for j in unique_jobs:
    src = j.get("source", "discovery")
    grouped.setdefault(src, []).append(j)

any_pending = False

for source_key, label in sources.items():
    jobs_in_group = grouped.get(source_key, [])
    if not jobs_in_group:
        continue

    st.markdown(f"### {label}")

    for job in jobs_in_group:
        job_id = job.get("job_id", "")
        title = job.get("title") or job.get("track_name") or "Unknown"

        try:
            status_resp = requests.get(f"{GATEWAY_URL}/status/{job_id}", timeout=5)
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                status = s_data.get("status", "unknown")
                actual_title = s_data.get("title") or title
                metadata = s_data.get("metadata") or {}
            else:
                s_data = {}
                status = "unknown"
                actual_title = title
                metadata = {}
        except Exception:
            s_data = {}
            status = "unknown"
            actual_title = title
            metadata = {}

        # Status badge colors
        if status == "completed":
            color = "#34d399"
            icon = "✅"
        elif status == "failed":
            color = "#f87171"
            icon = "❌"
        elif status in ("queued", "running"):
            color = "#a78bfa"
            icon = "⏳"
            any_pending = True
        else:
            color = "#64748b"
            icon = "❓"

        # Status row
        with st.container():
            cols = st.columns([0.5, 4, 1.5, 1.5])

            with cols[0]:
                st.markdown(f"<div style='font-size:1.3rem;text-align:center;padding-top:8px;'>{icon}</div>",
                            unsafe_allow_html=True)

            with cols[1]:
                st.markdown(
                    f"<div style='padding-top:4px;'>"
                    f"<div style='font-size:0.95rem;font-weight:600;color:#f1f5f9;'>{actual_title}</div>"
                    f"<div style='font-size:0.8rem;color:#64748b;'>"
                    f"{'👤 ' + metadata.get('uploader', '') + ' · ' if metadata.get('uploader') else ''}"
                    f"{'⏱ ' + str(metadata.get('duration', 0) // 60) + ':' + str(metadata.get('duration', 0) % 60).zfill(2) if metadata.get('duration') else ''}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

            with cols[2]:
                st.markdown(
                    f"<div style='padding-top:8px;'>"
                    f"<span style='padding:3px 10px;border-radius:20px;font-size:0.75rem;"
                    f"font-weight:600;background:rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))},0.15);"
                    f"color:{color};text-transform:uppercase;'>{status}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with cols[3]:
                if status == "completed":
                    download_url = s_data.get("download_url", "")
                    if download_url:
                        full_url = f"{GATEWAY_URL}{download_url}"
                        try:
                            audio_resp = requests.get(full_url, timeout=10)
                            if audio_resp.status_code == 200:
                                st.download_button(
                                    "📥 Save",
                                    data=audio_resp.content,
                                    file_name=f"{actual_title}.mp3",
                                    mime="audio/mpeg",
                                    key=f"save_{job_id}",
                                )
                        except Exception:
                            st.caption("⚠️ File unavailable")

                elif status == "failed":
                    err = s_data.get("error", "") if 's_data' in dir() else ""
                    if err:
                        st.caption(f"⚠️ {err[:50]}")

        # Audio player for completed downloads
        if status == "completed":
            download_url = s_data.get("download_url", "")
            if download_url:
                full_url = f"{GATEWAY_URL}{download_url}"
                try:
                    audio_resp = requests.get(full_url, timeout=10)
                    if audio_resp.status_code == 200:
                        st.audio(audio_resp.content, format="audio/mp3")
                except Exception:
                    pass

        st.markdown("<hr style='margin:0.3rem 0;border-color:rgba(255,255,255,0.04);'>",
                    unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

# ── summary footer ────────────────────────────────────────────────────────────
st.markdown("---")
total = len(unique_jobs)
st.markdown(
    f"<p style='color:#64748b;font-size:0.8rem;text-align:center;'>"
    f"{total} download{'s' if total != 1 else ''} this session · "
    f"Files auto-delete after 1 hour</p>",
    unsafe_allow_html=True,
)

# ── auto-refresh while pending ────────────────────────────────────────────────
if any_pending:
    time.sleep(3)
    st.rerun()
