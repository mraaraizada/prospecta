"""Facebook platform searcher — Facebook's Graph API requires App Review for
public-page discovery beyond a single known URL's oEmbed (confirmed in Vortiq's
identical investigation). This surfaces publicly-indexed Facebook profile/page
URLs via `site:facebook.com` Google Custom Search instead."""
from __future__ import annotations

import re

import httpx

from app.platforms import search_provider
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"facebook\.com/(?!(?:help|policy|terms|login|sharer)/)[A-Za-z0-9.]+/?$")


class FacebookSearcher(PlatformSearcher):
    name = "Facebook"

    def is_configured(self) -> bool:
        return search_provider.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: SERPER_API_KEY is required (Facebook's Graph API requires App Review for public discovery beyond oEmbed)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "facebook.com", raw_query, _PROFILE_PATTERN)
