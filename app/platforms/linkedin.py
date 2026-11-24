"""LinkedIn platform searcher — LinkedIn offers no public people-search API (its
Community Management API is approval-gated; see Vortiq's identical finding for
LinkedIn's company-page API). This module only surfaces LinkedIn profile URLs
Google has already publicly indexed via `site:linkedin.com`, filtered to real
`/in/<handle>` personal-profile or `/company/<slug>` business-profile paths —
never anything fetched by directly scraping linkedin.com itself.
"""
from __future__ import annotations

import re

import httpx

from app.platforms import google_cse
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"linkedin\.com/(in|company)/[^/?]+")


class LinkedInSearcher(PlatformSearcher):
    name = "LinkedIn"

    def is_configured(self) -> bool:
        return google_cse.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID are required (LinkedIn has no public search API of its own)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "linkedin.com", raw_query, _PROFILE_PATTERN)
