from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Recommendation Service Skeleton")

class RecommendationRequest(BaseModel):
    seed_genres: List[str] = Field(..., max_items=5)
    target_danceability: Optional[float] = None
    target_energy: Optional[float] = None
    target_valence: Optional[float] = None
    target_tempo: Optional[int] = None
    limit: int = 10

class TrackInfo(BaseModel):
    track_name: str
    artist_name: str
    search_query: str

@app.get("/genres")
def get_available_genres():
    """Skeletal mock data for genres."""
    return {"genres": ["pop", "rock", "hip-hop", "acoustic", "electronic", "metal", "chill"]}

@app.post("/recommend", response_model=List[TrackInfo])
def get_recommendations(req: RecommendationRequest):
    """
    Skeletal mock response. 
    In the future, we will integrate a robust API or custom model here.
    """
    # Mock response
    return [
        TrackInfo(track_name="Dummy Track 1", artist_name="Dummy Artist", search_query="Dummy Track 1 Dummy Artist audio"),
        TrackInfo(track_name="Dummy Track 2", artist_name="Dummy Artist", search_query="Dummy Track 2 Dummy Artist audio")
    ]

@app.get("/search", response_model=List[TrackInfo])
def search_tracks(q: str, limit: int = 10):
    """
    Skeletal mock response for searching tracks.
    """
    return [
        TrackInfo(track_name=f"Mock Result for {q}", artist_name="Unknown", search_query=f"{q} audio")
    ]
