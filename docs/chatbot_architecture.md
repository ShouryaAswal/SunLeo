# SunLeo Chatbot Agent Architecture

## Overview

The SunLeo Chatbot is an agentic AI assistant that lets users discover and download music using natural language. Users describe their mood, activity, or preferences, and the chatbot autonomously searches for tracks, recommends songs, and triggers downloads through the existing SunLeo pipeline.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                       │
│  ┌──────────────────────────────────────────────┐   │
│  │  Chat Widget (st.chat_input / st.chat_message)│   │
│  └──────────────┬───────────────────────────────┘   │
│                 │ User message                       │
└─────────────────┼───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│              Chatbot Backend (FastAPI)                │
│  POST /chat  { message, session_id }                 │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           LangChain ReAct Agent               │   │
│  │                                               │   │
│  │  LLM: Groq API (Free Tier)                    │   │
│  │  Model: Llama 3 70B / Mixtral 8x7B            │   │
│  │                                               │   │
│  │  Tools:                                       │   │
│  │   ├── search_tracks(query)                    │   │
│  │   ├── get_recommendations(genres, mood)        │   │
│  │   ├── download_tracks(urls)                    │   │
│  │   ├── check_download_status(job_ids)           │   │
│  │   └── create_playlist(name, tracks)            │   │
│  └──────────────────────────────────────────────┘   │
└───────────┬──────────────┬──────────────────────────┘
            │              │
            ▼              ▼
┌──────────────────┐ ┌──────────────────┐
│  Recommendation  │ │   YT Converter   │
│  Service :8001   │ │   Service :8000  │
│  /search         │ │  /convert/batch  │
│  /recommend      │ │  /status/{id}    │
│  /genres         │ │  /download/{id}  │
└──────────────────┘ └──────────────────┘
```

## Technology Stack (All Free)

| Component | Choice | Why |
|-----------|--------|-----|
| **LLM Provider** | Groq API (free tier) | Fastest inference (~500 tok/s), no credit card, supports tool-calling |
| **Model** | Llama 3 70B or Mixtral 8x7B | Strong instruction following and tool-calling capability |
| **Fallback Provider** | HuggingFace Inference API | Free 300 req/hr, massive model selection |
| **Agent Framework** | LangChain + LangGraph | Mature Python framework with built-in ReAct agent and tool support |
| **Training** | Not needed — prompt engineering only | Zero cost |

## Agent Tools

### 1. `search_tracks(query: str, limit: int = 10)`
- **Calls**: Recommendation Service `GET /search?q={query}&limit={limit}`
- **Returns**: List of `{track_name, artist_name, search_query}`
- **Use case**: User says "find songs by The Weeknd"

### 2. `get_recommendations(genres: list, energy: float, valence: float, limit: int)`
- **Calls**: Recommendation Service `POST /recommend`
- **Returns**: List of recommended tracks matching mood parameters
- **Use case**: User says "I want chill lo-fi beats for studying"

### 3. `download_tracks(youtube_urls: list)`
- **Calls**: YT Converter `POST /convert/batch`
- **Returns**: List of job IDs
- **Use case**: User says "download the first 3 results"

### 4. `check_download_status(job_ids: list)`
- **Calls**: YT Converter `GET /status/{job_id}` for each ID
- **Returns**: Status of each download job
- **Use case**: Agent polls after triggering downloads

### 5. `create_playlist(name: str, tracks: list)`
- **Calls**: Internal session management
- **Returns**: Confirmation of playlist creation
- **Use case**: User says "save these as my study playlist"

## Example Conversation Flow

```
User: "I want some chill lo-fi beats for studying"

Agent thinks: Extract intent → genre=lofi, mood=chill, activity=study
Agent calls: get_recommendations(genres=["chill"], energy=0.3, valence=0.5)
Agent receives: [{track_name: "Lo-fi Dream", artist: "ChillHop", ...}, ...]

Agent: "I found 10 chill lo-fi tracks for you:
        1. Lo-fi Dream by ChillHop
        2. Study Session by Beats Café
        ...
        Would you like me to download any of them?"

User: "Yes, download the first 3"

Agent calls: download_tracks([url1, url2, url3])
Agent calls: check_download_status([job1, job2, job3])

Agent: "All 3 tracks are downloaded and ready in your Player! 🎧"

User: "Save these as my study playlist"

Agent calls: create_playlist("Study Playlist", [track1, track2, track3])

Agent: "Created 'Study Playlist' with 3 tracks! ✅"
```

## System Prompt (for the LLM)

```
You are SunLeo DJ, a friendly music assistant. You help users discover
and download music based on their mood, activity, or preferences.

You have access to these tools:
- search_tracks: Search for specific songs or artists
- get_recommendations: Get AI-powered music recommendations by genre/mood
- download_tracks: Download songs as MP3 from YouTube
- check_download_status: Check if downloads are complete
- create_playlist: Save a collection of songs as a named playlist

Always be enthusiastic about music. When users describe a mood or
activity, map it to audio features:
- Chill/Study/Sleep → low energy (0.2-0.4), low valence
- Workout/Party/Hype → high energy (0.7-1.0), high valence
- Sad/Melancholy → low energy, low valence (0.1-0.3)
- Happy/Upbeat → high energy, high valence (0.7-1.0)

Never download without user confirmation. Always present options first.
```

## Training Strategy

**No fine-tuning is needed for the initial version.** The system prompt + structured tool definitions give Llama 3 / Mixtral enough guidance to handle music conversations effectively.

### Future Enhancement (Free)
If we want to customize the model's music understanding later:
1. **Platform**: Kaggle (free T4 GPUs, 30hrs/week)
2. **Method**: QLoRA (4-bit quantization + LoRA adapters)
3. **Dataset**: Curate ~1000 music conversation examples
4. **Base Model**: Llama 3 8B (small enough for T4)
5. **Training Time**: ~2-4 hours on T4

## Skeleton Code Structure

```
backend/chatbot_service/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI with /chat endpoint
│   ├── agent.py          # LangChain ReAct agent setup
│   └── tools.py          # Tool wrappers for existing APIs
├── requirements.txt      # groq, langchain, langchain-groq
└── .env.example          # GROQ_API_KEY placeholder
```

## Setup Steps (When Ready to Implement)

1. Sign up at [console.groq.com](https://console.groq.com) → Get free API key
2. Add `GROQ_API_KEY=gsk_...` to `.env`
3. Install: `pip install groq langchain langchain-groq`
4. Start the chatbot service alongside other services
5. Connect the Streamlit chat widget to `POST /chat`
