from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SunLeo Chatbot Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    actions: list[dict] = []


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint. Currently returns a placeholder response.
    Will be connected to LangChain ReAct agent with Groq LLM.
    """
    # TODO: Replace with actual agent invocation
    # from .agent import run_agent
    # result = await run_agent(request.message, request.session_id)

    return ChatResponse(
        reply=f"🎵 SunLeo DJ here! I heard you say: '{request.message}'. "
              f"Agent integration coming soon — I'll be able to search, recommend, "
              f"and download music for you!",
        actions=[]
    )
