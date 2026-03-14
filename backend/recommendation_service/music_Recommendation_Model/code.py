
# Language-Aware Music Recommendation System
# Case-Insensitive Input
# Hindi → Hindi | English → English
# No Duplicate Songs


import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------------------------
# 1. LOAD DATASET
# ------------------------------------------------
df = pd.read_csv("dataset.csv")

# Make lowercase copy for matching
df["track_name_lower"] = df["track_name"].str.lower()

# ------------------------------------------------
# 2. AUDIO FEATURES
# ------------------------------------------------
features = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness",
    "liveness", "valence", "tempo"
]

df = df.dropna(subset=features).reset_index(drop=True)

# ------------------------------------------------
# 3. LANGUAGE DETECTION
# ------------------------------------------------
def detect_language(row):

    genre = str(row["track_genre"]).lower()
    artist = str(row["artists"]).lower()

    if any(w in genre for w in ["indian", "bollywood", "desi"]):
        return "hindi"

    if any(w in artist for w in [
        "arijit","atif","shreya","rahat",
        "neha","sonu","udit","kk"
    ]):
        return "hindi"

    return "english"

df["language"] = df.apply(detect_language, axis=1)

# ------------------------------------------------
# 4. NORMALIZE FEATURES
# ------------------------------------------------
scaler = StandardScaler()
X = scaler.fit_transform(df[features])

# ------------------------------------------------
# 5. RECOMMENDATION FUNCTION
# ------------------------------------------------
def recommend_songs(user_songs, top_n=10):

    # Convert user songs to lowercase
    user_songs_lower = [s.lower() for s in user_songs]

    user_rows = df[df["track_name_lower"].isin(user_songs_lower)]

    if user_rows.empty:
        print("❌ Songs not found in dataset")
        return None

    user_language = user_rows["language"].mode()[0]

    filtered_df = df[df["language"] == user_language]
    filtered_X = X[filtered_df.index]

    user_indices = filtered_df[
        filtered_df["track_name_lower"].isin(user_songs_lower)
    ].index

    similarity = cosine_similarity(
        filtered_X,
        X[user_indices]
    )

    avg_similarity = similarity.mean(axis=1)

    recommendations = (
        filtered_df.assign(score=avg_similarity)
        .sort_values("score", ascending=False)
        .drop_duplicates(subset="track_name")   # remove repeats
        .loc[~filtered_df["track_name_lower"].isin(user_songs_lower)]
        .head(top_n)
    )

    return recommendations[
        ["track_name", "artists", "track_genre", "language", "score"]
    ]

# ------------------------------------------------
# 6. TEST
# ------------------------------------------------
if __name__ == "__main__":

    user_likes = [
        "tum hi ho",
        "BELIEVER"
    ]

    results = recommend_songs(user_likes, top_n=10)

    if results is not None:
        print("\n🎧 Recommended Songs:\n")

        for _, row in results.iterrows():
            print(
                f"{row['track_name']} - {row['artists']} "
                f"[{row['language'].upper()}]"
            )

