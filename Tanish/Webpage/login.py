import streamlit as st

st.set_page_config(page_title="Sun Leo - Login", layout="wide")

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

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.markdown("<div class='small-link'>Forgot Password?</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-link'>Create an Account</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.button("Login")
