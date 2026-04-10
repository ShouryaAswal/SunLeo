"""
SunLeo Design System — Dark Glassmorphic Theme
================================================
Shared CSS + component helpers. Every page should call inject_styles() once.
"""

import streamlit as st


# ──────────────────────── COLOUR TOKENS ────────────────────────
COLORS = {
    "bg":           "#08080f",
    "surface":      "rgba(255, 255, 255, 0.04)",
    "surface_hover": "rgba(255, 255, 255, 0.07)",
    "border":       "rgba(255, 255, 255, 0.08)",
    "border_hover": "rgba(124, 58, 237, 0.45)",
    "primary":      "#7c3aed",
    "primary_light": "#a78bfa",
    "gradient":     "linear-gradient(135deg, #7c3aed, #2563eb)",
    "success":      "#34d399",
    "danger":       "#f87171",
    "warning":      "#fbbf24",
    "text":         "#f1f5f9",
    "text_muted":   "#94a3b8",
    "text_dim":     "#64748b",
}


# ──────────────────────── FULL CSS ────────────────────────
_CSS = """
<style>
/* ─── Google Fonts ─── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─── Root variables ─── */
:root {
    --bg:           #08080f;
    --surface:      rgba(255, 255, 255, 0.04);
    --surface-hover: rgba(255, 255, 255, 0.07);
    --border:       rgba(255, 255, 255, 0.08);
    --border-hover: rgba(124, 58, 237, 0.45);
    --primary:      #7c3aed;
    --primary-light:#a78bfa;
    --gradient:     linear-gradient(135deg, #7c3aed, #2563eb);
    --success:      #34d399;
    --danger:       #f87171;
    --text:         #f1f5f9;
    --text-muted:   #94a3b8;
    --text-dim:     #64748b;
    --radius:       16px;
    --radius-sm:    10px;
    --blur:         16px;
}

/* ─── Global resets ─── */
.stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide the Streamlit deploy button and menu */
#MainMenu { visibility: hidden; }
header .stDecorator { display: none; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(124, 58, 237, 0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124, 58, 237, 0.5); }

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: rgba(8, 8, 15, 0.95) !important;
    border-right: 1px solid var(--border) !important;
    backdrop-filter: blur(20px);
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
}

section[data-testid="stSidebar"] .stRadio label span {
    color: var(--text) !important;
}

/* ─── Headings ─── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ─── Buttons ─── */
.stButton > button {
    background: var(--gradient) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 12px rgba(124, 58, 237, 0.25) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(124, 58, 237, 0.45) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Secondary / outline buttons (used via custom class) */
.stDownloadButton > button {
    background: transparent !important;
    border: 1.5px solid var(--primary) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--primary-light) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(124, 58, 237, 0.12) !important;
    transform: translateY(-1px) !important;
}

/* ─── Text inputs / text areas ─── */
div[data-baseweb="input"] > div {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    transition: border-color 0.2s ease !important;
}

div[data-baseweb="input"] > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15) !important;
}

div[data-baseweb="input"] input {
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-baseweb="textarea"] textarea {
    background-color: rgba(255, 255, 255, 0.03) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-baseweb="textarea"] textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15) !important;
}

/* ─── Select boxes ─── */
div[data-baseweb="select"] > div {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--surface);
    border-radius: var(--radius-sm);
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient) !important;
    color: white !important;
}

/* ─── Dividers ─── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ─── Metric cards ─── */
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
}

/* ─── Alert / info / warning boxes ─── */
.stAlert {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
}

/* ─── Slider ─── */
.stSlider > div > div > div {
    color: var(--text) !important;
}

/* ─── Spinner ─── */
.stSpinner > div {
    border-color: var(--primary) transparent transparent transparent !important;
}

/* ─── Expander ─── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ─── Forms ─── */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.5rem !important;
    backdrop-filter: blur(var(--blur));
}

/* ─── Toast / Balloons ─── */
.stToast {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
}

/* ─── Labels ─── */
label, .stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label, .stRadio label {
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

/* ─── Animations ─── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(124, 58, 237, 0.2); }
    50%      { box-shadow: 0 0 40px rgba(124, 58, 237, 0.4); }
}

@keyframes gradient-shift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ─── Reusable component classes ─── */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(124, 58, 237, 0.45);
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(124, 58, 237, 0.15);
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed, #2563eb, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 0.5rem;
    animation: fadeInUp 0.8s ease-out;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: #94a3b8;
    font-weight: 400;
    animation: fadeInUp 0.8s ease-out 0.15s both;
}

.accent-badge {
    display: inline-block;
    padding: 4px 14px;
    background: rgba(124, 58, 237, 0.15);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 20px;
    color: #a78bfa;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

.user-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 4px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 28px;
    font-size: 0.85rem;
    color: #f1f5f9;
}

.user-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    color: white;
}

.feature-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    overflow: hidden;
    font-family: 'Inter', sans-serif;
}

.feature-table thead th {
    background: rgba(124, 58, 237, 0.1);
    color: #a78bfa;
    font-weight: 600;
    padding: 14px 20px;
    text-align: left;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.feature-table tbody td {
    padding: 14px 20px;
    color: #f1f5f9;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    font-size: 0.92rem;
}

.feature-table tbody tr:last-child td {
    border-bottom: none;
}

.feature-table tbody tr:hover {
    background: rgba(124, 58, 237, 0.05);
}

.section-label {
    display: inline-block;
    padding: 3px 10px;
    background: rgba(124, 58, 237, 0.12);
    border-radius: 6px;
    color: #a78bfa;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}

.glow-border {
    animation: pulse-glow 3s ease-in-out infinite;
}

.download-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 20px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 2rem;
    animation: pulse-glow 4s ease-in-out infinite;
}

.playlist-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 0.8rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.playlist-card:hover {
    border-color: rgba(124, 58, 237, 0.45);
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.12);
}

.playlist-card img {
    width: 100%;
    border-radius: 10px;
    aspect-ratio: 1;
    object-fit: cover;
}

.playlist-card .title {
    margin-top: 10px;
    font-size: 0.92rem;
    font-weight: 600;
    color: #f1f5f9;
}

.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-processing {
    background: rgba(124, 58, 237, 0.15);
    color: #a78bfa;
}

.status-completed {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
}

.status-failed {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
}

/* ─── Responsive tweaks ─── */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem; }
    .hero-subtitle { font-size: 1rem; }
    .glass-card { padding: 1rem; }
    .download-card { padding: 1.2rem; }
}
</style>
"""


