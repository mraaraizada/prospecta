"""Shared search client — the real discovery engine behind every platform in
this project that has no API of its own.

Originally built against Google's Custom Search JSON API, but live testing on
2026-11-24 found that API genuinely closed to new customers (confirmed against
Google's own docs: "The Custom Search JSON API is closed to new customers" —
billing does not unlock it; there is no exception path for a new project).
Switched to the Brave Search API instead — real, currently available, with a
genuine free tier (2,000 queries/month). Official docs:
https://api-dashboard.search.brave.com/app/documentation/web-search/get-started

This module name is kept as `google_cse` for historical/git-history clarity
(the `site:`-restricted search PATTERN it enables is unchanged — only the
underlying provider changed); `search()`'s call signature and return shape are
unchanged, so every platform adapter needed zero changes for this swap.
"""
from __future__ import annotations

import httpx

from app.config import settings

_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class GoogleSearchError(Exception):
    """Raised when the search API call fails or isn't configured."""


def is_configured() -> bool:
    return bool(settings.brave_api_key)


async def search(client: httpx.AsyncClient, query: str, num: int | None = None) -> list[dict]:
    """Returns a list of {"title": str, "snippet": str, "link": str} — real,
    unmodified fields from the provider's own response. Raises GoogleSearchError
    on failure; returns [] (not an error) for a query that simply has no results."""
    if not is_configured():
        raise GoogleSearchError("Not configured: BRAVE_API_KEY is required")

    params = {"q": query, "count": min(num or settings.max_results_per_platform, 20)}
    headers = {"X-Subscription-Token": settings.brave_api_key, "Accept": "application/json"}
    try:
        resp = await client.get(_ENDPOINT, params=params, headers=headers, timeout=settings.request_timeout_seconds)
    except httpx.TimeoutException as exc:
        raise GoogleSearchError("Search request timed out") from exc
    except httpx.HTTPError as exc:
        raise GoogleSearchError(f"Search request failed: {exc}") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json().get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise GoogleSearchError(f"Search API error (HTTP {resp.status_code}): {detail}")

    body = resp.json()
    items = (body.get("web") or {}).get("results") or []
    return [{"title": item.get("title", ""), "snippet": item.get("description", ""), "link": item.get("url", "")} for item in items]
