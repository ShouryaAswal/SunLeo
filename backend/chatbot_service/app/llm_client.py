"""
SunLeo LLM Client — Groq → Gemini Flash fallback router.

Both providers are accessed via the OpenAI-compatible protocol so the same
tool schemas, message format, and response parsing work for both.

Provider selection logic:
  1. Default to Groq (fast, free tier)
  2. On rate limit → retry with exponential backoff (up to LLM_MAX_GROQ_RETRIES)
  3. After all retries exhausted → pin session to Gemini for the rest of
     that conversation (avoids hammering Groq repeatedly)
  4. Non-rate-limit errors (schema bugs, etc.) are re-raised immediately

No LangChain, no LangGraph — just the `openai` async SDK with different base_urls.
"""
from __future__ import annotations

import asyncio
import logging
import os
from enum import Enum

from openai import AsyncOpenAI, RateLimitError, APIError

log = logging.getLogger("sunleo.llm")

# ── Provider enum ─────────────────────────────────────────────────────────────

class Provider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"


# ── Client factories ─────────────────────────────────────────────────────────

def _groq_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY", ""),
        base_url="https://api.groq.com/openai/v1",
    )


def _gemini_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


# ── Session-level provider pinning ───────────────────────────────────────────

_session_providers: dict[str, Provider] = {}


def get_session_provider(session_id: str) -> str:
    """Return the active provider name for a session (default: groq)."""
    return _session_providers.get(session_id, Provider.GROQ).value


def pin_session_to_gemini(session_id: str) -> None:
    """Pin a session to Gemini after Groq retries are exhausted."""
    _session_providers[session_id] = Provider.GEMINI
    log.warning("Session %s pinned to Gemini (Groq retries exhausted)", session_id)


def reset_session_provider(session_id: str) -> None:
    """Reset a session back to the default provider (Groq)."""
    _session_providers.pop(session_id, None)


# ── Message adaptation ───────────────────────────────────────────────────────

def _adapt_messages_for_gemini(messages: list[dict]) -> list[dict]:
    """Convert system-role messages to user/assistant pairs for Gemini.

    Gemini's OpenAI-compatible endpoint does not support role=system.
    We convert each system message into a user instruction + assistant ack.
    """
    adapted: list[dict] = []
    for msg in messages:
        if msg.get("role") == "system":
            adapted.append({
                "role": "user",
                "content": f"[SYSTEM INSTRUCTIONS]\n{msg['content']}",
            })
            adapted.append({
                "role": "assistant",
                "content": "Understood. I will follow these instructions.",
            })
        else:
            adapted.append(msg)
    return adapted


# ── Provider-specific call helpers ────────────────────────────────────────────

async def _call_groq(
    messages: list[dict],
    tools: list[dict] | None,
    temperature: float,
    max_tokens: int,
):
    """Call Groq via OpenAI-compatible endpoint."""
    client = _groq_client()
    model = os.getenv("LLM_GROQ_MODEL", "llama-3.3-70b-versatile")
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    log.debug("Calling Groq model=%s", model)
    return await client.chat.completions.create(**kwargs)


async def _call_gemini(
    messages: list[dict],
    tools: list[dict] | None,
    temperature: float,
    max_tokens: int,
):
    """Call Gemini via OpenAI-compatible endpoint."""
    client = _gemini_client()
    model = os.getenv("LLM_GEMINI_MODEL", "gemini-2.0-flash")
    adapted = _adapt_messages_for_gemini(messages)
    kwargs: dict = {
        "model": model,
        "messages": adapted,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    log.info("Calling Gemini model=%s", model)
    return await client.chat.completions.create(**kwargs)


# ── Main entry point ─────────────────────────────────────────────────────────

_MAX_GROQ_RETRIES = int(os.getenv("LLM_MAX_GROQ_RETRIES", "3"))


async def chat_completion(
    session_id: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
    """
    Send a chat completion request with automatic Groq → Gemini fallback.

    Returns the raw OpenAI-compatible response object.
    Raises RuntimeError only if both providers fail.
    """
    provider = _session_providers.get(session_id, Provider.GROQ)

    # ── If already pinned to Gemini, go straight there ────────────────────
    if provider == Provider.GEMINI:
        return await _call_gemini_with_retry(session_id, messages, tools, temperature, max_tokens)

    # ── Try Groq with retry ──────────────────────────────────────────────
    last_groq_error: Exception | None = None

    for attempt in range(_MAX_GROQ_RETRIES):
        try:
            return await _call_groq(messages, tools, temperature, max_tokens)

        except RateLimitError as exc:
            last_groq_error = exc
            wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
            log.warning(
                "Groq rate limited (attempt %d/%d). Waiting %ds...",
                attempt + 1, _MAX_GROQ_RETRIES, wait_time,
            )
            await asyncio.sleep(wait_time)
            continue

        except APIError as exc:
            error_str = str(exc)
            # Rate limit may also surface as a generic APIError with 429
            if "429" in error_str or "rate_limit" in error_str.lower():
                last_groq_error = exc
                wait_time = 2 ** (attempt + 1)
                log.warning(
                    "Groq rate limited via APIError (attempt %d/%d). Waiting %ds...",
                    attempt + 1, _MAX_GROQ_RETRIES, wait_time,
                )
                await asyncio.sleep(wait_time)
                continue
            # Non-rate-limit API errors — re-raise (likely schema/tool problems)
            raise

        except Exception:
            # Non-rate-limit errors — re-raise immediately
            raise

    # ── Groq retries exhausted → fall through to Gemini ──────────────────
    log.warning(
        "Groq retries exhausted for session %s (last error: %s). Falling back to Gemini.",
        session_id, last_groq_error,
    )
    pin_session_to_gemini(session_id)

    return await _call_gemini_with_retry(session_id, messages, tools, temperature, max_tokens, last_groq_error)


_MAX_GEMINI_RETRIES = 2


async def _call_gemini_with_retry(
    session_id: str,
    messages: list[dict],
    tools: list[dict] | None,
    temperature: float,
    max_tokens: int,
    last_groq_error: Exception | None = None,
):
    """Call Gemini with up to 2 retry attempts on rate limits."""
    for attempt in range(_MAX_GEMINI_RETRIES):
        try:
            return await _call_gemini(messages, tools, temperature, max_tokens)
        except (RateLimitError, APIError) as exc:
            error_str = str(exc)
            if "429" in error_str or "rate_limit" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = 10 * (attempt + 1)  # 10s, 20s
                log.warning(
                    "Gemini rate limited (attempt %d/%d). Waiting %ds...",
                    attempt + 1, _MAX_GEMINI_RETRIES, wait_time,
                )
                await asyncio.sleep(wait_time)
                continue
            # Non-rate-limit error
            log.error("Gemini non-rate-limit error for session %s: %s", session_id, exc)
            raise RuntimeError(f"Gemini failed: {exc}") from exc
        except Exception as exc:
            log.error("Gemini call failed for session %s: %s", session_id, exc)
            raise RuntimeError(f"Gemini failed: {exc}") from exc

    # Both exhausted
    log.error(
        "Both Groq and Gemini failed for session %s. Groq: %s | Gemini: rate limited",
        session_id, last_groq_error,
    )
    raise RuntimeError(
        f"All LLM providers rate limited. Please wait a minute and try again."
    )

