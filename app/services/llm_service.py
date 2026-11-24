"""Gemini API client: two real calls per discovery request, not one per candidate
(a deliberate cost-optimization choice — see docs/llm_research.md).

1. `parse_query_intent` — turns the natural-language query into structured
   interest/audience/location/target_type, schema-enforced via Gemini's native
   structured-output support (same mechanism as Vortiq's link-analysis project).
2. `score_relevance_batch` — given the parsed intent and every raw candidate found
   by the platform searches, makes ONE call that returns, per candidate, whether
   it's genuinely relevant and the real display name to use — based only on the
   candidate's actual search-result title/snippet, never invented.
"""
from __future__ import annotations

import json

import httpx

from app.config import settings

_INTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "interest": {"type": "STRING"},
        "audience": {"type": "STRING"},
        "location": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING"},
                "state": {"type": "STRING"},
                "country": {"type": "STRING"},
            },
        },
        "target_type": {"type": "STRING", "enum": ["individual", "business"]},
    },
    "required": ["interest", "audience", "location", "target_type"],
}

_INTENT_PROMPT = """Parse this prospect-discovery search query into structured search parameters. \
Extract the interest/topic, the audience description, the geographical location (city, state, \
country — use null for any part not mentioned or not determinable), and whether the query is \
looking for individuals or businesses. Do not invent a location that isn't implied by the query.

Query: {query}

Produce the structured parameters now."""

_RELEVANCE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "is_relevant": {"type": "BOOLEAN"},
                    "display_name": {"type": "STRING"},
                    "reason": {"type": "STRING"},
                },
                "required": ["id", "is_relevant", "display_name", "reason"],
            },
        }
    },
    "required": ["results"],
}

_RELEVANCE_PROMPT = """You are filtering real search results for a prospect-discovery tool. \
For EACH candidate below, decide whether it genuinely indicates a connection to the stated \
interest and/or location — based ONLY on the candidate's actual title and snippet text, never \
on the name alone and never on assumption. Mark is_relevant=false for anything that isn't \
clearly supported by the title/snippet. Extract display_name as the real person or business \
name as it actually appears in the title (not invented, not guessed) — if no real name is \
identifiable, use is_relevant=false instead of guessing a name. Give a one-sentence reason \
citing what in the title/snippet supports (or fails to support) relevance.

Search intent: interest={interest!r}, audience={audience!r}, location={location!r}, target_type={target_type!r}

Candidates:
{candidates}

Return a result for every candidate id, in order."""


class LLMServiceError(Exception):
    """Raised when the LLM call fails or returns an unusable response."""


async def _call_gemini(client: httpx.AsyncClient, prompt: str, schema: dict) -> dict:
    if not settings.gemini_api_key:
        raise LLMServiceError("Not configured: GEMINI_API_KEY is required")

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema, "temperature": 0.3},
    }
    try:
        resp = await client.post(endpoint, params={"key": settings.gemini_api_key}, json=payload, timeout=settings.llm_timeout_seconds)
    except httpx.TimeoutException as exc:
        raise LLMServiceError("LLM request timed out") from exc
    except httpx.HTTPError as exc:
        raise LLMServiceError(f"LLM request failed: {exc}") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise LLMServiceError(f"Gemini API error (HTTP {resp.status_code}): {detail}")

    body = resp.json()
    candidates = body.get("candidates") or []
    if not candidates:
        raise LLMServiceError("Gemini response contained no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts or "text" not in parts[0]:
        raise LLMServiceError("Gemini response contained no text part")
    try:
        return json.loads(parts[0]["text"])
    except json.JSONDecodeError as exc:
        raise LLMServiceError(f"Gemini response was not valid JSON: {exc}") from exc


async def parse_query_intent(client: httpx.AsyncClient, query: str) -> dict:
    return await _call_gemini(client, _INTENT_PROMPT.format(query=query), _INTENT_SCHEMA)


async def score_relevance_batch(client: httpx.AsyncClient, intent: dict, candidates: list[dict]) -> list[dict]:
    """`candidates` is a list of {"id": int, "platform": str, "title": str, "snippet": str}.
    Returns the LLM's per-candidate relevance judgments in the same order."""
    if not candidates:
        return []
    lines = [f"{c['id']}. [{c['platform']}] title={c['title']!r} snippet={c['snippet']!r}" for c in candidates]
    prompt = _RELEVANCE_PROMPT.format(
        interest=intent.get("interest"),
        audience=intent.get("audience"),
        location=intent.get("location"),
        target_type=intent.get("target_type"),
        candidates="\n".join(lines),
    )
    body = await _call_gemini(prompt=prompt, client=client, schema=_RELEVANCE_SCHEMA)
    return body.get("results", [])
