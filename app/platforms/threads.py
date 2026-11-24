"""Threads platform searcher — Threads (Meta) has no public search-by-topic API
at all. This surfaces publicly-indexed Threads profile URLs via
`site:threads.net` Google Custom Search instead."""
from __future__ import annotations

import re

import httpx

from app.platforms import search_provider
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"threads\.net/@[A-Za-z0-9_.]+/?$")


class ThreadsSearcher(PlatformSearcher):
    name = "Threads"

    def is_configured(self) -> bool:
        return search_provider.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: SERPER_API_KEY is required (Threads has no public search-by-topic API)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "threads.net", raw_query, _PROFILE_PATTERN)
