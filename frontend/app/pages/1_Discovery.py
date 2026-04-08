import streamlit as st
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

st.set_page_config(page_title="Music Discovery", page_icon="🔍")

# ----- AUTHENTICATION LOCK -----
if not st.session_state.get('firebase_user'):
    st.warning("🔒 **Access Denied**: You must be logged in to access the Discovery & Recommendation portal.")
    st.info("Please navigate to the **Home** page and click the **Login** button to authenticate.")
    st.stop()  # Completely stops rendering the rest of the page
# -------------------------------

# API URL for Recommendation Service
RECOMMENDATION_API_URL = "http://localhost:8001"

st.title("🔍 Music Discovery & Search")
st.markdown("Search for specific songs or discover new ones based on your mood using Spotify's recommendation engine.")

tab1, tab2 = st.tabs(["Search by Name/Artist", "Discover by Mood/Genre"])

# --- TAB 1: Search ---
with tab1:
    st.subheader("Search Spotify")
    search_query = st.text_input("Enter a song name or artist (e.g., 'Blinding Lights')")
    search_limit = st.slider("Number of results", min_value=1, max_value=20, value=10)
    
    if st.button("Search"):
        if search_query:
            with st.spinner("Searching..."):
                try:
                    res = requests.get(f"{RECOMMENDATION_API_URL}/search", params={"q": search_query, "limit": search_limit})
                    if res.status_code == 200:
                        tracks = res.json()
                        if tracks:
                            st.success(f"Found {len(tracks)} results!")
                            for i, t in enumerate(tracks):
                                st.write(f"**{i+1}. {t['track_name']}** by {t['artist_name']}")
                        else:
                            st.warning("No tracks found.")
                    else:
                        st.error(f"Error: {res.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Recommendation Service. Is it running on port 8001?")
        else:
            st.warning("Please enter a search query.")


# --- TAB 2: Discover ---
with tab2:
    st.subheader("Discover New Music")
    st.markdown("Use Spotify's tuned parameters to find exactly what you're looking for.")
    
    # Need to fetch genres or hardcode a few common ones if backend fails
    genres_list = ["pop", "rock", "hip-hop", "acoustic", "dance", "electronic", "indie", "metal", "workout", "chill", "classical"]
    try:
        res = requests.get(f"{RECOMMENDATION_API_URL}/genres")
        if res.status_code == 200:
            genres_list = res.json().get("genres", genres_list)
    except:
        pass # Fallback to default list if service is down during page load
        
    with st.form("recommendation_form"):
        selected_genres = st.multiselect("Select up to 5 genres (Required)", options=genres_list, max_selections=5, default=["pop"])
        
        st.markdown("### Audio Features (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            use_valence = st.checkbox("Target Mood (Valence)", value=False)
            valence = st.slider("Mood (0.0 = Sad, 1.0 = Happy)", 0.0, 1.0, 0.5) if use_valence else None
            
            use_energy = st.checkbox("Target Energy", value=False)
            energy = st.slider("Energy", 0.0, 1.0, 0.7) if use_energy else None
            
        with col2:
            use_danceability = st.checkbox("Target Danceability", value=False)
            danceability = st.slider("Danceability", 0.0, 1.0, 0.6) if use_danceability else None
            
            use_tempo = st.checkbox("Target Tempo (BPM)", value=False)
            tempo = st.number_input("Tempo (e.g. 120)", min_value=40, max_value=200, value=120) if use_tempo else None
            
        rec_limit = st.slider("Number of recommendations", 1, 50, 10)
        
        submitted = st.form_submit_button("Get Recommendations")
        
        if submitted:
            if not selected_genres:
                st.error("Please select at least one genre.")
            else:
                payload = {
                    "seed_genres": selected_genres,
                    "limit": rec_limit
                }
                if use_valence: payload["target_valence"] = valence
                if use_energy: payload["target_energy"] = energy
                if use_danceability: payload["target_danceability"] = danceability
                if use_tempo: payload["target_tempo"] = tempo
                
                with st.spinner("Finding recommendations..."):
                    try:
                        res = requests.post(f"{RECOMMENDATION_API_URL}/recommend", json=payload)
                        if res.status_code == 200:
                            tracks = res.json()
                            if tracks:
                                st.success("Found these recommendations!")
                                for i, t in enumerate(tracks):
                                    st.write(f"**{i+1}. {t['track_name']}** by {t['artist_name']}")
                            else:
                                st.warning("No recommendations found for these settings.")
                        else:
                            st.error(f"Error: {res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to Recommendation Service. Is it running on port 8001?")

