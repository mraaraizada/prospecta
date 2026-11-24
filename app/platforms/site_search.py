"""Shared logic for every platform that has no search API of its own: a
`site:`-restricted Brave Search query, filtered to URLs that actually
look like a profile/page (not a generic help/login/terms page Google happens to
have indexed under that domain)."""
from __future__ import annotations

import re

import httpx

from app.platforms import web_search
from app.platforms.base import PlatformSearchError, RawCandidate


async def site_restricted_search(
    client: httpx.AsyncClient,
    platform_name: str,
    domain: str,
    query_terms: str,
    profile_path_pattern: re.Pattern[str],
) -> list[RawCandidate]:
    try:
        results = await web_search.search(client, f"site:{domain} {query_terms}")
    except web_search.GoogleSearchError as exc:
        raise PlatformSearchError(str(exc)) from exc

    candidates = []
    for r in results:
        link = r["link"]
        if profile_path_pattern.search(link):
            candidates.append(RawCandidate(platform=platform_name, title=r["title"], snippet=r["snippet"], link=link))
    return candidates
