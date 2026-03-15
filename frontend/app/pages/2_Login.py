import streamlit as st
import os
import sys

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from streamlit_google_auth import Authenticate
from auth_utils import write_client_secrets

st.set_page_config(page_title="Sun Leo - Login", layout="wide")

# Target the google_secret.json in the parent app directory
SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google_secret.json")

# In production, these should be securely injected via .env not typed into the UI, 
# but for local testing, this is the easiest way to generate the required file.
if not os.path.exists(SECRET_FILE):
    st.warning("Google OAuth Secrets missing. Please configure them below.")
    with st.form("secret_form"):
        st.write("First time setup: Enter your Google OAuth credentials")
        client_id_input = st.text_input("Client ID")
        client_secret_input = st.text_input("Client Secret", type="password")
        if st.form_submit_button("Save Credentials"):
            write_client_secrets(client_id_input, client_secret_input)
            st.success("Secrets saved! Refresh the page.")
            st.stop()
else:
    # Initialize the Google Authenticator
    authenticator = Authenticate(
        secret_credentials_path=SECRET_FILE,
        cookie_name='sunleo_cookie',
        cookie_key='sunleo_key',
        redirect_uri='http://localhost:8501',
    )
    
    # Needs to catch the callback on load
    authenticator.check_authentification()


# ---- GLOBAL DARK STYLE ----
st.markdown("""
<style>

/* Remove default padding */
.block-container {
    padding-top: 2rem;
}

/* Dark background */
.stApp {
    background: radial-gradient(circle at top, #0f1626, #0b0f19 70%);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

/* Input styling */
div[data-baseweb="input"] > div {
    background-color: #111827 !important;
    border: 2px solid #1f6feb !important;
    border-radius: 12px !important;
    box-shadow: 0 0 10px rgba(31,111,235,0.3);
}

div[data-baseweb="input"] input {
    color: white !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(90deg, #1f6feb, #3b82f6);
    border-radius: 10px;
    height: 45px;
    width: 100%;
    font-size: 18px;
    font-weight: 500;
    border: none;
    color: white;
    box-shadow: 0 0 15px rgba(31,111,235,0.5);
    transition: 0.3s;
}

.stButton > button:hover {
    box-shadow: 0 0 25px rgba(31,111,235,0.9);
    transform: scale(1.02);
}

.small-link {
    color: #9aa4b2;
    font-size: 14px;
    cursor: pointer;
}

.small-link:hover {
    color: white;
}

</style>
""", unsafe_allow_html=True)

# ---- CENTERED LAYOUT ----
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Login to Sun Leo</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.get('connected'):
        st.info("Please log in using your Google account to access the downloader.")
        
        # The library provides a built-in login button
        authenticator.login()
        
    else:
        st.success(f"Welcome back, {st.session_state['user_info'].get('name', 'User')}!")
        
        st.write("Email:", st.session_state['user_info'].get('email'))
        
        if st.session_state['user_info'].get('picture'):
            st.image(st.session_state['user_info'].get('picture'), width=100)
            
        st.markdown("### You are authenticated! You can now use the app.")
        if st.button("Go to Downloader & Player"):
            st.switch_page("home.py")
            
        authenticator.logout()
        

