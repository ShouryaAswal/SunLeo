import streamlit as st
import os
import requests
from datetime import datetime
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

# Ensure we can import from backend
sys.path.insert(0, str(_PROJECT_ROOT))
from backend.database.connection import get_db, init_db
from backend.database.dal import FeedbackDAL

st.set_page_config(page_title="Sun Leo — Feedback", page_icon="📝", layout="wide")

# Apply shared design system
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from _styles import inject_styles, section_label
inject_styles()

# ---------------- FEEDBACK CONFIG ----------------
EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY", "")


async def _save_feedback_dal(name: str, email: str, category: str, message: str):
    """Save feedback to the SQLite database via DAL."""
    await init_db()
    async with get_db() as db:
        dal = FeedbackDAL(db)
        await dal.save_feedback(name, email, category, message)


def save_feedback_db(name: str, email: str, category: str, message: str):
    """Synchronous wrapper to run the async DAL function."""
    asyncio.run(_save_feedback_dal(name, email, category, message))


def send_via_emailjs(name: str, email: str, category: str, message: str, rating: int) -> bool:
    """Send feedback via EmailJS REST API."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        st.warning("EmailJS environment variables are missing! Check your .env file.")
        return False
        
    url = "https://api.emailjs.com/api/v1.0/email/send"
    
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "template_params": {
            "from_name": name,
            "reply_to": email,
            "category": category,
            "rating": str(rating),
            "message": message,
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            st.error(f"EmailJS error: {resp.text}")
            return False
    except Exception as e:
        st.error(f"Failed to connect to EmailJS: {e}")
        return False


# ---------------- PAGE CONTENT ----------------
st.markdown(
    "<div style='margin-bottom:0.5rem;'>"
    "<div class='hero-title' style='font-size:2.2rem;'>📝 Feedback & Support</div>"
    "<div class='hero-subtitle'>Help us improve SunLeo! Report bugs, request features, or share your thoughts.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)


with st.form("feedback_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Your Name *", placeholder="John Doe")
    with col2:
        email = st.text_input("Email Address *", placeholder="john@example.com")
    
    col3, col4 = st.columns(2)
    with col3:
        category = st.selectbox(
            "Category *",
            ["Bug Report", "Feature Request", "General Feedback", "Other"]
        )
    with col4:
        rating = st.slider("Rate your experience (1=Poor, 5=Excellent)", min_value=1, max_value=5, value=5)
    
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
            final_message = f"[Rating: {rating}/5] {message.strip()}"
            
            # Save to SQLite DB
            save_feedback_db(name.strip(), email.strip(), category, final_message)
            
            # Send EmailJS
            email_sent = send_via_emailjs(name.strip(), email.strip(), category, message.strip(), rating)
            
            st.success("✅ Thank you for your feedback! We'll review it shortly.")
            if email_sent:
                st.info("📬 Email notification sent to the development team.")
            st.balloons()
