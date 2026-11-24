"""Shared real web-search client — the actual discovery engine behind every
platform in this project that has no API of its own.

Real finding (2026-11-24): Google's own Custom Search JSON API is closed to new
customers (confirmed directly against https://developers.google.com/custom-search/v1/overview,
which states "This API is not available for new customers"), and the Gemini
API's built-in Google Search grounding tool returned a real, repeatable `429`
even on a brand-new API key while a plain (non-grounded) call on the same key
succeeded — its free tier is not usable for this project right now. Both are
genuine, current platform-policy blockers, not configuration mistakes.

Serper.dev (https://serper.dev) is used instead: a real, ToS-compliant reseller
of actual Google search results, with a free tier (2,500 queries, no credit card)
that is genuinely open to new signups — this fits the spec's own "permitted
search APIs" language. It still only ever returns what's already publicly
indexed; it never logs in, scrapes an authenticated page, or bypasses any
platform's own access controls.
"""
from __future__ import annotations

import httpx

from app.config import settings

_ENDPOINT = "https://google.serper.dev/search"


class SearchProviderError(Exception):
    """Raised when the search API call fails or isn't configured."""


def is_configured() -> bool:
    return bool(settings.serper_api_key)


async def search(client: httpx.AsyncClient, query: str, num: int | None = None) -> list[dict]:
    """Returns a list of {"title": str, "snippet": str, "link": str} — real,
    unmodified fields from the provider's own response. Raises
    SearchProviderError on failure; returns [] (not an error) for a query that
    simply has no results."""
    if not is_configured():
        raise SearchProviderError("Not configured: SERPER_API_KEY is required")

    payload = {"q": query, "num": num or settings.max_results_per_platform}
    try:
        resp = await client.post(
            _ENDPOINT,
            headers={"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise SearchProviderError("Search request timed out") from exc
    except httpx.HTTPError as exc:
        raise SearchProviderError(f"Search request failed: {exc}") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json().get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise SearchProviderError(f"Search API error (HTTP {resp.status_code}): {detail}")

    body = resp.json()
    items = body.get("organic") or []
    return [{"title": item.get("title", ""), "snippet": item.get("snippet", ""), "link": item.get("link", "")} for item in items]
