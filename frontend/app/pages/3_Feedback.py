"""
3_Feedback.py — SunLeo Feedback & Support page.
Sends feedback directly via the EmailJS REST API.
No database dependency — pure HTTP, zero extra packages.
"""
import os
import sys
import requests
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── env ────────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SunLeo — Feedback", page_icon="📝", layout="wide")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from _styles import inject_styles
inject_styles()

# ── EmailJS config ─────────────────────────────────────────────────────────────
EMAILJS_SERVICE_ID  = os.getenv("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY  = os.getenv("EMAILJS_PUBLIC_KEY", "")


def send_via_emailjs(name: str, email: str, category: str, message: str, rating: int) -> bool:
    """Send feedback to the developer via the EmailJS REST API."""
    if not EMAILJS_SERVICE_ID or not EMAILJS_TEMPLATE_ID or not EMAILJS_PUBLIC_KEY:
        st.warning(
            "⚠️ **EmailJS is not fully configured.**  \n"
            "Set `EMAILJS_SERVICE_ID`, `EMAILJS_TEMPLATE_ID`, and `EMAILJS_PUBLIC_KEY` in your `.env` file.",
            icon="⚙️",
        )
        return False

    payload = {
        "service_id":  EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id":     EMAILJS_PUBLIC_KEY,
        "template_params": {
            "from_name":  name,
            "reply_to":   email,
            "category":   category,
            "rating":     f"{rating}/5",
            "message":    message,
        },
    }

    try:
        resp = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        st.error(f"EmailJS error {resp.status_code}: {resp.text}")
        return False
    except requests.exceptions.Timeout:
        st.error("⏱️ EmailJS request timed out. Please try again.")
        return False
    except Exception as exc:
        st.error(f"🔌 Failed to reach EmailJS: {exc}")
        return False


# ── page header ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='margin-bottom:0.5rem;'>"
    "<div class='hero-title' style='font-size:2.2rem;'>📝 Feedback &amp; Support</div>"
    "<div class='hero-subtitle'>Help us improve SunLeo — report bugs, request features, or just say hi!</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# ── feedback form ──────────────────────────────────────────────────────────────
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
            ["Bug Report", "Feature Request", "General Feedback", "Other"],
        )
    with col4:
        rating = st.slider(
            "Rate your experience  (1 = Poor · 5 = Excellent)",
            min_value=1, max_value=5, value=5,
        )

    message = st.text_area(
        "Your Message *",
        placeholder="Describe the issue or suggestion in detail…",
        height=160,
    )

    submitted = st.form_submit_button("🚀 Submit Feedback", use_container_width=True)

    if submitted:
        errors: list[str] = []
        if not name.strip():
            errors.append("Name is required.")
        if not email.strip() or "@" not in email:
            errors.append("A valid email address is required.")
        if not message.strip():
            errors.append("Please enter a message.")
        elif len(message.strip()) < 10:
            errors.append("Message must be at least 10 characters.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            stars = "⭐" * rating
            full_message = (
                f"**Category:** {category}\n"
                f"**Rating:** {stars} ({rating}/5)\n\n"
                f"{message.strip()}"
            )

            with st.spinner("Sending your feedback…"):
                sent = send_via_emailjs(
                    name.strip(), email.strip(),
                    category, full_message, rating,
                )

            if sent:
                st.success("✅ Thank you for your feedback! We'll review it shortly.")
                st.info("📬 Your message has been sent to the development team.")
                st.balloons()
            else:
                # Store locally as a fallback so feedback isn't lost
                st.warning(
                    "Your feedback couldn't be emailed right now, but it has been recorded below. "
                    "Please screenshot this and send it manually if needed.",
                )
                st.code(
                    f"Name: {name.strip()}\n"
                    f"Email: {email.strip()}\n"
                    f"Category: {category}\n"
                    f"Rating: {rating}/5\n\n"
                    f"{message.strip()}",
                    language="text",
                )
