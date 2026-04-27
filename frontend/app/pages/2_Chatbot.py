"""
2_Chatbot.py — SunLeo DJ AI Chatbot page.
Requires the user to be signed in (Firebase auth).
Streams messages to the chatbot service on port 8002.
"""
import os
import requests
import streamlit as st

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SunLeo DJ — AI Chatbot",
    page_icon="🤖",
    layout="wide",
)

# ── styles ────────────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _styles import inject_styles
inject_styles()

CHATBOT_URL = os.getenv("CHATBOT_API_URL", "http://localhost:8002")

# ── auth gate ─────────────────────────────────────────────────────────────────
user = st.session_state.get("firebase_user")
if not user:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;">
        <div style="font-size:3rem;">🤖</div>
        <h2 style="color:#f1f5f9;margin:1rem 0 0.5rem;">SunLeo DJ</h2>
        <p style="color:#94a3b8;">Please sign in to chat with your AI music assistant.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

uid = user.get("localId", "anonymous")
display_name = user.get("displayName") or user.get("email", "User").split("@")[0]

# ── session state init ────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "bot",
            "content": (
                f"Hey {display_name}! 🎵 I'm **SunLeo DJ**, your AI music assistant.\n\n"
                "I can help you:\n"
                "- 🔍 **Search** for any song or artist\n"
                "- 🎭 **Discover** music by mood (chill, workout, sad, party…)\n"
                "- ⬇️ **Download** songs as MP3 — just say \"download #2\"\n"
                "- 📋 **Create & manage** playlists — say \"save these as Chill Vibes\"\n\n"
                "What are you in the mood for today?"
            ),
        }
    ]

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

if "chatbot_downloads" not in st.session_state:
    st.session_state.chatbot_downloads = []

# ── quick action prompts ──────────────────────────────────────────────────────
QUICK_ACTIONS = [
    ("🎭 Chill vibes", "Find me some chill relaxing music"),
    ("💪 Workout mix", "Give me high-energy workout songs"),
    ("😔 Feeling sad", "I need some sad but beautiful songs"),
    ("🎉 Party time", "Get me hype party music"),
    ("📚 Study focus", "I need focus music for studying"),
    ("📋 My Playlists", "Show me my playlists"),
]

# ── header ────────────────────────────────────────────────────────────────────
col_title, col_actions = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div style="margin-bottom:0.5rem;">
        <span style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#2563eb);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🤖 SunLeo DJ</span>
        <span style="margin-left:10px;padding:3px 10px;background:rgba(52,211,153,0.12);
            border:1px solid rgba(52,211,153,0.3);border-radius:12px;
            color:#34d399;font-size:0.75rem;font-weight:600;">LIVE</span>
    </div>
    <p style="color:#94a3b8;font-size:0.9rem;margin:0;">
        Powered by Groq Llama 3 &nbsp;·&nbsp; Playlists saved to Firestore
    </p>
    """, unsafe_allow_html=True)

with col_actions:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_messages = [st.session_state.chat_messages[0]]
            st.rerun()
    with btn_col2:
        # Show active download count
        active_count = len(st.session_state.chatbot_downloads)
        if active_count > 0:
            st.markdown(
                f"<div style='text-align:center;padding:6px 0;'>"
                f"<span style='padding:3px 10px;background:rgba(124,58,237,0.15);"
                f"border:1px solid rgba(124,58,237,0.3);border-radius:12px;"
                f"color:#a78bfa;font-size:0.75rem;font-weight:600;'>"
                f"📥 {active_count} download{'s' if active_count != 1 else ''}</span></div>",
                unsafe_allow_html=True,
            )

st.markdown("---")

# ── quick action buttons ──────────────────────────────────────────────────────
st.markdown("<p style='color:#64748b;font-size:0.8rem;font-weight:600;letter-spacing:0.08em;'>QUICK ACTIONS</p>", unsafe_allow_html=True)
qa_cols = st.columns(len(QUICK_ACTIONS))
triggered_message = None
for i, (label, prompt) in enumerate(QUICK_ACTIONS):
    with qa_cols[i]:
        if st.button(label, key=f"qa_{i}", use_container_width=True):
            triggered_message = prompt

# ── chat history ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_messages:
        if msg["role"] == "bot":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])

# ── message input ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    input_col, send_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "Message",
            placeholder="Ask me anything about music…",
            label_visibility="collapsed",
        )
    with send_col:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

# ── handle message send ───────────────────────────────────────────────────────
message_to_send = triggered_message or (user_input.strip() if submitted and user_input else None)

if message_to_send:
    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": message_to_send})

    # Call chatbot service
    with st.spinner("🎵 SunLeo DJ is thinking…"):
        try:
            resp = requests.post(
                f"{CHATBOT_URL}/chat",
                json={
                    "message": message_to_send,
                    "session_id": st.session_state.session_id,
                    "user_uid": uid,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            bot_reply = data.get("reply", "Sorry, I couldn't get a response.")

            # Track any download actions from the chatbot
            actions = data.get("actions", [])
            for action in actions:
                if action.get("type") == "download_queued" and action.get("job_id"):
                    st.session_state.chatbot_downloads.append({
                        "job_id": action["job_id"],
                        "track_name": action.get("track_name", ""),
                        "artist_name": action.get("artist_name", ""),
                        "title": action.get("track_name", "Unknown"),
                        "source": "chatbot",
                    })
                    # Also add to discovery_jobs for the Downloads page
                    if "discovery_jobs" not in st.session_state:
                        st.session_state.discovery_jobs = []
                    st.session_state.discovery_jobs.append({
                        "job_id": action["job_id"],
                        "title": action.get("track_name", "Unknown"),
                        "source": "chatbot",
                    })

        except requests.exceptions.ConnectionError:
            bot_reply = (
                "⚠️ **Chatbot service is not running.** "
                "Make sure the chatbot service is started on port 8002.\n\n"
                "`cd backend/chatbot_service && uvicorn app.main:app --port 8002`"
            )
        except Exception as exc:
            bot_reply = f"⚠️ Error: {exc}"

    st.session_state.chat_messages.append({"role": "bot", "content": bot_reply})
    st.rerun()

# ── sidebar info ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:1rem;">
        <div style="font-size:0.75rem;font-weight:700;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;">
            Tips
        </div>
    </div>
    """, unsafe_allow_html=True)

    tips = [
        "🎵 Try: *\"Find me lo-fi beats for studying\"*",
        "⬇️ Say *\"download #2\"* to download a specific song",
        "📋 Say *\"save these as 'Chill Vibes'\"* to create a playlist",
        "📖 Say *\"show my playlists\"* to see what you've saved",
        "🎭 Name a mood and I'll find the perfect tracks",
        "📥 Check the **Downloads** page for all your downloads",
    ]
    for tip in tips:
        st.markdown(f"<p style='color:#94a3b8;font-size:0.82rem;margin:0.4rem 0;'>{tip}</p>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.75rem;color:#64748b;">
        Session: <code>{st.session_state.session_id[:8]}…</code>
    </div>
    """, unsafe_allow_html=True)
