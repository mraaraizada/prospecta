"""Shared Google Custom Search JSON API client — the real discovery engine behind
every platform in this project that has no API of its own. Official docs:
https://developers.google.com/custom-search/v1/overview

This only ever returns what Google has already publicly indexed; it never logs in,
scrapes an authenticated page, or bypasses any platform's own access controls —
it's the same mechanism as typing `site:linkedin.com football Washington DC` into
google.com, performed through the official, authorized API.
"""
from __future__ import annotations

import httpx

from app.config import settings

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchError(Exception):
    """Raised when the Custom Search API call fails or isn't configured."""


def is_configured() -> bool:
    return bool(settings.google_cse_api_key and settings.google_cse_id)


async def search(client: httpx.AsyncClient, query: str, num: int | None = None) -> list[dict]:
    """Returns a list of {"title": str, "snippet": str, "link": str} — real,
    unmodified fields from Google's own response. Raises GoogleSearchError on
    failure; returns [] (not an error) for a query that simply has no results."""
    if not is_configured():
        raise GoogleSearchError("Not configured: GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID are required")

    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_id,
        "q": query,
        "num": num or settings.max_results_per_platform,
    }
    try:
        resp = await client.get(_ENDPOINT, params=params, timeout=settings.request_timeout_seconds)
    except httpx.TimeoutException as exc:
        raise GoogleSearchError("Google Custom Search request timed out") from exc
    except httpx.HTTPError as exc:
        raise GoogleSearchError(f"Google Custom Search request failed: {exc}") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise GoogleSearchError(f"Google Custom Search API error (HTTP {resp.status_code}): {detail}")

    body = resp.json()
    items = body.get("items") or []
    return [{"title": item.get("title", ""), "snippet": item.get("snippet", ""), "link": item.get("link", "")} for item in items]
