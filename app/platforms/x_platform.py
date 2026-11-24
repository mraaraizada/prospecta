"""X (Twitter) platform searcher — X's v2 search-by-keyword API requires a paid
developer tier; this surfaces publicly-indexed X/Twitter profile URLs via
`site:x.com` Brave Search instead, filtered to real `x.com/<handle>`
profile paths (excluding status/post URLs, which aren't profiles)."""
from __future__ import annotations

import re

import httpx

from app.platforms import web_search
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"(x|twitter)\.com/(?!(?:i|home|search|explore)/)[A-Za-z0-9_]+/?$")


class XSearcher(PlatformSearcher):
    name = "X"

    def is_configured(self) -> bool:
        return web_search.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: BRAVE_API_KEY is required (X's keyword search API requires a paid developer tier)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "x.com", raw_query, _PROFILE_PATTERN)
