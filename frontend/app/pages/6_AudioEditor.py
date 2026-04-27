"""
6_AudioEditor.py — SunLeo Audio Editor.
Trim, apply effects, and export downloaded tracks in multiple formats.
"""
import os
import io
import requests
import streamlit as st

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Audio Editor — SunLeo", page_icon="🎛️", layout="wide")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _styles import inject_styles, section_label
inject_styles()

GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.editor-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.editor-card h4 {
    margin: 0 0 1rem 0;
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 700;
}
.effect-label {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-bottom: 0.2rem;
}
.format-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.format-table td {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #cbd5e1;
}
.format-table tr:hover {
    background: rgba(124,58,237,0.08);
}
.format-table .size {
    text-align: right;
    color: #a78bfa;
    font-weight: 600;
}
.duration-badge {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(124,58,237,0.15);
    border-radius: 20px;
    font-size: 0.85rem;
    color: #a78bfa;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Auth gate ─────────────────────────────────────────────────────────────────
user = st.session_state.get("firebase_user")
if not user:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;">
        <div style="font-size:3rem;">🎛️</div>
        <h2 style="color:#f1f5f9;margin:1rem 0 0.5rem;">Audio Editor</h2>
        <p style="color:#94a3b8;">Please sign in to use the audio editor.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.5rem;">
    <span style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#2563eb);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎛️ Audio Editor</span>
</div>
<p style="color:#94a3b8;font-size:0.9rem;margin:0 0 1.5rem;">
    Trim, add effects, and export your downloaded tracks in any format.
</p>
""", unsafe_allow_html=True)

# ── Collect completed downloads ──────────────────────────────────────────────
discovery_jobs = st.session_state.get("discovery_jobs", [])
chatbot_downloads = st.session_state.get("chatbot_downloads", [])

completed_tracks = []
for job in discovery_jobs + chatbot_downloads:
    job_id = job.get("job_id", "")
    if not job_id:
        continue
    try:
        resp = requests.get(f"{GATEWAY_URL}/status/{job_id}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "completed" and data.get("download_url"):
                completed_tracks.append({
                    "job_id": job_id,
                    "title": data.get("title") or job.get("track_name") or job.get("title") or "Unknown",
                    "download_url": data["download_url"],
                    "duration": (data.get("metadata") or {}).get("duration", 0),
                    "uploader": (data.get("metadata") or {}).get("uploader", ""),
                })
    except Exception:
        pass

# Check for pre-selected track from Downloads page
preselected_job = st.session_state.pop("editor_selected_job", None)

if not completed_tracks:
    st.markdown("""
    <div style="text-align:center;padding:3rem;background:rgba(255,255,255,0.03);
         border:1px dashed rgba(255,255,255,0.1);border-radius:16px;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">🎵</div>
        <p style="color:#94a3b8;">No completed downloads to edit.</p>
        <p style="color:#64748b;font-size:0.85rem;">
            Download songs from <b>Discovery</b>, the <b>Chatbot</b>, or <b>Playlists</b> first.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Track Selector ───────────────────────────────────────────────────────────
track_names = [t["title"] for t in completed_tracks]
default_idx = 0
if preselected_job:
    for i, t in enumerate(completed_tracks):
        if t["job_id"] == preselected_job:
            default_idx = i
            break

selected_idx = st.selectbox(
    "📂 Select a track to edit",
    range(len(track_names)),
    format_func=lambda i: track_names[i],
    index=default_idx,
    key="editor_track_select",
)
track = completed_tracks[selected_idx]

# Fetch audio file
@st.cache_data(ttl=300, show_spinner="Loading audio...")
def fetch_audio(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

try:
    audio_bytes = fetch_audio(f"{GATEWAY_URL}{track['download_url']}")
except Exception as e:
    st.error(f"Could not load audio: {e}")
    st.stop()

# Show original player
dur_sec = track.get("duration", 0)
dur_str = f"{dur_sec // 60}:{dur_sec % 60:02d}" if dur_sec else "unknown"

col_info, col_dur = st.columns([4, 1])
with col_info:
    st.markdown(f"**Now editing:** {track['title']}")
    if track.get("uploader"):
        st.caption(f"👤 {track['uploader']}")
with col_dur:
    st.markdown(f"<span class='duration-badge'>⏱ {dur_str}</span>", unsafe_allow_html=True)

st.audio(audio_bytes, format="audio/mp3")
st.markdown("---")

# ── TRIM SECTION ─────────────────────────────────────────────────────────────
st.markdown("<div class='editor-card'><h4>✂️ Trim & Cut</h4>", unsafe_allow_html=True)

max_dur = max(dur_sec, 1)
trim_col1, trim_col2 = st.columns(2)

with trim_col1:
    trim_start = st.slider(
        "Start time (seconds)",
        min_value=0.0,
        max_value=float(max_dur),
        value=0.0,
        step=0.5,
        key="trim_start",
    )
with trim_col2:
    trim_end = st.slider(
        "End time (seconds)",
        min_value=0.0,
        max_value=float(max_dur),
        value=float(max_dur),
        step=0.5,
        key="trim_end",
    )

# Validate
if trim_start >= trim_end:
    st.warning("⚠️ Start time must be before end time.")

sel_dur = max(0, trim_end - trim_start)
st.caption(f"📐 Selected: {int(trim_start // 60)}:{int(trim_start % 60):02d} — "
           f"{int(trim_end // 60)}:{int(trim_end % 60):02d} "
           f"({sel_dur:.1f}s)")

st.markdown("</div>", unsafe_allow_html=True)

# ── EFFECTS SECTION ──────────────────────────────────────────────────────────
st.markdown("<div class='editor-card'><h4>🎚️ Effects</h4>", unsafe_allow_html=True)

eff_row1 = st.columns(3)
eff_row2 = st.columns(3)

with eff_row1[0]:
    st.markdown("<div class='effect-label'>Fade In</div>", unsafe_allow_html=True)
    fade_in = st.slider("Fade In (seconds)", 0.0, 10.0, 0.0, 0.5, key="fade_in",
                         label_visibility="collapsed")
    st.caption(f"{fade_in}s")

with eff_row1[1]:
    st.markdown("<div class='effect-label'>Fade Out</div>", unsafe_allow_html=True)
    fade_out = st.slider("Fade Out (seconds)", 0.0, 10.0, 0.0, 0.5, key="fade_out",
                          label_visibility="collapsed")
    st.caption(f"{fade_out}s")

with eff_row1[2]:
    st.markdown("<div class='effect-label'>Volume (dB)</div>", unsafe_allow_html=True)
    volume_db = st.slider("Volume", -12.0, 12.0, 0.0, 0.5, key="volume",
                           label_visibility="collapsed")
    st.caption(f"{volume_db:+.1f} dB")

with eff_row2[0]:
    st.markdown("<div class='effect-label'>Bass Boost (dB)</div>", unsafe_allow_html=True)
    bass_db = st.slider("Bass", -12.0, 12.0, 0.0, 0.5, key="bass",
                         label_visibility="collapsed")
    st.caption(f"{bass_db:+.1f} dB")

with eff_row2[1]:
    st.markdown("<div class='effect-label'>Treble Boost (dB)</div>", unsafe_allow_html=True)
    treble_db = st.slider("Treble", -12.0, 12.0, 0.0, 0.5, key="treble",
                           label_visibility="collapsed")
    st.caption(f"{treble_db:+.1f} dB")

with eff_row2[2]:
    st.markdown("<div class='effect-label'>Speed</div>", unsafe_allow_html=True)
    speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.05, key="speed",
                       label_visibility="collapsed")
    label = "Normal" if abs(speed - 1.0) < 0.01 else f"{speed:.2f}×"
    st.caption(label)

st.markdown("</div>", unsafe_allow_html=True)

# ── EXPORT SECTION ───────────────────────────────────────────────────────────
st.markdown("<div class='editor-card'><h4>📤 Export</h4>", unsafe_allow_html=True)

FORMAT_OPTIONS = {
    "MP3 — 128 kbps": ("mp3", "128"),
    "MP3 — 192 kbps (recommended)": ("mp3", "192"),
    "MP3 — 320 kbps (high quality)": ("mp3", "320"),
    "WAV (lossless)": ("wav", "lossless"),
    "OGG — 128 kbps": ("ogg", "128"),
    "OGG — 192 kbps": ("ogg", "192"),
    "FLAC (lossless)": ("flac", "lossless"),
    "AAC — 192 kbps": ("aac", "192"),
}

exp_col1, exp_col2 = st.columns([2, 3])

with exp_col1:
    format_choice = st.selectbox(
        "Output format",
        list(FORMAT_OPTIONS.keys()),
        index=1,  # default to MP3 192
        key="export_format",
    )
    out_format, out_quality = FORMAT_OPTIONS[format_choice]

with exp_col2:
    # Show estimated sizes
    st.markdown("<div class='effect-label'>Estimated file sizes</div>", unsafe_allow_html=True)

    # Calculate estimates locally (fast, no API call needed)
    effective_dur = sel_dur if sel_dur > 0 else dur_sec
    if speed > 0:
        effective_dur = effective_dur / speed

    size_estimates = []
    for label_str, (fmt, qual) in FORMAT_OPTIONS.items():
        if qual == "lossless":
            if fmt == "wav":
                est_bytes = int(effective_dur * 44100 * 2 * 2) + 44  # 16-bit stereo
            else:  # flac
                est_bytes = int(effective_dur * 44100 * 2 * 2 * 0.6)
        else:
            est_bytes = int(effective_dur * int(qual) * 1000 / 8)

        if est_bytes < 1024 * 1024:
            size_str = f"{est_bytes / 1024:.0f} KB"
        else:
            size_str = f"{est_bytes / (1024 * 1024):.1f} MB"

        marker = " ← selected" if label_str == format_choice else ""
        size_estimates.append(f"<tr><td>{label_str}</td><td class='size'>{size_str}{marker}</td></tr>")

    table_html = "<table class='format-table'>" + "".join(size_estimates) + "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Action buttons ───────────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])


def _build_edit_form_data():
    """Build the multipart form data for the /audio/edit endpoint."""
    return {
        "trim_start_ms": str(int(trim_start * 1000)),
        "trim_end_ms": str(int(trim_end * 1000)),
        "fade_in_ms": str(int(fade_in * 1000)),
        "fade_out_ms": str(int(fade_out * 1000)),
        "bass_boost_db": str(bass_db),
        "treble_boost_db": str(treble_db),
        "volume_change_db": str(volume_db),
        "speed_factor": str(speed),
        "output_format": out_format,
        "output_quality": out_quality,
    }


with btn_col1:
    if st.button("🎵 Preview", key="preview_btn", type="secondary", use_container_width=True):
        if trim_start >= trim_end and dur_sec > 0:
            st.error("Fix trim range first!")
        else:
            with st.spinner("Processing preview..."):
                try:
                    form_data = _build_edit_form_data()
                    # Preview always as mp3 for browser compatibility
                    form_data["output_format"] = "mp3"
                    form_data["output_quality"] = "128"

                    resp = requests.post(
                        f"{GATEWAY_URL}/audio/edit",
                        files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                        data=form_data,
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        st.session_state["preview_audio"] = resp.content
                        st.success("✅ Preview ready!")
                    else:
                        st.error(f"Processing failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

with btn_col2:
    if st.button("📥 Export", key="export_btn", type="primary", use_container_width=True):
        if trim_start >= trim_end and dur_sec > 0:
            st.error("Fix trim range first!")
        else:
            with st.spinner(f"Exporting as {out_format.upper()}..."):
                try:
                    form_data = _build_edit_form_data()
                    resp = requests.post(
                        f"{GATEWAY_URL}/audio/edit",
                        files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                        data=form_data,
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        st.session_state["export_audio"] = resp.content
                        st.session_state["export_ext"] = out_format
                        st.success(f"✅ Export ready! ({len(resp.content) / (1024*1024):.1f} MB)")
                    else:
                        st.error(f"Export failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── Preview player ───────────────────────────────────────────────────────────
if "preview_audio" in st.session_state and st.session_state["preview_audio"]:
    st.markdown("---")
    st.markdown("#### 🔊 Preview")
    st.audio(st.session_state["preview_audio"], format="audio/mp3")

# ── Download button ──────────────────────────────────────────────────────────
if "export_audio" in st.session_state and st.session_state["export_audio"]:
    ext = st.session_state.get("export_ext", "mp3")
    mime_map = {
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
        "flac": "audio/flac", "aac": "audio/aac",
    }
    st.markdown("---")
    st.download_button(
        label=f"💾 Download {track['title']}.{ext}",
        data=st.session_state["export_audio"],
        file_name=f"{track['title']}.{ext}",
        mime=mime_map.get(ext, "audio/mpeg"),
        key="final_download",
        type="primary",
        use_container_width=True,
    )
