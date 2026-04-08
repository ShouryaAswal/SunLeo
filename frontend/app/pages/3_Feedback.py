import streamlit as st
import json
import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

st.set_page_config(page_title="Sun Leo - Feedback", page_icon="📝")

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

div[data-baseweb="textarea"] textarea {
    background-color: #111827 !important;
    color: white !important;
    border: 2px solid #1f6feb !important;
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- FEEDBACK CONFIG ----------------
# Set your Discord Webhook URL as an environment variable for notifications
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback_data.json")

def save_feedback_locally(feedback: dict):
    """Save feedback to a local JSON file as backup."""
    existing = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []
    
    existing.append(feedback)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(existing, f, indent=2)

def send_to_discord(feedback: dict) -> bool:
    """Send feedback as a Discord webhook embed message."""
    if not DISCORD_WEBHOOK_URL:
        return False
    
    # Color based on category
    color_map = {"Bug Report": 0xFF4444, "Feature Request": 0x44BB44, "General Feedback": 0x4488FF, "Other": 0xAAAAAA}

    embed = {
        "embeds": [{
            "title": f"📝 New Feedback: {feedback['category']}",
            "color": color_map.get(feedback['category'], 0x4488FF),
            "fields": [
                {"name": "👤 Name", "value": feedback['name'], "inline": True},
                {"name": "📧 Email", "value": feedback['email'], "inline": True},
                {"name": "📂 Category", "value": feedback['category'], "inline": True},
                {"name": "💬 Message", "value": feedback['message'][:1024], "inline": False},
            ],
            "footer": {"text": f"SunLeo Feedback | {feedback['timestamp']}"},
        }]
    }
    
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=10)
        return resp.status_code in (200, 204)
    except Exception:
        return False

# ---------------- PAGE CONTENT ----------------
st.title("📝 Feedback & Bug Reports")
st.markdown("Help us improve SunLeo! Report bugs, request features, or share your thoughts.")

st.write("---")

with st.form("feedback_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Your Name *", placeholder="John Doe")
    with col2:
        email = st.text_input("Email Address *", placeholder="john@example.com")
    
    category = st.selectbox(
        "Category *",
        ["Bug Report", "Feature Request", "General Feedback", "Other"]
    )
    
    message = st.text_area(
        "Your Message *",
        placeholder="Describe the issue or suggestion in detail...",
        height=150
    )
    
    submitted = st.form_submit_button("🚀 Submit Feedback", use_container_width=True)
    
    if submitted:
        # Validation
        errors = []
        if not name.strip():
            errors.append("Name is required.")
        if not email.strip() or "@" not in email:
            errors.append("A valid email address is required.")
        if not message.strip():
            errors.append("Please enter a message.")
        if len(message.strip()) < 10:
            errors.append("Message must be at least 10 characters.")
        
        if errors:
            for err in errors:
                st.error(err)
        else:
            feedback = {
                "name": name.strip(),
                "email": email.strip(),
                "category": category,
                "message": message.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Save locally as backup
            save_feedback_locally(feedback)
            
            # Try to send to Discord
            discord_sent = send_to_discord(feedback)
            
            st.success("✅ Thank you for your feedback! We'll review it shortly.")
            if discord_sent:
                st.info("📬 Notification sent to the development team.")
            st.balloons()
