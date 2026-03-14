# Music Recommendation System 🎧

This project implements a **content-based music recommendation system** using a Spotify songs dataset.
The system recommends songs based on **audio feature similarity** such as danceability, energy, tempo, and valence.

## Features

* Recommends songs similar to user input songs
* Case-insensitive song matching
* Language-aware filtering (Hindi → Hindi, English → English)
* Removes duplicate song recommendations
* Uses cosine similarity on normalized audio features

## Technologies Used

* Python
* Pandas
* Scikit-learn
* Spotify Audio Features Dataset

## How It Works

1. The dataset is loaded and cleaned.
2. Important audio features are normalized.
3. Cosine similarity is used to measure similarity between songs.
4. The system returns the most similar songs as recommendations.

## Usage

1. Place `dataset.csv` in the project folder.
2. Run the Python script.
3. Provide a list of songs you like.
4. The system outputs recommended songs.

## Example

Input:

```
["Tum Hi Ho", "Believer"]
```

Output:

```
Recommended Songs:
Humdard - Arijit Singh
Channa Mereya - Arijit Singh
Thunder - Imagine Dragons
```

## Author

Raj Kushwaha
