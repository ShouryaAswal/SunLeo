"""
SunLeo Chatbot Agent — LangChain ReAct Agent Setup.
Placeholder for when Groq API key is configured.
"""
from __future__ import annotations

# TODO: Uncomment and configure once GROQ_API_KEY is set
#
# import os
# from langchain_groq import ChatGroq
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain.tools import StructuredTool
# from langchain.prompts import PromptTemplate
# from .tools import search_tracks, get_recommendations, download_tracks, check_download_status, create_playlist
#
# SYSTEM_PROMPT = """You are SunLeo DJ, a friendly music assistant.
# You help users discover and download music based on their mood, activity, or preferences.
#
# You have access to these tools:
# - search_tracks: Search for specific songs or artists
# - get_recommendations: Get recommendations by genre/mood
# - download_tracks: Download songs as MP3 from YouTube
# - check_download_status: Check if downloads are complete
# - create_playlist: Save songs as a named playlist
#
# Map user moods to audio features:
# - Chill/Study/Sleep -> low energy (0.2-0.4), low valence
# - Workout/Party/Hype -> high energy (0.7-1.0), high valence
# - Sad/Melancholy -> low energy, low valence (0.1-0.3)
# - Happy/Upbeat -> high energy, high valence (0.7-1.0)
#
# Never download without user confirmation. Always present options first."""
#
#
# def create_agent():
#     llm = ChatGroq(
#         model_name="llama3-70b-8192",
#         api_key=os.getenv("GROQ_API_KEY"),
#         temperature=0.7,
#     )
#
#     tools = [
#         StructuredTool.from_function(search_tracks, name="search_tracks",
#             description="Search for tracks by name or artist"),
#         StructuredTool.from_function(get_recommendations, name="get_recommendations",
#             description="Get recommendations based on genres and mood parameters"),
#         StructuredTool.from_function(download_tracks, name="download_tracks",
#             description="Download YouTube URLs as MP3"),
#         StructuredTool.from_function(check_download_status, name="check_download_status",
#             description="Check download job status"),
#         StructuredTool.from_function(create_playlist, name="create_playlist",
#             description="Create a named playlist from tracks"),
#     ]
#
#     agent = create_react_agent(llm, tools, SYSTEM_PROMPT)
#     return AgentExecutor(agent=agent, tools=tools, verbose=True)
#
#
# async def run_agent(message: str, session_id: str) -> dict:
#     agent = create_agent()
#     result = agent.invoke({"input": message})
#     return {"reply": result["output"], "actions": []}