def inject_styles():
    """Inject the full SunLeo design system CSS. Call once per page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ──────────────────────── HTML COMPONENT BUILDERS ────────────────────────

def glass_card(content_html: str, extra_class: str = "") -> str:
    """Wrap content_html in a glassmorphic card div."""
    return f'<div class="glass-card {extra_class}">{content_html}</div>'


def section_label(text: str) -> str:
    """Small uppercase label above a section."""
    return f'<div class="section-label">{text}</div>'


def hero_block(title: str, subtitle: str) -> str:
    """Hero section with gradient title and muted subtitle."""
    return f"""
    <div style="margin-bottom: 1.5rem;">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """


def user_chip_html(display_name: str) -> str:
    """Small avatar + name chip for the header."""
    initial = display_name[0].upper() if display_name else "?"
    return f"""
    <div class="user-chip">
        <div class="user-avatar">{initial}</div>
        <span>{display_name}</span>
    </div>
    """


def feature_comparison_table() -> str:
    """Freemium feature comparison table HTML."""
    return """
    <table class="feature-table">
        <thead>
            <tr>
                <th>Feature</th>
                <th>Free</th>
                <th>Sun Leo Account</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>🔗 URL → MP3 Download</td>
                <td>✅</td>
                <td>✅</td>
            </tr>
            <tr>
                <td>🔍 Music Discovery</td>
                <td>❌</td>
                <td>✅</td>
            </tr>
            <tr>
                <td>🎵 AI Playlists</td>
                <td>❌</td>
                <td>✅</td>
            </tr>
            <tr>
                <td>🤖 Chatbot DJ</td>
                <td>❌</td>
                <td>✅</td>
            </tr>
            <tr>
                <td>📝 Feedback & Support</td>
                <td>✅</td>
                <td>✅</td>
            </tr>
        </tbody>
    </table>
    """


def status_pill(status: str) -> str:
    """Returns a small colored pill for job status."""
    cls = "status-processing"
    if status == "completed":
        cls = "status-completed"
    elif status == "failed":
        cls = "status-failed"
    return f'<span class="status-pill {cls}">{status}</span>'
