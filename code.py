

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# 1. LOAD DATASET

df = pd.read_csv("dataset.csv")

# 2. AUDIO FEATURES
features = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness",
    "liveness", "valence", "tempo"
]

df = df.dropna(subset=features).reset_index(drop=True)

# 3. LANGUAGE DETECTION (RULE-BASED)
def detect_language(row):
    genre = str(row["track_genre"]).lower()
    artist = str(row["artists"]).lower()

    if any(w in genre for w in ["indian", "bollywood", "desi"]):
        return "hindi"
    if any(w in artist for w in [
        "arijit", "atif", "shreya", "rahat",
        "neha", "sonu", "udit", "kk"
    ]):
        return "hindi"

    return "english"

df["language"] = df.apply(detect_language, axis=1)

# 4. NORMALIZE FEATURES
scaler = StandardScaler()
X = scaler.fit_transform(df[features])

# 5. RECOMMENDATION FUNCTION
def recommend_songs(user_songs, top_n=10):

    user_rows = df[df["track_name"].isin(user_songs)]

    if user_rows.empty:
        print("❌ Songs not found in dataset")
        return None

    # Detect user language (majority)
    user_language = user_rows["language"].mode()[0]

    # Filter by same language
    filtered_df = df[df["language"] == user_language]
    filtered_X = X[filtered_df.index]

    user_indices = filtered_df[
        filtered_df["track_name"].isin(user_songs)
    ].index

    similarity = cosine_similarity(
        filtered_X,
        X[user_indices]
    )

    avg_similarity = similarity.mean(axis=1)

    recommendations = (
        filtered_df.assign(score=avg_similarity)
        .sort_values("score", ascending=False)
        .drop_duplicates(subset="track_name")   # ✅ REMOVE DUPLICATES
        .loc[~filtered_df["track_name"].isin(user_songs)]
        .head(top_n)
    )

    return recommendations[
        ["track_name", "artists", "track_genre", "language", "score"]
    ]

# 6. TEST

if __name__ == "__main__":

    user_likes = [
        "Tum Hi Ho",     # Hindi
        "kesariya"       # English (language decided by majority)
    ]

    results = recommend_songs(user_likes, top_n=10)

    if results is not None:
        print("\n🎧 Recommended Songs:\n")
        for _, row in results.iterrows():
            print(
                f"{row['track_name']}  -  {row['artists']} "
                f"[{row['language'].upper()}]"
            )
