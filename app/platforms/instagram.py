"""Instagram platform searcher — Instagram's Graph API requires an approved
Business app for arbitrary profile discovery (confirmed in Vortiq's identical
investigation of Instagram's oEmbed limits). This surfaces publicly-indexed
Instagram profile URLs via `site:instagram.com` Google Custom Search instead."""
from __future__ import annotations

import re

import httpx

from app.platforms import google_cse
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"instagram\.com/(?!(?:p|reel|explore|accounts)/)[A-Za-z0-9_.]+/?$")


class InstagramSearcher(PlatformSearcher):
    name = "Instagram"

    def is_configured(self) -> bool:
        return google_cse.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID are required (Instagram's Graph API requires an approved Business app for discovery)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "instagram.com", raw_query, _PROFILE_PATTERN)
